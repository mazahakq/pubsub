import uuid
import json
import time
from flask import Flask, request
import pika
import logging
from prometheus_client import Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import os

#API
API_ADDRESS = os.getenv('API_ADDRESS', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app_a')

# Повышаем уровень логирования для библиотеки pika
logging.getLogger('pika').setLevel(logging.WARNING)  # Ставим минимальный уровень WARNINGS

# Настройки подключения к RabbitMQ
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
queue_name = 'numbers_queue'
reply_queue_name = 'result_queue'
TTL_SECONDS = 5  # Срок жизни сообщений в RabbitMQ — 5 секунд
TIMEOUT_MS = 50  # Таймаут ожидания ответа в миллисекундах

# Prometheus metrics
REQUEST_COUNTER = Counter('app_a_request_count', 'Количество запросов')
RESPONSE_TIME_HISTOGRAM = Histogram('app_a_response_time_histogram', 'Распределение времени ответа')

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Создаем очереди с параметрами TTL
args = {"x-message-ttl": TTL_SECONDS * 1000}  # TTL в миллисекундах
try:
    channel.queue_declare(queue=queue_name, arguments=args)
    channel.queue_declare(queue=reply_queue_name, arguments=args)
except pika.exceptions.ChannelClosedByBroker as err:
    logger.error(f"Ошибка объявления очереди: {err}. Удалите очереди и попробуйте снова.")
    exit(1)

app = Flask(__name__)

# Добавляем middleware для экспорта метрик
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

@app.route('/add', methods=['POST'])
def add_numbers():
    REQUEST_COUNTER.inc()  # Увеличение количества запросов
    start_time_total = time.time()  # Начало общей обработки

    data = request.get_json()
    num1 = int(data['num1'])
    num2 = int(data['num2'])

    # Уникальный correlation_id для идентификации запроса
    corr_id = str(uuid.uuid4())

    # Формирование тела сообщения с добавлением текущего timestamp
    current_timestamp = time.time()
    message_body = {
        'num1': num1,
        'num2': num2,
        'corr_id': corr_id,
        'timestamp': current_timestamp  # Собственный timestamp
    }

    # Открываем канал и слушатель для получения ответа
    with pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host)) as conn:
        ch = conn.channel()

        # Проверяем наличие очереди, используя пассивный режим
        try:
            ch.queue_declare(queue=reply_queue_name, passive=True, arguments=args)
        except pika.exceptions.ChannelClosedByBroker as err:
            # Если очередь не существует, объявляем её явно
            ch.queue_declare(queue=reply_queue_name, arguments=args)

        logger.info(f"Отправляется запрос {num1}+{num2} в RabbitMQ...")

        # Измеряем время отправки сообщения в RabbitMQ
        send_start_time = time.time()
        ch.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message_body),
            properties=pika.BasicProperties(correlation_id=corr_id)
        )
        send_end_time = time.time()
        logger.info(f"Сообщение отправлено в RabbitMQ за {(send_end_time - send_start_time)*1000:.3f} ms.")

        def wait_for_response(corr_id, timeout_ms):
            deadline = time.time() + timeout_ms / 1000  # Преобразование в секунды
            while time.time() < deadline:
                method_frame, header_frame, body = ch.basic_get(reply_queue_name, auto_ack=True)
                if body:
                    received_data = json.loads(body)
                    if received_data.get('corr_id') == corr_id:
                        return received_data['result'], time.time()  # Вернем ответ и время получения
                time.sleep(0.01)  # Небольшая пауза между проверками
            return None, None  # Таймаут превышен

        # Ждём ответа с таймаутом
        result, receive_time = wait_for_response(corr_id, TIMEOUT_MS)

        if result is None:
            logger.warning("Таймаут ожидания ответа истек.")
            return {"error": "Timeout exceeded"}, 504  # Возврат ошибки таймаута

        # Измеряем общее время обработки в приложении А
        total_processing_time = time.time() - start_time_total
        RESPONSE_TIME_HISTOGRAM.observe(total_processing_time)  # Сбор распределения времени обработки
        logger.info(f"Общее время обработки в приложении А: {total_processing_time*1000:.3f} ms.")

        # Измеряем время ожидания ответа
        waiting_time = receive_time - send_end_time
        logger.info(f"Время ожидания ответа из приложения Б: {waiting_time*1000:.3f} ms.")

    return {'result': result}

if __name__ == '__main__':
    from waitress import serve
    serve(app, host=API_ADDRESS, port=API_PORT)  # Запускаем сервер на порту
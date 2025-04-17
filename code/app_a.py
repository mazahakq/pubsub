import uuid
import json
import time
from flask import Flask, request
import pika
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app_a')

# Настройки подключения к RabbitMQ
rabbitmq_host = 'rabbitmq'
queue_name = 'numbers_queue'
reply_queue_name = 'result_queue'
TTL_SECONDS = 5  # Срок жизни сообщений в RabbitMQ — 5 секунд
TIMEOUT_MS = 50  # Таймаут ожидания ответа в миллисекундах

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Создаем очереди с параметрами TTL
args = {"x-message-ttl": TTL_SECONDS * 1000}  # TTL в миллисекундах
try:
    channel.queue_declare(queue=queue_name, passive=True, arguments=args)
    channel.queue_declare(queue=reply_queue_name, passive=True, arguments=args)
except pika.exceptions.ChannelClosedByBroker as err:
    logger.error(f"Ошибка объявления очереди: {err}. Удалите очереди и попробуйте снова.")
    exit(1)

app = Flask(__name__)

@app.route('/add', methods=['POST'])
def add_numbers():
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
        ch.queue_declare(queue=reply_queue_name, passive=True, arguments=args)

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
        logger.info(f"Общее время обработки в приложении А: {total_processing_time*1000:.3f} ms.")

        # Измеряем время ожидания ответа
        waiting_time = receive_time - send_end_time
        logger.info(f"Время ожидания ответа из приложения Б: {waiting_time*1000:.3f} ms.")

    return {'result': result}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
import uuid
import json
import time
from flask import Flask, request
import pika

# Настройки подключения к RabbitMQ
rabbitmq_host = 'rabbitmq'
queue_name = 'numbers_queue'
reply_queue_name = 'result_queue'
TIMEOUT_MS = 50  # Таймаут ожидания ответа в миллисекундах

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Создаем очереди
channel.queue_declare(queue=queue_name)
channel.queue_declare(queue=reply_queue_name)

app = Flask(__name__)

@app.route('/add', methods=['POST'])
def add_numbers():
    data = request.get_json()
    num1 = int(data['num1'])
    num2 = int(data['num2'])

    # Уникальный correlation_id для идентификации запроса
    corr_id = str(uuid.uuid4())

    # Формируем тело сообщения с корреляцией
    message_body = {
        'num1': num1,
        'num2': num2,
        'corr_id': corr_id
    }

    # Открываем канал и слушатель для получения ответа
    with pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host)) as conn:
        ch = conn.channel()
        ch.queue_declare(reply_queue_name)

        def wait_for_response(corr_id, timeout_ms):
            deadline = time.time() + timeout_ms / 1000  # преобразование в секунды
            while time.time() < deadline:
                method_frame, header_frame, body = ch.basic_get(reply_queue_name, auto_ack=True)
                if body:
                    received_data = json.loads(body)
                    if received_data.get('corr_id') == corr_id:
                        return received_data['result']
                time.sleep(0.01)  # Небольшая пауза между проверками
            return None  # Таймаут превышен

        # Отправляем запрос в очередь
        ch.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message_body),
            properties=pika.BasicProperties(correlation_id=corr_id)
        )

        # Ждём ответа с таймаутом
        result = wait_for_response(corr_id, TIMEOUT_MS)

        if result is None:
            return {"error": "Timeout exceeded"}, 504  # Возврат ошибки таймаута

    return {'result': result}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

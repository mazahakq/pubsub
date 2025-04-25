import time
from flask import Flask, jsonify, request
import pika
import uuid
import json

app = Flask(__name__)

# Настройки подключения к RabbitMQ
rabbitmq_host = 'rabbitmq'
queue_name = 'rpc_queue'
TIMEOUT_MS = 200  # Таймаут ожидания ответа в миллисекундах

def fibonacci_rpc(n1, n2):
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    # Создаем очередь ответов (exclusive, временные)
    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue

    # Корреляционный идентификатор
    corr_id = str(uuid.uuid4())

    # Определяем handler для получения ответа
    def on_response(ch, method, props, body):
        if corr_id == props.correlation_id:
            nonlocal response
            response = int(json.loads(body)['result'])

    # Подписываемся на очередь ответов
    channel.basic_consume(
        queue=callback_queue,
        on_message_callback=on_response,
        auto_ack=True
    )

    # Формируем тело запроса
    message_body = {
        'num1': n1,
        'num2': n2,
        'reply_to': callback_queue,
        'correlation_id': corr_id
    }

    # Отправляем запрос
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id
        ),
        body=json.dumps(message_body)
    )

    # Ждём ответ
    response = None
    deadline = time.time() + TIMEOUT_MS / 1000  # Преобразование в секунды
    while response is None:
        if time.time() > deadline:
            connection.close()
            return "timeout"
        connection.process_data_events()
        time.sleep(0.0001)

    connection.close()
    return response

@app.route('/add', methods=['POST'])
def sum_numbers():
    data = request.json
    num1 = data.get('num1')
    num2 = data.get('num2')

    if num1 is None or num2 is None:
        return jsonify({"error": "Необходимо передать оба числа"}), 400

    result = fibonacci_rpc(num1, num2)
    if result is 'timeout':
        return jsonify({"error": "Время ожидание превышено"}), 503
    
    return jsonify({"result": f"{result}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8000")
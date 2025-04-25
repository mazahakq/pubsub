import pika
import json

# Настройки подключения к RabbitMQ
rabbitmq_host = 'rabbitmq'
queue_name = 'rpc_queue'

def handle_request(channel, method, props, body):
    # Десериализируем JSON
    request_data = json.loads(body)
    n1 = request_data['num1']
    n2 = request_data['num2']

    # Вычисляем сумму
    result = n1 + n2

    # Формируем ответ
    response = {"result": result}

    # Возвращаем ответ клиенту
    channel.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=json.dumps(response)
    )

    # Подтверждение доставки
    channel.basic_ack(delivery_tag=method.delivery_tag)

# Создание соединения с RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Декларируем очередь для передачи заданий
channel.queue_declare(queue=queue_name)

# Начинаем прослушивание очереди
channel.basic_consume(queue=queue_name, on_message_callback=handle_request)

channel.start_consuming()
import json
import pika

# Настройки подключения к RabbitMQ
rabbitmq_host = 'rabbitmq'
queue_name = 'numbers_queue'
reply_queue_name = 'result_queue'

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Создаем очереди
channel.queue_declare(queue=queue_name)
channel.queue_declare(queue=reply_queue_name)

def process_message(channel, method, properties, body):
    message = json.loads(body)
    result = message['num1'] + message['num2']
    corr_id = message['corr_id']

    # Возвращаем результат с корреляционным id
    response = {
        'corr_id': corr_id,
        'result': result
    }

    channel.basic_publish(
        exchange='',
        routing_key=reply_queue_name,
        body=json.dumps(response),
        properties=pika.BasicProperties(correlation_id=properties.correlation_id)
    )

# Начинаем получать сообщения из очереди numbers_queue
channel.basic_consume(
    queue=queue_name,
    on_message_callback=process_message,
    auto_ack=True
)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    pass
finally:
    connection.close()

import json
import time
import pika
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app_b')

# Настройки подключения к RabbitMQ
rabbitmq_host = 'rabbitmq'
queue_name = 'numbers_queue'
reply_queue_name = 'result_queue'
MAX_MESSAGE_AGE = 1  # Максимально допустимый возраст сообщения — 1 секунда

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()

# Создаем очереди с параметрами TTL
args = {"x-message-ttl": 5000}  # TTL в миллисекундах (5 секунд)
try:
    channel.queue_declare(queue=queue_name, passive=True, arguments=args)
    channel.queue_declare(queue=reply_queue_name, passive=True, arguments=args)
except pika.exceptions.ChannelClosedByBroker as err:
    logger.error(f"Ошибка объявления очереди: {err}. Удалите очереди и попробуйте снова.")
    exit(1)

def process_message(channel, method, properties, body):
    start_time_total = time.time()  # Начало общей обработки

    message = json.loads(body)
    corr_id = message['corr_id']

    # Проверяем возраст сообщения
    message_age = time.time() - float(message['timestamp'])
    if message_age > MAX_MESSAGE_AGE:
        logger.warning(f"Игнорируем устаревшее сообщение {message['num1']}+{message['num2']}, возраст сообщения превышает {MAX_MESSAGE_AGE} сек.")
        return

    # Если сообщение актуально, продолжаем обработку
    result = message['num1'] + message['num2']

    # Измеряем время получения сообщения
    start_time_receive = time.time()
    logger.info(f"Получено сообщение {message['num1']}+{message['num2']} из RabbitMQ.")

    # Рассчитываем время получения сообщения относительно timestamp
    time_diff = (start_time_receive - float(message['timestamp'])) * 1000
    logger.info(f"Задержка получения сообщения: {time_diff:.3f} ms.")

    # Измеряем время выполнения операции сложения
    operation_start_time = time.time()
    result = message['num1'] + message['num2']
    operation_end_time = time.time()
    logger.info(f"Операция сложения выполнена за {(operation_end_time - operation_start_time)*1000:.3f} ms.")

    # Готовим ответ
    response = {
        'corr_id': corr_id,
        'result': result
    }

    # Измеряем время отправки ответа в RabbitMQ
    send_start_time = time.time()
    channel.basic_publish(
        exchange='',
        routing_key=reply_queue_name,
        body=json.dumps(response),
        properties=pika.BasicProperties(correlation_id=properties.correlation_id)
    )
    send_end_time = time.time()
    logger.info(f"Ответ отправлен в RabbitMQ за {(send_end_time - send_start_time)*1000:.3f} ms.")

    # Измеряем общее время обработки в приложении Б
    total_processing_time = time.time() - start_time_total
    logger.info(f"Общее время обработки в приложении Б: {total_processing_time*1000:.3f} ms.")

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
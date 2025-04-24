from kafka import KafkaProducer
import uuid
import json
import time
import os

# Параметры Kafka
bootstrap_servers = os.getenv('KAFKA_HOST', 'localhost:9092') # Адрес брокеров Kafka
topic = 'messages_topic'               # Название топика

# Создаем продюсера Kafka
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda m: json.dumps(m).encode('ascii')
)

# Количество сообщений для генерации
NUM_MESSAGES = 10001

for _ in range(NUM_MESSAGES):
    # Генерируем случайный GUID
    guid = str(uuid.uuid4())
    
    number = _
    
    # Формируем сообщение в формате JSON
    message = {'guid': guid, 'number': _}
    
    # Публикуем сообщение в Kafka
    future = producer.send(topic, message)
    result = future.get(timeout=10)
    print(f'Sent message: {message}')

    # Пауза между публикациями (опционально)
    #time.sleep(1)

# Завершаем работу продюсера
producer.flush()
producer.close()

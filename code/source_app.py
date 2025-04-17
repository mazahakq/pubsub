import os
import requests
import random
import time
from loguru import logger  # Быстрая библиотека логирования

# Читаем переменную окружения для частоты запросов
RATE_PER_SECOND = int(os.getenv('RATE_PER_SECOND', '2'))  # По умолчанию 2 запроса/сек
INTERVAL_BETWEEN_REQUESTS = 1 / RATE_PER_SECOND

# Адрес сервера App A
URL = 'http://app_a:8000/add'

# Настройка логгера Loguru
#logger.add("request_log.log", rotation="1 day", retention="1 week", enqueue=True)

while True:
    # Генерация двух случайных чисел
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)

    # Измерение времени начала запроса
    start_time = time.time()

    try:
        # Выполняем HTTP-запрос
        response = requests.post(URL, json={"num1": num1, "num2": num2})
        response.raise_for_status()  # Проверка статуса ответа

        # Измерение времени окончания запроса
        end_time = time.time()
        elapsed_time_ms = (end_time - start_time) * 1000  # Преобразование в миллисекунды

        # Вывод результатов в консоль и лог
        logger.info(f"Запрос: {num1}+{num2}; Ответ: {response.json().get('result')} ; Время отклика: {elapsed_time_ms:.3f} ms.")

    except requests.RequestException as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        continue  # Продолжаем следующий цикл

    # Задержка между запросами
    time.sleep(INTERVAL_BETWEEN_REQUESTS)

import threading
import os
import requests
import random
import time
from loguru import logger  # Быстрая библиотека логирования
from prometheus_client import Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from flask import Flask  # импортируем Flask
import sys  # импортируем sys

# Читаем переменную окружения для частоты запросов
RATE_PER_SECOND = int(os.getenv('RATE_PER_SECOND', '2'))  # По умолчанию 2 запроса/сек
INTERVAL_BETWEEN_REQUESTS = 1 / RATE_PER_SECOND

#API
API_ADDRESS = os.getenv('API_ADDRESS', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5001))

# Адрес сервера App A
SERVER_ADDRESS = os.getenv('SERVER_ADDRESS', 'http://app_a:8000')
URL = SERVER_ADDRESS + '/add'

# Prometheus metrics
SOURCE_REQUEST_COUNTER = Counter('source_request_count', 'Количество запросов от источника')
SOURCE_RESPONSE_TIME_HISTOGRAM = Histogram('source_response_time_histogram', 'Распределение времени ответа')

# Настройка логгера Loguru только для консольного вывода
logger.remove()  # Убираем предыдущие обработчики
logger.add(sys.stdout, colorize=True, format="{time} {level} {message}", backtrace=True, diagnose=True)

# Flask-приложение для экспорта метрик
app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# Основная логика генерации запросов
def generate_and_send_requests():
    while True:
        # Генерация двух случайных чисел
        num1 = random.randint(1, 10000)
        num2 = random.randint(1, 10000)

        # Измерение времени начала запроса
        start_time = time.time()

        try:
            # Выполняем HTTP-запрос
            response = requests.post(URL, json={"num1": num1, "num2": num2})
            response.raise_for_status()  # Проверка статуса ответа

            # Измерение времени окончания запроса
            end_time = time.time()
            elapsed_time_ms = (end_time - start_time) * 1000  # Преобразование в миллисекунды

            SOURCE_REQUEST_COUNTER.inc()  # Увеличение счетчика запросов
            SOURCE_RESPONSE_TIME_HISTOGRAM.observe(elapsed_time_ms / 1000)  # Сбор распределения времени обработки

            # Вывод результатов в консоль
            logger.info(f"Запрос: {num1}+{num2}; Ответ: {response.json().get('result')} ; Время отклика: {elapsed_time_ms:.3f} ms.")

        except requests.RequestException as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            continue  # Продолжаем следующий цикл

        # Задержка между запросами
        time.sleep(INTERVAL_BETWEEN_REQUESTS)

# Запускаем генерацию запросов в отдельном потоке
threading.Thread(target=generate_and_send_requests).start()

# Запускаем сервер Flask для экспорта метрик
if __name__ == "__main__":
    from waitress import serve
    serve(app, host=API_ADDRESS, port=API_PORT)  # Запускаем сервер на порту

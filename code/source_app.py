import requests
import random
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Адрес сервера App A
url = 'http://app_a:8000/add'

# Частота запросов (2 запроса в секунду)
rate_per_second = 2
interval_between_requests = 1 / rate_per_second

while True:
    # Генерация двух случайных чисел
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)

    # Измерение времени начала запроса
    start_time = time.time()

    try:
        # Выполняем HTTP-запрос
        response = requests.post(url, json={"num1": num1, "num2": num2})
        response.raise_for_status()  # Проверка статуса ответа

        # Измерение времени окончания запроса
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Вывод результатов в консоль
        print(f"Запрос: {num1}+{num2}; Ответ: {response.json().get('result')} ; Время отклика: {elapsed_time:.3f} сек.")

    except requests.RequestException as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        continue  # Продолжаем следующий цикл

    # Задержка между запросами
    time.sleep(interval_between_requests)

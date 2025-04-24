import { check } from 'k6';
import http from 'k6/http';

let SERVER_ADDRESS = __ENV.SERVER_ADDRESS || 'http://localhost:8000';

export let options = {
  scenarios: {
    constant_request_rate: {
      executor: 'constant-arrival-rate',
      rate: 10,              // Количество запросов в секунду (RPS)
      timeUnit: '1s',        // Интервал для расчета RPS
      duration: '2m',        // Общая продолжительность теста (2 минуты)
      preAllocatedVUs: 10,   // Начальное количество виртуальных пользователей
      maxVUs: 100            // Максимально возможное количество VU
    }
  }
};

export default function () {
  // Генерируем случайные числа между 1 и 10000 средствами стандартного JS
  const num1 = Math.floor(Math.random() * 10000) + 1;
  const num2 = Math.floor(Math.random() * 10000) + 1;

  const payload = JSON.stringify({ num1, num2 });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const response = http.post(`${SERVER_ADDRESS}/add`, payload, params);

  //console.log(`Response Status: ${response.status}`);
  //console.log(`Response Body: ${JSON.stringify(response.body)}`);

  check(response, {
    'status is 200': (res) => res.status === 200,
  });
}
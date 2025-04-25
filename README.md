Проект pubsub для тестирования передачи сообщений, архитектура  
```
- Приложение app_a принимает по api запрос (два числа) и публикует в очередь numbers_queue RabbitMQ полученное сообщение, ждет на него ответ от приложения app_b в очереди result_queue RabbitMQ
- Приложение app_b получает из очереди numbers_queue RabbitMQ сообщение (два числа), складывает их и отдает ответ для app_a в RabbitMQ через очередь result_queue
```

Каталоги:  
```
code - Каталог приложений
docker - Каталог сборок docker
dashboards - grafana dashboards
datasources - grafana datasources
flink - Конфигурации flink
haproxy - Конфигурации haproxy
prometheus - Конфигурации prometheus
```

Приложения:  
```
app_a.py - Приложение на python реализующее логику app_a
app_b.py - Приложение на python реализующее логику app_b
app_a_rpc.py - Приложение на python реализующее логику app_a через rpc взаимодействие
app_b_rpc.py - Приложение на python реализующее логику app_b через rpc взаимодействие
```

Приложения FLINK:  
```
Проект app_b_flink - https://github.com/mazahakq/app_b_flink реализует логику приложения app_b
Так же в данном проекте есть приложение app-b-flink-state которое реализует логику работы с flink state и поиском в нем данных при запросе через RabbitMQ
```

Приложения - Генераторы нагрузки:  
```
source_app.py - Приложение на python источник которое генерирует запросы в приложение app_a по api и посылает разные два числа, настройка rps через параметр RATE_PER_SECOND=100
source_app.js - Скрипт для k6 которое генерирует запросы в приложение app_a по api и посылает разные два числа, настройки нагрузки в скрипте параметры options
app_kafka_gen.py - Приложение на python которое генерирует сообщение содержащее number (число) по очереди и guid (случайный) после чего отправляет его в топик messages_topic kafka, настройки количества генерируемых записей в скрипте, параметр NUM_MESSAGES

```

Файлы сборки:  
```
app.Dockerfile - Сборка для приложений python
flink.Dockerfile - Сборка для flink
grafana.Dockerfile - Сборка для grafana
k6.Dockerfile - Сборка для k6
RabbitMQ.Dockerfile - Сборка для RabbitMQ
```

Файлы развертывания:  
```
docker-compose-app.yml - Развертывание приложения app_a и app_b
docker-compose-flink.yml - Развертывание Flink
docker-compose-generator.yml - Развертывание генераторов нагрузки
docker-compose-infra.yml - Развертывание инфраструктурных сервисов rabbitmq, prometheus, grafana, haproxy, influxdb, kafka, kafka-ui kafka-zookeeper
```

Пример развертывания окружения:  
```
#Развертываем инфраструктурные сервисы (haproxy нужно перезапустить после пересборки приложений)
docker-compose -f docker-compose-infra.yml up -d

#Развертываем Flink в случае тестирования flink приложений
docker-compose -f docker-compose-flink.yml up -d

#Развертываем приложений app_a.py
docker-compose -f docker-compose-app.yml --profile python_a  up -d

#Развертываем приложения app_b.py
docker-compose -f docker-compose-app.yml --profile python_b  up -d

#Развертываем приложений app_a_rpc.py
docker-compose -f docker-compose-app.yml --profile python_rpc_a  up -d

#Развертываем приложения app_b_rpc.py
docker-compose -f docker-compose-app.yml --profile python_rpc_b  up -d

#Развертываем генераторов нагрузки
docker-compose -f docker-compose-generator.yml --profile kafka_python  up -d
docker-compose -f docker-compose-generator.yml --profile source_python  up -d
docker-compose -f docker-compose-generator.yml --profile source_k6  up -d

```

Адреса сервисов:  
```
http://localhost:3000/ - Grafana (admin/admin)
http://localhost:9090/ - Prometheus
http://localhost:8080/ - Kafka-ui
http://localhost:15672/ - RabbitMQ (guest/guest)
http://localhost:8081/ - Flink
http://localhost:7000/stats - Haproxy Stats
```

Пример запроса в приложение А через curl:  
```
curl --location 'http://localhost:8000/add' \
--header 'Content-Type: application/json' \
--data '{
    "num1": 3,
    "num2": 200
}'
```
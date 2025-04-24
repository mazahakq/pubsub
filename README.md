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
```

Приложения - Генераторы нагрузки:  
```
source_app.py - Приложение на python источник которое генерирует запросы в приложение app_a по api и посылает разные два числа
source_app.js - Скрипт для k6 которое генерирует запросы в приложение app_a по api и посылает разные два числа
app_kafka_gen.py - Приложение на python которое генерирует сообщение содержащее number (число) по очереди и guid (случайный) после чего отправляет его в топик messages_topic kafka 

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

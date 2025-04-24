FROM rabbitmq:3.13.7-management
RUN rabbitmq-plugins enable --offline rabbitmq_management rabbitmq_prometheus
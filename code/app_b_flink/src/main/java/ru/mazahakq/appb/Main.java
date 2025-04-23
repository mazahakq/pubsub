package ru.mazahakq.appb;

import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.connectors.rabbitmq.common.RMQConnectionConfig;
import org.slf4j.LoggerFactory;
import org.apache.flink.streaming.connectors.rabbitmq.RMQSource;
import org.apache.flink.streaming.connectors.rabbitmq.RMQSink;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.time.Duration;
import java.time.Instant;
import org.slf4j.Logger;

public class Main {
    private static final Logger LOGGER = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Настройка конфигурации подключения к RabbitMQ
        RMQConnectionConfig connectionConfig = new RMQConnectionConfig.Builder()
            .setHost("rabbitmq")             // Хост RabbitMQ
            .setPort(5672)                   // Порт RabbitMQ
            .setUserName("guest")            // Пользователь
            .setPassword("guest")            // Пароль
            .setVirtualHost("/")             // Виртуальная среда
            .build();

        // Создаем отдельную зону для SOURCE
        DataStream<String> inputStream = env.addSource(new RMQSource<>(
            connectionConfig,                // Конфигурация подключения
            "numbers_queue",                 // Название очереди
            true,                            // Автоматическое подтверждение
            new SimpleStringSchema()         // Десериализатор (например, для строк)
        ));

        // Отдельная зона PROCESSING
        DataStream<String> resultStream = inputStream.map(message -> {
            Instant startTime = Instant.now(); // Начало обработки

            try {
                ObjectMapper mapper = new ObjectMapper();
                Map<String, Object> request = mapper.readValue(message, new TypeReference<Map<String, Object>>() {});
                int num1 = (int) request.get("num1");
                int num2 = (int) request.get("num2");
                String corrId = (String) request.get("corr_id");

                int result = num1 + num2;

                // Формируем ответ в формате JSON
                Map<String, Object> response = new HashMap<>();
                response.put("corr_id", corrId);
                response.put("result", result);

                Instant finishTime = Instant.now(); // Окончание обработки
                long durationMs = Duration.between(startTime, finishTime).toMillis(); //ms

                LOGGER.info("Processing time for message id '{}': {} ms", corrId, durationMs);

                return mapper.writeValueAsString(response);
            } catch (IOException e) {
                throw new RuntimeException("Error processing message", e);
            }
        });

        // Отдельная зона SINK
        resultStream.addSink(new RMQSink<>(
            connectionConfig,                // Конфигурация подключения
            "result_queue",                  // Название выходной очереди
            new SimpleStringSchema()         // Сериализатор
        ));

        // Выполнение задания
        env.execute("app_b");
    }
}
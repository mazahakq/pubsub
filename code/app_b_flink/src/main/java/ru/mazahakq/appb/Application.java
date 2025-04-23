package ru.mazahakq.appb;

import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

public class Application {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Добавляем источник данных из RabbitMQ
        RabbitMQSource source = new RabbitMQSource();
        DataStream<String> inputStream = source.createSource(env);

        // Обрабатываем полученные сообщения
        DataStream<JSONObject> processedStream = inputStream.map(new MessageProcessor());

        // Отправляем результаты обратно в RabbitMQ
        processedStream.addSink(new RabbitMQSink());

        // Запускаем выполнение задания
        env.execute("Flink PubSub Example");
    }
}
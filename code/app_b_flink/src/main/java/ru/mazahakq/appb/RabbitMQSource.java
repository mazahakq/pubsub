package ru.mazahakq.appb;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.connectors.rabbitmq.QueueingConsumer;
    
import com.rabbitmq.client.*;

import java.io.IOException;
import java.util.concurrent.TimeoutException;

public class RabbitMQSource {

    private static final String RABBITMQ_HOST = System.getenv("RABBITMQ_HOST") != null ? System.getenv("RABBITMQ_HOST") : "localhost";
    private static final String QUEUE_NAME = "numbers_queue";

    public DataStream<String> createSource(StreamExecutionEnvironment env) throws IOException, TimeoutException {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost(RABBITMQ_HOST);
        Connection conn = factory.newConnection();
        Channel channel = conn.createChannel();
        channel.queueDeclare(QUEUE_NAME, false, false, false, null);

        QueueingConsumer consumer = new QueueingConsumer(channel);
        channel.basicConsume(QUEUE_NAME, true, consumer);

        return env.addSource(new RabbitMQSourceFunction(consumer));
    }

    private static class RabbitMQSourceFunction extends org.apache.flink.streaming.connectors.rabbitmq.RMQSource<String> {
        public RabbitMQSourceFunction(QueueingConsumer consumer) {
            super(consumer, new DeserializationSchema());
        }
    }

    private static class DeserializationSchema implements org.apache.flink.streaming.connectors.rabbitmq.RMQDeserializationSchema<String> {
        @Override
        public String deserialize(byte[] bytes) throws IOException {
            return new String(bytes);
        }

        @Override
        public boolean isEndOfStream(String nextElement) {
            return false;
        }
    }
}

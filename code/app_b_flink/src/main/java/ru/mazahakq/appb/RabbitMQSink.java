package ru.mazahakq.appb;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.sink.RichSinkFunction;
import org.json.JSONObject;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeoutException;

public class RabbitMQSink extends RichSinkFunction<JSONObject> {

    private transient Connection connection;
    private transient Channel channel;
    private static final String REPLY_QUEUE_NAME = "result_queue";

    @Override
    public void open(Configuration parameters) throws Exception {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost(System.getenv("RABBITMQ_HOST"));
        this.connection = factory.newConnection();
        this.channel = connection.createChannel();
        channel.queueDeclare(REPLY_QUEUE_NAME, false, false, false, null);
    }

    @Override
    public void invoke(JSONObject value, Context context) throws Exception {
        byte[] responseBytes = value.toString().getBytes(StandardCharsets.UTF_8);
        try {
            channel.basicPublish("", REPLY_QUEUE_NAME, null, responseBytes);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void close() throws Exception {
        if (this.channel != null && this.channel.isOpen()) {
            this.channel.close();
        }
        if (this.connection != null && this.connection.isOpen()) {
            this.connection.close();
        }
    }
}
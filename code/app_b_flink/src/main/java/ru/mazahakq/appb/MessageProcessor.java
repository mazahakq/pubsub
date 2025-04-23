package ru.mazahakq.appb;

import org.apache.flink.api.common.functions.MapFunction;
import org.json.JSONObject;

public class MessageProcessor implements MapFunction<String, JSONObject> {

    @Override
    public JSONObject map(String value) throws Exception {
        // Преобразуем строку JSON в объект
        JSONObject message = new JSONObject(value);
        double num1 = message.getDouble("num1");
        double num2 = message.getDouble("num2");
        String corrId = message.getString("corr_id");

        // Выполняем операцию сложения
        double result = num1 + num2;

        // Формируем ответ
        return new JSONObject().put("corr_id", corrId).put("result", result);
    }
}
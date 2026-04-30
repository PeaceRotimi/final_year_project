package org.powertac.samplebroker.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
/**
 * bridging data between the Power TAC Broker and Redis
 * @authour Oluwatoni Rotimi-Fabolude
 *
 */


@Service
public class RedisBridge {
    @Autowired
    private StringRedisTemplate redisTemplate;

    public void sendToPython(String channel, String message){
        System.out.println("DEBUG: Sending to Redis [" + channel + "]: " + message);
        try {
            redisTemplate.opsForValue().set(channel, message);
        } catch (Exception e) {
            System.err.println("ERROR: Failed to send message to Redis on channel [" + channel + "]. " + e.getMessage());
        }
    }
}

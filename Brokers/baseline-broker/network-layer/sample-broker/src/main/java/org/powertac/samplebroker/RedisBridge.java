package org.powertac.samplebroker;
import org.springframework.stereotype.Service;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.StreamEntryID;
import java.util.Map;
import java.util.HashMap;

/**
 *
 *
 * a bridge allowing JSON messages from the Java netwrok layer to
 * be published to the blackboard for the AI core
 *
 * Using Singleton Pattern with Spring
 * @author Oluwatoni Rotimi-Fabolude
 */

@Service // one isntance of class

public class RedisBridge {
    private final Jedis jedis;

// Jedis connection for game

    public RedisBridge(){
        this.jedis = new Jedis("localhost", 6379);
    }

    // Jedis connection for testing

    public RedisBridge(Jedis jedis){
        this.jedis = jedis;

    }

    // adds JSON to Redis stream

    public void publish(String streamName,String message){
        if(message != null && !message.isEmpty()){
            Map<String, String> payload = new HashMap<>();
            payload.put("json",message);

            jedis.xadd(streamName,StreamEntryID.NEW_ENTRY,payload);
        }
    }


}

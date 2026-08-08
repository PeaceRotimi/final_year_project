package org.powertac.samplebroker;
import org.springframework.stereotype.Service;

import redis.clients.jedis.Jedis;

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

    // publishes redis messages if there is a message
    public void publish(String channel,String message){
        if(message != null && !message.isEmpty()){
            jedis.publish(channel, message);
        }
    }


}

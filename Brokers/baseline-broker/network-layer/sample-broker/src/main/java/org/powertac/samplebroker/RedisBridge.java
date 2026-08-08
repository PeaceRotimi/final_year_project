package org.powertac.samplebroker;
import redis.clients.jedis.Jedis;

/**
 *
 * @author
 * a bridge allowing JSON messages from the Java netwrok layer to
 * be published to the blackboard for the AI core
 *
 * @author Oluwatoni Rotimi-Fabolude
 */

public class RedisBridge {
    private final Jedis jedis;

    // Jedis connection

    public RedisBridge(Jedis jedis){
        this.jedis = jedis;

    }

    // publishes redis messages
    public void publish(String channel,String message){
        jedis.publish(channel, message);
    }


}

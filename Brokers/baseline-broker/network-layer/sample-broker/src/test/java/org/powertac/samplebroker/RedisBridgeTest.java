package org.powertac.samplebroker;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import redis.clients.jedis.Jedis;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.times;


public class RedisBridgeTest {
    @Test

    public void testPublishMessage(){

        //arrange: create fake Jedis object for testing and create bridge

        Jedis mockJedis = Mockito.mock(Jedis.class);

        RedisBridge bridge = new RedisBridge(mockJedis);

        // act: publish JSON string to channel

        String channel = "test-string";
        String jsonMessage = "{\"testJson\":10}";

        bridge.publish(channel,jsonMessage);

        //assert: Check if bridge sent the message and sent it once

        verify(mockJedis, times(1)).publish(channel, jsonMessage);
    }

}

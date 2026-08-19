package org.powertac.samplebroker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.StreamEntryID;
import redis.clients.jedis.resps.StreamEntry;

import static org.mockito.Mockito.verify;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.mock;


public class RedisBridgeTest {

    private Jedis mockJedis;
    private RedisBridge redisBridge;

    @BeforeEach
    public void setUp() {
        // Create a fake Jedis client so we don't need a real Redis server to run tests
        mockJedis = mock(Jedis.class);
        redisBridge = new RedisBridge(mockJedis);
    }

    @Test

    public void testPublishMessage(){

        //arrange: fake data

        String channel = "test-string";
        String jsonMessage = "{\"testJson\":10}";

        // act: publish JSON string to channel



        redisBridge.publish(channel,jsonMessage);

        //assert: Check if bridge sent the message and sent it once
        ArgumentCaptor<Map<String, String>> mapCaptor = ArgumentCaptor.forClass((Class) Map.class);

        Mockito.verify(mockJedis, times(1)).xadd(Mockito.eq(channel), Mockito.<StreamEntryID>eq(StreamEntryID.NEW_ENTRY) , mapCaptor.capture());

        Map<String, String> payload = mapCaptor.getValue();
        assertEquals(1, payload.size());
        assertEquals(jsonMessage, payload.get("json"));
    }

    @Test
    public void testPublishIgnoresEmptyMessages() {
        // act
        redisBridge.publish("weather-report", "");
        redisBridge.publish("weather-report", null);

        // assert

        verify(mockJedis, Mockito.never()).xadd(Mockito.anyString(), Mockito.<StreamEntryID>any(), Mockito.<Map<String, String>>any());
    }

}

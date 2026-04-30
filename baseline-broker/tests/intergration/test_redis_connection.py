import redis
import pytest
import os
import sys
from dotenv import load_dotenv
from infra.redis_manager import RedisBridge
import json



load_dotenv()

host = os.getenv('REDIS_HOST')
port= int(os.getenv('REDIS_PORT'))
db=int(os.getenv('REDIS_DB'))

@pytest.fixture
def clean_bridge():
    bridge = RedisBridge(host=host, port=port, db=db)
    yield bridge
    bridge.client.delete('test_timeslot')

#Test 1: test_redis_connection
def test_connection():
    #ARRANGE: set up connection
    con = redis.Redis(host=host, port=port)

    #ACT: ping connection
    response = con.ping()

    # ASSERT:check for reply
    assert response is True



# Test 2: test_write_data_and_verify
def test_read_and_write(clean_bridge):
    # Arrange: set up connection
    key = 'test_timeslot'
    value = 'rotterdam'
    clean_bridge.client.delete(key)


    # Act: Send data to Redis

    clean_bridge.write_state(key,value)

    # Assert: Check if data went to Redis db
    stored_value = clean_bridge.client.get(key)
    assert stored_value is not None
    assert b'rotterdam' in stored_value

#Test
def test_order_reaches_redis(clean_bridge):

    # Arrange: set up test data
    timeslot =  400
    energy_amount = 10.5
    limit_price = -30
    queue = "action_queue"

    clean_bridge.client.delete(queue)

    # Act: excute bid
    clean_bridge.send_market_order(timeslot,energy_amount,limit_price)

    # Assert:

    assert clean_bridge.client.llen(queue) == 1

    payload = clean_bridge.client.lindex(queue, 0)
    parsed = json.loads(payload)


    assert parsed["timeslot"] == timeslot
    assert parsed["energy_amount"] == energy_amount
    assert parsed["limit_price"] == limit_price

import redis
import pytest
import os
from dotenv import load_dotenv
from infra.redis_manager import RedisBridge

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
    con = redis. Redis(host=host, port=port)

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

    clean_bridge.write_state(key , value)

    # Assert: Check if data went to Redis db
    stored_value = clean_bridge.client.get(key)
    assert stored_value is not None
    assert b'rotterdam' in stored_value

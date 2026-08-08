import fakeredis
from main.stream_listener import StreamListener

def test_read_stream():
    # arrange - set up test redis connection and listener

    fake_stream = fakeredis.FakeStrictRedis(decode_responses=True)
    listener = StreamListener(redis_client=fake_stream, stream_name="weather-report")

    # fake data

    fake_stream.xadd("weather-report", {"json": '{"timeslotIndex": 400, "temperature": -20}'})

    # act  - read stream

    data = listener.read_latest()

    # assert
    # reads one message
    assert len(data) == 1
    stream_id, message = data[0]

    #check if message has been converted correctly

    assert message["timeslotIndex"] == 400
    assert message["temperature"] == -20

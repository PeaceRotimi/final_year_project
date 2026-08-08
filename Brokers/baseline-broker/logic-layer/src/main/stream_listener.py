import redis
import json

class StreamListener:
    def __init__(self,stream_name,redis_client=None,last_id="0-0"):
        self.redis_client = redis_client
        self.stream_name =stream_name
        self.last_id = last_id

    # reads stream

    def read_latest(self):
        # read unread items
        messages = self.redis_client.xread({self.stream_name:self.last_id},count = 10, block= 1000)

        stream_messages = []

        if not messages:
            return stream_messages

        for stream, message in messages:
            for message_id, data in message:
                self.last_id = message_id
                payload = json.loads(data["json"])
                stream_messages.append((message_id,payload))

        return stream_messages

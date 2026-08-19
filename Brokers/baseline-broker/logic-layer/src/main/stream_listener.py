import redis
import json

class StreamListener:
    def __init__(self,streams,redis_client=None):
        self.redis_client = redis_client
        self.streams =streams

    # reads stream

    def read_latest(self):
        # read unread items
        messages = self.redis_client.xread(self.streams,count = 10, block= 1000)
        #print(f"redis response {messages}")

        stream_messages = []

        if not messages:
            return stream_messages

        for stream_name, message_list in messages:
            for message_id, data in message_list:
                self.streams[stream_name] = message_id
                if isinstance(data, dict):
                    raw_payload = data.get("json") or data.get("payload") or data
                else:
                    raw_payload = data

                if isinstance(raw_payload, str):
                    try:
                        payload = json.loads(raw_payload)
                    except json.JSONDecodeError:
                        payload = raw_payload
                else:
                    payload = raw_payload

                stream_messages.append((stream_name, message_id, payload))

        return stream_messages

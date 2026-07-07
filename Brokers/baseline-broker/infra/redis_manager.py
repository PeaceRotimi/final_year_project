import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()


class RedisBridge:
    def __init__(self, host=None, port=None, db=None):

        # connecting to redis
        self.host= os.getenv('REDIS_HOST')
        self.port= int(os.getenv('REDIS_PORT'))
        self.db= int(os.getenv('REDIS_DB'))

        self.client = redis.Redis(
            host = self.host,
            port=self.port,
            db=int(self.db)
        )

    # write data to redis
    def write_state(self, key:str, json_data: str):
        self.client.set(key, json_data)

    # reads data from redis
    def read_state(self, key:str):
        data = self.client.get(key)

        return data.decode('utf-8') if data else None

    def send_market_order(self,timeslot,energy_amount,limit_price):
        # constructs an order for Power TAC
        order = {
            "timeslot": timeslot,
            "energy_amount" : energy_amount,
            "limit_price" : limit_price
        }


        result = self.client.rpush("action_queue", json.dumps(order))

        print(f"DEBUG: Python pushed order. Queue length is now: {result}")
        return result

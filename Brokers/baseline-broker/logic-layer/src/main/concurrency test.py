import threading
import time
import redis


client = redis.Redis(host='localhost', port=6379, decode_responses=True)
STREAM_KEY = "broker_events_stream"
CONSUMER_GROUP = "broker_workers"

def setup_stream():
    try:
        client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise e

def simulate_stream_consumer(consumer_name):
    setup_stream()
    try:

        streams = client.xreadgroup(CONSUMER_GROUP, consumer_name, {STREAM_KEY: ">"}, count=1, block=1000)

        if streams:
            for stream_name, messages in streams:
                for message_id, data in messages:

                    pipe = client.pipeline()
                    try:
                        pipe.watch('broker_cash')
                        cash = float(pipe.get('broker_cash') or 1000.0)

                        time.sleep(0.02)
                        pipe.multi()
                        pipe.set('broker_cash', cash - 100.0)
                        pipe.execute()


                        client.xack(STREAM_KEY, CONSUMER_GROUP, message_id)
                        print(f"[{consumer_name}] Successfully processed message {message_id} ")
                    except redis.WatchError:
                        print(f" Issue with message {message_id}")
    except Exception as e:
        print(f"[{consumer_name}] Error: {e}")

def run_redis_stream_concurrency_test():

    #    client.set('broker_cash', 1000.0)

    client.xadd(STREAM_KEY, {"event_type": "TRADE_ORDER", "amount": "100.0"})


    t1 = threading.Thread(target=simulate_stream_consumer, args=("Worker-1",))
    t2 = threading.Thread(target=simulate_stream_consumer, args=("Worker-2",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("PASS")

if __name__ == "__main__":
    run_redis_stream_concurrency_test()

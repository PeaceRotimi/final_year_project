import redis

client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class StateManager:
    def __init__(self, r_client):
        self.r = r_client

    def save(self, data):
        pipe = self.r.pipeline()
        for k, v in data.items():
            pipe.set(f"state:{k}", v)
        pipe.execute()

    def load(self, keys):
        result = {}
        for k in keys:
            val = self.r.get(f"state:{k}")
            if val is not None:
                result[k] = float(val) if '.' in val else int(val)
        return result

def test_recovery():
    state = {"cash": 1250.75, "price": 40.20, "fee": 0.0}
    keys = list(state.keys())

    try:
        mgr = StateManager(client)
        mgr.save(state)

        del mgr  # Simulate crash

        recovered = StateManager(client).load(keys)
        assert state == recovered
        print("Status: PASS")
    except Exception:
        print("Status: FAIL")
    finally:
        for k in keys:
            client.delete(f"state:{k}")

if __name__ == "__main__":
    test_recovery()

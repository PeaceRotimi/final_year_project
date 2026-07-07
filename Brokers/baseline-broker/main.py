import redis
import json
import os
from dotenv import load_dotenv


from forecasting.price_forecast import PriceForecast
from forecasting.load_forecast import LoadForecast

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
pubsub = r.pubsub()

pubsub.subscribe([
    "competion_info",
    "distribution_report",
    "tariff_transaction",
    "cleared_trade",
    "tariff_specification"
])



price_forecaster = PriceForecast(window_size=24, default_price=0.04)
load_forecaster = LoadForecast()

TARGET_MARGIN = 0.02
active_tariffs = {}
lowest_comp_rate = float('inf')
initial_tariff_created = False
timeslot_churn = 0
current_wholesale_price = 0.0

active_tariff = {
    "id": None,
    "rate": 0.0
}


def new_tariff(power_type: str, rate_value: float, periodic_payment: float):
    payload = {
        "action": "CREATE",
        "powerType": power_type,
        "rateValue": rate_value,
        "periodicPayment": periodic_payment
    }
    r.publish("broker_commands", json.dumps(payload))

def supersede_tariff(power_type: str, rate_value: float, periodic_payment: float):
    if active_tariff["id"] is None:

        return

    payload = {
        "action": "SUPERSEDE",
        "powerType": power_type,
        "rateValue": rate_value,
        "periodicPayment": periodic_payment,
        "supersedesId": active_tariff["id"]
    }
    r.publish("broker_commands", json.dumps(payload))
    print(f" Supersede tariff: {payload}")


    active_tariff["rate"] = rate_value

def revoke_tariff(tariff_id: int):
    payload = {
        "action": "REVOKE_TARIFF",
        "tariffId": tariff_id
    }
    r.publish("broker_commands", json.dumps(payload))
    print(f" Revoke tariff: {payload}")

def create_initial_tariffs():

    expected_price = price_forecaster.add_price(current_rate)
    starting_rate = -(expected_price * 1.20)

    new_tariff("CONSUMPTION", starting_rate, -2.0)
    active_tariff["rate"] = starting_rate




for message in pubsub.listen():
    if message["type"] == "message":
        channel = message["channel"]
        data = json.loads(message["data"])

        if channel == "competion_info":
            if not initial_tariff_created:
                create_initial_tariffs()
                initial_tariff_created = True

        elif channel == "cleared_trade":

            execution_price = data.get("executionPrice", 0.0) / 1000.0
            current_wholesale_price = execution_price
            price_forecaster.add_price(execution_price)

        elif channel == "tariff_specification":
            if data.get("broker", {}).get("username") != "YourBrokerName":
                power_type = data.get("powerType")

                if power_type == "CONSUMPTION":
                    rates = data.get("rates", [])
                    if rates:
                        comp_rate = abs(rates[0].get("value", 0.0))
                        if comp_rate < lowest_comp_rate:
                            lowest_comp_rate = comp_rate

        elif channel == "tariff_transaction":
            tx_type = data.get("txType")
            if tx_type == "WITHDRAW" and data.get("tariffSpec", {}).get("id") == active_tariff["id"]:
                timeslot_churn += data.get("customerCount", 1)

        elif channel == "distribution_report":

            current_rate = abs(float(active_tariff["rate"]))
            predicted_cost = price_forecaster.predict()


            if current_rate < current_wholesale_price:
                safe_rate = -(predicted_cost + TARGET_MARGIN)
                supersede_tariff("CONSUMPTION", safe_rate, -2.0)
                timeslot_churn = 0
                continue


            if timeslot_churn > 50:
                low_rate = current_rate - 0.01
                if low_rate > predicted_cost:
                    supersede_tariff("CONSUMPTION", -low_rate, -2.0)
                timeslot_churn = 0
                continue


            if lowest_comp_rate < current_rate:
                undercut_rate = lowest_comp_rate - 0.001
                if undercut_rate >= (predicted_cost + TARGET_MARGIN):
                    supersede_tariff("CONSUMPTION", -undercut_rate, -2.0)


            timeslot_churn = 0

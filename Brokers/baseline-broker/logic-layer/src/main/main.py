import redis
from stream_listener import StreamListener
import json
from datetime import datetime, timedelta

from forecasters.demand_forecaster import DemandForecaster
from forecasters.price_forecaster import PriceForecaster
from forecasters.renewable_forecaster import RenewableForecaster
from forecasters.revenue_forecaster import RevenueForecaster

from decision_engine.retail_engine import RetailEngine
from decision_engine.wholesale_engine import WholesaleEngine
from decision_engine.balancing_engine import BalancingEngine

from broker_logger import BrokerLogger

def run():

    # instantiated Forecaster
    demand_model = DemandForecaster()
    price_model = PriceForecaster()
    wind_model = RenewableForecaster()
    solar_model = RenewableForecaster()
    revenue_model = RevenueForecaster()

    # instantied descion engine

    retail = RetailEngine()
    wholesale = WholesaleEngine()
    balancing = BalancingEngine()
    logger = BrokerLogger()

    current_timeslot = 0
    simulation_basetime = None

    # placeholder values to prevent errors
    cash = 100000.0
    comp_price = 0.15


    # running stream listener
    my_redis = redis.Redis(host='localhost', port=6379, decode_responses=True)

    listener = StreamListener(
        streams={
            "game-state":"0-0",
            "weather-report":"0-0",
            "wholesale-market":"0-0",
            "customer-usage":"0-0",
            "bank-transactions":"0-0"
        },
        redis_client=my_redis
    )

    print("Listening for Server messages")


    try:
        while True:

            new_messagaes = listener.read_latest()

            for stream_name, message_id, payload in new_messagaes:

                print(f"Read message from stream: {stream_name}")

                data = json.loads(payload) if isinstance(payload,str) else payload
                commands_to_send = []


                if stream_name == "game-state":
                    if "timeslotIndex" in data:
                        current_timeslot = data["timeslotIndex"]

                    if "bankBalance" in data :
                        cash = data["bankBalance"]

                    if "simulationBaseTime" in data:

                        time = data["simulationBaseTime"].replace('Z','')
                        simulation_basetime = datetime.fromisoformat(time)
                        print(f"Simulation started: {simulation_basetime.strftime('%A')}")

                    if "bootstrapData" in data:
                        bootstrap_prices = data["bootstrapData"].get("clearingPrices",[])
                        price_model.load_bootstrap(bootstrap_prices)

                        print("Loaded bootstrap prices")


                    # Decision making pipeline

                elif stream_name == "weather-report":
                    if simulation_basetime is None:
                        simulation_basetime = datetime(2021,1,1)

                    if current_timeslot < 360:
                        print("skip")
                        continue
                    try:
                        temp = data.get("temperature",0.0)
                        wind_speed = data.get("windSpeed",0.0)
                        cloud_cover = data.get("cloudCover",0.0)
                        wind_dir = data.get("windDirection",0.0)

                        # process time and date details

                        current_time = simulation_basetime + timedelta(hours=current_timeslot)
                        hour = current_time.hour

                        if(current_time.weekday() >= 5):
                                is_weekend = 1
                        else:
                                is_weekend = 0

                        demand_features = [[temp,hour,is_weekend,cloud_cover]]
                        wind_features = [[wind_speed,wind_dir,]]
                        solar_features = [[cloud_cover,hour,temp]]

                        # generate prediction
                        predicted_demand = demand_model.predict(demand_features)
                        predicted_wind = wind_model.predict(wind_features)
                        predicted_solar = solar_model.predict(solar_features)
                        predicted_price = price_model.predict(periods_ahead=24)

                        print(f"Demand Prediction : {predicted_demand}")
                        print(f"Wind Prediction : {predicted_wind}")
                        print(f"Solar Prediction : {predicted_solar}")
                        print(f"Price Prediction : {predicted_price}")

                        # wholesale bidding

                        for i in range(1,25):
                            target_ts = current_timeslot + i
                            est_price = predicted_price[i-1] if i-1 < len(predicted_price) else 0.05

                            bid = wholesale.bid_wholesale_market(
                                current_timeslot=current_timeslot,
                                target_timeslot = target_ts,
                                demand_forecast=predicted_demand,
                                wind_forecast= predicted_wind,
                                solar_forecast=predicted_solar,
                                predicted_price_mean=est_price
                            )

                            print(f"DEBUG: Timeslot {target_ts} Bid Object: {bid}")

                            if bid:
                                commands_to_send.append(bid)
                                print(f" Submitting bids - {bid['amount']}")
                            else:
                                print(f"No Power needed")

                        # tariff

                        if current_timeslot % 24 == 0:
                            current_pred_price = predicted_price[0] if len(predicted_price) > 0 else 0.05
                            retail_cmds = retail.evaluate_tariffs(current_timeslot,revenue_model, comp_price,current_pred_price,cash)
                            commands_to_send.extend(retail_cmds)

                        # balancing engine

                        cleared = wholesale.cleared_energy.get(current_timeslot,0.0)
                        shortfall = predicted_demand - (predicted_wind + predicted_solar + cleared)
                        est_imbalance = -shortfall

                        active_tariff = [t["id"] for t  in retail.active_tariffs]

                        if active_tariff:
                            balance_cmds = balancing.manage_imbalance(active_tariff,est_imbalance)
                            commands_to_send.extend(balance_cmds)

                    # timeslot
                    except Exception as e:
                        print(f"{timeslot} - using failsafe")
                        import traceback
                        traceback.print_exc()
                        commands_to_send = []

                        for i in range(1,5):
                            target_ts = current_timeslot + i
                            commands_to_send.append({
                                "action": "submit_order",
                                "timeslot": target_ts,
                                "amount":5.0,
                                "limitPrice":0.08
                                })

                    for cmd in commands_to_send:
                        my_redis.xadd("broker-commands", {"json":json.dumps(cmd)})

                        if current_timeslot % 24 == 0:
                            logger.log(
                                timeslot=current_timeslot,
                                cash = cash,
                                no_tariffs= len(retail.active_tariffs),
                                comp_price=comp_price,
                                esti_imbalance=est_imbalance,
                                cleared_energy= cleared
                            )

                elif stream_name == "wholesale-market":
                    clearing_price = data.get("clearingPrice",0.0)
                    clearing_volume = data.get("clearedVolume",0.0)
                    ts = data.get("timeslotIndex", current_timeslot)

                    price_model.add_price(clearing_price)
                    wholesale.track_transaction(ts,clearing_volume)


                elif stream_name == "tariff-market":

                    # track in tariff
                    if "TariffSpecification" in data:
                        if data.get("brokerName") == "MyBroker":

                            retail.active_tariffs.append({
                                "id": data["tariffId"],
                                "price": data.get("periodicPayment",0.0),
                                "exit_fee": data.get("earlyWithdrawPayment",0.0)
                            })
                        else:
                            comp_price = data.get("periodicPayment",0.0)

                 # track revoked tariffs

                    elif "TariffRevoke" in data:
                        if data.get("brokerName") == "MyBroker":
                            revoke_id = data["tariffId"]

                            retail.active_tariff = [t for t in retail.active_tariffs if t["id"] != revoke_id]
                            print(f"revoked tariff {revoke_id}")

                    elif "TariffTransaction" in data:
                        tx_type = data.get("txType")
                        if tx_type in ["SIGNUP","WITHDRAW"]:
                            did_join = 1 if tx_type == "SIGNUP" else 0
                            tariff_id = data.get("tariff_id")

                            real_price = None
                            real_exit_fee = None

                            for t in retail.active_tariffs:
                                if t["id"] == tariff_id:
                                    real_price = t["price"]
                                    real_exit_fee = t["exit_fee"]

                            if real_price is not None:
                                revenue_model.observe_market(
                                    price= real_price,
                                    comp_price=comp_price,
                                    exit_fee=real_exit_fee,
                                    join=did_join
                                )



    except KeyboardInterrupt:
        print("Stream Listener closed")

if __name__ =="__main__":
    run()

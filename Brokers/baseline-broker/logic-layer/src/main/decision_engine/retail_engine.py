import redis
from pricing_strategies import ProfitMaximizationStrategy, MOOParetoStrategy

class RetailEngine:
    def __init__(self, redis_client, strategy=None):
        self.redis_client = redis_client
        self.active_tariffs = []
        self.min_profit_margin = 0.02
        self.improvement_threshold = 1.15

        # Default to the MOO strategy
        self.strategy = strategy if strategy else MOOParetoStrategy()

        #  fee to publish new tariffs
        self.publication_fee = 500.0

    def evaluate_tariffs(self, timeslot, revenue_model, comp_price, wholesale_cost):
        commands = []


        best_price, best_exit_fee, max_revenue = self.strategy.generate_optimal_parameters(
            wholesale_cost, comp_price, revenue_model
        )

        #
        publish = True
        if len(self.active_tariffs) > 0:
            current_best_revenue = 0.0
            for tariff in self.active_tariffs:
                current_features = [[tariff['price'], comp_price, tariff['exit_fee']]]
                current_share = revenue_model.predict(current_features)[0]
                current_exit_fee = -(tariff['exit_fee'] / 2.0)
                current_revenue = ((tariff['price'] - wholesale_cost) * current_share) + (tariff['exit_fee'] * 0.05 + current_exit_fee)

                if current_revenue > current_best_revenue:
                    current_best_revenue = current_revenue

            # only publish if 15% better than current tariff
            if max_revenue < (current_best_revenue * self.improvement_threshold):
                publish = False
                print(f"{timeslot} - not publishing any tariffs in this timeslot")


        if publish:
            pipeline = self.redis_client.pipeline()
            try:
                pipeline.watch('broker_cash')
                current_cash = float(pipeline.get('broker_cash') or 0.0)

                # Check if we can afford the publication fee
                if current_cash < self.publication_fee:
                    print(f"{timeslot} - Aborting publish: Insufficient funds (TOCTOU prevention).")
                    pipeline.unwatch()
                    return commands # Return empty, safely aborting

                # Commit the transaction safely
                pipeline.multi()
                # Deduct the fee locally so other modules know the cash is spent
                pipeline.set('broker_cash', current_cash - self.publication_fee)
                pipeline.execute()

            except redis.WatchError:
                print(f"{timeslot} - Collision detected: Cash altered by another thread. Aborting.")
                return commands


            print(f"{timeslot} Price = {best_price:.2f}, exit fee {best_exit_fee:.2f}")

            # Standard Tariff
            commands.append({
                "action": "publish_tariff",
                "powerType": "CONSUMPTION",
                "periodicPayment": best_price,
                "signupPayment": -(best_exit_fee / 2.0),
                "earlyWithdrawPayment": best_exit_fee
            })


            commands.append({
                "action": "publish_tariff",
                "powerType": "CONSUMPTION",
                "periodicPayment": 0.0,
                "signupPayment": -(best_exit_fee / 2.0),
                "earlyWithdrawPayment": best_exit_fee,
                "rates": [
                    {"value": best_price * 0.9, "dailyBegin": 7, "dailyEnd": 16},
                    {"value": best_price * 1.5, "dailyBegin": 17, "dailyEnd": 23},
                    {"value": best_price * 0.7, "dailyBegin": 0, "dailyEnd": 6}
                ]
            })

            # Solar production
            solar_payout = -(wholesale_cost * 0.80)
            commands.append({
                "action": "publish_tariff",
                "powerType": "SOLAR_PRODUCTION",
                "periodicPayment": solar_payout,
                "signupPayment": 0.0,
                "earlyWithdrawPayment": 0.0
            })

            # Wind production
            wind_payout = -(wholesale_cost * 0.75)
            commands.append({
                "action": "publish_tariff",
                "powerType": "WIND_PRODUCTION",
                "periodicPayment": wind_payout,
                "signupPayment": 0.0,
                "earlyWithdrawPayment": 0.0
            })

            # Revoke old tariffs
            remaining_tariff = []
            for tariff in self.active_tariffs:
                if tariff['price'] < wholesale_cost:
                    print(f"{timeslot} - revoking tariff {tariff['id']}")
                    commands.append({
                        "action": "revoke_tariff",
                        "tariffId": tariff['id']
                    })
                else:
                    remaining_tariff.append(tariff)
            self.active_tariffs = remaining_tariff

        return commands

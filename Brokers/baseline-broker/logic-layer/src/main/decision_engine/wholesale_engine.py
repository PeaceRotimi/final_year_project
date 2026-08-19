import random

class WholesaleEngine:
    def __init__(self):
        # always buy 5% extra power to prevent balancing penalties
        self.safety_buffer = 1.05
        # tracks sucessfully bought or sold energy for future timeslot
        self.cleared_energy = {}

    def track_transaction(self,timeslot,cleared_amount):
        if timeslot not in self.cleared_energy:
            self.cleared_energy[timeslot] =0.0
        self.cleared_energy[timeslot] += cleared_amount

    def bid_wholesale_market(self, current_timeslot, target_timeslot, demand_forecast, wind_forecast, solar_forecast,predicted_price_mean, predicted_price_std=0.01):
        # calculate energy need and place Gaussian bid

        # buy power
        net_demand = demand_forecast - (wind_forecast + solar_forecast)

        if net_demand > 0:
            net_demand = net_demand * self.safety_buffer

        cleared = self.cleared_energy.get(target_timeslot,0.0)

        shortfall = net_demand - cleared

        if abs(shortfall) <= 0.1:
            return None

        # Urgency

        hours_ahead = target_timeslot - current_timeslot

        if shortfall > 0:
            if hours_ahead > 16:
                target_price = predicted_price_mean - (1.0 * predicted_price_std)
                limit_price = random.gauss(target_price,predicted_price_std *0.2)
            elif hours_ahead> 6:
                 limit_price = random.gauss(predicted_price_mean, predicted_price_std *0.1)
            else:
                target_price = predicted_price_mean + (2.0 * predicted_price_std)
                limit_price = random.gauss(target_price,predicted_price_std*0.5)

            limit_price = max(0.001,limit_price)

            return{
                "action": "submit_order",
                "timeslot": target_timeslot,
                "amount": shortfall,
                "limitPrice": limit_price
            }

        # sell power
        elif shortfall < 0:

            surplus_amount =abs(shortfall)

            if hours_ahead > 16:
                target_price = predicted_price_mean - (1.0 * predicted_price_std)
                limit_price = random.gauss(target_price,predicted_price_std *0.2)
            elif hours_ahead> 6:
                 limit_price = random.gauss(predicted_price_mean, predicted_price_std *0.1)
            else:
                target_price = predicted_price_mean + (2.0 * predicted_price_std)
                limit_price = random.gauss(target_price,predicted_price_std*0.5)

            limit_price = max(0.001,limit_price)

            return{
                "action": "submit_order",
                "timeslot": target_timeslot,
                "amount": -surplus_amount,
                "limitPrice": limit_price
            }
        return None

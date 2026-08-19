import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# using holts winters statisitcal model to determine price

class PriceForecaster:
    # only keep 30 days worth of historical prices at once
    def __init__(self, max_history= 720):
        self.model = None
        self.past_prices = []
        self.max_history = max_history

    def load_bootstrap(self, bootstrap_prices):

        # get bootstrap prices

        self.past_prices.extend(bootstrap_prices)
        self.past_prices = self.past_prices[-self.max_history:]

    def add_price(self,current_price):

        self.past_prices.append(current_price)

        if len(self.past_prices)> self.max_history:
            self.past_prices.pop(0)

        self.past_prices = self.past_prices[-self.max_history:]

    def predict(self,periods_ahead=24):

        try:

            if len(self.past_prices) >= 48:
                self.model = ExponentialSmoothing(
                    self.past_prices,
                    trend='add',
                    seasonal='add',
                    seasonal_periods=24
                ).fit(optimized=True)

                return self.model.forecast(periods_ahead).tolist()
        except Exception:
            pass

        fallback_price = self.past_prices[-1] if self.past_prices else 0.05
        return [fallback_price] * periods_ahead

from collections import deque

class PriceForecast:
    def __init__(self, window_size=24, default_price=-30.0):
        self.price_history = deque(maxlen=window_size)
        self.default_price = default_price

    def add_price(self, execution_price):
        self.price_history.append(execution_price)

    def predict(self):

        if len(self.price_history) < 5:
            return self.default_price


        return sum(self.price_history) / len(self.price_history)

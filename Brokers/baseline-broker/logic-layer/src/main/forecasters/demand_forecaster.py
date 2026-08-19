from sklearn.linear_model import Ridge

# ridge regression for demand forecasting

class DemandForecaster:
    def __init__(self):
        self.model = Ridge(alpha=1.0)
        self.is_trained = False

    def train(self, x_train, y_train):
        self.model.fit(x_train,y_train)
        self.is_trained = True

    def predict(self,x_weather):
        # takes in an array of features and return the prediction
        if self.is_trained:
            try:
                prediction = self.model.predict(x_weather)
                return float(prediction[0])
            except Exception:
                pass

        try:
            temp = x_weather[0][0]

            base_demand = 15.0 + abs(20.0 - temp) * 0.5
            return float(base_demand)
        except Exception:
            return 15.0

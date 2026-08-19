from sklearn.ensemble import RandomForestRegressor

class RenewableForecaster:

    # random forest that can work for both wind and solar forecasting
    def __init__(self):

        self.model = RandomForestRegressor(n_estimators=50,max_depth=10,random_state=10)
        self.is_trained = False

    def train(self, Xtrain,ytrain):

        self.model.fit(Xtrain,ytrain)
        self.is_trained = True

    def predict(self, X_test):

        if not self.is_trained:
            try:
                return float(self.model.predict(x_features)[0])
            except Exception:
                pass

        return 5.0

import numpy as np
from sklearn.linear_model import LogisticRegression

class RevenueForecaster:
    def __init__(self):
        self.model = LogisticRegression(multi_class='multinomial',solver='lbfgs')
        self.is_trained = False

        self.history_X = []
        self.history_Y = []

    # fake data to make first decision in the first timeslot
    def mock_data(self):
        X_train = np.array([
            [0.10,0.15,0.0],
            [0.25, 0.10,50.0],
            [0.12, 0.12 , 0.0],
            [0.05,0.20,10.0]
        ])

        y_train = np.array([1,0,1,0])

        self.train(X_train, y_train)


    def train(self,X_train,y_train):

        self.model.fit(X_train, y_train)
        self.is_trained = True

    def observe_market(self,price,comp_price,exit_fee,join):

        # history of past tariffs
        self.history_X.append([our_price,comp_price,exit_fee])
        self.history_Y.append(join)

        # keeps 500 events
        if len(self.history_X)> 500:
            self.history_X.pop(0)
            self.history_Y.pop(0)

        # retrains every 50
        if len(self.history_X) >= 50 and len(self.history_X) % 50 == 0:
            self.train(np.array(self.history_X),np.array(self.history_Y))


    def predict(self,X_price):

        if not self.is_trained:
            self.mock_data()

        probabilities = self.model.predict_proba(X_price)

        prob = probabilities[0][1]

        return [prob,1.0- prob]

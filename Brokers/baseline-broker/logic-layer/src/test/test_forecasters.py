import pytest
import numpy as np

from forecasters.demand_forecaster import DemandForecaster
from forecasters.price_forecaster import PriceForecaster
from forecasters.renewable_forecaster import RenewableForecaster
from forecasters.revenue_forecaster import RevenueForecaster



def test_demand_untrained():

    #Arrange
    model = DemandForecaster()
    y_values = [[1.0,1.0,1.0,1.0]]

    #act

    prediction = model.predict(y_values)

    #assert - if not trained prediction returns 0
    assert prediction == 0.0

def test_demand_trained():
    #arrange

    model = DemandForecaster()

    x_train = [[1.0,1.0,1.0,1.0],[2.0,2.0,2.0,2.0],[3.0,3.0,3.0,3.0]]
    y_train = [4.0,4.0,4.0]
    model.train(x_train,y_train)
    x_weather = [[5.0,5.0,5.0,5.0]]

    # act
    prediction = model.predict(x_weather)

    #assert - check models is trained and that the prediction is a float
    assert model.is_trained == True
    assert isinstance(prediction,float)

def test_price_bootstrap():
    # arrange
    model = PriceForecaster(max_history=720)
    # populate 48
    fake_bootstrap = [40.0 + (i % 24) for i in range (50)]

    #act
    model.load_bootstrap(fake_bootstrap)

    #assert
    assert len(model.past_prices) == 50

def test_price_max_history():
    # arrange - set max of 50

    model = PriceForecaster(max_history=50)
    large_bootstrap = [5.0]*200

    # act

    model.load_bootstrap(large_bootstrap)

    # assert - the past price array should have a length of 50

    assert len(model.past_prices) == 50

def test_price_add_price():

    # Arrange
    model = PriceForecaster(max_history=720)
    model.load_bootstrap([40.0,41.0,42.0])

    #Act
    model.add_price(55.0)

    #Assert

    assert len(model.past_prices)== 4
    assert model.past_prices[-1]  == 55.0

    # check if add_price appends to past_prices
def test_window():
    # Arrange
    model = PriceForecaster(max_history=3)
    model.load_bootstrap([20.0,30.0,40.0])

    #act
    model.add_price(50.0)

    #assert
    # check window works
    assert len(model.past_prices) == 3
    # check that past price was dropped
    assert model.past_prices == [30.0,40.0,50.0]

def test_forecast_length():
    # Arrange
    model = PriceForecaster(max_history=720)
    bootstrap = [40.0 + (i%24) for i in range(48)]
    model.load_bootstrap(bootstrap)

    #Act

    forecast = model.predict(periods_ahead=24)

    # Assert
    assert len(forecast) ==24
    assert isinstance(forecast[0],float)

def test_renewable_untrained():

    #arrange

    model = RenewableForecaster()


    #Assert - checks if model won't run untrained
    assert model.is_trained is False

def test_renewable_pretraining():
    # arrange

    model = RenewableForecaster()
    test_data = [[10.0,20.0,30.0,40.0]]

    #act
    prediction = model.predict(test_data)

    # assert - returns 0

    assert prediction == 0.0

def test_renewable_trained():
    #Arrange

    model = RenewableForecaster()

    x_train = [[10.0,15.0,20.0],[25.0,30.0,35.0],[40.0,45.0,55.0]]

    y_train = [30.0,40.0,50.0]

    #Act

    model.train(x_train,y_train)

    # Assert

    assert model.is_trained is True

def test_renewable_float():

    #Arrange

    model = RenewableForecaster()
    X_train = [[10.0,15.0,20.0],[25.0,30.0,35.0],[40.0,45.0,55.0]]

    y_train = [30.0,40.0,50.0]

    model.train(X_train,y_train)

    #Act

    x_test = [[20.0,30.0,40.0]]
    prediction = model.predict(x_test)

    # assert
    assert isinstance(prediction,float)

def test_revenue_float():
    model = RevenueForecaster()

    assert model.is_trained is False

def test_revenue_pretraining():
    # arrange
    model = RevenueForecaster()
    test_price = [[30.0]]

    # act
    prediction = model.predict(test_price)

    #assert
    assert prediction == [0.5,0.5]

def test_revenue_trained():
    #arrange
    model = RevenueForecaster()

    X_train = [[20.0],[30.0],[40.0],[50.0]]

    y_train = [0,1,0,1]

    # act
    model.train(X_train,y_train)

    #assert
    assert model.is_trained is True

def test_revenue_returns_valid():

    #arrange
    model = RevenueForecaster()
    X_train = [[20.0],[30.0],[40.0],[50.0]]

    y_train = [0,1,0,1]

    model.train(X_train,y_train)

    # act
    X_test = [[30.0]]
    prediction = model.predict(X_test)

    # assert
    # returns an array of 2 probablities
    assert len(prediction) == 2

    # sum of all probabilities
    assert np.isclose(sum(prediction),1.0)

    # proablities are not negative

    assert prediction[0] >= 0.0
    assert prediction[1] >= 0.0

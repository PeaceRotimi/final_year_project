import pytest
from forecasting.price_forecast import PriceForecast

@pytest.fixture
# resets the queue before each test
def reset_memory():

    return PriceForecast(window_size=24,default_price=40)

def test_moving_average(reset_memory):
    prices = [50.0,40.0,30.0,30.0,20.0]

    for price in prices:
        prediction = reset_memory.predict(price)

    assert prediction == 34.0


def test_price_default(reset_memory):
    # arrange
    default_price = -30.0

    prices = [50.0,10.0]

    # act:
    for price in prices:
        prediction = reset_memory.predict(price)

    assert prediction == default_price

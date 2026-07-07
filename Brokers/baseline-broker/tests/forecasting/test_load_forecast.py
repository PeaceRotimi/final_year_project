import pytest
from forecasting.load_forecast import LoadForecast

@pytest.fixture
# resets the queue before each test
def reset_memory():

    return LoadForecast(window_size=24)

def test_before_a_full_day(reset_memory):
    # arrange
    load = 100.0

    # assert : that the load a the first time slot is equal to load
    assert reset_memory.predict(load) == load

def test_for_24_hours(reset_memory):
    #arrange: 24 timeslots have gone past

    for i in range(24):
        reset_memory.predict(float(i))

    # arrange :
    predict = reset_memory.predict(float(500))

    #assert:
    assert predict == 0.0

def test_fixed_24(reset_memory):
    # ensure the queue length is never longe than 24

    # arrange
    for i in range(100):
        reset_memory.predict(float(i))
    #assert:
    assert len(reset_memory.history) == 24

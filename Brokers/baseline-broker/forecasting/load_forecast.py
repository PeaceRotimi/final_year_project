from collections import deque

class LoadForecast:
    def __init__(self,window_size=24):

        self.history = deque(maxlen=window_size)

    def predict(self, current_load):

        # a tomorrow's predicted load is 24 hours actual load if 24hours hasn't past it is equal to current load
        if len(self.history) == self.history.maxlen:
            prediction = self.history[0]
        else:
            prediction = current_load

        self.history.append(current_load)
        return prediction

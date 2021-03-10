from math import trunc, isnan

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# Rounds value down to the desired number of decimals digits (controlled decimal_places) using math or truncate mode
def round_value(value, mode, decimal_places):
    if value == 0 or isnan(value):
        return 0
    if mode == "math":
        return round(value, decimal_places)
    elif mode == "down":
        # Check that decimal_places is a non-negative integer
        if not (type(decimal_places) == int):
            raise TypeError("The number of decimal places has to be an integer")
        elif decimal_places < 0:
            raise ValueError("The number of decimal places has to be positive")
        elif decimal_places == 0:
            return trunc(value)

        factor = 10.0 ** decimal_places
        return trunc(value * factor) / factor

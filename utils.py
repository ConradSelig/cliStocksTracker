from math import trunc, isnan


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Rounds value down to the desired number of decimals digits (controlled decimal_places) using math or truncate mode
def round_value(value, mode, decimal_places):
    # test for any case where 0 needs to be returned
    if value == 0 or isnan(value) or decimal_places < 0:
        return 0
    # test and make sure the decimal_places is an integer
    if type(decimal_places) != int:
        raise TypeError(
            "'" + str(type(decimal_places)) + "' cannot be interpreted as an integer"
        )
    # if math rounding, just use pythons builtin
    if mode == "math":
        return round(value, decimal_places)
    elif mode == "down":
        # if the decimal places are zero, we can just truncate
        if decimal_places == 0:
            return trunc(value)

        factor = 10.0 ** decimal_places
        return trunc(value * factor) / factor

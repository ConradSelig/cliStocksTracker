from math import trunc

#Rounds value down to the desired number of decimals digits (controlled decimal_places) using math or truncate mode
def round_value(value, mode, decimal_places):
    if mode == "math":
        return round(value, decimal_places)
    elif mode == "down":
        # Check that decimal_places is a non-negative integer
        if not(type(decimal_places)==int):
            raise TypeError("The number of decimal places has to be an integer")
        elif decimal_places < 0:
            raise ValueError("The number of decimal places has to be positive")
        elif decimal_places == 0:
            return trunc(value,f)
        
        factor = 10.0 ** decimal_places
        return trunc(value * factor) / factor
        
        
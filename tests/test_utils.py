import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import round_value, Singleton

class mysingleton(metaclass=Singleton):
    def __init__(cls):
        cls.count = 0

    def add_one(self):
        self.count += 1


class TestSingleton:

    def test_create_new(self, ensure_singleton_exists=False):
        self.new_singleton = mysingleton()
        if not ensure_singleton_exists:
            assert self.new_singleton.count == 0

    def test_create_again(self):
        self.test_create_new(ensure_singleton_exists=True)
        self.new_singleton.add_one()
        self.new_singleton = mysingleton()
        assert self.new_singleton.count == 1


class TestRoundValue:
    def test_math(self):
        assert round_value(1.456543, "math", 2) == 1.46

    def test_down(self):
        assert round_value(1.456543, "down", 2) == 1.45

    def test_zero(self):
        assert round_value(0, "math", 2) == 0

    def test_nan(self):
        assert round_value(float("NaN"), "math", 2) == 0

    def test_invalid_decimals(self):
        with pytest.raises(TypeError):
            round_value(1.456543, "math", "Hello World") 

    def test_negative_decimals(self):
        assert round_value(1.456543, "math", -3) == 0

    def test_zero_decimals_math(self):
        assert round_value(1.456543, "math", 0) == 1
    
    def test_zero_decimals_down(self):
        assert round_value(1.456543, "down", 0) == 1

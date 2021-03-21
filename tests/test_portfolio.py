import os
import sys
import pytest
from pandas import DataFrame

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import portfolio


class BlankArgs:
    time_period = None
    time_interval = None


class TestStockDataclass:

    my_stock = portfolio.Stock("TEST", [2, 1, 3, 5, 4])

    def test_symbol(self):
        assert self.my_stock.symbol == "TEST"

    def test_curr_value(self):
        assert self.my_stock.curr_value == 4

    def test_open_value(self):
        assert self.my_stock.open_value == 2

    def test_high(self):
        assert self.my_stock.high == 5

    def test_low(self):
        assert self.my_stock.low == 1

    def test_average(self):
        assert self.my_stock.average == 3

    def test_change_amount(self):
        return self.my_stock.change_amount == 2

    def test_change_percentage(self):
        return self.my_stock.change_percentage == 100


class TestPortfolioEntryDataclass:

    my_stock = portfolio.Stock("TEST", [2, 1, 3, 5, 4])
    my_portfolio_entry = portfolio.PortfolioEntry(my_stock, 4, 2.5, False, "blue")
    my_portfolio_entry_none_owned = portfolio.PortfolioEntry(
        my_stock, 0, 2.5, False, "blue"
    )

    def test_holding_market_value(self):
        assert self.my_portfolio_entry.holding_market_value == 16

    def test_holding_open_value(self):
        assert self.my_portfolio_entry.holding_open_value == 8

    def test_cost_basis(self):
        assert self.my_portfolio_entry.cost_basis == 10

    def test_gains(self):
        assert self.my_portfolio_entry.gains == 6

    def test_gains_per_share_none_owned(self):
        assert self.my_portfolio_entry_none_owned.gains_per_share == 0

    def test_gains_per_share(self):
        assert self.my_portfolio_entry.gains_per_share == 1.5


class TestPortfolio:

    my_portfolio = portfolio.Portfolio()
    my_stock_1 = portfolio.Stock("TEST_1", [2, 1, 3, 5, 4])
    my_stock_2 = portfolio.Stock("TEST_2", [2, 1, 3, 5, 4])

    def test_add_entry(self):
        self.my_portfolio.add_entry(self.my_stock_1, 4, 2, "blue", False)
        self.my_portfolio.add_entry(self.my_stock_2, 6, 3, "red", False)
        errors = []

        if not len(self.my_portfolio.stocks) == 2:
            errors.append(
                f"A stock was not added to the portfolio. {len(self.my_portfolio.stocks)} != 2"
            )
        if not self.my_portfolio.open_market_value == 20:
            errors.append(
                f"The open market value was not correctly calculated. {self.my_portfolio.open_market_value} != 20"
            )
        if not self.my_portfolio.market_value == 40:
            errors.append(
                f"The current market value was not correctly calculated. {self.my_portfolio.market_value} != 40"
            )
        if not self.my_portfolio.cost_value == 26:
            errors.append(
                f"The cost value was not correctly calculated. {self.my_portfolio.cost_value} != 30"
            )

        assert not errors, "errors occured:\n{}".format("\n".join(errors))

    def test_get_stocks(self):
        assert len(self.my_portfolio.stocks) == 2

    def test_get_stock(self):
        errors = []

        if not self.my_portfolio.get_stock("TEST_1").color == "blue":
            errors.append("TEST_1 stock returned the wrong color.")
        if not self.my_portfolio.get_stock("TEST_2").color == "red":
            errors.append("TEST_2 stock returned the wrong color.")

        assert not errors, "errors occured:\n{}".format("\n".join(errors))

    def test_average_buyin(self):
        set_a = ("1@1", "1@2", "1@3")
        set_b = ("1@1", "1@2", "2@3")
        set_c = ("100@1", "1@2", "1@3")

        errors = []

        if not self.my_portfolio.average_buyin(set_a, ()) == (3, 2):
            errors.append(
                f"Buyin average failed (Case 1). {self.my_portfolio.average_buyin(set_a, ())} != (3, 2)"
            )
        if not self.my_portfolio.average_buyin(set_b, ()) == (4, 2.25):
            errors.append(
                f"Buyin average failed (Case 2). {self.my_portfolio.average_buyin(set_b, ())} != (4, 2.25)"
            )
        if not self.my_portfolio.average_buyin(set_c, ()) == (102, 1.0294117647058822):
            errors.append(
                f"Buyin average failed (Case 3). {self.my_portfolio.average_buyin(set_c, ())} != (102, 1.0294117647058822)"
            )
        if not self.my_portfolio.average_buyin(set_b, set_b) == (0, 0):
            errors.append(
                f"Buyin average failed (Case 4). {self.my_portfolio.average_buyin(set_b, set_b)} != (0, 0)"
            )
        if not self.my_portfolio.average_buyin(set_b, set_a) == (1, 3):
            errors.append(
                f"Buyin average failed (Case 5). {self.my_portfolio.average_buyin(set_b, set_a)} != (1, 3)"
            )
        if not self.my_portfolio.average_buyin(set_c, set_a) == (99, 1):
            errors.append(
                f"Buyin average failed (Case 6). {self.my_portfolio.average_buyin(set_c, set_a)} != (102, 1.0294117647058822)"
            )

        assert not errors, "errors occured:\n{}".format("\n".join(errors))

    def test_download_market_data(self):
        assert (
            type(self.my_portfolio.download_market_data(BlankArgs(), ["AAPL"]))
            == DataFrame
        )

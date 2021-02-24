import io
import pytz
import utils
import plotille
import webcolors
import contextlib
import configparser

import numpy as np
import yfinance as market

from matplotlib import colors
from colorama import Fore, Style
from datetime import datetime, timedelta

import autocolors


def main():

    config = configparser.ConfigParser()
    config.read("config.ini")
    stocks_config = configparser.ConfigParser()
    stocks_config.read("portfolio.ini")
    portfolio = Portfolio()
    graphs = []

    # verify that the config is valid
    config_keys = {
        "DEFAULT": [],
        "Frame": ["width", "height"],
        "General": ["independent_graphs", "timezone", "rounding_mode"],
    }
    if list(config_keys.keys()) != list(config.keys()):
        print("Invalid config.ini, there is a missing section.")
        return
    for section in config_keys:
        if config_keys[section] != list(config[section].keys()):
            print("Invalid config.ini, " + section + " is missing keys.")
            return

    # check that at least one stock is in portfolio.ini
    if list(stocks_config.keys()) == ["DEFAULT"]:
        print(
            "portfolio.ini has no stocks added or does not exist. There is nothing to show."
        )
        return
    # and that the two required keys for each stock exist
    for key in list(stocks_config.keys()):
        if key == "DEFAULT":
            continue
        if "owned" not in list(stocks_config[key].keys()) and "bought_at" not in list(
            stocks_config[key].keys()
        ):
            print(
                "The stock '"
                + key
                + "' is missing a required section."
                / 'Each stock in the portfolio must have an "owned" and a "bought_at" attribute.'
            )

    for stock in stocks_config.sections():
        new_stock = Stock(stock)

        # get the stock data
        with contextlib.redirect_stdout(
            io.StringIO()
        ):  # this suppress output (library doesn't have a silent mode?)
            data = market.download(tickers=stock, period="1d", interval="1m")

        # just get the value at each minute
        data = data[["Open"]].to_numpy()
        data = [_[0] for _ in data]
        # and save that parsed data
        new_stock.data = data

        # save the current stock value
        new_stock.value = data[-1]

        # are we graphing this stock?
        if "graph" in list(stocks_config[stock].keys()):
            if stocks_config[stock]["graph"] == "True":
                new_stock.graph = True

        if "owned" in list(stocks_config[stock].keys()):
            count = float(stocks_config[stock]["owned"])
        else:
            count = 0

        if "bought_at" in list(stocks_config[stock].keys()):
            bought_at = float(stocks_config[stock]["bought_at"])
        else:
            bought_at = None

        # finally, add the stock to the portfolio
        portfolio.add_stock(new_stock, count, bought_at)

    # create the graph objects, the number is dependant on if independent graphing is on or not
    if config["General"]["independent_graphs"] == "False":
        graphing_list = []
        for stock in portfolio.get_stocks():
            if stock.graph:
                graphing_list.append(stock)
        if len(graphing_list) > 0:
            graphs.append(
                Graph(
                    graphing_list,
                    int(config["Frame"]["width"]),
                    int(config["Frame"]["height"]),
                    autocolors.color_list[: len(graphing_list)],
                    timezone=config["General"]["timezone"],
                )
            )
    else:
        for i, stock in enumerate(portfolio.get_stocks()):
            if stock.graph:
                graphs.append(
                    Graph(
                        [stock],
                        int(config["Frame"]["width"]),
                        int(config["Frame"]["height"]),
                        [autocolors.color_list[i]],
                        timezone=config["General"]["timezone"],
                    )
                )

    # generate and print the graphs
    for graph in graphs:
        graph.gen_graph()
        graph.draw()

    portfolio.print_table(config)

    return


def parse_args(self):
    parser = argparse.ArgumentParser(description="Take options for cliStockTracker.py")
    parser.add_argument("-w", "--width", type=int, help="the width of the chart")
    parser.add_argument("-h", "--height", type=int, help="the height of the chart")
    parser.add_argument(
        "-i",
        "--independent-graphs",
        action="store_true",
        help="show a chart for each stock",
    )
    parser.add_argument(
        "-tz",
        "--timezone",
        type=str,
        default="America/New_York",
        help="your timezione",
    )
    parser.add_argument(
        "-r", "--rounding-mode", type=str, help="how should numbers be rounded"
    )
    parser.add_argument(
        "-ti", "--time-interval", type=str, help="specify time interval for graphs"
    )
    parser.add_argument(
        "-tp", "--time-period", type=str, help="specify time period for graphs"
    )
    parser.add_argument(
        "--config",
        type=argparse.FileType("r", encoding="utf-8"),
        help="regular config file",
    )
    parser.add_argument(
        "--stocks-config",
        type=argparse.FileType("r", encoding="utf-8"),
        help="config file with your list of stonks",
    )
    args = parser.parse_args()
    return args


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Stock:
    def __init__(self, symbol: str, *args, **kwargs):
        self.symbol = symbol
        self.value = 0
        self.data = []
        self.graph = False  # are we going to be graphing this stock?
        return

    def calc_value(self, stocks_count):
        return self.data[-1] * stocks_count

    def get_curr(self):
        return self.data[-1]

    def get_open(self):
        return self.data[0]

    def get_data(self):
        return self.data

    def __str__(self):
        return (
            "Stock:"
            + str(self.symbol)
            + " "
            + str(self.value)
            + " "
            + str(len(self.data))
            + " "
            + str(self.graph)
        )


class Portfolio(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.stocks = []
        self.stocks_metadata = {}
        self.initial_value = 0
        return

    def add_stock(self, stock: Stock, count, value):
        self.stocks.append(stock)
        self.stocks_metadata[stock.symbol] = [float(count), float(value)]
        self.initial_value += (
            self.stocks_metadata[stock.symbol][0]
            * self.stocks_metadata[stock.symbol][1]
        )
        return

    def get_stocks(self):
        return self.stocks

    def get_stock(self, symbol):
        for stock in self.stocks:
            if stock.symbol == symbol:
                return stock
        return None

    def print_table(self, config):
        # table format:
        #   ticker    owned   last    change  change% low high    avg
        # each row will also get a bonus boolean at the end denoting what color to print the line:
        #   None = don't color (headers)
        #   True = green
        #   False = red
        # additional things to print: portfolio total value, portfolio change (and change %)
        mode = config["General"]["rounding_mode"]
        cell_width = 11  # buffer space between columns
        table = [
            [
                "Ticker",
                "Last",
                "Change",
                "Change%",
                "Low",
                "High",
                "Avg",
                "Owned",
                "Aggregate Value",
                None,
            ]
        ]
        table.append(
            ["-" * cell_width for _ in range(len(table[0]))]
        )  # this is the solid line under the header
        table[-1].append(None)  # make sure that solid line is not colored
        self.current_value = 0
        self.opening_value = 0
        for stock in self.stocks:
            line = []
            change_d = utils.round_value(
                stock.get_curr() - stock.get_open(), mode, 2
            )  # change
            change_p = utils.round_value(
                (stock.get_curr() - stock.get_open()) / stock.get_curr() * 100, mode, 2
            )  # change %
            line.append(stock.symbol)  # symbol
            line.append(
                "$" + str(utils.round_value(stock.get_curr(), mode, 2))
            )  # current value
            if change_d >= 0:  # insert the changes into the array
                line.append("+$" + str(change_d))
                line.append("+" + str(change_p) + "%")
            else:
                line.append(
                    "-$" + str(change_d)[1:]
                )  # string stripping here is to remove the native '-' sign
                line.append("-" + str(change_p)[1:] + "%")
            line.append(
                "$" + str(utils.round_value(min(stock.get_data()), mode, 2))
            )  # low
            line.append(
                "$" + str(utils.round_value(max(stock.get_data()), mode, 2))
            )  # high
            line.append(
                "$"
                + str(
                    utils.round_value(
                        sum(stock.get_data()) / len(stock.get_data()), mode, 2
                    )
                )
            )  # avg
            line.append(
                str(round(self.stocks_metadata[stock.symbol][0], 3))
            )  # number of stocks owned
            line.append(
                "$"
                + str(
                    utils.round_value(
                        stock.calc_value(self.stocks_metadata[stock.symbol][0]), mode, 2
                    )
                )
            )
            line.append(True if change_d >= 0 else False)
            table.append(line)

            # just add in the total value seeing as we're iterating stocks anyways
            self.current_value += stock.calc_value(
                self.stocks_metadata[stock.symbol][0]
            )
            # and the opening value of all the tracked stocks
            self.opening_value += (
                stock.get_open() * self.stocks_metadata[stock.symbol][0]
            )

        print("\nPortfolio Summary:\n")
        format_str = "{:" + str(cell_width) + "}"
        for line in table:
            if line[-1] is None:
                pass
            elif line[-1]:
                print(Fore.GREEN, end="")
            else:
                print(Fore.RED, end="")
            print("\t" + "".join([format_str.format(item) for item in line[:-1]]))
            print(Style.RESET_ALL, end="")
        print(
            "\n"
            + "{:25}".format("Total Value: ")
            + format_str.format("$" + str(round(self.current_value, 2)))
        )
        value_gained_day = self.current_value - self.opening_value
        if value_gained_day >= 0:
            print("{:25}".format("Value Gained Today: "), end="")
            print(Fore.GREEN, end="")
            print(
                format_str.format(
                    "+$" + str(utils.round_value(value_gained_day, mode, 2))
                )
                + format_str.format(
                    "+"
                    + str(
                        utils.round_value(
                            value_gained_day / self.current_value * 100, mode, 2
                        )
                    )
                    + "%"
                )
            )
        else:
            print("{:25}".format("Value Gained Today: "), end="")
            print(Fore.RED, end="")
            print(
                format_str.format(
                    "-$" + str(utils.round_value(value_gained_day, mode, 2))[1:]
                )
                + format_str.format(
                    str(
                        utils.round_value(
                            value_gained_day / self.current_value * 100, mode, 2
                        )
                    )
                    + "%"
                )
            )
        print(Style.RESET_ALL, end="")

        value_gained_all = self.current_value - self.initial_value
        if value_gained_all >= 0:
            print("{:25}".format("Value Gained Overall: "), end="")
            print(Fore.GREEN, end="")
            print(
                format_str.format(
                    "+$" + str(utils.round_value(value_gained_all, mode, 2))
                )
                + format_str.format(
                    "+"
                    + str(
                        utils.round_value(
                            value_gained_all / self.current_value * 100, mode, 2
                        )
                    )
                    + "%"
                )
            )
        else:
            print("{:25}".format("Value Gained Overall: "), end="")
            print(Fore.RED, end="")
            print(
                format_str.format(
                    "-$" + str(utils.round_value(value_gained_all, mode, 2))[1:]
                )
                + format_str.format(
                    str(
                        utils.round_value(
                            value_gained_all / self.current_value * 100, mode, 2
                        )
                    )
                    + "%"
                )
            )
        print(Style.RESET_ALL, end="")


class Graph:
    def __init__(
        self, stocks: list, width: int, height: int, colors: list, *args, **kwargs
    ):
        self.stocks = stocks
        self.graph = ""
        self.colors = colors
        self.plot = plotille.Figure()

        self.plot.width = width
        self.plot.height = height
        self.plot.color_mode = "rgb"
        self.plot.X_label = "Time"
        self.plot.Y_label = "Value"

        if "timezone" in kwargs.keys():
            self.timezone = pytz.timezone(kwargs["timezone"])
        else:
            self.timezone = pytz.utc

        if "starttime" in kwargs.keys():
            self.start = (
                kwargs["startend"].replace(tzinfo=pytz.utc).astimezone(self.timezone)
            )
        else:
            self.start = (
                datetime.now()
                .replace(hour=14, minute=30, second=0)
                .replace(tzinfo=pytz.utc)
                .astimezone(self.timezone)
            )

        if "endtime" in kwargs.keys():
            self.end = (
                kwargs["endtime"].replace(tzinfo=pytz.utc).astimezone(self.timezone)
            )
        else:
            self.end = (
                datetime.now()
                .replace(hour=21, minute=0, second=0)
                .replace(tzinfo=pytz.utc)
                .astimezone(self.timezone)
            )

        self.plot.set_x_limits(min_=self.start, max_=self.end)

        return

    def __call__(self):
        return self.graph

    def draw(self):
        print(self.graph)
        return

    def gen_graph(self):
        self.y_min, self.y_max = self.find_y_range()
        self.plot.set_y_limits(min_=self.y_min, max_=self.y_max)

        for i, stock in enumerate(self.stocks):
            self.plot.plot(
                [self.start + timedelta(minutes=i) for i in range(len(stock.data))],
                stock.data,
                lc=webcolors.hex_to_rgb(self.colors[i]),
                label=stock.symbol,
            )

        self.graph = self.plot.show(legend=True)
        return

    def find_y_range(self):
        y_min = 10000000000000  # Arbitrarily large number (bigger than any single stock should ever be worth)
        y_max = 0

        for stock in self.stocks:
            if y_min > min(stock.data):
                y_min = min(stock.data)
            if y_max < max(stock.data):
                y_max = max(stock.data)

        return y_min, y_max


if __name__ == "__main__":
    main()

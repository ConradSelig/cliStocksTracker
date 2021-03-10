import io
import pytz
import utils
import plotille
import warnings
import argparse
import webcolors
import autocolors
import contextlib
import configparser
import multiconfigparser
import math

import numpy as np
import yfinance as market

from matplotlib import colors
from colorama import Fore, Style
from datetime import datetime, timedelta
from renderer import Renderer


def merge_config(config, args):
    if config["General"]["independent_graphs"]:
        args.independent_graphs = config["General"]["independent_graphs"] == "True"

    if config["Frame"]["width"]:
        args.graph_width = int(config["Frame"]["width"])

    if config["Frame"]["height"]:
        args.graph_height = int(config["Frame"]["height"])

    if config["General"]["timezone"]:
        args.timezone = config["General"]["timezone"]

    if config["General"]["rounding_mode"]:
        args.rounding_mode = config["General"]["rounding_mode"]

    return


def main():
    config = multiconfigparser.ConfigParserMultiOpt()
    stocks_config = multiconfigparser.ConfigParserMultiOpt()
    args = parse_args()

    portfolio = Portfolio()

    # read config files
    config.read(args.config)
    stocks_config.read(args.portfolio_config)

    # verify that config files are correct
    verify_config_keys(config, stocks_config)

    merge_config(config, args)

    portfolio.populate(stocks_config, args)

    portfolio.gen_graphs(
        args.independent_graphs, args.graph_width, args.graph_height, args.timezone
    )

    # print to the screen
    render_engine = Renderer(args.rounding_mode, portfolio)
    render_engine.render()

    return


def parse_args():
    parser = argparse.ArgumentParser(description="Options for cliStockTracker.py")
    parser.add_argument(
        "--width",
        type=int,
        help="integer for the width of the chart (default is 80)",
        default=80,
    )
    parser.add_argument(
        "--height",
        type=int,
        help="integer for the height of the chart (default is 20)",
        default=20,
    )
    parser.add_argument(
        "--independent-graphs",
        action="store_true",
        help="show a chart for each stock (default false)",
        default=False,
    )
    parser.add_argument(
        "--timezone",
        type=str,
        help="your timezone (exmple and default: America/New_York)",
        default="America/New_York",
    )
    parser.add_argument(
        "-r",
        "--rounding-mode",
        type=str,
        help="how should numbers be rounded (math | down) (default math)",
        default="math",
    )
    parser.add_argument(
        "-ti",
        "--time-interval",
        type=str,
        help="specify time interval for graphs (ex: 1m, 15m, 1h) (default 1m)",
        default="1m",
    )
    parser.add_argument(
        "-tp",
        "--time-period",
        type=str,
        help="specify time period for graphs (ex: 15m, 1h, 1d) (default 1d)",
        default="1d",
    )
    parser.add_argument(
        "--config", type=str, help="path to a config.ini file", default="config.ini"
    )
    parser.add_argument(
        "--portfolio-config",
        type=str,
        help="path to a portfolio.ini file with your list of stonks",
        default="portfolio.ini",
    )
    args = parser.parse_args()
    return args


def verify_config_keys(config, stocks_config):
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
        exit()  # nothing else to do! Just force exit.


class Stock:
    def __init__(self, symbol: str, *args, **kwargs):
        self.symbol = symbol
        self.value = 0
        self.data = []
        self.graph = False  # are we going to be graphing this stock?
        self.color = None
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


class Portfolio(metaclass=utils.Singleton):
    def __init__(self, *args, **kwargs):
        self.stocks = {}
        self.stocks_metadata = {}
        self.initial_value = 0
        self.color_list = []
        return

    def add_stock(self, stock: Stock, count, value, color):
        self.stocks[stock.symbol] = stock
        self.stocks_metadata[stock.symbol] = [float(count), float(value)]
        self.initial_value += (
            self.stocks_metadata[stock.symbol][0]
            * self.stocks_metadata[stock.symbol][1]
        )
        self.color_list.append(color)
        return

    def get_stocks(self):
        return self.stocks

    def get_stock(self, symbol):
        return self.stocks[symbol]

    def get_color_list(self):
        for stock in self.stocks:
            self.color_list.append(stock.color)

    def average_buyin(self, buys: list, sells: list):
        buy_c, buy_p, sell_c, sell_p, count, bought_at = 0, 0, 0, 0, 0, 0
        buys = [_.split("@") for _ in ([buys] if type(buys) is not tuple else buys)]
        sells = [_.split("@") for _ in ([sells] if type(sells) is not tuple else sells)]

        for buy in buys:
            next_c = float(buy[0])
            if next_c <= 0:
                print(
                    'A negative "buy" key was detected. Use the sell key instead to guarantee accurate calculations.'
                )
                exit()
            buy_c += next_c
            buy_p += float(buy[1]) * next_c

        for sell in sells:
            next_c = float(sell[0])
            if next_c <= 0:
                print(
                    'A negative "sell" key was detected. Use the buy key instead to guarantee accurate calculations.'
                )
                exit()
            sell_c += next_c
            sell_p += float(sell[1]) * next_c

        count = buy_c - sell_c
        if count == 0:
            return 0, 0

        bought_at = (buy_p - sell_p) / count

        return count, bought_at

    # download all ticker data in a single request
    # harder to parse but this provides a signficant performance boost
    def download_market_data(self, args, stocks):
        # get graph time interval and period
        time_period = args.time_period if args.time_period else "1d"
        time_interval = args.time_interval if args.time_interval else "1m"

        try:
            return market.download(
                tickers=stocks,
                period=time_period,
                interval=time_interval,
                progress=False,
            )
        except:
            print(
                "cliStocksTracker must be connected to the internet to function. Please ensure that you are connected to the internet and try again."
            )

    def populate(self, stocks_config, args):
        # download all stock data
        market_data = self.download_market_data(args, stocks_config.sections())

        # iterate through each ticker data
        data_key = "Open"
        for td in market_data[[data_key]]:
            stock = td[1]
            new_stock = Stock(stock)

            # convert the numpy array into a list of prices while removing NaN values
            data = market_data[data_key][stock].values[~np.isnan(market_data[data_key][stock].values)]
            new_stock.data = data

            # save the current stock value
            new_stock.value = data[-1]

            # are we graphing this stock?
            if "graph" in list(stocks_config[stock].keys()):
                if stocks_config[stock]["graph"] == "True":
                    new_stock.graph = True

            if "buy" in list(stocks_config[stock].keys()):
                buyin = stocks_config[stock]["buy"]
            else:
                buyin = ()

            if "sell" in list(stocks_config[stock].keys()):
                sellout = stocks_config[stock]["sell"]
            else:
                sellout = ()

            count, bought_at = self.average_buyin(buyin, sellout)

            # Check the stock color for graphing
            if "color" in list(stocks_config[stock].keys()):
                color = str(stocks_config[stock]["color"])
            else:
                color = None

            # Check that the stock color that was entered is legal
            colorWarningFlag = True
            if color == None:
                colorWarningFlag = False
            elif type(color) == str:
                if (color.startswith("#")) or (
                    color in webcolors.CSS3_NAMES_TO_HEX.keys()
                ):
                    colorWarningFlag = False

            if colorWarningFlag:
                warnings.warn(
                    "The color selected for "
                    + stock
                    + " is not in not in the approved list. Automatic color selection will be used."
                )
                color = None

            # finally, add the stock to the portfolio
            self.add_stock(new_stock, count, bought_at, color)

    def gen_graphs(self, independent_graphs, graph_width, graph_height, cfg_timezone):
        graphs = []
        if not independent_graphs:
            graphing_list = []
            for stock in self.get_stocks().values():
                if stock.graph:
                    graphing_list.append(stock)
            if len(graphing_list) > 0:
                graphs.append(
                    Graph(
                        graphing_list,
                        graph_width,
                        graph_height,
                        self.color_list[: len(graphing_list)],
                        timezone=cfg_timezone,
                    )
                )
        else:
            for i, stock in enumerate(self.get_stocks().values()):
                if stock.graph:
                    graphs.append(
                        Graph(
                            [stock],
                            graph_width,
                            graph_height,
                            [self.color_list[i]],
                            timezone=cfg_timezone,
                        )
                    )
        for graph in graphs:
            graph.gen_graph(autocolors.color_list)
        self.graphs = graphs
        return


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

    def gen_graph(self, auto_colors):
        self.y_min, self.y_max = self.find_y_range()
        self.plot.set_y_limits(min_=self.y_min, max_=self.y_max)

        for i, stock in enumerate(self.stocks):
            if self.colors[i] == None:
                color = webcolors.hex_to_rgb(auto_colors[i % 67])
            elif self.colors[i].startswith("#"):
                color = webcolors.hex_to_rgb(self.colors[i])
            else:
                color = webcolors.hex_to_rgb(
                    webcolors.CSS3_NAMES_TO_HEX[self.colors[i]]
                )

            self.plot.plot(
                [self.start + timedelta(minutes=i) for i in range(len(stock.data))],
                stock.data,
                lc=color,
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

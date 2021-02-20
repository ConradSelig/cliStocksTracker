import io
import pytz
import plotille
import webcolors
import contextlib

import numpy as np
import yfinance as market

import utils

from matplotlib import colors
from colorama import Fore, Style
from datetime import datetime, timedelta


def main():

    config = Configuration("./config")
    stocks_config = Configuration("./stocks_config")
    portfolio = Portfolio()
    graphs = []

    auto_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#000000", 
        "#800000", "#008000", "#000080", "#808000", "#800080", "#008080", "#808080", 
        "#C00000", "#00C000", "#0000C0", "#C0C000", "#C000C0", "#00C0C0", "#C0C0C0", 
        "#400000", "#004000", "#000040", "#404000", "#400040", "#004040", "#404040", 
        "#200000", "#002000", "#000020", "#202000", "#200020", "#002020", "#202020", 
        "#600000", "#006000", "#000060", "#606000", "#600060", "#006060", "#606060", 
        "#A00000", "#00A000", "#0000A0", "#A0A000", "#A000A0", "#00A0A0", "#A0A0A0", 
        "#E00000", "#00E000", "#0000E0", "#E0E000", "#E000E0", "#00E0E0", "#E0E0E0"]
    
    for stock in stocks_config:
        new_stock = Stock(stock)

        # get the stock data
        with contextlib.redirect_stdout(io.StringIO()): # this suppress output (library doesn't have a silent mode?)
            data = market.download(tickers=stock, period="1d", interval="1m")

        # just get the value at each minute
        data = data[["Open"]].to_numpy()
        data = [_[0] for _ in data]
        # and save that parsed data
        new_stock.data = data

        # save the current stock value
        new_stock.value = data[-1] 

        # are we graphing this stock?
        if "graph" in stocks_config[stock].keys():
            if stocks_config[stock]["graph"] == "True":
                new_stock.graph = True
       
        if "owned" in stocks_config[stock].keys():
            count = float(stocks_config[stock]["owned"])
        else:
            count = 0

        if "bought_at" in stocks_config[stock].keys():
            bought_at = float(stocks_config[stock]["bought_at"])
        else:
            bought_at = None

        # finally, add the stock to the portfolio
        portfolio.add_stock(new_stock, count, bought_at)

    # create the graph objects, the number is dependant on if independent graphing is on or not
    if config["kwargs"]["independent_graphs"] == "False":
        graphing_list = []
        for stock in portfolio.get_stocks():
            if stock.graph:
                graphing_list.append(stock)
        graphs.append(Graph(graphing_list, int(config["frame"]["width"]), int(config["frame"]["height"]), auto_colors[:len(graphing_list)]))
    else:
        for i, stock in enumerate(portfolio.get_stocks()):
            if stock.graph:
                graphs.append(Graph([stock], int(config["frame"]["width"]), int(config["frame"]["height"]), [auto_colors[i]]))

    # generate and print the graphs
    for graph in graphs:
        graph.gen_graph()
        graph.draw()

    portfolio.print_table(config)

    return


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Configuration:
    def __init__(self, config_filepath: str, *args, **kwargs):
        self.config_filepath = config_filepath
        self.config = self.parse_config()
        return

    def __iter__(self):
        return iter(self.config.keys())  # just like a dictionary would do

    def __getitem__(self, key):
        return self.config[key]

    def parse_config(self) -> (dict, None):
        config = {}
        last_key = ""

        # grab all the config lines
        with open(self.config_filepath, "r") as config_file:
            filedata = config_file.read().splitlines()

        for line in filedata:
            # if the line is not indented
            if line[0] != " " and line[0] != "\t":
                config[line.replace(":", "")] = {}
                last_key = line.replace(":", "")
            # otherwise, it's a subkey
            else:
                pair = line.split(":")
                config[last_key][pair[0].strip()] = pair[1].strip()

        return config


class Stock:
    def __init__(self, symbol: str, *args, **kwargs):
        self.symbol = symbol
        self.value = 0
        self.data = []
        self.graph = False # are we going to be graphing this stock?
        return

    def calc_value(self, stocks_count):
        return self.data[-1] * stocks_count

    def get_curr(self):
        return self.data[-1]

    def get_open(self):
        return self.data[0]

    def get_data(self):
        return self.data

    def __repr__(self):
        print("Stock:", self.symbol, " ", self.value, " ", len(self.data), " ", self.graph)


class Portfolio(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.stocks = []
        self.stocks_metadata = {}
        self.initial_value = 0
        return

    def add_stock(self, stock: Stock, count, value):
        self.stocks.append(stock)
        self.stocks_metadata[stock.symbol] = [float(count), float(value)]
        self.initial_value += self.stocks_metadata[stock.symbol][0] * self.stocks_metadata[stock.symbol][1]
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
        mode = config["kwargs"]["rounding_mode"]
        cell_width = 11  # buffer space between columns
        table = [["Ticker", "Last", "Change", "Change%", "Low", "High", "Avg", "Owned", "Aggregate Value", None]]
        table.append(["-" * cell_width for _ in range(len(table[0]))])  # this is the solid line under the header
        table[-1].append(None)  # make sure that solid line is not colored
        self.current_value = 0
        self.opening_value = 0
        for stock in self.stocks:
            line = []
            change_d = utils.round_value(stock.get_curr() - stock.get_open(), mode, 2)  # change
            change_p = utils.round_value((stock.get_curr() - stock.get_open()) / stock.get_curr() * 100, mode, 2)  # change %
            line.append(stock.symbol)  # symbol
            line.append("$" + str(utils.round_value(stock.get_curr(), mode, 2)))  # current value
            if change_d >= 0:  # insert the changes into the array
                line.append("+$" + str(change_d))
                line.append("+" + str(change_p) + "%")
            else:
                line.append("-$" + str(change_d)[1:])  # string stripping here is to remove the native '-' sign
                line.append("-" + str(change_p)[1:]+ "%")
            line.append("$" + str(utils.round_value(min(stock.get_data()), mode, 2)))  # low
            line.append("$" + str(utils.round_value(max(stock.get_data()), mode, 2)))  # high
            line.append("$" + str(utils.round_value(sum(stock.get_data()) / len(stock.get_data()), mode, 2)))  # avg
            line.append(str(round(self.stocks_metadata[stock.symbol][0], 3)))  # number of stocks owned
            line.append("$" + str(utils.round_value(stock.calc_value(self.stocks_metadata[stock.symbol][0]), mode, 2)))
            line.append(True if change_d >=0 else False)
            table.append(line)

            # just add in the total value seeing as we're iterating stocks anyways
            self.current_value += stock.calc_value(self.stocks_metadata[stock.symbol][0])
            # and the opening value of all the tracked stocks
            self.opening_value += stock.get_open() * self.stocks_metadata[stock.symbol][0]

        print("\nPortfolio Summary:\n")
        format_str = "{:" + str(cell_width) + "}"
        for line in table:
            if line[-1] is None:
                pass
            elif line[-1]:
                print(Fore.GREEN, end="")
            else:
                print(Fore.RED, end="")
            print('\t' + ''.join([format_str.format(item) for item in line[:-1]]))
            print(Style.RESET_ALL, end="") 
        print("\n" + "{:25}".format("Total Value: ") + format_str.format("$" + str(round(self.current_value, 2))))
        value_gained_day = self.current_value - self.opening_value
        if value_gained_day >= 0:
            print("{:25}".format("Value Gained Today: "), end="")
            print(Fore.GREEN, end="")
            print(format_str.format("+$" + str(utils.round_value(value_gained_day, mode, 2))) + format_str.format("+" + str(utils.round_value(value_gained_day / self.current_value * 100, mode, 2)) + "%"))
        else:
            print("{:25}".format("Value Gained Today: "), end="")
            print(Fore.RED, end="")
            print(format_str.format("-$" + str(utils.round_value(value_gained_day, mode, 2))[1:]) + format_str.format(str(utils.round_value(value_gained_day / self.current_value * 100, mode, 2)) + "%"))
        print(Style.RESET_ALL, end="")

        value_gained_all = self.current_value - self.initial_value
        if value_gained_all >= 0:
            print("{:25}".format("Value Gained Overall: "), end="") 
            print(Fore.GREEN, end="")
            print(format_str.format("+$" + str(utils.round_value(value_gained_all, mode, 2))) + format_str.format("+" + str(utils.round_value(value_gained_all / self.current_value * 100, mode, 2)) + "%"))
        else:
            print("{:25}".format("Value Gained Overall: "), end="") 
            print(Fore.RED, end="")
            print(format_str.format("-$" + str(utils.round_value(value_gained_all, mode, 2))[1:]) + format_str.format(str(utils.round_value(value_gained_all / self.current_value * 100, mode, 2)) + "%"))
        print(Style.RESET_ALL, end="")


class Graph:
    def __init__(self, stocks: list, width: int, height: int, colors: list, *args, **kwargs):
        self.stocks = stocks
        self.graph = ""
        self.colors = colors
        self.plot = plotille.Figure()

        self.plot.width = width
        self.plot.height = height
        self.plot.color_mode = "rgb"
        self.plot.X_label="Time"
        self.plot.Y_label="Value"

        if "timezone" in kwargs.keys():
            self.timezone = pytz.timezone(kwargs["timezone"])
        else:
            self.timezone = pytz.utc

        if "starttime" in kwargs.keys():
            self.start = kwargs["startend"].replace(tzinfo=pytz.utc).astimezone(self.timezone)
        else:
            self.start = datetime.now().replace(hour=14, minute=30, second=0).replace(tzinfo=pytz.utc).astimezone(self.timezone)

        if "endtime" in kwargs.keys():
            self.end = kwargs["endtime"].replace(tzinfo=pytz.utc).astimezone(self.timezone)
        else:
            self.end = datetime.now().replace(hour=21, minute=0, second=0).replace(tzinfo=pytz.utc).astimezone(self.timezone)

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
            self.plot.plot([self.start + timedelta(minutes=i) for i in range(len(stock.data))], stock.data,
                      lc=webcolors.hex_to_rgb(self.colors[i]), label=stock.symbol)

        self.graph = self.plot.show(legend=True)
        return

    def find_y_range(self):
        y_min = 10000000000000 # Arbitrarily large number (bigger than any single stock should ever be worth)
        y_max = 0

        for stock in self.stocks:
            if y_min > min(stock.data):
                y_min = min(stock.data)
            if y_max < max(stock.data):
                y_max = max(stock.data)

        return y_min, y_max


if __name__ == "__main__":
    main()


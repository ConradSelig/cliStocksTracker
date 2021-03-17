import pytz
import utils
import plotille
import warnings
import webcolors
import autocolors

import numpy as np
import yfinance as market

from colorama import Fore, Style
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto


@dataclass
class TransactionType(Enum):
    NONE = auto()
    BUY = (auto(),)
    SELL = (auto(),)
    MARKET_SYNC = auto()


@dataclass
class Stock:
    symbol: str
    data: list = 0

    # TODO: better error handling on stocks not found
    def __post_init__(self):
        self.curr_value = self.data[-1]
        self.open_value = self.data[0]
        self.high = max(self.data)
        self.low = min(self.data)
        self.average = sum(self.data) / len(self.data)
        self.change_amount = self.curr_value - self.open_value
        self.change_percentage = (
            (self.change_amount / self.curr_value) * 100 if self.curr_value > 0 else 0
        )
        return

    def reinit(self):
        self.__post_init__()


@dataclass
class PortfolioEntry:
    stock: Stock
    count: float = 0
    average_cost: float = 0
    graph: bool = False
    color: str = None

    def __post_init__(self):
        self.holding_market_value = self.stock.curr_value * self.count
        self.holding_open_value = self.stock.open_value * self.count
        self.cost_basis = self.count * self.average_cost
        self.gains = self.holding_market_value - self.cost_basis
        self.gains_per_share = self.gains / self.count if self.count > 0 else 0
        return

    def process_transaction(
        self, ttype: TransactionType, count: float, cost: float, data: list
    ):
        if ttype is TransactionType.BUY:
            self.count += count
            self.average_cost = (self.cost_basis + cost) / 2
        elif ttype is TransactionType.SELL:
            self.count -= count
        elif ttype is TransactionType.MARKET_SYNC:
            self.stock.data = data
            self.stock.reinit()

        self.__post_init__()


class Portfolio(metaclass=utils.Singleton):
    def __init__(self, *args, **kwargs):
        self.stocks = {}

        # portfolio worth at market open
        self.open_market_value = 0
        # amount invested into the portfolio (sum of cost of share cost)
        self.cost_value = 0
        self.market_value = 0
        return

    # TODO: clean this up -- better as separate market update function?
    # TODO: remove graph and color from here?
    def _upsert_entry(
        self,
        ticker: str,
        data: list = (0),
        ttype: TransactionType = TransactionType.NONE,
        count: float = 0,
        bought_at: float = 0,
        color: str = None,
        graph: bool = False,
    ):
        # first see if it's an existing entry we can update
        entry = self.get_stock(ticker)
        if entry != None:
            # clear portfolio data so we can recalc -- TODO: clean this up
            self.open_market_value -= entry.holding_open_value
            self.market_value -= entry.holding_market_value
            self.cost_value -= entry.cost_basis

            entry.color = entry.color if ttype == TransactionType.MARKET_SYNC else color
            entry.graph = entry.graph if ttype == TransactionType.MARKET_SYNC else graph
            entry.process_transaction(ttype, count, bought_at, data)

            # update portfolio values
            self.open_market_value += entry.holding_open_value
            self.market_value += entry.holding_market_value
            self.cost_value += entry.cost_basis
            return

        # insert new entry
        self._add_new_entry(ticker, data, count, bought_at, color, graph)
        return

    def _remove_entry(self, ticker: str):
        entry = self.get_stock(ticker)
        if entry == None:
            return

        # remove entries effect on portoflio
        self.open_market_value -= entry.holding_open_value
        self.market_value -= entry.holding_market_value
        self.cost_value -= entry.cost_basis

        del self.stocks

    def _add_new_entry(
        self,
        ticker: str,
        data: list,
        count: float,
        bought_at: float,
        color: str,
        graph: bool,
    ):
        entry = PortfolioEntry(Stock(ticker, data), count, bought_at, graph, color)
        self.stocks[ticker] = entry

        self.open_market_value += entry.holding_open_value
        self.market_value += entry.holding_market_value
        self.cost_value += entry.cost_basis
        return

    def get_stocks(self):
        return self.stocks

    def get_stock(self, symbol) -> PortfolioEntry:
        return self.stocks.get(symbol)

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

    def load_from_config(self, stocks_config):
        for ticker in stocks_config.sections():
            # calculate average buy in
            buyin = (
                stocks_config[ticker]["buy"]
                if "buy" in list(stocks_config[ticker].keys())
                else ()
            )
            sellout = (
                stocks_config[ticker]["sell"]
                if "sell" in list(stocks_config[ticker].keys())
                else ()
            )
            count, bought_at = self.average_buyin(buyin, sellout)

            # Check the stock color for graphing
            color = (
                str(stocks_config[ticker]["color"])
                if "color" in list(stocks_config[ticker].keys())
                else None
            )

            should_graph = (
                "graph" in list(stocks_config[ticker].keys())
                and stocks_config[ticker]["graph"] == "True"
            )

            self._upsert_entry(
                ticker, [0], TransactionType.BUY, count, bought_at, color, should_graph
            )

        return

    """
    download all ticker data in a single request
    harder to parse but this provides a signficant performance boost
    """

    def _download_market_data(self, args, stocks):
        # get graph time interval and period
        time_period = args.time_period if args.time_period else "1d"
        time_interval = args.time_interval if args.time_interval else "1m"

        try:
            return market.download(
                tickers=stocks,
                period=time_period,
                interval=time_interval,
                progress=True,
            )
        except:
            print(Fore.RED, "Failed to download market data", Style.RESET_ALL)

    def market_sync(self, args, stock_list=()):
        # TODO: better error handling
        if not stock_list:
            print("No tickers supplied - default to existing entries")
            stock_list = list(self.stocks.keys())

        # temp workaround for different data format depending on number of stocks being queried
        singleWorkaround = False
        if len(stock_list) == 1:
            stock_list.append("foo")
            singleWorkaround = True

        # download all stock data
        print(Fore.GREEN, end="")
        market_data = self._download_market_data(args, stock_list)
        print(Style.RESET_ALL)

        if singleWorkaround:
            stock_list.pop()

        # iterate through each ticker data
        # TODO: add error handling to stocks not found
        data_key = "Open"
        for ticker in stock_list:
            # convert the numpy array into a list of prices while removing NaN values
            data = market_data[data_key][ticker].values[
                ~np.isnan(market_data[data_key][ticker].values)
            ]
            self._upsert_entry(ticker, data, TransactionType.MARKET_SYNC)

    def gen_graphs(self, independent_graphs, graph_width, graph_height, cfg_timezone):
        graphs = []
        if not independent_graphs:
            graphing_list = []
            color_list = []
            for sm in self.get_stocks().values():
                if sm.graph:
                    graphing_list.append(sm.stock)
                    color_list.append(sm.color)
            if len(graphing_list) > 0:
                graphs.append(
                    Graph(
                        graphing_list,
                        graph_width,
                        graph_height,
                        color_list,
                        timezone=cfg_timezone,
                    )
                )
        else:
            for sm in self.get_stocks().values():
                if sm.graph:
                    graphs.append(
                        Graph(
                            [sm.stock],
                            graph_width,
                            graph_height,
                            [sm.color],
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

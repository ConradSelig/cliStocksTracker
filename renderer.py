import io
import utils
import portfolio

from colorama import Fore, Style
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Callable


@dataclass
class CellData:
    value: str
    color: str = None

@dataclass
class ColumnFormatter:
    header: str
    width: int

    # function that takes a thing and produces a printable string for it
    generator: Callable[[object], CellData] = lambda v: CellData(str(v))

    def generate_string(self, input) -> str:
        cell_data = self.generator(input)
        return cell_data.value

def format_number(value) -> str:
        return str(abs(utils.round_value(value, "math", 2)))

def format_gl(value: float, is_currency: bool = True) -> str:
        change_symbol = "+" if value >= 0 else "-"
        if is_currency:
            change_symbol += "$"

        return change_symbol + format_number(value)

_stock_column_formatters = {
    "Ticker" : ColumnFormatter("Ticker", 9, lambda stock: CellData(stock.symbol)),
    "Current Price" : ColumnFormatter("Last", 12, lambda stock: CellData(format_number(stock.curr_value))),
    "Daily Change Amount": ColumnFormatter("Chg", 12, lambda stock: CellData(format_gl(stock.change_amount))),
    "Daily Change Percentage": ColumnFormatter("Chg%", 10, lambda stock: CellData(format_gl(stock.change_percentage, False))),
    "Low": ColumnFormatter("Low", 12, lambda stock: CellData(format_number(stock.low))),
    "High": ColumnFormatter("High", 12, lambda stock: CellData(format_number(stock.high))),
    "Daily Average Price": ColumnFormatter("Avg", 12, lambda stock: CellData(format_number(stock.average))),
}

_portfolio_column_formatters = {
    "Stocks Owned": ColumnFormatter("Owned", 9, lambda entry: CellData(format_number(entry.count))),
    "Gains per Share": ColumnFormatter("G/L/S", 12, lambda entry: CellData(format_gl(entry.gains_per_share))),
    "Current Market Value": ColumnFormatter("Mkt V", 12, lambda entry: CellData(format_number(entry.holding_market_value))),
    "Average Buy Price": ColumnFormatter("Buy", 12, lambda entry: CellData(format_number(entry.average_cost))),
    "Total Share Gains": ColumnFormatter("G/L/T", 12, lambda entry: CellData(format_gl(entry.gains))),
    "Total Share Cost": ColumnFormatter("Cost", 12, lambda entry: CellData(format_number(entry.cost_basis))),
}

class Renderer(metaclass=utils.Singleton):
    def __init__(self, rounding: str, portfolio: portfolio.Portfolio, *args, **kwargs):
        self.mode = rounding
        self.portfolio = portfolio
        self.cell_width = 13
        return

    def render(self):
        print()
        for graph in self.portfolio.graphs:
            graph.draw()

        self.print_new_table()
        return

    """
    def print_ticker_summaries(self, format_str, table):
        for line in table:
            if line[-1] is None:
                pass
            else:
                print(Fore.GREEN if line[-1] else Fore.RED, end="")

            print("\t" + "".join([format_str.format(item) for item in line[:-1]]))
            print(Style.RESET_ALL, end="")

        # print the totals line market value then cost
        print("{:126}".format("\nTotals: "), end="")

        # current market value
        print(
            Fore.GREEN
            if self.portfolio.market_value >= self.portfolio.cost_value
            else Fore.RED,
            end="",
        )
        print(
            format_str.format(
                "$" + self.format_number(self.portfolio.market_value)
            ),
            end="",
        )
        print(Fore.RESET, end="")

        # G/L Total
        print(
            Fore.GREEN
            if self.portfolio.market_value >= self.portfolio.cost_value
            else Fore.RED,
            end="",
        )
        print(
            "{:13}".format("")
            + format_str.format(
                self.format_gl(self.portfolio.market_value - self.portfolio.cost_value, True)
            ),
            end="",
        )
        print(Fore.RESET, end="")

        # portfolio cost total
        print(
            format_str.format(
                "$" + self.format_number(self.portfolio.cost_value)
            )
        )
        return
    """

    def print_gains(self, format_str, gain, timespan):
        positive_gain = gain >= 0
        gain_symbol = "+" if positive_gain else "-"
        gain_verboge = "Gained" if positive_gain else "Lost"

        print("{:25}".format("Value " + gain_verboge + " " + timespan + ": "), end="")
        print(Fore.GREEN if positive_gain else Fore.RED, end="")
        print(
            format_str.format(
                gain_symbol + "$" + str(abs(utils.round_value(gain, self.mode, 2)))
            )
            + format_str.format(
                gain_symbol
                + str(
                    abs(
                        utils.round_value(
                            gain / self.portfolio.cost_value * 100, self.mode, 2
                        )
                    )
                )
                + "%"
            )
        )
        print(Style.RESET_ALL, end="")
        return

    def print_overall_summary(self):
        print(
            "\n"
            + "{:25}".format("Current Time: ")
            + "{:13}".format(datetime.now().strftime("%A %b %d, %Y - %I:%M:%S %p"))
        )
        print(
            "{:25}".format("Total Cost: ")
            + "{:13}".format("$" + format_number(self.portfolio.cost_value))
        )
        print(
            "{:25}".format("Total Value: ")
            + "{:13}".format("$" + format_number(self.portfolio.market_value))
        )

        # print daily value
        value_gained_day = (
            self.portfolio.market_value - self.portfolio.open_market_value
        )
        self.print_gains("{:13}", value_gained_day, "Today")

        # print overall value
        value_gained_all = self.portfolio.market_value - self.portfolio.cost_value
        self.print_gains("{:13}", value_gained_all, "Overall")
        return

    def print_new_table(self, stock_cols = list(_stock_column_formatters.keys()), portfolio_cols = list(_portfolio_column_formatters.keys())):
        # print heading
        print("\nPortfolio Summary:\n")

        # print the heading
        heading = "\t"
        divider = "\t"
        for col in stock_cols + portfolio_cols:
            column = _stock_column_formatters.get(col) or _portfolio_column_formatters.get(col)
            heading += ("{:" + str(column.width) + "}").format(column.header)
            divider += "-" * column.width
        print(heading + "\n" + divider)

        # now print every portfolio entry
        for entry in self.portfolio.stocks.values():
            line = "\t"
            stock = entry.stock
            
            for i, col in enumerate(stock_cols + portfolio_cols):
                col_formatter = _stock_column_formatters.get(col) 
                
                is_stock = col_formatter != None
                if not is_stock:
                    col_formatter = _portfolio_column_formatters.get(col)
                line += ("{:" + str(col_formatter.width) + "}").format(col_formatter.generate_string(stock if is_stock else entry))

            # print the entry
            print(line)

        self.print_overall_summary()        
        return

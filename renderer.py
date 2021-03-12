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

    # function that takes a stock and generates the cell data for this column
    # generator: Callable[[portfolio.Stock], CellData] = None
    generator: Callable[[object], CellData] = None

table_headers = {
    "Ticker" : ColumnFormatter("Ticker", 10, lambda stock: CellData(stock.symbol)),
    "Current Price" : ColumnFormatter("Last", 13, lambda stock: CellData(stock.curr_value)),
    "Daily Change Amount": ColumnFormatter("Change", 12, lambda stock: CellData(stock.change_amount)),
    "Daily Change Percentage": ColumnFormatter("Change%", 12, lambda stock: CellData(stock.change_percentage)),
    "Low": ColumnFormatter("Low", 13, lambda stock: CellData(stock.low)),
    "High": ColumnFormatter("High", 13, lambda stock: CellData(stock.high)),
    "Daily Average Price": ColumnFormatter("Daily Avg", 13, lambda stock: CellData(stock.average)),
    "Stocks Owned": ColumnFormatter("Owned", 8, lambda entry: CellData(entry.count)),
    "Gains per Share": ColumnFormatter("G/L/S", 12, lambda entry: CellData(entry.gains_per_share)),
    "Current Market Value": ColumnFormatter("Mkt Value", 13, lambda entry: CellData(entry.holding_market_value)),
    "Average Buy Price": ColumnFormatter("Buy Price", 12, lambda entry: CellData(entry.average_cost)),
    "Total Share Gains": ColumnFormatter("G/L Total", 13, lambda entry: CellData(entry.gains)),
    "Total Share Cost": ColumnFormatter("Cost", 13, lambda entry: CellData(entry.cost_basis)),
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
        # self.print_table()
        return

    def format_number(self, value) -> str:
        return str(abs(utils.round_value(value, self.mode, 2)))

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

    def print_overall_summary(self, format_str):
        print(
            "\n"
            + "{:25}".format("Current Time: ")
            + format_str.format(datetime.now().strftime("%A %b %d, %Y - %I:%M:%S %p"))
        )
        print(
            "{:25}".format("Total Cost: ")
            + format_str.format("$" + self.format_number(self.portfolio.cost_value))
        )
        print(
            "{:25}".format("Total Value: ")
            + format_str.format("$" + self.format_number(self.portfolio.market_value))
        )

        # print daily value
        value_gained_day = (
            self.portfolio.market_value - self.portfolio.open_market_value
        )
        self.print_gains(format_str, value_gained_day, "Today")

        # print overall value
        value_gained_all = self.portfolio.market_value - self.portfolio.cost_value
        self.print_gains(format_str, value_gained_all, "Overall")
        return

    def format_gl(self, value: float, is_currency: bool) -> str:
        change_symbol = "+" if value >= 0 else "-"
        if is_currency:
            change_symbol += "$"

        return change_symbol + self.format_number(value)

    def print_new_table(self):
        # print heading
        print("\nPortfolio Summary:\n")

        # print the heading
        heading = "\t"
        divider = "\t"
        for column in table_headers.values():
            col_format = "{:" + str(column.width) + "}"
            heading += col_format.format(column.header)
            divider += "-" * column.width
        print(heading + "\n" + divider)

        # now print every portfolio entry
        for entry in self.portfolio.stocks.values():
            line = "\t"
            stock = entry.stock
            
            col_formatter = table_headers["Ticker"]
            curr_format = "{:" + str(table_headers["Ticker"].width) + "}"
            line += curr_format.format(col_formatter.generator(stock).value)

            print(line)



        return

    def print_table(self):
        table = [
            [
                "Ticker",
                "Last",
                "Change",
                "Change%",
                "Low",
                "High",
                "Daily Avg",
                "Owned",
                "G/L/S",
                "Mkt Value",
                "Avg Share",
                "G/L Total",
                "Total Cost",
                None,
            ]
        ]
        table.append(
            ["-" * self.cell_width for _ in range(len(table[0]) - 1)]
        )  # this is the solid line under the header
        table[-1].append(None)  # make sure that solid line is not colored

        for entry in self.portfolio.stocks.values():
            stock = entry.stock

            line = []
            line.append(stock.symbol)
            line.append("$" + self.format_number(stock.curr_value))

            # change stats
            line.append(self.format_gl(stock.change_amount, True))
            line.append(self.format_gl(stock.change_percentage, False) + "%")

            line.append("$" + self.format_number(stock.low))
            line.append("$" + self.format_number(stock.high))
            line.append("$" + self.format_number(stock.average))

            line.append(self.format_number(entry.count))
            line.append(self.format_gl(entry.gains_per_share, True))
            line.append("$" + self.format_number(entry.holding_market_value))
            line.append(self.format_number(entry.average_cost))
            line.append(self.format_gl(entry.gains, True))

            # total cost of shares
            line.append("$" + self.format_number(entry.cost_basis))
            line.append(True if stock.change_amount >= 0 else False)
            table.append(line)

        # generate ticker daily summary
        print("\nPortfolio Summary:\n")
        format_str = "{:" + str(self.cell_width) + "}"
        self.print_ticker_summaries(format_str, table)

        self.print_overall_summary(format_str)

import io
import utils
import portfolio

from colorama import Fore, Style
from datetime import datetime, timedelta


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

        self.print_table()
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
        print("{:138}".format("\nTotals: "), end="")
        print(
            Fore.GREEN
            if self.portfolio.market_value >= self.portfolio.cost_value
            else Fore.RED,
            end="",
        )
        print(
            format_str.format(
                "$" + str(utils.round_value(self.portfolio.market_value, self.mode, 2))
            ),
            end="",
        )
        print(Fore.RESET, end="")
        print(
            "{:13}".format("")
            + format_str.format(
                "$" + str(utils.round_value(self.portfolio.cost_value, self.mode, 2))
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

    def print_table(self):
        # table format:
        #   ticker    owned   last    change  change% low high    avg
        # each row will also get a bonus boolean at the end denoting what color to print the line:
        #   None = don't color (headers)
        #   True = green
        #   False = red
        # additional things to print: portfolio total value, portfolio change (and change %)

        cell_width = 13  # buffer space between columns
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
            ["-" * cell_width for _ in range(len(table[0]) - 1)]
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
        format_str = "{:" + str(cell_width) + "}"
        self.print_ticker_summaries(format_str, table)

        self.print_overall_summary(format_str)

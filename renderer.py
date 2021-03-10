import io
import utils

from colorama import Fore, Style
from datetime import datetime, timedelta

# from cliStocksTracker import Portfolio


class Renderer(metaclass=utils.Singleton):
    def __init__(self, rounding: str, portfolio, *args, **kwargs):
        self.mode = rounding
        self.portfolio = portfolio
        self.cell_width = 13
        return

    def render(self):
        for graph in self.portfolio.graphs:
            graph.draw()

        self.print_table()
        return

    def print_ticker_summaries(self, format_str, table):
        for line in table:
            if line[-1] is None:
                pass
            else:
                print(Fore.GREEN if line[-1] else Fore.RED, end="")

            print("\t" + "".join([format_str.format(item) for item in line[:-1]]))
            print(Style.RESET_ALL, end="")

        # print the totals line market value then cost
        print("{:112}".format("\nTotals: "), end="")
        print(
            Fore.GREEN
            if self.portfolio.current_value >= self.portfolio.initial_value
            else Fore.RED,
            end="",
        )
        print(
            format_str.format(
                "$" + str(utils.round_value(self.portfolio.current_value, self.mode, 2))
            ),
            end="",
        )
        print(Fore.RESET, end="")
        print(
            "{:13}".format("")
            + format_str.format(
                "$" + str(utils.round_value(self.portfolio.initial_value, self.mode, 2))
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
                            gain / self.portfolio.current_value * 100, self.mode, 2
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
            + format_str.format(
                "$" + str(utils.round_value(self.portfolio.initial_value, self.mode, 2))
            )
        )
        print(
            "{:25}".format("Total Value: ")
            + format_str.format(
                "$" + str(utils.round_value(self.portfolio.current_value, self.mode, 2))
            )
        )

        # print daily value
        value_gained_day = self.portfolio.current_value - self.portfolio.opening_value
        self.print_gains(format_str, value_gained_day, "Today")

        # print overall value
        value_gained_all = self.portfolio.current_value - self.portfolio.initial_value
        self.print_gains(format_str, value_gained_all, "Overall")
        return

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
                "Mkt Value",
                "Avg Share",
                "Total Cost",
                None,
            ]
        ]
        table.append(
            ["-" * cell_width for _ in range(len(table[0]) - 1)]
        )  # this is the solid line under the header
        table[-1].append(None)  # make sure that solid line is not colored
        self.portfolio.current_value = 0
        self.portfolio.opening_value = 0
        for stock in self.portfolio.stocks.values():
            line = []
            change_d = utils.round_value(
                stock.get_curr() - stock.get_open(), self.mode, 2
            )  # change
            change_p = utils.round_value(
                (stock.get_curr() - stock.get_open()) / stock.get_curr() * 100,
                self.mode,
                2,
            )  # change %
            line.append(stock.symbol)  # symbol
            line.append(
                "$" + str(utils.round_value(stock.get_curr(), self.mode, 2))
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
                "$" + str(utils.round_value(min(stock.get_data()), self.mode, 2))
            )  # low
            line.append(
                "$" + str(utils.round_value(max(stock.get_data()), self.mode, 2))
            )  # high
            line.append(
                "$"
                + str(
                    utils.round_value(
                        sum(stock.get_data()) / len(stock.get_data()), self.mode, 2
                    )
                )
            )  # avg

            line.append(
                str(
                    utils.round_value(
                        self.portfolio.stocks_metadata[stock.symbol][0], self.mode, 3
                    )
                )
            )  # number of stocks owned

            # current market value of shares
            curr_value = stock.calc_value(
                self.portfolio.stocks_metadata[stock.symbol][0]
            )
            line.append("$" + str(utils.round_value(curr_value, self.mode, 2)))

            # Average buy in cost
            line.append(
                str(
                    utils.round_value(
                        self.portfolio.stocks_metadata[stock.symbol][1], self.mode, 2
                    )
                )
            )

            # total cost of shares
            cost = (
                self.portfolio.stocks_metadata[stock.symbol][0]
                * self.portfolio.stocks_metadata[stock.symbol][1]
            )
            line.append("$" + str(utils.round_value(cost, self.mode, 2)))
            line.append(True if change_d >= 0 else False)
            table.append(line)

            # just add in the total value seeing as we're iterating stocks anyways
            self.portfolio.current_value += stock.calc_value(
                self.portfolio.stocks_metadata[stock.symbol][0]
            )
            # and the opening value of all the tracked stocks
            self.portfolio.opening_value += (
                stock.get_open() * self.portfolio.stocks_metadata[stock.symbol][0]
            )

        # generate ticker daily summary
        print("\nPortfolio Summary:\n")
        format_str = "{:" + str(cell_width) + "}"
        self.print_ticker_summaries(format_str, table)

        self.print_overall_summary(format_str)

import io
import pytz
import plotille
import webcolors
import contextlib

import numpy as np
import yfinance as market

from matplotlib import colors
from colorama import Fore, Style
from datetime import datetime, timedelta

def main():

    stocks_config = parse_config("stocks_config")
    config = parse_config("config")
    stock_data = {}
    current_values = {}
    folio_value = 0
    folio_delta = 0

    # validate the config file
    if "kwargs" not in config.keys() and "frame" not in config.keys():
        print("Invalid config file.")
        return
    if "width" not in config["frame"].keys() and "height" not in config["frame"].keys():
        print("Invalid config file.")
        return

    for stock in stocks_config:
        # get the stock data
        with contextlib.redirect_stdout(io.StringIO()): # this suppress output (library doesn't have a silent mode?)
            data = market.download(tickers=stock, period="1d", interval="1m")
        # just get the value at each minute
        data = data[["Open"]].to_numpy()
        data = [_[0] for _ in data]
        # and the current value, this is stored separate just in case the stock is not being graphed
        current_values[stock] = data[-1]
        # are we graphing this stock?
        if "graph" in stocks_config[stock].keys():
            if stocks_config[stock]["graph"] == "False":
                continue
        # add the data to known data
        if "color" in stocks_config[stock].keys():
            stock_data[stock] = [stocks_config[stock]["color"], data]
        else:
            stock_data[stock] = [None, data]

    # are the graphs being put together, or separate? Then plot
    if "independent_graphs" in config["kwargs"].keys():
        if config["kwargs"]["independent_graphs"] == "False":
            plot(stock_data, config)
        else:
            for stock in stock_data:
                plot({stock: stock_data[stock]}, config)
                print()
    else:
        plot(stock_data, config)

    # graphing is done, time for the portfolio summary

    print()
    print("Portfolio Summary:")
    for stock_name in stocks_config:
        stock = stocks_config[stock_name]
        keys = stock.keys()
        value = current_values[stock_name]
        # determine which type of output we need
        if "owned" in keys and "bought_at" in keys:
            original_val = float(stock["owned"]) * float(stock["bought_at"])
            current_val = float(stock["owned"]) * value
            delta = current_val - original_val
            
            print("\t" + stock_name + " " + stock["owned"] + "@" + str(round(value, 4)) + ": $" + str(round(float(stock["owned"]) * value, 2)), end="")
            if delta > 0:  # we're up!
                print(Fore.GREEN + "  $" + str(round(delta, 2)))
            else: # we're down :(
                print(Fore.RED + "  $" + str(round(delta, 2)))
            print(Style.RESET_ALL, end="")

            # don't forget to add the running totals in!
            folio_delta += delta
            folio_value += current_val

        elif "owned" in keys:
            current_val = float(stock["owned"]) * value

            print("\t" + stock_name + " " + stock["owned"] + "@" + str(round(value, 4)) + ": $" + str(round(current_val, 2))) 

            # don't forget to add the running totals in!
            folio_value += current_val
    # print the totals
    print()
    print("Total Value: $" + str(round(folio_value, 2)))
    print("Change Today: ", end="")
    if folio_delta > 0:  # we're up!
        print(Fore.GREEN + "$" + str(round(folio_delta, 2)))
    else: # we're down :(
        print(Fore.RED + "$" + str(round(folio_delta, 2)))
    print(Style.RESET_ALL, end="")

    return


def parse_config(config_filename):
    config = {}
    last_key = ""

    # grab all the config lines
    with open(config_filename, "r") as config_file:
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


def plot(stocks, config):

    y_min, y_max = find_y_range(stocks)

    auto_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#000000", 
        "#800000", "#008000", "#000080", "#808000", "#800080", "#008080", "#808080", 
        "#C00000", "#00C000", "#0000C0", "#C0C000", "#C000C0", "#00C0C0", "#C0C0C0", 
        "#400000", "#004000", "#000040", "#404000", "#400040", "#004040", "#404040", 
        "#200000", "#002000", "#000020", "#202000", "#200020", "#002020", "#202020", 
        "#600000", "#006000", "#000060", "#606000", "#600060", "#006060", "#606060", 
        "#A00000", "#00A000", "#0000A0", "#A0A000", "#A000A0", "#00A0A0", "#A0A0A0", 
        "#E00000", "#00E000", "#0000E0", "#E0E000", "#E000E0", "#00E0E0", "#E0E0E0"]

    plot = plotille.Figure()
    
    # set some standard plot settings
    plot.width = int(config["frame"]["width"])
    plot.height = int(config["frame"]["height"])
    plot.set_x_limits(min_=datetime.now().replace(hour=14, minute=30, second=0).replace(tzinfo=pytz.utc).astimezone(pytz.timezone(config["kwargs"]["timezone"])), 
                      max_=datetime.now().replace(hour=21, minute=0, second=0).replace(tzinfo=pytz.utc).astimezone(pytz.timezone(config["kwargs"]["timezone"])))
    plot.set_y_limits(min_=y_min, max_=y_max)
    plot.color_mode = "rgb"
    plot.X_label="Time"
    plot.Y_label="Value"

    for i, stock in enumerate(stocks):
        if stocks[stock][0] == None:
            plot.plot([datetime.now().replace(hour=7, minute=30, second=0) + timedelta(minutes=i) for i in range(len(stocks[stock][1]))], 
                      stocks[stock][1], lc=webcolors.hex_to_rgb(auto_colors[i % 67]), label=stock)
        else:
            color = webcolors.hex_to_rgb(webcolors.CSS3_NAMES_TO_HEX[stocks[stock][0]])
            plot.plot([datetime.now().replace(hour=7, minute=30, second=0) + timedelta(minutes=i) for i in range(len(stocks[stock][1]))], 
                      stocks[stock][1], lc=color, label=stock)
            

    print(plot.show(legend=True))

    return


def find_y_range(stocks):
    y_min = 10000000000000 # Arbitrarily large number (bigger than any single stock should ever be worth)
    y_max = 0

    for stock in stocks:
        if y_min > min(stocks[stock][1]):
            y_min = min(stocks[stock][1])
        if y_max < max(stocks[stock][1]):
            y_max = max(stocks[stock][1])

    return y_min, y_max


if __name__ == "__main__":
    main()


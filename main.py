import io
import pytz
import plotille
import contextlib

import numpy as np
import yfinance as market

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
        stock_data[stock] = data

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
        if line[0] != " ":
            config[line.replace(":", "")] = {}
            last_key = line.replace(":", "")
        # otherwise, it's a subkey
        else:
            pair = line.split(":")
            config[last_key][pair[0].strip()] = pair[1].strip()

    return config


def plot(stocks, config):

    y_min, y_max = find_y_range(stocks)

    plot = plotille.Figure()
    
    # set some standard plot settings
    plot.width = int(config["frame"]["width"])
    plot.height = int(config["frame"]["height"])
    plot.set_x_limits(min_=datetime.now().replace(hour=14, minute=30, second=0).replace(tzinfo=pytz.utc).astimezone(pytz.timezone(config["kwargs"]["timezone"])), 
                      max_=datetime.now().replace(hour=21, minute=0, second=0).replace(tzinfo=pytz.utc).astimezone(pytz.timezone(config["kwargs"]["timezone"])))
    plot.set_y_limits(min_=y_min, max_=y_max)
    plot.color_mode = 'byte'
    plot.X_label="Time"
    plot.Y_label="Value"

    for i, stock in enumerate(stocks):
        plot.plot([datetime.now().replace(hour=7, minute=30, second=0) + timedelta(minutes=i) for i in range(len(stocks[stock]))], 
                  stocks[stock], lc=25+i*100, label=stock)

    print(plot.show(legend=True))

    return


def find_y_range(stocks):
    y_min = 10000000000000 # Arbitrarily large number (bigger than any single stock should ever be worth)
    y_max = 0

    for stock in stocks:
        if y_min > min(stocks[stock]):
            y_min = min(stocks[stock])
        if y_max < max(stocks[stock]):
            y_max = max(stocks[stock])

    return y_min, y_max


if __name__ == "__main__":
    main()


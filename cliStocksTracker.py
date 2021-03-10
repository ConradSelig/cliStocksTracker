import io
import pytz
import utils
import plotille
import warnings
import argparse
import webcolors
import autocolors
import contextlib
import multiconfigparser

import numpy as np
import yfinance as market
import portfolio as port

from datetime import datetime, timedelta
from renderer import Renderer


def merge_config(config, args):
    if "General" in config:
        if "independent_graphs" in config["General"]:
            args.independent_graphs = config["General"]["independent_graphs"] == "True"
        if "timezone" in config["General"]:
            args.timezone = config["General"]["timezone"]
        if "rounding_mode" in config["General"]:
            args.rounding_mode = config["General"]["rounding_mode"]

    if "Frame" in config:
        if "width" in config["Frame"]:
            args.width = int(config["Frame"]["width"])
        if "height" in config["Frame"]:
            args.heigth = int(config["Frame"]["height"])

    return


def main():
    config = multiconfigparser.ConfigParserMultiOpt()
    stocks_config = multiconfigparser.ConfigParserMultiOpt()
    args = parse_args()

    portfolio = port.Portfolio()

    # read config files
    config.read(args.config)
    stocks_config.read(args.portfolio_config)

    # verify that config file is correct
    # merge options from cli and config
    verify_stock_keys(stocks_config)
    merge_config(config, args)

    portfolio.populate(stocks_config, args)
    portfolio.gen_graphs(
        args.independent_graphs, args.width, args.height, args.timezone
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


def verify_stock_keys(stocks_config):
    # check that at least one stock is in portfolio.ini
    if list(stocks_config.keys()) == ["DEFAULT"]:
        print(
            "portfolio.ini has no stocks added or does not exist. There is nothing to show."
        )
        exit()  # nothing else to do! Just force exit.


if __name__ == "__main__":
    main()

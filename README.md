# cliStocksTracker
[![GitHub](https://img.shields.io/github/license/ConradSelig/cliStocksTracker?style=for-the-badge)](https://github.com/ericm/stonks/blob/master/LICENSE)
[![GitHub contributors](https://img.shields.io/github/contributors/ConradSelig/cliStocksTracker?style=for-the-badge)](https://github.com/ericm/stonks/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/ConradSelig/cliStocksTracker?style=for-the-badge)](https://github.com/ericm/stonks/commits/master)

A command line stock market / portfolio tracker originally insipred by [Ericm's Stonks](https://github.com/ericm/stonks) program, featuring unicode for incredibly high detailed
graphs even in a terminal.

![Screenshot from 2021-02-01 12-21-08](https://user-images.githubusercontent.com/31974507/106507584-808d3600-6488-11eb-9805-8019b34fabf7.png)

## Installation

This project is still in Beta, so there is no executable packaged with the project.

Requirements:
  * Python >= 3.6.9
  * plotille >= 3.7.2
  * numpy >= 1.19.5
  * yfinance >= 0.1.55
  * pytz >= 2021.1
  * colorama >= 0.4.4
  
### Manual
```
$ git clone https://github.com/ConradSelig/cliStocksTracker
$ cd cliStocksTracker
$ python3 -m pip install -r requirements.txt
```

## Usage
```
$ python3 main.py
```
## Configuration

cliStocksTracker relies on two config files, "config" and "stocks_config".

### config

```
frame:
  width: [ graph width ]
  height: [ graph height ]
kwargs:
  independent_graphs: [ True | False ]
  timezone: [ pytz timezone stamp (ex. "America/New_York", "Asia/Shanghai", etc) ]
```
If indepentant_graphs is True, all the given stocks will be graphed on the same plot, otherwise all of the given stocks will be printed on independent plots.
There is currently no grouping of stocks, either manual or automatic (planned).

**All keys in the config file are required.**

### stocks_config

```
[ stock symbol ]:
  graph: [ True | False ]
  owned: [ float ]
  bought_at: [ float ]
[ stock symbol ]:
  graph: [ True | False ]
  owned: [ float ]
  bought_at: [ float ]
...
```

Each stock symbol has three additional config settings:
1. "graph": Determins if a graph is plotted of this symbol
2. "owned": Count of the number of stocks owned of this symbol
3. "bought_at": Price the stocks we're originally bought at, this is used to calculate portfolio delta.

There is currently no support for stocks of the same label being bought at different prices (planned).

There is currently no support for custom selection of symbol colors within a graph (planned).

**All keys in the stocks_config file are optional.**

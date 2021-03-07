# cliStocksTracker
[![GitHub](https://img.shields.io/github/license/ConradSelig/cliStocksTracker?style=for-the-badge)](https://github.com/ConradSelig/cliStocksTracker/blob/main/LICENSE)
[![GitHub contributors](https://img.shields.io/github/contributors/ConradSelig/cliStocksTracker?style=for-the-badge)](https://github.com/ConradSelig/cliStocksTracker/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/ConradSelig/cliStocksTracker?style=for-the-badge)](https://github.com/ConradSelig/cliStocksTracker/commits/main)

A command line stock market / portfolio tracker originally insipred by [Ericm's Stonks](https://github.com/ericm/stonks) program, featuring unicode for incredibly high detailed
graphs even in a terminal.

![image](https://user-images.githubusercontent.com/31974507/107873060-ac3af380-6e6c-11eb-8673-10fed1a16f0a.png)

## Installation

This project is still in Beta, so there is no executable packaged with the project.

Requirements:
  * Python >= 3.6.9
  * plotille >= 3.7.2
  * numpy >= 1.19.5
  * yfinance >= 0.1.55
  * pytz >= 2021.1
  * colorama >= 0.4.4
  * webcolors==1.11.1
  
### Manual
```
$ git clone https://github.com/ConradSelig/cliStocksTracker
$ cd cliStocksTracker
$ python3 -m pip install -r requirements.txt
```

## Usage
```
usage: cliStocksTracker.py [-h] [--width WIDTH] [--height HEIGHT]
                           [--independent-graphs] [--timezone TIMEZONE]
                           [-r ROUNDING_MODE] [-ti TIME_INTERVAL]
                           [-tp TIME_PERIOD] [--config CONFIG]
                           [--portfolio-config PORTFOLIO_CONFIG] [-g]

Options for cliStockTracker.py

optional arguments:
  -h, --help            show this help message and exit
  --width WIDTH         integer for the width of the chart (default is 80)
  --height HEIGHT       integer for the height of the chart (default is 20)
  --independent-graphs  show a chart for each stock
  --timezone TIMEZONE   your timezone (ex: America/New_York)
  -r ROUNDING_MODE, --rounding-mode ROUNDING_MODE
                        how should numbers be rounded (math | down)
  -ti TIME_INTERVAL, --time-interval TIME_INTERVAL
                        specify time interval for graphs (ex: 1m, 15m, 1h)
  -tp TIME_PERIOD, --time-period TIME_PERIOD
                        specify time period for graphs (ex: 15m, 1h, 1d)
  --config CONFIG       path to a config.ini file
  --portfolio-config PORTFOLIO_CONFIG
                        path to a portfolio.ini file with your list of stonks
  -g, --generate-config
                        generates example config files
```

Do note that any given command line argument will override settings from the config file.
## Configuration

cliStocksTracker relies on two config files, "config.ini" and "portfolio.ini".

### config.ini

```
[Frame]
width=[ graph width ]
height=[ graph height ]

[General]
independent_graphs=[ True | False ]
timezone=[ pytz timezone stamp (ex. "America/New_York", "Asia/Shanghai", etc) ]
rounding_mode=[math | down]
```
If independent_graphs is True, all the given stocks will be graphed on the same plot, otherwise all of the given stocks will be printed on independent plots.
There is currently no grouping of stocks, either manual or automatic (planned).

A default config.ini is packaged with the project.

**All keys in config.ini file are required.**

### portfolio.ini

```
[ stock symbol ]
graph=[ True | False ]
owned=[ float ]
bought_at=[ float ]
color=[str]

[ stock symbol ]
graph=[ True | False ]
owned=[ float ]
bought_at=[ float ]
color=[str]
...
```

Each stock symbol has four additional config settings:
1. "graph": Determines if a graph is plotted of this symbol
2. "owned": Count of the number of stocks owned of this symbol
3. "bought_at": Price the stocks we're originally bought at, this is used to calculate portfolio delta.
4. "color": The custom color to display the stock on the graphs. This is not a mandatory configuration setting, and if left empty automatic color selection will take place.

The color can be chosen from the following list of colors:
['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 
'chocolate', 'coral', 'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgrey', 'darkgreen', 'darkkhaki', 'darkmagenta', 
'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet',
 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray',
 'grey', 'green', 'greenyellow', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral',
 'lightcyan', 'lightgoldenrodyellow', 'lightgray', 'lightgrey', 'lightgreen', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightslategrey',
 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen',
 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy', 'oldlace',
 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum',
 'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray',
 'slategrey', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']

There is currently no support for stocks of the same label being bought at different prices (planned).

**"owned" and "bought_at" are required keys, all others optional."**


## Similar projects

- [DidierRLopes/GameStonkTerminal](https://github.com/DidierRLopes/GamestonkTerminal) - Python
- [aranair/rtscli](https://github.com/aranair/rtscli) - Python
---
- [mop-tracker/mop](https://github.com/mop-tracker/mop) - Go
- [achannarasappa/ticker](https://github.com/achannarasappa/ticker) - Go
---
- [tarkah/tickrs](https://github.com/tarkah/tickrs) - Rust

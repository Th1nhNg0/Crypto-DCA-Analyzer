# Crypto DCA Calculator

A Python tool to analyze Dollar Cost Averaging (DCA) investment strategy for cryptocurrencies, supporting multiple pairs and custom buy periods.

![DCA Analysis Example](./dca/dca_multiple.png)

## Features

- Historical price data fetching from various exchanges (default: Binance)
- Multi-pair DCA investment simulation with custom allocations
- Flexible buy periods (daily, weekly, biweekly, monthly)
- Detailed investment analysis for each pair
- Overall portfolio performance metrics
- Visual representation of results with price charts and P&L graphs
- Support for different trading pairs with percentage allocation
- Configurable daily investment amount

## Requirements

```
pandas
matplotlib
ccxt
colorama
```

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage (single pair):
```bash
python dca_btc.py --daily-investment 10 --pairs BTC/USDT:100
```

Multiple pairs with allocation:
```bash
python dca_btc.py --daily-investment 100 --pairs BTC/USDT:80 ETH/USDT:20
```

Weekly investment:
```bash
python dca_btc.py --daily-investment 100 --pairs BTC/USDT:60 ETH/USDT:30 SOL/USDT:10 --buy-period 1w
```

Advanced options:
```bash
python dca_btc.py --start-date 2020-01-01 --end-date 2023-12-31 --daily-investment 100 \
                  --pairs BTC/USDT:50 ETH/USDT:30 DOT/USDT:20 \
                  --exchange binance --buy-period 2w
```

### Arguments

- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format
- `--last-days`: Calculate for the last N days
- `--daily-investment`: Daily investment amount in USD
- `--exchange`: Exchange to fetch data from (default: binance)
- `--pairs`: List of trading pairs with allocation percentages (e.g., BTC/USDT:80 ETH/USDT:20)
- `--buy-period`: Investment frequency (e.g., 1d=daily, 1w=weekly, 2w=biweekly, 1m=monthly)

## Output

The tool generates:
1. Detailed investment summary for each pair in the console
2. Overall portfolio performance metrics
3. Price history and average cost charts for each pair
4. Profit/loss percentage charts for each pair
5. Saves combined chart to `dca/dca_multiple.png`

## Examples

1. Invest $100 daily, 80% in BTC and 20% in ETH:
```bash
python dca_btc.py --daily-investment 100 --pairs BTC/USDT:80 ETH/USDT:20
```

2. Weekly $500 investment split across three coins:
```bash
python dca_btc.py --daily-investment 500 --pairs BTC/USDT:50 ETH/USDT:30 SOL/USDT:20 --buy-period 1w
```

3. Monthly $1000 investment in BTC only:
```bash
python dca_btc.py --daily-investment 1000 --pairs BTC/USDT:100 --buy-period 1m
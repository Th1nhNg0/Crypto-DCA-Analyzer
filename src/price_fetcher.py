import ccxt
import pandas as pd
import time
from datetime import datetime
from rich.console import Console

console = Console()


class PriceDataFetcher:
    def __init__(self, exchange_id="binance", progress_context=None):
        self.exchange = self._initialize_exchange(exchange_id)
        self.progress = progress_context

    def _initialize_exchange(self, exchange_id):
        try:
            exchange_class = getattr(ccxt, exchange_id)
            return exchange_class({"enableRateLimit": True})
        except (AttributeError, Exception) as e:
            console.print(
                f"[yellow]Error initializing exchange {exchange_id}: {e}[/yellow]"
            )
            console.print("[yellow]Falling back to Binance...[/yellow]")
            return ccxt.binance({"enableRateLimit": True})

    def fetch_historical_data(self, symbol, start_date, end_date, task_id=None):
        timeframe = "1d"
        data = []
        current = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        while current < end_ts:
            try:
                if self.progress and task_id:
                    self.progress.update(
                        task_id,
                        description=f"Fetching {symbol} data for {datetime.fromtimestamp(current / 1000).strftime('%Y-%m-%d')}",
                    )

                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, current, 1000)
                if not ohlcv:
                    break

                # Only include data points up to end_date
                filtered_ohlcv = [candle for candle in ohlcv if candle[0] <= end_ts]
                if filtered_ohlcv:
                    data.extend(filtered_ohlcv)

                if not filtered_ohlcv or filtered_ohlcv[-1][0] >= end_ts:
                    break

                current = ohlcv[-1][0] + 86400000
                time.sleep(self.exchange.rateLimit / 1000)
            except ccxt.RateLimitExceeded:
                console.print("[yellow]Rate limit reached, waiting...[/yellow]")
                time.sleep(30)
            except ccxt.ExchangeError as e:
                console.print(f"[red]Exchange error: {e}[/red]")
                if not data:
                    raise
                break

        df = self._process_ohlcv_data(data)
        # Filter data to exactly match the date range
        df = df[
            (df["Start"].dt.date >= start_date.date())
            & (df["Start"].dt.date <= end_date.date())
        ]
        return df

    def _process_ohlcv_data(self, data):
        df = pd.DataFrame(
            data, columns=["Start", "Open", "High", "Low", "Close", "Volume"]
        )
        df["Start"] = pd.to_datetime(df["Start"], unit="ms")
        return df.sort_values("Start").drop_duplicates(subset=["Start"])

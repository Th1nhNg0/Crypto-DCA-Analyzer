import ccxt
import pandas as pd
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

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
        retry_count = 0
        max_retries = 3
        backoff_time = 30  # Initial backoff time in seconds

        while current < end_ts:
            try:
                if self.progress and task_id:
                    current_date = datetime.fromtimestamp(current / 1000)
                    progress_desc = f"[yellow]Fetching {symbol}[/yellow] ([cyan]{current_date.strftime('%Y-%m-%d')}[/cyan])"
                    self.progress.update(task_id, description=progress_desc)

                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, current, 1000)
                if not ohlcv:
                    break

                # Filter out data points after end_date
                filtered_ohlcv = [d for d in ohlcv if d[0] <= end_ts]
                data.extend(filtered_ohlcv)

                if not filtered_ohlcv or filtered_ohlcv[-1][0] >= end_ts:
                    break

                current = ohlcv[-1][0] + 86400000  # Move to next day
                time.sleep(self.exchange.rateLimit / 1000)
                retry_count = 0  # Reset retry count on successful request
                
            except ccxt.RateLimitExceeded:
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = backoff_time * (2 ** (retry_count - 1))  # Exponential backoff
                    if self.progress and task_id:
                        self.progress.update(
                            task_id,
                            description=f"[yellow]Rate limit reached for {symbol}, waiting {wait_time}s (Attempt {retry_count}/{max_retries})[/yellow]"
                        )
                    time.sleep(wait_time)
                else:
                    console.print(Panel(
                        f"[red]Maximum retries reached for {symbol}[/red]\n"
                        "[yellow]The exchange rate limit was reached too many times.[/yellow]\n"
                        "Try again later or use a different exchange.",
                        title="⚠️ Rate Limit Error",
                        border_style="red"
                    ))
                    raise
                    
            except ccxt.NetworkError as e:
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = backoff_time * (2 ** (retry_count - 1))
                    if self.progress and task_id:
                        self.progress.update(
                            task_id,
                            description=f"[yellow]Network error for {symbol}, retrying in {wait_time}s (Attempt {retry_count}/{max_retries})[/yellow]"
                        )
                    time.sleep(wait_time)
                else:
                    console.print(Panel(
                        f"[red]Network error while fetching {symbol}: {str(e)}[/red]\n"
                        "[yellow]Please check your internet connection and try again.[/yellow]",
                        title="❌ Network Error",
                        border_style="red"
                    ))
                    raise
                    
            except ccxt.ExchangeError as e:
                console.print(Panel(
                    f"[red]Exchange error while fetching {symbol}: {str(e)}[/red]\n"
                    "[yellow]The exchange might be having issues with this trading pair.[/yellow]",
                    title="❌ Exchange Error",
                    border_style="red"
                ))
                if not data:  # Only raise if we haven't fetched any data yet
                    raise
                break

        return self._process_ohlcv_data(data)

    def _process_ohlcv_data(self, data):
        df = pd.DataFrame(
            data, columns=["Start", "Open", "High", "Low", "Close", "Volume"]
        )
        df["Start"] = pd.to_datetime(df["Start"], unit="ms")
        df = df[
            df["Start"] <= pd.Timestamp(df["Start"].iloc[-1].date())
        ]  # Ensure we only include full days
        return df.sort_values("Start").drop_duplicates(subset=["Start"])

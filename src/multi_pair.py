from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from .price_fetcher import PriceDataFetcher
from .calculator import DCACalculator

console = Console()

class MultiPairDCAManager:
    def __init__(self, exchange_id='binance'):
        self.fetcher = PriceDataFetcher(exchange_id)
        
    def calculate_multiple_pairs(self, pairs_allocation, daily_investment, start_date, end_date, buy_period='1d'):
        results = {}
        total_allocation = sum(pairs_allocation.values())
        
        if abs(total_allocation - 100) > 0.01:
            error_panel = Panel(
                f"[red]Total allocation must equal 100% (current: {total_allocation}%)[/red]\n\n"
                "Current allocations:\n" +
                "\n".join(f"[yellow]• {pair}:[/yellow] [cyan]{alloc}%[/cyan]" for pair, alloc in pairs_allocation.items()),
                title="❌ Invalid Allocation",
                border_style="red"
            )
            console.print(error_panel)
            raise ValueError("Total allocation must equal 100%")

        # Display analysis parameters in a cleaner format
        console.print("\n")
        console.print(Panel(
            f"[cyan]Daily Investment:[/cyan] ${daily_investment:.2f}\n"
            f"[cyan]Period:[/cyan] {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
            f"[cyan]Buy Frequency:[/cyan] {buy_period}\n"
            f"[cyan]Exchange:[/cyan] {self.fetcher.exchange.name.upper()}\n\n"
            "[bold]Selected Pairs:[/bold]\n" +
            "\n".join(f"[yellow]• {pair}:[/yellow] [cyan]{alloc}%[/cyan]" for pair, alloc in pairs_allocation.items()),
            title="🚀 DCA Analysis Parameters",
            border_style="cyan"
        ))
        console.print("\n")
        
        for pair, allocation in pairs_allocation.items():
            pair_investment = daily_investment * (allocation / 100)
            price_data = self.fetcher.fetch_historical_data(pair, start_date, end_date)
            calculator = DCACalculator(price_data, pair_investment, buy_period)
            results[pair] = {
                'allocation': allocation,
                'calculator': calculator,
                'results': calculator.results
            }
        
        return results
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from rich.panel import Panel
from .price_fetcher import PriceDataFetcher
from .calculator import DCACalculator

console = Console()

class MultiPairDCAManager:
    def __init__(self, exchange_id='binance'):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
            refresh_per_second=4
        )
        self.fetcher = PriceDataFetcher(exchange_id, self.progress)
        
    def calculate_multiple_pairs(self, pairs_allocation, daily_investment, start_date, end_date, buy_period='1d'):
        results = {}
        total_allocation = sum(pairs_allocation.values())
        if abs(total_allocation - 100) > 0.01:
            error_msg = f"[red]Error: Total allocation must equal 100% (current: {total_allocation}%)[/red]\n\n"
            error_msg += "Current allocations:\n"
            for pair, alloc in pairs_allocation.items():
                error_msg += f"• {pair}: {alloc}%\n"
            console.print(Panel(error_msg, title="❌ Invalid Allocation", border_style="red"))
            raise ValueError("Total allocation must equal 100%")

        console.print(Panel(
            f"[cyan]Starting DCA analysis with:[/cyan]\n"
            f"• Investment: ${daily_investment:.2f} per day\n"
            f"• Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
            f"• Buy frequency: {buy_period}\n"
            f"• Pairs:\n" +
            "\n".join(f"  - {pair}: {alloc}%" for pair, alloc in pairs_allocation.items()),
            title="💡 Analysis Parameters",
            border_style="cyan"
        ))
        
        with self.progress:
            for pair, allocation in pairs_allocation.items():
                task_id = self.progress.add_task(f"Processing {pair}...", total=None)
                pair_investment = daily_investment * (allocation / 100)
                price_data = self.fetcher.fetch_historical_data(pair, start_date, end_date, task_id)
                calculator = DCACalculator(price_data, pair_investment, buy_period)
                results[pair] = {
                    'allocation': allocation,
                    'calculator': calculator,
                    'results': calculator.results
                }
                self.progress.update(task_id, completed=True)
        
        return results
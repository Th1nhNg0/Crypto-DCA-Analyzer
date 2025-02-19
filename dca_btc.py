import argparse
from datetime import datetime, timedelta
import ccxt
import os
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table
from src.multi_pair import MultiPairDCAManager
from src.visualizer import DCAVisualizer
from src.portfolio_analyzer import PortfolioAnalyzer

console = Console()

def validate_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        console.print(Panel(
            "[red]Invalid date format. Please use YYYY-MM-DD format.[/red]",
            title="❌ Date Error",
            border_style="red"
        ))
        return None

def validate_pairs(pairs_str):
    try:
        pairs_allocation = {}
        for pair_alloc in pairs_str:
            pair, allocation = pair_alloc.split(":")
            pairs_allocation[pair] = float(allocation)
        return pairs_allocation
    except ValueError:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="🚀 Cryptocurrency Dollar Cost Averaging (DCA) Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--last-days", type=int, help="Calculate for the last N days")
    parser.add_argument("--daily-investment", type=float, default=1.0,
                      help="Daily investment amount in USD")
    parser.add_argument("--exchange", type=str, default="binance",
                      help="Exchange to fetch data from")
    parser.add_argument("--pairs", type=str, nargs="+",
                      default=["BTC/USDT:100"],
                      help="Trading pairs with allocation (e.g., BTC/USDT:80 ETH/USDT:20)")
    parser.add_argument("--buy-period", type=str, default="1d",
                      help="Buy period (1d=daily, 1w=weekly, 2w=biweekly, 1m=monthly)")
    parser.add_argument("--plot-type", type=str,
                      choices=["all", "total", "both"],
                      default="both",
                      help="Type of plot to generate")

    args = parser.parse_args()

    # Create output directory
    os.makedirs("dca", exist_ok=True)

    # Show welcome message
    console.print(Panel.fit(
        "[bold cyan]Welcome to the Crypto DCA Analyzer![/bold cyan]\n"
        "This tool will help you analyze your cryptocurrency DCA strategy.",
        title="🚀 DCA Analyzer",
        border_style="cyan"
    ))

    # Validate and process dates
    end_date = datetime.now() if not args.end_date else validate_date(args.end_date)
    if args.last_days:
        start_date = end_date - timedelta(days=args.last_days)
    else:
        start_date = validate_date(args.start_date or "2020-01-01")

    if not start_date or not end_date:
        return

    # Validate pairs
    pairs_allocation = validate_pairs(args.pairs)
    if not pairs_allocation:
        console.print(Panel(
            "[red]Invalid pair format. Use PAIR:PERCENTAGE (e.g., BTC/USDT:80)[/red]\n"
            "Example: --pairs BTC/USDT:60 ETH/USDT:40",
            title="❌ Format Error",
            border_style="red"
        ))
        return

    try:
        # Initialize manager and run analysis
        manager = MultiPairDCAManager(args.exchange)
        results = manager.calculate_multiple_pairs(
            pairs_allocation,
            args.daily_investment,
            start_date,
            end_date,
            args.buy_period
        )

        # Generate timestamp for consistent file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create portfolio analyzer and display results
        analyzer = PortfolioAnalyzer(results)
        analyzer.display_portfolio_summary(timestamp)

        # Generate charts based on plot-type
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            if args.plot_type in ["all", "both"]:
                individual_task = progress.add_task("[cyan]Generating individual charts...", total=len(results))
                for pair, data in results.items():
                    token = pair.split("/")[0]
                    visualizer = DCAVisualizer(data["results"], token, start_date, end_date)
                    visualizer.plot_single_pair(timestamp)
                    progress.advance(individual_task)

            if args.plot_type in ["total", "both"]:
                portfolio_task = progress.add_task("[cyan]Generating portfolio chart...", total=1)
                first_pair = list(results.keys())[0]
                first_data = results[first_pair]["results"]
                visualizer = DCAVisualizer(first_data, "PORTFOLIO", start_date, end_date)
                visualizer.plot_total_portfolio(results, timestamp)
                progress.advance(portfolio_task)

        # Show completion message
        console.print(Panel(
            "[green]Analysis completed successfully! 🎉[/green]\n\n"
            f"[cyan]Analysis files have been saved with timestamp {timestamp} in the dca/ folder[/cyan]\n"
            "📊 Check out the generated charts for detailed insights!",
            title="✅ Analysis Complete",
            border_style="green"
        ))

    except ccxt.NetworkError as e:
        console.print(Panel(
            f"[red]Network error while fetching data: {str(e)}[/red]\n"
            "[yellow]Please check your internet connection and try again.[/yellow]",
            title="❌ Network Error",
            border_style="red"
        ))
    except ccxt.ExchangeError as e:
        console.print(Panel(
            f"[red]Exchange error: {str(e)}[/red]\n"
            "[yellow]The exchange might be experiencing issues. Try again later or use a different exchange.[/yellow]",
            title="❌ Exchange Error",
            border_style="red"
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]An unexpected error occurred: {str(e)}[/red]",
            title="❌ Error",
            border_style="red"
        ))
        raise

if __name__ == "__main__":
    main()

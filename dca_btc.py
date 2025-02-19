import argparse
from datetime import datetime, timedelta
import ccxt
import os
from rich.console import Console
from rich.panel import Panel
from src.multi_pair import MultiPairDCAManager
from src.visualizer import DCAVisualizer
from src.portfolio_analyzer import PortfolioAnalyzer

console = Console()


def main():
    os.makedirs("dca", exist_ok=True)
    parser = argparse.ArgumentParser(
        description="Cryptocurrency Dollar Cost Averaging (DCA) Calculator"
    )
    parser.add_argument(
        "--start-date", type=str, help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")
    parser.add_argument("--last-days", type=int, help="Calculate for the last N days")
    parser.add_argument(
        "--daily-investment",
        type=float,
        default=1.0,
        help="Daily investment amount in USD",
    )
    parser.add_argument(
        "--exchange", type=str, default="binance", help="Exchange to fetch data from"
    )
    parser.add_argument(
        "--pairs",
        type=str,
        nargs="+",
        default=["BTC/USDT:100"],
        help="Trading pairs with allocation in format PAIR:PERCENTAGE (e.g., BTC/USDT:80 ETH/USDT:20)",
    )
    parser.add_argument(
        "--buy-period",
        type=str,
        default="1d",
        help="Buy period (e.g., 1d=daily, 1w=weekly, 2w=biweekly, 1m=monthly)",
    )
    parser.add_argument(
        "--plot-type",
        type=str,
        choices=["all", "total", "both"],
        default="all",
        help="Type of plot to generate: all (individual pairs), total (portfolio), or both",
    )

    args = parser.parse_args()

    # Parse pairs and allocations
    pairs_allocation = {}
    try:
        for pair_alloc in args.pairs:
            pair, allocation = pair_alloc.split(":")
            pairs_allocation[pair] = float(allocation)
    except ValueError:
        console.print(
            Panel(
                "[red]Invalid pair format. Use PAIR:PERCENTAGE (e.g., BTC/USDT:80)[/red]\n"
                "Example: --pairs BTC/USDT:60 ETH/USDT:40",
                title="❌ Format Error",
                border_style="red",
            )
        )
        return

    # Determine date range
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()
        # Round to the start of today
        end_date = datetime.combine(end_date.date(), datetime.min.time())

    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    elif args.last_days:
        start_date = end_date - timedelta(days=args.last_days)
    else:
        start_date = datetime.strptime("2020-01-01", "%Y-%m-%d")

    # Validate date range
    if start_date > end_date:
        console.print(
            Panel(
                "[red]Start date cannot be after end date[/red]",
                title="❌ Date Error",
                border_style="red",
            )
        )
        return

    # Initialize manager and run analysis
    manager = MultiPairDCAManager(args.exchange)
    try:
        results = manager.calculate_multiple_pairs(
            pairs_allocation,
            args.daily_investment,
            start_date,
            end_date,
            args.buy_period,
        )

        # Generate timestamp once for consistent file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create portfolio analyzer and display results
        analyzer = PortfolioAnalyzer(results)
        analyzer.display_portfolio_summary(timestamp)  # Pass timestamp for CSV naming

        # Create the charts directory
        os.makedirs("dca", exist_ok=True)

        # Generate charts based on plot-type
        if args.plot_type in ["all", "both"]:
            for pair, data in results.items():
                token = pair.split("/")[0]
                visualizer = DCAVisualizer(data["results"], token, start_date, end_date)
                visualizer.plot_single_pair(timestamp)

        if args.plot_type in ["total", "both"]:
            # Use the first pair's data to initialize the visualizer
            first_pair = list(results.keys())[0]
            first_data = results[first_pair]["results"]
            visualizer = DCAVisualizer(first_data, "PORTFOLIO", start_date, end_date)
            visualizer.plot_total_portfolio(results, timestamp)

        # Show completion message with new naming pattern
        console.print(
            Panel(
                "[green]Analysis completed successfully! 🎉[/green]\n"
                + f"Analysis files have been saved with timestamp {timestamp} in the [cyan]dca/[/cyan] folder",
                title="✅ Complete",
                border_style="green",
            )
        )

    except ValueError as e:
        pass
    except ccxt.NetworkError as e:
        console.print(
            Panel(
                f"[red]Network error while fetching data: {str(e)}[/red]\n"
                + "[yellow]Please check your internet connection and try again.[/yellow]",
                title="❌ Network Error",
                border_style="red",
            )
        )
    except ccxt.ExchangeError as e:
        console.print(
            Panel(
                f"[red]Exchange error: {str(e)}[/red]\n"
                + "[yellow]The exchange might be experiencing issues. Try again later or use a different exchange.[/yellow]",
                title="❌ Exchange Error",
                border_style="red",
            )
        )
    except Exception as e:
        console.print(
            Panel(f"[red]{str(e)}[/red]", title="❌ Error", border_style="red")
        )


if __name__ == "__main__":
    main()

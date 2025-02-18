import argparse
from datetime import datetime, timedelta
import ccxt
import os
from rich.console import Console
from rich.panel import Panel
from src.multi_pair import MultiPairDCAManager
from src.visualizer import DCAVisualizer

console = Console()

def main():
    parser = argparse.ArgumentParser(description='Cryptocurrency Dollar Cost Averaging (DCA) Calculator')
    parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=str, help='End date in YYYY-MM-DD format')
    parser.add_argument('--last-days', type=int, help='Calculate for the last N days')
    parser.add_argument('--daily-investment', type=float, default=1.0, help='Daily investment amount in USD')
    parser.add_argument('--exchange', type=str, default='binance', help='Exchange to fetch data from')
    parser.add_argument('--pairs', type=str, nargs='+', default=['BTC/USDT:100'], 
                      help='Trading pairs with allocation in format PAIR:PERCENTAGE (e.g., BTC/USDT:80 ETH/USDT:20)')
    parser.add_argument('--buy-period', type=str, default='1d',
                      help='Buy period (e.g., 1d=daily, 1w=weekly, 2w=biweekly, 1m=monthly)')
    
    args = parser.parse_args()
    
    # Parse pairs and allocations
    pairs_allocation = {}
    try:
        for pair_alloc in args.pairs:
            pair, allocation = pair_alloc.split(':')
            pairs_allocation[pair] = float(allocation)
    except ValueError:
        console.print(
            Panel(
                "[red]Invalid pair format. Use PAIR:PERCENTAGE (e.g., BTC/USDT:80)[/red]\n"
                "Example: --pairs BTC/USDT:60 ETH/USDT:40",
                title="❌ Format Error",
                border_style="red"
            )
        )
        return
    
    # Determine date range
    end_date = datetime.now() if not args.end_date else datetime.strptime(args.end_date, '%Y-%m-%d')
    start_date = (end_date - timedelta(days=args.last_days)) if args.last_days else \
                datetime.strptime(args.start_date or '2020-01-01', '%Y-%m-%d')
    
    # Initialize manager and run analysis
    manager = MultiPairDCAManager(args.exchange)
    try:
        results = manager.calculate_multiple_pairs(pairs_allocation, args.daily_investment, 
                                                start_date, end_date, args.buy_period)
        
        # Get first pair for visualization
        first_pair = list(results.keys())[0]
        first_token = first_pair.split('/')[0]
        
        # Create visualizer and plot results
        visualizer = DCAVisualizer(results[first_pair]['results'], 
                                 first_token, start_date, end_date)
        visualizer.plot_single_pair()
        
        # Show completion message
        console.print(Panel(
            "[green]Analysis completed successfully! 🎉[/green]\n" +
            "Charts have been saved to the [cyan]dca/[/cyan] folder.",
            title="✅ Complete",
            border_style="green"
        ))
            
    except ValueError as e:
        pass
    except ccxt.NetworkError as e:
        console.print(Panel(
            f"[red]Network error while fetching data: {str(e)}[/red]\n" +
            "[yellow]Please check your internet connection and try again.[/yellow]",
            title="❌ Network Error",
            border_style="red"
        ))
    except ccxt.ExchangeError as e:
        console.print(Panel(
            f"[red]Exchange error: {str(e)}[/red]\n" +
            "[yellow]The exchange might be experiencing issues. Try again later or use a different exchange.[/yellow]",
            title="❌ Exchange Error",
            border_style="red"
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]{str(e)}[/red]",
            title="❌ Error",
            border_style="red"
        ))

if __name__ == "__main__":
    main()

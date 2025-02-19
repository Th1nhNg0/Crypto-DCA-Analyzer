from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import DOUBLE

console = Console()

class PortfolioAnalyzer:
    def __init__(self, results):
        self.results = results
        
    def _format_currency(self, value):
        return f"${value:,.2f}"
        
    def _format_percentage(self, value, include_plus=True):
        if include_plus and value > 0:
            return f"+{value:.2f}%"
        return f"{value:.2f}%"
        
    def _create_progress_bar(self, percentage, width=20):
        filled = int(width * (percentage / 100))
        color = "green" if percentage >= 80 else "yellow" if percentage >= 20 else "red"
        
        # Create the bar and percentage display
        bar = ("█" * filled) + "░" * (width - filled)
        percentage_text = f" [{color}]{percentage:>5.1f}%[/{color}]"
        
        return f"[{color}]{bar}[/{color}]{percentage_text}"

    def _get_trend_arrow(self, value):
        if value > 100:
            return "⬆️"  # Exceptional gain (>100%)
        elif value > 50:
            return "↗️↗️"  # Very strong uptrend
        elif value > 20:
            return "↗️"  # Strong uptrend
        elif value > 5:
            return "➡️↗️"  # Moderate uptrend
        elif value > -5:
            return "➡️"  # Sideways
        elif value > -20:
            return "➡️↘️"  # Moderate downtrend
        elif value > -50:
            return "↘️"  # Strong downtrend
        else:
            return "⬇️"  # Severe downtrend
        
    def display_pair_summary(self, pair, data):
        allocation = data['allocation']
        results = data['results']
        current_price = results['prices'][-1]
        total_invested = results['total_invested']
        current_value = results['current_value']
        pnl = current_value - total_invested
        pnl_percentage = (pnl / total_invested * 100) if total_invested > 0 else 0
        trend_arrow = self._get_trend_arrow(pnl_percentage)
        profit_color = "green" if pnl_percentage >= 0 else "red"
        
        # Create fear index display
        fear_index = results['fear_index']
        fear_color = "green" if fear_index < 30 else "yellow" if fear_index < 60 else "red"
        fear_emoji = "😊" if fear_index < 30 else "😰" if fear_index < 60 else "😱"
        fear_days = f"{results['negative_pnl_days']} of {results['total_days']}"
        
        # Create summary with consistent styling
        token = pair.split('/')[0]
        quote = pair.split('/')[1]
        
        summary = ""
        # Add token icon based on common cryptocurrencies
        token_icon = {
            'BTC': '₿',
            'ETH': 'Ξ',
            'SOL': '◎',
            'DOT': '●',
            'USDT': '₮',
        }.get(token, '💲')
        
        summary += f"[bold cyan]{token_icon} {token}[/bold cyan]/[dim]{quote}[/dim] {trend_arrow}\n" + "─" * 50 + "\n"
        
        # Investment metrics with improved visual hierarchy
        alloc_bar = self._create_progress_bar(allocation, 25)  # Slightly reduced width for better layout
        daily_amount = results['total_invested'] / len(results['dates']) if len(results['dates']) > 0 else 0
        
        summary += f"💼 [dim]Allocation[/dim]        │ {alloc_bar}\n"
        summary += f"💰 [dim]Total Invested[/dim]    │ [bold]{self._format_currency(total_invested)}[/bold] ([dim]~{self._format_currency(daily_amount)}/day[/dim])\n"
        summary += f"💲 [dim]Amount[/dim]            │ [bold]{results['total_crypto']:.8f}[/bold] {token}\n"
        summary += f"💎 [dim]Current Value[/dim]     │ [bold]{self._format_currency(current_value)}[/bold]\n"
        summary += f"📊 [dim]Net Profit/Loss[/dim]   │ [bold {profit_color}]{self._format_currency(pnl)}[/bold {profit_color}] ([{profit_color}]{self._format_percentage(pnl_percentage)}[/{profit_color}])\n"
        
        # Add fear index metrics
        summary += f"😱 [dim]Fear Index[/dim]        │ [{fear_color}]{fear_emoji} {fear_index:.1f}% ({fear_days} days)[/{fear_color}]\n"
        
        # Price metrics with highlighting
        summary += "\n[bold cyan]Price Analysis[/bold cyan]\n" + "─" * 50 + "\n"
        avg_vs_current = "green" if current_price > results['cost_basis'] else "red"
        
        summary += f"📈 [dim]Average Cost[/dim]      │ [bold]{self._format_currency(results['cost_basis'])}[/bold]\n"
        summary += f"🎯 [dim]Current Price[/dim]     │ [bold {avg_vs_current}]{self._format_currency(current_price)}[/bold {avg_vs_current}]\n"
        
        if 'highest_price' in results and 'lowest_price' in results:
            high_date = results.get('best_day', [None, None])[1]
            low_date = results.get('worst_day', [None, None])[1]
            
            high_date_str = f" ([dim]{high_date.strftime('%Y-%m-%d')}[/dim])" if high_date else ""
            low_date_str = f" ([dim]{low_date.strftime('%Y-%m-%d')}[/dim])" if low_date else ""
            
            summary += f"🔺 [dim]Highest Price[/dim]     │ [bold]{self._format_currency(results['highest_price'])}[/bold]{high_date_str}\n"
            summary += f"🔻 [dim]Lowest Price[/dim]      │ [bold]{self._format_currency(results['lowest_price'])}[/bold]{low_date_str}\n"
        
        console.print(Panel(
            summary,
            title=f"[{profit_color}]{'🟢' if pnl_percentage >= 0 else '🔴'} {token} Analysis[/{profit_color}]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        return {
            'invested': total_invested,
            'current_value': current_value,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage
        }
    
    def display_portfolio_summary(self, timestamp=None):
        console.print("\n")
        console.print(Panel(
            "[bold cyan]🚀 Multiple Pairs DCA Analysis[/bold cyan]",
            style="cyan"
        ))
        
        total_stats = {'invested': 0, 'current_value': 0, 'pnl': 0}
        pair_stats = {}
        
        # First display individual pair summaries
        for pair, data in self.results.items():
            stats = self.display_pair_summary(pair, data)
            pair_stats[pair] = stats
            for key in total_stats:
                total_stats[key] += stats[key]
        
        # Save analysis to CSV
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"dca/dca_analysis_{timestamp}.csv"
        self._save_analysis_to_csv(pair_stats, total_stats, csv_file)
        
        # Display overall portfolio performance with enhanced styling
        total_pnl_percentage = (total_stats['pnl'] / total_stats['invested'] * 100) if total_stats['invested'] > 0 else 0
        profit_color = "green" if total_pnl_percentage >= 0 else "red"
        
        # Create a visually appealing portfolio summary
        summary = ""
        
        # Portfolio allocation section with gradient bars
        summary += "[bold cyan]Portfolio Allocation[/bold cyan]\n" + "─" * 50 + "\n"
        for pair, data in self.results.items():
            alloc_bar = self._create_progress_bar(data['allocation'], 25)
            roi = pair_stats[pair]['pnl_percentage']
            roi_color = "green" if roi >= 0 else "red"
            summary += f"{pair:<10} │ {alloc_bar} {data['allocation']:>5.1f}% │ ROI: [{roi_color}]{self._format_percentage(roi)}[/{roi_color}]\n"
        
        # Performance metrics with icons and colors
        summary += "\n[bold cyan]Performance Metrics[/bold cyan]\n" + "─" * 50 + "\n"
        summary += f"💰 Total Invested    │ {self._format_currency(total_stats['invested'])}\n"
        summary += f"💎 Current Value     │ {self._format_currency(total_stats['current_value'])}\n"
        summary += f"📊 Net Profit/Loss   │ [{profit_color}]{self._format_currency(total_stats['pnl'])} ({self._format_percentage(total_pnl_percentage)})[/{profit_color}]\n"
        
        # Add time period and market stats
        if len(self.results) > 0:
            first_pair = next(iter(self.results.values()))
            n_days = len(first_pair['results']['dates'])
            start_date = first_pair['results']['dates'][0].strftime('%Y-%m-%d')
            end_date = first_pair['results']['dates'][-1].strftime('%Y-%m-%d')
            summary += f"\n[bold cyan]Analysis Period[/bold cyan]\n" + "─" * 50 + "\n"
            summary += f"📅 Duration         │ {n_days} days\n"
            summary += f"📈 Period           │ {start_date} → {end_date}\n"
        
        # Add overall status indicator
        status = "🟢 PROFITABLE" if total_pnl_percentage >= 0 else "🔴 AT LOSS"
        status_color = "green" if total_pnl_percentage >= 0 else "red"
        
        console.print(Panel(
            summary,
            title=f"[{status_color}]{status}[/{status_color}]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # Show CSV save confirmation with style
        console.print(Panel(
            f"[green]📊 Analysis results exported to:[/green]\n[blue]{csv_file}[/blue]",
            border_style="green",
            style="green"
        ))
    
    def _save_analysis_to_csv(self, pair_stats, total_stats, filename):
        data = []
        for pair, stats in pair_stats.items():
            data.append({
                'Pair': pair,
                'Total Invested': stats['invested'],
                'Current Value': stats['current_value'],
                'Net Profit/Loss': stats['pnl'],
                'Return': f"{stats['pnl_percentage']:.2f}%"
            })
        
        # Add portfolio total
        data.append({
            'Pair': 'TOTAL',
            'Total Invested': total_stats['invested'],
            'Current Value': total_stats['current_value'],
            'Net Profit/Loss': total_stats['pnl'],
            'Return': f"{(total_stats['pnl'] / total_stats['invested'] * 100):.2f}%" if total_stats['invested'] > 0 else "0.00%"
        })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
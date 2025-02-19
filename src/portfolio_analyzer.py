from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import DOUBLE, ROUNDED

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
        allocation = data["allocation"]
        results = data["results"]
        current_price = results["prices"][-1]
        total_invested = results["total_invested"]
        current_value = results["current_value"]
        pnl = current_value - total_invested
        pnl_percentage = (pnl / total_invested * 100) if total_invested > 0 else 0
        trend_arrow = self._get_trend_arrow(pnl_percentage)
        profit_color = "green" if pnl_percentage >= 0 else "red"

        # Create fear index display
        fear_index = results["fear_index"]
        fear_color = (
            "green" if fear_index < 30 else "yellow" if fear_index < 60 else "red"
        )
        fear_emoji = "😊" if fear_index < 30 else "😰" if fear_index < 60 else "😱"
        fear_days = f"{results['negative_pnl_days']} of {results['total_days']}"

        # Create summary with consistent styling
        token = pair.split("/")[0]
        quote = pair.split("/")[1]

        summary = ""
        # Add token icon based on common cryptocurrencies
        token_icon = {
            "BTC": "₿",
            "ETH": "Ξ",
            "SOL": "◎",
            "DOT": "●",
            "USDT": "₮",
        }.get(token, "💲")

        summary += (
            f"[bold cyan]{token_icon} {token}[/bold cyan]/[dim]{quote}[/dim] {trend_arrow}\n"
            + "─" * 50
            + "\n"
        )

        # Investment metrics with improved visual hierarchy
        alloc_bar = self._create_progress_bar(
            allocation, 25
        )  # Slightly reduced width for better layout
        daily_amount = (
            results["total_invested"] / len(results["dates"])
            if len(results["dates"]) > 0
            else 0
        )

        summary += f"💼 [dim]Allocation[/dim]        │ {alloc_bar}\n"
        summary += f"💰 [dim]Total Invested[/dim]    │ [bold]{self._format_currency(total_invested)}[/bold] ([dim]~{self._format_currency(daily_amount)}/day[/dim])\n"
        summary += f"💲 [dim]Amount[/dim]            │ [bold]{results['total_crypto']:.8f}[/bold] {token}\n"
        summary += f"💎 [dim]Current Value[/dim]     │ [bold]{self._format_currency(current_value)}[/bold]\n"
        summary += f"📊 [dim]Net Profit/Loss[/dim]   │ [bold {profit_color}]{self._format_currency(pnl)}[/bold {profit_color}] ([{profit_color}]{self._format_percentage(pnl_percentage)}[/{profit_color}])\n"

        # Add fear index metrics
        summary += f"😱 [dim]Fear Index[/dim]        │ [{fear_color}]{fear_emoji} {fear_index:.1f}% ({fear_days} days)[/{fear_color}]\n"

        # Price metrics with highlighting
        summary += "\n[bold cyan]Price Analysis[/bold cyan]\n" + "─" * 50 + "\n"
        avg_vs_current = "green" if current_price > results["cost_basis"] else "red"

        summary += f"📈 [dim]Average Cost[/dim]      │ [bold]{self._format_currency(results['cost_basis'])}[/bold]\n"
        summary += f"🎯 [dim]Current Price[/dim]     │ [bold {avg_vs_current}]{self._format_currency(current_price)}[/bold {avg_vs_current}]\n"

        if "highest_price" in results and "lowest_price" in results:
            high_date = results.get("best_day", [None, None])[1]
            low_date = results.get("worst_day", [None, None])[1]

            high_date_str = (
                f" ([dim]{high_date.strftime('%Y-%m-%d')}[/dim])" if high_date else ""
            )
            low_date_str = (
                f" ([dim]{low_date.strftime('%Y-%m-%d')}[/dim])" if low_date else ""
            )

            summary += f"🔺 [dim]Highest Price[/dim]     │ [bold]{self._format_currency(results['highest_price'])}[/bold]{high_date_str}\n"
            summary += f"🔻 [dim]Lowest Price[/dim]      │ [bold]{self._format_currency(results['lowest_price'])}[/bold]{low_date_str}\n"

        console.print(
            Panel(
                summary,
                title=f"[{profit_color}]{'🟢' if pnl_percentage >= 0 else '🔴'} {token} Analysis[/{profit_color}]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        return {
            "invested": total_invested,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_percentage": pnl_percentage,
        }

    def display_portfolio_summary(self, timestamp=None):
        total_invested = sum(
            data["results"]["total_invested"] for data in self.results.values()
        )
        total_value = sum(
            data["results"]["current_value"] for data in self.results.values()
        )
        total_pnl = total_value - total_invested
        total_pnl_percentage = (
            (total_pnl / total_invested * 100) if total_invested > 0 else 0
        )

        table = Table(title="Portfolio Summary", box=ROUNDED)
        table.add_column("Pair", style="cyan")
        table.add_column("Allocation", justify="right")
        table.add_column("Invested", justify="right")
        table.add_column("Current Value", justify="right")
        table.add_column("P/L", justify="right")
        table.add_column("P/L %", justify="right")
        table.add_column("Fear Index", justify="right")

        for pair, data in self.results.items():
            results = data["results"]
            pnl = results["current_value"] - results["total_invested"]
            pnl_pct = (
                (pnl / results["total_invested"] * 100)
                if results["total_invested"] > 0
                else 0
            )

            color = "green" if pnl >= 0 else "red"
            table.add_row(
                pair,
                f"{data['allocation']}%",
                f"${results['total_invested']:,.2f}",
                f"${results['current_value']:,.2f}",
                f"${pnl:,.2f}",
                f"{pnl_pct:+.2f}%",
                f"{results['fear_index']:.1f}%",
            )

        # Add total row
        table.add_row(
            "TOTAL",
            "100%",
            f"${total_invested:,.2f}",
            f"${total_value:,.2f}",
            f"${total_pnl:,.2f}",
            f"{total_pnl_percentage:+.2f}%",
            "-",
            style="bold",
        )

        console.print("\n")
        console.print(table)

    def _save_analysis_to_csv(self, pair_stats, total_stats, filename):
        data = []
        for pair, stats in pair_stats.items():
            data.append(
                {
                    "Pair": pair,
                    "Total Invested": stats["invested"],
                    "Current Value": stats["current_value"],
                    "Net Profit/Loss": stats["pnl"],
                    "Return": f"{stats['pnl_percentage']:.2f}%",
                }
            )

        # Add portfolio total
        data.append(
            {
                "Pair": "TOTAL",
                "Total Invested": total_stats["invested"],
                "Current Value": total_stats["current_value"],
                "Net Profit/Loss": total_stats["pnl"],
                "Return": f"{(total_stats['pnl'] / total_stats['invested'] * 100):.2f}%"
                if total_stats["invested"] > 0
                else "0.00%",
            }
        )

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

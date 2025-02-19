import matplotlib.pyplot as plt
import numpy as np
import os
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

class ChartStyle:
    @staticmethod
    def setup():
        plt.style.use('default')
        plt.rcParams.update({
            'figure.facecolor': '#ffffff',
            'axes.facecolor': '#ffffff',
            'axes.grid': True,
            'grid.color': '#e0e0e0',
            'grid.linestyle': '--',
            'grid.alpha': 0.5,
            'axes.labelcolor': '#2c3e50',
            'text.color': '#2c3e50',
            'xtick.color': '#2c3e50',
            'ytick.color': '#2c3e50',
            'axes.spines.top': False,
            'axes.spines.right': False,
            'font.size': 10,
            'axes.titlesize': 12,
            'legend.fontsize': 9,
        })

class DCAVisualizer:
    def __init__(self, results, token_symbol, start_date, end_date):
        self.results = results
        self.token_symbol = token_symbol
        self.start_date = start_date
        self.end_date = end_date
        ChartStyle.setup()

    def plot_single_pair(self, timestamp):
        r = self.results
        fig = plt.figure(figsize=(12, 8))
        
        # Create subplots with proper spacing
        ax1 = plt.subplot2grid((2, 1), (0, 0), rowspan=1)
        ax2 = plt.subplot2grid((2, 1), (1, 0), rowspan=1)
        plt.subplots_adjust(hspace=0.3)
        
        # Price plot with minimal annotations
        ax1.plot(r['dates'], r['prices'], label=f'Price', color='#3498db', linewidth=2)
        ax1.plot(r['dates'], r['dca_prices'], label='Avg Cost', color='#2ecc71', 
                linewidth=2, linestyle='--')
        
        # Simple fill between
        ax1.fill_between(r['dates'], r['prices'], r['dca_prices'],
                        where=np.array(r['prices']) >= np.array(r['dca_prices']),
                        color='#2ecc71', alpha=0.15)
        ax1.fill_between(r['dates'], r['prices'], r['dca_prices'],
                        where=np.array(r['prices']) < np.array(r['dca_prices']),
                        color='#e74c3c', alpha=0.15)
        
        # Only show current price annotation
        current_price = r['prices'][-1]
        ax1.annotate(f'${current_price:,.0f}',
                    xy=(r['dates'][-1], current_price),
                    xytext=(-50, 20),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='#95a5a6', alpha=0.9),
                    fontsize=9)
        
        ax1.set_ylabel('Price (USD)')
        ax1.set_title(f'{self.token_symbol} Price & Cost Basis')
        ax1.legend(loc='upper left')
        
        # PnL plot
        ax2.plot(r['dates'], r['pnl_percentages'], label='P/L %', 
                color='#9b59b6', linewidth=2)
        
        # Fill for profit/loss areas
        ax2.fill_between(r['dates'], r['pnl_percentages'], 0,
                        where=np.array(r['pnl_percentages']) >= 0,
                        color='#2ecc71', alpha=0.15)
        ax2.fill_between(r['dates'], r['pnl_percentages'], 0,
                        where=np.array(r['pnl_percentages']) < 0,
                        color='#e74c3c', alpha=0.15)
        
        ax2.axhline(y=0, color='#95a5a6', linestyle='-', linewidth=1)
        ax2.set_ylabel('Profit/Loss %')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:+.1f}%'))
        ax2.legend(loc='upper left')
        
        # Add fear index to stats box
        pnl = r['current_value'] - r['total_invested']
        pnl_percentage = (pnl / r['total_invested'] * 100) if r['total_invested'] > 0 else 0
        fear_emoji = "😊" if r['fear_index'] < 30 else "😰" if r['fear_index'] < 60 else "😱"
        stats = (f'Return: {pnl_percentage:+.1f}%\n'
                f'Avg Cost: ${r["cost_basis"]:,.0f}\n'
                f'Fear Index: {r["fear_index"]:.1f}% {fear_emoji}')
        
        # Adjust stats box position to avoid overlap
        plt.figtext(0.95, 0.95, stats,
                   bbox=dict(facecolor='white', edgecolor='#95a5a6', alpha=0.9),
                   verticalalignment='top',
                   horizontalalignment='right',
                   fontsize=9)
        
        # Save with timestamp in filename
        plt.savefig(f'dca/dca_analysis_{timestamp}_{self.token_symbol.lower()}.png', 
                   dpi=300, bbox_inches='tight',
                   pad_inches=0.2)

    def plot_total_portfolio(self, all_results, timestamp):
        fig = plt.figure(figsize=(12, 8))
        
        # Create subplots with proper spacing
        ax1 = plt.subplot2grid((2, 1), (0, 0), rowspan=1)
        ax2 = plt.subplot2grid((2, 1), (1, 0), rowspan=1)
        plt.subplots_adjust(hspace=0.3)
        
        total_invested = 0
        total_current_value = 0
        dates = None
        
        # Calculate totals and combine data
        for pair_data in all_results.values():
            r = pair_data['results']
            if dates is None:
                dates = r['dates']
                total_prices = np.zeros(len(dates))
                total_dca_prices = np.zeros(len(dates))
                total_values = np.zeros(len(dates))
                total_costs = np.zeros(len(dates))
            
            # Calculate total value directly without token_amount
            prices = np.array(r['prices'])
            dca_prices = np.array(r['dca_prices'])
            total_values += np.array(r['values']) if 'values' in r else prices * (r['total_invested'] / dca_prices[-1])
            total_costs += np.array(r['costs']) if 'costs' in r else dca_prices * (r['total_invested'] / dca_prices[-1])
            total_invested += r['total_invested']
            total_current_value += r['current_value']
        
        # Calculate total portfolio PnL percentages
        total_pnl_percentages = [(v - c) / c * 100 if c > 0 else 0 
                                for v, c in zip(total_values, total_costs)]
        
        # Plot total portfolio value
        ax1.plot(dates, total_values, label='Portfolio Value', color='#3498db', linewidth=2)
        ax1.plot(dates, total_costs, label='Total Cost Basis', color='#2ecc71', 
                linewidth=2, linestyle='--')
        
        # Fill between areas
        ax1.fill_between(dates, total_values, total_costs,
                        where=total_values >= total_costs,
                        color='#2ecc71', alpha=0.15)
        ax1.fill_between(dates, total_values, total_costs,
                        where=total_values < total_costs,
                        color='#e74c3c', alpha=0.15)
        
        # Annotate current portfolio value
        ax1.annotate(f'${total_values[-1]:,.0f}',
                    xy=(dates[-1], total_values[-1]),
                    xytext=(-50, 20),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='#95a5a6', alpha=0.9),
                    fontsize=9)
        
        ax1.set_ylabel('Value (USD)')
        ax1.set_title('Total Portfolio Performance')
        ax1.legend(loc='upper left')
        
        # Plot total PnL
        ax2.plot(dates, total_pnl_percentages, label='Portfolio P/L %', 
                color='#9b59b6', linewidth=2)
        
        # Fill for profit/loss areas
        ax2.fill_between(dates, total_pnl_percentages, 0,
                        where=np.array(total_pnl_percentages) >= 0,
                        color='#2ecc71', alpha=0.15)
        ax2.fill_between(dates, total_pnl_percentages, 0,
                        where=np.array(total_pnl_percentages) < 0,
                        color='#e74c3c', alpha=0.15)
        
        ax2.axhline(y=0, color='#95a5a6', linestyle='-', linewidth=1)
        ax2.set_ylabel('Profit/Loss %')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:+.1f}%'))
        ax2.legend(loc='upper left')
        
        # Add portfolio stats
        total_pnl = total_current_value - total_invested
        total_pnl_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        stats = (f'Total Return: {total_pnl_percentage:+.1f}%\n'
                f'Total Invested: ${total_invested:,.0f}\n'
                f'Current Value: ${total_current_value:,.0f}')
        
        plt.figtext(0.95, 0.95, stats,
                   bbox=dict(facecolor='white', edgecolor='#95a5a6', alpha=0.9),
                   verticalalignment='top',
                   horizontalalignment='right',
                   fontsize=9)
        
        plt.savefig(f'dca/dca_analysis_{timestamp}_total_portfolio.png', 
                   dpi=300, bbox_inches='tight',
                   pad_inches=0.2)
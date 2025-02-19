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
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams.update({
            'figure.facecolor': '#ffffff',
            'axes.facecolor': '#f8f9fa',
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
            'figure.titlesize': 14,
            'figure.subplot.hspace': 0.3,
            'axes.prop_cycle': plt.cycler('color', 
                ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c', '#1abc9c'])
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
        
        # Create two subplots with proper spacing
        gs = plt.GridSpec(2, 1, height_ratios=[2, 1], hspace=0.3)
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        
        # Price and cost basis plot
        ax1.plot(r['dates'], r['prices'], label='Market Price', 
                color='#3498db', linewidth=2)
        ax1.plot(r['dates'], r['dca_prices'], label='Average Cost', 
                color='#34495e', linewidth=2, linestyle='--')
        
        # Simplified fill between
        ax1.fill_between(r['dates'], r['prices'], r['dca_prices'],
                        where=np.array(r['prices']) >= np.array(r['dca_prices']),
                        color='#2ecc71', alpha=0.15)
        ax1.fill_between(r['dates'], r['prices'], r['dca_prices'],
                        where=np.array(r['prices']) < np.array(r['dca_prices']),
                        color='#e74c3c', alpha=0.15)
        
        ax1.set_ylabel('Price (USD)')
        ax1.set_title(f'{self.token_symbol} Price & Cost Analysis', pad=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        # Investment value plot
        if 'values' in r and 'costs' in r:
            ax2.plot(r['dates'], r['values'], label='Position Value',
                    color='#2ecc71' if r['values'][-1] >= r['costs'][-1] else '#e74c3c',
                    linewidth=2)
            ax2.plot(r['dates'], r['costs'], label='Total Investment',
                    color='#34495e', linewidth=2, linestyle='--')
            
            ax2.fill_between(r['dates'], r['values'], r['costs'],
                           where=np.array(r['values']) >= np.array(r['costs']),
                           color='#2ecc71', alpha=0.15)
            ax2.fill_between(r['dates'], r['values'], r['costs'],
                           where=np.array(r['values']) < np.array(r['costs']),
                           color='#e74c3c', alpha=0.15)
            
            ax2.set_ylabel('Position Value (USD)')
            ax2.set_title('Investment Performance', pad=10)
            ax2.grid(True, linestyle='--', alpha=0.7)
            ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        # Format y-axis labels as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Add statistics box
        stats = (
            f"Current Price: ${r['prices'][-1]:,.2f}\n"
            f"Average Cost: ${r['dca_prices'][-1]:,.2f}\n"
            f"Return: {r['pnl_percentages'][-1]:+.1f}%\n"
            f"Volatility: {r.get('volatility', 0):.1f}%\n"
            f"Max Drawdown: {r.get('max_drawdown', 0):+.1f}%"
        )
        
        plt.figtext(0.02, 0.02, stats,
                   bbox=dict(facecolor='white', edgecolor='#95a5a6', alpha=0.9),
                   verticalalignment='bottom',
                   horizontalalignment='left',
                   fontsize=9)
        
        plt.suptitle(
            f'{self.token_symbol} DCA Analysis - {self.start_date.strftime("%Y-%m-%d")} to {self.end_date.strftime("%Y-%m-%d")}',
            y=0.95,
            fontsize=14,
            fontweight='bold'
        )
        
        # Adjust layout to prevent text cutoff and warnings
        plt.subplots_adjust(right=0.85, bottom=0.15, top=0.9)
        
        # Save with high quality
        plt.savefig(f'dca/dca_analysis_{timestamp}_{self.token_symbol.lower()}.png', 
                   dpi=300, bbox_inches='tight',
                   pad_inches=0.2)
        plt.close()

    def plot_total_portfolio(self, all_results, timestamp):
        fig = plt.figure(figsize=(12, 8))
        gs = plt.GridSpec(3, 1, height_ratios=[2, 1, 0.3], hspace=0.3)
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        ax3 = plt.subplot(gs[2])
        
        dates = None
        colors = plt.cm.tab10(np.linspace(0, 1, len(all_results)))
        
        # Top plot: Asset value lines
        for (pair, data), color in zip(all_results.items(), colors):
            r = data['results']
            if dates is None:
                dates = r['dates']
                total_values = np.zeros(len(dates))
                
            values = np.array(r['values']) if 'values' in r else \
                    np.array(r['prices']) * (r['total_invested'] / r['dca_prices'][-1])
            ax1.plot(dates, values, label=f"{pair} ({data['allocation']}%)", 
                    color=color, alpha=0.7, linewidth=2)
            total_values += values
        
        # Add total portfolio value line
        ax1.plot(dates, total_values, label='Total Portfolio', 
                color='black', linewidth=2.5, linestyle='-')
        
        ax1.set_ylabel('Asset Values (USD)')
        ax1.set_title('Individual Asset Performance', pad=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        # Bottom plot: Total portfolio value and cost basis
        total_invested = sum(data['results']['total_invested'] for data in all_results.values())
        total_value = sum(data['results']['current_value'] for data in all_results.values())
        pnl_percentage = ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
        
        # Plot total portfolio value with filled area
        ax2.plot(dates, total_values, label='Portfolio Value', 
                color='#2ecc71' if pnl_percentage >= 0 else '#e74c3c', 
                linewidth=2)
        ax2.fill_between(dates, total_values, alpha=0.15, 
                        color='#2ecc71' if pnl_percentage >= 0 else '#e74c3c')
        
        # Calculate and plot cost basis line
        total_costs = np.zeros(len(dates))
        for data in all_results.values():
            r = data['results']
            if 'costs' in r:
                total_costs += np.array(r['costs'])
        
        ax2.plot(dates, total_costs, label='Total Investment', 
                color='#34495e', linewidth=2, linestyle='--')
        
        ax2.set_ylabel('Portfolio Value (USD)')
        ax2.set_title('Total Portfolio Performance', pad=10)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        # New progress bar visualization
        progress = (total_value - total_invested) / total_invested if total_invested > 0 else 0
        max_range = max(abs(progress), 0.5)  # At least ±50% range
        ax3.set_xlim(-max_range, max_range)
        ax3.set_ylim(0, 1)
        
        # Create progress bar
        bar_color = '#2ecc71' if progress >= 0 else '#e74c3c'
        ax3.barh(0.5, progress, height=0.3, color=bar_color, alpha=0.3)
        ax3.barh(0.5, progress, height=0.1, color=bar_color)
        
        # Add center line and percentage text
        ax3.axvline(x=0, color='#95a5a6', linestyle='-', linewidth=1)
        ax3.text(progress, 0.5, f'{progress:+.1%}', 
                horizontalalignment='center' if abs(progress) < max_range/2 else 'left',
                verticalalignment='center',
                fontsize=10,
                fontweight='bold')
        
        # Clean up progress bar appearance
        ax3.set_yticks([])
        ax3.set_xticks([])
        for spine in ax3.spines.values():
            spine.set_visible(False)
        
        # Format y-axis labels as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Add portfolio stats box
        stats = (
            f"Total Value: ${total_value:,.2f}\n"
            f"Total Investment: ${total_invested:,.2f}\n"
            f"Total Return: {pnl_percentage:+.1f}%"
        )
        
        plt.figtext(0.02, 0.02, stats,
                   bbox=dict(facecolor='white', edgecolor='#95a5a6', alpha=0.9),
                   verticalalignment='bottom',
                   horizontalalignment='left',
                   fontsize=9)
        
        plt.suptitle(
            f'Portfolio Analysis - {self.start_date.strftime("%Y-%m-%d")} to {self.end_date.strftime("%Y-%m-%d")}',
            y=0.95,
            fontsize=14,
            fontweight='bold'
        )
        
        # Adjust layout to prevent text cutoff and warnings
        plt.subplots_adjust(right=0.85, bottom=0.1, top=0.9)
        
        # Save with high quality
        plt.savefig(f'dca/dca_analysis_{timestamp}_total_portfolio.png', 
                   dpi=300, bbox_inches='tight',
                   pad_inches=0.2)
        plt.close()
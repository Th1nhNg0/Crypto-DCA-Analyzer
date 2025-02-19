import numpy as np
from datetime import datetime

class DCACalculator:
    def __init__(self, price_data, daily_investment=1.0, buy_period="1d"):
        self.price_data = price_data
        self.daily_investment = daily_investment
        self.buy_period = self._parse_buy_period(buy_period)
        self.results = self._calculate_dca()

    def _parse_buy_period(self, period):
        """Convert period string to number of days"""
        units = {"d": 1, "w": 7, "m": 30}
        number = int(period[:-1])
        unit = period[-1].lower()
        if unit not in units:
            raise ValueError(f"Invalid buy period format: {period}. Use format like 1d, 1w, 2w, 1m")
        return number * units[unit]

    def _calculate_dca(self):
        dates = self.price_data["Start"].tolist()
        prices = np.array(self.price_data["Close"].tolist())
        
        # Initialize arrays for vectorized operations
        investments = np.zeros(len(dates))
        crypto_amounts = np.zeros(len(dates))
        days_since_buy = 0
        
        # Calculate buy points
        for i in range(len(dates)):
            days_since_buy += 1
            if days_since_buy >= self.buy_period:
                investment = self.daily_investment * self.buy_period
                investments[i] = investment
                crypto_amounts[i] = investment / prices[i]
                days_since_buy = 0
        
        # Cumulative calculations
        total_invested = np.cumsum(investments)
        total_crypto = np.cumsum(crypto_amounts)
        
        # Avoid division by zero
        nonzero_crypto = np.where(total_crypto > 0, total_crypto, np.inf)
        dca_prices = np.where(total_crypto > 0, total_invested / nonzero_crypto, prices)
        
        # Current values and PnL calculations
        current_values = total_crypto * prices
        pnl_percentages = np.where(total_crypto > 0, 
                                 ((prices - dca_prices) / dca_prices * 100),
                                 np.zeros_like(prices))
        
        # Find highest and lowest prices with dates
        highest_idx = np.argmax(prices)
        lowest_idx = np.argmin(prices)
        
        # Calculate drawdown and markup periods
        rolling_max = np.maximum.accumulate(current_values)
        drawdowns = (current_values - rolling_max) / rolling_max * 100
        max_drawdown = np.min(drawdowns)
        
        # Calculate positive and negative days
        invested_mask = total_invested > 0
        negative_pnl_days = np.sum((current_values < total_invested) & invested_mask)
        total_invested_days = np.sum(invested_mask)
        
        # Calculate volatility
        daily_returns = np.diff(prices) / prices[:-1]
        volatility = np.std(daily_returns) * np.sqrt(365) * 100
        
        # Calculate Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_returns = daily_returns - (risk_free_rate / 365)
        sharpe_ratio = np.sqrt(365) * np.mean(excess_returns) / np.std(daily_returns) if len(daily_returns) > 0 else 0
        
        return {
            "dates": dates,
            "prices": prices.tolist(),
            "dca_prices": dca_prices.tolist(),
            "pnl_percentages": pnl_percentages.tolist(),
            "total_invested": total_invested[-1],
            "total_crypto": total_crypto[-1],
            "highest_price": prices[highest_idx],
            "lowest_price": prices[lowest_idx],
            "best_day": (prices[highest_idx], dates[highest_idx]),
            "worst_day": (prices[lowest_idx], dates[lowest_idx]),
            "avg_price": np.mean(prices),
            "cost_basis": dca_prices[-1],
            "current_value": current_values[-1],
            "fear_index": (negative_pnl_days / total_invested_days * 100) if total_invested_days > 0 else 0,
            "negative_pnl_days": int(negative_pnl_days),
            "total_days": int(total_invested_days),
            "max_drawdown": max_drawdown,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "values": current_values.tolist(),
            "costs": total_invested.tolist()
        }

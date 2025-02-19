class DCACalculator:
    def __init__(self, price_data, daily_investment=1.0, buy_period="1d"):
        # Filter price data to only include rows within the specified date range
        self.df = price_data
        self.daily_investment = daily_investment
        self.buy_period = self._parse_buy_period(buy_period)
        self.results = self._calculate_dca()

    def _parse_buy_period(self, period):
        """Convert period string to number of days (e.g., '1d'->1, '1w'->7, '2w'->14, '1m'->30)"""
        number = int(period[:-1])
        unit = period[-1].lower()
        if unit == "d":
            return number
        elif unit == "w":
            return number * 7
        elif unit == "m":
            return number * 30
        raise ValueError(
            f"Invalid buy period format: {period}. Use format like 1d, 1w, 2w, 1m"
        )

    def _calculate_dca(self):
        if self.df.empty:
            raise ValueError("No price data available for the specified date range")

        total_invested = 0
        total_crypto = 0
        dates, prices, dca_prices, pnl_percentages = [], [], [], []
        values, costs = []  # Add arrays to track portfolio value and cost basis
        highest_price = float("-inf")
        lowest_price = float("inf")
        best_day = worst_day = None
        days_since_last_buy = 0
        negative_pnl_days = 0
        total_days = 0

        for _, row in self.df.iterrows():
            price = row["Close"]
            if price > highest_price:
                highest_price = price
                best_day = (price, row["Start"])
            if price < lowest_price:
                lowest_price = price
                worst_day = (price, row["Start"])

            days_since_last_buy += 1
            if days_since_last_buy >= self.buy_period:
                investment = self.daily_investment * self.buy_period
                crypto_bought = investment / price
                total_crypto += crypto_bought
                total_invested += investment
                days_since_last_buy = 0

            current_value = total_crypto * price
            values.append(current_value)  # Track portfolio value over time
            costs.append(total_invested)  # Track cost basis over time

            dca_price = total_invested / total_crypto if total_crypto > 0 else price
            pnl_percentage = (
                ((price - dca_price) / dca_price * 100) if total_crypto > 0 else 0
            )

            if total_invested > 0:
                total_days += 1
                if current_value < total_invested:
                    negative_pnl_days += 1

            dates.append(row["Start"])
            prices.append(price)
            dca_prices.append(dca_price)
            pnl_percentages.append(pnl_percentage)

        fear_index = (negative_pnl_days / total_days * 100) if total_days > 0 else 0

        return {
            "dates": dates,
            "prices": prices,
            "dca_prices": dca_prices,
            "pnl_percentages": pnl_percentages,
            "values": values,  # Add portfolio values array
            "costs": costs,  # Add cost basis array
            "total_invested": total_invested,
            "total_crypto": total_crypto,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "best_day": best_day,
            "worst_day": worst_day,
            "avg_price": self.df["Close"].mean(),
            "cost_basis": total_invested / total_crypto if total_crypto > 0 else 0,
            "current_value": total_crypto * self.df.iloc[-1]["Close"],
            "fear_index": fear_index,
            "negative_pnl_days": negative_pnl_days,
            "total_days": total_days,
        }

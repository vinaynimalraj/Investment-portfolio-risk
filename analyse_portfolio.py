"""Session 2: reconstruct the buy-and-hold portfolio from adjusted prices.

Run: python analyse_portfolio.py
The script reads local CSV files and does not download new data.
Distributions are modelled as reinvested through the adjusted-price series.
There are no deposits, withdrawals, rebalancing, fees, taxes or leverage.
"""

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent


def calculate_portfolio(portfolio, prices):
    """Return value, weights, returns and performance contribution by holding."""
    required = {"ticker", "currency", "initial_weight", "initial_investment_usd"}
    if not required.issubset(portfolio.columns) or portfolio.empty:
        raise ValueError("portfolio.csv must contain ticker, currency, initial_weight and initial_investment_usd.")
    if portfolio[list(required)].isna().any().any():
        raise ValueError("The portfolio contains missing inputs.")
    holdings = portfolio.copy()
    holdings["ticker"] = holdings["ticker"].astype(str).str.strip().str.upper()
    if holdings["ticker"].duplicated().any() or holdings["ticker"].eq("").any():
        raise ValueError("Portfolio tickers must be unique and non-empty.")
    if not holdings["currency"].eq("USD").all():
        raise ValueError("This version supports the USD sample portfolio only.")
    holdings = holdings.set_index("ticker")
    tickers = holdings.index.tolist()
    if len(prices) < 2 or set(prices.columns) != set(tickers):
        raise ValueError("The price file must have at least two dates and exactly the portfolio tickers.")
    if prices.columns.duplicated().any():
        raise ValueError("The price file contains duplicate columns.")
    if prices.index.has_duplicates or prices.index.isna().any() or not prices.index.is_monotonic_increasing:
        raise ValueError("Price dates must be valid, unique and in ascending order.")

    prices = prices.loc[:, tickers].apply(pd.to_numeric, errors="raise")
    price_values = prices.to_numpy(dtype=float)
    if not np.isfinite(price_values).all() or (price_values <= 0).any():
        raise ValueError("Prices must be finite, positive and complete. Run download_prices.py first.")
    allocations = holdings[["initial_weight", "initial_investment_usd"]].apply(pd.to_numeric, errors="raise")
    allocation_values = allocations.to_numpy(dtype=float)
    if not np.isfinite(allocation_values).all() or (allocation_values <= 0).any():
        raise ValueError("Starting weights and investments must be finite and positive.")
    starting_amounts = allocations["initial_investment_usd"]
    starting_weights = allocations["initial_weight"]
    starting_total = float(starting_amounts.sum())
    if not np.isclose(starting_weights.sum(), 1, atol=1e-8, rtol=0):
        raise ValueError("Starting weights must add up to 100%.")
    if not np.allclose(starting_amounts, starting_weights * starting_total, atol=0.01, rtol=0):
        raise ValueError("Starting weights and investment amounts do not agree.")

    # Start each price series at 1, then multiply by its starting investment.
    # Adjusted prices provide a total-return approximation, not execution prices.
    growth = prices.div(prices.iloc[0], axis="columns")
    holding_values = growth.mul(starting_amounts, axis="columns")
    total_value = holding_values.sum(axis=1)

    # Buy-and-hold means the weights change as the holdings grow or shrink.
    holding_weights = holding_values.div(total_value, axis="index")
    asset_returns = prices.pct_change(fill_method=None).iloc[1:]
    history = pd.DataFrame({
        "portfolio_value_usd": total_value,
        "daily_return_decimal": total_value.pct_change(fill_method=None),
        "cumulative_return_decimal": total_value / starting_total - 1,
    })
    history.index.name = "Date"
    # The first row's daily return is blank because there is no prior observation.

    ending_values = holding_values.iloc[-1]
    profit_loss = ending_values - starting_amounts
    summary = pd.DataFrame({
        "starting_value_usd": starting_amounts,
        "ending_value_usd": ending_values,
        "profit_loss_usd": profit_loss,
        "initial_weight_pct": starting_weights * 100,
        "ending_weight_pct": holding_weights.iloc[-1] * 100,
        "holding_total_return_pct": (growth.iloc[-1] - 1) * 100,
        "contribution_to_portfolio_return_pp": profit_loss / starting_total * 100,
    })
    summary.index.name = "ticker"
    return history, holding_values, holding_weights, asset_returns, summary


def main():
    portfolio = pd.read_csv(PROJECT_DIR / "portfolio.csv")
    price_path = PROJECT_DIR / "data" / "adjusted_prices.csv"
    prices = pd.read_csv(price_path, index_col="Date", parse_dates=["Date"])
    history, values, weights, returns, summary = calculate_portfolio(portfolio, prices)

    reports = PROJECT_DIR / "reports"
    reports.mkdir(exist_ok=True)
    history.to_csv(reports / "portfolio_history.csv", date_format="%Y-%m-%d")
    values.to_csv(reports / "holding_values.csv", index_label="Date", date_format="%Y-%m-%d")
    weights.to_csv(reports / "holding_weights.csv", index_label="Date", date_format="%Y-%m-%d")
    returns.to_csv(reports / "asset_daily_returns.csv", index_label="Date", date_format="%Y-%m-%d")
    summary.to_csv(reports / "holding_summary.csv")

    start_value = history["portfolio_value_usd"].iloc[0]
    end_value = history["portfolio_value_usd"].iloc[-1]
    elapsed_years = (history.index[-1] - history.index[0]).days / 365.25
    annualised_return = (end_value / start_value) ** (1 / elapsed_years) - 1
    print(f"\nSIMULATED BUY-AND-HOLD PORTFOLIO (USD)")
    print(f"Period: {history.index[0].date()} to {history.index[-1].date()}")
    print(f"Starting value: ${start_value:,.2f}")
    print(f"Ending value:   ${end_value:,.2f}")
    print(f"Profit / loss:  ${end_value - start_value:,.2f}")
    print(f"Total return:   {(end_value / start_value - 1) * 100:,.2f}%")
    print(f"Annualised compound return: {annualised_return * 100:,.2f}%")
    print(f"Daily returns per holding: {len(returns):,}")
    print("\nHoldings summary (percentages and USD):")
    print(summary.round(2).to_string())
    print(f"\nFive CSV reports saved in: {reports}")
    print("Open holding_summary.csv in Excel first.")
    print("Time-series return and weight files use decimals: 0.05 means 5%.")
    print("Contribution is in percentage points and adds up to the portfolio's total return.")
    print("Re-running this script replaces these five reports.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Analysis stopped: {exc}") from exc

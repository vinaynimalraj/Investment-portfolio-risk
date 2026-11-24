"""Attribute the latest portfolio's estimated volatility to individual holdings.

Run: python calculate_risk_contributions.py
Requires analyse_portfolio.py, portfolio.csv and data/adjusted_prices.csv.
Uses sample daily covariance over the available history and 252 days per year.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analyse_portfolio import calculate_portfolio


PROJECT_DIR = Path(__file__).resolve().parent
TRADING_DAYS = 252


def attribute_volatility(asset_returns, weights):
    """Euler volatility decomposition using one fixed allocation snapshot.

    Daily portfolio variance = w' Sigma w.
    Holding i's annualised volatility contribution =
        w_i * (Sigma w)_i / daily_portfolio_volatility * sqrt(252).
    Dividing each component by total volatility gives its risk share.
    Components can be negative when a holding offsets portfolio fluctuations.
    """
    if asset_returns.empty or len(asset_returns) < 2:
        raise ValueError("At least two common daily returns are required.")
    if asset_returns.columns.has_duplicates or weights.index.has_duplicates:
        raise ValueError("Holdings must be unique.")
    if set(asset_returns.columns) != set(weights.index):
        raise ValueError("Return columns and weight tickers must match.")
    weights = weights.reindex(asset_returns.columns).astype(float)
    data = asset_returns.to_numpy(dtype=float)
    if not np.isfinite(data).all() or not np.isfinite(weights.to_numpy()).all():
        raise ValueError("Returns and weights must be finite and complete.")
    if (weights < 0).any() or not np.isclose(weights.sum(), 1, atol=1e-8, rtol=0):
        raise ValueError("This version requires non-negative weights summing to 100%.")

    covariance = asset_returns.cov(ddof=1)
    covariance_with_portfolio = covariance.dot(weights)
    variance = float(weights.dot(covariance_with_portfolio))
    if variance <= 0:
        raise ValueError("Portfolio volatility must be positive to calculate risk shares.")
    daily_volatility = np.sqrt(variance)
    annualised_volatility = daily_volatility * np.sqrt(TRADING_DAYS)
    components = weights * covariance_with_portfolio / daily_volatility * np.sqrt(TRADING_DAYS)

    result = pd.DataFrame({
        "current_weight_pct": weights * 100,
        "standalone_annualised_volatility_pct": asset_returns.std(ddof=1) * np.sqrt(TRADING_DAYS) * 100,
        "contribution_to_annualised_volatility_pp": components * 100,
        "share_of_portfolio_volatility_pct": components / annualised_volatility * 100,
    })
    result.index.name = "ticker"
    if not np.isclose(result["share_of_portfolio_volatility_pct"].sum(), 100, atol=1e-8, rtol=0):
        raise ValueError("Risk shares did not reconcile to 100%.")
    return result.sort_values("share_of_portfolio_volatility_pct", ascending=False), annualised_volatility


def main():
    portfolio = pd.read_csv(PROJECT_DIR / "portfolio.csv")
    prices = pd.read_csv(PROJECT_DIR / "data" / "adjusted_prices.csv", index_col="Date", parse_dates=["Date"])
    history, values, weights, returns, holding_summary = calculate_portfolio(portfolio, prices)
    latest_weights = weights.iloc[-1]
    contributions, snapshot_volatility = attribute_volatility(returns, latest_weights)
    realised_volatility = history["daily_return_decimal"].dropna().std(ddof=1) * np.sqrt(TRADING_DAYS)

    reports = PROJECT_DIR / "reports"
    reports.mkdir(exist_ok=True)
    contributions.to_csv(reports / "risk_contributions.csv")
    returns.corr().to_csv(reports / "correlation_matrix.csv", index_label="ticker")
    method = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "weights_as_of": weights.index[-1].date().isoformat(),
        "price_history_start": prices.index[0].date().isoformat(),
        "price_history_end": prices.index[-1].date().isoformat(),
        "daily_return_observations": len(returns),
        "annualisation_trading_days": TRADING_DAYS,
        "covariance_estimator": "Sample covariance of common daily adjusted-price returns; ddof=1",
        "allocation_model": "Latest simulated buy-and-hold weights applied to historical covariance",
        "current_weights_decimal": {ticker: float(weight) for ticker, weight in latest_weights.items()},
        "estimated_current_weight_annualised_volatility_pct": float(snapshot_volatility * 100),
        "realised_buy_and_hold_annualised_volatility_pct": float(realised_volatility * 100),
        "risk_contribution_method": "Euler decomposition of portfolio volatility",
        "units": "CSV weight, standalone volatility and risk-share fields are percentage numbers; contributions are percentage points.",
        "limitations": [
            "Historical covariance is an estimate; future volatility and correlations can change.",
            "The current-weight estimate describes one allocation snapshot, not realised historical performance.",
            "Attribution treats each ETF as a holding; constituent-level overlap is not decomposed.",
            "Volatility contributions measure variability, not shares of losses or VaR.",
        ],
    }
    (reports / "risk_contribution_methodology.json").write_text(json.dumps(method, indent=2) + "\n", encoding="utf-8")

    print(f"\nCURRENT-WEIGHT VOLATILITY CONTRIBUTIONS — as of {method['weights_as_of']}")
    print(f"Historical daily returns used: {len(returns):,}")
    print(f"Realised buy-and-hold annualised volatility: {realised_volatility * 100:.2f}%")
    print(f"Estimated annualised volatility at latest weights: {snapshot_volatility * 100:.2f}%")
    print("These use different allocation assumptions; the current-weight estimate is a separate measure.")
    print("\nAllocation versus share of estimated volatility (percentage numbers):")
    print(contributions[["current_weight_pct", "share_of_portfolio_volatility_pct"]].round(2).to_string())
    print(f"\nRisk shares total: {contributions['share_of_portfolio_volatility_pct'].sum():.2f}%")
    print(f"Saved three reports in: {reports}")
    print("Open risk_contributions.csv in Excel. It is sorted by risk share, not by ticker.")
    print("Re-running this script replaces its three reports.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Risk analysis stopped: {exc}") from exc

"""Download and validate daily adjusted prices for the portfolio.

Run from the activated project environment: python download_prices.py
Inputs and outputs are relative to this script, not the terminal directory.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf


PROJECT_DIR = Path(__file__).resolve().parent


def read_portfolio(path):
    """Check the starting allocation before requesting market data."""
    portfolio = pd.read_csv(path)
    required = {"ticker", "currency", "initial_weight", "initial_investment_usd"}
    missing = required.difference(portfolio.columns)
    if missing:
        raise ValueError(f"Missing portfolio columns: {', '.join(sorted(missing))}")
    if portfolio.empty or portfolio[list(required)].isna().any().any():
        raise ValueError("The portfolio is empty or contains missing inputs.")

    portfolio["ticker"] = portfolio["ticker"].astype(str).str.strip().str.upper()
    if portfolio["ticker"].eq("").any() or portfolio["ticker"].duplicated().any():
        raise ValueError("Each holding must have a unique, non-empty ticker.")
    if not portfolio["currency"].eq("USD").all():
        raise ValueError("This first version supports the USD sample portfolio only.")

    for column in ("initial_weight", "initial_investment_usd"):
        portfolio[column] = pd.to_numeric(portfolio[column], errors="raise")
        values = portfolio[column].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError(f"{column} must contain finite positive numbers.")

    weights = portfolio["initial_weight"]
    amounts = portfolio["initial_investment_usd"]
    if not np.isclose(weights.sum(), 1.0, atol=1e-8, rtol=0):
        raise ValueError("Starting weights must add up to 1.00 (100%).")
    if not np.allclose(amounts, weights * amounts.sum(), atol=0.01, rtol=0):
        raise ValueError("Starting investment amounts do not match their weights.")
    return portfolio


def clean_prices(prices, tickers):
    """Keep common observation dates; never invent or forward-fill a price."""
    missing = [ticker for ticker in tickers if ticker not in prices.columns]
    if missing:
        raise ValueError(f"No price column returned for: {', '.join(missing)}")
    prices = prices.loc[:, tickers].copy().sort_index()
    if prices.index.has_duplicates:
        raise ValueError("Duplicate dates were returned; investigate before continuing.")
    if prices.index.isna().any():
        raise ValueError("Invalid dates were returned.")
    prices = prices.apply(pd.to_numeric, errors="raise")
    if prices.empty or prices.isna().all().any():
        raise ValueError("At least one holding has no data. Check the download messages.")

    values = prices.to_numpy(dtype=float)
    if np.isinf(values).any() or (values <= 0).any():
        raise ValueError("Non-positive or infinite prices were returned.")

    missing_counts = prices.isna().sum().astype(int).to_dict()
    clean = prices.dropna(how="any").copy()
    if len(clean) < 2:
        raise ValueError("Too few common observations remain after checking missing prices.")
    return prices, clean, missing_counts


def main():
    portfolio = read_portfolio(PROJECT_DIR / "portfolio.csv")
    tickers = portfolio["ticker"].tolist()

    # Exclude today's US session, which could still be in progress.
    end = datetime.now(ZoneInfo("America/New_York")).date()
    try:
        start = end.replace(year=end.year - 5)
    except ValueError:  # A five-year offset from 29 February needs 28 February.
        start = end.replace(year=end.year - 5, day=28)

    print(f"Holdings: {', '.join(tickers)}")
    print(f"Requesting {start} to {end} (end date excluded).")
    print("Downloading adjusted daily prices; an internet connection is required...")
    downloaded = yf.download(
        tickers=tickers,
        start=start.isoformat(),
        end=end.isoformat(),
        interval="1d",
        auto_adjust=True,
        group_by="column",
        multi_level_index=True,
        keepna=True,
        ignore_tz=True,
        threads=False,
        progress=False,
        timeout=30,
    )
    if downloaded is None or downloaded.empty:
        raise ValueError("No data was downloaded. Check your connection and try again later.")

    # With auto_adjust=True, Close is the provider's adjusted closing series.
    prices = downloaded["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
    raw, clean, missing_counts = clean_prices(prices, tickers)
    raw.index.name = clean.index.name = "Date"

    warnings = []
    dropped = len(raw) - len(clean)
    if dropped:
        warnings.append(f"Removed {dropped} dates with a missing price; review missing counts.")
    if (clean.index.min().date() - start).days > 10:
        warnings.append("The common history starts more than 10 days after the requested start.")
    if (end - clean.index.max().date()).days > 7:
        warnings.append("The latest common price is over 7 days old; investigate freshness.")

    summary = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance via yfinance",
        "yfinance_version": yf.__version__,
        "pandas_version": pd.__version__,
        "requested_tickers": tickers,
        "requested_start_inclusive": start.isoformat(),
        "requested_end_exclusive": end.isoformat(),
        "interval": "1d",
        "adjustment": "yfinance auto_adjust=True; adjusted Close series",
        "first_common_date": clean.index.min().date().isoformat(),
        "last_common_date": clean.index.max().date().isoformat(),
        "downloaded_rows": len(raw),
        "common_rows": len(clean),
        "rows_removed_for_missing_prices": dropped,
        "missing_prices_by_ticker": missing_counts,
        "warnings": warnings,
        "limitations": [
            "Only dates returned by the provider are checked; no exchange calendar reconciliation.",
            "Provider adjustments have not been independently verified against corporate actions.",
            "Adjusted price levels are not trade execution prices.",
        ],
    }

    output_dir = PROJECT_DIR / "data"
    output_dir.mkdir(exist_ok=True)
    raw.to_csv(output_dir / "adjusted_prices_download.csv", date_format="%Y-%m-%d")
    clean.to_csv(output_dir / "adjusted_prices.csv", date_format="%Y-%m-%d")
    (output_dir / "download_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print(f"\nSaved {len(clean):,} common daily observations for {len(tickers)} holdings.")
    print(f"Date range: {summary['first_common_date']} to {summary['last_common_date']}")
    print(f"Missing prices by ticker: {missing_counts}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print(f"\nFiles saved in: {output_dir}")
    print("Latest 5 observations (adjusted prices):")
    print(clean.tail().round(2).to_string())
    print("\nRe-running this script replaces the three data output files.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Download stopped: {exc}") from exc

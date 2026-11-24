"""Independent calculations for the investment risk dashboard.

All returns and weights are decimals internally. Cash flows, costs, taxes,
leverage and ETF constituent look-through are outside this model.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def validate_weights(weights, tickers):
    if weights.index.has_duplicates or set(weights.index) != set(tickers):
        raise ValueError("Provide exactly one weight for every holding.")
    weights = pd.to_numeric(weights.reindex(tickers), errors="raise").astype(float)
    if not np.isfinite(weights.to_numpy()).all():
        raise ValueError("Every holding needs a finite numeric weight.")
    if (weights < 0).any() or (weights > 1).any():
        raise ValueError("Each weight must be between 0% and 100%.")
    if not np.isclose(weights.sum(), 1, atol=1e-8, rtol=0):
        raise ValueError(f"Weights total {weights.sum():.4%}; enter a total of 100%.")
    return weights


def validate_scenarios(scenarios, tickers):
    if scenarios.index.has_duplicates or set(scenarios.index) != set(tickers):
        raise ValueError("Each scenario needs exactly one shock for every holding.")
    if scenarios.columns.has_duplicates or not len(scenarios.columns):
        raise ValueError("Scenario names must be unique and non-empty.")
    frame = scenarios.reindex(tickers).apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("Fill every scenario shock with a finite number, including explicit zeroes.")
    if (frame < -1).any().any():
        raise ValueError("A holding's assumed loss cannot exceed 100% in this unlevered model.")
    return frame


def analyse_prices(portfolio, prices):
    required = {"ticker", "asset_class", "initial_weight", "initial_investment_usd"}
    if not required.issubset(portfolio.columns) or portfolio.empty:
        raise ValueError("The portfolio file is missing required allocation columns.")
    portfolio = portfolio.copy()
    if portfolio[list(required)].isna().any().any():
        raise ValueError("The portfolio has a missing required input.")
    portfolio["ticker"] = portfolio["ticker"].astype(str).str.strip().str.upper()
    if portfolio.ticker.duplicated().any() or portfolio.ticker.eq("").any():
        raise ValueError("Portfolio tickers must be unique and non-empty.")
    if "currency" in portfolio and not portfolio.currency.eq("USD").all():
        raise ValueError("This dashboard's allocations must be denominated in USD.")
    portfolio = portfolio.set_index("ticker")
    tickers = portfolio.index.tolist()
    if prices.columns.has_duplicates or set(prices.columns) != set(tickers):
        raise ValueError("Price columns must match the six portfolio tickers exactly.")
    prices = prices.loc[:, tickers].copy()
    prices.index = pd.to_datetime(prices.index, errors="raise")
    if prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)
    if len(prices) < 3 or prices.index.has_duplicates or prices.index.isna().any() or not prices.index.is_monotonic_increasing:
        raise ValueError("Prices need at least three unique valid dates in ascending order.")
    if (prices.index.day_of_week >= 5).any():
        raise ValueError("This daily US securities dataset contains weekend observations.")
    prices = prices.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any():
        raise ValueError("Prices must be finite, positive and complete. Investigate missing data before loading it.")
    initial_weights = validate_weights(portfolio.initial_weight, tickers)
    amounts = pd.to_numeric(portfolio.initial_investment_usd, errors="raise").astype(float)
    if not np.isfinite(amounts).all() or (amounts <= 0).any():
        raise ValueError("Initial investments must be finite and positive.")
    nav0 = float(amounts.sum())
    if not np.allclose(amounts, initial_weights * nav0, atol=.01, rtol=0):
        raise ValueError("Initial amounts and weights do not agree.")
    values = prices.div(prices.iloc[0]).mul(amounts)
    nav = values.sum(axis=1).rename("Portfolio value (USD)")
    actual_returns = nav.pct_change(fill_method=None).iloc[1:]
    asset_returns = prices.pct_change(fill_method=None).iloc[1:]
    weights_history = values.div(nav, axis=0)
    drawdown = (nav / nav.cummax() - 1).rename("Drawdown")
    years = (prices.index[-1] - prices.index[0]).days / 365.25
    summary = pd.DataFrame({
        "Initial value ($)": amounts,
        "Latest value ($)": values.iloc[-1],
        "Gain/loss ($)": values.iloc[-1] - amounts,
        "Initial weight (%)": initial_weights * 100,
        "Latest weight (%)": weights_history.iloc[-1] * 100,
        "Holding return (%)": (prices.iloc[-1] / prices.iloc[0] - 1) * 100,
        "Portfolio return contribution (pp)": (values.iloc[-1] - amounts) / nav0 * 100,
    })
    return {
        "portfolio": portfolio, "prices": prices, "returns": asset_returns,
        "values": values, "nav": nav, "actual_returns": actual_returns,
        "weights_history": weights_history, "current": weights_history.iloc[-1],
        "drawdown": drawdown, "summary": summary, "initial_nav": nav0,
        "latest_nav": float(nav.iloc[-1]), "total_return": float(nav.iloc[-1]/nav0-1),
        "cagr": float((nav.iloc[-1]/nav0)**(1/years)-1),
    }


def load_snapshot(directory):
    directory = Path(directory)
    portfolio = pd.read_csv(directory / "portfolio.csv")
    prices = pd.read_csv(directory / "adjusted_prices.csv", index_col="Date", parse_dates=["Date"])
    state = analyse_prices(portfolio, prices)
    tickers = state["portfolio"].index.tolist()
    proposal = pd.read_csv(directory / "proposal.csv", index_col="ticker")["weight"]
    state["proposal"] = validate_weights(proposal, tickers)
    state["scenarios"] = validate_scenarios(pd.read_csv(directory / "scenarios.csv", index_col="ticker"), tickers)
    state["limits"] = json.loads((directory / "limits.json").read_text())
    for key in ("single_stock", "equity"):
        value = state["limits"][key]
        if not isinstance(value, (int,float)) or not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"Invalid {key} limit.")
    if not set(state["limits"]["direct_stock_tickers"]).issubset(tickers):
        raise ValueError("A direct-stock risk limit references an unknown holding.")
    state["reference"] = json.loads((directory / "audit_reference.json").read_text())
    state["matches_reviewed_inputs"] = (
        hashlib.sha256((directory/'adjusted_prices.csv').read_bytes()).hexdigest()==state['reference']['price_data_sha256']
        and hashlib.sha256((directory/'portfolio.csv').read_bytes()).hexdigest()==state['reference']['portfolio_data_sha256']
    )
    return state


def risk_metrics(returns, confidence=.95):
    r = pd.Series(returns).astype(float)
    if len(r) < 2 or not np.isfinite(r).all() or not 0 < confidence < 1:
        raise ValueError("Risk measures require finite returns and a confidence level between 0 and 1.")
    q = float(r.quantile(1-confidence, interpolation="linear"))
    return {
        "Annualised volatility": float(r.std(ddof=1)*np.sqrt(TRADING_DAYS)),
        "One-day VaR": -q,
        "One-day Expected Shortfall": float(-r[r<=q].mean()),
    }


def volatility_contributions(returns, weights):
    weights = validate_weights(weights, returns.columns)
    covariance = returns.cov(ddof=1)
    cov_with_portfolio = covariance.dot(weights)
    variance = float(weights.dot(cov_with_portfolio))
    if variance <= 1e-20:
        raise ValueError("Volatility shares are undefined when estimated portfolio variance is zero.")
    vol = np.sqrt(variance)
    components = weights * cov_with_portfolio / vol * np.sqrt(TRADING_DAYS)
    result = pd.DataFrame({
        "Weight (%)": weights*100,
        "Volatility contribution (pp)": components*100,
        "Share of volatility (%)": components/(vol*np.sqrt(TRADING_DAYS))*100,
    })
    result.index.name = "Holding"
    return result.sort_values("Share of volatility (%)", ascending=False)


def make_proposal(current, nvda_target=.12, bond_share=.5):
    if not 0 <= nvda_target <= 1 or not 0 <= bond_share <= 1:
        raise ValueError("Target weight and bond share must be between 0 and 100%.")
    proposal = current.copy()
    released = float(current["NVDA"] - nvda_target)
    proposal["NVDA"] = nvda_target
    proposal["IEF"] += released*bond_share
    proposal["GLD"] += released*(1-bond_share)
    return validate_weights(proposal, current.index)


def stress_results(scenarios, weights, nav):
    weights = validate_weights(weights, scenarios.index)
    scenarios = validate_scenarios(scenarios, weights.index)
    result = scenarios.mul(weights, axis=0).sum(axis=0)
    return pd.DataFrame({
        "Scenario return (%)": result*100,
        "Loss ($)": -result*nav,
        "Value after stress ($)": (1+result)*nav,
    }).rename_axis("Scenario")


def limit_table(weights, portfolio, limits):
    weights = validate_weights(weights, portfolio.index)
    rows = []
    for ticker in limits["direct_stock_tickers"]:
        rows.append((f"Direct {ticker}",float(weights[ticker]),float(limits["single_stock"])))
    equity_tickers = portfolio.index[portfolio.asset_class.str.lower().eq("equity")]
    rows.append(("Total equities",float(weights.loc[equity_tickers].sum()),float(limits["equity"])))
    return pd.DataFrame([{
        "Risk measure": name, "Exposure (%)": exposure*100, "Limit (%)": limit*100,
        "Excess (pp)": max(0.,(exposure-limit)*100),
        "Status": "BREACH" if exposure>limit+1e-10 else "Within limit",
        "Response": "Escalate and review allocation" if exposure>limit+1e-10 else "Monitor",
    } for name,exposure,limit in rows]).set_index("Risk measure")


def trade_table(current, proposed, nav):
    proposed = validate_weights(proposed, current.index)
    return pd.DataFrame({
        "Current weight (%)": current*100, "Proposed weight (%)": proposed*100,
        "Change (pp)": (proposed-current)*100,
        "Illustrative trade ($)": (proposed-current)*nav,
    }).rename_axis("Holding")


def recommendation(state, proposed, scenarios, limits, confidence=.95):
    current=state["current"]
    before=risk_metrics(state["returns"].dot(current), confidence)
    after=risk_metrics(state["returns"].dot(proposed), confidence)
    old=stress_results(scenarios,current,state["latest_nav"])
    new=stress_results(scenarios,proposed,state["latest_nav"])
    breaches=limit_table(proposed,state["portfolio"],limits)
    worst=new["Scenario return (%)"].idxmin()
    return f'''# Investment risk comparison

Data as of {state['prices'].index[-1].date()}. Simulated portfolio value: ${state['latest_nav']:,.2f}.

## Proposed allocation

{trade_table(current,proposed,state['latest_nav']).to_csv(float_format='%.6f')}
## Risk measures

Estimated annualised volatility: {before['Annualised volatility']:.2%} current, {after['Annualised volatility']:.2%} proposed.
Historical {confidence:.0%} one-day VaR: {before['One-day VaR']:.2%} current, {after['One-day VaR']:.2%} proposed.
Historical {confidence:.0%} one-day Expected Shortfall: {before['One-day Expected Shortfall']:.2%} current, {after['One-day Expected Shortfall']:.2%} proposed.
These measures apply each fixed allocation to the same historical return observations.

## Scenario comparison

{pd.DataFrame({'Current return (%)':old['Scenario return (%)'],'Proposed return (%)':new['Scenario return (%)']}).to_csv(float_format='%.6f')}
The lowest proposed return among the scenarios tested is {new.loc[worst,'Scenario return (%)']:.2f}% under {worst}.

## Internal limits

{breaches.to_csv(float_format='%.6f')}
{int(breaches.Status.eq('BREACH').sum())} proposed allocation breaches under the selected direct-stock and equity limits.

## Decisions requiring review

Review fund objectives, expected return implications, bond and gold sensitivity, transaction costs and taxes, execution feasibility, and company exposures inside ETFs before adopting a proposal. Treasury bonds and gold carry their own risks. ETF constituent look-through has not been quantified.

## Method

Adjusted-price total-return approximation; 252 trading days per year; sample standard deviation and covariance (ddof=1); linearly interpolated historical return quantile; Expected Shortfall is the average observation at or below that cutoff. Risk shares use the Euler decomposition of volatility. Scenario returns are explicit hypothetical holding-level shocks. No costs, taxes, cash flows, leverage or trade execution are included.
'''

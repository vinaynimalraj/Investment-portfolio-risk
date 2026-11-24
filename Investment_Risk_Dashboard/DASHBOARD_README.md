# Investment Risk Monitor

An interactive Streamlit dashboard built from the investment risk workbook. The included, reviewed snapshot ends on **23 November 2026**. Opening the app uses local files and does not download new market prices or execute trades.

## First launch on your Windows computer

1. Extract the whole ZIP. Open the extracted folder containing `app.py`, `dashboard_core.py` and `dashboard_data`. Keep these together. This dashboard can run in its own folder or beside your existing project scripts.
2. Activate the Python environment you created earlier in Command Prompt:

```bat
"%LOCALAPPDATA%\venvs\investment-risk\Scripts\activate.bat"
```

3. Change to the extracted dashboard folder. To avoid typing its path: type `cd /d `, drag the extracted folder from File Explorer into Command Prompt, then press Enter.
4. Install the dashboard dependencies:

```bat
python -m pip install -r dashboard_requirements.txt
```

5. Launch:

```bat
python -m streamlit run app.py --server.headless true --server.address 127.0.0.1
```

Keep Command Prompt open. Streamlit prints the local address, normally http://localhost:8501. Open the printed local address in your browser. The local-only launch command does not open a browser automatically. Press **Ctrl+C** in Command Prompt to stop the app.

After installation, double-click **START_DASHBOARD.bat** for subsequent launches. It uses your existing investment-risk environment and serves the app on localhost.

The listed packages support the Python 3.14 installation used in this project. The dashboard is tested with the listed package versions; its independent calculation checks are also run against the reviewed workbook results.

## Dashboard views

- **Overview:** portfolio value, return, holdings, performance contributions and direct-exposure alerts.
- **Risk:** separate latest fixed-weight and realised buy-and-hold measures, 95% or 99% historical daily VaR and Expected Shortfall, drawdown, correlations and volatility contributions.
- **Stress tests:** editable holding-level shocks, current/proposed comparisons and holding-level loss attribution. Apply changes with the form button.
- **Rebalance:** the workbook proposal, a Nvidia target with explicit funding allocation, an editor for all weights, trade reconciliation, risk metrics, risk contributions and limit comparisons.
- **Methods:** definitions, source, scope, audit notes and the workbook's saved recommendation.

The **Download this comparison and report** button exports the applied proposal, scenario assumptions, limits, results and a Markdown review with the selected confidence level. App changes remain within the current session until exported. Restarting restores the saved inputs.

## Inputs

All input files are in dashboard_data:

| File | Purpose |
|---|---|
| portfolio.csv | Six holdings, original USD amounts and initial weights |
| adjusted_prices.csv | Supplied adjusted closing-price snapshot |
| scenarios.csv | Reviewed scenario shocks as decimal returns |
| proposal.csv | Reviewed proposed weights as decimals |
| limits.json | Illustrative direct-stock and equity limits |
| download_summary.json | Original market-data download metadata |
| audit_reference.json | Source-workbook checksum, snapshot and checked results |

dashboard_core.py owns the calculations. app.py provides controls and presentation. tests/test_dashboard.py checks the engine against the reviewed workbook and known examples.

Daily returns use fractions: 0.01 means 1%. Portfolio value normalises adjusted prices to initial allocations. No rebalancing occurs in the realised historical portfolio. Separate fixed-allocation estimates apply the latest or proposed weights to every historical daily asset-return observation.

Risk measures use sample standard deviation/covariance and 252 trading days per year. VaR uses a linearly interpolated historical return quantile. Expected Shortfall averages observed losses at or below that return cutoff. Euler volatility contributions add to total volatility; relative risk shares add to 100%, including any negative hedging components.

The inflation scenario uses explicit price returns. It does not derive its bond shock from duration or a specified yield change. No cash flows, trading costs, taxes, leverage or ETF constituent look-through are included.

## Reviewed baseline

| Measure | Current weights | Workbook proposal |
|---|---:|---:|
| Annualised volatility | 27.35% | 16.21% |
| Historical 95% daily VaR | 2.57% | 1.59% |
| Historical 95% daily ES | 3.67% | 2.22% |
| Equity sell-off return | -15.43% | -9.44% |
| Technology crash return | -25.73% | -13.99% |
| Inflation shock return | -19.62% | -14.00% |

Realised buy-and-hold annualised volatility is 22.53%, with maximum drawdown of -28.92%. The original simulated $10 million portfolio ends at $21,169,852.98.

See WORKBOOK_REVIEW.md for review scope and checks. The original Excel workbook is not included or changed by this package.

## Refreshing and retaining inputs

Validate replacement data before changing dashboard_data/adjusted_prices.csv. Keep the six ticker columns, Date column, positive finite adjusted prices, common trading dates and ascending dates without duplicates or missing holding prices. Refresh/restart the app after replacing files. It warns when price/allocation inputs differ from the reviewed snapshot.

Updating prices recomputes the buy-and-hold history from the first available date and original initial allocations. Proposal weights, scenarios and limits remain separate inputs; review them after a refresh. The workbook's narrative and audit reference remain dated records. Changed inputs are not covered by the earlier workbook checks.

Your original download_prices.py writes to the earlier project's data folder. It does not update dashboard_data automatically. Review a new download, then copy the intended price file into the dashboard input folder.

To retain app edits, use the Rebalance download button. Exported weights and scenario files are labelled as decimal inputs. After review, these can replace proposal.csv and scenarios.csv; selected_limits.json can replace limits.json. Retain a copy of the baseline.

## Running checks

From this folder in the active environment:

```bat
python -m unittest discover -s tests -v
```

The checks cover workbook reconciliation, known buy-and-hold and risk examples, scenario losses, funding, direct-limit boundaries, missing inputs and input changes.

## Sources

- Original analysis: portfolio_review.xlsx, supplied by the user.
- Prices: Yahoo Finance through yfinance, with download metadata supplied alongside the source data.
- Streamlit API: https://docs.streamlit.io/
- Risk attribution reference: Thomas S. Coleman, A Practical Guide to Risk Management, Research Foundation of CFA Institute, 2011, pp. 159–162: https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2011/rf-v2011-n3-1-pdf.pdf

## Validation scope

See VALIDATION.md for completed checks and remaining verification limits. The cloud browser could not access the workspace local preview; visual layout inspection was not completed.

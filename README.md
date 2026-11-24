# Investment Portfolio Risk Management & Monitoring

A Python and Excel project analysing a simulated $10 million investment portfolio using real historical market data.

**Status:** Session 1 — project brief and starting allocation. Data collection, calculations and dashboard development are planned; they have not yet been implemented.

## Project brief

I am acting as an Investment Risk Analyst for a fictional asset management business. The portfolio manager selects investments; my role is to independently assess their risks, monitor exposures and communicate findings that support investment decisions.

The project will answer five questions:

1. What does the portfolio hold, and where is its exposure concentrated?
2. How has the portfolio performed, and which holdings explain its gains and losses?
3. How much could it lose under historical and hypothetical adverse conditions?
4. Does it breach the internal risk limits defined for this case study?
5. What changes should the portfolio manager investigate, and what trade-offs would they involve?

## Starting portfolio

| Ticker | Investment | Asset class | Initial weight | Initial investment (USD) |
|---|---|---|---:|---:|
| SPY | S&P 500 ETF | Equity | 25% | $2,500,000 |
| QQQ | Nasdaq-100 ETF | Equity | 20% | $2,000,000 |
| NVDA | Nvidia | Equity | 15% | $1,500,000 |
| AAPL | Apple | Equity | 10% | $1,000,000 |
| IEF | US Treasury bond ETF | Fixed income | 20% | $2,000,000 |
| GLD | Gold fund | Commodity | 10% | $1,000,000 |
| **Total** | | | **100%** | **$10,000,000** |

The initial allocation is 70% equities, 20% fixed income and 10% gold. It is deliberately designed for investigating concentration and overlapping exposures. ETF exposure to individual companies must be measured using dated holdings data rather than assumed from the ticker alone.

## Starting data file

`portfolio.csv` contains six holdings and these columns:

| Column | Meaning |
|---|---|
| `ticker` | Market data identifier for the investment |
| `security_name` | Plain-English investment label |
| `asset_class` | Broad asset class for allocation analysis |
| `investment_focus` | Description of the investment's exposure |
| `currency` | Currency of the starting investment amount |
| `initial_weight` | Starting allocation as a decimal: 0.25 means 25% |
| `initial_investment_usd` | Fictional starting allocation in US dollars |

There is no total row, so Python can read every row as a holding. These are initial allocations, not current market values or actual brokerage positions. Share quantities and the portfolio start date will be determined when historical data is available.

## Analysis assumptions

- Use USD as the reporting currency and approximately five years of daily historical data. Record exact dates, source, adjustment method and download date when data is collected.
- Invest the starting allocations on the first common valid observation date. Start with buy-and-hold and allow weights to drift; there is no automatic rebalancing.
- Model distributions as reinvested using suitable adjusted data. Normalise each adjusted-price series to its initial allocation; do not treat adjusted prices as actual trade execution prices.
- Initially exclude transaction costs, taxes, additional deposits, withdrawals and leverage. Document these limitations alongside results.
- Distinguish realised portfolio performance from risk estimates that apply current weights to historical asset returns.
- Define hypothetical stress assumptions and case-study limits explicitly. They are analytical choices, not forecasts or universal investment rules.

## Planned work

| Stage | Work | Deliverable |
|---|---|---|
| 1. Portfolio monitoring | Obtain and validate prices; calculate returns, values, drifting weights and performance contributions | Clean datasets and portfolio summary |
| 2. Risk measurement | Calculate annualised volatility, maximum drawdown, historical 95% one-day VaR, Expected Shortfall, correlations and volatility contributions | Risk analysis with explanations |
| 3. Stress testing | Model equity, technology, bond-yield and combined market shocks | Scenario loss table in percentages and USD |
| 4. Limits and proposals | Define internal limits, flag breaches, investigate ETF overlap and compare fully funded allocation changes | Breach register and recommendation memo |
| 5. Reporting | Combine the analysis in an interactive dashboard and final report | Streamlit dashboard, Excel checks and investment risk report |

Use Python for repeatable calculations, Excel for independent spot checks and reporting, and GitHub for documentation and version history. Supporting libraries and installation instructions will be added when implementation begins.

## Session 1 checklist

- [ ] Create a GitHub repository named `investment-portfolio-risk`.
- [ ] Upload this README and `portfolio.csv` together at the repository root.
- [ ] Check that the six starting weights sum to 1.00 and investments total $10 million.
- [ ] Explain why four equity holdings can still share important exposures.
- [ ] Begin the next session with price collection and data validation.

## Applying this to real investments

The same framework can be adapted to monitor a personal investment portfolio. Replace the fictional allocation with actual holdings, quantities, cash and dated transactions from a broker export. Reconcile calculated values against broker statements.

For a GBP investor, convert values and returns into GBP using appropriately dated exchange rates. Separate investment gains from deposits and withdrawals, and account for dividends, corporate actions, fees and relevant taxes. Trading currency alone does not describe an investment's underlying currency risk.

Personal holdings and account details should stay outside a public repository. A later version could support periodic CSV imports or an authorised read-only broker connection.

The first version is an educational monitoring prototype. Historical losses and risk estimates are not guarantees about future losses, and a limit alert is a prompt for investigation. The project does not execute trades. This case study is not affiliated with an investment firm and its sample allocation is not a recommendation to purchase these investments.

## What success looks like

Another person can reproduce the results, understand the assumptions and trace the key figures to their inputs. The final report explains which risks matter, what could happen under stress, and which actions merit investigation, supported by numbers and clear limitations.

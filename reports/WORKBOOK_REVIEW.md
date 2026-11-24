# Workbook review

Reviewed: portfolio_review.xlsx, saved snapshot ending 2026-11-23.

## Result

The core calculations reconcile to independent Python calculations. 45 checks passed across 12 worksheets. Scanned 5,137 formulas and found no saved formula errors, broken references or external workbook links.

| Measure | Current allocation | Proposed allocation |
|---|---:|---:|
| Annualised volatility | 27.35% | 16.21% |
| Historical 95% one-day VaR | 2.57% | 1.59% |
| Historical 95% one-day Expected Shortfall | 3.67% | 2.22% |

Portfolio ending value: $21,169,852.98. Realised buy-and-hold annualised volatility: 22.53%. Maximum historical drawdown: -28.92%.

## Checks performed

- Initial portfolio totals and amounts
- Ending holding values
- Latest holding weights
- Every historical portfolio value
- Every realised daily return
- Every asset daily return
- Current-weight daily portfolio return series
- Proposed-weight daily portfolio return series
- Every historical running peak
- Every drawdown observation
- Realised volatility, VaR and Expected Shortfall
- Maximum drawdown
- Current weight volatility, VaR and Expected Shortfall
- Proposed weight volatility, VaR and Expected Shortfall
- Weights fully invested
- Proposed weight totals and zero net trading
- Trade values for every holding
- Equity sell-off: every holding P/L
- Equity sell-off: portfolio results
- Equity sell-off: scenario summary links
- Equity sell-off: rebalance comparison
- Technology crash: every holding P/L
- Technology crash: portfolio results
- Technology crash: scenario summary links
- Technology crash: rebalance comparison
- Inflation shock: every holding P/L
- Inflation shock: portfolio results
- Inflation shock: scenario summary links
- Inflation shock: rebalance comparison
- NVDA: risk attribution
- QQQ: risk attribution
- SPY: risk attribution
- AAPL: risk attribution
- GLD: risk attribution
- IEF: risk attribution
- SPY/QQQ: correlation
- QQQ/NVDA: correlation
- SPY/IEF: correlation
- SPY/GLD: correlation
- Risk limit row 2: exposure and excess
- Risk limit row 3: exposure and excess
- Risk limit row 4: exposure and excess
- All saved formula results scanned for errors
- No broken references or external workbook links found
- Every copied running-peak, drawdown and weighted-return formula checked

## Interpretation and remaining scope

- Current-weight and proposed-weight statistics apply each fixed allocation to the same historical daily returns. These are distinct from realised buy-and-hold statistics, where weights drift.
- Risk-limit checks cover direct NVDA/AAPL holdings and total equity allocation. ETF constituent exposure has not been measured. Company exposure through funds remains a follow-up task.
- Stress assumptions are hypothetical holding-level price returns, including the chosen bond and gold shocks. The inflation scenario is not derived from an explicit yield/duration model.
- Excel holding values and risk-contribution tables are imported snapshots. Refresh them when their source data changes. The dashboard recomputes its metrics from its input files.
- There is a small label typo in Scenario summary!D1: “Value ater stress ($)”. It does not affect calculations.
- The workbook was reviewed without modifying it. Saved Excel results were checked against independent calculations; native Excel recalculation and every possible future input change were not exercised in this review.

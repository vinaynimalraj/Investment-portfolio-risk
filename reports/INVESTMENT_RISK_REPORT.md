# Investment Risk Review

**Simulated multi-asset portfolio**  
**Market-data snapshot:** 23 November 2026  
**Historical analysis period:** 24 November 2021–23 November 2026  
**Reporting currency:** USD

## Recommendation

Take the proposed rebalance to the portfolio manager for further assessment. It addresses the two defined direct-exposure breaches and reduces estimated volatility, historical tail-loss measures and losses under each of the three selected scenarios. Its increased bond and gold exposures, investment-mandate fit, transaction costs and ETF constituent exposures need review before adoption. This comparison evaluates one candidate allocation; it does not identify an optimal portfolio or establish future performance.

## Portfolio findings

The original fictional $10 million portfolio finishes at $21,169,852.98, a total return of 111.70% and a compound annualised return of 16.20%. Nvidia's direct allocation rises from 15.00% to 35.95%, and its holding contributes 68.61% of the latest allocation's estimated volatility.

Current total equity exposure is 81.70%, above the case-study limit of 65%. Direct Nvidia exposure exceeds the 12% single-stock limit. Direct Apple exposure remains below 12%. The limits apply to direct positions, with ETF overlap remaining unmeasured.

## Candidate allocation and funding

Reduce direct Nvidia exposure to 12%. Allocate half of the released capital to IEF and half to GLD, holding other investment weights unchanged.

| Measure | Current weight (%) | Proposed weight (%) |
|---|---:|---:|
| SPY | 19.43 | 19.43 |
| QQQ | 15.89 | 15.89 |
| NVDA | 35.95 | 12.00 |
| AAPL | 10.43 | 10.43 |
| IEF | 8.89 | 20.86 |
| GLD | 9.41 | 21.39 |

This requires an illustrative Nvidia sale of $5,070,118.25 and purchases of approximately $2,535,059.13 in each of IEF and GLD. The net trade value is zero before costs, using full-precision calculations. Proposed total equity exposure is 57.75%. The proposal meets all three defined direct-stock/equity checks.

## Estimated allocation risk

| Measure | Current (%) | Proposed (%) |
|---|---:|---:|
| Annualised volatility | 27.35 | 16.21 |
| One-day VaR | 2.57 | 1.59 |
| One-day Expected Shortfall | 3.67 | 2.22 |

These comparisons apply each fixed allocation to the same 1,253 historical daily asset-return observations. They are separate from realised buy-and-hold statistics, where the allocation drifts through time. The realised annualised volatility is 22.53%; the maximum historical drawdown is -28.92%.

VaR is a historical loss threshold at the stated confidence, rather than a maximum possible loss. Expected Shortfall is the average observed loss in the selected historical tail. Volatility measures variability in both gains and losses.

## Hypothetical stress scenarios

| Measure | Current return (%) | Proposed return (%) | Improvement (pp) |
|---|---:|---:|---:|
| Equity sell-off | -15.43 | -9.44 | 5.99 |
| Technology crash | -25.73 | -13.99 | 11.74 |
| Inflation shock | -19.62 | -14.00 | 5.63 |

The current allocation's largest loss is under the technology-crash assumptions. After rebalancing, the technology and inflation scenarios are virtually tied at about a 14% loss; the inflation result is marginally worse in the unrounded calculation. That tiny ranking difference should not be treated as evidence that one event is more likely or reliably more dangerous.

### Scenario inputs: holding returns (%)

| Measure | Equity sell-off | Technology crash | Inflation shock |
|---|---:|---:|---:|
| SPY | -20.00 | -15.00 | -15.00 |
| QQQ | -20.00 | -30.00 | -20.00 |
| NVDA | -20.00 | -45.00 | -30.00 |
| AAPL | -20.00 | -25.00 | -15.00 |
| IEF | 5.00 | 3.00 | -8.00 |
| GLD | 5.00 | 5.00 | -5.00 |

Each scenario applies simultaneous price shocks to the holdings. Bond and gold gains in the first two scenarios are assumptions. The inflation scenario includes losses in both holdings, demonstrating that they need not provide an offset during every shock. Its bond shock is not calculated from a specific yield movement or duration estimate.

## Trade-offs and follow-up actions

- Review the fund's objectives and expected-return implications alongside the reduction in equity exposure.
- Test additional bond and gold stresses. Their proposed weights rise to 20.86% and 21.39%.
- Obtain dated SPY and QQQ holdings to quantify total company exposures through the ETFs.
- Estimate trading costs, tax consequences and execution feasibility before implementation.
- Record how the two current breaches are escalated, monitored and resolved under the case-study risk policy.
- Refresh prices and recheck the proposal when market values change.

## Methods and verification

Prices were supplied from Yahoo Finance via yfinance, using adjusted closing-price series. Price ratios approximate reinvested distributions. The simulated historical portfolio starts with the original dollar amounts and has no rebalancing, external cash flows, leverage, transaction costs or taxes.

Volatility and covariance use sample estimates (ddof=1), with 252 trading days per year. Historical one-day VaR uses a linearly interpolated return quantile. Expected Shortfall averages observations at or below that return cutoff. Risk contributions use Euler volatility attribution. Historical relationships and the selected shocks are model inputs, not guarantees about future losses.

The Excel workbook's saved results reconcile to independent calculations in 45 checks across 12 worksheets. A scan of 5,137 formulas found no saved formula errors. Native Excel recalculation was not performed as part of that review. See WORKBOOK_REVIEW.md for the detailed scope.

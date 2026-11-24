# Validation record

Validated on 24 November 2026 using the package versions in dashboard_requirements.txt.

- **Workbook review:** 45 independent checks across 12 worksheets; 5,137 formulas scanned, no saved formula errors. Portfolio values, daily return series, copied formula ranges, drawdown, historical risk statistics, correlations, risk contributions, limits, stress results and proposed trades reconcile.
- **Calculation suite:** 8 tests cover reconciliation to the reviewed workbook, a known buy-and-hold example, quantile/tail calculations, negative hedging risk components, all three scenarios, trade funding, limit equality boundaries, changed inputs and rejection of invalid or missing inputs.
- **Streamlit application checks:** all five views run without application exceptions. Tested realised-risk mode, 99% confidence, changing Nvidia's target, rejecting an unfunded proposal while retaining the previous valid allocation, restoring the workbook proposal and changing internal limits/breach counts.
- **Export:** the comparison archive contains ten files. The report includes the selected allocation risk estimates and the indicative trades reconcile to zero net funding.
- **Local server:** starts successfully with the packaged production-mode configuration.

The cloud browser could not access this workspace's local preview, so visual browser layout inspection was not completed. Native Excel recalculation was not performed; saved workbook values and formula structures were checked against independent calculations. The Windows launcher is supplied for the user's existing investment-risk environment; it was not run on the user's Windows computer during these checks.

## Subsequent Windows confirmation

The user launched the dashboard on Windows and supplied an Overview screenshot. The headline metrics, charts, holdings and breach table were visible and consistent with the checked snapshot. Other views were checked through Streamlit application tests; full browser-based visual coverage remains outside the validation scope.

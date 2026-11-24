"""Launch with: python -m streamlit run app.py"""
from pathlib import Path
import io
import json
import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dashboard_core import (
    load_snapshot, validate_weights, validate_scenarios, risk_metrics,
    volatility_contributions, make_proposal, stress_results, limit_table,
    trade_table, recommendation,
)

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title="Investment Risk Monitor",page_icon="📊",layout="wide")
st.markdown("""<style>
.block-container{padding-top:2rem;max-width:1500px}
[data-testid="stMetric"]{background:#f4f6fb;border:1px solid #e1e6ef;border-radius:10px;padding:14px 18px}
[data-testid="stMetricLabel"]{font-weight:550}
h1,h2,h3{letter-spacing:-.025em}
</style>""",unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def read_snapshot(signature):
    return load_snapshot(ROOT/"dashboard_data")

try:
    signature=tuple((p.name,p.stat().st_mtime_ns) for p in sorted((ROOT/"dashboard_data").iterdir()) if p.is_file())
    state=read_snapshot(signature)
except (OSError,ValueError,KeyError) as exc:
    st.error(f"Unable to load portfolio inputs: {exc}")
    st.stop()

tickers=state["portfolio"].index.tolist()
current=state["current"]
if "proposal" not in st.session_state:
    st.session_state.proposal=state["proposal"].copy()
if "scenarios" not in st.session_state:
    st.session_state.scenarios=state["scenarios"].copy()
if "limits" not in st.session_state:
    st.session_state.limits=state["limits"].copy()
if "edit_version" not in st.session_state:
    st.session_state.edit_version=0

with st.sidebar:
    st.title("Portfolio review")
    page=st.radio("View",["Overview","Risk","Stress tests","Rebalance","Methods"],label_visibility="collapsed")
    confidence=st.selectbox("Historical risk confidence",[.95,.99],format_func=lambda x:f"{x:.0%}")
    st.caption(f"Data as of {state['prices'].index[-1]:%d %b %Y}")
    st.caption("Simulated USD portfolio. Changes are session-only until downloaded.")
    with st.expander("Internal limits"):
        with st.form("limits_form"):
            stock_limit=st.number_input("Direct single-stock limit (%)",min_value=0.,max_value=100.,value=float(st.session_state.limits['single_stock']*100),step=1.)
            equity_limit=st.number_input("Total equity limit (%)",min_value=0.,max_value=100.,value=float(st.session_state.limits['equity']*100),step=1.)
            if st.form_submit_button("Apply limits"):
                st.session_state.limits={**state['limits'],"single_stock":stock_limit/100,"equity":equity_limit/100}
    st.caption("Limits are illustrative internal policy choices.")

proposed=validate_weights(st.session_state.proposal,tickers)
scenarios=validate_scenarios(st.session_state.scenarios,tickers)
limits=st.session_state.limits

def chart(fig,height=340):
    fig.update_layout(template="plotly_white",height=height,margin=dict(l=10,r=15,t=20,b=10),font=dict(family="Arial",color="#273347"),legend_title_text="")
    st.plotly_chart(fig,width="stretch")

def show_frame(frame,formats=None):
    st.dataframe(frame.style.format(formats or "{:,.2f}"),width="stretch")

def snapshot_comparison():
    a=risk_metrics(state['returns'].dot(current),confidence)
    b=risk_metrics(state['returns'].dot(proposed),confidence)
    return pd.DataFrame({'Current (%)':pd.Series(a)*100,'Proposed (%)':pd.Series(b)*100})

def export_bundle():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("allocation_comparison.csv",trade_table(current,proposed,state['latest_nav']).to_csv())
        z.writestr("risk_comparison.csv",snapshot_comparison().to_csv())
        z.writestr("current_stress_results.csv",stress_results(scenarios,current,state['latest_nav']).to_csv())
        z.writestr("proposed_stress_results.csv",stress_results(scenarios,proposed,state['latest_nav']).to_csv())
        z.writestr("scenario_assumptions_decimal.csv",scenarios.to_csv())
        z.writestr("proposal_weights_decimal.csv",proposed.rename('weight').rename_axis('ticker').to_csv())
        z.writestr("selected_limits.json",json.dumps(limits,indent=2))
        z.writestr("current_limit_monitoring.csv",limit_table(current,state['portfolio'],limits).to_csv())
        z.writestr("proposed_limit_monitoring.csv",limit_table(proposed,state['portfolio'],limits).to_csv())
        z.writestr("risk_review.md",recommendation(state,proposed,scenarios,limits,confidence))
    return stream.getvalue()

st.title("Investment Risk Monitor")
st.caption(f"Simulated multi-asset portfolio · USD · {state['prices'].index[0]:%d %b %Y}–{state['prices'].index[-1]:%d %b %Y} · {len(state['returns']):,} daily returns")
if not state["matches_reviewed_inputs"]:
    st.warning("The inputs differ from the workbook-reviewed snapshot. Results have been recomputed; the earlier checks apply only to the original snapshot.")

if page=="Overview":
    now_limits=limit_table(current,state['portfolio'],limits)
    count=int(now_limits.Status.eq('BREACH').sum())
    c=st.columns(4)
    c[0].metric("Portfolio value",f"${state['latest_nav']/1e6:.2f}m")
    c[1].metric("Total historical return",f"{state['total_return']:.2%}")
    c[2].metric("Annualised compound return",f"{state['cagr']:.2%}")
    c[3].metric("Current limit breaches",str(count))
    if count:
        st.error(f"{count} current exposures exceed the selected internal limits. Review the allocation and escalation table below.")
    st.subheader("Portfolio value through time")
    chart(px.line(state['nav'].reset_index(),x="Date",y="Portfolio value (USD)",color_discrete_sequence=["#335bd6"]),380)
    left,right=st.columns([1.1,1])
    with left:
        st.subheader("Latest allocation")
        allocation=pd.DataFrame({'Holding':current.index,'Weight (%)':current.values*100})
        chart(px.bar(allocation,x='Holding',y='Weight (%)',color_discrete_sequence=['#335bd6']),280)
    with right:
        st.subheader("Performance by holding")
        gains=state['summary']['Gain/loss ($)'].sort_values().rename_axis('Holding').reset_index()
        chart(px.bar(gains,x='Gain/loss ($)',y='Holding',orientation='h',color_discrete_sequence=['#13836f']),280)
    st.subheader("Holdings")
    show_frame(state['summary'])
    st.subheader("Internal limit monitoring")
    st.dataframe(now_limits,width="stretch")
    st.caption("Direct company exposures are measured separately from ETFs. ETF constituent overlap remains unquantified.")
    st.download_button("Download holdings CSV",state['summary'].to_csv(),"holdings_summary.csv","text/csv")

elif page=="Risk":
    mode=st.radio("Allocation basis",["Latest fixed weights","Realised buy-and-hold"],horizontal=True)
    r=state['returns'].dot(current) if mode=="Latest fixed weights" else state['actual_returns']
    metrics=risk_metrics(r,confidence)
    columns=st.columns(3)
    columns[0].metric("Annualised volatility",f"{metrics['Annualised volatility']:.2%}")
    columns[1].metric(f"Historical {confidence:.0%} one-day VaR",f"{metrics['One-day VaR']:.2%}")
    columns[2].metric(f"Historical {confidence:.0%} one-day ES",f"{metrics['One-day Expected Shortfall']:.2%}")
    if mode=="Latest fixed weights":
        st.caption("The latest allocation is applied to each historical daily market movement. This estimates today's allocation risk using historical observations.")
    else:
        st.caption("Realised simulated returns use drifting weights over the entire period. These are distinct from the latest fixed-weight allocation estimates.")
    with st.expander("Interpret these measures"):
        st.write(f"The daily loss threshold at the selected confidence is {metrics['One-day VaR']:.2%}. Expected Shortfall averages the observations at or below that return cutoff. Neither is a maximum-loss guarantee. Volatility includes both upward and downward variation.")
    if mode=="Latest fixed weights":
        st.subheader("Latest allocation: sources of volatility")
        attribution=volatility_contributions(state['returns'],current)
        chart(px.bar(attribution.reset_index(),x='Holding',y='Share of volatility (%)',color_discrete_sequence=['#335bd6']))
        show_frame(attribution)
        st.caption("Shares add to 100%. A negative component, when present, represents an offset to estimated variability. This measures volatility, not a share of future losses.")
    else:
        st.subheader("Historical peak-to-trough declines")
        st.metric("Maximum historical drawdown",f"{state['drawdown'].min():.2%}")
        chart(px.area(state['drawdown'].mul(100).rename('Drawdown (%)').reset_index(),x='Date',y='Drawdown (%)',color_discrete_sequence=['#c04c51']))
    left,right=st.columns(2)
    with left:
        st.subheader("Asset return correlations")
        chart(px.imshow(state['returns'].corr(),zmin=-1,zmax=1,color_continuous_scale='RdBu',text_auto='.2f',aspect='auto'),370)
    with right:
        st.subheader("Daily portfolio returns")
        fig=px.histogram(x=r*100,nbins=65,labels={'x':'Daily return (%)'},color_discrete_sequence=['#718bd7'])
        fig.add_vline(x=-metrics['One-day VaR']*100,line_dash='dash',line_color='#c04c51')
        chart(fig,370)

elif page=="Stress tests":
    st.subheader("Hypothetical market scenarios")
    st.write("Edit holding-level return shocks, then apply them to compare the current and proposed allocations.")
    with st.form("scenario_form"):
        edited=st.data_editor(scenarios*100,num_rows="fixed",key=f"scenario_editor_{st.session_state.edit_version}",width="stretch",
            column_config={name:st.column_config.NumberColumn(name,help="Assumed holding return in percent",min_value=-100.,max_value=1000.,step=1.,format="%.1f%%") for name in scenarios.columns})
        if st.form_submit_button("Apply scenario shocks"):
            try:
                candidate=validate_scenarios(edited/100,tickers)
                st.session_state.scenarios=candidate
                scenarios=candidate
                st.success("Scenario assumptions applied.")
            except (ValueError,TypeError) as exc:
                st.error(str(exc))
    if st.button("Restore workbook scenario assumptions"):
        st.session_state.scenarios=state['scenarios'].copy()
        st.session_state.edit_version+=1
        st.rerun()
    a=stress_results(scenarios,current,state['latest_nav'])
    b=stress_results(scenarios,proposed,state['latest_nav'])
    result=pd.DataFrame({'Current return (%)':a['Scenario return (%)'],'Proposed return (%)':b['Scenario return (%)'],
        'Current loss ($)':a['Loss ($)'],'Proposed loss ($)':b['Loss ($)'],
        'Improvement (pp)':b['Scenario return (%)']-a['Scenario return (%)']})
    show_frame(result)
    chart(px.bar(result[['Current return (%)','Proposed return (%)']].reset_index().melt(id_vars='Scenario',var_name='Allocation',value_name='Return (%)'),x='Scenario',y='Return (%)',color='Allocation',barmode='group',color_discrete_sequence=['#335bd6','#13836f']))
    selected=st.selectbox("Inspect holding-level impact",list(scenarios.columns))
    impact=pd.DataFrame({'Shock (%)':scenarios[selected]*100,'Current P/L ($)':current*state['latest_nav']*scenarios[selected],
        'Proposed P/L ($)':proposed*state['latest_nav']*scenarios[selected]})
    show_frame(impact)
    st.caption("Scenarios are chosen assumptions. Bond and gold returns are direct price shocks, including the inflation scenario; they are not derived from specified yield changes.")

elif page=="Rebalance":
    st.subheader("Evaluate a fully funded allocation change")
    st.write("The workbook proposal targets 12% direct Nvidia exposure and splits released capital equally between Treasury bonds and gold.")
    with st.form("target_form"):
        c1,c2=st.columns(2)
        target=c1.number_input("Target Nvidia weight (%)",min_value=0.,max_value=100.,value=12.,step=1.)
        bond_share=c2.slider("Share of released capital allocated to IEF (%)",min_value=0,max_value=100,value=50,step=5)
        if st.form_submit_button("Apply Nvidia target"):
            try:
                proposed=make_proposal(current,target/100,bond_share/100)
                st.session_state.proposal=proposed
                st.session_state.edit_version+=1
                st.success("Proposed allocation updated.")
            except ValueError as exc:
                st.error(str(exc))
    with st.expander("Edit all proposed weights"):
        with st.form("custom_weights_form"):
            table=pd.DataFrame({'Current weight (%)':current*100,'Proposed weight (%)':proposed*100})
            edited_weights=st.data_editor(table,disabled=['Current weight (%)'],num_rows='fixed',key=f"weights_editor_{st.session_state.edit_version}",width="stretch",
                column_config={'Proposed weight (%)':st.column_config.NumberColumn(min_value=0.,max_value=100.,step=.1,format='%.2f')})
            if st.form_submit_button("Apply all weights"):
                try:
                    proposed=validate_weights(edited_weights['Proposed weight (%)']/100,tickers)
                    st.session_state.proposal=proposed
                    st.success("Proposed weights applied.")
                except (ValueError,TypeError) as exc:
                    st.error(str(exc))
    if st.button("Restore workbook proposal"):
        st.session_state.proposal=state['proposal'].copy()
        st.session_state.edit_version+=1
        st.rerun()
    st.subheader("Allocation and indicative funding")
    trades=trade_table(current,proposed,state['latest_nav'])
    show_frame(trades)
    st.caption(f"Proposed weights total {proposed.sum():.2%}. Net indicative trades: ${trades['Illustrative trade ($)'].sum():,.2f}. Positive values are purchases; negative values are sales. Trading costs and taxes are excluded.")
    st.subheader("Risk at current and proposed weights")
    show_frame(snapshot_comparison())
    old=limit_table(current,state['portfolio'],limits)
    new=limit_table(proposed,state['portfolio'],limits)
    combined=old[['Exposure (%)','Limit (%)','Status']].rename(columns={'Exposure (%)':'Current exposure (%)','Status':'Current status'})
    combined['Proposed exposure (%)']=new['Exposure (%)']
    combined['Proposed status']=new.Status
    st.subheader("Limit comparison")
    st.dataframe(combined,width="stretch")
    attribution=volatility_contributions(state['returns'],proposed)
    st.subheader("Proposed allocation: volatility contributions")
    show_frame(attribution)
    st.info(f"Proposed IEF weight: {proposed['IEF']:.2%}. Proposed gold weight: {proposed['GLD']:.2%}. Review their sensitivities and the fund mandate alongside the reduction in direct equity concentration.")
    st.download_button("Download this comparison and report",export_bundle(),"investment_risk_comparison.zip","application/zip")

else:
    st.subheader("Data and calculation methods")
    st.write(f"The loaded data contain {len(state['prices']):,} adjusted-price observations and {len(state['returns']):,} daily returns per holding, ending {state['prices'].index[-1]:%d %B %Y}. The original workbook review covered the snapshot ending {state['reference']['as_of']}.")
    st.markdown("""
- **Performance:** buy-and-hold from the first price date, with the original dollar allocations. Adjusted prices approximate reinvested distributions. Weights drift through time.
- **Allocation risk:** current or proposed fixed weights applied to the same daily asset returns. These estimates describe allocation snapshots.
- **Volatility:** sample daily standard deviation, annualised by the square root of 252.
- **VaR:** negative of the historical return quantile, with linear interpolation. **Expected Shortfall:** negative of the mean observed return at or below that cutoff.
- **Maximum drawdown:** minimum of portfolio value divided by its running peak, less one. This is shown for realised buy-and-hold performance.
- **Volatility attribution:** Euler decomposition using sample covariance. Components add to total volatility; relative shares add to 100%.
- **Scenarios:** simultaneous hypothetical price returns for each holding, with unchanged positions during the shock.
- **Limits:** direct NVDA/AAPL holdings and total equity allocation. Changing a limit updates the monitoring tables.
- **Rebalance:** a fully invested, unlevered allocation at unchanged market prices. No deposits, withdrawals, trading costs, taxes or execution are modelled.
""")
    st.warning("ETF constituent overlap has not been quantified. This dashboard does not measure look-through company, sector or issuer exposure within the funds.")
    st.caption("Data source: Yahoo Finance via yfinance. This is a supplied historical snapshot; opening the dashboard does not refresh market prices.")
    st.subheader("Workbook review")
    st.write(f"{state['reference']['check_count']} independent checks passed across {state['reference']['sheets']} worksheets. The review compared saved results and formula patterns with independent calculations; it did not run Excel's native calculation engine.")
    with st.expander("Read the workbook's saved recommendation"):
        st.write(state['reference']['recommendation'])
        st.caption("This is the recommendation saved with the original workbook, before any session changes in this dashboard.")
    st.download_button("Download workbook review notes",(ROOT/'WORKBOOK_REVIEW.md').read_text(),"WORKBOOK_REVIEW.md","text/markdown")
    st.subheader("Reproduce or refresh the analysis")
    st.write("The bundled dashboard_data files own this dashboard's inputs. Its price snapshot is kept separate from your existing data folder and your Excel workbook. Replace its adjusted_prices.csv only after validating the replacement; all risk results are then recomputed. Proposal weights, scenario shocks and limits remain explicit separate inputs. Export session changes from the Rebalance view to retain them.")
    st.markdown("[Streamlit documentation](https://docs.streamlit.io/) · [CFA risk management reference](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2011/rf-v2011-n3-1-pdf.pdf)")

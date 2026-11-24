from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from dashboard_core import (analyse_prices,load_snapshot,risk_metrics,volatility_contributions,make_proposal,stress_results,limit_table,trade_table,validate_weights,validate_scenarios)

ROOT=Path(__file__).resolve().parents[1]

class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state=load_snapshot(ROOT/'dashboard_data')

    def test_workbook_reconciliation(self):
        s=self.state; ref=s['reference']
        for r,expected in ((s['actual_returns'],ref['realised_metrics']),(s['returns'].dot(s['current']),ref['current_metrics']),(s['returns'].dot(s['proposal']),ref['proposed_metrics'])):
            np.testing.assert_allclose(list(risk_metrics(r).values()),expected,atol=1e-12)
        self.assertAlmostEqual(s['latest_nav'],ref['ending_value'],places=5)
        self.assertAlmostEqual(s['drawdown'].min(),ref['maximum_drawdown'])
        self.assertEqual(len(s['returns']),1253)
        self.assertTrue(s['matches_reviewed_inputs'])

    def test_known_buy_and_hold(self):
        p=pd.DataFrame({'ticker':['A','B'],'asset_class':['Equity','Equity'],'initial_weight':[.6,.4],'initial_investment_usd':[600.,400.]})
        x=pd.DataFrame({'B':[100.,50.,100.],'A':[100.,200.,100.]},index=pd.bdate_range('2026-01-05',periods=3,name='Date'))
        s=analyse_prices(p,x)
        np.testing.assert_allclose(s['nav'],[1000,1400,1000])
        np.testing.assert_allclose(s['actual_returns'],[.4,-2/7])

    def test_known_tail_quantile(self):
        m=risk_metrics(pd.Series([-.10,-.05,0,.05,.10]),.8)
        self.assertAlmostEqual(m['One-day VaR'],.06)
        self.assertAlmostEqual(m['One-day Expected Shortfall'],.10)

    def test_negative_hedge_contribution(self):
        r=pd.DataFrame({'A':[.01,-.01,.01,-.01],'B':[-.01,.01,-.01,.01]})
        c=volatility_contributions(r,pd.Series({'B':.2,'A':.8}))
        self.assertAlmostEqual(c.loc['A','Share of volatility (%)'],400/3)
        self.assertAlmostEqual(c.loc['B','Share of volatility (%)'],-100/3)
        self.assertAlmostEqual(c['Share of volatility (%)'].sum(),100)

    def test_stress_and_funding(self):
        s=self.state
        a=[-.15425233017578482,-.25729869370276737,-.19623740311435445]
        b=[-.09437805685896408,-.1399451180017988,-.13995558619654286]
        np.testing.assert_allclose(stress_results(s['scenarios'],s['current'],s['latest_nav'])['Scenario return (%)']/100,a,atol=1e-12)
        np.testing.assert_allclose(stress_results(s['scenarios'],s['proposal'],s['latest_nav'])['Scenario return (%)']/100,b,atol=1e-12)
        np.testing.assert_allclose(make_proposal(s['current']),s['proposal'],atol=1e-12)
        self.assertAlmostEqual(trade_table(s['current'],s['proposal'],s['latest_nav'])['Illustrative trade ($)'].sum(),0.,places=6)

    def test_limit_boundaries(self):
        s=self.state
        self.assertEqual(limit_table(s['current'],s['portfolio'],s['limits']).Status.eq('BREACH').sum(),2)
        self.assertEqual(limit_table(s['proposal'],s['portfolio'],s['limits']).Status.eq('BREACH').sum(),0)
        self.assertEqual(limit_table(s['proposal'],s['portfolio'],s['limits']).loc['Direct NVDA','Status'],'Within limit')

    def test_changes_update_results(self):
        s=self.state; new=make_proposal(s['current'],.20,.80)
        self.assertNotAlmostEqual(risk_metrics(s['returns'].dot(new))['Annualised volatility'],risk_metrics(s['returns'].dot(s['proposal']))['Annualised volatility'])
        shocks=s['scenarios'].copy(); shocks.loc['NVDA','Technology crash']=-.60
        self.assertLess(stress_results(shocks,new,s['latest_nav']).loc['Technology crash','Scenario return (%)'],stress_results(s['scenarios'],new,s['latest_nav']).loc['Technology crash','Scenario return (%)'])

    def test_invalid_inputs(self):
        s=self.state
        bad=s['proposal'].copy(); bad['NVDA']=np.nan
        with self.assertRaises(ValueError): validate_weights(bad,bad.index)
        bad=s['proposal'].copy(); bad['NVDA']+=.01
        with self.assertRaises(ValueError): validate_weights(bad,bad.index)
        shocks=s['scenarios'].copy(); shocks.iloc[0,0]=np.nan
        with self.assertRaises(ValueError): validate_scenarios(shocks,s['current'].index)
        shocks=s['scenarios'].copy(); shocks.iloc[0,0]=-1.01
        with self.assertRaises(ValueError): validate_scenarios(shocks,s['current'].index)
        with self.assertRaises(ValueError): make_proposal(s['current'],1.,.5)
        with self.assertRaises(ValueError): volatility_contributions(pd.DataFrame({'A':[0.,0.,0.]}),pd.Series({'A':1.}))

if __name__=='__main__':
    unittest.main()

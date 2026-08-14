import pytest
from retsim.core.types import TaxCategory
from retsim.models.investments import Portfolio, AssetCategory
from retsim.models.withdrawal import BaselineTieredWithdrawalBehavior


def test_qol_budget_full_satisfaction():
    portfolio = Portfolio(accounts=[
        AssetCategory(
            account_id="taxable",
            name="Taxable Brokerage",
            tax_category=TaxCategory.TAXABLE,
            average_annual_return=0.0,
            expense_ratio_fee=0.0,
            current_balance=100000.0,
        )
    ])
    behavior = BaselineTieredWithdrawalBehavior()
    res = behavior.execute_monthly_withdrawal(
        basic_target_net=2000.0,
        qol_target_net=1000.0,
        guaranteed_income_net=1500.0,
        portfolio=portfolio,
    )

    assert res.basic_satisfied is True
    assert res.delivered_basic_cash == 2000.0
    assert res.delivered_qol_cash == 1000.0
    assert res.qol_satisfaction_ratio == pytest.approx(1.0)
    # Total drawn from portfolio should be 3000 - 1500 = 1500
    assert sum(res.account_withdrawals.values()) == pytest.approx(1500.0)


def test_qol_budget_partial_satisfaction():
    # Portfolio only has $800 available
    portfolio = Portfolio(accounts=[
        AssetCategory(
            account_id="taxable",
            name="Taxable Brokerage",
            tax_category=TaxCategory.TAXABLE,
            average_annual_return=0.0,
            expense_ratio_fee=0.0,
            current_balance=800.0,
        )
    ])
    behavior = BaselineTieredWithdrawalBehavior()
    res = behavior.execute_monthly_withdrawal(
        basic_target_net=2000.0,
        qol_target_net=1000.0,
        guaranteed_income_net=1500.0,
        portfolio=portfolio,
    )

    # Basic requires 2000 - 1500 = 500 from portfolio
    # Leaves 300 for QoL. Target QoL is 1000, so delivery is 300/1000 = 30%
    assert res.basic_satisfied is True
    assert res.delivered_basic_cash == 2000.0
    assert res.delivered_qol_cash == 300.0
    assert res.qol_satisfaction_ratio == pytest.approx(0.30)
    assert portfolio.total_balance == pytest.approx(0.0)

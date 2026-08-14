import pytest
from retsim.tax.alabama import AlabamaStateTaxEngine


def test_alabama_tax_ss_and_pension_exemption():
    engine = AlabamaStateTaxEngine()

    # $50,000 Social Security + $40,000 Defined Benefit Pension -> 100% EXEMPT from AL tax
    tax_exempt = engine.calculate_annual_state_tax(
        ordinary_income=0.0,
        ss_income_annual=50000.0,
        pension_annual=40000.0,
        taxable_withdrawals_annual=0.0,
        inflation_mult=1.0,
    )
    assert tax_exempt == 0.0


def test_alabama_tax_graduated_rates():
    engine = AlabamaStateTaxEngine()

    # $20,000 taxable IRA withdrawal
    # Deductions (MFJ) = $3,000 exemption + $8,500 standard = $11,500
    # Taxable AL Income = $20,000 - $11,500 = $8,500
    # 2% on first $1,000 = $20
    # 4% on next $4,000 = $160
    # 5% on balance ($3,500) = $175
    # Total AL Tax = $20 + $160 + $175 = $355
    tax = engine.calculate_annual_state_tax(
        ordinary_income=0.0,
        ss_income_annual=0.0,
        pension_annual=0.0,
        taxable_withdrawals_annual=20000.0,
        inflation_mult=1.0,
    )
    assert tax == pytest.approx(355.0)

import pytest
from retsim.models.mortgage import Mortgage


def test_mortgage_30_year_clean_amortization():
    mort = Mortgage(
        name="Main Residence",
        original_principal=300000.0,
        annual_interest_rate=0.06,  # 6% annual interest
        term_months=360,
    )

    expected_monthly = mort.monthly_payment
    assert expected_monthly == pytest.approx(1798.65, abs=0.5)

    total_principal_paid = 0.0
    for month in range(360):
        p, princ, int_paid = mort.process_month()
        total_principal_paid += princ

    assert mort.current_balance == pytest.approx(0.0, abs=0.01)
    assert total_principal_paid == pytest.approx(300000.0, abs=0.01)

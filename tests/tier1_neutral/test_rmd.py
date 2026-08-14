import pytest
from retsim.models.rmd import RMDEngine


def test_rmd_secure_act_age_thresholds():
    engine = RMDEngine()
    assert engine.get_rmd_start_age(1948) == 72
    assert engine.get_rmd_start_age(1955) == 73
    assert engine.get_rmd_start_age(1962) == 75


def test_rmd_calculation_lookup():
    engine = RMDEngine()
    # Age 75, $1,000,000 balance -> Uniform lifetime factor = 24.6
    rmd = engine.calculate_annual_rmd(age=75, birth_year=1955, prior_dec_31_tax_deferred_balance=1000000.0)
    assert rmd == pytest.approx(1000000.0 / 24.6, rel=1e-3)

    # Age 70 (below RMD start age 73 for born 1955) -> $0 RMD
    rmd_under = engine.calculate_annual_rmd(age=70, birth_year=1955, prior_dec_31_tax_deferred_balance=1000000.0)
    assert rmd_under == 0.0

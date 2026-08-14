import pytest
from retsim.models.social_security import (
    SocialSecurityRecipient,
    SocialSecurityConfig,
    SocialSecurityEngine,
    SocialSecurityTaxabilityCalculator,
)
from retsim.models.inflation import ConstantInflationModel


def test_ss_claim_age_adjustment():
    adj_67 = SocialSecurityEngine.calculate_claim_adjustment(67, 1960)
    assert adj_67 == 1.0

    adj_62 = SocialSecurityEngine.calculate_claim_adjustment(62, 1960)
    assert adj_62 == pytest.approx(0.70)  # 30% reduction at 62

    adj_70 = SocialSecurityEngine.calculate_claim_adjustment(70, 1960)
    assert adj_70 == pytest.approx(1.24)  # 24% credit at 70


def test_ss_insolvency_cliff():
    recip = SocialSecurityRecipient(
        name="Primary",
        birth_year=1960,
        primary_insurance_amount_fra=2000.0,
        claim_age=67,
    )
    config = SocialSecurityConfig(
        recipients=[recip],
        insolvency_cliff_year=2033,
        insolvency_reduction_factor=0.77,
    )
    engine = SocialSecurityEngine(config, ConstantInflationModel(0.0), start_year=2026)

    # In 2032 (pre-cliff) -> Full benefit $2,000/mo
    ben_2032 = engine.get_monthly_benefit(recip, current_year=2032, current_age=67)
    assert ben_2032 == 2000.0

    # In 2033 (cliff year) -> 23% haircut -> $1,540/mo
    ben_2033 = engine.get_monthly_benefit(recip, current_year=2033, current_age=68)
    assert ben_2033 == pytest.approx(2000.0 * 0.77)


def test_ss_combined_income_taxability():
    # Provisional income below $32,000 -> 0% taxable
    taxable_0 = SocialSecurityTaxabilityCalculator.calculate_taxable_ss(
        non_ss_agi=15000.0, gross_ss_annual=20000.0, is_mfj=True
    )
    assert taxable_0 == 0.0

    # Provisional income $40,000 -> 50% bracket ($40k - $32k) * 0.5 = $4,000
    taxable_50 = SocialSecurityTaxabilityCalculator.calculate_taxable_ss(
        non_ss_agi=30000.0, gross_ss_annual=20000.0, is_mfj=True
    )
    assert taxable_50 == pytest.approx(4000.0)

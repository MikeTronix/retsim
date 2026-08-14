import tempfile
from pathlib import Path
import pytest

from retsim.core.config import SimulationConfig
from retsim.core.types import TaxCategory
from retsim.models.budget import BudgetConfig
from retsim.models.inflation import ConstantInflationModel
from retsim.models.investments import Portfolio, AssetCategory
from retsim.models.mortgage import Mortgage
from retsim.models.social_security import SocialSecurityConfig, SocialSecurityRecipient
from retsim.simulator.deterministic import DeterministicSimulator
from retsim.exporters.excel import ExcelExporter


def test_deterministic_simulator_end_to_end():
    # Setup test scenario: 10-year retirement simulation
    portfolio = Portfolio(accounts=[
        AssetCategory(
            account_id="taxable",
            name="Taxable Brokerage",
            tax_category=TaxCategory.TAXABLE,
            average_annual_return=0.06,
            expense_ratio_fee=0.001,
            current_balance=200000.0,
        ),
        AssetCategory(
            account_id="trad_ira",
            name="Traditional IRA",
            tax_category=TaxCategory.TRADITIONAL_IRA,
            average_annual_return=0.07,
            expense_ratio_fee=0.0015,
            current_balance=500000.0,
        ),
        AssetCategory(
            account_id="roth_ira",
            name="Roth IRA",
            tax_category=TaxCategory.ROTH_IRA,
            average_annual_return=0.07,
            expense_ratio_fee=0.0015,
            current_balance=150000.0,
        )
    ])

    recip = SocialSecurityRecipient(
        name="Primary Spouse",
        birth_year=1960,
        primary_insurance_amount_fra=2500.0,
        claim_age=67,
    )

    mortgage = Mortgage(
        name="Home Mortgage",
        original_principal=200000.0,
        annual_interest_rate=0.055,
        term_months=360,
    )

    config = SimulationConfig(
        start_year=2026,
        num_years=10,
        primary_birth_year=1960,
        primary_start_age=66,
        budget_config=BudgetConfig(
            basic_budget_base_monthly=3500.0,
            qol_budget_base_monthly=1500.0,
            base_year=2026,
        ),
        portfolio=portfolio,
        inflation_model=ConstantInflationModel(0.025),
        ss_config=SocialSecurityConfig(
            recipients=[recip],
            insolvency_cliff_year=2033,
            insolvency_reduction_factor=0.77,
        ),
        mortgages=[mortgage],
    )

    simulator = DeterministicSimulator(config)
    ledgers = simulator.run()

    # 1. Verify 10 years of annual ledgers produced
    assert len(ledgers) == 10
    assert ledgers[0].year == 2026
    assert ledgers[-1].year == 2035

    # 2. Verify basic budget was satisfied
    for lg in ledgers:
        assert lg.basic_budget_fully_satisfied is True
        assert lg.cumulative_qol_satisfaction_percentage > 0.0

    # 3. Verify Social Security started at age 67 (Year 2027)
    assert ledgers[0].total_social_security_income == 0.0  # Age 66
    assert ledgers[1].total_social_security_income > 0.0   # Age 67

    # 4. Verify Social Security insolvency cliff applied in 2033
    # Compare 2032 vs 2033 SS income (2033 should be reduced by cliff factor despite inflation)
    ss_2032 = ledgers[6].total_social_security_income
    ss_2033 = ledgers[7].total_social_security_income
    assert ss_2033 < ss_2032

    # 5. Verify Excel export functionality
    with tempfile.TemporaryDirectory() as tmp_dir:
        excel_path = Path(tmp_dir) / "retsim_output.xlsx"
        ExcelExporter.export_ledgers_to_excel(ledgers, excel_path)
        assert excel_path.exists()
        assert excel_path.stat().st_size > 0

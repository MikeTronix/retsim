from typing import Protocol


class StateTaxEngine(Protocol):
    def calculate_annual_state_tax(
        self,
        ordinary_income: float,
        ss_income_annual: float,
        pension_annual: float,
        taxable_withdrawals_annual: float,
        inflation_mult: float,
    ) -> float:
        ...


class AlabamaStateTaxEngine:
    """
    Alabama State Income Tax Engine (MFJ rules):
    - Social Security: 100% EXEMPT.
    - Defined Benefit Pensions (Government/Qualified): 100% EXEMPT.
    - Traditional IRA & 401(k) Withdrawals: TAXABLE.
    - Rates (MFJ):
        2% on first $1,000
        4% on $1,001 - $5,000 ($4,000 bracket)
        5% on balance over $5,000
    - Personal Exemption (MFJ): $3,000
    - Standard Deduction (MFJ Base): $8,500
    """

    def calculate_annual_state_tax(
        self,
        ordinary_income: float,
        ss_income_annual: float,
        pension_annual: float,
        taxable_withdrawals_annual: float,
        inflation_mult: float,
    ) -> float:
        # Alabama Taxable Income excludes Social Security & Qualified Pensions
        gross_al_income = ordinary_income + taxable_withdrawals_annual
        
        # AL Deductions & Exemptions
        al_deductions = (3000.0 + 8500.0) * inflation_mult
        al_taxable = max(0.0, gross_al_income - al_deductions)

        if al_taxable <= 0:
            return 0.0

        tax = 0.0
        # 2% on first $1,000
        b1 = min(al_taxable, 1000.0 * inflation_mult)
        tax += b1 * 0.02

        # 4% on next $4,000 ($1,000 to $5,000)
        if al_taxable > 1000.0 * inflation_mult:
            b2 = min(al_taxable - (1000.0 * inflation_mult), 4000.0 * inflation_mult)
            tax += b2 * 0.04

        # 5% on over $5,000
        if al_taxable > 5000.0 * inflation_mult:
            b3 = al_taxable - (5000.0 * inflation_mult)
            tax += b3 * 0.05

        return tax

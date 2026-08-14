from dataclasses import dataclass, field
from retsim.models.social_security import SocialSecurityTaxabilityCalculator


@dataclass
class TaxBracket:
    rate: float
    threshold: float  # Lower bound threshold for bracket


@dataclass
class FederalTaxConfig:
    standard_deduction_base: float = 29200.0  # Married Filing Jointly 2024
    brackets_base: list[TaxBracket] = field(default_factory=lambda: [
        TaxBracket(0.10, 0.0),
        TaxBracket(0.12, 23200.0),
        TaxBracket(0.22, 94300.0),
        TaxBracket(0.24, 201050.0),
        TaxBracket(0.32, 383900.0),
        TaxBracket(0.35, 487450.0),
        TaxBracket(0.37, 731200.0),
    ])


class FederalTaxEngine:
    def __init__(self, config: FederalTaxConfig | None = None):
        self.config = config or FederalTaxConfig()

    def calculate_annual_tax(
        self,
        ordinary_income_ex_ss: float,
        gross_ss_annual: float,
        pension_annual: float,
        inflation_mult: float,
        itemized_deductions: float = 0.0,
        is_mfj: bool = True,
    ) -> tuple[float, float]:
        """
        Returns: (total_federal_tax, total_agi)
        """
        # 1. Compute taxable portion of Social Security
        taxable_ss = SocialSecurityTaxabilityCalculator.calculate_taxable_ss(
            non_ss_agi=ordinary_income_ex_ss + pension_annual,
            gross_ss_annual=gross_ss_annual,
            is_mfj=is_mfj,
        )

        total_agi = ordinary_income_ex_ss + pension_annual + taxable_ss

        # 2. Inflation-adjusted standard deduction
        std_deduction = self.config.standard_deduction_base * inflation_mult
        effective_deduction = max(std_deduction, itemized_deductions)

        taxable_income = max(0.0, total_agi - effective_deduction)

        # 3. Progressive tax calculation across inflation-adjusted brackets
        adj_brackets = [
            TaxBracket(b.rate, b.threshold * inflation_mult)
            for b in self.config.brackets_base
        ]
        sorted_brackets = sorted(adj_brackets, key=lambda b: b.threshold)

        tax = 0.0
        for i, b in enumerate(sorted_brackets):
            if taxable_income <= b.threshold:
                break
            next_threshold = (
                sorted_brackets[i + 1].threshold
                if i + 1 < len(sorted_brackets)
                else taxable_income
            )
            income_in_bracket = min(taxable_income, next_threshold) - b.threshold
            if income_in_bracket > 0:
                tax += income_in_bracket * b.rate

        return tax, total_agi

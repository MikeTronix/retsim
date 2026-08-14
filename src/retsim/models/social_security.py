from dataclasses import dataclass, field
from retsim.core.types import Year
from retsim.models.inflation import InflationModel


@dataclass
class SocialSecurityRecipient:
    name: str
    birth_year: int
    primary_insurance_amount_fra: float  # Base monthly benefit at Full Retirement Age (FRA)
    claim_age: int                        # Target claiming age (62 through 70)


@dataclass
class SocialSecurityConfig:
    recipients: list[SocialSecurityRecipient] = field(default_factory=list)
    insolvency_cliff_year: Year = 2033         # Trustee report projected depletion year
    insolvency_reduction_factor: float = 0.77  # Proportional benefit cut (e.g., 23% cut -> 77% factor)


class SocialSecurityEngine:
    def __init__(self, config: SocialSecurityConfig, inflation_model: InflationModel, start_year: Year):
        self.config = config
        self.inflation_model = inflation_model
        self.start_year = start_year

    @staticmethod
    def get_full_retirement_age(birth_year: int) -> float:
        if birth_year <= 1937:
            return 65.0
        elif birth_year <= 1942:
            return 65.0 + (birth_year - 1937) * (2 / 12)
        elif birth_year <= 1954:
            return 66.0
        elif birth_year <= 1959:
            return 66.0 + (birth_year - 1954) * (2 / 12)
        else:
            return 67.0

    @classmethod
    def calculate_claim_adjustment(cls, claim_age: int, birth_year: int) -> float:
        fra = cls.get_full_retirement_age(birth_year)
        if claim_age == fra:
            return 1.0
        elif claim_age < fra:
            months_early = int((fra - claim_age) * 12)
            if months_early <= 36:
                reduction = months_early * (5 / 9 / 100)
            else:
                reduction = (36 * (5 / 9 / 100)) + ((months_early - 36) * (5 / 12 / 100))
            return max(0.0, 1.0 - reduction)
        else:
            # Delayed retirement credits: 8% per year up to age 70
            years_delayed = min(claim_age, 70) - fra
            return 1.0 + (years_delayed * 0.08)

    def get_monthly_benefit(
        self, recipient: SocialSecurityRecipient, current_year: Year, current_age: int
    ) -> float:
        if current_age < recipient.claim_age:
            return 0.0

        adj = self.calculate_claim_adjustment(recipient.claim_age, recipient.birth_year)
        base_monthly = recipient.primary_insurance_amount_fra * adj

        # Apply COLA inflation multiplier from simulation start_year
        cola_mult = self.inflation_model.get_cumulative_multiplier(self.start_year, current_year)
        monthly_benefit = base_monthly * cola_mult

        # Apply insolvency haircut cliff if year is at or past cliff year
        if current_year >= self.config.insolvency_cliff_year:
            monthly_benefit *= self.config.insolvency_reduction_factor

        return monthly_benefit


class SocialSecurityTaxabilityCalculator:
    # Unindexed Federal Thresholds (MFJ)
    BASE_THRESHOLD_MFJ = 32000.0   # 50% taxability threshold
    UPPER_THRESHOLD_MFJ = 44000.0  # 85% taxability threshold

    # Unindexed Federal Thresholds (Single)
    BASE_THRESHOLD_SINGLE = 25000.0
    UPPER_THRESHOLD_SINGLE = 34000.0

    @classmethod
    def calculate_taxable_ss(cls, non_ss_agi: float, gross_ss_annual: float, is_mfj: bool = True) -> float:
        base = cls.BASE_THRESHOLD_MFJ if is_mfj else cls.BASE_THRESHOLD_SINGLE
        upper = cls.UPPER_THRESHOLD_MFJ if is_mfj else cls.UPPER_THRESHOLD_SINGLE

        provisional_income = non_ss_agi + (0.5 * gross_ss_annual)

        if provisional_income <= base:
            return 0.0
        elif provisional_income <= upper:
            taxable_50 = 0.5 * (provisional_income - base)
            return min(taxable_50, 0.5 * gross_ss_annual)
        else:
            taxable_50 = 0.5 * (upper - base)
            taxable_85 = 0.85 * (provisional_income - upper)
            return min(taxable_50 + taxable_85, 0.85 * gross_ss_annual)

from dataclasses import dataclass, field
from retsim.core.types import Year
from retsim.models.budget import BudgetConfig
from retsim.models.inflation import InflationModel, ConstantInflationModel
from retsim.models.social_security import SocialSecurityConfig
from retsim.models.mortgage import Mortgage
from retsim.models.investments import Portfolio
from retsim.models.healthcare import MedicareConfig
from retsim.models.withdrawal import WithdrawalBehavior, BaselineTieredWithdrawalBehavior
from retsim.tax.federal import FederalTaxConfig
from retsim.tax.alabama import AlabamaStateTaxEngine, StateTaxEngine


@dataclass
class SimulationConfig:
    start_year: Year
    num_years: int
    primary_birth_year: int
    primary_start_age: int
    budget_config: BudgetConfig
    portfolio: Portfolio
    inflation_model: InflationModel = field(default_factory=ConstantInflationModel)
    ss_config: SocialSecurityConfig = field(default_factory=SocialSecurityConfig)
    mortgages: list[Mortgage] = field(default_factory=list)
    medicare_config: MedicareConfig = field(default_factory=MedicareConfig)
    federal_tax_config: FederalTaxConfig = field(default_factory=FederalTaxConfig)
    state_tax_engine: StateTaxEngine = field(default_factory=AlabamaStateTaxEngine)
    withdrawal_behavior: WithdrawalBehavior = field(default_factory=BaselineTieredWithdrawalBehavior)

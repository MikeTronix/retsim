from dataclasses import dataclass
from retsim.core.types import Year
from retsim.models.inflation import InflationModel


@dataclass
class BudgetConfig:
    basic_budget_base_monthly: float  # Non-discretionary baseline expenses
    qol_budget_base_monthly: float    # Quality of life discretionary expenses
    base_year: Year                    # Base year for initial budget dollars


class BudgetEvaluator:
    def __init__(self, config: BudgetConfig, inflation_model: InflationModel):
        self.config = config
        self.inflation_model = inflation_model

    def get_monthly_targets(self, current_year: Year) -> tuple[float, float]:
        """
        Returns (inflation_adjusted_basic_monthly, inflation_adjusted_qol_monthly).
        """
        mult = self.inflation_model.get_cumulative_multiplier(
            start_year=self.config.base_year, 
            current_year=current_year
        )
        basic_adjusted = self.config.basic_budget_base_monthly * mult
        qol_adjusted = self.config.qol_budget_base_monthly * mult
        return basic_adjusted, qol_adjusted

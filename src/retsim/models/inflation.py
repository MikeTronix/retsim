from dataclasses import dataclass, field
from typing import Protocol
from retsim.core.types import Year


class InflationModel(Protocol):
    def get_rate(self, year: Year) -> float:
        """Returns annual inflation rate for target year."""
        ...

    def get_cumulative_multiplier(self, start_year: Year, current_year: Year) -> float:
        """Returns price multiplier relative to start_year."""
        ...


@dataclass
class ConstantInflationModel:
    base_rate: float = 0.025  # 2.5% annual inflation

    def get_rate(self, year: Year) -> float:
        return self.base_rate

    def get_cumulative_multiplier(self, start_year: Year, current_year: Year) -> float:
        if current_year <= start_year:
            return 1.0
        return (1.0 + self.base_rate) ** (current_year - start_year)


@dataclass
class StepInflationModel:
    schedule: dict[Year, float] = field(default_factory=dict)  # e.g., {2026: 0.03, 2030: 0.025}
    default_rate: float = 0.025

    def get_rate(self, year: Year) -> float:
        if not self.schedule:
            return self.default_rate
        applicable_years = [y for y in sorted(self.schedule.keys()) if y <= year]
        if not applicable_years:
            return self.default_rate
        return self.schedule[applicable_years[-1]]

    def get_cumulative_multiplier(self, start_year: Year, current_year: Year) -> float:
        if current_year <= start_year:
            return 1.0
        multiplier = 1.0
        for y in range(start_year, current_year):
            multiplier *= (1.0 + self.get_rate(y))
        return multiplier

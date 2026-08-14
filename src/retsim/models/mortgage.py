from dataclasses import dataclass
from retsim.core.types import Month, Year


@dataclass
class Mortgage:
    name: str
    original_principal: float
    annual_interest_rate: float  # e.g., 0.065 for 6.5%
    term_months: int = 360       # 30 years default
    start_year: Year = 2020
    start_month: Month = 1
    current_balance: float = 0.0

    def __post_init__(self) -> None:
        if self.current_balance <= 0.0:
            self.current_balance = self.original_principal

    @property
    def monthly_payment(self) -> float:
        if self.current_balance <= 0.001:
            return 0.0
        r = self.annual_interest_rate / 12.0
        n = self.term_months
        if r == 0:
            return self.original_principal / n
        return self.original_principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

    def process_month(self) -> tuple[float, float, float]:
        """
        Processes 1 monthly payment step.
        Returns: (payment_made, principal_paid, interest_paid)
        """
        if self.current_balance <= 0.001:
            return 0.0, 0.0, 0.0

        r = self.annual_interest_rate / 12.0
        pmt = self.monthly_payment
        interest = self.current_balance * r
        principal = min(self.current_balance, pmt - interest)

        self.current_balance -= principal
        actual_payment = principal + interest
        return actual_payment, principal, interest

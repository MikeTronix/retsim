from dataclasses import dataclass, field
from retsim.core.types import TaxCategory


@dataclass
class AssetCategory:
    account_id: str
    name: str
    tax_category: TaxCategory
    average_annual_return: float  # e.g., 0.07 for 7% gross annual return
    expense_ratio_fee: float       # e.g., 0.0015 for 15 bps annual fee
    current_balance: float
    cost_basis: float = 0.0        # Cost basis for taxable accounts

    @property
    def net_annual_return_rate(self) -> float:
        return self.average_annual_return - self.expense_ratio_fee

    @property
    def net_monthly_return_rate(self) -> float:
        return (1.0 + self.net_annual_return_rate) ** (1 / 12) - 1.0

    def step_monthly_growth(self, custom_monthly_return: float | None = None) -> float:
        """
        Applies 1 month of net growth.
        Returns gross growth dollars added.
        """
        if self.current_balance <= 0.0:
            return 0.0

        r = custom_monthly_return if custom_monthly_return is not None else self.net_monthly_return_rate
        growth = self.current_balance * r
        self.current_balance += growth
        return growth

    def withdraw(self, amount: float) -> float:
        """
        Withdraws up to amount from account balance.
        Returns actual cash withdrawn.
        """
        if amount <= 0.0 or self.current_balance <= 0.0:
            return 0.0
        withdrawn = min(self.current_balance, amount)
        self.current_balance -= withdrawn
        return withdrawn


@dataclass
class Portfolio:
    accounts: list[AssetCategory] = field(default_factory=list)

    @property
    def total_balance(self) -> float:
        return sum(acct.current_balance for acct in self.accounts)

    def get_tax_deferred_balance(self) -> float:
        """Sum of Traditional IRA and 401(k) balances (subject to RMDs)."""
        return sum(
            acct.current_balance for acct in self.accounts
            if acct.tax_category in (TaxCategory.FOUR_01K, TaxCategory.TRADITIONAL_IRA)
        )

    def step_monthly_growth(self, monthly_returns_map: dict[str, float] | None = None) -> float:
        total_growth = 0.0
        for acct in self.accounts:
            ret = monthly_returns_map.get(acct.account_id) if monthly_returns_map else None
            total_growth += acct.step_monthly_growth(ret)
        return total_growth

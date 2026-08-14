from dataclasses import dataclass, field
from typing import Protocol
from retsim.core.types import TaxCategory
from retsim.models.investments import Portfolio, AssetCategory


@dataclass
class WithdrawalResult:
    delivered_basic_cash: float
    delivered_qol_cash: float
    account_withdrawals: dict[str, float]
    total_taxable_withdrawals: float
    basic_satisfied: bool
    qol_satisfaction_ratio: float  # 0.0 to 1.0 for this month


class WithdrawalBehavior(Protocol):
    def execute_monthly_withdrawal(
        self,
        basic_target_net: float,
        qol_target_net: float,
        guaranteed_income_net: float,
        portfolio: Portfolio,
        waterfall_priority: list[TaxCategory],
    ) -> WithdrawalResult:
        """
        Executes spending determination and portfolio withdrawals.
        """
        ...


@dataclass
class BaselineTieredWithdrawalBehavior:
    """
    Default strategy:
    1. Satisfies 100% of basic_target_net first.
    2. Satisfies as much as possible of qol_target_net second.
    3. Draws from portfolio using waterfall priority (Taxable -> 401k -> TradIRA -> RothIRA).
    """

    def execute_monthly_withdrawal(
        self,
        basic_target_net: float,
        qol_target_net: float,
        guaranteed_income_net: float,
        portfolio: Portfolio,
        waterfall_priority: list[TaxCategory] | None = None,
    ) -> WithdrawalResult:
        if waterfall_priority is None:
            waterfall_priority = [
                TaxCategory.TAXABLE,
                TaxCategory.FOUR_01K,
                TaxCategory.TRADITIONAL_IRA,
                TaxCategory.ROTH_IRA,
            ]

        # Step 1: Apply guaranteed income towards basic_target_net first
        basic_rem_net = max(0.0, basic_target_net - guaranteed_income_net)
        surplus_income = max(0.0, guaranteed_income_net - basic_target_net)

        # Step 2: Apply surplus income towards qol_target_net
        qol_rem_net = max(0.0, qol_target_net - surplus_income)
        delivered_qol_income = min(qol_target_net, surplus_income)

        total_net_portfolio_needed = basic_rem_net + qol_rem_net
        account_withdrawals: dict[str, float] = {}
        total_taxable_withdrawals = 0.0

        cash_withdrawn = 0.0
        remaining_needed = total_net_portfolio_needed

        # Execute waterfall priority across tax categories
        for cat in waterfall_priority:
            if remaining_needed <= 0.001:
                break
            matching_accounts = [a for a in portfolio.accounts if a.tax_category == cat]
            for acct in matching_accounts:
                if remaining_needed <= 0.001:
                    break
                drawn = acct.withdraw(remaining_needed)
                if drawn > 0:
                    account_withdrawals[acct.account_id] = account_withdrawals.get(acct.account_id, 0.0) + drawn
                    cash_withdrawn += drawn
                    remaining_needed -= drawn
                    if cat in (TaxCategory.FOUR_01K, TaxCategory.TRADITIONAL_IRA):
                        total_taxable_withdrawals += drawn

        # Distribute drawn cash: BasicBudget first, then QoLBudget
        delivered_basic = min(basic_target_net, guaranteed_income_net + cash_withdrawn)
        basic_satisfied = delivered_basic >= (basic_target_net - 0.01)

        total_qol_cash_delivered = delivered_qol_income + max(0.0, cash_withdrawn - basic_rem_net)
        delivered_qol = min(qol_target_net, total_qol_cash_delivered)

        qol_ratio = 1.0 if qol_target_net <= 0.0 else min(1.0, max(0.0, delivered_qol / qol_target_net))

        return WithdrawalResult(
            delivered_basic_cash=delivered_basic,
            delivered_qol_cash=delivered_qol,
            account_withdrawals=account_withdrawals,
            total_taxable_withdrawals=total_taxable_withdrawals,
            basic_satisfied=basic_satisfied,
            qol_satisfaction_ratio=qol_ratio,
        )

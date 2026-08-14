from dataclasses import dataclass, field
from retsim.core.types import Month, Year


@dataclass
class MonthlyState:
    year: Year
    month: Month
    month_index: int  # 0-indexed total month count
    age: int
    
    # Portfolio balances at start of month
    total_portfolio_start: float
    
    # Budgets & Spending Targets
    basic_budget_target: float
    qol_budget_target: float
    
    # Income Streams
    social_security_income: float
    pension_income: float
    other_income: float
    
    # Debt & Obligations
    mortgage_payment: float
    mortgage_interest: float
    mortgage_principal: float
    
    # Healthcare & IRMAA
    healthcare_cost: float
    irmaa_surcharge: float
    
    # RMDs
    rmd_mandatory_amount: float
    rmd_withdrawn_amount: float
    
    # Portfolio Withdrawals
    total_withdrawn: float
    withdrawn_taxable: float
    withdrawn_401k: float
    withdrawn_trad_ira: float
    withdrawn_roth_ira: float
    
    # Taxes
    estimated_federal_tax: float
    estimated_state_tax: float
    
    # Budget Fulfillment
    delivered_basic_cash: float
    delivered_qol_cash: float
    basic_satisfied: bool
    qol_satisfaction_ratio: float  # 0.0 to 1.0 for this month
    
    # Portfolio balances at end of month
    total_portfolio_end: float


@dataclass
class QoLSatisfactionTracker:
    total_qol_target_cum: float = 0.0
    total_qol_delivered_cum: float = 0.0

    def add_month(self, target: float, delivered: float) -> None:
        self.total_qol_target_cum += target
        self.total_qol_delivered_cum += delivered

    @property
    def cumulative_satisfaction_ratio(self) -> float:
        if self.total_qol_target_cum <= 0.0:
            return 1.0
        return min(1.0, max(0.0, self.total_qol_delivered_cum / self.total_qol_target_cum))

    @property
    def cumulative_satisfaction_percentage(self) -> float:
        return self.cumulative_satisfaction_ratio * 100.0


@dataclass
class AnnualSnapshotLedger:
    year: Year
    starting_age: int
    ending_age: int
    
    # Aggregated Financial Totals for Year
    total_portfolio_start: float
    total_portfolio_end: float
    
    total_gross_income: float
    total_social_security_income: float
    total_pension_income: float
    
    total_basic_budget_target: float
    total_delivered_basic_cash: float
    total_qol_budget_target: float
    total_delivered_qol_cash: float
    
    total_mortgage_paid: float
    total_mortgage_principal: float
    total_mortgage_interest: float
    
    total_healthcare_paid: float
    total_irmaa_paid: float
    
    total_rmd_taken: float
    
    total_withdrawn_taxable: float
    total_withdrawn_401k: float
    total_withdrawn_trad_ira: float
    total_withdrawn_roth_ira: float
    total_portfolio_withdrawn: float
    
    total_federal_tax_paid: float
    total_state_tax_paid: float
    
    # Annual & Cumulative QoL Satisfaction Metrics
    annual_qol_satisfaction_ratio: float
    cumulative_qol_satisfaction_ratio: float
    cumulative_qol_satisfaction_percentage: float
    basic_budget_fully_satisfied: bool
    magi_for_irmaa: float = 0.0  # Computed MAGI for IRMAA T-2 lookback

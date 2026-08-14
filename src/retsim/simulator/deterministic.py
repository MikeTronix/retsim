from retsim.core.config import SimulationConfig
from retsim.core.state import MonthlyState, AnnualSnapshotLedger, QoLSatisfactionTracker
from retsim.models.budget import BudgetEvaluator
from retsim.models.social_security import SocialSecurityEngine
from retsim.models.healthcare import MedicareIRMAAEngine
from retsim.models.rmd import RMDEngine
from retsim.tax.federal import FederalTaxEngine


class DeterministicSimulator:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.budget_evaluator = BudgetEvaluator(config.budget_config, config.inflation_model)
        self.ss_engine = SocialSecurityEngine(
            config.ss_config, config.inflation_model, config.start_year
        )
        self.healthcare_engine = MedicareIRMAAEngine(config.medicare_config)
        self.rmd_engine = RMDEngine()
        self.federal_tax_engine = FederalTaxEngine(config.federal_tax_config)
        self.qol_tracker = QoLSatisfactionTracker()

    def run(self) -> list[AnnualSnapshotLedger]:
        annual_ledgers: list[AnnualSnapshotLedger] = []
        
        # Track 2-year lookback MAGI for IRMAA (Defaults to base budget level initially)
        magi_history: dict[int, float] = {}

        total_months = self.config.num_years * 12
        current_year = self.config.start_year
        current_age = self.config.primary_start_age

        monthly_states_current_year: list[MonthlyState] = []
        year_start_portfolio = self.config.portfolio.total_balance

        for month_idx in range(total_months):
            month_in_year = (month_idx % 12) + 1
            years_from_start = month_idx // 12
            current_year = self.config.start_year + years_from_start
            current_age = self.config.primary_start_age + years_from_start

            port_start_m = self.config.portfolio.total_balance

            # 1. Step Monthly Investment Growth (Net of Fees)
            self.config.portfolio.step_monthly_growth()

            # 2. Compute Inflation-Adjusted Monthly Budgets
            basic_target_m, qol_target_m = self.budget_evaluator.get_monthly_targets(current_year)

            # 3. Accrue Social Security Income for Month
            ss_income_m = 0.0
            for recip in self.config.ss_config.recipients:
                ss_income_m += self.ss_engine.get_monthly_benefit(
                    recip, current_year, current_age
                )

            # 4. Pay Mortgages for Month
            mort_payment_m = 0.0
            mort_princ_m = 0.0
            mort_int_m = 0.0
            for mort in self.config.mortgages:
                p, princ, int_paid = mort.process_month()
                mort_payment_m += p
                mort_princ_m += princ
                mort_int_m += int_paid

            # 5. Compute Medicare & IRMAA Costs (2-year MAGI lookback)
            magi_t_minus_2 = magi_history.get(current_year - 2, 0.0)
            base_health_m, irmaa_m = self.healthcare_engine.calculate_monthly_healthcare(
                age=current_age,
                magi_t_minus_2=magi_t_minus_2,
                years_from_start=years_from_start
            )
            total_health_m = base_health_m + irmaa_m

            # 6. Check RMD Requirements for Month (Dec 31 Prior Tax-Deferred Balance)
            rmd_m = 0.0
            if month_in_year == 1:
                # Dec 31 prior balance approximation
                prior_tax_deferred = self.config.portfolio.get_tax_deferred_balance()
                annual_rmd = self.rmd_engine.calculate_annual_rmd(
                    age=current_age,
                    birth_year=self.config.primary_birth_year,
                    prior_dec_31_tax_deferred_balance=prior_tax_deferred
                )
                rmd_m = annual_rmd / 12.0
            else:
                rmd_m = 0.0  # RMD processed in first month or spread

            # Total non-discretionary baseline obligation = BasicBudget + Mortgage + Healthcare
            total_basic_obligation_m = basic_target_m + mort_payment_m + total_health_m

            # 7. Execute Modular Withdrawal Strategy
            withdrawal_res = self.config.withdrawal_behavior.execute_monthly_withdrawal(
                basic_target_net=total_basic_obligation_m,
                qol_target_net=qol_target_m,
                guaranteed_income_net=ss_income_m,
                portfolio=self.config.portfolio,
            )

            # Record QoL tracking
            self.qol_tracker.add_month(qol_target_m, withdrawal_res.delivered_qol_cash)

            port_end_m = self.config.portfolio.total_balance

            # Estimate tax withholdings
            est_fed_tax_m = (withdrawal_res.total_taxable_withdrawals * 0.12) / 12.0
            est_state_tax_m = (withdrawal_res.total_taxable_withdrawals * 0.04) / 12.0

            m_state = MonthlyState(
                year=current_year,
                month=month_in_year,
                month_index=month_idx,
                age=current_age,
                total_portfolio_start=port_start_m,
                basic_budget_target=basic_target_m,
                qol_budget_target=qol_target_m,
                social_security_income=ss_income_m,
                pension_income=0.0,
                other_income=0.0,
                mortgage_payment=mort_payment_m,
                mortgage_interest=mort_int_m,
                mortgage_principal=mort_princ_m,
                healthcare_cost=base_health_m,
                irmaa_surcharge=irmaa_m,
                rmd_mandatory_amount=rmd_m,
                rmd_withdrawn_amount=rmd_m if withdrawal_res.total_taxable_withdrawals >= rmd_m else withdrawal_res.total_taxable_withdrawals,
                total_withdrawn=sum(withdrawal_res.account_withdrawals.values()),
                withdrawn_taxable=withdrawal_res.account_withdrawals.get("taxable", 0.0),
                withdrawn_401k=withdrawal_res.account_withdrawals.get("401k", 0.0),
                withdrawn_trad_ira=withdrawal_res.account_withdrawals.get("trad_ira", 0.0),
                withdrawn_roth_ira=withdrawal_res.account_withdrawals.get("roth_ira", 0.0),
                estimated_federal_tax=est_fed_tax_m,
                estimated_state_tax=est_state_tax_m,
                delivered_basic_cash=withdrawal_res.delivered_basic_cash,
                delivered_qol_cash=withdrawal_res.delivered_qol_cash,
                basic_satisfied=withdrawal_res.basic_satisfied,
                qol_satisfaction_ratio=withdrawal_res.qol_satisfaction_ratio,
                total_portfolio_end=port_end_m,
            )
            monthly_states_current_year.append(m_state)

            # End of Year Rollup
            if month_in_year == 12 or month_idx == total_months - 1:
                year_ss = sum(ms.social_security_income for ms in monthly_states_current_year)
                year_taxable_withdrawn = sum(
                    ms.withdrawn_401k + ms.withdrawn_trad_ira for ms in monthly_states_current_year
                )

                inf_mult = self.config.inflation_model.get_cumulative_multiplier(
                    self.config.start_year, current_year
                )

                # Compute exact annual taxes
                actual_fed_tax, magi_calculated = self.federal_tax_engine.calculate_annual_tax(
                    ordinary_income_ex_ss=0.0,
                    gross_ss_annual=year_ss,
                    pension_annual=0.0,
                    inflation_mult=inf_mult,
                    itemized_deductions=0.0,
                )
                actual_state_tax = self.config.state_tax_engine.calculate_annual_state_tax(
                    ordinary_income=0.0,
                    ss_income_annual=year_ss,
                    pension_annual=0.0,
                    taxable_withdrawals_annual=year_taxable_withdrawn,
                    inflation_mult=inf_mult,
                )

                magi_history[current_year] = magi_calculated

                year_qol_target = sum(ms.qol_budget_target for ms in monthly_states_current_year)
                year_qol_delivered = sum(ms.delivered_qol_cash for ms in monthly_states_current_year)
                annual_qol_ratio = 1.0 if year_qol_target == 0 else min(1.0, year_qol_delivered / year_qol_target)

                ledger = AnnualSnapshotLedger(
                    year=current_year,
                    starting_age=monthly_states_current_year[0].age,
                    ending_age=monthly_states_current_year[-1].age,
                    total_portfolio_start=year_start_portfolio,
                    total_portfolio_end=self.config.portfolio.total_balance,
                    total_gross_income=year_ss,
                    total_social_security_income=year_ss,
                    total_pension_income=0.0,
                    total_basic_budget_target=sum(ms.basic_budget_target for ms in monthly_states_current_year),
                    total_delivered_basic_cash=sum(ms.delivered_basic_cash for ms in monthly_states_current_year),
                    total_qol_budget_target=year_qol_target,
                    total_delivered_qol_cash=year_qol_delivered,
                    total_mortgage_paid=sum(ms.mortgage_payment for ms in monthly_states_current_year),
                    total_mortgage_principal=sum(ms.mortgage_principal for ms in monthly_states_current_year),
                    total_mortgage_interest=sum(ms.mortgage_interest for ms in monthly_states_current_year),
                    total_healthcare_paid=sum(ms.healthcare_cost for ms in monthly_states_current_year),
                    total_irmaa_paid=sum(ms.irmaa_surcharge for ms in monthly_states_current_year),
                    total_rmd_taken=sum(ms.rmd_mandatory_amount for ms in monthly_states_current_year),
                    total_withdrawn_taxable=sum(ms.withdrawn_taxable for ms in monthly_states_current_year),
                    total_withdrawn_401k=sum(ms.withdrawn_401k for ms in monthly_states_current_year),
                    total_withdrawn_trad_ira=sum(ms.withdrawn_trad_ira for ms in monthly_states_current_year),
                    total_withdrawn_roth_ira=sum(ms.withdrawn_roth_ira for ms in monthly_states_current_year),
                    total_portfolio_withdrawn=sum(ms.total_withdrawn for ms in monthly_states_current_year),
                    total_federal_tax_paid=actual_fed_tax,
                    total_state_tax_paid=actual_state_tax,
                    annual_qol_satisfaction_ratio=annual_qol_ratio,
                    cumulative_qol_satisfaction_ratio=self.qol_tracker.cumulative_satisfaction_ratio,
                    cumulative_qol_satisfaction_percentage=self.qol_tracker.cumulative_satisfaction_percentage,
                    basic_budget_fully_satisfied=all(ms.basic_satisfied for ms in monthly_states_current_year),
                    magi_for_irmaa=magi_calculated,
                )
                annual_ledgers.append(ledger)

                # Reset for next year
                monthly_states_current_year = []
                year_start_portfolio = self.config.portfolio.total_balance

        return annual_ledgers

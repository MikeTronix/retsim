# User's Guide: `retsim` Modular Retirement Simulator

Welcome to **`retsim`**, a typed Python library designed for multi-decade retirement planning, tax projection, healthcare cost modeling, and cash flow simulation.

Whether you are a financial planner, fiduciary advisor, or software engineer, `retsim` provides an institutional-grade simulation framework that bridges the gap between oversimplified retail calculators and real-world tax & financial friction.

---

## 1. Overview & Key Principles

`retsim` is built around six foundational architectural principles:

1. **Monthly Core Calculation Loop (\(dt = \frac{1}{12}\)):** All asset growth, inflation compounding, mortgage payments, Social Security income accruals, RMD checks, and portfolio withdrawals execute internally on a **monthly schedule**. Monthly states are aggregated into high-level **annual snapshot ledgers**.
2. **Tiered Budget Model (`BasicBudget` & `QoLBudget`):**
   - **`BasicBudget` (Mandatory):** Non-discretionary baseline expenses (housing, utilities, debt/mortgage, basic food, medical). Must always be 100% satisfied. If portfolio liquidity is exhausted, an explicit insolvency flag is raised.
   - **`QoLBudget` (Discretionary Quality of Life):** Discretionary lifestyle expenses (travel, dining, hobbies). Satisfied to the maximum extent possible after `BasicBudget` and taxes are met.
   - **Cumulative QoL Satisfaction Index (\(0\%\)–\(100\%\)):**
     \[\text{QoL}_{\text{cum\_satisfaction}} = \frac{\sum_{m=1}^M \text{Delivered QoL}_m}{\sum_{m=1}^M \text{Target QoL}_m} \times 100\%\]
3. **Modular `WithdrawalBehavior` Protocol Strategy Pattern:** Decouples spending and portfolio withdrawal logic into pluggable strategy modules. Default strategy follows the priority waterfall:
   \[\text{Taxable (Brokerage / Already-Taxed Basis)} \longrightarrow \text{401(k) Accounts} \longrightarrow \text{Traditional IRA} \longrightarrow \text{Roth IRA}\]
4. **Medicare Part B/D & 2-Year Lookback IRMAA Engine:** Calculates Medicare premiums plus Income-Related Monthly Adjustment Amount (IRMAA) surcharges based on Modified Adjusted Gross Income (MAGI) from **2 years prior** (\(T-2\)).
5. **Tax Friction & Social Security Combined Income:** Models unindexed Federal Provisional Income thresholds (\$25,000 / \$32,000 at 50%, \$34,000 / \$44,000 at 85%) alongside a modular state tax engine (initialized with Alabama state tax exemptions).
6. **Correlated Stochastic Engine:** Models multivariate asset returns using Cholesky Decomposition (\(\mathbf{L}\mathbf{L}^T = \mathbf{\Sigma}\)) with automated Higham Positive Semi-Definite (PSD) matrix repair.

---

## 2. Installation & Environment Setup

### Prerequisites
- **Python:** Version 3.11 or higher
- **Dependencies:** `pydantic`, `numpy`, `scipy`, `pandas`, `openpyxl`

### Installation
Clone the repository and install `retsim` in editable mode:

```bash
git clone https://github.com/your-repo/retsim.git
cd retsim
pip install -e .
```

To install development dependencies (for running `pytest` and `mypy`):

```bash
pip install -e ".[dev]"
```

---

## 3. Package Structure & Module Reference

```
retsim/
├── pyproject.toml                 # Package configuration & dependencies
├── README.md                      # High-level summary
├── users_guide.md                 # Complete User's Guide (this document)
├── src/
│   └── retsim/
│       ├── core/
│       │   ├── types.py           # Domain Enums (TaxCategory, ClaimAge, TaxFilingStatus)
│       │   ├── config.py          # SimulationConfig master container
│       │   └── state.py           # MonthlyState & AnnualSnapshotLedger
│       ├── models/
│       │   ├── budget.py          # BudgetConfig & BudgetEvaluator
│       │   ├── withdrawal.py      # WithdrawalBehavior Protocol & Baseline Strategy
│       │   ├── social_security.py # Social Security PIA, claim ages, insolvency cliff
│       │   ├── mortgage.py        # 30-year fixed home mortgage schedule
│       │   ├── rmd.py             # SECURE 2.0 & IRS Pub 590-B RMD calculator
│       │   ├── healthcare.py      # Medicare Part B/D + IRMAA lookback engine
│       │   ├── investments.py     # AssetCategory & Portfolio containers
│       │   └── inflation.py       # Constant & Step inflation models
│       ├── tax/
│       │   ├── federal.py         # Progressive Federal tax & SS Combined Income tax
│       │   └── alabama.py         # Alabama State Tax Engine & exemptions
│       ├── simulator/
│       │   ├── deterministic.py   # Phase (a) Deterministic Step Engine
│       │   └── stochastic.py      # Phase (b) Correlated Multivariate Return Generator
│       └── exporters/
│           └── excel.py           # Multi-tab Excel ledger exporter
└── tests/
    ├── tier1_neutral/             # Analytical neutral portfolio unit tests
    ├── tier2_benchmarks/          # External benchmark parity checks
    └── test_deterministic_engine.py # End-to-end integration tests
```

---

## 4. Subsystem Deep Dive

### 4.1 Budget System (`retsim.models.budget`)
`retsim` breaks living costs into two distinct pools:

1. **`BasicBudget`:** Essential baseline expenses. The simulator enforces 100% satisfaction every month. If cash liquidity drops below `BasicBudget`, `basic_satisfied` is set to `False` and an insolvency flag is raised.
2. **`QoLBudget`:** Discretionary lifestyle expenses. Fulfillable to the extent portfolio liquidity permits.

#### Code Example:
```python
from retsim.models.budget import BudgetConfig

budget_cfg = BudgetConfig(
    basic_budget_base_monthly=3500.0,  # $3,500/mo essential baseline
    qol_budget_base_monthly=1500.0,    # $1,500/mo discretionary QoL
    base_year=2026
)
```

---

### 4.2 Portfolio & Priority Withdrawal Waterfall (`retsim.models.investments` & `retsim.models.withdrawal`)

Up to 10 asset categories can be configured across three tax structures:
- `TaxCategory.TAXABLE`: Taxable brokerage accounts (already-taxed basis + capital gains).
- `TaxCategory.FOUR_01K`: Traditional 401(k) / 403(b) tax-deferred accounts.
- `TaxCategory.TRADITIONAL_IRA`: Traditional IRA tax-deferred accounts.
- `TaxCategory.ROTH_IRA`: Roth IRA tax-free growth and withdrawal accounts.

The default strategy `BaselineTieredWithdrawalBehavior` draws cash according to the priority waterfall:

\[\text{Taxable (Already-Taxed Basis)} \longrightarrow \text{401(k)} \longrightarrow \text{Traditional IRA} \longrightarrow \text{Roth IRA}\]

#### Code Example:
```python
from retsim.core.types import TaxCategory
from retsim.models.investments import Portfolio, AssetCategory

portfolio = Portfolio(accounts=[
    AssetCategory(
        account_id="taxable",
        name="Taxable Brokerage",
        tax_category=TaxCategory.TAXABLE,
        average_annual_return=0.06,  # 6% gross annual return
        expense_ratio_fee=0.001,     # 10 bps fee
        current_balance=200000.0,
    ),
    AssetCategory(
        account_id="trad_ira",
        name="Traditional IRA",
        tax_category=TaxCategory.TRADITIONAL_IRA,
        average_annual_return=0.07,
        expense_ratio_fee=0.0015,
        current_balance=500000.0,
    ),
    AssetCategory(
        account_id="roth_ira",
        name="Roth IRA",
        tax_category=TaxCategory.ROTH_IRA,
        average_annual_return=0.07,
        expense_ratio_fee=0.0015,
        current_balance=150000.0,
    ),
])
```

---

### 4.3 Social Security Engine (`retsim.models.social_security`)

Models recipient birth year, Primary Insurance Amount (PIA) at Full Retirement Age (FRA), claiming age (62–70), COLA indexation, and the scheduled Trustee Report insolvency cliff.

- **Claiming Age Multipliers:**
  - Age 62 (Early): 30% benefit reduction for birth year \(\ge 1960\).
  - Age 67 (FRA): 100% benefit payout.
  - Age 70 (Delayed): 124% benefit payout (8% delayed retirement credits per year).
- **Insolvency Cliff:** Programmable benefit cut (e.g. 23% reduction starting in 2033).
- **Federal Combined Income Taxability:** Calculates taxable Social Security portion based on provisional income:

\[\text{Provisional Income} = \text{AGI (excl. SS)} + \text{Tax-Exempt Interest} + 0.5 \times \text{Gross SS Benefit}\]

#### Code Example:
```python
from retsim.models.social_security import SocialSecurityConfig, SocialSecurityRecipient

recip = SocialSecurityRecipient(
    name="Primary Spouse",
    birth_year=1960,
    primary_insurance_amount_fra=2500.0, # $2,500/mo at FRA
    claim_age=67,
)

ss_cfg = SocialSecurityConfig(
    recipients=[recip],
    insolvency_cliff_year=2033,         # Trustee report depletion year
    insolvency_reduction_factor=0.77,   # 23% benefit cut
)
```

---

### 4.4 Home Mortgages (`retsim.models.mortgage`)

Models 30-year fixed home mortgages, tracking principal vs. interest breakdown for itemized tax deduction purposes and verifying exact \$0.00 balance payoff at month 360.

#### Code Example:
```python
from retsim.models.mortgage import Mortgage

mortgage = Mortgage(
    name="Primary Residence",
    original_principal=250000.0,
    annual_interest_rate=0.055,  # 5.5% fixed interest
    term_months=360,
)
```

---

### 4.5 Healthcare & Medicare Part B/D + IRMAA (`retsim.models.healthcare`)

- **Pre-65 Bridge:** Inflation-adjusted private health insurance costs.
- **Post-65 Medicare Part B & D:** Inflation-adjusted base premiums.
- **2-Year MAGI Lookback IRMAA Surcharges:** Evaluates MAGI from year \(T-2\) against IRMAA tiers, applying monthly surcharges if thresholds are crossed.

---

### 4.6 Tax Subsystem (Federal & Alabama State Tax) (`retsim.tax`)

- **Federal Tax Engine (`FederalTaxEngine`):** Inflation-projected tax brackets, standard deduction, and Social Security taxability integration.
- **Alabama State Tax Engine (`AlabamaStateTaxEngine`):**
  - **Exemptions:** Social Security (100% EXEMPT), Qualified Defined Benefit Pensions (100% EXEMPT).
  - **Taxable:** Traditional IRA and 401(k) withdrawals.
  - **Rates (MFJ):** 2% on first \$1,000, 4% on next \$4,000, 5% on balance over \$5,000.

---

### 4.7 Correlated Asset Stochastic Engine (`retsim.simulator.stochastic`)

Generates correlated multivariate monthly asset returns using Cholesky Decomposition:

\[\mathbf{r}_m = \boldsymbol{\mu}_m + \mathbf{L} \mathbf{z}_m, \quad \text{where } \mathbf{L}\mathbf{L}^T = \mathbf{\Sigma}, \, \mathbf{z}_m \sim \mathcal{N}(\mathbf{0}, \mathbf{I})\]

Includes automated **Higham Positive Semi-Definite (PSD) matrix repair** via eigenvalue clipping to fix invalid user-specified cross-correlation matrices.

---

## 5. End-to-End Simulation Script Example

Below is a complete, runnable Python script demonstrating how to configure, run, inspect, and export a 10-year retirement simulation:

```python
from pathlib import Path
from retsim.core.config import SimulationConfig
from retsim.core.types import TaxCategory
from retsim.models.budget import BudgetConfig
from retsim.models.inflation import ConstantInflationModel
from retsim.models.investments import Portfolio, AssetCategory
from retsim.models.mortgage import Mortgage
from retsim.models.social_security import SocialSecurityConfig, SocialSecurityRecipient
from retsim.simulator.deterministic import DeterministicSimulator
from retsim.exporters.excel import ExcelExporter

def main():
    # 1. Define Portfolio Accounts
    portfolio = Portfolio(accounts=[
        AssetCategory(
            account_id="taxable",
            name="Taxable Brokerage",
            tax_category=TaxCategory.TAXABLE,
            average_annual_return=0.06,
            expense_ratio_fee=0.001,
            current_balance=200000.0,
        ),
        AssetCategory(
            account_id="trad_ira",
            name="Traditional IRA",
            tax_category=TaxCategory.TRADITIONAL_IRA,
            average_annual_return=0.07,
            expense_ratio_fee=0.0015,
            current_balance=500000.0,
        ),
        AssetCategory(
            account_id="roth_ira",
            name="Roth IRA",
            tax_category=TaxCategory.ROTH_IRA,
            average_annual_return=0.07,
            expense_ratio_fee=0.0015,
            current_balance=150000.0,
        )
    ])

    # 2. Define Social Security Recipient
    recip = SocialSecurityRecipient(
        name="Primary Spouse",
        birth_year=1960,
        primary_insurance_amount_fra=2500.0,
        claim_age=67,
    )

    # 3. Define Home Mortgage
    mortgage = Mortgage(
        name="Home Mortgage",
        original_principal=200000.0,
        annual_interest_rate=0.055,
        term_months=360,
    )

    # 4. Master Simulation Configuration
    config = SimulationConfig(
        start_year=2026,
        num_years=10,
        primary_birth_year=1960,
        primary_start_age=66,
        budget_config=BudgetConfig(
            basic_budget_base_monthly=3500.0,  # $3,500/mo essential baseline
            qol_budget_base_monthly=1500.0,    # $1,500/mo discretionary QoL
            base_year=2026,
        ),
        portfolio=portfolio,
        inflation_model=ConstantInflationModel(0.025), # 2.5% inflation
        ss_config=SocialSecurityConfig(
            recipients=[recip],
            insolvency_cliff_year=2033,
            insolvency_reduction_factor=0.77, # 23% cut in 2033
        ),
        mortgages=[mortgage],
    )

    # 5. Run Deterministic Simulator
    simulator = DeterministicSimulator(config)
    ledgers = simulator.run()

    # 6. Print Summary Output to Terminal
    print("Year | Age | Portfolio End  | SS Income | Basic Satisfied | QoL Cum % | Fed Tax")
    print("-" * 75)
    for lg in ledgers:
        print(
            f"{lg.year} |  {lg.ending_age} | ${lg.total_portfolio_end:,.2f} | "
            f"${lg.total_social_security_income:,.2f} | {lg.basic_budget_fully_satisfied} | "
            f"{lg.cumulative_qol_satisfaction_percentage:.1f}% | ${lg.total_federal_tax_paid:,.2f}"
        )

    # 7. Export to Excel Workbook
    output_excel = Path("my_retirement_ledger.xlsx")
    ExcelExporter.export_ledgers_to_excel(ledgers, output_excel)
    print(f"\nSuccessfully exported multi-tab summary ledger to {output_excel.resolve()}")

if __name__ == "__main__":
    main()
```

---

## 6. Running Automated Tests

`retsim` comes with a 13-test automated verification suite covering:
- **Tier 1 (Neutral Portfolios):** Mathematical compound growth, mortgage zero balance payoff, pure RMD decay, QoL budget fulfillment.
- **Tier 2 (External Benchmarks):** IRS Form 1040 tax tables & baseline regression CSVs.
- **Tier 3 (Property-Based Invariants):** `hypothesis` tests for conservation of money and covariance matrix convergence.

To execute the test suite:

```bash
pytest
```

---

## 7. Extending `retsim`

### 7.1 Creating a Custom `WithdrawalBehavior` Strategy
Implement the `WithdrawalBehavior` protocol to create custom dynamic guardrails (Guyton-Klinger / VPW) or tactical pre-RMD Roth conversion strategies:

```python
from retsim.models.withdrawal import WithdrawalResult
from retsim.models.investments import Portfolio
from retsim.core.types import TaxCategory

class MyCustomGuardrailStrategy:
    def execute_monthly_withdrawal(
        self,
        basic_target_net: float,
        qol_target_net: float,
        guaranteed_income_net: float,
        portfolio: Portfolio,
        waterfall_priority: list[TaxCategory] | None = None,
    ) -> WithdrawalResult:
        # Custom logic to dynamically trim qol_target_net during portfolio drawdowns
        adjusted_qol = qol_target_net * 0.8  # Example 20% trim
        # Perform withdrawal...
        ...
```

### 7.2 Creating a Custom `StateTaxEngine`
Implement the `StateTaxEngine` protocol to model other state tax systems (e.g. Florida, Georgia, California):

```python
class FloridaStateTaxEngine:
    def calculate_annual_state_tax(
        self,
        ordinary_income: float,
        ss_income_annual: float,
        pension_annual: float,
        taxable_withdrawals_annual: float,
        inflation_mult: float,
    ) -> float:
        return 0.0  # Florida has no personal income tax
```

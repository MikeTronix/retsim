# `retsim` - Modular Retirement Simulator in Typed Python

> [!WARNING]
> **USE AT YOUR OWN RISK -- THIS PRODUCT DOES NOT CONSTITUTE INVESTMENT ADVICE**  
> *This software is designed solely for educational, research, and modeling purposes. It does not provide financial, investment, tax, or legal advice. Users are strongly encouraged to consult with qualified, fiduciary financial advisors and certified tax professionals before making any financial decisions.*

---

## 📌 Features & Architectural Highlights

`retsim` is a typed Python library built for multi-decade retirement planning, tax projection, healthcare cost modeling, and cash flow simulation.

- **Simulation Granularity:** Monthly core calculation loop (\(dt = \frac{1}{12}\)) with aggregated annual summary snapshot ledgers.
- **Tiered Budget Model:**
  - `BasicBudget`: Essential baseline expenses (housing, utilities, mortgage, food, Medicare Part B/D). Always 100% satisfied.
  - `QoLBudget`: Quality of Life discretionary expenses (travel, dining, hobbies).
  - `Cumulative QoL Satisfaction Index`: Tracks lifestyle fulfillment from 0% to 100%.
- **Modular `WithdrawalBehavior` Strategy Protocol:**
  - Default Priority Waterfall: `Taxable (Already-Taxed Basis) -> 401(k) -> Traditional IRA -> Roth IRA`.
  - Strategy hooks for **Guyton-Klinger / VPW Guardrails**, **Tactical Pre-RMD Roth Conversions**, and **Tax-Aware Asset Rebalancing**.
- **Tax & Healthcare Precision:**
  - Progressive Federal Income Tax engine with inflation-projected brackets & standard deduction.
  - Social Security Combined Income taxability calculator (\$25k/\$32k and \$34k/\$44k unindexed thresholds).
  - Medicare Part B & D base premiums + 2-year lookback Modified Adjusted Gross Income (MAGI) IRMAA surcharges.
  - Modular State Tax Engine initialized with Alabama State Tax rules & exemptions.
- **Social Security & Mortgages:**
  - Full Retirement Age (FRA) adjustment (ages 62–70), COLA indexation, and Trustee Report insolvency haircut cliff modeling (e.g. 23% cut).
  - 30-year fixed home mortgage amortization tracking principal vs. interest breakdown.
- **Stochastic Returns Engine:**
  - Multivariate asset returns via Cholesky Decomposition (\(\mathbf{L}\mathbf{L}^T = \mathbf{\Sigma}\)) with Higham Positive Semi-Definite (PSD) matrix repair.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/your-repo/retsim.git
cd retsim
pip install -e .
```

### Run Example Simulation

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

# Configure Portfolio Accounts
portfolio = Portfolio(accounts=[
    AssetCategory("taxable", "Taxable Brokerage", TaxCategory.TAXABLE, 0.06, 0.001, 200000.0),
    AssetCategory("trad_ira", "Traditional IRA", TaxCategory.TRADITIONAL_IRA, 0.07, 0.0015, 500000.0),
    AssetCategory("roth_ira", "Roth IRA", TaxCategory.ROTH_IRA, 0.07, 0.0015, 150000.0),
])

# Master Configuration
config = SimulationConfig(
    start_year=2026,
    num_years=10,
    primary_birth_year=1960,
    primary_start_age=66,
    budget_config=BudgetConfig(3500.0, 1500.0, 2026),
    portfolio=portfolio,
    inflation_model=ConstantInflationModel(0.025),
    ss_config=SocialSecurityConfig(
        recipients=[SocialSecurityRecipient("Primary Spouse", 1960, 2500.0, 67)],
        insolvency_cliff_year=2033,
        insolvency_reduction_factor=0.77,
    ),
    mortgages=[Mortgage("Home Mortgage", 200000.0, 0.055, 360)],
)

# Execute Simulation & Export to Excel
simulator = DeterministicSimulator(config)
ledgers = simulator.run()
ExcelExporter.export_ledgers_to_excel(ledgers, "my_retirement_ledger.xlsx")
```

---

## 🧪 Testing

`retsim` features a 13-test automated verification suite:

```bash
pytest
```

---

## 📖 Documentation & Presentation
- 📑 **User's Guide:** [`users_guide.md`](users_guide.md)
- 📊 **Financial Planner Presentation:** [`retsim_financial_planner_presentation.pptx`](retsim_financial_planner_presentation.pptx)

---

## ⚖️ Legal Disclaimer

**USE AT YOUR OWN RISK -- THIS PRODUCT DOES NOT CONSTITUTE INVESTMENT ADVICE**

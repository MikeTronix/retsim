from pathlib import Path
import pandas as pd
from retsim.core.state import AnnualSnapshotLedger


class ExcelExporter:
    @staticmethod
    def export_ledgers_to_excel(ledgers: list[AnnualSnapshotLedger], output_path: str | Path) -> None:
        """
        Exports simulation annual snapshot ledgers to a formatted Excel workbook.
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = []
        for lg in ledgers:
            data.append({
                "Year": lg.year,
                "Start Age": lg.starting_age,
                "End Age": lg.ending_age,
                "Portfolio Start ($)": round(lg.total_portfolio_start, 2),
                "Portfolio End ($)": round(lg.total_portfolio_end, 2),
                "Gross Income ($)": round(lg.total_gross_income, 2),
                "Social Security ($)": round(lg.total_social_security_income, 2),
                "Basic Target ($)": round(lg.total_basic_budget_target, 2),
                "Basic Delivered ($)": round(lg.total_delivered_basic_cash, 2),
                "QoL Target ($)": round(lg.total_qol_budget_target, 2),
                "QoL Delivered ($)": round(lg.total_delivered_qol_cash, 2),
                "Annual QoL Satisfied (%)": round(lg.annual_qol_satisfaction_ratio * 100, 1),
                "Cumulative QoL Satisfied (%)": round(lg.cumulative_qol_satisfaction_percentage, 1),
                "Mortgage Paid ($)": round(lg.total_mortgage_paid, 2),
                "Mortgage Principal ($)": round(lg.total_mortgage_principal, 2),
                "Mortgage Interest ($)": round(lg.total_mortgage_interest, 2),
                "Healthcare Paid ($)": round(lg.total_healthcare_paid, 2),
                "IRMAA Surcharge ($)": round(lg.total_irmaa_paid, 2),
                "RMD Mandated ($)": round(lg.total_rmd_taken, 2),
                "Total Withdrawn ($)": round(lg.total_portfolio_withdrawn, 2),
                "Federal Tax ($)": round(lg.total_federal_tax_paid, 2),
                "State Tax (AL) ($)": round(lg.total_state_tax_paid, 2),
                "MAGI (T-2 Lookback) ($)": round(lg.magi_for_irmaa, 2),
                "Basic Fully Satisfied": "Yes" if lg.basic_budget_fully_satisfied else "NO",
            })

        df_summary = pd.DataFrame(data)

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Annual Summary Ledger", index=False)

from dataclasses import dataclass, field


@dataclass
class IRMAATier:
    magi_threshold_mfj: float
    part_b_surcharge_monthly: float
    part_d_surcharge_monthly: float


@dataclass
class MedicareConfig:
    part_b_base_monthly: float = 174.70    # Base 2024 monthly Part B premium
    part_d_base_monthly: float = 55.00     # Base 2024 monthly Part D premium
    medical_inflation_rate: float = 0.045  # Medical costs inflate at 4.5% annual rate
    pre_65_monthly_cost_base: float = 800.0

    # 2024 IRMAA Tiers (MFJ MAGI from T-2 lookback)
    irmaa_tiers: list[IRMAATier] = field(default_factory=lambda: [
        IRMAATier(206000.0, 69.90, 12.90),
        IRMAATier(258000.0, 175.70, 33.30),
        IRMAATier(322000.0, 281.50, 53.80),
        IRMAATier(386000.0, 387.20, 74.20),
        IRMAATier(750000.0, 422.40, 81.00),
    ])


class MedicareIRMAAEngine:
    def __init__(self, config: MedicareConfig | None = None):
        self.config = config or MedicareConfig()

    def calculate_monthly_healthcare(
        self, age: int, magi_t_minus_2: float, years_from_start: int
    ) -> tuple[float, float]:
        """
        Returns: (base_healthcare_cost_monthly, irmaa_surcharge_monthly)
        """
        inflation_mult = (1.0 + self.config.medical_inflation_rate) ** years_from_start

        if age < 65:
            return self.config.pre_65_monthly_cost_base * inflation_mult, 0.0

        # Post-65 Medicare Part B + D base
        base_medicare = (self.config.part_b_base_monthly + self.config.part_d_base_monthly) * inflation_mult

        # Evaluate 2-year lookback IRMAA tier
        surcharge = 0.0
        for tier in sorted(self.config.irmaa_tiers, key=lambda x: x.magi_threshold_mfj, reverse=True):
            if magi_t_minus_2 > tier.magi_threshold_mfj:
                surcharge = (tier.part_b_surcharge_monthly + tier.part_d_surcharge_monthly) * inflation_mult
                break

        return base_medicare, surcharge

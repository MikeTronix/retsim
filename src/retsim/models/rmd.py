from dataclasses import dataclass, field


@dataclass
class RMDEngine:
    # IRS Uniform Lifetime Table (Age -> Distribution Period Factor)
    UNIFORM_LIFETIME_TABLE: dict[int, float] = field(default_factory=lambda: {
        72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1,
        80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
        88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1, 94: 9.5, 95: 8.9,
        96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0, 102: 5.6, 103: 5.2,
        104: 4.9, 105: 4.6, 106: 4.3, 107: 4.1, 108: 3.9, 109: 3.7, 110: 3.5
    })

    def get_rmd_start_age(self, birth_year: int) -> int:
        """SECURE Act 2.0 rules for mandatory RMD start age."""
        if birth_year <= 1950:
            return 72
        elif 1951 <= birth_year <= 1959:
            return 73
        else:
            return 75  # Born 1960 or later

    def calculate_annual_rmd(self, age: int, birth_year: int, prior_dec_31_tax_deferred_balance: float) -> float:
        start_age = self.get_rmd_start_age(birth_year)
        if age < start_age or prior_dec_31_tax_deferred_balance <= 0:
            return 0.0

        factor = self.UNIFORM_LIFETIME_TABLE.get(age, max(2.0, 26.5 - (age - 73)))
        return prior_dec_31_tax_deferred_balance / factor

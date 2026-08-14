from enum import Enum, auto
from typing import TypeAlias

Money: TypeAlias = float
Year: TypeAlias = int
Month: TypeAlias = int


class TaxCategory(Enum):
    TAXABLE = auto()           # Taxable brokerage (Already-taxed basis + LTCG)
    FOUR_01K = auto()          # Traditional 401(k) / 403(b)
    TRADITIONAL_IRA = auto()   # Traditional IRA
    ROTH_IRA = auto()          # Roth IRA (Tax-free growth & withdrawals)


class TaxFilingStatus(Enum):
    SINGLE = auto()
    MFJ = auto()  # Married Filing Jointly


class ClaimAge(Enum):
    AGE_62 = 62
    AGE_63 = 63
    AGE_64 = 64
    AGE_65 = 65
    AGE_66 = 66
    AGE_67 = 67  # Standard FRA for birth years >= 1960
    AGE_68 = 68
    AGE_69 = 69
    AGE_70 = 70

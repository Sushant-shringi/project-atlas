"""
Project Atlas - Financial & Market Projection Calculator
Executes compound annual growth rate projections:
FV = PV * (1 + CAGR)^n
Enforces boundary checking on forecast years and makes assumptions explicit.
"""

from typing import Any, Dict, List, Optional, Tuple


class MarketCalculator:
    """Deterministic calculation engine for market projections and estimations."""

    @classmethod
    def calculate_future_value(
        cls,
        present_value: float,
        cagr_percent: float,
        base_year: int,
        target_year: int,
        periods: Optional[int] = None
    ) -> float:
        """
        Calculates Future Value using compound annual growth rate formula:
        FV = PV * (1 + (CAGR / 100))^n
        where n is the number of compounding periods (defaults to target_year - base_year).
        """
        n = periods if periods is not None else (target_year - base_year)
        if n < 0:
            raise ValueError(f"Target year ({target_year}) cannot precede base year ({base_year}).")
        rate = cagr_percent / 100.0
        future_value = present_value * ((1.0 + rate) ** n)
        return round(future_value, 4)

    @classmethod
    def compute_apac_smart_water_meter_2030(cls) -> Dict[str, Any]:
        """
        Computes the 2030 APAC Smart Water Meter Market projection based on R-101.
        Inputs:
        - 2024 Global Market Size: USD 4.21 Billion (R-101, p.8)
        - 2024 APAC Market Share: 38% (0.38) (R-101, p.8)
        - 2024 Base APAC Size: 4.21 * 0.38 = USD 1.5998 Billion
        - Global CAGR (2025-2030): 11.2% (R-101, p.8)
        - Compounding Periods: 5 periods (2025 through 2030 forecast window)
        Formula:
        FV = 1.5998 * (1 + 0.112)^5 = 1.5998 * 1.7000 = USD 2.7197 Billion (~ USD 2.72 Billion)
        """
        global_2024 = 4.21
        apac_share_2024 = 0.38
        base_apac_2024 = round(global_2024 * apac_share_2024, 4)  # 1.5998
        cagr = 11.20
        periods = 5  # Explicit five-period calculation for 2025-2030 forecast window

        fv = cls.calculate_future_value(
            present_value=base_apac_2024,
            cagr_percent=cagr,
            base_year=2024,
            target_year=2030,
            periods=periods
        )
        rounded_fv = round(fv, 2)  # 2.72

        return {
            "metric": "Asia-Pacific Smart Water Meter Market Size (2030 Projection)",
            "derived_value": rounded_fv,
            "unit": "USD Billion",
            "base_value": base_apac_2024,
            "base_year": 2024,
            "target_year": 2030,
            "cagr_applied": cagr,
            "formula": "FV = PV_apac * (1 + CAGR_global)^5",
            "is_derived_estimate": True,
            "assumptions": [
                "Applied global 2025–2030 CAGR of 11.2% to APAC base because report R-101 does not disclose an APAC-specific growth rate.",
                "Base 2024 APAC market valuation derived as 38% of global USD 4.21B market = USD 1.60B.",
                "Assumed compounding over 5 annual periods from end-of-year 2024/2025 baseline to 2030."
            ],
            "citations": [
                {
                    "report_id": "R-101",
                    "title": "Global Smart Water Meter Market 2025",
                    "page": 8,
                    "evidence": "Valued at USD 4.21 billion in 2024 with 11.2% CAGR from 2025 to 2030; APAC accounted for 38% of 2024 revenue."
                }
            ]
        }

    @classmethod
    def evaluate_extrapolation(cls, target_year: int, max_forecast_year: int = 2030) -> Tuple[bool, str]:
        """
        Validates whether projection target year is within report forecast boundaries.
        Returns:
            (is_valid, warning_message)
        """
        if target_year > max_forecast_year:
            return False, (
                f"Unsupported Extrapolation: The publication forecast horizon terminates at {max_forecast_year}. "
                f"Extrapolating forward to {target_year} introduces unverified macroeconomic assumptions and cannot be certified."
            )
        return True, "Valid forecast horizon."

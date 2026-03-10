"""Damages calculator with prejudgment interest computation."""

from __future__ import annotations

from datetime import date
from typing import Optional

from .models import DamagesEstimate


# ── Interest Rates by Jurisdiction ──

INTEREST_RATES: dict[str, dict] = {
    "CA": {
        "prejudgment_rate": 0.10,  # 10% per annum — Cal. Civil Code § 3287(a)
        "statute": "Cal. Civil Code § 3287(a)",
        "type": "simple",
        "notes": "Applies to damages certain or ascertainable by calculation",
    },
    "FEDERAL": {
        "prejudgment_rate": None,  # Set by court, often T-bill rate
        "statute": "28 U.S.C. § 1961",
        "type": "compound",
        "notes": "Post-judgment rate is 52-week T-bill. Pre-judgment is discretionary.",
    },
    "NY": {
        "prejudgment_rate": 0.09,  # 9% per annum — CPLR § 5004
        "statute": "N.Y. CPLR § 5004",
        "type": "simple",
        "notes": "Mandatory for most contract and tort claims",
    },
}


class DamagesCalculator:
    """Calculates estimated damages with prejudgment interest."""

    def __init__(self, jurisdiction: str = "CA"):
        self.jurisdiction = jurisdiction
        self._estimates: list[DamagesEstimate] = []

    @property
    def estimates(self) -> list[DamagesEstimate]:
        return self._estimates

    def calculate(
        self,
        claim_id: str,
        principal: float,
        underpayment_start: date,
        as_of: date = None,
        custom_rate: float = None,
        method: str = "simple",
        notes: str = "",
    ) -> DamagesEstimate:
        """Calculate damages with prejudgment interest.

        Args:
            claim_id: The claim this damages estimate relates to.
            principal: The underpayment amount (actual damages).
            underpayment_start: When the underpayment began (for interest calculation).
            as_of: Calculate interest as of this date (default: today).
            custom_rate: Override the jurisdiction's default interest rate.
            method: 'simple' or 'compound' interest calculation.
            notes: Additional notes about the calculation.
        """
        today = as_of or date.today()

        # Get interest rate
        rate_info = INTEREST_RATES.get(self.jurisdiction, INTEREST_RATES["CA"])
        rate = custom_rate if custom_rate is not None else rate_info.get("prejudgment_rate", 0.10)
        calc_method = method or rate_info.get("type", "simple")

        if rate is None:
            rate = 0.05  # Default 5% if jurisdiction rate is discretionary

        # Calculate interest
        years = (today - underpayment_start).days / 365.25

        if calc_method == "simple":
            interest = principal * rate * years
        else:  # compound
            interest = principal * ((1 + rate) ** years - 1)

        estimate = DamagesEstimate(
            claim_id=claim_id,
            principal=round(principal, 2),
            interest_rate=rate,
            interest_start_date=underpayment_start,
            accrued_interest=round(interest, 2),
            total_with_interest=round(principal + interest, 2),
            calculation_method=(
                f"{calc_method} interest at {rate*100:.1f}% per annum "
                f"({rate_info.get('statute', 'N/A')})"
            ),
            notes=notes,
        )

        self._estimates.append(estimate)
        return estimate

    def calculate_phased(
        self,
        claim_id: str,
        underpayments: list[dict],
        as_of: date = None,
    ) -> DamagesEstimate:
        """Calculate damages for multiple underpayment periods.

        Args:
            claim_id: The claim ID.
            underpayments: List of dicts with 'amount', 'start_date', and optional 'end_date'.
                Example: [{"amount": 5000, "start_date": "2015-01-01"}, ...]
            as_of: Calculate as of this date.
        """
        today = as_of or date.today()
        rate_info = INTEREST_RATES.get(self.jurisdiction, INTEREST_RATES["CA"])
        rate = rate_info.get("prejudgment_rate", 0.10)

        total_principal = 0.0
        total_interest = 0.0
        details = []

        for period in underpayments:
            amount = period["amount"]
            start = period["start_date"]
            if isinstance(start, str):
                start = date.fromisoformat(start)

            years = (today - start).days / 365.25
            interest = amount * rate * years

            total_principal += amount
            total_interest += interest
            details.append(f"${amount:,.2f} from {start} ({years:.1f}yr = ${interest:,.2f} interest)")

        estimate = DamagesEstimate(
            claim_id=claim_id,
            principal=round(total_principal, 2),
            interest_rate=rate,
            interest_start_date=underpayments[0]["start_date"] if underpayments else None,
            accrued_interest=round(total_interest, 2),
            total_with_interest=round(total_principal + total_interest, 2),
            calculation_method=f"Phased simple interest at {rate*100:.1f}% — {len(underpayments)} periods",
            notes="; ".join(details),
        )

        self._estimates.append(estimate)
        return estimate

    def total_estimated_recovery(self) -> dict:
        """Calculate total estimated recovery across all claims."""
        total_principal = sum(e.principal for e in self._estimates)
        total_interest = sum(e.accrued_interest for e in self._estimates)
        total = sum(e.total_with_interest for e in self._estimates)

        return {
            "total_principal": round(total_principal, 2),
            "total_interest": round(total_interest, 2),
            "total_recovery": round(total, 2),
            "claims": len(self._estimates),
            "jurisdiction": self.jurisdiction,
            "interest_statute": INTEREST_RATES.get(self.jurisdiction, {}).get("statute", "N/A"),
        }

    def evaluate_settlement(self, offer_amount: float) -> dict:
        """Evaluate a settlement offer against estimated damages."""
        recovery = self.total_estimated_recovery()
        total = recovery["total_recovery"]
        ratio = (offer_amount / total * 100) if total > 0 else 0

        if ratio >= 80:
            recommendation = "FAVORABLE — offer is >= 80% of estimated recovery"
        elif ratio >= 60:
            recommendation = "REASONABLE — offer is 60-80% of estimated recovery, consider litigation costs"
        elif ratio >= 40:
            recommendation = "LOW — offer is 40-60% of estimated recovery, counter-offer recommended"
        else:
            recommendation = "REJECT — offer is < 40% of estimated recovery"

        return {
            "offer_amount": offer_amount,
            "estimated_recovery": total,
            "offer_percentage": round(ratio, 1),
            "recommendation": recommendation,
            "note": "This is a mathematical comparison only, not legal advice. "
                    "Litigation costs, probability of success, and time value should be factored in.",
        }

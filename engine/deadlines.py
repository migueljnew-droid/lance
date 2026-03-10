"""Deadline calculator and statute of limitations engine."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .models import (
    Case,
    Claim,
    ClaimType,
    Deadline,
    DeadlineStatus,
    DeadlineType,
    EscalationAction,
)


# ── Statute of Limitations Reference ──
# Jurisdiction -> Claim Type -> {years, discovery_rule, tolling_notes}

SOL_REFERENCE: dict[str, dict[str, dict]] = {
    "CA": {
        "breach_of_contract": {
            "written": 4,  # CCP § 337
            "oral": 2,  # CCP § 339
            "discovery_rule": True,
            "statute": "Cal. CCP § 337 (written), § 339 (oral)",
            "tolling": [
                "Discovery rule: SOL runs from date breach discovered or should have been discovered",
                "Fraudulent concealment tolls SOL until discovery",
                "Each royalty statement = separate breach (installment contract rule)",
                "Defendant's absence from state tolls SOL (CCP § 351)",
            ],
        },
        "fraud": {
            "years": 3,  # CCP § 338(d)
            "discovery_rule": True,
            "statute": "Cal. CCP § 338(d)",
            "tolling": [
                "SOL runs from discovery of facts constituting fraud",
                "Fiduciary relationship extends discovery period",
                "Fraudulent concealment doctrine applies",
            ],
        },
        "breach_of_fiduciary_duty": {
            "years": 4,  # CCP § 343
            "discovery_rule": True,
            "statute": "Cal. CCP § 343",
            "tolling": [
                "Discovery rule applies when fiduciary conceals breach",
                "Fiduciary's duty of disclosure extends discovery period",
            ],
        },
        "accounting": {
            "years": 4,  # CCP § 345
            "discovery_rule": True,
            "statute": "Cal. CCP § 345",
            "tolling": [
                "Right to accounting is equitable - flexible SOL",
                "Continuous duty to account may reset SOL",
            ],
        },
        "unfair_business_practices": {
            "years": 4,  # Bus. & Prof. Code § 17208
            "discovery_rule": False,
            "statute": "Cal. Bus. & Prof. Code § 17208",
            "tolling": [
                "UCL claims: 4 years from commission of unfair act",
                "No discovery rule - runs from date of act",
            ],
        },
        "unjust_enrichment": {
            "years": 4,
            "discovery_rule": True,
            "statute": "Cal. CCP § 343 (catch-all)",
            "tolling": [
                "Discovery rule applies",
            ],
        },
    },
    "FEDERAL": {
        "copyright_infringement": {
            "years": 3,  # 17 USC § 507(b)
            "discovery_rule": True,
            "statute": "28 U.S.C. § 507(b)",
            "tolling": [
                "Warner/Chappell v. Nealy (2024): No separate damages bar under discovery rule",
                "Once timely filed, damages reach back to full period of infringement",
                "Discovery rule: SOL runs from when infringement discovered or should have been",
            ],
        },
    },
}


class DeadlineEngine:
    """Manages deadlines, SOL calculations, and expiry alerts."""

    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.deadlines_file = self.case_dir / "deadlines.json"
        self._deadlines: list[Deadline] = []
        self._load()

    def _load(self) -> None:
        """Load deadlines from file."""
        if self.deadlines_file.exists():
            with open(self.deadlines_file) as f:
                data = json.load(f)
            self._deadlines = [Deadline(**d) for d in data.get("deadlines", [])]

    def save(self) -> None:
        """Save deadlines to file."""
        self.case_dir.mkdir(parents=True, exist_ok=True)
        data = {"deadlines": [json.loads(d.model_dump_json()) for d in self._deadlines]}
        with open(self.deadlines_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @property
    def deadlines(self) -> list[Deadline]:
        return self._deadlines

    def add_response_deadline(
        self,
        description: str,
        trigger_date: date,
        days: int = 30,
        counterparty: str = "",
        trigger_event: str = "",
        escalation_rule: str = "",
    ) -> Deadline:
        """Add a response deadline (e.g., 30 days to respond to demand)."""
        dl_id = f"DL-{len(self._deadlines) + 1:03d}"
        deadline = Deadline(
            id=dl_id,
            type=DeadlineType.RESPONSE,
            description=description,
            trigger_date=trigger_date,
            trigger_event=trigger_event,
            days=days,
            due_date=trigger_date + timedelta(days=days),
            on_expiry=EscalationAction(
                action="escalate",
                escalation_rule=escalation_rule,
                description=f"No response from {counterparty} after {days} days",
            ) if escalation_rule else None,
        )
        self._deadlines.append(deadline)
        self.save()
        return deadline

    def add_sol_deadline(
        self,
        claim: Claim,
        jurisdiction: str = "CA",
        contract_type: str = "written",
    ) -> Deadline:
        """Calculate and add a statute of limitations deadline for a claim."""
        sol_info = self._get_sol_info(claim.type.value, jurisdiction, contract_type)
        if sol_info is None:
            raise ValueError(f"No SOL reference for {claim.type.value} in {jurisdiction}")

        years = sol_info.get("years") or sol_info.get("written", sol_info.get("oral", 4))

        # Use discovery date if available and discovery rule applies, otherwise accrual date
        start_date = claim.accrual_date
        if sol_info.get("discovery_rule") and claim.discovery_date:
            start_date = claim.discovery_date

        if start_date is None:
            raise ValueError(f"Claim {claim.id} has no accrual_date or discovery_date")

        due_date = date(start_date.year + years, start_date.month, start_date.day)

        dl_id = f"DL-SOL-{len(self._deadlines) + 1:03d}"
        deadline = Deadline(
            id=dl_id,
            type=DeadlineType.SOL,
            description=f"SOL for {claim.type.value} ({jurisdiction} {years}-year)",
            claim_id=claim.id,
            trigger_date=start_date,
            days=int((due_date - start_date).days),
            due_date=due_date,
            alert_days_before=[365, 180, 90, 30, 14],
            status=DeadlineStatus.ACTIVE,
            on_expiry=EscalationAction(
                action="sol_expired",
                description=f"CRITICAL: Statute of limitations expired for {claim.type.value}",
            ),
            notes=(
                f"Statute: {sol_info.get('statute', 'N/A')}. "
                f"Discovery rule: {'Yes' if sol_info.get('discovery_rule') else 'No'}. "
                f"Tolling: {'; '.join(sol_info.get('tolling', []))}"
            ),
        )
        self._deadlines.append(deadline)
        self.save()
        return deadline

    def _get_sol_info(self, claim_type: str, jurisdiction: str, contract_type: str = "written") -> dict | None:
        """Look up SOL reference for a claim type and jurisdiction."""
        jur_data = SOL_REFERENCE.get(jurisdiction, {})
        sol_info = jur_data.get(claim_type)
        if sol_info and "written" in sol_info:
            sol_info = {**sol_info, "years": sol_info[contract_type]}
        return sol_info

    def get_sol_reference(self, claim_type: str, jurisdiction: str = "CA") -> dict | None:
        """Get the full SOL reference entry for a claim type."""
        return self._get_sol_info(claim_type, jurisdiction)

    def check_deadlines(self, as_of: date = None) -> dict:
        """Check all deadlines and return status report."""
        today = as_of or date.today()
        report = {
            "as_of": str(today),
            "expired": [],
            "urgent": [],       # <= 7 days
            "approaching": [],  # <= 30 days
            "active": [],
            "completed": [],
        }

        for dl in self._deadlines:
            if dl.status == DeadlineStatus.COMPLETED:
                report["completed"].append(self._deadline_summary(dl, today))
                continue

            remaining = (dl.due_date - today).days

            if remaining < 0:
                dl.status = DeadlineStatus.EXPIRED
                report["expired"].append(self._deadline_summary(dl, today))
            elif remaining <= 7:
                dl.status = DeadlineStatus.URGENT
                report["urgent"].append(self._deadline_summary(dl, today))
            elif remaining <= 30:
                dl.status = DeadlineStatus.APPROACHING
                report["approaching"].append(self._deadline_summary(dl, today))
            else:
                dl.status = DeadlineStatus.ACTIVE
                report["active"].append(self._deadline_summary(dl, today))

        self.save()
        return report

    def _deadline_summary(self, dl: Deadline, today: date) -> dict:
        remaining = (dl.due_date - today).days
        return {
            "id": dl.id,
            "type": dl.type.value,
            "description": dl.description,
            "due_date": str(dl.due_date),
            "days_remaining": remaining,
            "status": dl.status.value,
            "notes": dl.notes,
            "escalation": dl.on_expiry.action if dl.on_expiry else None,
        }

    def complete_deadline(self, deadline_id: str, notes: str = "") -> None:
        """Mark a deadline as completed."""
        for dl in self._deadlines:
            if dl.id == deadline_id:
                dl.status = DeadlineStatus.COMPLETED
                if notes:
                    dl.notes = (dl.notes or "") + f" | Completed: {notes}"
                self.save()
                return
        raise ValueError(f"Deadline {deadline_id} not found")

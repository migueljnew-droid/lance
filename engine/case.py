"""Case state machine and lifecycle management."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import yaml

from .models import Case, CaseState, Event


# ── State Machine Definition ──

STATE_TRANSITIONS: dict[CaseState, dict] = {
    CaseState.EVIDENCE_GATHERING: {
        "description": "Collecting and organizing evidence",
        "entry_criteria": [
            "Case file created",
            "At least one claim identified",
        ],
        "exit_criteria": [
            "Evidence dossier complete",
            "All documents hashed and manifested",
            "Discrepancy analysis run",
            "Estimated damages calculated",
        ],
        "allowed_transitions": [CaseState.DEMAND],
    },
    CaseState.DEMAND: {
        "description": "Formal demands sent to respondents",
        "entry_criteria": [
            "Evidence gathering exit criteria met",
        ],
        "exit_criteria": [
            "All demand letters sent (certified mail or equivalent)",
            "Tracking numbers recorded",
            "Response deadlines calculated and tracked",
        ],
        "allowed_transitions": [
            CaseState.NEGOTIATION,
            CaseState.REGULATORY_FILING,
            CaseState.LITIGATION,
        ],
    },
    CaseState.NEGOTIATION: {
        "description": "Active negotiation with respondents",
        "entry_criteria": [
            "At least one respondent has acknowledged or responded",
        ],
        "exit_criteria": [
            "Settlement reached OR negotiation declared failed",
        ],
        "allowed_transitions": [
            CaseState.RESOLUTION,
            CaseState.MEDIATION,
            CaseState.REGULATORY_FILING,
            CaseState.LITIGATION,
        ],
    },
    CaseState.REGULATORY_FILING: {
        "description": "Complaints filed with regulatory bodies",
        "entry_criteria": [
            "Demand sent and response deadline expired",
            "OR evidence of regulatory violation identified",
        ],
        "exit_criteria": [
            "All applicable complaints filed",
            "Filing confirmations received",
        ],
        "allowed_transitions": [
            CaseState.LITIGATION,
            CaseState.NEGOTIATION,
            CaseState.RESOLUTION,
        ],
    },
    CaseState.MEDIATION: {
        "description": "Third-party mediation",
        "entry_criteria": [
            "Mediator selected",
            "Both parties agreed to mediate",
        ],
        "exit_criteria": [
            "Mediation complete (settled or failed)",
        ],
        "allowed_transitions": [
            CaseState.RESOLUTION,
            CaseState.LITIGATION,
        ],
    },
    CaseState.LITIGATION: {
        "description": "Formal legal proceedings filed",
        "entry_criteria": [
            "Attorney retained OR pro se filing prepared",
            "All pre-litigation requirements met",
            "Statute of limitations verified as not expired",
        ],
        "exit_criteria": [
            "Judgment entered OR settlement reached",
        ],
        "allowed_transitions": [CaseState.RESOLUTION],
    },
    CaseState.RESOLUTION: {
        "description": "Dispute resolved",
        "entry_criteria": [
            "Settlement agreement signed OR judgment entered OR claims withdrawn",
        ],
        "exit_criteria": [
            "All terms of resolution documented",
            "Payment received (if applicable)",
            "Registrations corrected (if applicable)",
        ],
        "allowed_transitions": [CaseState.CLOSED],
    },
    CaseState.CLOSED: {
        "description": "Case archived",
        "entry_criteria": ["All resolution terms satisfied"],
        "exit_criteria": [],
        "allowed_transitions": [],
    },
}


class CaseManager:
    """Manages case lifecycle, state transitions, and event logging."""

    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.case_file = self.case_dir / "case.yaml"
        self.events_file = self.case_dir / "events.jsonl"
        self._case: Optional[Case] = None

    @property
    def case(self) -> Case:
        if self._case is None:
            self._case = self.load()
        return self._case

    def load(self) -> Case:
        """Load case from YAML file."""
        if not self.case_file.exists():
            raise FileNotFoundError(f"No case file at {self.case_file}")
        with open(self.case_file) as f:
            data = yaml.safe_load(f)
        case_data = data.get("case", data)
        self._case = Case(**case_data)
        return self._case

    def save(self) -> None:
        """Save case to YAML file."""
        self.case_dir.mkdir(parents=True, exist_ok=True)
        data = {"case": json.loads(self.case.model_dump_json())}
        with open(self.case_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def can_transition(self, target: CaseState) -> tuple[bool, list[str]]:
        """Check if transition to target state is allowed."""
        current = self.case.state
        state_def = STATE_TRANSITIONS.get(current)
        if state_def is None:
            return False, [f"Unknown current state: {current}"]

        errors = []
        if target not in state_def["allowed_transitions"]:
            errors.append(
                f"Transition from {current.value} to {target.value} is not allowed. "
                f"Allowed: {[s.value for s in state_def['allowed_transitions']]}"
            )

        return len(errors) == 0, errors

    def transition(self, target: CaseState, reason: str = "") -> Event:
        """Transition case to a new state."""
        can, errors = self.can_transition(target)
        if not can:
            raise ValueError(f"Cannot transition: {'; '.join(errors)}")

        old_state = self.case.state
        self.case.state = target
        self.case.updated = date.today()

        event = self.log_event(
            event_type="state_transition",
            actor="system",
            description=f"State: {old_state.value} -> {target.value}. {reason}".strip(),
            metadata={"from": old_state.value, "to": target.value, "reason": reason},
        )

        self.save()
        return event

    def log_event(self, event_type: str, actor: str, description: str, metadata: dict = None) -> Event:
        """Append an event to the event log."""
        event_count = 0
        if self.events_file.exists():
            with open(self.events_file) as f:
                event_count = sum(1 for _ in f)

        event = Event(
            id=f"EVT-{event_count + 1:04d}",
            timestamp=datetime.now(),
            type=event_type,
            actor=actor,
            description=description,
            metadata=metadata or {},
        )

        self.case_dir.mkdir(parents=True, exist_ok=True)
        with open(self.events_file, "a") as f:
            f.write(event.model_dump_json() + "\n")

        return event

    def get_events(self, event_type: str = None) -> list[Event]:
        """Read events from the log, optionally filtered by type."""
        if not self.events_file.exists():
            return []
        events = []
        with open(self.events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                evt = Event(**json.loads(line))
                if event_type is None or evt.type == event_type:
                    events.append(evt)
        return events

    def status_summary(self) -> dict:
        """Generate a status summary of the case."""
        state_def = STATE_TRANSITIONS.get(self.case.state, {})
        events = self.get_events()
        return {
            "case_id": self.case.id,
            "title": self.case.title,
            "state": self.case.state.value,
            "state_description": state_def.get("description", ""),
            "exit_criteria": state_def.get("exit_criteria", []),
            "allowed_transitions": [s.value for s in state_def.get("allowed_transitions", [])],
            "claims_count": len(self.case.claims),
            "respondents_count": len(self.case.respondents),
            "total_events": len(events),
            "last_event": events[-1].description if events else "None",
            "created": str(self.case.created),
            "updated": str(self.case.updated),
        }

    @classmethod
    def init_case(cls, case_dir: Path, case: Case) -> "CaseManager":
        """Initialize a new case directory and save the case file."""
        case_dir = Path(case_dir)
        for subdir in ["evidence/docs", "correspondence/outbound", "correspondence/inbound",
                        "audit_reports", "arguments", "handoff"]:
            (case_dir / subdir).mkdir(parents=True, exist_ok=True)

        mgr = cls(case_dir)
        mgr._case = case
        mgr.save()
        mgr.log_event(
            event_type="case_created",
            actor="claimant",
            description=f"Case initialized: {case.title}",
            metadata={"case_id": case.id, "type": case.type},
        )
        return mgr

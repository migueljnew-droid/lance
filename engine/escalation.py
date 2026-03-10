"""Rule-based escalation engine for legal disputes."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .communications import CommunicationTracker
from .deadlines import DeadlineEngine
from .models import DeadlineStatus, EscalationRule


# ── Default Escalation Rules ──

DEFAULT_RULES: list[dict] = [
    {
        "id": "ESC-001",
        "name": "Follow-up on ignored demand",
        "trigger": "no_response",
        "days": 14,
        "action": "draft_follow_up",
        "action_description": "Draft a follow-up letter referencing original demand and noting lack of response",
        "priority": 2,
    },
    {
        "id": "ESC-002",
        "name": "Second follow-up warning",
        "trigger": "no_response",
        "days": 30,
        "action": "draft_second_follow_up",
        "action_description": "Draft a firm follow-up citing contractual obligations and noting potential regulatory action",
        "priority": 3,
    },
    {
        "id": "ESC-003",
        "name": "Regulatory complaint trigger",
        "trigger": "no_response",
        "days": 60,
        "action": "draft_regulatory_complaint",
        "action_description": "Draft complaint to California Attorney General (Consumer Protection) and/or Copyright Office",
        "priority": 4,
    },
    {
        "id": "ESC-004",
        "name": "Attorney retention trigger",
        "trigger": "no_response",
        "days": 90,
        "action": "recommend_attorney",
        "action_description": "SOL clock is running. Recommend retaining entertainment attorney (contingency basis for $30K+ cases)",
        "priority": 5,
    },
    {
        "id": "ESC-005",
        "name": "Settlement evaluation",
        "trigger": "settlement_offered",
        "action": "evaluate_settlement",
        "action_description": "Compare settlement offer against estimated damages with interest. Flag if offer < 70% of estimated recovery.",
        "priority": 3,
    },
    {
        "id": "ESC-006",
        "name": "SOL approaching - 90 day warning",
        "trigger": "sol_approaching",
        "days": 90,
        "action": "sol_warning",
        "action_description": "URGENT: Statute of limitations expires in 90 days. Must file or settle before expiry.",
        "priority": 5,
    },
    {
        "id": "ESC-007",
        "name": "Evidence integrity check",
        "trigger": "periodic",
        "days": 30,
        "action": "verify_evidence",
        "action_description": "Run SHA-256 integrity check on all evidence files",
        "priority": 1,
    },
]


class EscalationEngine:
    """Evaluates case state against rules and recommends actions."""

    def __init__(self, case_dir: Path, rules: list[EscalationRule] = None):
        self.case_dir = Path(case_dir)
        self.rules_file = self.case_dir / "escalation_rules.json"

        if rules:
            self._rules = rules
        else:
            self._rules = self._load_rules()

    def _load_rules(self) -> list[EscalationRule]:
        """Load rules from file or use defaults."""
        if self.rules_file.exists():
            with open(self.rules_file) as f:
                data = json.load(f)
            return [EscalationRule(**r) for r in data.get("rules", [])]
        return [EscalationRule(**r) for r in DEFAULT_RULES]

    def save_rules(self) -> None:
        """Save current rules to file."""
        self.case_dir.mkdir(parents=True, exist_ok=True)
        data = {"rules": [json.loads(r.model_dump_json()) for r in self._rules]}
        with open(self.rules_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_rule(self, rule: EscalationRule) -> None:
        """Add a custom escalation rule."""
        self._rules.append(rule)
        self.save_rules()

    def evaluate(
        self,
        comms_tracker: CommunicationTracker,
        deadline_engine: DeadlineEngine,
        as_of: date = None,
    ) -> list[dict]:
        """Evaluate all rules against current case state. Returns triggered actions."""
        today = as_of or date.today()
        triggered = []

        # Check no-response rules
        awaiting = comms_tracker.get_awaiting_response(today)
        for comm in awaiting:
            if not comm["overdue"]:
                continue
            days_overdue = comm["days_overdue"]
            for rule in self._rules:
                if rule.trigger == "no_response" and rule.days and days_overdue >= rule.days:
                    triggered.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "trigger": rule.trigger,
                        "action": rule.action,
                        "description": rule.action_description,
                        "priority": rule.priority,
                        "context": {
                            "communication_id": comm["id"],
                            "counterparty": comm["counterparty"],
                            "days_overdue": days_overdue,
                            "original_summary": comm["summary"],
                        },
                    })

        # Check SOL approaching rules
        deadline_report = deadline_engine.check_deadlines(today)
        for dl in deadline_report.get("urgent", []) + deadline_report.get("approaching", []):
            if dl["type"] != "statute_of_limitations":
                continue
            for rule in self._rules:
                if rule.trigger == "sol_approaching" and rule.days:
                    if dl["days_remaining"] <= rule.days:
                        triggered.append({
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "trigger": rule.trigger,
                            "action": rule.action,
                            "description": rule.action_description,
                            "priority": rule.priority,
                            "context": {
                                "deadline_id": dl["id"],
                                "description": dl["description"],
                                "days_remaining": dl["days_remaining"],
                                "due_date": dl["due_date"],
                            },
                        })

        # Check for expired deadlines
        for dl in deadline_report.get("expired", []):
            if dl["type"] == "statute_of_limitations":
                triggered.append({
                    "rule_id": "SYSTEM",
                    "rule_name": "SOL EXPIRED",
                    "trigger": "sol_expired",
                    "action": "CRITICAL_ALERT",
                    "description": f"STATUTE OF LIMITATIONS HAS EXPIRED: {dl['description']}",
                    "priority": 10,
                    "context": dl,
                })

        # Sort by priority (highest first)
        triggered.sort(key=lambda x: x["priority"], reverse=True)

        # Deduplicate by rule_id + counterparty (keep highest priority)
        seen = set()
        deduped = []
        for t in triggered:
            key = (t["rule_id"], t["context"].get("counterparty", ""))
            if key not in seen:
                seen.add(key)
                deduped.append(t)

        return deduped

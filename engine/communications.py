"""Communication tracker for all case correspondence."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .models import CommMethod, CommStatus, Communication


class CommunicationTracker:
    """Tracks all outbound and inbound communications."""

    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.comms_file = self.case_dir / "communications.json"
        self._communications: list[Communication] = []
        self._load()

    def _load(self) -> None:
        if self.comms_file.exists():
            with open(self.comms_file) as f:
                data = json.load(f)
            self._communications = [Communication(**c) for c in data.get("communications", [])]

    def save(self) -> None:
        self.case_dir.mkdir(parents=True, exist_ok=True)
        data = {"communications": [json.loads(c.model_dump_json()) for c in self._communications]}
        with open(self.comms_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    @property
    def communications(self) -> list[Communication]:
        return self._communications

    def log_outbound(
        self,
        counterparty_id: str,
        method: CommMethod,
        summary: str,
        subject: str = "",
        documents: list[str] = None,
        tracking_number: str = "",
        response_days: int = 30,
        sent_date: date = None,
    ) -> Communication:
        """Log an outbound communication."""
        comm_id = f"COM-{len(self._communications) + 1:03d}"
        send_date = sent_date or date.today()

        comm = Communication(
            id=comm_id,
            direction="outbound",
            date=send_date,
            counterparty_id=counterparty_id,
            method=method,
            status=CommStatus.SENT,
            subject=subject,
            summary=summary,
            documents=documents or [],
            tracking_number=tracking_number,
            response_deadline=send_date + timedelta(days=response_days),
        )

        self._communications.append(comm)
        self.save()
        return comm

    def log_inbound(
        self,
        counterparty_id: str,
        method: CommMethod,
        summary: str,
        subject: str = "",
        documents: list[str] = None,
        received_date: date = None,
    ) -> Communication:
        """Log an inbound communication."""
        comm_id = f"COM-{len(self._communications) + 1:03d}"

        comm = Communication(
            id=comm_id,
            direction="inbound",
            date=received_date or date.today(),
            counterparty_id=counterparty_id,
            method=method,
            status=CommStatus.RESPONDED,
            subject=subject,
            summary=summary,
            documents=documents or [],
        )

        self._communications.append(comm)
        self.save()
        return comm

    def update_status(self, comm_id: str, status: CommStatus, notes: str = "") -> None:
        """Update the status of a communication."""
        for comm in self._communications:
            if comm.id == comm_id:
                comm.status = status
                if notes:
                    comm.notes = (comm.notes or "") + f" | {notes}"
                self.save()
                return
        raise ValueError(f"Communication {comm_id} not found")

    def mark_responded(self, comm_id: str, response_date: date = None) -> None:
        """Mark an outbound communication as having received a response."""
        for comm in self._communications:
            if comm.id == comm_id:
                comm.status = CommStatus.RESPONDED
                comm.response_received = response_date or date.today()
                self.save()
                return
        raise ValueError(f"Communication {comm_id} not found")

    def get_awaiting_response(self, as_of: date = None) -> list[dict]:
        """Get all outbound communications still awaiting response."""
        today = as_of or date.today()
        awaiting = []
        for comm in self._communications:
            if (comm.direction == "outbound"
                    and comm.status in (CommStatus.SENT, CommStatus.DELIVERED)
                    and comm.response_deadline):
                days_waiting = (today - comm.date).days
                overdue = today > comm.response_deadline
                awaiting.append({
                    "id": comm.id,
                    "counterparty": comm.counterparty_id,
                    "sent_date": str(comm.date),
                    "method": comm.method.value,
                    "summary": comm.summary,
                    "response_deadline": str(comm.response_deadline),
                    "days_waiting": days_waiting,
                    "overdue": overdue,
                    "days_overdue": (today - comm.response_deadline).days if overdue else 0,
                })
        return awaiting

    def get_communications_for(self, counterparty_id: str) -> list[Communication]:
        """Get all communications with a specific counterparty."""
        return [c for c in self._communications if c.counterparty_id == counterparty_id]

    def summary(self) -> dict:
        """Generate communication summary."""
        outbound = [c for c in self._communications if c.direction == "outbound"]
        inbound = [c for c in self._communications if c.direction == "inbound"]
        awaiting = self.get_awaiting_response()
        return {
            "total": len(self._communications),
            "outbound": len(outbound),
            "inbound": len(inbound),
            "awaiting_response": len(awaiting),
            "overdue": sum(1 for a in awaiting if a["overdue"]),
        }

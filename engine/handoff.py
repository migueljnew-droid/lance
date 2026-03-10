"""Attorney handoff package generator."""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime
from pathlib import Path

from .case import CaseManager
from .communications import CommunicationTracker
from .damages import DamagesCalculator
from .deadlines import DeadlineEngine
from .evidence import EvidenceManager


class HandoffGenerator:
    """Generates a complete attorney handoff package."""

    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)

    def generate(self, output_dir: Path = None) -> Path:
        """Generate a complete attorney handoff package.

        Creates a directory with:
        - CASE_SUMMARY.md — narrative summary
        - case_data.json — structured case data
        - evidence/ — copies of all evidence files
        - correspondence/ — all communication records
        - arguments/ — all built legal arguments
        - deadlines.json — all active deadlines
        - damages_estimate.json — damages calculations
        - timeline.md — chronological timeline of all events
        """
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.case_dir / "handoff" / f"package_{timestamp}"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load all components
        case_mgr = CaseManager(self.case_dir)
        case = case_mgr.case
        events = case_mgr.get_events()

        evidence_mgr = EvidenceManager(self.case_dir)
        comms = CommunicationTracker(self.case_dir)
        deadlines = DeadlineEngine(self.case_dir)

        # 1. Case summary markdown
        summary = self._build_summary(case, events, evidence_mgr, comms, deadlines)
        (output_dir / "CASE_SUMMARY.md").write_text(summary)

        # 2. Structured case data
        case_data = json.loads(case.model_dump_json())
        with open(output_dir / "case_data.json", "w") as f:
            json.dump(case_data, f, indent=2, default=str)

        # 3. Copy evidence files
        ev_dir = output_dir / "evidence"
        ev_dir.mkdir(exist_ok=True)
        docs_src = self.case_dir / "evidence" / "docs"
        if docs_src.exists():
            for doc in docs_src.iterdir():
                if doc.is_file():
                    shutil.copy2(doc, ev_dir / doc.name)

        # Copy evidence manifest
        manifest_src = self.case_dir / "evidence" / "manifest.json"
        if manifest_src.exists():
            shutil.copy2(manifest_src, ev_dir / "manifest.json")

        # 4. Communications
        comms_src = self.case_dir / "communications.json"
        if comms_src.exists():
            shutil.copy2(comms_src, output_dir / "communications.json")

        # 5. Arguments
        args_src = self.case_dir / "arguments"
        if args_src.exists():
            args_dest = output_dir / "arguments"
            args_dest.mkdir(exist_ok=True)
            for f in args_src.glob("*.json"):
                shutil.copy2(f, args_dest / f.name)

        # 6. Deadlines
        dl_src = self.case_dir / "deadlines.json"
        if dl_src.exists():
            shutil.copy2(dl_src, output_dir / "deadlines.json")

        # 7. Timeline
        timeline = self._build_timeline(events, comms)
        (output_dir / "TIMELINE.md").write_text(timeline)

        # 8. Generate index
        index = self._build_index(output_dir)
        (output_dir / "INDEX.md").write_text(index)

        return output_dir

    def _build_summary(self, case, events, evidence_mgr, comms, deadlines) -> str:
        """Build narrative case summary."""
        lines = [
            f"# CASE SUMMARY — {case.title}",
            f"**Case ID:** {case.id}",
            f"**Generated:** {date.today().strftime('%B %d, %Y')}",
            f"**Current State:** {case.state.value}",
            "",
            "---",
            "",
            "## Parties",
            "",
            f"### Claimant",
            f"- **Name:** {case.claimant.name}",
        ]
        if case.claimant.aka:
            lines.append(f"- **Also known as:** {', '.join(case.claimant.aka)}")
        if case.claimant.address:
            lines.append(f"- **Address:** {case.claimant.address}")
        if case.claimant.email:
            lines.append(f"- **Email:** {case.claimant.email}")

        lines.extend(["", "### Respondents", ""])
        for resp in case.respondents:
            lines.append(f"**{resp.name}** ({resp.role})")
            if resp.entity:
                lines.append(f"- Entity: {resp.entity}")
            if resp.address:
                lines.append(f"- Address: {resp.address}")
            if resp.email:
                lines.append(f"- Email: {resp.email}")
            if resp.counsel:
                lines.append(f"- Counsel: {resp.counsel}")
            lines.append("")

        lines.extend(["## Jurisdiction", ""])
        lines.append(f"- **Primary State:** {case.jurisdiction.primary_state}")
        lines.append(f"- **Federal Claims:** {'Yes' if case.jurisdiction.federal else 'No'}")
        lines.append(f"- **Governing Law:** {case.jurisdiction.governing_law}")
        if case.jurisdiction.venue:
            lines.append(f"- **Venue:** {case.jurisdiction.venue}")

        if case.contract:
            lines.extend(["", "## Underlying Contract", ""])
            lines.append(f"- **Type:** {case.contract.type}")
            if case.contract.date_signed:
                lines.append(f"- **Date Signed:** {case.contract.date_signed}")
            for term in case.contract.key_terms:
                lines.append(f"- {term}")
            if case.contract.audit_clause:
                lines.append(f"- **Audit Clause:** {case.contract.audit_clause}")

        lines.extend(["", "## Claims", ""])
        for claim in case.claims:
            lines.append(f"### {claim.id}: {claim.type.value}")
            lines.append(f"- **Description:** {claim.description}")
            if claim.statute:
                lines.append(f"- **Statute:** {claim.statute}")
            if claim.estimated_damages:
                lines.append(f"- **Estimated Damages:** ${claim.estimated_damages:,.2f}")
            if claim.discovery_date:
                lines.append(f"- **Discovery Date:** {claim.discovery_date}")
            if claim.notes:
                lines.append(f"- **Notes:** {claim.notes}")
            lines.append("")

        ev_summary = evidence_mgr.summary()
        lines.extend([
            "## Evidence Summary",
            "",
            f"- **Total Items:** {ev_summary['total_items']}",
        ])
        for etype, count in ev_summary.get("by_type", {}).items():
            lines.append(f"- {etype}: {count}")

        comm_summary = comms.summary()
        lines.extend([
            "", "## Communications Summary", "",
            f"- **Total:** {comm_summary['total']}",
            f"- **Outbound:** {comm_summary['outbound']}",
            f"- **Inbound:** {comm_summary['inbound']}",
            f"- **Awaiting Response:** {comm_summary['awaiting_response']}",
            f"- **Overdue:** {comm_summary['overdue']}",
        ])

        dl_report = deadlines.check_deadlines()
        lines.extend([
            "", "## Active Deadlines", "",
        ])
        for category in ["expired", "urgent", "approaching", "active"]:
            for dl in dl_report.get(category, []):
                marker = "EXPIRED" if category == "expired" else f"{dl['days_remaining']} days"
                lines.append(f"- **[{marker}]** {dl['description']} (due {dl['due_date']})")

        lines.extend(["", "---", "",
                       "*Generated by LANCE — Legal Action & Negotiation Command Engine*"])

        return "\n".join(lines)

    def _build_timeline(self, events, comms) -> str:
        """Build chronological timeline from events and communications."""
        lines = [
            "# CASE TIMELINE",
            f"**Generated:** {date.today().strftime('%B %d, %Y')}",
            "",
            "---",
            "",
        ]

        # Merge events and communications into timeline
        timeline_items = []
        for evt in events:
            timeline_items.append({
                "date": evt.timestamp.strftime("%Y-%m-%d"),
                "time": evt.timestamp.strftime("%I:%M %p"),
                "type": evt.type,
                "description": evt.description,
                "source": "event_log",
            })

        for comm in comms.communications:
            timeline_items.append({
                "date": str(comm.date),
                "time": "N/A",
                "type": f"communication_{comm.direction}",
                "description": f"[{comm.method.value}] {comm.summary}",
                "source": "communications",
            })

        timeline_items.sort(key=lambda x: x["date"])

        current_date = None
        for item in timeline_items:
            if item["date"] != current_date:
                current_date = item["date"]
                lines.append(f"## {current_date}")
                lines.append("")

            lines.append(f"- **{item['type']}:** {item['description']}")

        lines.extend(["", "---", "*Generated by LANCE*"])
        return "\n".join(lines)

    def _build_index(self, output_dir: Path) -> str:
        """Build index of all files in the handoff package."""
        lines = [
            "# ATTORNEY HANDOFF PACKAGE — INDEX",
            f"**Generated:** {date.today().strftime('%B %d, %Y')}",
            "",
            "---",
            "",
            "| File | Description |",
            "|------|-------------|",
            "| CASE_SUMMARY.md | Narrative case summary with all parties, claims, evidence |",
            "| case_data.json | Machine-readable case data (Pydantic model export) |",
            "| TIMELINE.md | Chronological timeline of all case events |",
            "| communications.json | All correspondence records |",
            "| deadlines.json | Active deadlines and SOL tracking |",
            "| evidence/ | Evidence files with manifest |",
            "| arguments/ | Structured legal arguments |",
            "",
            "---",
            "*Generated by LANCE — Legal Action & Negotiation Command Engine*",
        ]
        return "\n".join(lines)

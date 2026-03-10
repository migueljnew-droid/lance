"""Bridge to external audit agents (royalty auditors, financial analyzers)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path


class AuditBridge:
    """Integrates external audit tools with LANCE case management."""

    def __init__(self, case_dir: Path, audit_agent_dir: Path = None):
        self.case_dir = Path(case_dir)
        self.audit_agent_dir = Path(audit_agent_dir) if audit_agent_dir else None
        self.reports_dir = self.case_dir / "audit_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_audit(
        self,
        mlc_files: list[str] = None,
        ascap_files: list[str] = None,
        warner_files: list[str] = None,
        data_dir: str = None,
        python_path: str = None,
    ) -> dict:
        """Run the audit agent and capture results.

        Args:
            mlc_files: Paths to MLC TSV files.
            ascap_files: Paths to ASCAP CSV files.
            warner_files: Paths to Warner CSV files.
            data_dir: Directory to scan for all data files.
            python_path: Path to Python interpreter (default: sys.executable).
        """
        if self.audit_agent_dir is None:
            raise ValueError("No audit_agent_dir configured. Set it in the AuditBridge constructor.")

        audit_script = self.audit_agent_dir / "audit.py"
        if not audit_script.exists():
            raise FileNotFoundError(f"Audit script not found: {audit_script}")

        python = python_path or sys.executable
        cmd = [python, str(audit_script), "--output", str(self.reports_dir)]

        if data_dir:
            cmd.extend(["--all", data_dir])
        else:
            if mlc_files:
                cmd.extend(["--mlc"] + mlc_files)
            if ascap_files:
                cmd.extend(["--ascap"] + ascap_files)
            if warner_files:
                cmd.extend(["--warner"] + warner_files)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        audit_result = {
            "date": str(date.today()),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

        # Try to find the JSON report
        json_reports = sorted(self.reports_dir.glob("AUDIT_REPORT_*.json"), reverse=True)
        if json_reports:
            with open(json_reports[0]) as f:
                audit_result["report"] = json.load(f)
            audit_result["report_file"] = str(json_reports[0])

        return audit_result

    def import_findings(self, report_path: str) -> list[dict]:
        """Import findings from an existing audit report JSON file."""
        with open(report_path) as f:
            report = json.load(f)

        findings = report.get("all_findings", [])
        return findings

    def findings_to_evidence(self, findings: list[dict]) -> list[dict]:
        """Convert audit findings into evidence-ready summaries."""
        evidence_items = []
        for finding in findings:
            if finding.get("severity") in ("CRITICAL", "WARNING"):
                evidence_items.append({
                    "title": f"Audit Finding: {finding.get('category', 'Unknown')}",
                    "description": finding.get("message", ""),
                    "severity": finding.get("severity"),
                    "data": finding.get("data", {}),
                    "suggested_claim": self._map_finding_to_claim(finding),
                })
        return evidence_items

    @staticmethod
    def _map_finding_to_claim(finding: dict) -> str:
        """Map an audit finding category to a claim type."""
        category = finding.get("category", "").lower()
        mapping = {
            "share": "breach_of_contract",
            "revenue": "breach_of_contract",
            "registration": "unfair_business_practices",
            "unauthorized": "breach_of_fiduciary_duty",
            "missing": "accounting",
        }
        for key, claim in mapping.items():
            if key in category:
                return claim
        return "breach_of_contract"

    def list_reports(self) -> list[dict]:
        """List all audit reports in the case."""
        reports = []
        for f in sorted(self.reports_dir.glob("AUDIT_REPORT_*"), reverse=True):
            reports.append({
                "filename": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "modified": str(date.fromtimestamp(f.stat().st_mtime)),
            })
        return reports

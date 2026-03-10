"""Legal argument builder — structures arguments from evidence + law."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class ArgumentBuilder:
    """Builds structured legal arguments from evidence and legal citations."""

    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.arguments_dir = self.case_dir / "arguments"
        self.arguments_dir.mkdir(parents=True, exist_ok=True)

    def build_argument(
        self,
        claim_id: str,
        claim_type: str,
        elements: list[dict],
        evidence_ids: list[str],
        statutes: list[str],
        case_citations: list[str],
        damages_estimate: float = None,
        notes: str = "",
    ) -> dict:
        """Build a structured legal argument.

        Args:
            claim_id: The claim this argument supports.
            claim_type: Type of claim (e.g., 'breach_of_contract').
            elements: List of legal elements with proof.
                Each: {"element": str, "proof": str, "evidence": [str], "strength": str}
            evidence_ids: Evidence item IDs supporting this argument.
            statutes: Applicable statute citations.
            case_citations: Supporting case law citations.
            damages_estimate: Estimated damages amount.
            notes: Additional notes.
        """
        argument = {
            "id": f"ARG-{claim_id}",
            "claim_id": claim_id,
            "claim_type": claim_type,
            "date_built": str(date.today()),
            "legal_standard": self._get_legal_standard(claim_type),
            "elements": elements,
            "evidence_ids": evidence_ids,
            "statutes": statutes,
            "case_citations": case_citations,
            "damages_estimate": damages_estimate,
            "strength_assessment": self._assess_strength(elements),
            "notes": notes,
        }

        # Save argument
        arg_file = self.arguments_dir / f"{claim_id}_argument.json"
        with open(arg_file, "w") as f:
            json.dump(argument, f, indent=2)

        return argument

    def _get_legal_standard(self, claim_type: str) -> dict:
        """Get the legal standard (burden of proof, required elements) for a claim type."""
        standards = {
            "breach_of_contract": {
                "burden": "Preponderance of the evidence",
                "required_elements": [
                    "Existence of a valid contract",
                    "Plaintiff's performance or excuse for nonperformance",
                    "Defendant's breach",
                    "Resulting damages",
                ],
                "source": "CACI 303 (California Civil Jury Instructions)",
            },
            "breach_of_fiduciary_duty": {
                "burden": "Preponderance of the evidence",
                "required_elements": [
                    "Existence of fiduciary relationship",
                    "Breach of fiduciary duty",
                    "Resulting damages",
                ],
                "source": "CACI 4100",
            },
            "fraud": {
                "burden": "Clear and convincing evidence",
                "required_elements": [
                    "Misrepresentation (false representation, concealment, or nondisclosure)",
                    "Knowledge of falsity (scienter)",
                    "Intent to defraud (induce reliance)",
                    "Justifiable reliance",
                    "Resulting damages",
                ],
                "source": "CACI 1900; Lazar v. Superior Court (1996) 12 Cal.4th 631",
            },
            "accounting": {
                "burden": "Preponderance of the evidence",
                "required_elements": [
                    "Fiduciary relationship or other relationship requiring accounting",
                    "Some balance is due from defendant to plaintiff",
                    "Defendant has refused to render an accounting",
                ],
                "source": "Equitable remedy; Teselle v. McLoughlin (2009) 173 Cal.App.4th 156",
            },
            "unfair_business_practices": {
                "burden": "Preponderance of the evidence",
                "required_elements": [
                    "Defendant engaged in unlawful, unfair, or fraudulent business act/practice",
                    "Plaintiff suffered injury in fact",
                    "Plaintiff lost money or property as a result",
                ],
                "source": "Cal. Bus. & Prof. Code § 17200; CACI 4500",
            },
            "copyright_infringement": {
                "burden": "Preponderance of the evidence",
                "required_elements": [
                    "Ownership of valid copyright",
                    "Defendant copied constituent elements of the work that are original",
                ],
                "source": "Feist Publications v. Rural Telephone (1991) 499 U.S. 340",
            },
        }
        return standards.get(claim_type, {
            "burden": "Preponderance of the evidence",
            "required_elements": ["Consult applicable law"],
            "source": "Unknown claim type",
        })

    @staticmethod
    def _assess_strength(elements: list[dict]) -> dict:
        """Assess overall argument strength from element strengths."""
        if not elements:
            return {"overall": "INSUFFICIENT", "met": 0, "total": 0, "percentage": 0}

        strength_values = {"strong": 3, "moderate": 2, "weak": 1, "missing": 0}
        scores = [strength_values.get(e.get("strength", "missing"), 0) for e in elements]
        avg = sum(scores) / len(scores)
        met = sum(1 for s in scores if s >= 2)

        if avg >= 2.5 and met == len(elements):
            overall = "STRONG"
        elif avg >= 1.5 and met >= len(elements) * 0.75:
            overall = "MODERATE"
        elif avg >= 1.0:
            overall = "WEAK"
        else:
            overall = "INSUFFICIENT"

        return {
            "overall": overall,
            "met": met,
            "total": len(elements),
            "percentage": round(met / len(elements) * 100, 1),
            "average_score": round(avg, 2),
        }

    def list_arguments(self) -> list[dict]:
        """List all built arguments."""
        args = []
        for f in sorted(self.arguments_dir.glob("*_argument.json")):
            with open(f) as fh:
                arg = json.load(fh)
            args.append({
                "id": arg["id"],
                "claim_type": arg["claim_type"],
                "strength": arg["strength_assessment"]["overall"],
                "elements_met": f"{arg['strength_assessment']['met']}/{arg['strength_assessment']['total']}",
            })
        return args

"""Evidence management with SHA-256 integrity and chain of custody."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

from .models import CustodyEntry, EvidenceItem, EvidenceManifest, EvidenceType


class EvidenceManager:
    """Manages evidence collection, hashing, and chain of custody."""

    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.evidence_dir = self.case_dir / "evidence"
        self.docs_dir = self.evidence_dir / "docs"
        self.manifest_file = self.evidence_dir / "manifest.json"
        self._manifest: EvidenceManifest | None = None

    @property
    def manifest(self) -> EvidenceManifest:
        if self._manifest is None:
            self._manifest = self._load_manifest()
        return self._manifest

    def _load_manifest(self) -> EvidenceManifest:
        """Load or create evidence manifest."""
        if self.manifest_file.exists():
            with open(self.manifest_file) as f:
                data = json.load(f)
            return EvidenceManifest(**data)
        return EvidenceManifest(case_id="unknown")

    def save(self) -> None:
        """Save manifest to file."""
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_file, "w") as f:
            json.dump(json.loads(self.manifest.model_dump_json()), f, indent=2, default=str)

    def add_evidence(
        self,
        file_path: Path,
        title: str,
        evidence_type: EvidenceType,
        description: str = "",
        source: str = "",
        custodian: str = "",
        date_created: date = None,
        claim_ids: list[str] = None,
        copy_file: bool = True,
    ) -> EvidenceItem:
        """Add a file as evidence. Computes hash and creates custody entry."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")

        # Compute hash
        sha256 = self._hash_file(file_path)

        # Check for duplicate
        for item in self.manifest.evidence:
            if item.sha256 == sha256:
                raise ValueError(
                    f"Duplicate evidence: {file_path.name} has same hash as {item.id} ({item.title})"
                )

        # Generate ID
        ev_id = f"EV-{len(self.manifest.evidence) + 1:03d}"

        # Copy file to evidence directory
        if copy_file:
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            dest = self.docs_dir / file_path.name
            if dest.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                dest = self.docs_dir / f"{stem}_{ev_id}{suffix}"
            shutil.copy2(file_path, dest)
            stored_filename = dest.name
        else:
            stored_filename = file_path.name

        item = EvidenceItem(
            id=ev_id,
            title=title,
            filename=stored_filename,
            type=evidence_type,
            date_created=date_created,
            date_obtained=date.today(),
            sha256=sha256,
            size_bytes=file_path.stat().st_size,
            source=source,
            custodian=custodian,
            description=description,
            relevance=claim_ids or [],
            chain_of_custody=[
                CustodyEntry(
                    date=date.today(),
                    holder=custodian or "case_manager",
                    action="added_to_case_file",
                )
            ],
        )

        self.manifest.evidence.append(item)
        self.save()
        return item

    def verify_integrity(self) -> list[dict]:
        """Verify SHA-256 hashes of all evidence files."""
        results = []
        for item in self.manifest.evidence:
            file_path = self.docs_dir / item.filename
            if not file_path.exists():
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "status": "MISSING",
                    "detail": f"File not found: {file_path}",
                })
                continue

            current_hash = self._hash_file(file_path)
            if current_hash == item.sha256:
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "status": "VERIFIED",
                    "detail": f"SHA-256 matches: {current_hash[:16]}...",
                })
            else:
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "status": "TAMPERED",
                    "detail": f"Hash mismatch! Expected {item.sha256[:16]}..., got {current_hash[:16]}...",
                })

        return results

    def add_custody_entry(self, evidence_id: str, holder: str, action: str, notes: str = "") -> None:
        """Add a chain of custody entry to an evidence item."""
        for item in self.manifest.evidence:
            if item.id == evidence_id:
                item.chain_of_custody.append(
                    CustodyEntry(
                        date=date.today(),
                        holder=holder,
                        action=action,
                        notes=notes or None,
                    )
                )
                self.save()
                return
        raise ValueError(f"Evidence {evidence_id} not found")

    def get_evidence(self, evidence_id: str) -> EvidenceItem | None:
        """Get an evidence item by ID."""
        for item in self.manifest.evidence:
            if item.id == evidence_id:
                return item
        return None

    def get_evidence_for_claim(self, claim_id: str) -> list[EvidenceItem]:
        """Get all evidence items linked to a specific claim."""
        return [item for item in self.manifest.evidence if claim_id in item.relevance]

    def summary(self) -> dict:
        """Generate evidence summary."""
        by_type = {}
        for item in self.manifest.evidence:
            by_type.setdefault(item.type.value, []).append(item.id)
        return {
            "total_items": len(self.manifest.evidence),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "total_size_bytes": sum(i.size_bytes or 0 for i in self.manifest.evidence),
        }

    @staticmethod
    def _hash_file(file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

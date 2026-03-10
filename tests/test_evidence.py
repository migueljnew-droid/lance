"""Tests for evidence management."""

import pytest
import tempfile
from pathlib import Path

from engine.evidence import EvidenceManager, EvidenceType


@pytest.fixture
def temp_case_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_case_dir):
    f = temp_case_dir / "test_contract.pdf"
    f.write_bytes(b"fake pdf content for testing")
    return f


class TestEvidenceManager:
    def test_add_evidence(self, temp_case_dir, sample_file):
        mgr = EvidenceManager(temp_case_dir)
        mgr.manifest.case_id = "TEST-001"
        item = mgr.add_evidence(
            file_path=sample_file,
            title="Test Contract",
            evidence_type=EvidenceType.CONTRACT,
            description="A test contract",
            custodian="Tester",
        )
        assert item.id == "EV-001"
        assert item.sha256 is not None
        assert len(item.sha256) == 64
        assert item.chain_of_custody[0].action == "added_to_case_file"

    def test_verify_integrity_pass(self, temp_case_dir, sample_file):
        mgr = EvidenceManager(temp_case_dir)
        mgr.manifest.case_id = "TEST-001"
        mgr.add_evidence(sample_file, "Test", EvidenceType.CONTRACT)
        results = mgr.verify_integrity()
        assert results[0]["status"] == "VERIFIED"

    def test_verify_integrity_tampered(self, temp_case_dir, sample_file):
        mgr = EvidenceManager(temp_case_dir)
        mgr.manifest.case_id = "TEST-001"
        item = mgr.add_evidence(sample_file, "Test", EvidenceType.CONTRACT)
        # Tamper with the file
        stored = temp_case_dir / "evidence" / "docs" / item.filename
        stored.write_bytes(b"tampered content")
        results = mgr.verify_integrity()
        assert results[0]["status"] == "TAMPERED"

    def test_duplicate_detection(self, temp_case_dir, sample_file):
        mgr = EvidenceManager(temp_case_dir)
        mgr.manifest.case_id = "TEST-001"
        mgr.add_evidence(sample_file, "First", EvidenceType.CONTRACT)
        with pytest.raises(ValueError, match="Duplicate"):
            mgr.add_evidence(sample_file, "Second", EvidenceType.CONTRACT)

    def test_custody_chain(self, temp_case_dir, sample_file):
        mgr = EvidenceManager(temp_case_dir)
        mgr.manifest.case_id = "TEST-001"
        item = mgr.add_evidence(sample_file, "Test", EvidenceType.CONTRACT)
        mgr.add_custody_entry(item.id, "Attorney", "delivered_to_counsel")
        updated = mgr.get_evidence(item.id)
        assert len(updated.chain_of_custody) == 2
        assert updated.chain_of_custody[1].holder == "Attorney"

    def test_evidence_summary(self, temp_case_dir, sample_file):
        mgr = EvidenceManager(temp_case_dir)
        mgr.manifest.case_id = "TEST-001"
        mgr.add_evidence(sample_file, "Test", EvidenceType.CONTRACT)
        summary = mgr.summary()
        assert summary["total_items"] == 1
        assert "contract" in summary["by_type"]

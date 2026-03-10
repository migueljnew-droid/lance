"""Tests for case state machine."""

import pytest
import tempfile
from pathlib import Path
from datetime import date

from engine.case import CaseManager
from engine.models import Case, CaseState, Jurisdiction, Party


@pytest.fixture
def temp_case_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_case():
    return Case(
        id="TEST-001",
        title="Test Case",
        type="breach_of_contract",
        jurisdiction=Jurisdiction(
            primary_state="CA",
            governing_law="CA",
        ),
        claimant=Party(id="claimant", name="Test Claimant", role="claimant"),
    )


class TestCaseManager:
    def test_init_case(self, temp_case_dir, sample_case):
        mgr = CaseManager.init_case(temp_case_dir, sample_case)
        assert mgr.case.id == "TEST-001"
        assert mgr.case.state == CaseState.EVIDENCE_GATHERING
        assert (temp_case_dir / "case.yaml").exists()
        assert (temp_case_dir / "events.jsonl").exists()

    def test_load_case(self, temp_case_dir, sample_case):
        CaseManager.init_case(temp_case_dir, sample_case)
        mgr = CaseManager(temp_case_dir)
        loaded = mgr.load()
        assert loaded.id == "TEST-001"
        assert loaded.title == "Test Case"

    def test_valid_transition(self, temp_case_dir, sample_case):
        mgr = CaseManager.init_case(temp_case_dir, sample_case)
        event = mgr.transition(CaseState.DEMAND, reason="Evidence complete")
        assert mgr.case.state == CaseState.DEMAND
        assert "demand" in event.description.lower()

    def test_invalid_transition(self, temp_case_dir, sample_case):
        mgr = CaseManager.init_case(temp_case_dir, sample_case)
        with pytest.raises(ValueError):
            mgr.transition(CaseState.LITIGATION)  # Can't skip to litigation

    def test_event_logging(self, temp_case_dir, sample_case):
        mgr = CaseManager.init_case(temp_case_dir, sample_case)
        mgr.log_event("test_event", "tester", "Testing event log")
        events = mgr.get_events()
        assert len(events) == 2  # init + test event
        assert events[1].type == "test_event"

    def test_status_summary(self, temp_case_dir, sample_case):
        mgr = CaseManager.init_case(temp_case_dir, sample_case)
        summary = mgr.status_summary()
        assert summary["state"] == "evidence_gathering"
        assert summary["case_id"] == "TEST-001"
        assert len(summary["exit_criteria"]) > 0

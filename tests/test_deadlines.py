"""Tests for deadline engine."""

import pytest
import tempfile
from pathlib import Path
from datetime import date, timedelta

from engine.deadlines import DeadlineEngine
from engine.models import Claim, ClaimType


@pytest.fixture
def temp_case_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestDeadlineEngine:
    def test_add_response_deadline(self, temp_case_dir):
        engine = DeadlineEngine(temp_case_dir)
        dl = engine.add_response_deadline(
            description="Warner response to demand",
            trigger_date=date.today(),
            days=30,
            counterparty="warner",
        )
        assert dl.id == "DL-001"
        assert dl.due_date == date.today() + timedelta(days=30)

    def test_add_sol_deadline(self, temp_case_dir):
        engine = DeadlineEngine(temp_case_dir)
        claim = Claim(
            id="CLM-001",
            type=ClaimType.BREACH_OF_CONTRACT,
            description="Breach of publishing agreement",
            discovery_date=date(2026, 2, 25),
        )
        dl = engine.add_sol_deadline(claim, jurisdiction="CA")
        assert "337" in dl.notes  # CCP § 337
        assert dl.due_date == date(2030, 2, 25)  # 4 years from discovery

    def test_check_deadlines_urgent(self, temp_case_dir):
        engine = DeadlineEngine(temp_case_dir)
        engine.add_response_deadline(
            description="Urgent deadline",
            trigger_date=date.today() - timedelta(days=25),
            days=30,
        )
        report = engine.check_deadlines()
        assert len(report["urgent"]) == 1
        assert report["urgent"][0]["days_remaining"] <= 7

    def test_check_deadlines_expired(self, temp_case_dir):
        engine = DeadlineEngine(temp_case_dir)
        engine.add_response_deadline(
            description="Expired deadline",
            trigger_date=date.today() - timedelta(days=60),
            days=30,
        )
        report = engine.check_deadlines()
        assert len(report["expired"]) == 1

    def test_complete_deadline(self, temp_case_dir):
        engine = DeadlineEngine(temp_case_dir)
        dl = engine.add_response_deadline(
            description="Test deadline",
            trigger_date=date.today(),
            days=30,
        )
        engine.complete_deadline(dl.id, notes="Response received")
        report = engine.check_deadlines()
        assert len(report["completed"]) == 1

    def test_sol_reference_lookup(self, temp_case_dir):
        engine = DeadlineEngine(temp_case_dir)
        info = engine.get_sol_reference("fraud", "CA")
        assert info is not None
        assert info["years"] == 3
        assert "338" in info["statute"]

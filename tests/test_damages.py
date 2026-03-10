"""Tests for the damages calculator."""

import pytest
from datetime import date

from engine.damages import DamagesCalculator


class TestDamagesCalculator:
    def test_simple_interest_ca(self):
        calc = DamagesCalculator(jurisdiction="CA")
        est = calc.calculate(
            claim_id="CLM-001",
            principal=30000.0,
            underpayment_start=date(2020, 1, 1),
            as_of=date(2025, 1, 1),
        )
        assert est.principal == 30000.0
        assert est.interest_rate == 0.10
        # 5 years at 10% simple = $15,000 interest
        assert abs(est.accrued_interest - 15000) < 100  # Allow rounding
        assert abs(est.total_with_interest - 45000) < 100

    def test_custom_rate(self):
        calc = DamagesCalculator(jurisdiction="CA")
        est = calc.calculate(
            claim_id="CLM-001",
            principal=10000.0,
            underpayment_start=date(2023, 1, 1),
            as_of=date(2024, 1, 1),
            custom_rate=0.05,
        )
        assert est.interest_rate == 0.05
        assert abs(est.accrued_interest - 500) < 10

    def test_phased_calculation(self):
        calc = DamagesCalculator(jurisdiction="CA")
        underpayments = [
            {"amount": 5000, "start_date": "2018-01-01"},
            {"amount": 10000, "start_date": "2020-01-01"},
            {"amount": 15000, "start_date": "2022-01-01"},
        ]
        est = calc.calculate_phased(
            claim_id="CLM-001",
            underpayments=underpayments,
            as_of=date(2025, 1, 1),
        )
        assert est.principal == 30000.0
        assert est.accrued_interest > 0
        assert est.total_with_interest > 30000.0

    def test_settlement_evaluation_favorable(self):
        calc = DamagesCalculator()
        calc.calculate("CLM-001", 30000.0, date(2020, 1, 1), as_of=date(2025, 1, 1))
        result = calc.evaluate_settlement(40000.0)
        assert "FAVORABLE" in result["recommendation"] or "REASONABLE" in result["recommendation"]

    def test_settlement_evaluation_reject(self):
        calc = DamagesCalculator()
        calc.calculate("CLM-001", 100000.0, date(2015, 1, 1), as_of=date(2025, 1, 1))
        result = calc.evaluate_settlement(10000.0)
        assert "REJECT" in result["recommendation"]

    def test_total_recovery(self):
        calc = DamagesCalculator()
        calc.calculate("CLM-001", 20000.0, date(2020, 1, 1), as_of=date(2025, 1, 1))
        calc.calculate("CLM-002", 10000.0, date(2021, 1, 1), as_of=date(2025, 1, 1))
        total = calc.total_estimated_recovery()
        assert total["total_principal"] == 30000.0
        assert total["claims"] == 2
        assert total["total_recovery"] > 30000.0

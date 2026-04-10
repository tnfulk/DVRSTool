"""Tests that require explicit confirmation when the plan table changes."""

from __future__ import annotations

import unittest

from dvrs_tool.plan_table_guard import PLAN_TABLE_CHANGE_CONFIRMATION, current_plan_table_sha256


class PlanTableGuardTests(unittest.TestCase):
    def test_plan_table_changes_require_explicit_confirmation(self) -> None:
        self.assertTrue(
            PLAN_TABLE_CHANGE_CONFIRMATION["confirmed_intentional"],
            "Plan table edits must be explicitly marked intentional.",
        )
        self.assertTrue(
            PLAN_TABLE_CHANGE_CONFIRMATION["confirmed_by"],
            "Plan table edits require a confirmer name.",
        )
        self.assertTrue(
            PLAN_TABLE_CHANGE_CONFIRMATION["confirmed_on"],
            "Plan table edits require a confirmation date.",
        )
        self.assertTrue(
            PLAN_TABLE_CHANGE_CONFIRMATION["reason"],
            "Plan table edits require a brief explanation.",
        )
        self.assertEqual(
            current_plan_table_sha256(),
            PLAN_TABLE_CHANGE_CONFIRMATION["approved_table_sha256"],
            "The plan table changed. Update dvrs_tool/plan_table_guard.py only after explicitly confirming the change is intended.",
        )


if __name__ == "__main__":
    unittest.main()

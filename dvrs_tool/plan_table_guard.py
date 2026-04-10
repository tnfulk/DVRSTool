"""Guardrail for intentional edits to the published plan table."""

from __future__ import annotations

import hashlib
import json

from .models import BandFamily
from .plan_data import TECHNICAL_PLANS


PLAN_TABLE_CHANGE_CONFIRMATION = {
    "confirmed_intentional": True,
    "confirmed_by": "Codex with user-approved corrections",
    "confirmed_on": "2026-04-10",
    "reason": "Baseline approved after manual reconciliation of the 700/800 plan table values.",
    "approved_table_sha256": "e4390507b36669d37ae6f08bfdbae764ec5a9e627a93c12dac45198797b88efe",
}


def current_plan_table_sha256() -> str:
    """Return a stable digest of the user-facing plan table fields."""

    rows: list[dict[str, object]] = []
    for family in (BandFamily.BAND_700, BandFamily.BAND_800):
        for plan in TECHNICAL_PLANS[family]:
            rows.append(
                {
                    "id": plan.id,
                    "display_name": plan.display_name,
                    "dvrs_rx_window": plan.dvrs_rx_window,
                    "dvrs_tx_window": plan.dvrs_tx_window,
                    "system_700_rx_range": plan.system_700_rx_range,
                    "system_700_tx_range": plan.system_700_tx_range,
                    "system_800_rx_range": plan.system_800_rx_range,
                    "system_800_tx_range": plan.system_800_tx_range,
                    "fixed_dvrs_rx_range": plan.fixed_dvrs_rx_range,
                    "fixed_dvrs_tx_range": plan.fixed_dvrs_tx_range,
                }
            )

    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

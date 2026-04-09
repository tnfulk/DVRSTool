"""Command-line interface for the DVRS planning tool."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from .engine import DVRSCalculationEngine
from .exceptions import DVRSBaseError
from .models import CalculationRequest, Country

HELP_EPILOG = """Examples:
  python -m dvrs_tool --country "United States" --mobile-tx-low 806.0 --mobile-tx-high 809.0
  python -m dvrs_tool --country Canada --mobile-tx-low 151.0 --mobile-tx-high 151.2 --mobile-rx-low 156.0 --mobile-rx-high 156.2

Returned JSON shape:
  {
    "status": "ok" | "error",
    "data": {
      "request": { ...original normalized inputs... },
      "system_summary": {
        "detected_band": string,
        "mobile_tx_range": { "low_mhz": number, "high_mhz": number },
        "mobile_rx_range": { ... } | null,
        "system_rx_range": { ... },
        "system_tx_range": { ... } | null,
        "pairing_source": string,
        "warnings": [string]
      },
      "plan_results": [
        {
          "plan_id": string,
          "display_name": string,
          "technical_status": string,
          "regulatory_status": string,
          "confidence": number,
          "proposed_dvrs_tx_range": { ... } | null,
          "proposed_dvrs_rx_range": { ... } | null,
          "mount_compatibility": [string],
          "failure_reasons": [string],
          "warnings": [string],
          "regulatory_reasons": [string],
          "notes": [string]
        }
      ],
      "ordering_summary": {
        "system_tx_range": { ... } | null,
        "system_rx_range": { ... },
        "proposed_dvrs_tx_range": { ... } | null,
        "proposed_dvrs_rx_range": { ... } | null,
        "actual_licensed_dvrs_tx_range": { ... } | null,
        "actual_licensed_dvrs_rx_range": { ... } | null,
        "notes": [string]
      },
      "errors": [object]
    },
    "error": {
      "code": string,
      "message": string,
      "details": object
    }
  }
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dvrs_tool",
        description="Evaluate DVRS in-band planning scenarios and return JSON.",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--country",
        required=True,
        choices=[country.value for country in Country],
        help="Country-specific regulatory policy to apply.",
    )
    parser.add_argument(
        "--mobile-tx-low",
        required=True,
        type=float,
        help="Lowest mobile transmit frequency in MHz.",
    )
    parser.add_argument(
        "--mobile-tx-high",
        required=True,
        type=float,
        help="Highest mobile transmit frequency in MHz.",
    )
    parser.add_argument(
        "--mobile-rx-low",
        type=float,
        help="Optional lowest mobile receive frequency in MHz.",
    )
    parser.add_argument(
        "--mobile-rx-high",
        type=float,
        help="Optional highest mobile receive frequency in MHz.",
    )
    parser.add_argument(
        "--use-latest-ordering-ruleset",
        dest="use_latest_ordering_ruleset",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable the latest ordering ruleset logic. Default: enabled.",
    )
    parser.add_argument(
        "--agency-notes",
        help="Optional free-form note included in the ordering summary.",
    )
    parser.add_argument(
        "--actual-licensed-dvrs-tx-low",
        type=float,
        help="Optional lowest actually licensed DVRS TX frequency in MHz.",
    )
    parser.add_argument(
        "--actual-licensed-dvrs-tx-high",
        type=float,
        help="Optional highest actually licensed DVRS TX frequency in MHz.",
    )
    parser.add_argument(
        "--actual-licensed-dvrs-rx-low",
        type=float,
        help="Optional lowest actually licensed DVRS RX frequency in MHz.",
    )
    parser.add_argument(
        "--actual-licensed-dvrs-rx-high",
        type=float,
        help="Optional highest actually licensed DVRS RX frequency in MHz.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Spaces to use when pretty-printing output JSON. Default: 2.",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    request = CalculationRequest(
        country=Country(args.country),
        mobile_tx_low_mhz=args.mobile_tx_low,
        mobile_tx_high_mhz=args.mobile_tx_high,
        mobile_rx_low_mhz=args.mobile_rx_low,
        mobile_rx_high_mhz=args.mobile_rx_high,
        use_latest_ordering_ruleset=args.use_latest_ordering_ruleset,
        agency_notes=args.agency_notes,
        actual_licensed_dvrs_tx_low_mhz=args.actual_licensed_dvrs_tx_low,
        actual_licensed_dvrs_tx_high_mhz=args.actual_licensed_dvrs_tx_high,
        actual_licensed_dvrs_rx_low_mhz=args.actual_licensed_dvrs_rx_low,
        actual_licensed_dvrs_rx_high_mhz=args.actual_licensed_dvrs_rx_high,
    )

    engine = DVRSCalculationEngine()

    try:
        response = engine.evaluate(request)
        payload = {
            "status": "ok",
            "data": response.to_dict(),
        }
        print(json.dumps(payload, indent=args.indent))
        return 0
    except DVRSBaseError as exc:
        payload = {
            "status": "error",
            "error": exc.to_dict(),
        }
        print(json.dumps(payload, indent=args.indent), file=sys.stderr)
        return 1


def main() -> int:
    return run()

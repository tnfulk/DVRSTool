"""Unit tests for the DVRS calculation engine."""

from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from dvrs_tool.api import create_app
from dvrs_tool.cli import build_parser, run
from dvrs_tool.engine import DVRSCalculationEngine
from dvrs_tool.exceptions import UnsupportedBandError
from dvrs_tool.models import CalculationRequest, Country, PairingSource, RegulatoryStatus, TechnicalStatus
from dvrs_tool.pdf_export import build_ordering_summary_pdf


class DVRSCalculationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DVRSCalculationEngine()

    def test_700_band_deterministic_pairing_and_valid_plan(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=803.0,
            mobile_tx_high_mhz=804.0,
        )

        response = self.engine.evaluate(request)

        self.assertEqual(response.system_summary.pairing_source, PairingSource.DETERMINISTIC)
        self.assertEqual(response.system_summary.system_tx_range.low_mhz, 773.0)
        self.assertEqual(response.system_summary.system_tx_range.high_mhz, 774.0)
        valid_plans = [plan for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID]
        self.assertTrue(valid_plans)
        self.assertEqual(valid_plans[0].proposed_dvrs_rx_range.low_mhz, 799.0)
        self.assertEqual(valid_plans[0].proposed_dvrs_rx_range.high_mhz, 800.0)
        self.assertEqual(valid_plans[0].proposed_dvrs_tx_range.low_mhz, 769.0)
        self.assertEqual(valid_plans[0].proposed_dvrs_tx_range.high_mhz, 770.0)
        self.assertEqual(valid_plans[0].regulatory_status, RegulatoryStatus.LIKELY_LICENSABLE)

    def test_800_band_plan_c_can_be_technically_valid(self) -> None:
        request = CalculationRequest(
            country=Country.CANADA,
            mobile_tx_low_mhz=806.0,
            mobile_tx_high_mhz=807.0,
        )

        response = self.engine.evaluate(request)
        plan_c = next(plan for plan in response.plan_results if plan.plan_id == "800-C")

        self.assertEqual(plan_c.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.low_mhz, 810.0)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.low_mhz, 855.0)
        self.assertIn(plan_c.regulatory_status, {RegulatoryStatus.LIKELY_LICENSABLE, RegulatoryStatus.COORDINATION_REQUIRED})

    def test_wide_mobile_block_only_limits_proposed_dvrs_passband(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=806.0,
            mobile_tx_high_mhz=809.0,
        )

        response = self.engine.evaluate(request)
        plan_a1 = next(plan for plan in response.plan_results if plan.plan_id == "800-A1")
        warning_text = " ".join(plan_a1.warnings)

        self.assertEqual(response.system_summary.system_tx_range.low_mhz, 851.0)
        self.assertEqual(response.system_summary.system_tx_range.high_mhz, 854.0)
        self.assertEqual(plan_a1.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.width_mhz, 1.0)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.width_mhz, 1.0)
        self.assertIn("Only the proposed DVRS TX/RX range was limited", warning_text)
        self.assertNotIn("Input mobile TX passband exceeds", warning_text)

    def test_vhf_duplex_requires_manual_rx_override(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=151.0,
            mobile_tx_high_mhz=151.2,
        )

        response = self.engine.evaluate(request)
        duplex_plan = next(plan for plan in response.plan_results if plan.plan_id == "VHF-A")
        simplex_plan = next(plan for plan in response.plan_results if plan.plan_id == "VHF-D1")

        self.assertEqual(response.system_summary.pairing_source, PairingSource.UNAVAILABLE)
        self.assertEqual(duplex_plan.technical_status, TechnicalStatus.INVALID)
        self.assertIn("Manual mobile RX input is required", duplex_plan.failure_reasons[0])
        self.assertEqual(simplex_plan.technical_status, TechnicalStatus.VALID)

    def test_vhf_manual_override_enables_duplex_plan_attempt(self) -> None:
        request = CalculationRequest(
            country=Country.CANADA,
            mobile_tx_low_mhz=151.0,
            mobile_tx_high_mhz=151.2,
            mobile_rx_low_mhz=156.0,
            mobile_rx_high_mhz=156.2,
        )

        response = self.engine.evaluate(request)
        duplex_plan = next(plan for plan in response.plan_results if plan.plan_id == "VHF-A")

        self.assertEqual(response.system_summary.pairing_source, PairingSource.MANUAL_OVERRIDE)
        self.assertEqual(duplex_plan.technical_status, TechnicalStatus.VALID)

    def test_invalid_band_raises_structured_error(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=300.0,
            mobile_tx_high_mhz=301.0,
        )

        with self.assertRaises(UnsupportedBandError) as ctx:
            self.engine.evaluate(request)

        self.assertEqual(ctx.exception.code, "UNSUPPORTED_OR_AMBIGUOUS_BAND")
        self.assertIn("mobile_tx_low_mhz", ctx.exception.details)

    def test_api_factory_builds_expected_routes_when_dependencies_are_installed(self) -> None:
        app = create_app()
        routes = {route.path for route in app.routes}

        self.assertIn("/health", routes)
        self.assertIn("/", routes)
        self.assertIn("/v1/evaluate", routes)
        self.assertIn("/v1/order-summary.pdf", routes)

    def test_api_evaluate_expects_json_body(self) -> None:
        app = create_app()
        route = next(route for route in app.routes if route.path == "/v1/evaluate")

        self.assertEqual(len(route.dependant.body_params), 1)
        self.assertEqual(route.dependant.body_params[0].name, "payload")

    def test_pdf_export_contains_ordering_form_summary(self) -> None:
        from io import BytesIO

        from pypdf import PdfReader

        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=809.8125,
                mobile_tx_high_mhz=814.6125,
            )
        )

        pdf = build_ordering_summary_pdf(response)
        reader = PdfReader(BytesIO(pdf))
        text = reader.pages[0].extract_text()

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertIn("DVRS/VRX1000 SUPPLEMENTAL ORDERING FORM", text)
        self.assertIn("774.0000", text)
        self.assertIn("809.8125", text)

    def test_cli_run_returns_json_payload_for_valid_request(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = run(
                [
                    "--country",
                    "United States",
                    "--mobile-tx-low",
                    "803.0",
                    "--mobile-tx-high",
                    "804.0",
                ]
            )

        output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn('"status": "ok"', output)
        self.assertIn('"system_summary"', output)
        self.assertIn('"plan_results"', output)

    def test_cli_run_returns_structured_error_for_invalid_request(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr):
            exit_code = run(
                [
                    "--country",
                    "United States",
                    "--mobile-tx-low",
                    "300.0",
                    "--mobile-tx-high",
                    "301.0",
                ]
            )

        output = stderr.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn('"status": "error"', output)
        self.assertIn('"code": "UNSUPPORTED_OR_AMBIGUOUS_BAND"', output)

    def test_cli_help_describes_arguments_and_response_shape(self) -> None:
        parser = build_parser()
        help_text = parser.format_help()

        self.assertIn("--country", help_text)
        self.assertIn("--mobile-tx-low", help_text)
        self.assertIn("Returned JSON shape", help_text)
        self.assertIn('"status": "ok" | "error"', help_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

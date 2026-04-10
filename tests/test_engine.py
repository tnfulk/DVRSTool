"""Unit tests for the DVRS calculation engine."""

from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from dvrs_tool.api import create_app
from dvrs_tool.cli import build_parser, run
from dvrs_tool.engine import DVRSCalculationEngine
from dvrs_tool.exceptions import InputValidationError, UnsupportedBandError
from dvrs_tool.models import (
    BandFamily,
    CalculationRequest,
    Country,
    PairingSource,
    RegulatoryStatus,
    SystemBandHint,
    TechnicalStatus,
)
from dvrs_tool.plan_data import TECHNICAL_PLANS
from dvrs_tool.pdf_export import build_ordering_summary_pdf


class DVRSCalculationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DVRSCalculationEngine()

    def test_700_only_system_is_not_a_supported_standard_configuration_model(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=803.0,
            mobile_tx_high_mhz=804.0,
        )

        with self.assertRaises(UnsupportedBandError) as ctx:
            self.engine.evaluate(request)

        self.assertEqual(ctx.exception.code, "UNSUPPORTED_700_ONLY_SYSTEM")
        self.assertEqual(ctx.exception.details["supported_models"], ["800 only", "700 and 800"])

    def test_800_band_plan_c_is_valid_when_at_least_one_channel_in_fixed_range_works(self) -> None:
        request = CalculationRequest(
            country=Country.CANADA,
            mobile_tx_low_mhz=810.0,
            mobile_tx_high_mhz=811.0,
        )

        response = self.engine.evaluate(request)
        plan_c = next(plan for plan in response.plan_results if plan.plan_id == "800-C")

        self.assertEqual(plan_c.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.low_mhz, 806.0)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.high_mhz, 807.0)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.low_mhz, 851.0)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.high_mhz, 852.0)
        self.assertEqual(plan_c.rule_violations, [])

    def test_actual_700_mhz_dvrs_pair_selects_700_plan_family(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=810.0,
                mobile_tx_high_mhz=811.0,
                actual_dvrs_tx_mhz=774.5,
                actual_dvrs_rx_mhz=804.5,
            )
        )

        valid_plan_ids = [
            plan.plan_id for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID
        ]

        self.assertEqual(valid_plan_ids, ["700-A"])

        plan_a = next(plan for plan in response.plan_results if plan.plan_id == "700-A")
        self.assertEqual(plan_a.proposed_dvrs_tx_range.low_mhz, 774.5)
        self.assertEqual(plan_a.proposed_dvrs_tx_range.high_mhz, 774.5)
        self.assertEqual(plan_a.proposed_dvrs_rx_range.low_mhz, 804.5)
        self.assertEqual(plan_a.proposed_dvrs_rx_range.high_mhz, 804.5)

    def test_wide_mobile_block_limits_proposed_ranges_without_extra_warning(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=806.0,
            mobile_tx_high_mhz=810.0,
        )

        system_summary = self.engine._build_system_summary(request, BandFamily.BAND_800)
        plan_a1_definition = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-A1")
        plan_a1 = self.engine._evaluate_plan(request, system_summary, plan_a1_definition)
        warning_text = " ".join(plan_a1.warnings)

        self.assertEqual(system_summary.system_tx_range.low_mhz, 851.0)
        self.assertEqual(system_summary.system_tx_range.high_mhz, 855.0)
        self.assertEqual(plan_a1.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.low_mhz, 816.0)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.high_mhz, 824.0)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.low_mhz, 861.0)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.high_mhz, 869.0)
        self.assertEqual(warning_text, "")

    def test_ordering_guide_windows_are_encoded_exactly_for_core_700_800_plans(self) -> None:
        plan_700_b = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_700] if plan.id == "700-B")
        plan_800_a1 = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-A1")
        plan_800_a2 = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-A2")
        plan_800_b = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-B")
        plan_800_c = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-C")

        self.assertEqual(plan_700_b.active_mobile_tx_window, (802.0, 805.0))
        self.assertEqual(plan_700_b.fixed_dvrs_rx_range, (799.0, 802.0))
        self.assertEqual(plan_700_b.fixed_dvrs_tx_range, (769.0, 772.0))
        self.assertEqual(plan_800_a1.dvrs_rx_window, (816.0, 824.0))
        self.assertEqual(plan_800_a1.active_mobile_tx_window, (806.0, 819.0))
        self.assertEqual(plan_800_a1.dvrs_tx_window, (861.0, 869.0))
        self.assertEqual(plan_800_a1.pair_offset_mhz, 45.0)
        self.assertEqual(plan_800_a1.fixed_dvrs_tx_range, (861.0, 869.0))
        self.assertEqual(plan_800_a1.max_dvrs_passband_mhz, 3.0)
        self.assertEqual(plan_800_a2.dvrs_rx_window, (806.0, 814.0))
        self.assertEqual(plan_800_a2.active_mobile_tx_window, (811.0, 824.0))
        self.assertEqual(plan_800_b.dvrs_tx_window, (854.0, 869.0))
        self.assertEqual(plan_800_c.dvrs_rx_window, (806.0, 821.0))
        self.assertEqual(plan_800_c.dvrs_tx_window, (851.0, 866.0))

    def test_800_a1_accepts_spacing_valid_actual_pair(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0125,
                mobile_tx_high_mhz=813.8375,
                actual_dvrs_tx_mhz=863.2125,
                actual_dvrs_rx_mhz=818.2125,
            )
        )

        plan_a1 = next(plan for plan in response.plan_results if plan.plan_id == "800-A1")

        self.assertEqual(plan_a1.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.low_mhz, 863.2125)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.high_mhz, 863.2125)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.low_mhz, 818.2125)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.high_mhz, 818.2125)

    def test_800_a1_recommended_ranges_stay_within_fixed_ordering_guide_values(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=806.0,
            mobile_tx_high_mhz=813.0,
        )
        system_summary = self.engine._build_system_summary(request, BandFamily.BAND_800)
        plan_a1_definition = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-A1")
        plan_a1 = self.engine._evaluate_plan(request, system_summary, plan_a1_definition)

        self.assertEqual(plan_a1.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.low_mhz, 816.0)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.high_mhz, 824.0)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.low_mhz, 861.0)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.high_mhz, 869.0)

    def test_engine_accepts_five_decimal_place_inputs(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=810.12345,
            mobile_tx_high_mhz=811.12345,
        )

        response = self.engine.evaluate(request)

        self.assertEqual(response.system_summary.mobile_tx_range.low_mhz, 810.12345)
        self.assertEqual(response.system_summary.system_tx_range.low_mhz, 855.12345)

    def test_800_only_hint_uses_tx_plus_45_for_system_pairing(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=811.0,
                mobile_tx_high_mhz=812.0,
                system_band_hint=SystemBandHint.BAND_800_ONLY,
            )
        )

        self.assertEqual(response.system_summary.detected_band, BandFamily.BAND_800)
        self.assertEqual(response.system_summary.system_tx_range.low_mhz, 856.0)
        self.assertEqual(response.system_summary.system_tx_range.high_mhz, 857.0)

    def test_800_only_hint_evaluates_700_a_and_800_c_to_offer_both_dvrs_locations(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=811.0,
                mobile_tx_high_mhz=812.0,
                system_band_hint=SystemBandHint.BAND_800_ONLY,
            )
        )

        self.assertEqual([plan.plan_id for plan in response.plan_results], ["700-A", "800-C"])

    def test_800_c_is_valid_when_fixed_range_contains_a_spacing_compliant_channel(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=811.0,
            mobile_tx_high_mhz=818.0,
        )
        system_summary = self.engine._build_system_summary(request, BandFamily.BAND_800)
        plan_c_definition = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-C")
        plan_c = self.engine._evaluate_plan(request, system_summary, plan_c_definition)

        self.assertEqual(plan_c.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.low_mhz, 806.0)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.high_mhz, 808.0)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.low_mhz, 851.0)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.high_mhz, 853.0)
        self.assertEqual(plan_c.rule_violations, [])

    def test_auto_detected_800_only_system_uses_same_two_plan_model(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=808.0,
                mobile_tx_high_mhz=818.0,
            )
        )

        self.assertEqual(response.system_summary.detected_band, BandFamily.BAND_800)
        self.assertEqual([plan.plan_id for plan in response.plan_results], ["700-A", "800-C"])

    def test_engine_rejects_more_than_five_decimal_places_with_exact_reason(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=803.123456,
            mobile_tx_high_mhz=804.12345,
        )

        with self.assertRaises(InputValidationError) as ctx:
            self.engine.evaluate(request)

        self.assertEqual(ctx.exception.code, "TOO_MANY_DECIMAL_PLACES")
        self.assertEqual(ctx.exception.details["field"], "mobile_tx_low_mhz")
        self.assertEqual(ctx.exception.details["max_decimal_places"], 5)
        self.assertEqual(ctx.exception.rule_violations[0]["code"], "TOO_MANY_DECIMAL_PLACES")

    def test_actual_dvrs_outside_computed_range_can_still_validate_matching_plan(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0125,
                mobile_tx_high_mhz=813.8375,
                actual_dvrs_tx_mhz=863.2125,
                actual_dvrs_rx_mhz=818.2125,
            )
        )

        plan_a1 = next(plan for plan in response.plan_results if plan.plan_id == "800-A1")

        self.assertEqual(plan_a1.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.low_mhz, 863.2125)
        self.assertEqual(plan_a1.proposed_dvrs_tx_range.high_mhz, 863.2125)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.low_mhz, 818.2125)
        self.assertEqual(plan_a1.proposed_dvrs_rx_range.high_mhz, 818.2125)
        self.assertFalse(
            any(
                violation.code == "ACTUAL_DVRS_FREQUENCY_OUTSIDE_COMPUTED_RANGE"
                for plan in response.plan_results
                for violation in plan.rule_violations
            )
        )

    def test_actual_dvrs_frequency_can_leave_only_matching_plans_valid(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0,
                mobile_tx_high_mhz=807.0,
                actual_dvrs_tx_mhz=855.5,
                actual_dvrs_rx_mhz=810.5,
            )
        )

        valid_plan_ids = [
            plan.plan_id for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID
        ]
        self.assertEqual(valid_plan_ids, ["800-B"])

    def test_actual_dvrs_window_mismatch_does_not_override_spacing_and_plan_rules(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0125,
                mobile_tx_high_mhz=813.8375,
                actual_dvrs_tx_mhz=855.5,
                actual_dvrs_rx_mhz=810.5,
            )
        )

        self.assertEqual([plan.plan_id for plan in response.plan_results], ["800-A2", "800-B", "800-C"])

        plan_a2 = next(plan for plan in response.plan_results if plan.plan_id == "800-A2")
        self.assertEqual(plan_a2.technical_status, TechnicalStatus.INVALID)
        self.assertEqual(plan_a2.rule_violations[0].code, "MOBILE_TX_OUTSIDE_ACTIVE_PLAN_WINDOW")

    def test_700_a_is_preferred_for_800_system_when_actual_dvrs_pair_is_700_mhz(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0125,
                mobile_tx_high_mhz=818.2125,
                actual_dvrs_tx_mhz=770.0,
                actual_dvrs_rx_mhz=800.0,
            )
        )

        valid_plan_ids = [
            plan.plan_id for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID
        ]

        self.assertEqual(valid_plan_ids, ["700-A"])
        self.assertEqual(
            response.ordering_summary.notes[0],
            "Best preliminary standard plan: 700 MHz In-Band Plan A.",
        )

    def test_system_band_hint_700_and_800_limits_default_candidates(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=802.0,
                mobile_tx_700_high_mhz=803.0,
                mobile_tx_800_low_mhz=806.0,
                mobile_tx_800_high_mhz=807.0,
            )
        )

        self.assertEqual(
            [plan.plan_id for plan in response.plan_results],
            ["700-B", "700-C", "800-A1", "800-A2", "800-B"],
        )

    def test_mixed_system_summary_exposes_both_700_and_800_deterministic_ranges(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=802.0125,
                mobile_tx_700_high_mhz=804.8875,
                mobile_tx_800_low_mhz=806.2125,
                mobile_tx_800_high_mhz=822.2125,
            )
        )

        summary = response.system_summary

        self.assertEqual(summary.pairing_source, PairingSource.DETERMINISTIC)
        self.assertEqual(summary.mobile_tx_700_range.low_mhz, 802.0125)
        self.assertEqual(summary.mobile_tx_700_range.high_mhz, 804.8875)
        self.assertEqual(summary.system_tx_700_range.low_mhz, 772.0125)
        self.assertEqual(summary.system_tx_700_range.high_mhz, 774.8875)
        self.assertEqual(summary.mobile_tx_800_range.low_mhz, 806.2125)
        self.assertEqual(summary.mobile_tx_800_range.high_mhz, 822.2125)
        self.assertEqual(summary.system_tx_800_range.low_mhz, 851.2125)
        self.assertEqual(summary.system_tx_800_range.high_mhz, 867.2125)
        self.assertIsNone(summary.system_tx_range)

    def test_800_c_is_only_evaluated_when_800_only_is_selected(self) -> None:
        mixed_response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=810.0,
                mobile_tx_700_high_mhz=811.0,
                mobile_tx_800_low_mhz=813.0,
                mobile_tx_800_high_mhz=814.0,
            )
        )
        only_800_response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=810.0,
                mobile_tx_high_mhz=811.0,
                system_band_hint=SystemBandHint.BAND_800_ONLY,
            )
        )

        self.assertNotIn("800-C", [plan.plan_id for plan in mixed_response.plan_results])
        self.assertEqual([plan.plan_id for plan in only_800_response.plan_results], ["700-A", "800-C"])

    def test_actual_dvrs_native_plan_driver_overrides_system_band_hint(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0125,
                mobile_tx_high_mhz=818.2125,
                system_band_hint=SystemBandHint.BAND_800_ONLY,
                actual_dvrs_tx_mhz=770.0,
                actual_dvrs_rx_mhz=800.0,
            )
        )

        valid_plan_ids = [
            plan.plan_id for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID
        ]

        self.assertEqual(valid_plan_ids, ["700-A"])

    def test_800_only_hint_with_700_mhz_dvrs_pair_does_not_leak_non_700_800_plans(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0,
                mobile_tx_high_mhz=807.0,
                system_band_hint=SystemBandHint.BAND_800_ONLY,
                actual_dvrs_tx_mhz=770.0,
                actual_dvrs_rx_mhz=800.0,
            )
        )

        returned_plan_ids = [plan.plan_id for plan in response.plan_results]
        valid_plan_ids = [
            plan.plan_id for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID
        ]

        self.assertEqual(returned_plan_ids, ["700-A"])
        self.assertEqual(valid_plan_ids, ["700-A"])

    def test_mixed_700_and_800_ranges_can_validate_700_plan_b_from_actual_dvrs_pair(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=802.0,
                mobile_tx_700_high_mhz=803.0,
                mobile_tx_800_low_mhz=806.0,
                mobile_tx_800_high_mhz=807.0,
                actual_dvrs_tx_mhz=770.0,
                actual_dvrs_rx_mhz=800.0,
            )
        )

        returned_plan_ids = [plan.plan_id for plan in response.plan_results]
        valid_plan_ids = [
            plan.plan_id for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID
        ]

        self.assertEqual(returned_plan_ids, ["700-B"])
        self.assertEqual(valid_plan_ids, [])
        self.assertEqual(
            response.ordering_summary.notes[0],
            "No technically valid standard plan proposal was produced.",
        )

    def test_mixed_700_and_800_700_b_plan_result_uses_plan_specific_system_ranges(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=802.0125,
                mobile_tx_700_high_mhz=804.8875,
                mobile_tx_800_low_mhz=806.2125,
                mobile_tx_800_high_mhz=822.2125,
                actual_dvrs_tx_mhz=770.0,
                actual_dvrs_rx_mhz=800.0,
            )
        )

        plan_b = next(plan for plan in response.plan_results if plan.plan_id == "700-B")

        self.assertEqual(plan_b.mobile_tx_range.low_mhz, 802.0125)
        self.assertEqual(plan_b.mobile_tx_range.high_mhz, 804.8875)
        self.assertEqual(plan_b.system_tx_range.low_mhz, 772.0125)
        self.assertEqual(plan_b.system_tx_range.high_mhz, 774.8875)
        self.assertEqual(plan_b.system_rx_range.low_mhz, 802.0125)
        self.assertEqual(plan_b.system_rx_range.high_mhz, 804.8875)

    def test_mixed_700_and_800_700_b_ordering_summary_uses_best_plan_system_ranges(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=802.0125,
                mobile_tx_700_high_mhz=804.8875,
                mobile_tx_800_low_mhz=806.2125,
                mobile_tx_800_high_mhz=822.2125,
                actual_dvrs_tx_mhz=770.0,
                actual_dvrs_rx_mhz=800.0,
            )
        )

        self.assertIsNone(response.ordering_summary.system_tx_range)
        self.assertEqual(response.ordering_summary.system_rx_range.low_mhz, 802.0125)
        self.assertEqual(response.ordering_summary.system_rx_range.high_mhz, 822.2125)

    def test_mixed_ranges_return_surviving_compliant_subrange_for_700_c(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=None,
                mobile_tx_high_mhz=None,
                system_band_hint=SystemBandHint.BAND_700_AND_800,
                mobile_tx_700_low_mhz=799.2125,
                mobile_tx_700_high_mhz=801.8875,
                mobile_tx_800_low_mhz=806.0125,
                mobile_tx_800_high_mhz=822.3875,
            )
        )

        plan_c = next(plan for plan in response.plan_results if plan.plan_id == "700-C")

        self.assertEqual(plan_c.technical_status, TechnicalStatus.VALID)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.low_mhz, 804.8875)
        self.assertEqual(plan_c.proposed_dvrs_rx_range.high_mhz, 805.0)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.low_mhz, 774.8875)
        self.assertEqual(plan_c.proposed_dvrs_tx_range.high_mhz, 775.0)
        self.assertEqual(plan_c.rule_violations, [])

    def test_active_mobile_windows_limit_plan_validity(self) -> None:
        request = CalculationRequest(
            country=Country.UNITED_STATES,
            mobile_tx_low_mhz=806.0125,
            mobile_tx_high_mhz=818.2125,
            actual_dvrs_tx_mhz=770.0,
            actual_dvrs_rx_mhz=800.0,
        )

        system_summary = self.engine._build_system_summary(request, BandFamily.BAND_800)
        plan_a = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_700] if plan.id == "700-A")
        plan_b = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_700] if plan.id == "700-B")

        result_a = self.engine._evaluate_plan(request, system_summary, plan_a)
        result_b = self.engine._evaluate_plan(request, system_summary, plan_b)

        self.assertEqual(result_a.technical_status, TechnicalStatus.VALID)
        self.assertEqual(result_b.technical_status, TechnicalStatus.INVALID)
        self.assertEqual(result_b.rule_violations[0].code, "MOBILE_TX_OUTSIDE_ACTIVE_PLAN_WINDOW")

    def test_exact_dvrs_frequency_can_pass_with_spacing_note_when_advisory_window_would_fail(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=806.0,
                mobile_tx_high_mhz=807.0,
                actual_dvrs_tx_mhz=855.0,
                actual_dvrs_rx_mhz=810.0,
            )
        )

        plan_b = next(plan for plan in response.plan_results if plan.plan_id == "800-B")
        self.assertEqual(plan_b.technical_status, TechnicalStatus.VALID)
        self.assertTrue(
            any("+/-0.5 MHz window would reduce spacing" in note for note in plan_b.notes)
        )

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
        self.assertIn("supported_mobile_tx_windows", ctx.exception.details)
        self.assertEqual(ctx.exception.rule_violations[0]["code"], "UNSUPPORTED_OR_AMBIGUOUS_BAND")

    def test_spacing_failure_reports_exact_reason(self) -> None:
        request = CalculationRequest(
            country=Country.CANADA,
            mobile_tx_low_mhz=823.0,
            mobile_tx_high_mhz=824.0,
        )

        system_summary = self.engine._build_system_summary(request, BandFamily.BAND_800)
        plan_b_definition = next(plan for plan in TECHNICAL_PLANS[BandFamily.BAND_800] if plan.id == "800-B")
        plan_b = self.engine._evaluate_plan(request, system_summary, plan_b_definition)

        self.assertEqual(plan_b.technical_status, TechnicalStatus.INVALID)
        self.assertIn("Mobile TX range falls outside the plan's supported active mobile TX window", plan_b.failure_reasons[0])
        self.assertNotIn("ordering-guide", plan_b.failure_reasons[0].lower())
        self.assertEqual(plan_b.rule_violations[0].code, "MOBILE_TX_OUTSIDE_ACTIVE_PLAN_WINDOW")

    def test_valid_plan_returns_empty_rule_violations(self) -> None:
        response = self.engine.evaluate(
            CalculationRequest(
                country=Country.UNITED_STATES,
                mobile_tx_low_mhz=810.0,
                mobile_tx_high_mhz=811.0,
                system_band_hint=SystemBandHint.BAND_800_ONLY,
            )
        )

        valid_plan = next(plan for plan in response.plan_results if plan.technical_status == TechnicalStatus.VALID)
        self.assertEqual(valid_plan.rule_violations, [])

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
                agency_name="Metro Fire",
                quote_date="2026-04-09",
                mobile_radio_type="APX",
                control_head_type="O9",
                msu_antenna_type="Roof mount",
            )
        )

        pdf = build_ordering_summary_pdf(response)
        reader = PdfReader(BytesIO(pdf))
        text = reader.pages[0].extract_text()

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertIn("DVRS/VRX1000 SUPPLEMENTAL ORDERING FORM", text)
        self.assertIn("Metro Fire", text)
        self.assertIn("859.6125", text)
        self.assertIn("809.8125", text)

    def test_cli_run_returns_json_payload_for_valid_request(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = run(
                [
                    "--country",
                    "United States",
                    "--mobile-tx-low",
                    "810.0",
                    "--mobile-tx-high",
                    "811.0",
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
        self.assertIn('"rule_violations"', output)

    def test_api_returns_structured_error_for_optional_zero_value(self) -> None:
        app = create_app()
        try:
            from fastapi.testclient import TestClient
            client = TestClient(app)
        except (ImportError, RuntimeError):
            self.skipTest("FastAPI test client is not installed.")
        response = client.post(
            "/v1/evaluate",
            json={
                "country": "United States",
                "mobile_tx_low_mhz": 799.16875,
                "mobile_tx_high_mhz": 804.84375,
                "actual_dvrs_rx_mhz": 0,
            },
        )

        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"]["code"], "INVALID_REQUEST_BODY")
        self.assertEqual(payload["error"]["details"]["field_errors"][0]["field"], "actual_dvrs_rx_mhz")
        self.assertIn("leave it blank instead of entering 0", payload["error"]["details"]["field_errors"][0]["hint"])

    def test_cli_help_describes_arguments_and_response_shape(self) -> None:
        parser = build_parser()
        help_text = parser.format_help()

        self.assertIn("--country", help_text)
        self.assertIn("--mobile-tx-low", help_text)
        self.assertIn("--dvrs-tx", help_text)
        self.assertIn("Returned JSON shape", help_text)
        self.assertIn('"status": "ok" | "error"', help_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

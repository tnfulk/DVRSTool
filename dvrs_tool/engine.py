"""Core DVRS calculation engine."""

from __future__ import annotations

from dataclasses import replace

from .exceptions import InputValidationError, UnsupportedBandError
from .models import (
    BandFamily,
    CalculationRequest,
    CalculationResponse,
    FrequencyRange,
    OrderingSummary,
    PairingSource,
    PlanResult,
    RegulatoryStatus,
    SystemSummary,
    TechnicalPlan,
    TechnicalStatus,
)
from .plan_data import TECHNICAL_PLANS, classify_regulatory_status


class DVRSCalculationEngine:
    """Evaluate Futurecom DVRS in-band planning scenarios."""

    def evaluate(self, request: CalculationRequest) -> CalculationResponse:
        self._validate_request(request)
        band = self._detect_band(request.mobile_tx_low_mhz, request.mobile_tx_high_mhz)
        system_summary = self._build_system_summary(request, band)
        plan_results = [
            self._evaluate_plan(request, system_summary, plan)
            for plan in TECHNICAL_PLANS[band]
        ]
        ordering_summary = self._build_ordering_summary(request, system_summary, plan_results)
        return CalculationResponse(
            request=request,
            system_summary=system_summary,
            plan_results=plan_results,
            ordering_summary=ordering_summary,
        )

    def _validate_request(self, request: CalculationRequest) -> None:
        if request.mobile_tx_low_mhz >= request.mobile_tx_high_mhz:
            raise InputValidationError(
                code="INVALID_MOBILE_TX_RANGE",
                message="Lowest mobile TX must be lower than highest mobile TX.",
                details={
                    "mobile_tx_low_mhz": request.mobile_tx_low_mhz,
                    "mobile_tx_high_mhz": request.mobile_tx_high_mhz,
                },
            )
        if request.mobile_rx_low_mhz is not None and request.mobile_rx_high_mhz is not None:
            if request.mobile_rx_low_mhz >= request.mobile_rx_high_mhz:
                raise InputValidationError(
                    code="INVALID_MOBILE_RX_RANGE",
                    message="Lowest mobile RX must be lower than highest mobile RX.",
                    details={
                        "mobile_rx_low_mhz": request.mobile_rx_low_mhz,
                        "mobile_rx_high_mhz": request.mobile_rx_high_mhz,
                    },
                )
        for field_name in [
            "mobile_tx_low_mhz",
            "mobile_tx_high_mhz",
            "mobile_rx_low_mhz",
            "mobile_rx_high_mhz",
            "actual_licensed_dvrs_tx_low_mhz",
            "actual_licensed_dvrs_tx_high_mhz",
            "actual_licensed_dvrs_rx_low_mhz",
            "actual_licensed_dvrs_rx_high_mhz",
        ]:
            value = getattr(request, field_name)
            if value is not None and value <= 0:
                raise InputValidationError(
                    code="INVALID_FREQUENCY_VALUE",
                    message="Frequencies must be positive MHz values.",
                    details={"field": field_name, "value": value},
                )

    def _detect_band(self, low_mhz: float, high_mhz: float) -> BandFamily:
        candidate_ranges = [
            (BandFamily.BAND_700, 799.0, 805.0),
            (BandFamily.BAND_800, 806.0, 824.0),
            (BandFamily.VHF, 136.0, 174.0),
            (BandFamily.UHF_380, 380.0, 430.0),
            (BandFamily.UHF_450, 450.0, 470.0),
        ]
        matches = [
            band
            for band, band_low, band_high in candidate_ranges
            if low_mhz >= band_low and high_mhz <= band_high
        ]
        if len(matches) != 1:
            raise UnsupportedBandError(
                code="UNSUPPORTED_OR_AMBIGUOUS_BAND",
                message="Mobile TX range does not fit exactly one supported DVRS band family.",
                details={"mobile_tx_low_mhz": low_mhz, "mobile_tx_high_mhz": high_mhz},
            )
        return matches[0]

    def _build_system_summary(self, request: CalculationRequest, band: BandFamily) -> SystemSummary:
        mobile_tx = FrequencyRange(request.mobile_tx_low_mhz, request.mobile_tx_high_mhz)
        warnings: list[str] = []
        pairing_source = PairingSource.UNAVAILABLE
        mobile_rx: FrequencyRange | None = None
        system_tx: FrequencyRange | None = None

        if request.mobile_rx_low_mhz is not None and request.mobile_rx_high_mhz is not None:
            mobile_rx = FrequencyRange(request.mobile_rx_low_mhz, request.mobile_rx_high_mhz)
            system_tx = mobile_rx
            pairing_source = PairingSource.MANUAL_OVERRIDE
            warnings.append("System TX/RX pairing was derived from the manual mobile RX override.")
        elif band == BandFamily.BAND_700:
            mobile_rx = FrequencyRange(
                round(request.mobile_tx_low_mhz - 30.0, 4),
                round(request.mobile_tx_high_mhz - 30.0, 4),
            )
            system_tx = mobile_rx
            pairing_source = PairingSource.DETERMINISTIC
        elif band == BandFamily.BAND_800:
            mobile_rx = FrequencyRange(
                round(request.mobile_tx_low_mhz + 45.0, 4),
                round(request.mobile_tx_high_mhz + 45.0, 4),
            )
            system_tx = mobile_rx
            pairing_source = PairingSource.DETERMINISTIC
        elif band == BandFamily.UHF_450:
            mobile_rx = FrequencyRange(
                round(request.mobile_tx_low_mhz - 5.0, 4),
                round(request.mobile_tx_high_mhz - 5.0, 4),
            )
            system_tx = mobile_rx
            pairing_source = PairingSource.DETERMINISTIC
        else:
            warnings.append(
                "This band does not have a deterministic system pairing in v1. "
                "Provide mobile RX values for duplex-plan validation."
            )

        return SystemSummary(
            detected_band=band,
            mobile_tx_range=mobile_tx,
            mobile_rx_range=mobile_rx,
            system_rx_range=mobile_tx,
            system_tx_range=system_tx,
            pairing_source=pairing_source,
            warnings=warnings,
        )

    def _evaluate_plan(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
    ) -> PlanResult:
        warnings = list(system_summary.warnings)
        notes = list(plan.notes)
        derived_pair_offset = self._derive_pair_offset_from_system(system_summary, plan)

        if plan.requires_mobile_rx_range and system_summary.mobile_rx_range is None:
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=None,
                proposed_dvrs_rx_range=None,
                mount_compatibility=plan.mount_compatibility,
                failure_reasons=["Manual mobile RX input is required for this duplex plan."],
                warnings=warnings,
                notes=notes + ["No proposal computed because duplex pairing could not be inferred safely."],
            )

        proposed_dvrs_passband = min(
            system_summary.mobile_tx_range.width_mhz,
            plan.max_dvrs_passband_mhz,
        )
        if system_summary.mobile_tx_range.width_mhz > plan.max_dvrs_passband_mhz:
            warnings.append(
                "The mobile system TX range is wider than the DVRS passband. "
                f"Only the proposed DVRS TX/RX range was limited to {plan.max_dvrs_passband_mhz:.4f} MHz."
            )

        proposed_rx = self._propose_dvrs_rx(system_summary.mobile_tx_range, plan, proposed_dvrs_passband)
        if proposed_rx is None:
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=None,
                proposed_dvrs_rx_range=None,
                mount_compatibility=plan.mount_compatibility,
                failure_reasons=[
                    "No contiguous DVRS RX window satisfies the minimum separation and allowed-band constraints."
                ],
                warnings=warnings,
                notes=notes,
            )

        proposed_tx = self._derive_tx_from_rx(proposed_rx, plan, derived_pair_offset)
        if proposed_tx is None:
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=None,
                proposed_dvrs_rx_range=proposed_rx,
                mount_compatibility=plan.mount_compatibility,
                failure_reasons=["DVRS TX range could not be derived from the proposed DVRS RX range."],
                warnings=warnings,
                notes=notes,
            )

        if not self._range_within_window(proposed_tx, plan.dvrs_tx_window):
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=proposed_tx,
                proposed_dvrs_rx_range=proposed_rx,
                mount_compatibility=plan.mount_compatibility,
                failure_reasons=["Derived DVRS TX range falls outside the plan's allowed TX window."],
                warnings=warnings,
                notes=notes,
            )

        regulatory_status, confidence, regulatory_reasons = classify_regulatory_status(
            request.country,
            plan.band_family,
            (proposed_tx.low_mhz, proposed_tx.high_mhz),
            (proposed_rx.low_mhz, proposed_rx.high_mhz),
        )

        return PlanResult(
            plan_id=plan.id,
            display_name=plan.display_name,
            technical_status=TechnicalStatus.VALID,
            regulatory_status=regulatory_status,
            confidence=confidence,
            proposed_dvrs_tx_range=proposed_tx,
            proposed_dvrs_rx_range=proposed_rx,
            mount_compatibility=plan.mount_compatibility,
            warnings=warnings,
            regulatory_reasons=regulatory_reasons,
            notes=notes,
        )

    def _propose_dvrs_rx(
        self,
        mobile_tx: FrequencyRange,
        plan: TechnicalPlan,
        requested_passband: float,
    ) -> FrequencyRange | None:
        if plan.dvrs_rx_window is None:
            return None

        window_low, window_high = plan.dvrs_rx_window
        if requested_passband <= 0 or requested_passband > (window_high - window_low):
            return None

        if plan.placement == "below_mobile_tx":
            candidate_high = min(window_high, round(mobile_tx.low_mhz - plan.min_separation_from_mobile_tx_mhz, 4))
            candidate_low = round(candidate_high - requested_passband, 4)
            if candidate_low < window_low:
                return None
            return FrequencyRange(candidate_low, candidate_high)

        if plan.placement == "above_mobile_tx":
            candidate_low = max(window_low, round(mobile_tx.high_mhz + plan.min_separation_from_mobile_tx_mhz, 4))
            candidate_high = round(candidate_low + requested_passband, 4)
            if candidate_high > window_high:
                return None
            return FrequencyRange(candidate_low, candidate_high)

        return None

    def _derive_tx_from_rx(
        self,
        proposed_rx: FrequencyRange,
        plan: TechnicalPlan,
        derived_pair_offset: float | None,
    ) -> FrequencyRange | None:
        if plan.dvrs_mode == "simplex":
            return replace(proposed_rx)
        effective_offset = plan.pair_offset_mhz if plan.pair_offset_mhz is not None else derived_pair_offset
        if effective_offset is None:
            return None

        if plan.pair_direction == "tx_below_rx":
            return FrequencyRange(
                round(proposed_rx.low_mhz - effective_offset, 4),
                round(proposed_rx.high_mhz - effective_offset, 4),
            )
        if plan.pair_direction in {"tx_above_rx", "manual"}:
            return FrequencyRange(
                round(proposed_rx.low_mhz + effective_offset, 4),
                round(proposed_rx.high_mhz + effective_offset, 4),
            )
        return None

    def _derive_pair_offset_from_system(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
    ) -> float | None:
        if plan.pair_offset_mhz is not None:
            return plan.pair_offset_mhz
        if system_summary.system_tx_range is None:
            return None

        low_offset = round(
            system_summary.system_tx_range.low_mhz - system_summary.system_rx_range.low_mhz,
            4,
        )
        high_offset = round(
            system_summary.system_tx_range.high_mhz - system_summary.system_rx_range.high_mhz,
            4,
        )
        if low_offset != high_offset:
            return None
        return abs(low_offset)

    def _range_within_window(
        self,
        frequency_range: FrequencyRange,
        window: tuple[float, float] | None,
    ) -> bool:
        if window is None:
            return True
        return frequency_range.low_mhz >= window[0] and frequency_range.high_mhz <= window[1]

    def _build_ordering_summary(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        plan_results: list[PlanResult],
    ) -> OrderingSummary:
        best_plan = next(
            (
                plan
                for plan in plan_results
                if plan.technical_status == TechnicalStatus.VALID
                and plan.regulatory_status != RegulatoryStatus.LIKELY_NOT_LICENSABLE
            ),
            next((plan for plan in plan_results if plan.technical_status == TechnicalStatus.VALID), None),
        )

        actual_tx = self._optional_range(
            request.actual_licensed_dvrs_tx_low_mhz,
            request.actual_licensed_dvrs_tx_high_mhz,
        )
        actual_rx = self._optional_range(
            request.actual_licensed_dvrs_rx_low_mhz,
            request.actual_licensed_dvrs_rx_high_mhz,
        )

        notes = []
        if request.agency_notes:
            notes.append(request.agency_notes)
        if best_plan is None:
            notes.append("No technically valid standard plan proposal was produced.")
        else:
            notes.append(f"Best preliminary standard plan: {best_plan.display_name}.")

        return OrderingSummary(
            system_tx_range=system_summary.system_tx_range,
            system_rx_range=system_summary.system_rx_range,
            proposed_dvrs_tx_range=best_plan.proposed_dvrs_tx_range if best_plan else None,
            proposed_dvrs_rx_range=best_plan.proposed_dvrs_rx_range if best_plan else None,
            actual_licensed_dvrs_tx_range=actual_tx,
            actual_licensed_dvrs_rx_range=actual_rx,
            notes=notes,
        )

    def _optional_range(self, low_mhz: float | None, high_mhz: float | None) -> FrequencyRange | None:
        if low_mhz is None or high_mhz is None:
            return None
        return FrequencyRange(low_mhz, high_mhz)

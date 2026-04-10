"""Core DVRS calculation engine."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, InvalidOperation

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
    RuleViolation,
    SystemBandHint,
    SystemSummary,
    TechnicalPlan,
    TechnicalStatus,
)
from .plan_data import TECHNICAL_PLANS, classify_regulatory_status


class DVRSCalculationEngine:
    """Evaluate Futurecom DVRS in-band planning scenarios."""

    MAX_INPUT_DECIMAL_PLACES = 5
    ACTUAL_DVRS_RANGE_HALF_WIDTH_MHZ = 0.5

    def evaluate(self, request: CalculationRequest) -> CalculationResponse:
        self._validate_request(request)
        system_band = self._resolve_system_band(request)
        system_summary = self._build_system_summary(request, system_band)
        candidate_plans = self._candidate_plans(request, system_band)
        plan_results = [
            self._evaluate_plan(request, self._build_plan_system_summary(request, system_band, plan), plan)
            for plan in candidate_plans
        ]
        ordering_summary = self._build_ordering_summary(request, system_summary, plan_results)
        return CalculationResponse(
            request=request,
            system_summary=system_summary,
            plan_results=plan_results,
            ordering_summary=ordering_summary,
        )

    def _validate_request(self, request: CalculationRequest) -> None:
        if request.system_band_hint == SystemBandHint.BAND_700_AND_800:
            self._validate_required_range(
                "mobile_tx_700_low_mhz",
                "mobile_tx_700_high_mhz",
                request.mobile_tx_700_low_mhz,
                request.mobile_tx_700_high_mhz,
                "700 MHz mobile TX",
            )
            self._validate_required_range(
                "mobile_tx_800_low_mhz",
                "mobile_tx_800_high_mhz",
                request.mobile_tx_800_low_mhz,
                request.mobile_tx_800_high_mhz,
                "800 MHz mobile TX",
            )
        else:
            self._validate_required_range(
                "mobile_tx_low_mhz",
                "mobile_tx_high_mhz",
                request.mobile_tx_low_mhz,
                request.mobile_tx_high_mhz,
                "mobile TX",
            )

        if request.mobile_rx_low_mhz is not None and request.mobile_rx_high_mhz is not None:
            if request.mobile_rx_low_mhz >= request.mobile_rx_high_mhz:
                raise InputValidationError(
                    code="INVALID_MOBILE_RX_RANGE",
                    message="Lowest mobile RX must be lower than highest mobile RX.",
                    details={
                        "mobile_rx_low_mhz": request.mobile_rx_low_mhz,
                        "mobile_rx_high_mhz": request.mobile_rx_high_mhz,
                        "rule": "mobile_rx_low_mhz < mobile_rx_high_mhz",
                    },
                    rule_violations=[
                        {
                            "code": "INVALID_MOBILE_RX_RANGE",
                            "message": "Lowest mobile RX must be lower than highest mobile RX.",
                            "details": {
                                "mobile_rx_low_mhz": request.mobile_rx_low_mhz,
                                "mobile_rx_high_mhz": request.mobile_rx_high_mhz,
                                "rule": "mobile_rx_low_mhz < mobile_rx_high_mhz",
                            },
                        }
                    ],
                )
        for field_name in [
            "mobile_tx_low_mhz",
            "mobile_tx_high_mhz",
            "mobile_tx_700_low_mhz",
            "mobile_tx_700_high_mhz",
            "mobile_tx_800_low_mhz",
            "mobile_tx_800_high_mhz",
            "mobile_rx_low_mhz",
            "mobile_rx_high_mhz",
            "actual_dvrs_tx_mhz",
            "actual_dvrs_rx_mhz",
        ]:
            value = getattr(request, field_name)
            if value is not None and value <= 0:
                raise InputValidationError(
                    code="INVALID_FREQUENCY_VALUE",
                    message="Frequencies must be positive MHz values.",
                    details={"field": field_name, "value": value, "rule": "value > 0"},
                    rule_violations=[
                        {
                            "code": "INVALID_FREQUENCY_VALUE",
                            "message": "Frequencies must be positive MHz values.",
                            "details": {"field": field_name, "value": value, "rule": "value > 0"},
                        }
                    ],
                )
            if value is not None and self._decimal_places(value) > self.MAX_INPUT_DECIMAL_PLACES:
                raise InputValidationError(
                    code="TOO_MANY_DECIMAL_PLACES",
                    message=(
                        f"Frequency field '{field_name}' supports at most "
                        f"{self.MAX_INPUT_DECIMAL_PLACES} decimal places."
                    ),
                    details={
                        "field": field_name,
                        "value": value,
                        "decimal_places": self._decimal_places(value),
                        "max_decimal_places": self.MAX_INPUT_DECIMAL_PLACES,
                    },
                    rule_violations=[
                        {
                            "code": "TOO_MANY_DECIMAL_PLACES",
                            "message": (
                                f"Frequency field '{field_name}' supports at most "
                                f"{self.MAX_INPUT_DECIMAL_PLACES} decimal places."
                            ),
                            "details": {
                                "field": field_name,
                                "value": value,
                                "decimal_places": self._decimal_places(value),
                                "max_decimal_places": self.MAX_INPUT_DECIMAL_PLACES,
                            },
                        }
                    ],
                )

    def _validate_required_range(
        self,
        low_field: str,
        high_field: str,
        low_value: float | None,
        high_value: float | None,
        label: str,
    ) -> None:
        if low_value is None or high_value is None:
            raise InputValidationError(
                code="MISSING_REQUIRED_FREQUENCY_RANGE",
                message=f"Both low and high values are required for {label}.",
                details={
                    "low_field": low_field,
                    "high_field": high_field,
                    "label": label,
                    "rule": "both range endpoints must be provided",
                },
                rule_violations=[
                    {
                        "code": "MISSING_REQUIRED_FREQUENCY_RANGE",
                        "message": f"Both low and high values are required for {label}.",
                        "details": {
                            "low_field": low_field,
                            "high_field": high_field,
                            "label": label,
                            "rule": "both range endpoints must be provided",
                        },
                    }
                ],
            )
        if low_value >= high_value:
            raise InputValidationError(
                code="INVALID_MOBILE_TX_RANGE",
                message=f"Lowest {label} must be lower than highest {label}.",
                details={
                    low_field: low_value,
                    high_field: high_value,
                    "rule": f"{low_field} < {high_field}",
                },
                rule_violations=[
                    {
                        "code": "INVALID_MOBILE_TX_RANGE",
                        "message": f"Lowest {label} must be lower than highest {label}.",
                        "details": {
                            low_field: low_value,
                            high_field: high_value,
                            "rule": f"{low_field} < {high_field}",
                        },
                    }
                ],
            )

    def _resolve_system_band(self, request: CalculationRequest) -> BandFamily:
        if request.system_band_hint == SystemBandHint.BAND_700_AND_800:
            return BandFamily.BAND_700_800
        if request.system_band_hint == SystemBandHint.BAND_800_ONLY:
            return BandFamily.BAND_800
        if request.mobile_tx_low_mhz is None or request.mobile_tx_high_mhz is None:
            raise UnsupportedBandError(
                code="UNSUPPORTED_OR_AMBIGUOUS_BAND",
                message="Mobile TX range is required unless a mixed 700 and 800 system is selected.",
                details={
                    "mobile_tx_low_mhz": request.mobile_tx_low_mhz,
                    "mobile_tx_high_mhz": request.mobile_tx_high_mhz,
                },
                rule_violations=[
                    {
                        "code": "UNSUPPORTED_OR_AMBIGUOUS_BAND",
                        "message": "Mobile TX range is required unless a mixed 700 and 800 system is selected.",
                        "details": {
                            "mobile_tx_low_mhz": request.mobile_tx_low_mhz,
                            "mobile_tx_high_mhz": request.mobile_tx_high_mhz,
                        },
                    }
                ],
            )
        return self._detect_band(request.mobile_tx_low_mhz, request.mobile_tx_high_mhz)

    def _detect_band(self, low_mhz: float, high_mhz: float) -> BandFamily:
        if low_mhz >= 799.0 and high_mhz <= 805.0:
            raise UnsupportedBandError(
                code="UNSUPPORTED_700_ONLY_SYSTEM",
                message="Standard configuration plans do not support systems that only have 700 MHz channels.",
                details={
                    "mobile_tx_low_mhz": low_mhz,
                    "mobile_tx_high_mhz": high_mhz,
                    "supported_models": ["800 only", "700 and 800"],
                    "rule": "700-only systems are not standard-plan candidates",
                },
                rule_violations=[
                    {
                        "code": "UNSUPPORTED_700_ONLY_SYSTEM",
                        "message": "Standard configuration plans do not support systems that only have 700 MHz channels.",
                        "details": {
                            "mobile_tx_low_mhz": low_mhz,
                            "mobile_tx_high_mhz": high_mhz,
                            "supported_models": ["800 only", "700 and 800"],
                            "rule": "700-only systems are not standard-plan candidates",
                        },
                    }
                ],
            )

        if low_mhz >= 806.0 and high_mhz <= 824.0:
            return BandFamily.BAND_800

        raise UnsupportedBandError(
            code="UNSUPPORTED_OR_AMBIGUOUS_BAND",
            message="Mobile TX range does not fit exactly one supported DVRS band family.",
            details={
                "mobile_tx_low_mhz": low_mhz,
                "mobile_tx_high_mhz": high_mhz,
                "supported_mobile_tx_windows": {
                    "800 MHz": [806.0, 824.0],
                },
            },
            rule_violations=[
                {
                    "code": "UNSUPPORTED_OR_AMBIGUOUS_BAND",
                    "message": "Mobile TX range does not fit exactly one supported DVRS band family.",
                    "details": {
                        "mobile_tx_low_mhz": low_mhz,
                        "mobile_tx_high_mhz": high_mhz,
                        "supported_mobile_tx_windows": {
                            "800 MHz": [806.0, 824.0],
                        },
                    },
                }
            ],
        )

    def _build_system_summary(self, request: CalculationRequest, band: BandFamily) -> SystemSummary:
        if band == BandFamily.BAND_700_800:
            mobile_tx_700 = FrequencyRange(request.mobile_tx_700_low_mhz, request.mobile_tx_700_high_mhz)
            mobile_tx_800 = FrequencyRange(request.mobile_tx_800_low_mhz, request.mobile_tx_800_high_mhz)
            system_tx_700 = FrequencyRange(
                self._round_freq(request.mobile_tx_700_low_mhz - 30.0),
                self._round_freq(request.mobile_tx_700_high_mhz - 30.0),
            )
            system_tx_800 = FrequencyRange(
                self._round_freq(request.mobile_tx_800_low_mhz + 45.0),
                self._round_freq(request.mobile_tx_800_high_mhz + 45.0),
            )
            mobile_tx = FrequencyRange(
                min(request.mobile_tx_700_low_mhz, request.mobile_tx_800_low_mhz),
                max(request.mobile_tx_700_high_mhz, request.mobile_tx_800_high_mhz),
            )
        else:
            mobile_tx = FrequencyRange(request.mobile_tx_low_mhz, request.mobile_tx_high_mhz)
            mobile_tx_700 = None
            mobile_tx_800 = None
            system_tx_700 = None
            system_tx_800 = None
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
                self._round_freq(request.mobile_tx_low_mhz - 30.0),
                self._round_freq(request.mobile_tx_high_mhz - 30.0),
            )
            system_tx = mobile_rx
            pairing_source = PairingSource.DETERMINISTIC
        elif band == BandFamily.BAND_800:
            mobile_rx = FrequencyRange(
                self._round_freq(request.mobile_tx_low_mhz + 45.0),
                self._round_freq(request.mobile_tx_high_mhz + 45.0),
            )
            system_tx = mobile_rx
            pairing_source = PairingSource.DETERMINISTIC
        elif band == BandFamily.BAND_700_800:
            pairing_source = PairingSource.DETERMINISTIC
            warnings.append(
                "Mixed 700 and 800 system selected. Plan evaluation uses the dedicated 700 MHz or 800 MHz mobile TX range for each candidate plan."
            )

        return SystemSummary(
            detected_band=band,
            mobile_tx_range=mobile_tx,
            mobile_rx_range=mobile_rx,
            system_rx_range=mobile_tx,
            system_tx_range=system_tx,
            pairing_source=pairing_source,
            mobile_tx_700_range=mobile_tx_700,
            system_rx_700_range=mobile_tx_700,
            system_tx_700_range=system_tx_700,
            mobile_tx_800_range=mobile_tx_800,
            system_rx_800_range=mobile_tx_800,
            system_tx_800_range=system_tx_800,
            warnings=warnings,
        )

    def _build_plan_system_summary(
        self,
        request: CalculationRequest,
        system_band: BandFamily,
        plan: TechnicalPlan,
    ) -> SystemSummary:
        derived_pair_request = self._request_with_plan_specific_pairing(request, plan)
        if derived_pair_request is not request:
            system_summary = self._build_system_summary(derived_pair_request, plan.band_family)
            system_summary.pairing_source = PairingSource.DETERMINISTIC
            system_summary.warnings = [
                warning
                for warning in system_summary.warnings
                if "manual mobile RX override" not in warning.lower()
            ]
            return system_summary

        if system_band != BandFamily.BAND_700_800 or plan.band_family not in {BandFamily.BAND_700, BandFamily.BAND_800}:
            return self._build_system_summary(
                request,
                plan.band_family if system_band == BandFamily.BAND_700_800 else system_band,
            )

        if plan.band_family == BandFamily.BAND_700:
            plan_request = replace(
                request,
                mobile_tx_low_mhz=request.mobile_tx_700_low_mhz,
                mobile_tx_high_mhz=request.mobile_tx_700_high_mhz,
            )
            return self._build_system_summary(plan_request, BandFamily.BAND_700)

        plan_request = replace(
            request,
            mobile_tx_low_mhz=request.mobile_tx_800_low_mhz,
            mobile_tx_high_mhz=request.mobile_tx_800_high_mhz,
        )
        return self._build_system_summary(plan_request, BandFamily.BAND_800)

    def _request_with_plan_specific_pairing(
        self,
        request: CalculationRequest,
        plan: TechnicalPlan,
    ) -> CalculationRequest:
        return request

    def _build_active_window_summary(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
    ) -> SystemSummary:
        if request.system_band_hint != SystemBandHint.BAND_700_AND_800:
            return system_summary

        if plan.band_family == BandFamily.BAND_700:
            plan_request = replace(
                request,
                mobile_tx_low_mhz=request.mobile_tx_700_low_mhz,
                mobile_tx_high_mhz=request.mobile_tx_700_high_mhz,
            )
            return self._build_system_summary(plan_request, BandFamily.BAND_700)

        if plan.band_family == BandFamily.BAND_800:
            plan_request = replace(
                request,
                mobile_tx_low_mhz=request.mobile_tx_800_low_mhz,
                mobile_tx_high_mhz=request.mobile_tx_800_high_mhz,
            )
            return self._build_system_summary(plan_request, BandFamily.BAND_800)

        return system_summary

    def _evaluate_plan(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
    ) -> PlanResult:
        candidate_results = [
            self._evaluate_plan_variant(request, system_summary, plan, variant_label, variant_plan)
            for variant_label, variant_plan in self._plan_variants(plan)
        ]
        selected_result = self._select_best_plan_result(request, plan, candidate_results)
        selected_result.mobile_tx_range = system_summary.mobile_tx_range
        selected_result.mobile_rx_range = system_summary.mobile_rx_range
        selected_result.system_tx_range = system_summary.system_tx_range
        selected_result.system_rx_range = system_summary.system_rx_range
        return selected_result

    def _evaluate_plan_variant(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        variant_label: str,
        variant_plan: TechnicalPlan,
    ) -> PlanResult:
        warnings = list(system_summary.warnings)
        notes = list(variant_plan.notes)
        derived_pair_offset = self._derive_pair_offset_from_system(system_summary, variant_plan)

        active_window_violation = self._validate_active_mobile_windows(
            request,
            system_summary,
            plan,
            variant_label,
            variant_plan,
        )
        if active_window_violation is not None:
            preview_rx = self._preview_plan_rx_range(variant_plan)
            preview_tx = self._preview_plan_tx_range(variant_plan, preview_rx, derived_pair_offset)
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=preview_tx,
                proposed_dvrs_rx_range=preview_rx,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[active_window_violation.message],
                rule_violations=[active_window_violation],
                warnings=warnings,
                notes=notes,
            )

        if variant_plan.requires_mobile_rx_range and system_summary.mobile_rx_range is None:
            violation = RuleViolation(
                code="MANUAL_MOBILE_RX_REQUIRED",
                message="Manual mobile RX input is required for this duplex plan.",
                details={"plan_id": plan.id, "band_family": plan.band_family.value, "variant": variant_label},
            )
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=None,
                proposed_dvrs_rx_range=None,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[violation.message],
                rule_violations=[violation],
                warnings=warnings,
                notes=notes + ["No proposal computed because duplex pairing could not be inferred safely."],
            )

        proposed_dvrs_passband = min(
            system_summary.mobile_tx_range.width_mhz,
            variant_plan.max_dvrs_passband_mhz,
        )

        proposed_rx = self._propose_dvrs_rx(system_summary, variant_plan, proposed_dvrs_passband)
        if proposed_rx is None:
            violation = RuleViolation(
                code="NO_VALID_DVRS_RX_WINDOW",
                message=self._build_no_rx_solution_reason(system_summary.mobile_tx_range, variant_plan, proposed_dvrs_passband),
                details={
                    "plan_id": plan.id,
                    "variant": variant_label,
                    "input_mobile_tx_range": {
                        "low_mhz": system_summary.mobile_tx_range.low_mhz,
                        "high_mhz": system_summary.mobile_tx_range.high_mhz,
                    },
                    "dvrs_rx_window": self._window_details(variant_plan.dvrs_rx_window),
                    "required_min_separation_mhz": variant_plan.min_separation_from_mobile_tx_mhz,
                    "requested_dvrs_passband_mhz": proposed_dvrs_passband,
                },
            )
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=None,
                proposed_dvrs_rx_range=None,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[violation.message],
                rule_violations=[violation],
                warnings=warnings,
                notes=notes,
            )

        proposed_tx = self._propose_dvrs_tx(proposed_rx, variant_plan, derived_pair_offset)
        if proposed_tx is None:
            violation = RuleViolation(
                code="UNABLE_TO_DERIVE_DVRS_TX",
                message=(
                    "DVRS TX range could not be derived from the proposed DVRS RX range because this plan "
                    "does not define a fixed offset and no consistent offset could be inferred from the system pairing."
                ),
                details={
                    "plan_id": plan.id,
                    "variant": variant_label,
                    "proposed_dvrs_rx_range": {
                        "low_mhz": proposed_rx.low_mhz,
                        "high_mhz": proposed_rx.high_mhz,
                    },
                    "derived_pair_offset_mhz": derived_pair_offset,
                    "pair_direction": variant_plan.pair_direction,
                },
            )
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=None,
                proposed_dvrs_rx_range=proposed_rx,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[violation.message],
                rule_violations=[violation],
                warnings=warnings,
                notes=notes,
            )

        proposed_tx, proposed_rx = self._apply_actual_dvrs_frequencies(
            request,
            variant_plan,
            proposed_tx,
            proposed_rx,
            widened=False,
        )

        actual_setup_violation = self._validate_actual_frequency_setup(
            system_summary,
            plan,
            variant_label,
            variant_plan,
            proposed_tx,
            proposed_rx,
            derived_pair_offset,
        )
        if actual_setup_violation is not None:
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=proposed_tx,
                proposed_dvrs_rx_range=proposed_rx,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[actual_setup_violation.message],
                rule_violations=[actual_setup_violation],
                warnings=warnings,
                notes=notes,
            )

        actual_spacing_note = self._build_actual_frequency_spacing_note(
            request,
            system_summary,
            plan,
            variant_label,
            variant_plan,
            derived_pair_offset,
            proposed_tx,
            proposed_rx,
        )
        if actual_spacing_note is not None:
            notes.append(actual_spacing_note)

        mobile_rx_spacing_violation = self._validate_mobile_rx_spacing(system_summary, variant_plan, proposed_tx)
        if mobile_rx_spacing_violation is not None:
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=proposed_tx,
                proposed_dvrs_rx_range=proposed_rx,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[mobile_rx_spacing_violation.message],
                rule_violations=[mobile_rx_spacing_violation],
                warnings=warnings,
                notes=notes,
            )

        if not self._range_within_window(proposed_tx, variant_plan.dvrs_tx_window):
            violation = RuleViolation(
                code="DVRS_TX_OUTSIDE_ALLOWED_WINDOW",
                message=(
                    "Derived DVRS TX range falls outside the plan's allowed TX window. "
                    f"Derived TX={self._format_range(proposed_tx)}; allowed TX window={self._format_window(variant_plan.dvrs_tx_window)}."
                ),
                details={
                    "plan_id": plan.id,
                    "variant": variant_label,
                    "derived_dvrs_tx_range": {
                        "low_mhz": proposed_tx.low_mhz,
                        "high_mhz": proposed_tx.high_mhz,
                    },
                    "allowed_dvrs_tx_window": self._window_details(variant_plan.dvrs_tx_window),
                },
            )
            return PlanResult(
                plan_id=plan.id,
                display_name=plan.display_name,
                technical_status=TechnicalStatus.INVALID,
                regulatory_status=RegulatoryStatus.NOT_EVALUATED,
                confidence=0.0,
                proposed_dvrs_tx_range=proposed_tx,
                proposed_dvrs_rx_range=proposed_rx,
                mount_compatibility=variant_plan.mount_compatibility,
                failure_reasons=[violation.message],
                rule_violations=[violation],
                warnings=warnings,
                notes=notes,
            )

        regulatory_status, confidence, regulatory_reasons = classify_regulatory_status(
            request.country,
            variant_plan.band_family,
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
            mount_compatibility=variant_plan.mount_compatibility,
            rule_violations=[],
            warnings=warnings,
            regulatory_reasons=regulatory_reasons,
            notes=notes,
        )

    def _plan_variants(self, plan: TechnicalPlan) -> list[tuple[str, TechnicalPlan]]:
        return [("native", plan)]

    def _candidate_plans(
        self,
        request: CalculationRequest,
        system_band: BandFamily,
    ) -> list[TechnicalPlan]:
        if request.actual_dvrs_tx_mhz is not None or request.actual_dvrs_rx_mhz is not None:
            matching_plans = [
                plan
                for plans in TECHNICAL_PLANS.values()
                for plan in plans
                if self._native_plan_matches_actual_dvrs(plan, request)
            ]
            hinted_plans = self._plans_for_system_band_hint(request.system_band_hint)
            if hinted_plans is not None:
                hinted_ids = {plan.id for plan in hinted_plans}
                filtered_matches = [plan for plan in matching_plans if plan.id in hinted_ids]
                if filtered_matches:
                    return filtered_matches
            if matching_plans:
                return matching_plans

        hinted_plans = self._plans_for_system_band_hint(request.system_band_hint)
        if hinted_plans is not None:
            return hinted_plans

        if system_band == BandFamily.BAND_800:
            return self._plans_for_system_band_hint(SystemBandHint.BAND_800_ONLY) or []

        return list(TECHNICAL_PLANS[system_band])

    def _plans_for_system_band_hint(
        self,
        system_band_hint: SystemBandHint | None,
    ) -> list[TechnicalPlan] | None:
        if system_band_hint is None:
            return None

        if system_band_hint == SystemBandHint.BAND_800_ONLY:
            eight_hundred_only_plan_ids = {"700-A", "800-C"}
            return [
                plan
                for family in (BandFamily.BAND_700, BandFamily.BAND_800)
                for plan in TECHNICAL_PLANS[family]
                if plan.id in eight_hundred_only_plan_ids
            ]

        if system_band_hint == SystemBandHint.BAND_700_AND_800:
            mixed_plan_ids = {"700-B", "700-C", "800-A1", "800-A2", "800-B"}
            return [
                plan
                for family in (BandFamily.BAND_700, BandFamily.BAND_800)
                for plan in TECHNICAL_PLANS[family]
                if plan.id in mixed_plan_ids
            ]

        return None

    def _native_plan_matches_actual_dvrs(
        self,
        plan: TechnicalPlan,
        request: CalculationRequest,
    ) -> bool:
        actual_tx = self._frequency_point_range(request.actual_dvrs_tx_mhz)
        actual_rx = self._frequency_point_range(request.actual_dvrs_rx_mhz)

        if actual_tx is not None and not self._range_within_window(actual_tx, plan.dvrs_tx_window):
            return False
        if actual_rx is not None and not self._range_within_window(actual_rx, plan.dvrs_rx_window):
            return False

        if actual_tx is not None and plan.fixed_dvrs_tx_range is not None:
            if not self._range_within_window(actual_tx, plan.fixed_dvrs_tx_range):
                return False
        if actual_rx is not None and plan.fixed_dvrs_rx_range is not None:
            if not self._range_within_window(actual_rx, plan.fixed_dvrs_rx_range):
                return False

        if actual_tx is None or actual_rx is None:
            return True

        if plan.dvrs_mode == "simplex":
            return actual_tx.low_mhz == actual_rx.low_mhz and actual_tx.high_mhz == actual_rx.high_mhz

        if plan.pair_offset_mhz is None:
            return True

        if plan.pair_direction == "tx_below_rx":
            delta = self._round_freq(actual_rx.low_mhz - actual_tx.low_mhz)
        else:
            delta = self._round_freq(actual_tx.low_mhz - actual_rx.low_mhz)
        return delta == plan.pair_offset_mhz

    def _build_interop_variant(self, plan: TechnicalPlan) -> TechnicalPlan | None:
        if plan.band_family == BandFamily.BAND_700:
            return replace(
                plan,
                dvrs_rx_window=(806.0, 824.0),
                dvrs_tx_window=(851.0, 869.0),
                pair_offset_mhz=45.0,
                pair_direction="tx_above_rx",
                max_dvrs_passband_mhz=1.0,
                active_mobile_tx_window=None,
                active_mobile_rx_window=None,
                fixed_dvrs_tx_range=None,
                fixed_dvrs_rx_range=None,
                notes=list(plan.notes)
                + [
                    "700/800 interoperability profile enabled: this plan may also place DVRS RX in 806-824 MHz and DVRS TX in 851-869 MHz using a 45 MHz TX-above-RX pairing."
                ],
            )
        if plan.band_family == BandFamily.BAND_800:
            return replace(
                plan,
                dvrs_rx_window=(799.0, 805.0),
                dvrs_tx_window=(769.0, 775.0),
                pair_offset_mhz=30.0,
                pair_direction="tx_below_rx",
                max_dvrs_passband_mhz=1.0,
                active_mobile_tx_window=None,
                active_mobile_rx_window=None,
                fixed_dvrs_tx_range=None,
                fixed_dvrs_rx_range=None,
                notes=list(plan.notes)
                + [
                    "700/800 interoperability profile enabled: this plan may also place DVRS RX in 799-805 MHz and DVRS TX in 769-775 MHz using a 30 MHz TX-below-RX pairing."
                ],
            )
        return None

    def _select_best_plan_result(
        self,
        request: CalculationRequest,
        plan: TechnicalPlan,
        candidate_results: list[PlanResult],
    ) -> PlanResult:
        matching_actual_results = [
            result
            for result, (_, variant_plan) in zip(candidate_results, self._plan_variants(plan))
            if self._variant_matches_actual_licensed(request, variant_plan)
        ]
        valid_matching = [
            result for result in matching_actual_results if result.technical_status == TechnicalStatus.VALID
        ]
        if valid_matching:
            return valid_matching[0]

        valid_results = [
            result for result in candidate_results if result.technical_status == TechnicalStatus.VALID
        ]
        if valid_results:
            return valid_results[0]

        if matching_actual_results:
            return matching_actual_results[0]
        return candidate_results[0]

    def _variant_matches_actual_licensed(
        self,
        request: CalculationRequest,
        plan: TechnicalPlan,
    ) -> bool:
        actual_tx = self._frequency_point_range(request.actual_dvrs_tx_mhz)
        actual_rx = self._frequency_point_range(request.actual_dvrs_rx_mhz)

        tx_matches = actual_tx is None or self._range_within_window(actual_tx, plan.dvrs_tx_window)
        rx_matches = actual_rx is None or self._range_within_window(actual_rx, plan.dvrs_rx_window)
        return tx_matches and rx_matches

    def _validate_active_mobile_windows(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        base_plan: TechnicalPlan,
        variant_label: str,
        plan: TechnicalPlan,
    ) -> RuleViolation | None:
        active_summary = self._build_active_window_summary(request, system_summary, plan)

        if (
            plan.active_mobile_tx_window is not None
            and not self._range_within_window(active_summary.mobile_tx_range, plan.active_mobile_tx_window)
        ):
            return RuleViolation(
                code="MOBILE_TX_OUTSIDE_ACTIVE_PLAN_WINDOW",
                message=(
                    "Mobile TX range falls outside the plan's supported active mobile TX window. "
                    f"Mobile TX={self._format_range(active_summary.mobile_tx_range)}; "
                    f"allowed window={self._format_window(plan.active_mobile_tx_window)}."
                ),
                details={
                    "plan_id": base_plan.id,
                    "variant": variant_label,
                    "mobile_tx_range": {
                        "low_mhz": active_summary.mobile_tx_range.low_mhz,
                        "high_mhz": active_summary.mobile_tx_range.high_mhz,
                    },
                    "active_mobile_tx_window": self._window_details(plan.active_mobile_tx_window),
                },
            )

        if active_summary.mobile_rx_range is None or plan.active_mobile_rx_window is None:
            return None

        if self._range_within_window(active_summary.mobile_rx_range, plan.active_mobile_rx_window):
            return None

        return RuleViolation(
            code="MOBILE_RX_OUTSIDE_ACTIVE_PLAN_WINDOW",
            message=(
                "Mobile RX range falls outside the plan's supported active mobile RX window. "
                f"Mobile RX={self._format_range(active_summary.mobile_rx_range)}; "
                f"allowed window={self._format_window(plan.active_mobile_rx_window)}."
            ),
            details={
                "plan_id": base_plan.id,
                "variant": variant_label,
                "mobile_rx_range": {
                    "low_mhz": active_summary.mobile_rx_range.low_mhz,
                    "high_mhz": active_summary.mobile_rx_range.high_mhz,
                },
                "active_mobile_rx_window": self._window_details(plan.active_mobile_rx_window),
            },
        )

    def _propose_dvrs_rx(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        requested_passband: float,
    ) -> FrequencyRange | None:
        if plan.fixed_dvrs_rx_range is not None:
            relation_options = [None]
            if system_summary.mobile_rx_range is not None:
                relation_options = ["tx_before_mobile_rx", "tx_after_mobile_rx"]

            best_candidate: FrequencyRange | None = None
            best_width = -1.0
            for relation in relation_options:
                candidate = self._solve_feasible_rx_interval(
                    system_summary,
                    plan,
                    plan.fixed_dvrs_rx_range,
                    relation,
                )
                if candidate is None:
                    continue
                if candidate.width_mhz > best_width:
                    best_candidate = candidate
                    best_width = candidate.width_mhz
            return best_candidate

        if plan.dvrs_rx_window is None:
            return None

        window_low, window_high = plan.dvrs_rx_window
        if requested_passband <= 0:
            return None

        relation_options = [None]
        if system_summary.mobile_rx_range is not None:
            relation_options = ["tx_before_mobile_rx", "tx_after_mobile_rx"]

        best_candidate: FrequencyRange | None = None
        best_width = -1.0
        for relation in relation_options:
            candidate = self._solve_candidate_rx_range(system_summary, plan, requested_passband, relation)
            if candidate is None:
                continue
            if candidate.width_mhz > best_width:
                best_candidate = candidate
                best_width = candidate.width_mhz

        return best_candidate

    def _propose_dvrs_tx(
        self,
        proposed_rx: FrequencyRange,
        plan: TechnicalPlan,
        derived_pair_offset: float | None,
    ) -> FrequencyRange | None:
        return self._derive_tx_from_rx(proposed_rx, plan, derived_pair_offset)

    def _preview_plan_rx_range(self, plan: TechnicalPlan) -> FrequencyRange | None:
        if plan.fixed_dvrs_rx_range is not None:
            return FrequencyRange(plan.fixed_dvrs_rx_range[0], plan.fixed_dvrs_rx_range[1])
        if plan.dvrs_rx_window is not None:
            return FrequencyRange(plan.dvrs_rx_window[0], plan.dvrs_rx_window[1])
        return None

    def _preview_plan_tx_range(
        self,
        plan: TechnicalPlan,
        preview_rx: FrequencyRange | None,
        derived_pair_offset: float | None,
    ) -> FrequencyRange | None:
        if plan.fixed_dvrs_tx_range is not None:
            return FrequencyRange(plan.fixed_dvrs_tx_range[0], plan.fixed_dvrs_tx_range[1])
        if preview_rx is not None:
            return self._derive_tx_from_rx(preview_rx, plan, derived_pair_offset)
        if plan.dvrs_tx_window is not None:
            return FrequencyRange(plan.dvrs_tx_window[0], plan.dvrs_tx_window[1])
        return None

    def _solve_candidate_rx_range(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        requested_passband: float,
        tx_mobile_rx_relation: str | None,
    ) -> FrequencyRange | None:
        if plan.dvrs_rx_window is None:
            return None

        a_low = plan.dvrs_rx_window[0]
        b_high = plan.dvrs_rx_window[1]
        mobile_tx = system_summary.mobile_tx_range

        if plan.placement == "below_mobile_tx":
            b_high = min(
                b_high,
                self._round_freq(mobile_tx.low_mhz - plan.min_separation_from_mobile_tx_mhz),
            )
        elif plan.placement == "above_mobile_tx":
            a_low = max(
                a_low,
                self._round_freq(mobile_tx.high_mhz + plan.min_separation_from_mobile_tx_mhz),
            )

        a_low, b_high = self._apply_tx_window_bounds(a_low, b_high, plan)
        a_low, b_high = self._apply_mobile_rx_relation_bounds(
            a_low,
            b_high,
            system_summary.mobile_rx_range,
            plan,
            tx_mobile_rx_relation,
        )

        max_feasible_width = self._round_freq(b_high - a_low)
        if max_feasible_width <= 0:
            return None

        width = min(requested_passband, max_feasible_width)
        if width <= 0:
            return None

        if plan.placement == "below_mobile_tx":
            candidate_high = b_high
            candidate_low = self._round_freq(candidate_high - width)
            if candidate_low < a_low:
                return None
        else:
            candidate_low = a_low
            candidate_high = self._round_freq(candidate_low + width)
            if candidate_high > b_high:
                return None

        return FrequencyRange(candidate_low, candidate_high)

    def _solve_feasible_rx_interval(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        base_rx_range: tuple[float, float],
        tx_mobile_rx_relation: str | None,
    ) -> FrequencyRange | None:
        a_low = base_rx_range[0]
        b_high = base_rx_range[1]
        mobile_tx = system_summary.mobile_tx_range

        if plan.placement == "below_mobile_tx":
            b_high = min(
                b_high,
                self._round_freq(mobile_tx.low_mhz - plan.min_separation_from_mobile_tx_mhz),
            )
        elif plan.placement == "above_mobile_tx":
            a_low = max(
                a_low,
                self._round_freq(mobile_tx.high_mhz + plan.min_separation_from_mobile_tx_mhz),
            )

        a_low, b_high = self._apply_tx_window_bounds(a_low, b_high, plan)
        a_low, b_high = self._apply_mobile_rx_relation_bounds(
            a_low,
            b_high,
            system_summary.mobile_rx_range,
            plan,
            tx_mobile_rx_relation,
        )

        if self._round_freq(b_high - a_low) < 0:
            return None
        return FrequencyRange(a_low, b_high)

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
                self._round_freq(proposed_rx.low_mhz - effective_offset),
                self._round_freq(proposed_rx.high_mhz - effective_offset),
            )
        if plan.pair_direction in {"tx_above_rx", "manual"}:
            return FrequencyRange(
                self._round_freq(proposed_rx.low_mhz + effective_offset),
                self._round_freq(proposed_rx.high_mhz + effective_offset),
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

        low_offset = self._round_freq(
            system_summary.system_tx_range.low_mhz - system_summary.system_rx_range.low_mhz,
        )
        high_offset = self._round_freq(
            system_summary.system_tx_range.high_mhz - system_summary.system_rx_range.high_mhz,
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

        actual_tx = self._frequency_point_range(request.actual_dvrs_tx_mhz)
        actual_rx = self._frequency_point_range(request.actual_dvrs_rx_mhz)

        notes = []
        if request.agency_notes:
            notes.append(request.agency_notes)
        if best_plan is None:
            notes.append("No technically valid standard plan proposal was produced.")
            if request.actual_dvrs_tx_mhz is not None or request.actual_dvrs_rx_mhz is not None:
                notes.append(
                    "Consult a Motorola Presale Engineer before proceeding because no standard plan fits the provided DVRS frequency setup."
                )
        else:
            notes.append(f"Best preliminary standard plan: {best_plan.display_name}.")

        return OrderingSummary(
            system_tx_range=best_plan.system_tx_range if best_plan and best_plan.system_tx_range is not None else system_summary.system_tx_range,
            system_rx_range=best_plan.system_rx_range if best_plan and best_plan.system_rx_range is not None else system_summary.system_rx_range,
            proposed_dvrs_tx_range=best_plan.proposed_dvrs_tx_range if best_plan else None,
            proposed_dvrs_rx_range=best_plan.proposed_dvrs_rx_range if best_plan else None,
            actual_dvrs_tx_range=actual_tx,
            actual_dvrs_rx_range=actual_rx,
            notes=notes,
        )

    def _optional_range(self, low_mhz: float | None, high_mhz: float | None) -> FrequencyRange | None:
        if low_mhz is None or high_mhz is None:
            return None
        return FrequencyRange(low_mhz, high_mhz)

    def _frequency_point_range(self, value_mhz: float | None) -> FrequencyRange | None:
        if value_mhz is None:
            return None
        rounded = self._round_freq(value_mhz)
        return FrequencyRange(rounded, rounded)

    def _actual_range(self, value_mhz: float | None) -> FrequencyRange | None:
        if value_mhz is None:
            return None
        low_mhz = self._round_freq(value_mhz - self.ACTUAL_DVRS_RANGE_HALF_WIDTH_MHZ)
        high_mhz = self._round_freq(value_mhz + self.ACTUAL_DVRS_RANGE_HALF_WIDTH_MHZ)
        return FrequencyRange(low_mhz, high_mhz)

    def _apply_actual_dvrs_frequencies(
        self,
        request: CalculationRequest,
        plan: TechnicalPlan,
        proposed_tx: FrequencyRange,
        proposed_rx: FrequencyRange,
        widened: bool,
    ) -> tuple[FrequencyRange, FrequencyRange]:
        range_builder = self._actual_range if widened else self._frequency_point_range
        actual_tx = range_builder(request.actual_dvrs_tx_mhz)
        actual_rx = range_builder(request.actual_dvrs_rx_mhz)

        adjusted_tx = actual_tx or proposed_tx
        adjusted_rx = actual_rx or proposed_rx

        if plan.dvrs_mode != "simplex":
            return adjusted_tx, adjusted_rx

        if actual_tx is not None and actual_rx is None:
            adjusted_rx = actual_tx
        elif actual_rx is not None and actual_tx is None:
            adjusted_tx = actual_rx
        return adjusted_tx, adjusted_rx

    def _build_actual_frequency_spacing_note(
        self,
        request: CalculationRequest,
        system_summary: SystemSummary,
        base_plan: TechnicalPlan,
        variant_label: str,
        plan: TechnicalPlan,
        derived_pair_offset: float | None,
        exact_tx: FrequencyRange,
        exact_rx: FrequencyRange,
    ) -> str | None:
        if request.actual_dvrs_tx_mhz is None and request.actual_dvrs_rx_mhz is None:
            return None

        widened_tx, widened_rx = self._apply_actual_dvrs_frequencies(
            request,
            plan,
            exact_tx,
            exact_rx,
            widened=True,
        )
        widened_violation = self._validate_actual_frequency_setup(
            system_summary,
            base_plan,
            variant_label,
            plan,
            widened_tx,
            widened_rx,
            derived_pair_offset,
        )
        if widened_violation is None:
            return None

        spacing_messages: list[str] = []
        mobile_tx_spacing = self._describe_mobile_tx_spacing(system_summary, plan, exact_rx)
        if mobile_tx_spacing is not None:
            spacing_messages.append(mobile_tx_spacing)
        mobile_rx_spacing = self._describe_mobile_rx_spacing(system_summary, plan, exact_tx)
        if mobile_rx_spacing is not None:
            spacing_messages.append(mobile_rx_spacing)

        if not spacing_messages:
            return None

        return (
            "Exact DVRS frequency validation passed, but the advisory +/-0.5 MHz window would reduce spacing below the normal margin. "
            + " ".join(spacing_messages)
        )

    def _validate_actual_frequency_setup(
        self,
        system_summary: SystemSummary,
        base_plan: TechnicalPlan,
        variant_label: str,
        plan: TechnicalPlan,
        proposed_tx: FrequencyRange,
        proposed_rx: FrequencyRange,
        derived_pair_offset: float | None,
    ) -> RuleViolation | None:
        if plan.fixed_dvrs_rx_range is not None and not self._range_within_window(proposed_rx, plan.fixed_dvrs_rx_range):
            return RuleViolation(
                code="DVRS_RX_OUTSIDE_FIXED_PLAN_RANGE",
                message=(
                    "DVRS RX range falls outside the plan's fixed ordering-guide RX range. "
                    f"DVRS RX={self._format_range(proposed_rx)}; fixed RX range={self._format_window(plan.fixed_dvrs_rx_range)}."
                ),
                details={
                    "plan_id": base_plan.id,
                    "variant": variant_label,
                    "dvrs_rx_range": {
                        "low_mhz": proposed_rx.low_mhz,
                        "high_mhz": proposed_rx.high_mhz,
                    },
                    "fixed_dvrs_rx_range": self._window_details(plan.fixed_dvrs_rx_range),
                },
            )

        if plan.fixed_dvrs_tx_range is not None and not self._range_within_window(proposed_tx, plan.fixed_dvrs_tx_range):
            return RuleViolation(
                code="DVRS_TX_OUTSIDE_FIXED_PLAN_RANGE",
                message=(
                    "DVRS TX range falls outside the plan's fixed ordering-guide TX range. "
                    f"DVRS TX={self._format_range(proposed_tx)}; fixed TX range={self._format_window(plan.fixed_dvrs_tx_range)}."
                ),
                details={
                    "plan_id": base_plan.id,
                    "variant": variant_label,
                    "dvrs_tx_range": {
                        "low_mhz": proposed_tx.low_mhz,
                        "high_mhz": proposed_tx.high_mhz,
                    },
                    "fixed_dvrs_tx_range": self._window_details(plan.fixed_dvrs_tx_range),
                },
            )

        if not self._range_within_window(proposed_rx, plan.dvrs_rx_window):
            return RuleViolation(
                code="DVRS_RX_OUTSIDE_ALLOWED_WINDOW",
                message=(
                    "DVRS RX range falls outside the plan's allowed RX window. "
                    f"DVRS RX={self._format_range(proposed_rx)}; allowed RX window={self._format_window(plan.dvrs_rx_window)}."
                ),
                details={
                    "plan_id": base_plan.id,
                    "variant": variant_label,
                    "dvrs_rx_range": {
                        "low_mhz": proposed_rx.low_mhz,
                        "high_mhz": proposed_rx.high_mhz,
                    },
                    "allowed_dvrs_rx_window": self._window_details(plan.dvrs_rx_window),
                },
            )

        mobile_tx_sep = self._minimum_range_separation(system_summary.mobile_tx_range, proposed_rx)
        if plan.placement == "below_mobile_tx":
            if proposed_rx.high_mhz > system_summary.mobile_tx_range.low_mhz:
                mobile_tx_sep = 0.0
        elif plan.placement == "above_mobile_tx":
            if proposed_rx.low_mhz < system_summary.mobile_tx_range.high_mhz:
                mobile_tx_sep = 0.0
        if mobile_tx_sep + 1e-9 < plan.min_separation_from_mobile_tx_mhz:
            return RuleViolation(
                code="INSUFFICIENT_MOBILE_TX_TO_DVRS_RX_SEPARATION",
                message=(
                    "Mobile TX to DVRS RX spacing is below the plan requirement. "
                    f"Mobile TX={self._format_range(system_summary.mobile_tx_range)}; "
                    f"DVRS RX={self._format_range(proposed_rx)}; "
                    f"required separation={plan.min_separation_from_mobile_tx_mhz:.5f} MHz; "
                    f"actual separation={mobile_tx_sep:.5f} MHz."
                ),
                details={
                    "plan_id": base_plan.id,
                    "variant": variant_label,
                    "mobile_tx_range": {
                        "low_mhz": system_summary.mobile_tx_range.low_mhz,
                        "high_mhz": system_summary.mobile_tx_range.high_mhz,
                    },
                    "dvrs_rx_range": {
                        "low_mhz": proposed_rx.low_mhz,
                        "high_mhz": proposed_rx.high_mhz,
                    },
                    "required_separation_mhz": plan.min_separation_from_mobile_tx_mhz,
                    "actual_separation_mhz": mobile_tx_sep,
                },
            )

        if plan.dvrs_mode == "simplex":
            if proposed_tx.low_mhz == proposed_rx.low_mhz and proposed_tx.high_mhz == proposed_rx.high_mhz:
                return None
            return RuleViolation(
                code="SIMPLEX_DVRS_TX_RX_MISMATCH",
                message=(
                    "This simplex plan requires DVRS TX and DVRS RX to use the same range. "
                    f"DVRS TX={self._format_range(proposed_tx)}; DVRS RX={self._format_range(proposed_rx)}."
                ),
                details={
                    "plan_id": base_plan.id,
                    "variant": variant_label,
                    "dvrs_tx_range": {"low_mhz": proposed_tx.low_mhz, "high_mhz": proposed_tx.high_mhz},
                    "dvrs_rx_range": {"low_mhz": proposed_rx.low_mhz, "high_mhz": proposed_rx.high_mhz},
                },
            )

        expected_offset = plan.pair_offset_mhz if plan.pair_offset_mhz is not None else derived_pair_offset
        if expected_offset is None:
            return None

        if plan.pair_direction == "tx_below_rx":
            low_delta = self._round_freq(proposed_rx.low_mhz - proposed_tx.low_mhz)
            high_delta = self._round_freq(proposed_rx.high_mhz - proposed_tx.high_mhz)
        else:
            low_delta = self._round_freq(proposed_tx.low_mhz - proposed_rx.low_mhz)
            high_delta = self._round_freq(proposed_tx.high_mhz - proposed_rx.high_mhz)

        if low_delta == expected_offset and high_delta == expected_offset:
            return None

        return RuleViolation(
            code="DVRS_TX_RX_PAIRING_MISMATCH",
            message=(
                "The DVRS TX/RX ranges do not maintain the plan's required pairing offset. "
                f"DVRS TX={self._format_range(proposed_tx)}; "
                f"DVRS RX={self._format_range(proposed_rx)}; "
                f"required offset={expected_offset:.5f} MHz."
            ),
            details={
                "plan_id": base_plan.id,
                "variant": variant_label,
                "pair_direction": plan.pair_direction,
                "required_offset_mhz": expected_offset,
                "actual_low_delta_mhz": low_delta,
                "actual_high_delta_mhz": high_delta,
            },
        )

    def _validate_mobile_rx_spacing(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        proposed_tx: FrequencyRange,
    ) -> RuleViolation | None:
        if system_summary.mobile_rx_range is None:
            return None

        required_sep = (
            plan.min_separation_from_mobile_rx_mhz
            if plan.min_separation_from_mobile_rx_mhz is not None
            else plan.min_separation_from_mobile_tx_mhz
        )
        actual_sep = self._minimum_range_separation(system_summary.mobile_rx_range, proposed_tx)
        if actual_sep + 1e-9 >= required_sep:
            return None

        return RuleViolation(
            code="INSUFFICIENT_MOBILE_RX_TO_DVRS_TX_SEPARATION",
            message=(
                "Mobile RX to DVRS TX spacing is below the plan requirement. "
                f"Mobile RX={self._format_range(system_summary.mobile_rx_range)}; "
                f"DVRS TX={self._format_range(proposed_tx)}; "
                f"required separation={required_sep:.5f} MHz; actual separation={actual_sep:.5f} MHz."
            ),
            details={
                "plan_id": plan.id,
                "mobile_rx_range": {
                    "low_mhz": system_summary.mobile_rx_range.low_mhz,
                    "high_mhz": system_summary.mobile_rx_range.high_mhz,
                },
                "dvrs_tx_range": {
                    "low_mhz": proposed_tx.low_mhz,
                    "high_mhz": proposed_tx.high_mhz,
                },
                "required_separation_mhz": required_sep,
                "actual_separation_mhz": actual_sep,
            },
        )

    def _describe_mobile_tx_spacing(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        proposed_rx: FrequencyRange,
    ) -> str | None:
        actual_sep = self._minimum_range_separation(system_summary.mobile_tx_range, proposed_rx)
        if plan.placement == "below_mobile_tx" and proposed_rx.high_mhz > system_summary.mobile_tx_range.low_mhz:
            actual_sep = 0.0
        elif plan.placement == "above_mobile_tx" and proposed_rx.low_mhz < system_summary.mobile_tx_range.high_mhz:
            actual_sep = 0.0
        if actual_sep + 1e-9 < plan.min_separation_from_mobile_tx_mhz:
            return None
        return (
            "Actual mobile TX to DVRS RX separation is "
            f"{actual_sep:.5f} MHz against a {plan.min_separation_from_mobile_tx_mhz:.5f} MHz requirement."
        )

    def _describe_mobile_rx_spacing(
        self,
        system_summary: SystemSummary,
        plan: TechnicalPlan,
        proposed_tx: FrequencyRange,
    ) -> str | None:
        if system_summary.mobile_rx_range is None:
            return None

        required_sep = (
            plan.min_separation_from_mobile_rx_mhz
            if plan.min_separation_from_mobile_rx_mhz is not None
            else plan.min_separation_from_mobile_tx_mhz
        )
        actual_sep = self._minimum_range_separation(system_summary.mobile_rx_range, proposed_tx)
        if actual_sep + 1e-9 < required_sep:
            return None
        return (
            "Actual mobile RX to DVRS TX separation is "
            f"{actual_sep:.5f} MHz against a {required_sep:.5f} MHz requirement."
        )

    def _round_freq(self, value: float) -> float:
        return round(value, self.MAX_INPUT_DECIMAL_PLACES)

    def _apply_tx_window_bounds(
        self,
        a_low: float,
        b_high: float,
        plan: TechnicalPlan,
    ) -> tuple[float, float]:
        if plan.dvrs_tx_window is None:
            return a_low, b_high

        tx_low_window, tx_high_window = plan.dvrs_tx_window
        if plan.dvrs_mode == "simplex":
            return max(a_low, tx_low_window), min(b_high, tx_high_window)

        offset = plan.pair_offset_mhz or 0.0
        if plan.pair_direction in {"tx_above_rx", "manual"}:
            return (
                max(a_low, self._round_freq(tx_low_window - offset)),
                min(b_high, self._round_freq(tx_high_window - offset)),
            )
        if plan.pair_direction == "tx_below_rx":
            return (
                max(a_low, self._round_freq(tx_low_window + offset)),
                min(b_high, self._round_freq(tx_high_window + offset)),
            )
        return a_low, b_high

    def _apply_mobile_rx_relation_bounds(
        self,
        a_low: float,
        b_high: float,
        mobile_rx_range: FrequencyRange | None,
        plan: TechnicalPlan,
        relation: str | None,
    ) -> tuple[float, float]:
        if mobile_rx_range is None or relation is None:
            return a_low, b_high

        required_sep = (
            plan.min_separation_from_mobile_rx_mhz
            if plan.min_separation_from_mobile_rx_mhz is not None
            else plan.min_separation_from_mobile_tx_mhz
        )
        offset = plan.pair_offset_mhz or 0.0

        if plan.dvrs_mode == "simplex":
            if relation == "tx_after_mobile_rx":
                a_low = max(a_low, self._round_freq(mobile_rx_range.high_mhz + required_sep))
            else:
                b_high = min(b_high, self._round_freq(mobile_rx_range.low_mhz - required_sep))
            return a_low, b_high

        if plan.pair_direction in {"tx_above_rx", "manual"}:
            if relation == "tx_after_mobile_rx":
                a_low = max(a_low, self._round_freq(mobile_rx_range.high_mhz + required_sep - offset))
            else:
                b_high = min(b_high, self._round_freq(mobile_rx_range.low_mhz - required_sep - offset))
            return a_low, b_high

        if plan.pair_direction == "tx_below_rx":
            if relation == "tx_after_mobile_rx":
                a_low = max(a_low, self._round_freq(mobile_rx_range.high_mhz + required_sep + offset))
            else:
                b_high = min(b_high, self._round_freq(mobile_rx_range.low_mhz - required_sep + offset))

        return a_low, b_high

    def _decimal_places(self, value: float) -> int:
        try:
            decimal_value = Decimal(str(value)).normalize()
        except InvalidOperation:
            return 0
        exponent = decimal_value.as_tuple().exponent
        return abs(exponent) if exponent < 0 else 0

    def _format_window(self, window: tuple[float, float] | None) -> str:
        if window is None:
            return "unbounded"
        return f"{window[0]:.5f}-{window[1]:.5f} MHz"

    def _format_range(self, value: FrequencyRange) -> str:
        return f"{value.low_mhz:.5f}-{value.high_mhz:.5f} MHz"

    def _window_details(self, window: tuple[float, float] | None) -> dict[str, float] | None:
        if window is None:
            return None
        return {"low_mhz": window[0], "high_mhz": window[1]}

    def _minimum_range_separation(self, left: FrequencyRange, right: FrequencyRange) -> float:
        if left.high_mhz <= right.low_mhz:
            return self._round_freq(right.low_mhz - left.high_mhz)
        if right.high_mhz <= left.low_mhz:
            return self._round_freq(left.low_mhz - right.high_mhz)
        return 0.0

    def _build_no_rx_solution_reason(
        self,
        mobile_tx: FrequencyRange,
        plan: TechnicalPlan,
        proposed_dvrs_passband: float,
    ) -> str:
        if plan.fixed_dvrs_rx_range is not None:
            return (
                "No channel inside the plan's fixed ordering-guide DVRS RX range satisfies the required constraints. "
                f"Input mobile TX={self._format_range(mobile_tx)}; "
                f"fixed DVRS RX range={self._format_window(plan.fixed_dvrs_rx_range)}; "
                f"required minimum separation from mobile TX={plan.min_separation_from_mobile_tx_mhz:.5f} MHz."
            )
        return (
            "No contiguous DVRS RX window satisfies this plan's spacing and frequency constraints. "
            f"Input mobile TX={self._format_range(mobile_tx)}; "
            f"DVRS RX window={self._format_window(plan.dvrs_rx_window)}; "
            f"required minimum separation from mobile TX={plan.min_separation_from_mobile_tx_mhz:.5f} MHz; "
            f"requested DVRS passband={proposed_dvrs_passband:.5f} MHz."
        )

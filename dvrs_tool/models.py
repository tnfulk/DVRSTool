"""Domain models for the DVRS calculation engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any


class Country(str, Enum):
    UNITED_STATES = "United States"
    CANADA = "Canada"


class BandFamily(str, Enum):
    BAND_700 = "700 MHz"
    BAND_800 = "800 MHz"
    VHF = "VHF"
    UHF_380 = "UHF 380-430"
    UHF_450 = "UHF 450-470"


class PairingSource(str, Enum):
    DETERMINISTIC = "deterministic"
    MANUAL_OVERRIDE = "manual_override"
    UNAVAILABLE = "unavailable"


class TechnicalStatus(str, Enum):
    VALID = "TECHNICALLY_VALID"
    INVALID = "TECHNICALLY_INVALID"


class RegulatoryStatus(str, Enum):
    LIKELY_LICENSABLE = "LIKELY_LICENSABLE"
    COORDINATION_REQUIRED = "COORDINATION_REQUIRED"
    LIKELY_NOT_LICENSABLE = "LIKELY_NOT_LICENSABLE"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass
class FrequencyRange:
    low_mhz: float
    high_mhz: float

    @property
    def width_mhz(self) -> float:
        return round(self.high_mhz - self.low_mhz, 4)


@dataclass
class CalculationRequest:
    country: Country
    mobile_tx_low_mhz: float
    mobile_tx_high_mhz: float
    mobile_rx_low_mhz: float | None = None
    mobile_rx_high_mhz: float | None = None
    use_latest_ordering_ruleset: bool = True
    agency_notes: str | None = None
    actual_licensed_dvrs_tx_low_mhz: float | None = None
    actual_licensed_dvrs_tx_high_mhz: float | None = None
    actual_licensed_dvrs_rx_low_mhz: float | None = None
    actual_licensed_dvrs_rx_high_mhz: float | None = None


@dataclass
class SystemSummary:
    detected_band: BandFamily
    mobile_tx_range: FrequencyRange
    mobile_rx_range: FrequencyRange | None
    system_rx_range: FrequencyRange
    system_tx_range: FrequencyRange | None
    pairing_source: PairingSource
    warnings: list[str] = field(default_factory=list)


@dataclass
class TechnicalPlan:
    id: str
    display_name: str
    band_family: BandFamily
    dvrs_mode: str
    placement: str
    mount_compatibility: list[str]
    dvrs_rx_window: tuple[float, float] | None
    dvrs_tx_window: tuple[float, float] | None
    pair_offset_mhz: float | None
    pair_direction: str
    min_separation_from_mobile_tx_mhz: float
    max_dvrs_passband_mhz: float
    requires_mobile_rx_range: bool = False
    rule_precision: str = "derived"
    notes: list[str] = field(default_factory=list)


@dataclass
class PlanResult:
    plan_id: str
    display_name: str
    technical_status: TechnicalStatus
    regulatory_status: RegulatoryStatus
    confidence: float
    proposed_dvrs_tx_range: FrequencyRange | None
    proposed_dvrs_rx_range: FrequencyRange | None
    mount_compatibility: list[str]
    failure_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    regulatory_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class OrderingSummary:
    system_tx_range: FrequencyRange | None
    system_rx_range: FrequencyRange
    proposed_dvrs_tx_range: FrequencyRange | None
    proposed_dvrs_rx_range: FrequencyRange | None
    actual_licensed_dvrs_tx_range: FrequencyRange | None
    actual_licensed_dvrs_rx_range: FrequencyRange | None
    notes: list[str] = field(default_factory=list)


@dataclass
class CalculationResponse:
    request: CalculationRequest
    system_summary: SystemSummary
    plan_results: list[PlanResult]
    ordering_summary: OrderingSummary
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value

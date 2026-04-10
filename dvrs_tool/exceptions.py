"""Custom exceptions for the DVRS calculation engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DVRSBaseError(Exception):
    """Base structured exception for engine and API errors."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    rule_violations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "rule_violations": self.rule_violations,
        }

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class InputValidationError(DVRSBaseError):
    """Raised for invalid user inputs."""


class UnsupportedBandError(DVRSBaseError):
    """Raised when a frequency range does not map to a supported band."""


class FrequencyInferenceError(DVRSBaseError):
    """Raised when a derived frequency range cannot be safely inferred."""


class MissingDependencyError(DVRSBaseError):
    """Raised when optional runtime dependencies are not installed."""

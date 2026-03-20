from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Regime(StrEnum):
    NOMINAL = "nominal"
    DISTURBANCE = "disturbance"
    WEAR = "wear"
    DEFORMATION = "deformation"
    UNKNOWN = "unknown"


class DiagnosticMode(StrEnum):
    NORMAL = "normal"
    SUSPECT = "suspect"
    PROBE = "probe"
    CONFIRMED = "confirmed"
    UNKNOWN = "unknown"


@dataclass
class ResidualEvent:
    t: int
    residual: tuple[float, float, float]
    residual_norm: float
    context: dict[str, Any]
    true_regime: Regime
    onset_step: int | None = None


@dataclass
class InterpreterState:
    mode: DiagnosticMode = DiagnosticMode.NORMAL
    hypothesis_scores: dict[str, float] = field(
        default_factory=lambda: {
            Regime.NOMINAL.value: 1.0,
            Regime.DISTURBANCE.value: 0.0,
            Regime.WEAR.value: 0.0,
            Regime.DEFORMATION.value: 0.0,
            Regime.UNKNOWN.value: 0.0,
        }
    )
    top_hypothesis: str = Regime.NOMINAL.value
    confidence: float = 1.0
    evidence_steps: int = 0
    ema_short: float = 0.0
    ema_long: float = 0.0
    last_magnitude: float = 0.0
    last_residual: tuple[float, float, float] = (0.0, 0.0, 0.0)
    last_reason: str = "initialized"
    cooldown_remaining: int = 0


@dataclass
class SelfLedger:
    health: float = 1.0
    deformation: float = 0.0
    calibration: float = 0.0
    version: int = 0

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.health, self.deformation, self.calibration)


@dataclass
class StepAudit:
    t: int
    regime: str
    residual: tuple[float, float, float]
    residual_norm: float
    mode: str
    top_hypothesis: str
    confidence: float
    gate_open: bool
    gate_reason: str
    ledger: tuple[float, float, float]
    note: str


@dataclass
class MethodResult:
    method_name: str
    regime: str
    seed: int
    onset_step: int | None
    ledger_history: list[SelfLedger]
    audit: list[StepAudit]
    write_steps: list[int]
    committed_classes: list[str]

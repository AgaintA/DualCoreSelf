from __future__ import annotations

from .features import clamp
from .types import InterpreterState, Regime, ResidualEvent, SelfLedger


class SelfStateCore:
    def apply(self, previous: SelfLedger, state: InterpreterState, event: ResidualEvent) -> SelfLedger:
        health, deformation, calibration = previous.as_tuple()

        if state.top_hypothesis == Regime.WEAR.value:
            health = clamp(health - (0.010 + 0.030 * max(0.0, state.confidence - 0.78)), 0.0, 1.0)
            calibration = clamp(calibration + abs(event.residual[2]) * 0.040, 0.0, 1.0)
        elif state.top_hypothesis == Regime.DEFORMATION.value:
            deformation = clamp(deformation + 0.030 + abs(event.residual[1]) * 0.150, 0.0, 1.0)
            health = clamp(health - 0.015, 0.0, 1.0)
            calibration = clamp(calibration + abs(event.residual[2]) * 0.060, 0.0, 1.0)

        return SelfLedger(
            health=health,
            deformation=deformation,
            calibration=calibration,
            version=previous.version + 1,
        )

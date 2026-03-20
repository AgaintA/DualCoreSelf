from __future__ import annotations

from ecoa_dual_core.core.features import clamp, smooth
from ecoa_dual_core.core.types import MethodResult, ResidualEvent, SelfLedger, StepAudit


class ThresholdedEMAUpdater:
    def __init__(self, alpha: float, threshold: float, step_size: float) -> None:
        self.alpha = alpha
        self.threshold = threshold
        self.step_size = step_size

    def _forced_class(self, event: ResidualEvent) -> str:
        return "deformation" if abs(event.residual[1]) >= abs(event.residual[0]) else "wear"

    def run(self, events: list[ResidualEvent], seed: int) -> MethodResult:
        ledger = SelfLedger()
        ema = 0.0
        ledger_history = [SelfLedger()]
        audit: list[StepAudit] = []
        write_steps: list[int] = []
        committed_classes: list[str] = []

        for event in events:
            ema = smooth(ema, event.residual_norm, self.alpha)
            changed = ema >= self.threshold
            if changed:
                ledger = SelfLedger(
                    health=clamp(ledger.health - abs(event.residual[0]) * self.step_size, 0.0, 1.0),
                    deformation=clamp(ledger.deformation + abs(event.residual[1]) * self.step_size, 0.0, 1.0),
                    calibration=clamp(ledger.calibration + abs(event.residual[2]) * self.step_size, 0.0, 1.0),
                    version=ledger.version + 1,
                )
                write_steps.append(event.t)
                committed_classes.append(self._forced_class(event))

            ledger_history.append(ledger)
            audit.append(
                StepAudit(
                    t=event.t,
                    regime=event.true_regime.value,
                    residual=event.residual,
                    residual_norm=event.residual_norm,
                    mode="ema_thresh",
                    top_hypothesis=self._forced_class(event) if changed else "ema_threshold",
                    confidence=min(1.0, ema),
                    gate_open=changed,
                    gate_reason="ema above threshold" if changed else "ema below threshold",
                    ledger=ledger.as_tuple(),
                    note=f"ema={ema:.4f}, threshold={self.threshold:.4f}",
                )
            )

        return MethodResult(
            method_name="Thresholded EMA",
            regime=events[0].true_regime.value,
            seed=seed,
            onset_step=events[0].onset_step,
            ledger_history=ledger_history,
            audit=audit,
            write_steps=write_steps,
            committed_classes=committed_classes,
        )

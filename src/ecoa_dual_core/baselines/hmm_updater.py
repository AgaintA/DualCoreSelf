from __future__ import annotations

from ecoa_dual_core.core.features import clamp, cosine_similarity, smooth
from ecoa_dual_core.core.types import MethodResult, Regime, ResidualEvent, SelfLedger, StepAudit


class HMMFaultStateUpdater:
    def __init__(self, commit_threshold: float) -> None:
        self.commit_threshold = commit_threshold
        self.transition = {
            Regime.NOMINAL.value: {
                Regime.NOMINAL.value: 0.76,
                Regime.DISTURBANCE.value: 0.10,
                Regime.WEAR.value: 0.06,
                Regime.DEFORMATION.value: 0.03,
                Regime.UNKNOWN.value: 0.05,
            },
            Regime.DISTURBANCE.value: {
                Regime.NOMINAL.value: 0.24,
                Regime.DISTURBANCE.value: 0.56,
                Regime.WEAR.value: 0.08,
                Regime.DEFORMATION.value: 0.04,
                Regime.UNKNOWN.value: 0.08,
            },
            Regime.WEAR.value: {
                Regime.NOMINAL.value: 0.05,
                Regime.DISTURBANCE.value: 0.05,
                Regime.WEAR.value: 0.76,
                Regime.DEFORMATION.value: 0.04,
                Regime.UNKNOWN.value: 0.10,
            },
            Regime.DEFORMATION.value: {
                Regime.NOMINAL.value: 0.04,
                Regime.DISTURBANCE.value: 0.04,
                Regime.WEAR.value: 0.07,
                Regime.DEFORMATION.value: 0.75,
                Regime.UNKNOWN.value: 0.10,
            },
            Regime.UNKNOWN.value: {
                Regime.NOMINAL.value: 0.08,
                Regime.DISTURBANCE.value: 0.10,
                Regime.WEAR.value: 0.10,
                Regime.DEFORMATION.value: 0.08,
                Regime.UNKNOWN.value: 0.64,
            },
        }

    def _emissions(
        self,
        magnitude: float,
        ema_short: float,
        ema_long: float,
        abruptness: float,
        consistency: float,
    ) -> dict[str, float]:
        wear_score = max(0.01, ema_long * 1.0 + max(0.0, ema_short - ema_long) * 1.2 + max(0.0, consistency))
        deformation_score = max(0.01, abruptness * 1.8 + ema_short * 0.7 + max(0.0, consistency) * 0.3)
        disturbance_score = max(0.01, abruptness * 1.4 + magnitude * 0.8 - max(0.0, consistency) * 0.7)
        nominal_score = max(0.01, 1.0 - magnitude * 4.0)
        unknown_score = max(0.01, magnitude * 0.9 + (1.0 - abs(consistency)) * 0.5)
        return {
            Regime.NOMINAL.value: nominal_score,
            Regime.DISTURBANCE.value: disturbance_score,
            Regime.WEAR.value: wear_score,
            Regime.DEFORMATION.value: deformation_score,
            Regime.UNKNOWN.value: unknown_score,
        }

    def run(self, events: list[ResidualEvent], seed: int) -> MethodResult:
        posterior = {
            Regime.NOMINAL.value: 1.0,
            Regime.DISTURBANCE.value: 0.0,
            Regime.WEAR.value: 0.0,
            Regime.DEFORMATION.value: 0.0,
            Regime.UNKNOWN.value: 0.0,
        }
        ledger = SelfLedger()
        ledger_history = [SelfLedger()]
        audit: list[StepAudit] = []
        write_steps: list[int] = []
        committed_classes: list[str] = []

        ema_short = 0.0
        ema_long = 0.0
        last_magnitude = 0.0
        last_residual = (0.0, 0.0, 0.0)

        for event in events:
            magnitude = event.residual_norm
            ema_short = smooth(ema_short, magnitude, 0.45)
            ema_long = smooth(ema_long, magnitude, 0.10)
            abruptness = max(0.0, magnitude - last_magnitude)
            consistency = cosine_similarity(event.residual, last_residual)

            emissions = self._emissions(magnitude, ema_short, ema_long, abruptness, consistency)
            predicted = {}
            for next_state in posterior:
                predicted[next_state] = sum(
                    posterior[state] * self.transition[state][next_state] for state in posterior
                )

            unnormalized = {state: predicted[state] * emissions[state] for state in posterior}
            total = sum(unnormalized.values()) or 1.0
            posterior = {state: value / total for state, value in unnormalized.items()}

            top_state, confidence = max(posterior.items(), key=lambda item: item[1])
            changed = top_state in {Regime.WEAR.value, Regime.DEFORMATION.value} and confidence >= self.commit_threshold

            if changed:
                ledger = SelfLedger(
                    health=clamp(
                        ledger.health - (0.020 if top_state == Regime.DEFORMATION.value else 0.010),
                        0.0,
                        1.0,
                    ),
                    deformation=clamp(
                        ledger.deformation + (0.060 if top_state == Regime.DEFORMATION.value else 0.015),
                        0.0,
                        1.0,
                    ),
                    calibration=clamp(ledger.calibration + abs(event.residual[2]) * 0.060, 0.0, 1.0),
                    version=ledger.version + 1,
                )
                write_steps.append(event.t)
                committed_classes.append(top_state)

            ledger_history.append(ledger)
            audit.append(
                StepAudit(
                    t=event.t,
                    regime=event.true_regime.value,
                    residual=event.residual,
                    residual_norm=event.residual_norm,
                    mode="hmm",
                    top_hypothesis=top_state,
                    confidence=confidence,
                    gate_open=changed,
                    gate_reason="posterior commit" if changed else "posterior below commit threshold",
                    ledger=ledger.as_tuple(),
                    note=(
                        f"short={ema_short:.3f}, long={ema_long:.3f}, abrupt={abruptness:.3f}, "
                        f"consistency={consistency:.3f}"
                    ),
                )
            )

            last_magnitude = magnitude
            last_residual = event.residual

        return MethodResult(
            method_name="HMM updater",
            regime=events[0].true_regime.value,
            seed=seed,
            onset_step=events[0].onset_step,
            ledger_history=ledger_history,
            audit=audit,
            write_steps=write_steps,
            committed_classes=committed_classes,
        )

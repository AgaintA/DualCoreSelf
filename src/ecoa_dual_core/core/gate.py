from __future__ import annotations

from .types import DiagnosticMode, InterpreterState, Regime


class WriteGate:
    def __init__(self, config: dict[str, float]) -> None:
        self.confirm_confidence = float(config["confirm_confidence"])
        self.confirm_steps = int(config["confirm_steps"])
        self.cooldown_steps = int(config["cooldown_steps"])
        self.min_hypothesis_score = 0.46
        self.max_unknown_for_wear = 0.09
        self.max_unknown_for_deformation = 0.16
        self.min_wear_over_deformation_ratio = 1.90
        self.min_deformation_over_wear_ratio = 1.25

    def evaluate(self, state: InterpreterState) -> tuple[bool, str]:
        if state.cooldown_remaining > 0:
            return False, f"cooldown={state.cooldown_remaining}"
        if state.mode != DiagnosticMode.CONFIRMED:
            return False, f"mode={state.mode.value}"
        if state.top_hypothesis not in {Regime.WEAR.value, Regime.DEFORMATION.value}:
            return False, f"class={state.top_hypothesis}"
        if state.confidence < self.confirm_confidence:
            return False, f"confidence={state.confidence:.3f}"
        if state.evidence_steps < self.confirm_steps:
            return False, f"evidence_steps={state.evidence_steps}"
        target_score = state.hypothesis_scores.get(state.top_hypothesis, 0.0)
        if target_score < self.min_hypothesis_score:
            return False, f"top_score={target_score:.3f}"
        unknown_score = state.hypothesis_scores.get(Regime.UNKNOWN.value, 0.0)
        wear_score = state.hypothesis_scores.get(Regime.WEAR.value, 0.0)
        deformation_score = state.hypothesis_scores.get(Regime.DEFORMATION.value, 0.0)

        if state.top_hypothesis == Regime.WEAR.value:
            if unknown_score >= self.max_unknown_for_wear:
                return False, f"unknown_score={unknown_score:.3f}"
            if (state.ema_short - state.ema_long) < 0.01:
                return False, f"wear_slope={state.ema_short - state.ema_long:.3f}"
            ratio = wear_score / max(deformation_score, 1e-9)
            if ratio < self.min_wear_over_deformation_ratio:
                return False, f"wear_ratio={ratio:.3f}"

        if state.top_hypothesis == Regime.DEFORMATION.value:
            if unknown_score >= self.max_unknown_for_deformation:
                return False, f"unknown_score={unknown_score:.3f}"
            ratio = deformation_score / max(wear_score, 1e-9)
            if ratio < self.min_deformation_over_wear_ratio:
                return False, f"deformation_ratio={ratio:.3f}"

        return True, "confirmed persistent self-relevant change"

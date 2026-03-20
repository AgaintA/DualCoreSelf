from __future__ import annotations

from .features import clamp, cosine_similarity, smooth
from .types import DiagnosticMode, InterpreterState, Regime, ResidualEvent


class SelfModelInterpreter:
    def __init__(self, config: dict[str, float], gate_config: dict[str, float]) -> None:
        self.short_alpha = float(config["short_alpha"])
        self.long_alpha = float(config["long_alpha"])
        self.score_decay = float(config["score_decay"])
        self.confirm_confidence = float(gate_config["confirm_confidence"])
        self.confirm_steps = int(gate_config["confirm_steps"])

    def step(self, previous: InterpreterState, event: ResidualEvent) -> InterpreterState:
        magnitude = event.residual_norm
        ema_short = smooth(previous.ema_short, magnitude, self.short_alpha)
        ema_long = smooth(previous.ema_long, magnitude, self.long_alpha)
        slope = ema_short - ema_long
        abruptness = max(0.0, magnitude - previous.last_magnitude)
        consistency = cosine_similarity(event.residual, previous.last_residual)
        coherence = max(0.0, consistency)
        ambiguity = abs(event.residual[0] * event.residual[1]) + abs(event.residual[2]) * 0.4
        wear_axis = max(0.0, event.residual[0])
        deformation_axis = abs(event.residual[1])

        raw_scores = {
            Regime.NOMINAL.value: max(0.0, 1.0 - magnitude * 4.0),
            Regime.DISTURBANCE.value: max(
                0.0,
                abruptness * 1.8 + max(0.0, magnitude - 0.20) * 0.8 - coherence * 0.7,
            ),
            Regime.WEAR.value: max(
                0.0,
                ema_long * 0.8
                + max(0.0, slope) * 1.2
                + coherence * 0.7
                + wear_axis * 1.1
                - abruptness * 0.3
                - deformation_axis * 0.4,
            ),
            Regime.DEFORMATION.value: max(
                0.0,
                abruptness * 1.5 + ema_short * 0.6 + deformation_axis * 1.6 + coherence * 0.3,
            ),
            Regime.UNKNOWN.value: max(
                0.0,
                magnitude * 0.9 + ambiguity * 0.7 - max(wear_axis, deformation_axis) * 0.2,
            ),
        }

        decayed_scores = {}
        for hypothesis, score in previous.hypothesis_scores.items():
            decayed_scores[hypothesis] = score * self.score_decay + raw_scores[hypothesis]

        total = sum(decayed_scores.values()) or 1.0
        normalized_scores = {key: value / total for key, value in decayed_scores.items()}
        ordered = sorted(normalized_scores.items(), key=lambda item: item[1], reverse=True)
        top_hypothesis, top_probability = ordered[0]
        second_probability = ordered[1][1] if len(ordered) > 1 else 0.0
        confidence = clamp(top_probability + (top_probability - second_probability) * 0.5, 0.0, 1.0)
        evidence_steps = previous.evidence_steps + 1 if top_hypothesis == previous.top_hypothesis else 1
        cooldown_remaining = max(0, previous.cooldown_remaining - 1)

        if top_hypothesis == Regime.NOMINAL.value and confidence >= 0.45 and magnitude < 0.15:
            mode = DiagnosticMode.NORMAL
        elif top_hypothesis == Regime.UNKNOWN.value and confidence >= 0.34:
            mode = DiagnosticMode.UNKNOWN
        elif top_hypothesis in {Regime.WEAR.value, Regime.DEFORMATION.value}:
            if confidence >= self.confirm_confidence and evidence_steps >= self.confirm_steps:
                mode = DiagnosticMode.CONFIRMED
            elif confidence >= max(0.42, self.confirm_confidence - 0.14) and evidence_steps >= 2:
                mode = DiagnosticMode.PROBE
            else:
                mode = DiagnosticMode.SUSPECT
        else:
            mode = DiagnosticMode.PROBE if confidence >= 0.50 else DiagnosticMode.SUSPECT

        reason = (
            f"mag={magnitude:.3f}, short={ema_short:.3f}, long={ema_long:.3f}, "
            f"slope={slope:.3f}, abrupt={abruptness:.3f}, consistency={consistency:.3f}"
        )

        return InterpreterState(
            mode=mode,
            hypothesis_scores=normalized_scores,
            top_hypothesis=top_hypothesis,
            confidence=confidence,
            evidence_steps=evidence_steps,
            ema_short=ema_short,
            ema_long=ema_long,
            last_magnitude=magnitude,
            last_residual=event.residual,
            last_reason=reason,
            cooldown_remaining=cooldown_remaining,
        )

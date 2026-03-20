from __future__ import annotations

import math
import random

from ecoa_dual_core.core.features import l2_norm
from ecoa_dual_core.core.types import Regime, ResidualEvent


REGIME_OFFSETS = {
    Regime.NOMINAL: 11,
    Regime.DISTURBANCE: 23,
    Regime.WEAR: 37,
    Regime.DEFORMATION: 53,
    Regime.UNKNOWN: 71,
}


def _noise(rng: random.Random, scale: float) -> float:
    return rng.gauss(0.0, scale)


def generate_trial(regime: Regime, steps: int, seed: int) -> list[ResidualEvent]:
    rng = random.Random(seed * 997 + REGIME_OFFSETS[regime])
    onset_step: int | None = None
    events: list[ResidualEvent] = []

    burst_start = rng.randint(steps // 4, steps // 2)
    burst_length = rng.randint(5, 10)

    for t in range(steps):
        residual = [_noise(rng, 0.025), _noise(rng, 0.020), _noise(rng, 0.020)]
        context: dict[str, float | int] = {"probe_signal": 0.0, "seed": seed}

        if regime == Regime.NOMINAL:
            pass

        elif regime == Regime.DISTURBANCE:
            if burst_start <= t < burst_start + burst_length:
                sign = -1.0 if t % 2 else 1.0
                residual[0] += sign * rng.uniform(0.20, 0.40)
                residual[1] += -sign * rng.uniform(0.15, 0.30)
                residual[2] += rng.uniform(-0.08, 0.08)
                context["probe_signal"] = 1.0

        elif regime == Regime.WEAR:
            onset_step = steps // 3
            if t >= onset_step:
                progress = (t - onset_step) / max(1, steps - onset_step - 1)
                residual[0] += 0.08 + 0.22 * progress
                residual[2] += 0.03 + 0.07 * progress
                context["probe_signal"] = progress

        elif regime == Regime.DEFORMATION:
            onset_step = steps // 2
            if t >= onset_step:
                residual[0] += 0.10
                residual[1] += 0.45 + 0.05 * rng.random()
                residual[2] += 0.06
                context["probe_signal"] = 1.0

        elif regime == Regime.UNKNOWN:
            onset_step = steps // 3
            if t >= onset_step:
                flip = -1.0 if (t // 3) % 2 else 1.0
                residual[0] += 0.12 * flip + 0.08 * math.sin(t * 0.37)
                residual[1] += 0.20 * math.cos(t * 0.21)
                residual[2] += rng.uniform(-0.14, 0.14)
                context["probe_signal"] = 0.5

        residual_tuple = (residual[0], residual[1], residual[2])
        events.append(
            ResidualEvent(
                t=t,
                residual=residual_tuple,
                residual_norm=l2_norm(residual_tuple),
                context=context,
                true_regime=regime,
                onset_step=onset_step,
            )
        )

    return events

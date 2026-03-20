from __future__ import annotations

from statistics import mean, pstdev

from ecoa_dual_core.core.features import l1_distance
from ecoa_dual_core.core.types import MethodResult, Regime


def ledger_volatility(result: MethodResult) -> float:
    if len(result.ledger_history) < 2:
        return 0.0
    deltas = [
        l1_distance(curr.as_tuple(), prev.as_tuple())
        for prev, curr in zip(result.ledger_history[:-1], result.ledger_history[1:], strict=True)
    ]
    return mean(deltas)


def disturbance_false_update(result: MethodResult) -> float:
    if result.regime != Regime.DISTURBANCE.value:
        return 0.0
    return 1.0 if result.write_steps else 0.0


def detection_delay(result: MethodResult, regime: str) -> float:
    if result.regime != regime:
        return 0.0
    if result.onset_step is None:
        return 0.0
    for step in result.write_steps:
        if step >= result.onset_step:
            return float(step - result.onset_step)
    return float(len(result.audit) - result.onset_step)


def unknown_overcommitment(result: MethodResult) -> float:
    if result.regime != Regime.UNKNOWN.value:
        return 0.0
    target_classes = {Regime.WEAR.value, Regime.DEFORMATION.value}
    return 1.0 if any(label in target_classes for label in result.committed_classes) else 0.0


def summarize(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], 0.0
    return mean(values), pstdev(values)

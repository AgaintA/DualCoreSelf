from __future__ import annotations

import math


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def l2_norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def l1_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b, strict=True))


def cosine_similarity(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    norm_a = l2_norm(a)
    norm_b = l2_norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / (norm_a * norm_b)


def smooth(previous: float, current: float, alpha: float) -> float:
    return alpha * current + (1.0 - alpha) * previous

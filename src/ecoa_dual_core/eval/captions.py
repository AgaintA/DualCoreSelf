from __future__ import annotations

from pathlib import Path


def _find_method(stats: list[dict[str, float | str]], method_name: str) -> dict[str, float | str]:
    for item in stats:
        if str(item["Method"]) == method_name:
            return item
    raise ValueError(f"Method not found: {method_name}")


def write_captions_markdown(stats: list[dict[str, float | str]], output_path: Path, audit_seed: int) -> Path:
    dual = _find_method(stats, "Proposed Dual-Core mechanism")
    hmm = _find_method(stats, "HMM updater")
    direct = _find_method(stats, "Direct residual-to-self")
    ema = _find_method(stats, "Thresholded EMA")

    text = f"""# Figure Captions

## Figure 1. Quantitative Comparison Across Update Mechanisms

![Figure 1](./figure_metrics.svg)

Comparison of the four evaluated update mechanisms across the five paper-aligned metrics: self-ledger volatility under nominal operation, false self-update rate under disturbance, detection delay under wear, detection delay under deformation, and unknown-condition overcommitment. The proposed Dual-Core mechanism achieves zero false self-updates under disturbance and zero unknown-condition overcommitment in the current prototype, while preserving finite detection delay under both gradual wear and abrupt deformation. In contrast, the Direct and EMA baselines remain highly prone to over-writing persistent self state under disturbance and unknown conditions, whereas the HMM updater reacts faster but remains less conservative under uncertainty.

Current run highlights:

- Dual-Core disturbance false-update rate: {float(dual["disturbance_mean"]):.4f} +/- {float(dual["disturbance_std"]):.4f}
- Dual-Core unknown overcommitment: {float(dual["unknown_mean"]):.4f} +/- {float(dual["unknown_std"]):.4f}
- Dual-Core wear delay: {float(dual["wear_mean"]):.4f} +/- {float(dual["wear_std"]):.4f}
- Dual-Core deformation delay: {float(dual["deformation_mean"]):.4f} +/- {float(dual["deformation_std"]):.4f}
- HMM wear / deformation delay: {float(hmm["wear_mean"]):.4f} +/- {float(hmm["wear_std"]):.4f} / {float(hmm["deformation_mean"]):.4f} +/- {float(hmm["deformation_std"]):.4f}
- Direct disturbance false-update rate: {float(direct["disturbance_mean"]):.4f} +/- {float(direct["disturbance_std"]):.4f}
- EMA unknown overcommitment: {float(ema["unknown_mean"]):.4f} +/- {float(ema["unknown_std"]):.4f}

## Figure 2. Representative Dual-Core Diagnostic Trajectories

![Figure 2](./figure_dual_core_trajectories.svg)

Representative audit trajectories for the proposed Dual-Core mechanism using seed {audit_seed}. Each panel shows residual magnitude, interpreter confidence, ground-truth onset, and the timing of persistent self-ledger writes for one operating regime. The disturbance panel illustrates that transient mismatch can elevate interpreter activity without forcing persistent self rewriting. The wear and deformation panels show the intended interpret-then-write ordering: residual evidence first accumulates, interpreter confidence rises, and only then does the gate authorize a persistent update. The unknown panel illustrates the conservative target behavior in which discrepancy may remain diagnostically active without immediate commitment to a known self-change class.

## Figure 3. Dual-Core Interpret-Then-Write Architecture

![Figure 3](./figure_dual_core_mechanism.svg)

Architecture diagram of the proposed Dual-Core mechanism. Residual evidence and auxiliary context are first processed by the Self-Model Interpreter, which maintains hypothesis scores and a diagnostic state machine. A class-specific write gate then decides whether diagnostic evidence has become strong enough to authorize persistent self rewriting. If the gate remains closed, the system records the discrepancy in the audit path while keeping the self ledger stable. If the gate opens, the Self-State Core applies a conservative persistent rewrite. This diagram visualizes the paper's central architectural claim: diagnosis may change quickly, but persistent self state should change only through explicit mediated write authority.
"""

    output_path.write_text(text, encoding="utf-8")
    return output_path

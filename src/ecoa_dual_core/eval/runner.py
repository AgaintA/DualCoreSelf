from __future__ import annotations

import csv
import json
from pathlib import Path

from ecoa_dual_core.baselines.direct import DirectResidualUpdater
from ecoa_dual_core.baselines.ema_thresh import ThresholdedEMAUpdater
from ecoa_dual_core.baselines.hmm_updater import HMMFaultStateUpdater
from ecoa_dual_core.core.dual_core import DualCoreSystem
from ecoa_dual_core.core.types import MethodResult, Regime
from ecoa_dual_core.eval.metrics import (
    detection_delay,
    disturbance_false_update,
    ledger_volatility,
    summarize,
    unknown_overcommitment,
)
from ecoa_dual_core.eval.captions import write_captions_markdown
from ecoa_dual_core.eval.plots import (
    write_dual_core_trajectory_svg,
    write_mechanism_mermaid,
    write_mechanism_svg,
    write_summary_svg,
)
from ecoa_dual_core.eval.tables import write_table_latex, write_table_markdown
from ecoa_dual_core.sim.regimes import generate_trial


def _results_for_method(method_runner, steps: int, seeds: list[int]) -> list[MethodResult]:
    results: list[MethodResult] = []
    for seed in seeds:
        for regime in Regime:
            events = generate_trial(regime, steps, seed)
            results.append(method_runner.run(events, seed))
    return results


def _aggregate_stats(results: list[MethodResult]) -> list[dict[str, float | str]]:
    methods = sorted({result.method_name for result in results})
    stats: list[dict[str, float | str]] = []

    for method in methods:
        method_results = [result for result in results if result.method_name == method]
        volatility_values = [ledger_volatility(result) for result in method_results if result.regime == Regime.NOMINAL.value]
        disturbance_values = [
            disturbance_false_update(result) for result in method_results if result.regime == Regime.DISTURBANCE.value
        ]
        wear_values = [detection_delay(result, Regime.WEAR.value) for result in method_results if result.regime == Regime.WEAR.value]
        deformation_values = [
            detection_delay(result, Regime.DEFORMATION.value)
            for result in method_results
            if result.regime == Regime.DEFORMATION.value
        ]
        unknown_values = [
            unknown_overcommitment(result) for result in method_results if result.regime == Regime.UNKNOWN.value
        ]

        vol_mean, vol_std = summarize(volatility_values)
        dist_mean, dist_std = summarize(disturbance_values)
        wear_mean, wear_std = summarize(wear_values)
        deform_mean, deform_std = summarize(deformation_values)
        unk_mean, unk_std = summarize(unknown_values)

        stats.append(
            {
                "Method": method,
                "volatility_mean": vol_mean,
                "volatility_std": vol_std,
                "disturbance_mean": dist_mean,
                "disturbance_std": dist_std,
                "wear_mean": wear_mean,
                "wear_std": wear_std,
                "deformation_mean": deform_mean,
                "deformation_std": deform_std,
                "unknown_mean": unk_mean,
                "unknown_std": unk_std,
            }
        )

    return stats


def _aggregate_rows(stats: list[dict[str, float | str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in stats:
        rows.append(
            {
                "Method": str(item["Method"]),
                "Self-ledger Volatility": f'{float(item["volatility_mean"]):.4f} +/- {float(item["volatility_std"]):.4f}',
                "False Self-Update Rate": f'{float(item["disturbance_mean"]):.4f} +/- {float(item["disturbance_std"]):.4f}',
                "Detection Delay (Wear)": f'{float(item["wear_mean"]):.4f} +/- {float(item["wear_std"]):.4f}',
                "Detection Delay (Deformation)": f'{float(item["deformation_mean"]):.4f} +/- {float(item["deformation_std"]):.4f}',
                "Unknown Overcommitment": f'{float(item["unknown_mean"]):.4f} +/- {float(item["unknown_std"]):.4f}',
            }
        )
    return rows


def _write_summary(rows: list[dict[str, str]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_audit(results: list[MethodResult], output_dir: Path, audit_seed: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        if result.method_name != "Proposed Dual-Core mechanism" or result.seed != audit_seed:
            continue
        audit_path = output_dir / f"audit_{result.regime}_seed_{audit_seed}.jsonl"
        with audit_path.open("w", encoding="utf-8") as handle:
            for entry in result.audit:
                handle.write(
                    json.dumps(
                        {
                            "t": entry.t,
                            "regime": entry.regime,
                            "residual": entry.residual,
                            "residual_norm": round(entry.residual_norm, 6),
                            "mode": entry.mode,
                            "top_hypothesis": entry.top_hypothesis,
                            "confidence": round(entry.confidence, 6),
                            "gate_open": entry.gate_open,
                            "gate_reason": entry.gate_reason,
                            "ledger": entry.ledger,
                            "note": entry.note,
                        },
                        ensure_ascii=True,
                    )
                    + "\n"
                )


def run_experiment(config: dict) -> tuple[list[dict[str, str]], Path, list[Path]]:
    experiment_config = config["experiment"]
    baseline_config = config["baselines"]
    dual_core_config = config["dual_core"]
    gate_config = config["gate"]

    steps = int(experiment_config["trial_steps"])
    seeds = [int(seed) for seed in experiment_config["seeds"]]
    output_dir = Path(config["project_root"]) / str(experiment_config["output_dir"])
    audit_seed = int(experiment_config["audit_seed"])

    methods = [
        DirectResidualUpdater(step_size=float(baseline_config["direct_step"])),
        ThresholdedEMAUpdater(
            alpha=float(baseline_config["ema_alpha"]),
            threshold=float(baseline_config["ema_threshold"]),
            step_size=float(baseline_config["ema_step"]),
        ),
        HMMFaultStateUpdater(commit_threshold=float(baseline_config["hmm_commit_threshold"])),
        DualCoreSystem(dual_core_config=dual_core_config, gate_config=gate_config),
    ]

    all_results: list[MethodResult] = []
    for method in methods:
        all_results.extend(_results_for_method(method, steps, seeds))

    stats = _aggregate_stats(all_results)
    rows = _aggregate_rows(stats)
    _write_summary(rows, output_dir)
    _write_audit(all_results, output_dir, audit_seed)
    figure_paths = [
        write_summary_svg(stats, output_dir / "figure_metrics.svg"),
        write_dual_core_trajectory_svg(all_results, audit_seed, output_dir / "figure_dual_core_trajectories.svg"),
        write_mechanism_svg(output_dir / "figure_dual_core_mechanism.svg"),
        write_mechanism_mermaid(output_dir / "figure_dual_core_mechanism.mmd"),
        write_captions_markdown(stats, output_dir / "captions.md", audit_seed),
        write_table_markdown(stats, output_dir / "table1.md"),
        write_table_latex(stats, output_dir / "table1.tex"),
    ]
    return rows, output_dir, figure_paths

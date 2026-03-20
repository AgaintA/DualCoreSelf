from __future__ import annotations

from pathlib import Path


def _format_value(mean: float, std: float) -> str:
    return f"{mean:.4f} +/- {std:.4f}"


def _format_value_tex(mean: float, std: float) -> str:
    return f"{mean:.4f} $\\pm$ {std:.4f}"


def write_table_markdown(stats: list[dict[str, float | str]], output_path: Path) -> Path:
    lines = [
        "# Table 1",
        "",
        "| Method | Self-ledger Volatility | False Self-Update Rate | Detection Delay (Wear) | Detection Delay (Deformation) | Unknown Overcommitment |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for item in stats:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["Method"]),
                    _format_value(float(item["volatility_mean"]), float(item["volatility_std"])),
                    _format_value(float(item["disturbance_mean"]), float(item["disturbance_std"])),
                    _format_value(float(item["wear_mean"]), float(item["wear_std"])),
                    _format_value(float(item["deformation_mean"]), float(item["deformation_std"])),
                    _format_value(float(item["unknown_mean"]), float(item["unknown_std"])),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "Mean +/- standard deviation across repeated seeds. Lower is better for all metrics.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_table_latex(stats: list[dict[str, float | str]], output_path: Path) -> Path:
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Quantitative comparison across update mechanisms. Lower is better for all metrics. Values are mean $\\pm$ standard deviation across repeated seeds.}",
        "\\label{tab:quantitative-comparison}",
        "\\begin{tabular}{lccccc}",
        "\\hline",
        "Method & Self-ledger Volatility & False Self-Update Rate & Detection Delay (Wear) & Detection Delay (Deformation) & Unknown Overcommitment \\\\",
        "\\hline",
    ]

    for item in stats:
        lines.append(
            " & ".join(
                [
                    str(item["Method"]),
                    _format_value_tex(float(item["volatility_mean"]), float(item["volatility_std"])),
                    _format_value_tex(float(item["disturbance_mean"]), float(item["disturbance_std"])),
                    _format_value_tex(float(item["wear_mean"]), float(item["wear_std"])),
                    _format_value_tex(float(item["deformation_mean"]), float(item["deformation_std"])),
                    _format_value_tex(float(item["unknown_mean"]), float(item["unknown_std"])),
                ]
            )
            + " \\\\"
        )

    lines.extend(
        [
            "\\hline",
            "\\end{tabular}",
            "\\end{table*}",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path

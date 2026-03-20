from __future__ import annotations

from html import escape
from pathlib import Path

from ecoa_dual_core.core.types import MethodResult, Regime


METHOD_COLORS = {
    "Direct residual-to-self": "#8c2d04",
    "Thresholded EMA": "#d94801",
    "HMM updater": "#2b8cbe",
    "Proposed Dual-Core mechanism": "#2ca25f",
}

METHOD_LABELS = {
    "Direct residual-to-self": "Direct",
    "Thresholded EMA": "EMA",
    "HMM updater": "HMM",
    "Proposed Dual-Core mechanism": "Dual-Core",
}


def _svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfbf8" />',
        '<style>',
        'text { font-family: "Segoe UI", Arial, sans-serif; fill: #1f2937; }',
        '.title { font-size: 26px; font-weight: 700; }',
        '.subtitle { font-size: 14px; fill: #4b5563; }',
        '.panel-title { font-size: 15px; font-weight: 700; }',
        '.axis { font-size: 11px; fill: #6b7280; }',
        '.legend { font-size: 12px; }',
        '</style>',
    ]


def _svg_footer(lines: list[str]) -> str:
    return "\n".join(lines + ["</svg>"])


def _metric_specs() -> list[tuple[str, str]]:
    return [
        ("volatility_mean", "Self-ledger Volatility"),
        ("disturbance_mean", "False Self-Update Rate"),
        ("wear_mean", "Detection Delay (Wear)"),
        ("deformation_mean", "Detection Delay (Deformation)"),
        ("unknown_mean", "Unknown Overcommitment"),
    ]


def write_summary_svg(stats: list[dict[str, float | str]], output_path: Path) -> Path:
    width = 1500
    height = 900
    panel_width = 430
    panel_height = 260
    origin_x = 70
    origin_y = 120
    gap_x = 40
    gap_y = 55

    lines = _svg_header(width, height)
    lines.append('<text x="70" y="52" class="title">ECOA Dual-Core Quantitative Comparison</text>')
    lines.append(
        '<text x="70" y="78" class="subtitle">Five paper-aligned metrics across Direct, EMA, HMM, and Dual-Core methods</text>'
    )

    metric_specs = _metric_specs()
    methods = [str(item["Method"]) for item in stats]

    for index, (metric_key, title) in enumerate(metric_specs):
        col = index % 2
        row = index // 2
        x = origin_x + col * (panel_width + gap_x)
        y = origin_y + row * (panel_height + gap_y)
        panel_values = [float(item[metric_key]) for item in stats]
        panel_stds = [float(item[metric_key.replace("_mean", "_std")]) for item in stats]
        max_value = max(panel_values + [0.001])
        if max_value == 0.0:
            max_value = 1.0

        lines.append(f'<rect x="{x}" y="{y}" width="{panel_width}" height="{panel_height}" rx="14" fill="#ffffff" stroke="#d1d5db" />')
        lines.append(f'<text x="{x + 18}" y="{y + 28}" class="panel-title">{escape(title)}</text>')

        chart_x = x + 20
        chart_y = y + 48
        chart_w = panel_width - 40
        chart_h = panel_height - 80
        baseline_y = chart_y + chart_h
        lines.append(f'<line x1="{chart_x}" y1="{baseline_y}" x2="{chart_x + chart_w}" y2="{baseline_y}" stroke="#9ca3af" />')
        lines.append(f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{baseline_y}" stroke="#9ca3af" />')

        bar_gap = 16
        bar_width = (chart_w - bar_gap * (len(methods) + 1)) / len(methods)

        for tick_index in range(5):
            tick_value = max_value * tick_index / 4
            tick_y = baseline_y - (tick_value / max_value) * chart_h
            lines.append(f'<line x1="{chart_x}" y1="{tick_y}" x2="{chart_x + chart_w}" y2="{tick_y}" stroke="#eef2f7" />')
            lines.append(f'<text x="{chart_x - 8}" y="{tick_y + 4}" text-anchor="end" class="axis">{tick_value:.2f}</text>')

        for method_index, method in enumerate(methods):
            value = panel_values[method_index]
            std = panel_stds[method_index]
            bar_x = chart_x + bar_gap + method_index * (bar_width + bar_gap)
            bar_h = (value / max_value) * chart_h if max_value else 0.0
            bar_y = baseline_y - bar_h
            color = METHOD_COLORS[method]
            lines.append(f'<rect x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_width:.1f}" height="{bar_h:.1f}" rx="8" fill="{color}" />')

            err_h = (std / max_value) * chart_h if max_value else 0.0
            err_top = max(chart_y, bar_y - err_h)
            center_x = bar_x + bar_width / 2
            lines.append(f'<line x1="{center_x:.1f}" y1="{err_top:.1f}" x2="{center_x:.1f}" y2="{bar_y:.1f}" stroke="#111827" />')
            lines.append(f'<line x1="{center_x - 7:.1f}" y1="{err_top:.1f}" x2="{center_x + 7:.1f}" y2="{err_top:.1f}" stroke="#111827" />')
            lines.append(f'<text x="{center_x:.1f}" y="{baseline_y + 18}" text-anchor="middle" class="axis">{METHOD_LABELS[method]}</text>')
            lines.append(f'<text x="{center_x:.1f}" y="{bar_y - 8:.1f}" text-anchor="middle" class="axis">{value:.2f}</text>')

    legend_y = 835
    legend_x = 80
    for method in methods:
        color = METHOD_COLORS[method]
        label = METHOD_LABELS[method]
        lines.append(f'<rect x="{legend_x}" y="{legend_y - 12}" width="18" height="18" rx="4" fill="{color}" />')
        lines.append(f'<text x="{legend_x + 26}" y="{legend_y + 2}" class="legend">{escape(label)}</text>')
        legend_x += 150

    output_path.write_text(_svg_footer(lines), encoding="utf-8")
    return output_path


def _polyline(points: list[tuple[float, float]], color: str, width: float = 2.5, opacity: float = 1.0) -> str:
    joined = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polyline fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}" points="{joined}" />'
    )


def write_dual_core_trajectory_svg(results: list[MethodResult], audit_seed: int, output_path: Path) -> Path:
    target_results = [
        result
        for result in results
        if result.method_name == "Proposed Dual-Core mechanism"
        and result.seed == audit_seed
        and result.regime in {
            Regime.DISTURBANCE.value,
            Regime.WEAR.value,
            Regime.DEFORMATION.value,
            Regime.UNKNOWN.value,
        }
    ]
    regime_order = [
        Regime.DISTURBANCE.value,
        Regime.WEAR.value,
        Regime.DEFORMATION.value,
        Regime.UNKNOWN.value,
    ]
    target_results.sort(key=lambda item: regime_order.index(item.regime))

    width = 1500
    height = 1120
    lines = _svg_header(width, height)
    lines.append('<text x="70" y="52" class="title">Dual-Core Diagnostic Trajectories</text>')
    lines.append(
        f'<text x="70" y="78" class="subtitle">Audit seed {audit_seed}: residual norm, interpreter confidence, and persistent writes</text>'
    )

    panel_x = 70
    panel_y = 110
    panel_w = 1360
    panel_h = 220
    gap_y = 30
    mode_colors = {
        "normal": "#f3f4f6",
        "suspect": "#fff7ed",
        "probe": "#eff6ff",
        "confirmed": "#ecfdf5",
        "unknown": "#fdf2f8",
    }

    for index, result in enumerate(target_results):
        x = panel_x
        y = panel_y + index * (panel_h + gap_y)
        chart_x = x + 20
        chart_y = y + 40
        chart_w = panel_w - 40
        chart_h = panel_h - 70
        baseline_y = chart_y + chart_h
        steps = len(result.audit)
        max_residual = max([entry.residual_norm for entry in result.audit] + [1.0])

        lines.append(f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="14" fill="#ffffff" stroke="#d1d5db" />')
        lines.append(f'<text x="{x + 20}" y="{y + 26}" class="panel-title">{escape(result.regime.title())}</text>')

        for audit_index, entry in enumerate(result.audit):
            segment_x = chart_x + (audit_index / max(1, steps)) * chart_w
            next_x = chart_x + ((audit_index + 1) / max(1, steps)) * chart_w
            fill = mode_colors.get(entry.mode, "#f3f4f6")
            lines.append(
                f'<rect x="{segment_x:.2f}" y="{chart_y}" width="{max(1.0, next_x - segment_x):.2f}" height="{chart_h}" fill="{fill}" opacity="0.45" />'
            )

        lines.append(f'<line x1="{chart_x}" y1="{baseline_y}" x2="{chart_x + chart_w}" y2="{baseline_y}" stroke="#9ca3af" />')
        lines.append(f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{baseline_y}" stroke="#9ca3af" />')

        residual_points: list[tuple[float, float]] = []
        confidence_points: list[tuple[float, float]] = []

        for audit_index, entry in enumerate(result.audit):
            px = chart_x + (audit_index / max(1, steps - 1)) * chart_w
            residual_y = baseline_y - (entry.residual_norm / max_residual) * chart_h
            confidence_y = baseline_y - entry.confidence * chart_h
            residual_points.append((px, residual_y))
            confidence_points.append((px, confidence_y))

        lines.append(_polyline(residual_points, "#111827", width=2.7))
        lines.append(_polyline(confidence_points, "#2563eb", width=2.3, opacity=0.95))

        onset_step = result.onset_step
        if onset_step is not None:
            onset_x = chart_x + (onset_step / max(1, steps - 1)) * chart_w
            lines.append(f'<line x1="{onset_x:.2f}" y1="{chart_y}" x2="{onset_x:.2f}" y2="{baseline_y}" stroke="#7c3aed" stroke-dasharray="5 5" />')
            lines.append(f'<text x="{onset_x + 6:.2f}" y="{chart_y + 14}" class="axis">onset</text>')

        for write_step in result.write_steps:
            write_x = chart_x + (write_step / max(1, steps - 1)) * chart_w
            lines.append(f'<line x1="{write_x:.2f}" y1="{chart_y}" x2="{write_x:.2f}" y2="{baseline_y}" stroke="#059669" stroke-width="2.5" />')

        final_ledger = result.ledger_history[-1]
        summary = (
            f"writes={len(result.write_steps)}  "
            f"final health={final_ledger.health:.2f}  "
            f"deformation={final_ledger.deformation:.2f}  "
            f"calibration={final_ledger.calibration:.2f}"
        )
        lines.append(f'<text x="{x + 120}" y="{y + 26}" class="subtitle">{escape(summary)}</text>')

        for tick_index in range(5):
            tick_value = tick_index / 4
            tick_y = baseline_y - tick_value * chart_h
            lines.append(f'<line x1="{chart_x}" y1="{tick_y}" x2="{chart_x + chart_w}" y2="{tick_y}" stroke="#eef2f7" />')
            residual_tick = max_residual * tick_value
            lines.append(
                f'<text x="{chart_x - 8}" y="{tick_y + 4}" text-anchor="end" class="axis">{residual_tick:.2f}</text>'
            )

        lines.append(f'<text x="{chart_x}" y="{baseline_y + 20}" class="axis">0</text>')
        lines.append(f'<text x="{chart_x + chart_w - 18}" y="{baseline_y + 20}" class="axis">t</text>')

    legend_y = 1080
    legend_items = [
        ("#111827", "Residual norm"),
        ("#2563eb", "Interpreter confidence"),
        ("#059669", "Persistent write"),
        ("#7c3aed", "True onset"),
    ]
    legend_x = 80
    for color, label in legend_items:
        lines.append(f'<line x1="{legend_x}" y1="{legend_y - 6}" x2="{legend_x + 18}" y2="{legend_y - 6}" stroke="{color}" stroke-width="3" />')
        lines.append(f'<text x="{legend_x + 26}" y="{legend_y - 2}" class="legend">{escape(label)}</text>')
        legend_x += 220

    output_path.write_text(_svg_footer(lines), encoding="utf-8")
    return output_path


def write_mechanism_mermaid(output_path: Path) -> Path:
    mermaid = """flowchart LR
    R[Residual Stream r_t] --> F[Self-Model Interpreter F]
    X[Auxiliary Context x_t] --> F

    subgraph InterpreterCore[Diagnostic Core]
        F --> H[Hypothesis Scores\\nnominal | disturbance | wear | deformation | unknown]
        H --> M[Diagnostic State Machine\\nnormal -> suspect -> probe -> confirmed or unknown]
    end

    M --> G{Write Gate gamma(i_t)}
    G -->|deny| A[Audit Trail / Keep Ledger Stable]
    G -->|allow| W[Persistent Rewrite G]

    subgraph LedgerCore[Persistent Self-State Core]
        S[(Self Ledger s_t)] --> W
        W --> S2[(Updated Self Ledger s_t+1)]
    end

    S2 --> C[Future Control / Diagnosis / Adaptation]
    A --> C

    classDef signal fill:#f3f4f6,stroke:#6b7280,color:#111827
    classDef diagnostic fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef gate fill:#fef3c7,stroke:#d97706,color:#92400e
    classDef ledger fill:#dcfce7,stroke:#059669,color:#065f46
    classDef outcome fill:#ede9fe,stroke:#7c3aed,color:#5b21b6

    class R,X signal
    class F,H,M diagnostic
    class G gate
    class S,W,S2,A ledger
    class C outcome
"""
    output_path.write_text(mermaid, encoding="utf-8")
    return output_path


def write_mechanism_svg(output_path: Path) -> Path:
    width = 1500
    height = 780
    lines = _svg_header(width, height)
    lines.append('<text x="70" y="52" class="title">Dual-Core Interpret-Then-Write Mechanism</text>')
    lines.append(
        '<text x="70" y="78" class="subtitle">Architecture view of diagnostic interpretation, gated write authority, and persistent self-state update</text>'
    )

    def box(x: int, y: int, w: int, h: int, title: str, subtitle: str, fill: str, stroke: str) -> None:
        lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="2" />')
        lines.append(f'<text x="{x + 18}" y="{y + 32}" class="panel-title">{escape(title)}</text>')
        for idx, chunk in enumerate(subtitle.split("\n")):
            lines.append(f'<text x="{x + 18}" y="{y + 58 + idx * 18}" class="subtitle">{escape(chunk)}</text>')

    def arrow(x1: int, y1: int, x2: int, y2: int, label: str = "", color: str = "#4b5563", dash: bool = False) -> None:
        dash_attr = ' stroke-dasharray="7 6"' if dash else ""
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"{dash_attr} />')
        if x2 >= x1:
            points = f"{x2-12},{y2-8} {x2},{y2} {x2-12},{y2+8}"
        else:
            points = f"{x2+12},{y2-8} {x2},{y2} {x2+12},{y2+8}"
        lines.append(f'<polygon points="{points}" fill="{color}" />')
        if label:
            lx = (x1 + x2) / 2
            ly = (y1 + y2) / 2 - 10
            lines.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" class="axis">{escape(label)}</text>')

    box(90, 160, 230, 90, "Residual Stream r_t", "prediction error\nsensor mismatch\nbody discrepancy", "#f3f4f6", "#9ca3af")
    box(90, 300, 230, 90, "Auxiliary Context x_t", "probe outcomes\ncalibration cues\ntask context", "#f3f4f6", "#9ca3af")

    lines.append('<rect x="390" y="130" width="420" height="360" rx="24" fill="#eff6ff" stroke="#60a5fa" stroke-width="2.5" />')
    lines.append('<text x="414" y="166" class="panel-title">Self-Model Interpreter</text>')
    lines.append('<text x="414" y="190" class="subtitle">Fast diagnostic adaptation is allowed here; persistent rewriting is not.</text>')

    box(430, 220, 340, 90, "Hypothesis Accumulator", "nominal | disturbance | wear |\ndeformation | unknown", "#dbeafe", "#2563eb")
    box(430, 350, 340, 100, "Diagnostic State Machine", "normal -> suspect -> probe -> confirmed\nor remain unknown / cautious", "#dbeafe", "#2563eb")

    box(900, 255, 220, 100, "Write Gate gamma(i_t)", "open only under mediated,\nclass-specific, auditable evidence", "#fef3c7", "#d97706")

    lines.append('<rect x="1180" y="130" width="240" height="360" rx="24" fill="#ecfdf5" stroke="#34d399" stroke-width="2.5" />')
    lines.append('<text x="1202" y="166" class="panel-title">Self-State Core</text>')
    lines.append('<text x="1202" y="190" class="subtitle">Slow persistent ledger protected from raw residual contamination.</text>')
    box(1210, 230, 180, 90, "Self Ledger s_t", "health\ndeformation\ncalibration", "#dcfce7", "#059669")
    box(1210, 360, 180, 90, "Persistent Rewrite G", "apply only after\ngate approval", "#dcfce7", "#059669")

    box(430, 560, 300, 90, "Denied Path", "keep self ledger stable\nrecord audit evidence\ncontinue diagnosis", "#f9fafb", "#9ca3af")
    box(940, 560, 360, 90, "Downstream Use", "future control\ndiagnosis\nadaptation and monitoring", "#ede9fe", "#7c3aed")

    arrow(320, 205, 430, 265, "residual evidence")
    arrow(320, 345, 430, 395, "context")
    arrow(600, 310, 600, 350, "aggregate / escalate", "#2563eb")
    arrow(770, 400, 900, 305, "i_t")
    arrow(1120, 305, 1210, 405, "allow")
    arrow(900, 330, 730, 605, "deny", "#6b7280", True)
    arrow(1300, 320, 1300, 360, "current ledger", "#059669")
    arrow(1300, 450, 1300, 560, "s_t+1", "#059669")
    arrow(730, 605, 940, 605, "stable ledger path", "#6b7280")
    arrow(1390, 605, 1300, 605, "", "#7c3aed")

    lines.append('<rect x="86" y="685" width="1320" height="54" rx="14" fill="#ffffff" stroke="#e5e7eb" />')
    lines.append('<text x="108" y="718" class="subtitle">Key principle: residuals may update diagnosis immediately, but persistent self state changes only through explicit interpret-then-write authority.</text>')

    output_path.write_text(_svg_footer(lines), encoding="utf-8")
    return output_path

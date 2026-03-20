from __future__ import annotations

import tomllib
from pathlib import Path

from ecoa_dual_core.eval.runner import run_experiment


def _load_config() -> dict:
    project_root = Path(__file__).resolve().parents[3]
    config_path = project_root / "configs" / "default.toml"
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    config["project_root"] = str(project_root)
    return config


def _print_table(rows: list[dict[str, str]]) -> None:
    headers = list(rows[0].keys())
    widths = {header: len(header) for header in headers}

    for row in rows:
        for header in headers:
            widths[header] = max(widths[header], len(str(row[header])))

    def render(values: list[str]) -> str:
        return " | ".join(value.ljust(widths[header]) for value, header in zip(values, headers, strict=True))

    print(render(headers))
    print("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        print(render([str(row[header]) for header in headers]))


def main() -> None:
    config = _load_config()
    rows, output_dir, figure_paths = run_experiment(config)
    _print_table(rows)
    print()
    print(f"Outputs written to: {output_dir}")
    for figure_path in figure_paths:
        print(f"Figure written to: {figure_path}")


if __name__ == "__main__":
    main()

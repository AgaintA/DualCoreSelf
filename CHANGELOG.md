# Changelog

## v0.1.0 - 2026-03-21

Initial public research prototype release.

### Added

- Dual-Core architecture with:
  - `SelfModelInterpreter`
  - `WriteGate`
  - `SelfStateCore`
- Simplified embodied simulation with five regimes:
  - `nominal`
  - `disturbance`
  - `wear`
  - `deformation`
  - `unknown`
- Three comparison baselines:
  - direct residual-to-self update
  - thresholded EMA update
  - HMM-style fault-state update
- Evaluation pipeline for:
  - self-ledger volatility
  - disturbance false self-update rate
  - wear detection delay
  - deformation detection delay
  - unknown-condition overcommitment
- Generated manuscript-facing assets in `outputs/`, including:
  - `summary.csv`
  - `figure_metrics.svg`
  - `figure_dual_core_trajectories.svg`
  - `figure_dual_core_mechanism.svg`
  - `captions.md`
  - `table1.md`
  - `table1.tex`
  - audit trace `.jsonl` files

### Notes

- This release is intended as a proof-of-mechanism research prototype rather than a production diagnosis system.

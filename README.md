# DualCoreSelf

Proof-of-mechanism research prototype for the paper *Separating Fault Diagnosis from Persistent Self State: A Dual-Core Mechanism for Conservative Self-Update*.

This repository studies one narrow architectural idea: residuals can update diagnostic belief quickly, but persistent self state should be rewritten only through an explicit interpret-then-write gate.

## What This Repository Contains

- A simplified embodied simulation with five regimes:
  - `nominal`
  - `disturbance`
  - `wear`
  - `deformation`
  - `unknown`
- A Dual-Core implementation with:
  - `SelfModelInterpreter`
  - `WriteGate`
  - `SelfStateCore`
- Three comparison baselines:
  - direct residual-to-self update
  - thresholded EMA update
  - HMM-style fault-state update
- Evaluation code for:
  - self-ledger volatility
  - false self-update rate under disturbance
  - detection delay under wear
  - detection delay under deformation
  - unknown-condition overcommitment
- Output generation for summary tables, figure assets, and audit traces

## Quick Start

Requirements:

- Python 3.11+

Run from the project root:

```powershell
python run_experiment.py
```

## Outputs

Running the experiment writes results to `outputs/`, including:

- `summary.csv`
- `figure_metrics.svg`
- `figure_dual_core_trajectories.svg`
- `figure_dual_core_mechanism.svg`
- `captions.md`
- `table1.md`
- `table1.tex`
- audit trace `.jsonl` files

## Current Prototype Result Shape

In the current prototype, the Dual-Core mechanism is intentionally more conservative than faster baselines:

- `False Self-Update Rate (disturbance) = 0.0000`
- `Unknown Overcommitment = 0.0000`
- `Detection Delay (wear) = 8.8000 +/- 2.3152`
- `Detection Delay (deformation) = 7.8000 +/- 2.6382`

The point of the repository is not to claim state-of-the-art diagnosis, but to make the diagnostic-persistence separation mechanism concrete, inspectable, and easy to reproduce.

## Project Layout

```text
configs/
outputs/
src/ecoa_dual_core/
  app/
  baselines/
  core/
  eval/
  sim/
run_experiment.py
```

## Related Manuscript Assets

This codebase was used to generate manuscript-facing artifacts such as summary tables, figure files, and trajectory traces for the associated draft.

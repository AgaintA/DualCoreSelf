# ECOA Dual-Core Prototype

Minimal proof-of-mechanism code for the paper "Separating Fault Diagnosis from Persistent Self State: A Dual-Core Mechanism for Conservative Self-Update".

This prototype focuses on the paper's main architectural claim:

- residuals should update diagnosis quickly;
- persistent self state should update only through an explicit gate.

## What Is Included

- a simplified embodied simulation with five regimes:
  - `nominal`
  - `disturbance`
  - `wear`
  - `deformation`
  - `unknown`
- a `DualCoreSystem` implementing:
  - `SelfModelInterpreter`
  - `WriteGate`
  - `SelfStateCore`
- three baselines:
  - direct residual-to-self update
  - thresholded EMA updater
  - simple HMM-like fault-state updater
- evaluation metrics aligned with the draft paper:
  - self-ledger volatility
  - false self-update rate under disturbance
  - detection delay under wear
  - detection delay under deformation
  - unknown-condition overcommitment
- audit-trace export for qualitative trajectory inspection

## Run

From the project root:

```powershell
python run_experiment.py
```

Outputs are written to `outputs/`.

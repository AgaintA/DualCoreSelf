# DualCoreSelf v0.1.0

First public release of the DualCoreSelf proof-of-mechanism prototype.

## Highlights

- Implements a Dual-Core architecture that separates diagnostic interpretation from persistent self-state rewriting
- Includes five simulation regimes: `nominal`, `disturbance`, `wear`, `deformation`, and `unknown`
- Provides three baselines for comparison: direct update, thresholded EMA, and HMM-style update
- Generates manuscript-ready outputs such as figures, tables, captions, and audit traces

## Current Prototype Result Shape

- `False Self-Update Rate (disturbance) = 0.0000`
- `Unknown Overcommitment = 0.0000`
- `Detection Delay (wear) = 8.8000 +/- 2.3152`
- `Detection Delay (deformation) = 7.8000 +/- 2.6382`

## Scope

This release is a research prototype for demonstrating conservative persistent self updating through diagnostic-persistence separation. It is not presented as a production robotics or industrial fault-diagnosis system.

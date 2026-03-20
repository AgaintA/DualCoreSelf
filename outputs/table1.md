# Table 1

| Method | Self-ledger Volatility | False Self-Update Rate | Detection Delay (Wear) | Detection Delay (Deformation) | Unknown Overcommitment |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct residual-to-self | 0.0041 +/- 0.0002 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 1.0000 +/- 0.0000 |
| HMM updater | 0.0000 +/- 0.0000 | 0.2000 +/- 0.4000 | 5.4000 +/- 1.0198 | 1.6000 +/- 0.4899 | 1.0000 +/- 0.0000 |
| Proposed Dual-Core mechanism | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 8.8000 +/- 2.3152 | 7.8000 +/- 2.6382 | 0.0000 +/- 0.0000 |
| Thresholded EMA | 0.0000 +/- 0.0000 | 1.0000 +/- 0.0000 | 34.6000 +/- 2.0591 | 1.0000 +/- 0.0000 | 1.0000 +/- 0.0000 |

Mean +/- standard deviation across repeated seeds. Lower is better for all metrics.

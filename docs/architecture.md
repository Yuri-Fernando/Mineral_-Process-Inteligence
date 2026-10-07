# Architecture

The package and CLI are the source of truth. The API, dashboard and notebooks call production
modules rather than carrying independent formulas.

```text
real public case studies                explicitly synthetic environment
GeoMet | iron flotation | polymetallic  digital twin + fault injection
                  \                     /
                   data contracts + QC
                            |
            features + models + uncertainty
                            |
             constrained optimization + MPC
                            |
             advisory API / reports / dashboard
```

Case-study data remain separate. Shared code means shared schemas, validation and algorithms, not
an invented unified plant. Optional MLflow can track runs, while the required core always writes
portable JSON/CSV/model artifacts locally.

## Module map

- `domain`: mass/metal conservation, Bond comminution, hydrocyclone curve and flotation kinetics.
- `data`: acquisition, checksums, provenance and case-specific loaders.
- `features` and `quality`: causal temporal transformations and industrial tag flags.
- `models` and `geomet`: temporal soft sensor and spatial-block modeling.
- `simulation`: deterministic plant and reproducible sensor faults.
- `optimization` and `control`: constrained recommendation, Pareto search and economic MPC.
- `monitoring`: PSI, KS and Wasserstein drift signals.
- `api`: advisory boundary; no PLC/DCS write integration exists.

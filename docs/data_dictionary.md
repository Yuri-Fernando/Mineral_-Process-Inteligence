# Core data dictionary

| Field | Unit | Meaning |
|---|---|---|
| `feed_grade` | mass fraction | valuable mineral/metal grade in feed |
| `feed_hardness` | kWh/t proxy | Bond work index used by the compact mill model |
| `feed_f80_um` | µm | 80% passing size of mill feed |
| `p80_um` | µm | 80% passing size of mill product |
| `throughput_tph` | t/h | dry solids throughput proxy |
| `mill_power_kw` | kW | mill power |
| `specific_energy_kwh_t` | kWh/t | mill power divided by throughput |
| `air_flow` | normalized engineering unit | flotation air-flow surrogate |
| `pulp_level` | fraction | normalized pulp level |
| `ph` | pH | pulp acidity/basicity |
| `reagent_gpt` | g/t | total reagent-dose surrogate |
| `recovery` | fraction | recovered valuable metal / feed valuable metal |
| `concentrate_grade` | mass fraction | valuable grade in concentrate |
| `tailings_grade` | mass fraction | valuable grade in tailings |

Dataset-specific headers are preserved at ingestion and mapped only inside their case study. Values
named “normalized engineering unit” must not be converted into a plant setpoint without calibration.

# Safety and claim boundaries

This project is applied research and portfolio software. It has no connector that can write to a
PLC, DCS, historian or production optimization layer.

The recommendation contract is fail-closed. It rejects action when critical state is missing,
quality is `BAD`/`MISSING`, uncertainty exceeds the configured limit, or optimization cannot satisfy
the grade/bounds logic. A `SAFE` result means only “inside this simulator's configured constraints.”
It is not a process-safety certification.

Before any real operation could use this work, a multidisciplinary owner would need plant-specific
data reconciliation, calibration, hazard review, change management, controller validation,
cybersecurity review, operator acceptance and controlled commissioning.

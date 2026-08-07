---
name: stack-bootstrap
description: Bootstrap the smallest VenturaData Python structure for the approved analysis MVP using only declared stack needs. Use when the repository is ready to move from incubation docs to executable code. Do not use when a functional project structure already exists or the task is only product scoping.
---

# Stack bootstrap

- Confirm the approved data MVP before adding dependencies.
- Add only packages required by the first EDA anomaly or dashboard path.
- Separate application code tests and a small reproducible demo dataset.
- Keep large datasets generated outputs and local caches out of Git.
- Add one deterministic smoke test from input dataset to output artifact.
- Document supported formats and local run commands.
- Reuse the shared repository CI standard.

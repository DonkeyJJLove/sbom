# SBOM / AID Process Guard

The repository is maintained around one rule: **measurement without provenance is not evidence, and evidence without a decision contract is not control**.

## Core chain

```text
source tree
→ AID identity
→ SBOM / scan observation
→ delta
→ policy threshold
→ gate
→ stored analytical evidence
```

## Invariants

- AID must bind observations to a stable application identity over time;
- SBOM snapshots are compared through delta, not interpreted as isolated truth;
- CI/CD gates must be deterministic and auditable;
- backend analytics (Elastic or Splunk) stores evidence but does not become the authority source;
- local service data, credentials and runtime state are never committed;
- changes to event schema or gate logic require regression examples.

## `_neuro` / EEG-style interpretation

```text
baseline = accepted SBOM + scan + policy state
burst    = sudden dependency / vulnerability delta
coupling = one dependency change affecting many applications
 drift   = inventory / identity / policy no longer agree
recovery = reconciled identity, evidence and gate state
```

## Review loop

```text
baseline snapshot
→ delta measurement
→ provenance validation
→ policy evaluation
→ falsification / negative test
→ gate decision
→ evidence retention
→ merge
```

Do not convert a dashboard signal directly into authority. The decision path must remain reconstructable from `AID`, event data, policy and gate outcome.

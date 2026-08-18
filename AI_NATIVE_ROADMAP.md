# sbom — AI-Native Enterprise Roadmap

Enterprise role: **Identity / Provenance / Composition Intelligence** with a continuing SBOM supply-chain specialization.

The strongest current pattern is already enterprise-compatible:

```text
stable AID
→ repeated observation
→ sbom / scan
→ delta
→ gate
```

The roadmap preserves this model and extends it through adapters rather than redefining SBOM itself.

## Phase 1 — strengthen the SBOM specialization

- preserve AID propagation across one measurement cycle;
- strengthen CycloneDX/SBOM generation, scanning, signing/attestation and dependency/license analysis;
- preserve summary-first event payloads and full artifact references separately;
- keep `delta` as the primary signal of structural change;
- make `gate` decisions explicit and reproducible.

## Phase 2 — Cyber-Lion identity/event compatibility

Dual-emit or adapt:

```text
AID → EntityIdentity
legacy event → EventEnvelope
sbom/scan/delta → typed observation
legacy gate → GateApplied only when policy + decision semantics are explicit
```

Keep lossless compatibility with existing AID records.

## Phase 3 — provenance graph provider

Expose queryable relationships:

```text
entity
→ vcs/build
→ components
→ SBOM
→ scan
→ delta
→ gate
→ artifact/image
→ execution receipt
```

All graph edges retain source and timestamp.

## Phase 4 — relation / decision composition research

Research additional BOM-like structures for enterprise objects:

```text
Agent composition
Model composition
Tool composition
Swarm composition
Policy/decision lineage
```

These are custom Cyber-Lion provenance structures unless mapped to a real external standard. Do not relabel them as standard SBOM formats.

## Phase 5 — agent/swarm composition adapter

Given an `AgentSpec` or `SwarmSpec`, produce a composition observation containing:

```text
agent/swarm identity
model/provider refs
capability refs
tool refs
memory policy refs
execution-domain refs
source artifact refs
```

The composition record does not grant any listed capability.

## Phase 6 — supply-chain gates for Agent Foundry

Agent admission may require supply-chain evidence such as:

```text
known model/artifact identity
approved image/build provenance
no blocking dependency findings
attestation/signature state
```

Supply-chain gate output is one policy input, not the whole authority decision.

## Required tests

- AID mutation inside one correlated cycle;
- unknown/unreconstructable VCS ref;
- duplicate component/delta observations;
- gate event missing policy/decision;
- tampered provenance link;
- agent composition listing undeclared capability;
- legacy AID round-trip.

## Do not do

```text
AID owner_team == runtime permission
component list == trusted composition
signature == correctness
custom Decision-BOM == established SBOM standard
full payload everywhere == better observability
```

## Enterprise reference

`https://github.com/DonkeyJJLove/ai_platform/tree/master/cyber_lion/enterprise`

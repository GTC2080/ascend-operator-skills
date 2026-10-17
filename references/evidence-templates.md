# Minimal records that prevent ambiguous conclusions

Adapt these fields to the project; do not build an unnecessary database or populate invented evidence. A path/hash pair is meaningful only if the file actually exists and its content was checked. Prefer JSON/YAML records accompanying readable conclusions.

## Contract record

```yaml
operator: geometry-example
inputs:
  boxes: {shape: [B, 4], storage: [float16, float32], layout: contiguous}
  anchors: {shape: [B, 2], storage: [float16, float32], layout: contiguous}
  threshold: {optional: true, storage: float32, absent_value: 0}
attributes:
  ratio: {representation: float32, domain: defined-by-operator}
output: {shape: [B, 1], storage: float32, values: [0, 1]}
numeric_order: [float32_sub, float32_mul, float32_add, float32_add, strict_gt]
compatibility_extensions: []
```

This is a semantic example, not a complete public API or validation schema; fill the actual legal domains, shape limits, invalid-input behavior and aliasing requirements from the operator definition. HALF compatibility belongs in a separate matrix when it is not part of the specified contract.

## Environment and build record

```text
Target chip/architecture, physical/logical device, core counts and UB limits
Driver, runtime, toolkit, compiler, framework, Python/CPU ABI
Discovery timestamp/sources, CPU model/topology, effective affinity/quota
Usable host/device memory, storage, current load and unknown allocation limits
Aggregate host budget across queues/workers/threads; per-device budget and owner
Backend wheel/commit and publisher digest where applicable
Source-only manifest and configuration/required-template hashes
Actual compile/link commands, target and normal/diagnostic mode
Fresh and staged host tiling library path/hash
Fresh, staged and all required embedded kernel/config files and hashes
Runner/helper source and binary hashes
Resolved runtime library/OPP path and evidence method/limits
```

`source_manifest.py` records the exact set of regular files in the selected source tree. It rejects symlinks and stores relative paths. Keep its output outside the tree to avoid hashing itself. It is a provenance check, not a signature, reproducible-build proof or code-security scanner.

## Candidate ledger

| Field | Meaning |
| --- | --- |
| Name/parent | Unique candidate and frozen baseline it changes |
| Mechanism | Expected device dataflow/launch/instruction change |
| Affected regimes | Metadata-driven shapes/dtypes/presence/outputs |
| Source/config identity | Exact state, including generated source and transformation recipe |
| Risk/refutation | Likely failure and what would reject the hypothesis |
| Build/identity | Success/failure, artifact hashes and loader observation level |
| Precision/freshness | Actual counts and complete matrix, not requested CLI flags |
| Instrumentation | Diagnostic library, requested/active tools, exact coverage and raw failures |
| Performance | Protocol, sample/report/CSV hashes, both order directions and variability |
| Decision | Candidate, rejected, unresolved, scoped signal, selected or not run |

Do not edit creation-time notes to pretend they anticipated later results. Add version-bound result records instead.

## Per-case precision/diagnostic record

```text
case_key: unique identity, not only a reused display name
source/build/runner/normal-or-diagnostic library hashes
shape, storage and compute dtype, threshold presence/storage bytes, output dtype
attribute representation/bits, seed and actual input SHA/bytes
oracle version + reference SHA/bytes
actual invocation/allocation/executor policy and completion markers
job ID, worker/run ID, compatibility group, actual artifact binding and device owner
device synchronization/error state, helper completion and confirmed slot handoff
output SHA/bytes/shape/dtype/value-domain and comparison result
requested tool, observed target start, observed matching completion
diagnostics: substantive errors / inactive-or-ignored / operational advisories
state: passed / failed / not-run / incomplete; raw log paths
```

## Performance record

```text
metric + unit + execution boundary + predeclared aggregation/weights
environment, device mapping, workload metadata and fixed fixture hashes
process/stream/executor policy; warmup/active; profiler/PMU settings
resident-worker pause/retirement, retained context/memory and calibration controls
arm-specific actual host geometry and resolved library identity
phase schedule, start/end, resource exclusion and external-load blind spots
capture-job finalization and capture-child completion; process restart/blocked-slot reasons
precheck/postcheck output and unchanged input digests
collector completion; target CSV SHA and exact raw-row audit
raw active duration arrays per arm/direction/case, spread and descriptive ratios
missing/failed/invalidated cases and reasons
local claim versus target-environment observation; inference boundaries
```

An auditor should reject corrupted rows/identities, not merely compute a mean. Record its negative-control checks. Descriptive statistics alone do not establish significance.

## Final handoff

Include one selected source, verified rollback, reproduction recipe and evidence index. State separately: built, loaded, precision, freshness, diagnostics, performance and unresolved scope. Identify which checks must rerun after a change.

For an archive, enumerate regular relative paths, sizes and SHA; read back every member and compare. Before removing task-owned loose files, recheck they have not changed or gained new members. Do not pack credentials, personal machine paths, irrelevant home directories or entire caches. Restore to a new directory for a reproduction.

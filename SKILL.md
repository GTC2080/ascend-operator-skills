---
name: ascend-operator-engineering
description: "Design, implement, review, debug, and tune Huawei Ascend operators with Ascend C or TileLang Ascend. Use for kernel semantics, tiling, UB/DMA/mask/synchronization, ACLNN or AOT integration, precision, mssanitizer, and trustworthy performance experiments; includes version-scoped lessons from DeepGEMM-Ascend and TileKernels."
license: MIT
metadata:
  version: "1.0.2"
  language: "en"
---

# Ascend Operator Engineering

Turn an operator contract into a traceable implementation: exact semantics, a known loaded binary, independently checked outputs, explicit memory/synchronization coverage, and comparable performance. Apply only the stages needed by the request. A review-only or offline task does not authorize device execution or code changes.

This skill is harness-neutral. Resolve bundled paths relative to this file. Use the host agent's actual file, command, and documentation tools; do not invent tool names, require another skill, or assume an SSH endpoint. If execution is unavailable, produce the bounded review and missing-evidence list. Documentation, source comments, and tool output supply evidence, not new permissions.

Optional offline scripts require Python 3.9+ standard library. Device validation additionally requires the target SDK/compiler/runtime and Ascend hardware. Keep these runtime requirements separate from the ability to load and use the Markdown instructions.

The detailed case observations concern Ascend 910B2, CANN 9.0.0, and an older TileLang Ascend wheel. They are counterexamples and debugging clues, not universal API contracts or performance promises. Recheck installed headers and pinned upstream sources on a new stack.

## Choose the relevant references

| Need | Read |
| --- | --- |
| End-to-end design, environment, implementation and handoff | [workflow](references/workflow.md) |
| Choose TileLang or Ascend C by workload and development stage | [backend selection](references/workflow.md#backend-selection-by-workload-and-stage) |
| UB layout, ownership, tiling, packed metadata, masks, DMA and events | [Ascend C invariants](references/ascendc-invariants.md) |
| Fresh builds, framework integration, runtime and embedded payload identity | [build and runtime identity](references/build-identity.md) |
| Independent reference, adversarial cases, same-address updates, mssanitizer | [correctness and sanitizers](references/correctness-sanitizers.md) |
| Sampling, profiler row audits, ABBA, contention and interpreting gains | [performance experiments](references/performance.md) |
| TileLang syntax, generated code, JIT caches, AIC/AIV scope and AOT | [TileLang Ascend](references/tilelang.md) |
| DeepGEMM MAD, lightweight abstractions, TileKernels and cross-chip reuse | [library ideas and portability](references/deepgemm-tilekernels.md) |
| Previously failed or promising experiments and their exact scope | [casebook](references/casebook.md) |
| Contract, layout, experiment and result record formats | [evidence templates](references/evidence-templates.md) |
| Version-pinned upstream references and local evidence provenance | [sources](references/sources.md) |

Read the applicable reference before changing fragile code. Do not load every file for a small task. For a new operator, start with workflow and the contract; add backend-specific material when choosing that backend.

## Development sequence

### 1. Establish the contract and the actual caller

Read the operator definition, host registration, kernel, generated API signature, and runner. Record input/output shapes, strides, storage dtype, compute dtype, optional-input presence, scalar attributes, rounding, broadcasting, comparison boundaries, and supported metadata.

Distinguish specified behavior, observed caller behavior, and additional compatibility. FP16 coordinates do not establish FP16 threshold or output. A successful default output path cannot validate an unexecuted compatibility branch. Build the independent oracle before optimizing.

### 2. Establish the target and preserve the baseline

Record actual device/architecture, toolkit and compiler versions, backend commit/wheel, framework/runtime, physical-to-logical device mapping, available vector/cube cores, UB limits, and the generated build template. Resolve SDK symlinks before interpreting headers.

Keep one immutable known baseline. Read old experiment summaries before rediscovering a failed route. Use independent candidate directories and new build directories. Reuse the project build system and dependency set; a new compiler backend is a measured engineering choice, not an automatic upgrade.

Before a new implementation or backend rewrite, apply the [backend selection policy](references/workflow.md#backend-selection-by-workload-and-stage). TileLang is a useful starting preference for rapid prototyping and block/pipeline exploration on a supported stack; established Ascend C is a useful preference for a mature integration or fine tuning of tiny latency-sensitive kernels. Treat these as workload- and stage-dependent heuristics. Record the choice, target support, baseline and evidence that would justify switching; retain an already validated TileLang implementation when it meets the deployment and performance goals.

### 3. Design the complete data path

Write the per-core work and prove full coverage. Ordinary non-atomic output stores need unique ownership; shared updates need an explicit valid atomic/reduction protocol, initialization and numerical-order contract. Separate logical rows, padded rows, allocation capacity and transfer bytes. Account for every UB interval, alignment gap, predicate buffer, API temporary, stage and final store completion. Describe the producer/consumer pipeline for every dependency.

Specialize using legal shape/dtype/presence metadata. Never read changing device tensor values into persistent host tiling or cache results by pointer. Do not delete barriers, padding, mask initialization or state setup solely to shorten code.

### 4. Implement one falsifiable change

Choose a mechanism and a test that could refute it. Start with the smallest complete implementation that preserves the contract; then inspect generated device code. Single-variable experiments help attribution, but substantial structural alternatives are valid when each has an independent baseline and full validation.

For a DSL, inspect generated Ascend C and actual compilation settings. A library's abstractions hide syntax, not the requirements for memory ownership, numeric semantics and synchronization. Compiler output can invalidate source-level assumptions.

### 5. Prove build and runtime identity

Bind source/configuration hashes to the fresh build, staged kernel resources, generated API library, host tiling library, device artifacts, runner and runtime environment. Check every packaging route expected by this template; absence is a failure, not an omitted comparison. Determine the loaded path as far as the available diagnostics allow.

`scripts/verify_embedded_kernel.py` checks a particular ELF64 little-endian Ascend C template's fresh/staged/direct/registry resources. It is optional, has explicit layout limits, and proves packaging consistency only. It does not prove which runtime route executed. Use project-native equivalents for other templates.

Compare device artifacts when changing wrappers. A changed source or API-library hash may leave device instructions unchanged. Identical device text alone does not settle changes to constants, relocations, host tiling or launch geometry.

### 6. Validate precision and input freshness

Run the same independent oracle against real framework/API calls. Include each dtype/presence branch, tiny inputs, alignment/tile/core boundaries, tails, mixed output values and floating-point decision boundaries. Check output dtype/shape, value range, exact bytes or the contract's justified tolerance, and input immutability.

Reuse tensor addresses and metadata while changing values so expected outputs change. Exercise coordinates, thresholds and runtime attributes separately. Test both one-executor and recreated-executor paths if supported; document which actually ran. Validate a new test adapter on a known baseline and with a negative control.

### 7. Validate memory and synchronization separately

Build an independent diagnostic artifact using this build route's actual instrumentation options. Inspect instrumentation sections and linkage. For each requested sanitizer, require its real target start and matching completion, a completed runner, exact output and absence of substantive diagnostics. `exit=0`, a `passed` label, or memcheck alone is insufficient.

Record coverage by source/library hash, tool, shape, dtype, threshold and output metadata. Do not call a diagnostic a false positive merely because a documentation limitation might apply. Preserve unresolved failures and continue permitted offline analysis. Do not benchmark a candidate with unresolved correctness or safety issues as an eligible winner.

### 8. Measure comparable execution

Separate compilation, initialization, host elapsed time, kernel duration, graph execution and application latency. Keep the same runner, cases, output metadata, warmup/active protocol and profiler filters on both arms. Check outputs before and after measurement. Preserve every raw active sample, case identity and failure.

Use ordered paired runs such as A-forward/B-forward/B-reverse/A-reverse, with independent confirmation for promising effects. Audit target row count, operation/core identity, task selection, block count, valid positive durations and CSV hashes. Fixed sample counts and TaskIDs in the casebook belong to that runner, not every profiler.

Exclude build, diagnostic and compression work from performance sampling; hold the exclusion through child-process completion. CPU-only export may run in isolated workers after device capture ends. Record ambiguous isolation as a limitation instead of silently accepting its timing.

### 9. Interpret and combine improvements

Report per-case and per-regime changes, both order directions and variability before an aggregate. Retain a genuine local gain even if the total is flat. Treat it as a scoped signal until confirmed; do not claim every point improved. More cores, stages or smaller tiles can have nonmonotonic effects.

Combine only understood, validated mechanisms and repeat full correctness, safety and paired performance for the new combination. Small pilot wins, smaller code and a high-quality DSL do not imply hardware saturation. External libraries' throughput claims are not evidence for this operator.

### 10. Freeze a reproducible handoff

Deliver the selected source/configuration, source-to-binary identity, independent precision evidence, sanitizer coverage/limitations, raw timing and interpretation, unresolved cases, and a verified baseline rollback. Keep current source and the version that actually ran unambiguous.

Retain necessary generated source, fixtures, manifests, failure logs and target CSVs; do not copy full caches or unrelated machine data. Hash-check archives before cleaning task-owned experiments. Stop when the user changes or ends the goal; do not automatically begin another operator.

## Completion vocabulary

Use precise states: **designed**, **generated**, **compiled**, **linked**, **loaded**, **device-precision passed**, **instrumented checks passed for specified cases**, **local performance observed**, **independently confirmed**, or **unresolved**. Passing one stage does not imply the next. Say what was actually checked, not what the author or helper intended.

This package deliberately contains no account, remote submission, cloud rental, billing, power-control or harness UI workflow.

# End-to-end operator development

## 1. Intake: specify behavior before choosing an implementation

Read the mathematical definition and the complete calling chain: framework wrapper → shape/dtype inference → API registration → workspace/executor preparation → host tiling → device entry → output reconstruction. Record differences between the documented interface and observed callers; investigate them rather than silently changing the contract.

Create a concise contract containing:

- Tensor names, logical/storage shapes, contiguous or strided layouts, dtype, optionality, alignment and aliasing rules.
- Scalar attributes: representation, valid range, update frequency and whether they are compile-time or runtime values.
- Compute dtype, operation order, permitted contraction, reduction order, exactness/tolerance and special-value handling.
- Output dtype, shape and value domain; absent-input semantics; valid broadcasting.
- Target workloads and the performance metric that matters to their caller.

Enforce that contract at the public entry: support or reject actual strides, offsets, aliasing and broadcasts. A contiguous AoS kernel cannot accept arbitrary ND strides merely because shapes match. Test the specified rejection paths before device launch, including invalid dimensions/attributes and resource/tiling overflow.

For the geometry case, storage coordinates may be FP16, but arithmetic is four separate FP32 operations followed by strict comparison. A tiny change at the decision boundary flips a full output bit. For a reduction/GEMM/decomposition, derive its own accuracy contract; do not impose this case's bit-exact rule on every operator.

## 2. Inventory the target without assuming compatibility

Record device model, architecture identifier, physical/logical device mapping, driver/runtime/toolkit/compiler versions, OS/CPU ABI, Python and framework packages, backend version/commit and build options. Query actual core counts and memory capacities; a machine label is not a resource contract.

Inspect generated API headers and installed SDK signatures. Resolve symlinks before following includes. Match documentation to the installed release; the newest website and a same-named function are not proof of compatibility. Capture only relevant environment values, not a dump containing credentials.

When a backend is new to the environment:

For a missing or incompatible TileLang installation, use the [server setup guide](tilelang-installation.md) before attempting operator development.

1. Confirm the wheel/source release, architecture/ABI tags and digest against its publisher.
2. Reuse an existing suitable environment or isolate task dependencies.
3. Verify import, compiler discovery and a minimal official device example separately.
4. Then compile and run the actual operator.

Import success does not prove a required CLI is on PATH. In the case study, Cython was already installed but its launcher was missing from the task PATH; reinstalling did not address that fact. Avoid global changes or repeated installation without a diagnosed need.

## 3. Freeze a useful baseline

Read earlier candidate summaries. Preserve known-good source, configuration, build recipe, binary identities and its verification scope. Do not mutate the baseline during a comparison. Distinguish a historical best observation from the source currently selected for use.

A practical source/results layout is:

```text
operator/
  current/                 selected source only
  experiments/<name>/      isolated candidate source and recipe
  results/<name>/<run>/     reports, raw target CSVs and diagnostics
  baseline/                verified rollback or content-addressed archive
```

Use the project's existing equivalent instead of reorganizing it unnecessarily. Stable helpers belong in shared tooling; experiment-specific scripts stay with their experiment. Identify scripts' callers before moving them.

## 4. Design both algorithm and kernel

Write the algorithm in the contract's numerical domain. Then write the kernel plan:

- Core assignment, interval coverage, tail ownership and actual launch geometry.
- Input layout, field extraction, padding and output layout.
- UB regions, sizes, alignment gaps, scratch reservations and maximum live end address.
- Producer/consumer dependencies by pipeline and stage.
- Optional-input/dtype paths, host guards and workspace lifetime.
- Which runtime values may change without recompilation.

Choose vector, cube, mixed, SIMT or a DSL route because it matches the computation and current hardware. A matrix multiply abstraction is not automatically appropriate for a few elementwise operations with strict intermediate rounding. A compiled probe is useful for API compatibility; it is not an algorithm benchmark.

### Backend selection by workload and stage

Choose an implementation route after fixing the contract, target and development stage. The preferences below are engineering heuristics, not measured claims that one language is always faster or cheaper for an agent. Both routes require tiling decisions, numerical validation, memory/synchronization checks and comparable measurements.

First check feasibility: the actual chip/toolchain/backend must support the required operations, numerical behavior and runtime updates. Confirm the deployment accepts the intended JIT, AOT or framework/API integration. An existing Ascend C template does not establish that a DSL is prohibited; exporting a compatible kernel is an option only after its full integration chain is verified. Respect the user's chosen route when feasible; report a concrete blocker before proposing a change.

| Operator or project characteristic | Starting preference and reason |
| --- | --- |
| New block-structured GEMM/attention, fused vector or reduction work with many plausible tile/layout/pipeline choices | Consider TileLang for a correct prototype and parameter exploration when its supported primitives preserve the contract. Compact expressions and configurable tiles can help implementation; they do not establish device speed. |
| Tiny inputs, very short device durations, few arithmetic steps or strict floating-point decision boundaries | Prefer an established Ascend C path for fine tuning when it exposes the needed launch, copy, mask and synchronization control. TileLang remains eligible if its generated code and device results meet the same requirements. |
| Mature verified Ascend C kernel, fixed integration template or little time for a backend migration | Continue Ascend C and test targeted changes against the preserved baseline. Require a specific capability or performance hypothesis before a rewrite. |
| Validated TileLang kernel with a reproducible compiler/cache path and acceptable deployment | Continue TileLang through tuning and delivery. A successful DSL implementation does not need a hand rewrite solely because delivery is approaching. |
| Required low-level instruction, layout or scheduling control is available through the target SDK but unsupported by the installed DSL | Prefer the supported Ascend C route for that mechanism. Confirm the actual SDK capability; lower-level access does not repair an invalid algorithm or unsupported chip feature. |
| Many dynamic shapes/attributes, frequent specialization or a cold-start/application-latency objective | Compare specialization/cache behavior, startup cost and caller integration as well as steady-state device duration. Choose the route that meets the actual caller's objective. |

Apply the preference to the current stage:

1. **Prototype:** use the feasible route most likely to produce a correct, testable implementation within the task budget. Reuse a valid existing kernel where possible. On a new supported stack with substantial block-level exploration, TileLang is a reasonable first choice; read its [version and code-generation guidance](tilelang.md). Check representative tails, dtype/optional paths and runtime attributes before expanding the search.
2. **Explore:** vary justified algorithm, tile, core and pipeline choices within the selected route. Keep a known-good baseline and a bounded experiment plan. A second backend is an isolated candidate only when it tests a useful hypothesis; do not maintain two full implementations by default.
3. **Fine tune:** inspect the actual generated/device behavior and measured bottleneck. If a tiny kernel has repeatable redundant work that the installed DSL cannot remove, compare an Ascend C alternative. If the TileLang candidate is already correct and competitive, tune it in place. More explicit source control does not guarantee a faster binary.
4. **Integrate and deliver:** retain the route with verified semantics, safety, build/runtime identity and acceptable performance for the intended workload. A backend switch or JIT-to-AOT change is a new candidate requiring the affected validation again, not a packaging-only operation.

Agent convenience includes the whole feedback loop: reproducible compilation, useful errors, inspectable generated code, a trustworthy oracle and automated measurements. Shorter source may reduce authoring work while codegen, cache or adapter failures increase debugging work. Ascend C also has abstraction layers and compiler transformations; do not assume every hand-written expression maps directly to one instruction.

Reconsider a route when a diagnosed compatibility gap, unresolved compiler/integration failure or measured bottleneck justifies the migration cost. Preserve the baseline, define a bounded probe and an acceptance condition, and keep the same public contract. Compare compilation/setup cost separately from steady-state kernel and application time, using equivalent inputs, metadata, calling paths and measurement protocols. If neither route has been tested, report a provisional preference rather than a performance winner.

Record a short decision for a new implementation or proposed switch:

```text
Stage and workload: size regimes, layout, precision and caller metric
Selected route and reason: relevant characteristics and target support evidence
Baseline and validation: preserved candidate and next decisive check
Revisit condition: concrete blocker or measured opportunity; bounded probe
```

## 5. Implement and review the complete mechanism

Prefer the current template and existing dependencies. Keep framework-required CMake, registration and tiling-key files unchanged when the project requires it; hash them to prove this. The number and names of files are template-specific.

For a performance experiment, record:

```text
Mechanism: what instructions/dataflow/launch assignment should change?
Expected benefit: which workload regime, and why?
Risk: what semantics, bounds or dependencies could fail?
Refutation: what generated-code observation or experiment would reject it?
```

Review host, device entry, helper and caller together. With generated code, read the emitted arguments and callee implementations. Do not infer data movement from source tensor shapes alone. If a transformation rewrites generated code, reject unknown structures instead of trying to repair arbitrary syntax.

## 6. Use explicit evidence gates

| Stage | Evidence required before the next claim |
| --- | --- |
| Build | Full successful compile/link, target version/config and fresh artifact manifest |
| Identity | Expected fresh/staged/embedded resources and host tiling; resolved runtime libraries/OPP |
| Precision | Actual device calls, independent reference, metadata/boundary matrix and negative controls |
| Freshness | Same-address value changes and runtime-attribute updates affect outputs correctly |
| Diagnostic | Real requested tools executed on the bound instrumented kernel; exact outputs and raw logs |
| Performance | Normal binary, correct pre/post outputs, isolated comparable capture and audited raw rows |
| Adoption | Confirmed benefit in the intended workload, full new-combination validation and rollback |

Stages can be investigated in parallel when they do not contaminate evidence; an unresolved memory or precision failure prevents an eligible performance/adoption claim. It need not prevent an authorized offline design review.

Do not infer a stage from an author statement or a helper's variable name. Creation-time notes such as “not yet compiled” remain historical notes; later results must be bound to the exact source they tested.

## 7. Make failures informative

Classify the failure layer: import/parse, C++ generation, compilation, linkage, API registration, tiling, load, allocation/metadata, launch, sync, output comparison or instrumentation. Preserve the first substantive error and exact input/configuration.

Change one explanatory factor when diagnosing causality. Identical failure counts can have different causes: this case had both a ratio literal error and an AIC/AIV scalar-ownership error producing 44 incorrect rows. Rerun the smallest affected case, then the affected matrix and full eligible path. Never weaken strict output assertions to hide a compiler error.

Stop on unsupported assumptions and report the bounded missing capability. Repeatedly changing flags without inspecting generated commands or logs increases ambiguity.

## 8. Freeze and close cleanly

Keep selected source, source/config hashes, build instructions, required generated artifacts, independent oracle, fixtures, full failures, target CSVs and interpretation. Large caches/build trees are not default handoff artifacts. Prefer an incremental evidence transfer over repeated copies of already verified files.

Write the report completely before replacing a final report; normalize numeric scalar types first. A serialization failure must not leave a truncated success-looking JSON. Verify archive members by name, size and SHA after reading them back. Before removing task-owned loose experiments, verify they still match the archived snapshot and are not in use.

Restore archives into an independent location for reproduction. Source and script changes invalidate the affected evidence; do not overwrite running scripts or output directories. Record running task processes and incomplete stages when stopping. Follow the user's current stopping goal rather than an earlier open-ended optimization objective.

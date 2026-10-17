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

### Hardware discovery before resource allocation

Before assigning build workers, CPU threads, device jobs or kernel launch geometry, the agent must discover the **current execution machine and its effective allocation**. Run read-only queries in the actual server/container and task environment, not on the local client. Do not inherit a CPU count, device model, memory capacity or worker split from the case study or a previous server. Record a timestamp, query source and units; distinguish advertised capacity, currently accessible capacity and observed performance.

| Inventory | Required facts and suitable query sources |
| --- | --- |
| Host hardware | CPU model, architecture, sockets, physical cores, logical CPUs/SMT and NUMA topology where exposed; on Linux use `uname -m` and `lscpu`. Container/VM output may describe only the visible topology. |
| Effective CPU allocation | Process affinity, online/allowed CPUs and applicable scheduler/cgroup quotas, including ancestor limits. Linux `os.sched_getaffinity(0)` and the process's cgroup membership help locate these; `os.cpu_count()` alone is insufficient. |
| Host memory | Available RAM, effective container memory ceiling/current usage, swap pressure and per-job peak demand; use OS and cgroup observations together. Host total RAM alone is not the task's memory budget. |
| Storage and I/O | Free space in the actual build/cache/output filesystems and relevant I/O contention; distinguish reported capacity from observed build/export throughput. |
| Accelerator hardware | Actual NPU model/variant and architecture, visible physical/logical mapping, allocated devices, device memory and usable Cube/Vector resources. Use `npu-smi info`, supported runtime/platform queries and installed-version documentation; do not infer these from the CPU model or a cloud product label. |
| Software and current state | Driver/runtime/CANN/compiler/backend/framework versions, existing relevant load, device health and available utilization/thermal/throttling counters. Record unavailable fields explicitly rather than treating them as zero or unlimited. |

If a query/tool is unavailable, use another supported read-only source and state the remaining uncertainty. Do not install a monitoring stack, start a long stress test or change quotas just to fill this table. For non-Linux targets use the host's supported equivalents; do not invent universal command flags or SDK property names.

Use verified CPU/quota and host/device memory limits to bound any initial pilot. Reuse an existing representative baseline/build or run a bounded task-relevant pilot to check actual completed-work throughput, CPU/device utilization, memory pressure and I/O behavior; model specifications and peak FLOPS are not measured capacity for this workload. Then choose a phase-specific plan from those observations, ready jobs and each job's nested threads/peak memory, reserving the observed host demand for device orchestration. Increase useful concurrency toward the available allocation and revise it if contention, throttling or lower throughput appears. CPU and NPU assignments have separate budgets.

Save the detected profile, chosen worker/thread/device budgets, evidence and reasons for limits with the experiment record. Refresh discovery after changing server, container, scheduler allocation, visible devices or toolchain, and refresh available-capacity observations as load changes. When a limit is unknown, keep it unresolved and use a bounded provisional plan based on verified capacity; do not assume all host resources are available. Apply the scheduling policy below only after this discovery.

Inspect generated API headers and installed SDK signatures. Resolve symlinks before following includes. Match documentation to the installed release; the newest website and a same-named function are not proof of compatibility. Capture only relevant environment values, not a dump containing credentials.

When a backend is new to the environment:

For a missing or incompatible TileLang installation, use the [server setup guide](tilelang-installation.md) before attempting operator development.

1. Confirm the wheel/source release, architecture/ABI tags and digest against its publisher.
2. Reuse an existing suitable environment or isolate task dependencies.
3. Verify import, compiler discovery and a minimal official device example separately.
4. Then compile and run the actual operator.

Import success does not prove a required CLI is on PATH. In the case study, Cython was already installed but its launcher was missing from the task PATH; reinstalling did not address that fact. Avoid global changes or repeated installation without a diagnosed need.

### Resource utilization by phase

Default to high **useful task throughput** on the allocated server. Do not leave independent ready work serialized on one CPU, or accept a fixed half-core worker limit without checking why it exists. Use as much of the allocation as the task dependencies, memory budget and measurement phase support. Do not create redundant work or busy loops merely to raise utilization.

Use the [detected hardware profile](#hardware-discovery-before-resource-allocation), not a fixed core count. Distinguish host logical CPUs from NPU vector/cube cores. CPU affinity and cgroup quota are separate limits; check the current cgroup and applicable ancestor limits rather than assuming the cgroup mount root describes this process. Keep these checks read-only; do not change quota or affinity to evade the allocation.

Choose workers/build slots from the measured allocation, ready work and memory envelope. With independent single-threaded jobs and sufficient memory, use the available CPU budget; with multithreaded jobs, count compiler subprocesses and native thread pools across all workers to avoid oversubscription. Set supported thread limits per task process, not in global shell configuration. CPU-bound Python may need processes or native code that releases the GIL; adding ordinary Python threads alone does not establish multicore execution.

| Phase | Resource plan |
| --- | --- |
| Native compilation | Use the project's supported parallel build slots. If one target exposes little parallel work, build independent candidates in separate build directories within one total CPU/memory budget. |
| CPU-only TileLang generation/export or parameter preparation | Use isolated worker processes, unique cache/output directories and explicit configuration keys. Confirm the work is actually CPU-only; a JIT wrapper may also launch device jobs. |
| Independent CPU references, source audits, raw CSV export and analysis | Shard independent cases/files and process them in parallel. Preserve deterministic seeds, per-job evidence and failure status; isolate mutable module globals. |
| Device correctness or sanitizer work | Dispatch an artifact-ready job to an available NPU while compatible CPU work continues. Parallelize independent devices only when supported and attributable. On one shared NPU, serialize device jobs by default unless deliberately testing a supported concurrency scenario with bounded device memory and distinct results. |
| Formal kernel-latency capture | Give the target NPU one measurement owner and keep competing build/export/compression/device work out through all capture-child lifetimes. Other-device work is eligible only with demonstrated host/I/O isolation. |

For CMake 3.12+ builds, a supported explicit setting is:

```bash
cmake --build "$TASK_BUILD_DIR" --parallel "$TASK_BUILD_JOBS"
```

`TASK_BUILD_JOBS` is a positive integer chosen from the measured allocation, ready work and memory envelope. `CMAKE_BUILD_PARALLEL_LEVEL` supplies a default only when no explicit parallel option overrides it. Read the real launcher and compiler commands; setting an environment variable does not prove a wrapper honored it. For Make/Ninja or another backend, use its supported bounded job control rather than inventing flags or starting unlimited jobs.

Budget both per-job peak memory and nested thread counts. Increase concurrency toward the useful allocation when capacity permits; reduce it for observed OOM risk, swap/throttling, I/O saturation or lower completed-jobs throughput. Do not reserve half the server arbitrarily, but preserve enough headroom for observed stability. Do not rewrite a dependency-limited compilation or an already efficient kernel solely to make every core busy.

Use overlapping CPU and NPU work queues for compatible tasks, with dedicated isolated windows for formal latency capture. A phase label is a resource requirement, not a global barrier that forces all CPU work to finish before any device validation can start. Multiple allocated devices may have independent queues where the runtime and isolation permit. Follow the scheduling rules below and the [measurement exclusion rules](performance.md#isolate-measurement-from-experiment-machinery).

#### Overlap CPU and NPU work when their dependencies permit

Track ready work by resource class: CPU-only preparation/build/analysis, NPU validation/diagnostics, or exclusive latency capture. Each job needs a stable candidate/artifact identity, prerequisites, host CPU/RAM demand, device/memory demand and distinct output paths. Use the existing task runner or a bounded queue; this policy does not require a new scheduler service or another agent conversation.

Refill both queues on completion and resource-availability events. When a CPU job completes, publish a candidate as NPU-ready only after its required build, artifact binding and test inputs are complete. If CPU capacity becomes available while the NPU is busy with validation or diagnostics, immediately dispatch compatible ready CPU-only work: compile another candidate, generate inputs/reference results or analyze already completed outputs. Do not wait for the NPU job or the entire device batch to finish. When an NPU job finishes, finalize its outputs and release the device slot, then dispatch the next compatible ready validation job without waiting for unrelated CPU jobs. The same resource and shared-state checks apply in both directions:

| Trigger | CPU work | NPU work |
| --- | --- | --- |
| NPU busy; CPU capacity available | Fill available slots with ready builds, input/reference preparation or analysis of completed results | Continue the current validation; do not make CPU dispatch wait for it |
| CPUs busy; NPU available | Keep compatible CPU jobs running and enough host capacity to feed the device | Dispatch the next artifact-ready validation job |
| Capture window | Quiesce competing heavy jobs | Measure the selected candidate against its baseline in isolation |

An idle NPU plus saturated CPUs is a reason to reconsider the host allocation, not to wait passively for the whole CPU batch. Reserve or prioritize the measured CPU/RAM share needed for device orchestration, data preparation and result handling, then use the remaining budget for builds and analysis. Determine the split from the detected allocation and observed demand; there is no fixed build-to-orchestration ratio. Keep the remaining CPU budget busy with distinct useful work.

Before overlap, confirm the jobs do not mutate shared state used by the device worker. Freeze source, executable scripts, generated code, libraries, inputs and runtime settings for each running job. Use private build/cache/staging paths where supported; serialize conflicting OPP registration, library replacement, package installation or toolchain changes. A completed compile alone does not prove another process can safely stage or load that candidate concurrently. Bound queued artifacts, host memory, device memory and I/O as well as worker count.

For a formal latency window, stop admitting competing heavy jobs, let task-owned children reach completion, acquire the existing exclusion mechanism and capture through finalization. Schedule such windows so an unlimited CPU queue cannot starve benchmark work. Resume compatible CPU/NPU dispatch afterward. Do not terminate unrelated jobs or bypass a lock to make room. Timings from validation while CPU jobs are active describe that loaded scenario; they are not eligible isolated kernel-latency samples. A real output or sanitizer failure still requires diagnosis and cannot be dismissed as load.

Dispatch only useful work within the current authorized operator-development scope. If either resource has no compatible ready job, record the missing prerequisite or other idle reason and advance work that can unblock it on the other resource; do not start another operator, repeat completed work or add synthetic load merely to keep CPU or NPU busy. Record CPU/NPU overlap, idle time for each resource, ready-queue wait and completed-work throughput separately from formal kernel timing. This documents resource use; it does not claim measured gains from an unexecuted scheduling plan.

For the kernel itself, choose NPU launch geometry from the workload, actual vector/cube resources, per-core work and measured performance. Large workloads may benefit from all suitable device cores; tiny workloads may finish sooner with fewer. Never translate the host CPU count into an equal NPU block count or force maximum BlockDim without coverage, ownership and comparable latency checks.

Record the phase, actual resource envelope, workers/build slots and nested-thread limits, observed CPU/memory/I/O usage, completed-work throughput and reason for any lower utilization. Verify concurrency in running children or build logs. Tooling throughput and total experiment time are separate from kernel speed; a utilization percentage alone proves neither improvement.

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

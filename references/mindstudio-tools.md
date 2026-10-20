# MindStudio tools for operator engineering

Use this guide when selecting a tool, preparing a diagnostic build or interpreting an operator report. Read only the relevant linked manual. The reviewed documentation is [mindstudio-docs/26.0.0](https://github.com/mindstudio-docs/26.0.0/tree/e5538cc1437535f503ae0d61e6c7624a088ff36c), snapshot `e5538cc1437535f503ae0d61e6c7624a088ff36c`, inspected on 2026-10-19. The repository name identifies a documentation release; it does not establish the installed CANN/tool version or support for a particular chip, feature or calling route.

This is an original tool-selection and evidence workflow, with attributed upstream references. No tool, manual, installer or runtime is bundled. Reviewing these documents did not install tools or run a new device experiment. Retain the [contract and build-identity gates](workflow.md#6-use-explicit-evidence-gates) for both Ascend C and TileLang-generated kernels.

## Select the tool by the question

| Question | Relevant tool and evidence | Boundary |
| --- | --- | --- |
| Which data path or tiling is promising before implementation? | msKPP models instructions, transfers and pipeline costs | A prediction from a selected chip model; it does not compute or validate the operator's real outputs |
| How should a new host/kernel project be scaffolded? | msOpGen creates a template from an operator description | Generate into a new candidate directory; preserve an existing validated build and integration route |
| Where does a device program diverge or stop? | msDebug provides breakpoints, variables, registers and core focus | Requires a supported target, usable symbols and permitted host debugging; an unavailable debugger is not a kernel failure |
| Is there an invalid access, race, uninitialized read or event mismatch? | msSanitizer runs the selected checks on a bound diagnostic artifact | Coverage depends on instrumentation, chip, instruction and caller; record actual activation and omissions |
| Which compute/memory path limits the running kernel? | msOpProf board mode collects operator metrics; simulator mode investigates instruction behavior | Keep board measurements, simulator results and replayed diagnostic metrics distinct |
| Can a CATLASS template's tiling space be searched? | msOpTuner instantiates configurations and measures them on a supported board | The reviewed tool targets CATLASS; it is not a general TileLang/Ascend C autotuner |
| Does the problem concern graph scheduling, allocation footprint or visual inspection? | Consult the separate msprof, msMemScope or MindStudio Insight documentation as appropriate | Allocation footprint is distinct from illegal-access detection; installing a desktop viewer is unnecessary for a headless CSV analysis |

The [msOT overview](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msot/README.md) supplies the toolchain map. At this snapshot the root README also lists msKL and msOpModeling, but the Git tree contains no `mskl/` or `msopmodeling/` documentation directory. Consult their actual separate upstream documentation before proposing commands or compatibility claims.

## Inventory before installing or changing an environment

Start from the [detected hardware and effective allocation](workflow.md#hardware-discovery-before-resource-allocation). Add the actual component paths/versions, compiler options, caller type, supported collection mode and required privileges. Resolve executables and SDK symlinks; a similarly named command from another toolkit can invalidate the comparison.

The reviewed installation guides for msKPP, msDebug, msSanitizer and msOpProf say those tools can already be supplied with CANN. Check the actual installation before adding packages. For example, in the task's server environment:

```bash
command -v msprof
command -v mssanitizer
command -v msdebug
command -v msopgen
```

A missing command is an inventory result, not a reason to execute the other commands or install the whole toolchain. For found executables, read their local help and use the version-reporting mechanism that release actually supports. For the Python-library tool msKPP, inspect the selected environment's package metadata and module location; do not infer absence from a missing `mskpp` executable. An import does not establish that the selected chip model or device integration works.

If installation is necessary and authorized, select a component release compatible with the actual CANN, driver, host architecture and Python ABI. Read its installation guide and inspect installer effects before running it. Use a task-local tooling environment where supported. Keep compiler/runtime/library changes out of an initialized resident NPU worker; apply the [isolation rules](workflow.md#reuse-a-resident-npu-worker-for-compatible-validation) when the environment must change.

Adapt tutorial setup steps to the real project:

- Quick starts reset example directories and prescribe a complete learning environment. Use a new task-owned directory and the current project's dependency requirements; a tutorial's NumPy pin is not a blanket instruction to downgrade a working Torch/TileLang stack.
- The reviewed msOpTuner installation example sets a global plaintext Git credential helper and downloads moving dependencies. Neither is required by this skill. Preserve authentication settings and pin the dependencies actually chosen for a reproducible build.
- Derive build concurrency from the shared CPU/RAM/I/O budget rather than copying `make -j$(nproc)` from an example. Do not give tool builds an independent full-machine budget.
- Simulator library paths/preloads and diagnostic settings belong to a dedicated subprocess. Do not apply them to a live worker, global shell configuration or ordinary board-timing process.

## Model and generate only where useful

The [msKPP quick start](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mskpp/docs/zh/quick_start/mskpp_quick_start.md) uses a Python modeling DSL with `Chip`, `Tensor`, instruction calls and optional trace/metric output. It estimates behavior without hardware execution. It is separate from an executable TileLang or Ascend C implementation.

Describe the actual GM/UB/L1/L0 traffic, layouts, compute operations and dependencies in a supported chip model. Save the model/version, assumptions and predicted costs. Use it to prioritize a bounded set of implementations, then compare predictions with real counters and independent timing. Unmodeled launch/control overhead, unsupported instructions or a different target cost database limit the prediction. A modeled trace or cycle estimate cannot establish precision, synchronization safety, TBest or hardware saturation.

For a new project, the [msOpGen quick start](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopgen/docs/zh/quick_start/msopgen_quick_start.md) demonstrates JSON descriptors and an explicit SoC selection. Derive that selection from the actual target and supported generator syntax. Review generated signatures, required/optional metadata, storage types, package paths and build options. Keep generated scaffolding distinct from implemented numerical behavior. Do not regenerate over a known baseline or install a package over the one used by a running worker.

## Debug a bounded reproduction

Use msDebug for a small failing call with the actual runner, kernel object and source identities. The [debugger quick start](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msdebug/docs/zh/quick_start/msdebug_quick_start.md) describes a separate `-g -O0` build and, for separately deployed kernel objects, `LAUNCH_KERNEL_PATH` pointing to the object whose symbols must be loaded. Confirm the build route and local debugger requirements before adopting those settings.

That quick start requires a host debug switch and privileged access; a container-visible `/proc/debug_switch` value alone may not establish usable host debugging. Read the available state, then report a blocked prerequisite if the permission is unavailable. Do not enable a host switch, add container privileges or change system configuration merely because a tutorial does so. Continue permitted source, output and log analysis.

Break at the first incorrect value or dependency, inspect the intended AIC/AIV core and record the matching source line, variables and memory interval. Keep the debugger process under the same device-ownership mechanism as other jobs. A stopped process still owns resources. Retire it and confirm cleanup before handing the device slot to another job. Debug-build timing is not release-kernel timing.

## Run diagnostics with explicit coverage

Read the [msSanitizer user guide](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mssanitizer/docs/zh/user_guide/mssanitizer_user_guide.md) together with its [build-route configuration](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mssanitizer/docs/zh/user_guide/compile_option_config.md). Choose the current target's actual mode:

- The documented limited mode without sanitizer instrumentation covers certain GM-related invalid or misaligned accesses, with additional optimization/link/caller restrictions. It does not establish full race, initialization, synchronization or local-memory coverage.
- The instrumented route needs the correct compiler **and linker/package** configuration for the template. The manual's kernel-invocation, template-library and msOpGen examples use different integration points. Verify the resulting artifact, runtime linkage and active target checks; accepting a flag or passing `-g` alone is insufficient.
- Chip and instruction restrictions remain even when a mode is called full detection. This snapshot explicitly lists masked vector instructions and multithreaded operators as limitations, and excludes some checks or instrumentation options on Atlas 350. Match the exact installed tool to the actual kernel instructions and record uncovered mechanisms. A documented limitation is not proof that an observed warning is harmless.
- Heap/software-stack checking modes can disable kernel-internal checking. Record the effective mode rather than counting every invocation as a kernel check. The Triton-specific `TRITON_ENABLE_SANITIZER` setting is not evidence of a TileLang instrumentation interface.

After local help confirms these options, select a supported check (`memcheck`, `racecheck`, `initcheck` or `synccheck`) as `TASK_SANITIZER_CHECK` and run it in a separate diagnostic process. This command shape assumes `TASK_INSTRUMENTED_RUNNER` is a prepared executable reproduction that needs no further arguments; add its verified argv when necessary:

```bash
mssanitizer --tool="$TASK_SANITIZER_CHECK" "$TASK_INSTRUMENTED_RUNNER"
```

Select checks by the target and required coverage; these are not four mandatory runs for every task. Preserve each invoked check's return status and logs, require the [actual target start/completion and output validation](correctness-sanitizers.md#each-requested-tool-must-really-execute), and stop adoption on unresolved substantive errors. Before another device job, confirm the previous job completed and the runtime is healthy; uncertain failures follow worker retirement rules rather than an unconditional loop over checks. If using `--log-file`, choose a new per-run file: the documented option overwrites existing contents. Sanitizer `--kernel-name` uses substring matching in this snapshot; audit the target set rather than assuming exact matching.

For TileLang, first identify the generated Ascend C/object and the compiler route that produced it. Prove instrumentation and runtime binding on that route or record missing coverage; a documented Triton or hand-written Ascend C recipe does not automatically instrument a DSL kernel. Preserve source maps where available. Keep normal, debug, simulator and instrumented artifacts/caches separate and never use diagnostic durations as a speedup claim.

## Collect focused operator evidence, then confirm latency

Read the [board-mode manual](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_user_guide.md), [calling-route examples](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_usage.md) and [metric definitions](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_performance_data.md). Validate the app normally before profiling it. At this snapshot the public command shape is `msprof op`; naming a component msOpProf does not guarantee a separate `msopprof` command is available.

Choose a small reproduction with known target launches and correct outputs. The following shape is for an already prepared standalone runner; every `TASK_*` value and any runner arguments must come from the current experiment and local help:

```bash
msprof op --output="$TASK_PROFILE_DIR" \
  --kernel-name="$TASK_KERNEL_FILTER" \
  --launch-count="$TASK_PROFILE_LAUNCHES" \
  --aic-metrics="$TASK_PROFILE_METRICS" \
  --warm-up="$TASK_PROFILE_WARMUP" "$TASK_BOARD_RUNNER"
```

Check the traps before interpreting a report:

1. **Target selection.** Without a name filter the reviewed tool collects the first dispatched operator, and its default launch limit is one. Framework initialization or another kernel can be selected. The profiler's name filter is prefix/pattern based, unlike the sanitizer substring filter. Audit the actual operation, artifact, device, core class and selected launches. `--launch-skip-before-match` counts kernels before filtering; it is not automatically the number of warmups for your operator.
2. **Replay and state.** The reviewed default is kernel replay; application and range replay have different semantics and restrictions. Repeated metric collection can execute kernels or applications multiple times. Confirm that inputs, in-place updates, outputs, RNG and allocations remain valid across that replay. Use a supported appropriate mode or a faithful replay-safe reproduction; do not infer timing equivalence or safety from repeated filenames. Record the effective warmup, replay mode, requested metrics and real collected tasks. Its launch limit is not a raw independent latency-sample count.
3. **Feature support.** Select metrics supported by the exact chip **and caller**. The reviewed `TimelineDetail` route has framework/API restrictions and excludes some callers; `PipeTimeline` is limited to Atlas 350. An A2/910B profiler installation does not make every metric supported. Source hotspots need usable symbols. `NA`, missing columns and failed collection are unavailable evidence rather than zero cost.
4. **Interpretation.** Inspect Cube/Vector/Scalar activity, transfer bandwidth, UB conflicts and cache behavior using their actual field definitions. Overlapping pipe times do not add to total duration. Distinguish model-derived/estimated fields from collected counters. Use evidence to propose a mechanism, then change and revalidate the kernel; a roofline graphic or instruction count does not prove the explanation.
5. **Isolation and completion.** The manual disallows simultaneous profiling tasks on the same device. Use the [existing capture handoff](workflow.md#overlap-cpu-and-npu-work-when-their-dependencies-permit): pause/drain competing jobs, isolate the capture through finalization and checks, and account for any retained resident context. Keep output directories unique, task-owned, without symlink components and within the budget for RAM, disk and collection time. A report produced after interruption is partial until completeness is established. Avoid automatic `--kill=on` when it would skip checks or teardown.

Keep application-call receipts separate from profiler replay. In the eigh Default protocol, each case made five checked application calls and produced five real `OpBasicInfo` sets under `0`…`4`; warmup/launch options and internal replay were recorded separately. These counts describe that runner, not every Default invocation. Missing `OpBasicInfo` or timing leaves collection unconfirmed, and a displayed `Fail` alone does not identify a numerical error or timeout. Preserve the first API, synchronization or exporter error before assigning a cause. A successful application marker alone does not prove complete collection.

For detailed instruction investigation use a separate simulator-compatible build and environment described by the [simulator manual](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_simulator_user_guide.md). Specify the actual modeled SoC and reduce irrelevant work in the reproduction. A kernel filter does not necessarily stop the simulator executing preceding operations. Simulator results remain model evidence, even when their output contains cycle counts or microseconds.

After diagnostics, run the unchanged independent oracle and the [paired native timing protocol](performance.md) on the selected normal artifact. Keep profiler metric/replay runs separate from the calibrated latency dataset. Replacing an existing collector or process-lifetime protocol requires A/A calibration and equivalent A/B conditions. A CSV created by msOpProf does not inherit the task IDs, sample counts or timing semantics of an earlier Torch profiler runner.

## Search configurations and keep resources useful

The reviewed [msOpTuner scope and installation](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msoptuner/docs/zh/install_guide/msoptuner_install_guide.md) target CATLASS and specify an Atlas A2 environment. Verify the current release, template, compiler and device support before using it. Bound the legal search space by storage/layout, UB and memory ownership constraints. A faster configuration must still pass this operator's precision and memory/synchronization gates; a tuning-tool score alone is insufficient.

For a plain Ascend C or TileLang kernel, reuse the existing candidate runner or backend's verified search mechanism. Do not add a CATLASS dependency solely to enumerate tile sizes. Keep promising and failing configurations with source/build identities rather than only a winning parameter tuple.

Apply the [shared CPU/NPU resource policy](workflow.md#resource-utilization-by-phase) to all tool work. Ready CPU modeling, generation, builds and completed-report analysis can fill available host capacity while an independently isolated NPU validation job runs. Device diagnostics use the same device ownership and uncertain-failure retirement rules as validation. Formal latency capture excludes competing work through the full capture-job lifetime. Do not treat detailed profiling as a cheap resident-worker job or leave a debugger owning an apparently idle device. Bound simulator/modeling memory, nested threads, logs and trace volume as part of the same host budget.

## Record what the tool established

With the existing experiment record, retain the tool/version and documentation snapshot; target/caller; source, generated source and artifact hashes; build options; invocation and process environment changes; requested/effective mode and coverage; kernel filter, launches, replay and warmup; raw report/log hashes; output checks; and any unsupported or unconfirmed stage. Preserve whether a result is **modeled**, **simulated**, **debug-observed**, **instrumented**, **board-profiled**, or **independently timed**. One stage does not establish another.

The reviewed [msOpProf documentation license](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/LICENSE) is CC BY 4.0. Its [license notice](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/legal/license_notice.md) separates that documentation license from product-code licensing; the debugger's code notice differs again. This guide condenses and adapts the linked engineering facts and procedures and is not an upstream manual or endorsement. Preserve source attribution and verify component-specific terms before copying upstream documentation, code or binaries; this package's MIT license does not replace theirs.

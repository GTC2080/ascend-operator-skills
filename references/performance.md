# Trustworthy performance engineering

## Define the quantity being optimized

Name the execution boundary: device task duration, graph latency, host API latency, end-to-end application latency, compilation time or experiment throughput. Keep them in separate fields. Python wall time around JIT+launch is not kernel duration.

Freeze the workload distribution and aggregate before measuring. A geometric mean of candidate/baseline latency ratios weights cases differently from the ratio of total latencies; a business-weighted mean answers another question. Do not select whichever aggregate looks best afterward.

Document device/runtime/backend, actual entry, input/output/threshold metadata, process initialization, stream synchronization, profiler/PMU options, warmup and active counts, target filters, expected task geometry and failure handling. Compare all these fields, not just tensor shape.

## Calibrate the measuring instrument

Run same-code A/A controls when introducing a runner, profiler setting, process model or entry path. The historical controls demonstrate why:

| Same G implementation, changed condition | Observed case result | Interpretation |
| --- | --- | --- |
| Process boundary changed | 1.6237→2.3680µs, about+45.84% | This is a protocol effect, not an algorithm change |
| PMU default→explicit None | One direction 2.0611→1.74335µs | Instrumentation can change observations |
| Frozen native G/G, two independent runs | about+0.53% and−0.65% | Small changes can be noise under this protocol |

These observations do not define a universal0.65% noise floor, confidence interval or production-equivalent profiler setting. Measure variability on the actual stack. Small effects require enough independent evidence to distinguish them; repeated runs only help when comparable and correctly audited.

## Freeze data as well as metadata

Generate each case once from its canonical metadata/seed or preserve its actual input files. Every arm/direction reads the same bytes. Record actual storage dtype, reference, attribute bits and hashes. Recheck input digests after capture.

An advancing global RNG creates different case data when order reverses. A metadata-derived seed also changes when output/threshold dtype changes. For a dtype isolation experiment, deliberately retain the same coordinate data and quantize the changed field; do not assume two automatically generated fixtures isolate dtype cost.

Formal output and extra compatibility output are different workloads. Benchmark the path being claimed. A FLOAT-output timing cannot establish a HALF-output Select optimization.

## Freeze a runner, then audit its calls

The case's native protocol was:

```text
one real precheck launch → save a D2H output snapshot
five warmup launches
start collector → five active launches → stop/finalize collector
D2H postcheck, with no extra operator launch
explicit synchronization/teardown
```

The parent checker compared both saved pre/post snapshots against the independent oracle after capture and child completion. This historical runner did not gate warmup on an oracle comparison inside the child. A new runner may use such a gate, but should preserve/calibrate its protocol explicitly.

This is11 real launches, not10 or12. Its active TaskIDs were6–10. Both the counts and IDs are **this runner's contract**, not a general rule. Another runner, graph capture or fused/mixed operator needs its own verified mapping. Five active samples were a fixed comparison convention here, not sufficient statistical power for every optimization.

Record actual executor and workspace reuse. A runner that prepares a new executor per call cannot support a claim that an optimization works under permanent executor reuse.

When investigating a deadline through native ACLNN and framework callers, bind the same input/API and explicitly match their synchronization budget. The eigh deadline probes used 3000 ms; that value is not a general requirement, and their full regression retained its original default synchronization. A default-sync pass does not establish a timed-call pass, and a timed failure is not a latency sample or proof of failure on another chip.

Changing process lifetime or combining cases may reduce device initialization costs, but requires new calibration. Do not compare that report directly with the old process protocol.

The [resident validation-worker policy](workflow.md#reuse-a-resident-npu-worker-for-compatible-validation) permits compatible candidates to reuse Torch/NPU initialization while CPU builds continue. Record process reuse, startup/restart counts and validation throughput separately from device duration. When measuring in that process, calibrate the new protocol with A/A controls and preserve equivalent initialization, warmup, cache and reuse conditions for both arms. Cold-start objectives still need cold-start measurements; validation in a resident process does not replace required fresh-process checks or exclusive performance capture.

## Pair and reverse the experiments

One useful design is:

```text
A forward → B forward → B reverse → A reverse
```

Keep case order exactly mirrored, metadata/bytes unchanged and the same runner mode. In the studied12-case setup this meant48 independent case processes and240 active samples. Other workloads can use a more suitable paired/randomized schedule, but retain order information.

Preserve all raw active durations and report each direction's central tendency and spread. Include medians/ranges or quantiles when useful. Do not discard a slower sample because it contradicts the hypothesis. Do not use the minimum as typical latency. Bimodal samples need to remain visible.

For a case with positive means `A_f,A_r,B_f,B_r`, one descriptive ratio is:

```text
r_case = (B_f + B_r) / (A_f + A_r)
change_percent = 100 * (r_case - 1)
geometric_mean_ratio = exp(mean(log(r_case)))
```

This pools equal-size forward/reverse means; it is not a significance test. Report `B_f/A_f` and `B_r/A_r` as well. Opposing directions should not disappear inside the aggregate. If repetition/workload weights differ, use the predeclared appropriate estimator.

Use small pilots to reject obvious regressions or find regimes. Then test the full workload and independently confirm promising effects, including regressions and failures. A new combination needs its own full evidence.

## Audit the raw target rows

Reject ambiguous or incomplete data. Derive expected fields from the actual operator/collector:

- Exactly the intended output CSV/report set, with hashes and exporter status.
- Complete active sample count and expected task/step identities, no duplicate or missing rows.
- Correct operation, core/task class, logical device, shape, input/output dtype and optional metadata.
- Block count and mixed topology consistent with **that arm's** host tiling.
- Positive, finite, parseable durations and actual pre/post reference/output checks.
- Runner completion, profiler finalization and expected call markers.

The pure-vector case required `AI_VECTOR_CORE`, logical0 and Mix Block Num0. A legitimate GEMM or mixed kernel can require different values; parameterize the audit instead of rejecting every MIX task.

Add negative controls to the auditor: alter row count, task IDs, block count, MIX, duration, input digest or output dtype and verify rejection. A `summary.json` pass flag is not an independent raw-row audit. Historical labels can also be stale: the final Vector4 report retained a `scalar` geometry-selector label, while source/build/payload identified its true implementation.

If capture times out, save partial diagnostics and mark finalization unconfirmed. Stop the affected group and inspect task processes/runtime state before a bounded retry. Never silently drop failed cases or aggregate only surviving samples.

## Isolate measurement from experiment machinery

Compilation, instrumentation, NPU testing and compression can contend with latency capture. The case study invalidated a timing group because compression isolation could not be established.

Use a single task-scoped resource exclusion mechanism covering all relevant entrypoints and the **full capture-job lifetime**, including warmup, active capture, collector finalization, required checks and completion of capture-specific children. On a suitable local system a native file lock is sufficient; another harness can serialize explicitly. Do not invent a second lock per round and bypass an already running job. Follow the [queue handoff rules](workflow.md#overlap-cpu-and-npu-work-when-their-dependencies-permit): pause competing admissions and drain active work before capture. A resident process may remain alive only after an acknowledged idle state and when its retained context/memory is permitted by, and matched across, the calibrated protocol; a frozen independent-process protocol can require retiring it first. Process liveness alone neither extends nor completes a capture job.

Your lock coordinates your jobs, not unknown tenants or system services. Record external-load/clock/thermal observations where available, and their blind spots. Without measurements, frequency, cache and instruction-cache explanations remain hypotheses.

For collectors that export after application completion, keep the capture lease until the expected raw/CSV files finish, their completeness is checked and capture-specific children exit. An exception must contain owned children inside that lease, using the [bounded supervisor rules](workflow.md#7-make-failures-informative); releasing a parent lock while its profiler child remains alive ends isolation prematurely.

CPU-only offline export can be bounded-parallel **after** the capture job is complete and all capture-specific children exit; an allowed idle resident worker need not exit solely to release this window. Use process isolation if a legacy auditor temporarily changes module globals for each arm's expected geometry. A thread pool sharing that state can cross-contaminate A/B validation. Export throughput improvement is not kernel speedup.

Use the [phase resource policy](workflow.md#resource-utilization-by-phase) to fill available CPU capacity during build and offline-analysis phases. Exclusive latency capture is a deliberate measurement phase, not a reason to serialize the entire development workflow. End-to-end throughput/concurrency benchmarks may intentionally include competing requests; name that objective and calibrate its protocol separately instead of mixing its samples with isolated kernel latency.

Outside formal latency capture, independent NPU validation can overlap compatible CPU preparation/build/analysis under the [CPU/NPU queue rules](workflow.md#overlap-cpu-and-npu-work-when-their-dependencies-permit). Keep device feeding responsive and running artifacts immutable. Label timings from that overlap as loaded-workflow observations; collect a fresh isolated comparison for a kernel-speed claim. The capture exclusion is not a global ban on using CPU and NPU simultaneously.

Do not overwrite executing scripts or generated sources. Freeze a revision, result directory and helper hash. After asynchronous transfers or builds, confirm completion before launching dependent work.

## Interpret hardware counters carefully

For msOpProf collection, follow the [MindStudio profiling workflow](mindstudio-tools.md#collect-focused-operator-evidence-then-confirm-latency). Verify the actual kernel/launch selection, supported metrics and replay behavior before analyzing fields. Model/simulator estimates and detailed replayed metrics are separate evidence from the paired native-latency dataset; changing collectors requires calibration rather than inheriting this case's task IDs or sample counts.

Read actual CSV fields and values before saying a counter was uncollected. In the early geometry profile, Vector was roughly0.157–0.286µs while Scalar was0.546–1.517µs. One FP16 small case had stable Vector time while total duration varied by over2µs.

This supports investigating fixed control/data-movement paths. It does not prove a particular scalar instruction caused the variation. Scalar, Vector, MTE2 and MTE3 overlap and must not be summed into total latency. `Duration−AIV` is not automatically CPU launch time. Source-level API counts are not machine instruction counts or time shares.

For each regime, calculate bytes, effective rows/core, allocated rows, tile count, actual cores and expected occupancy. The maximum studied FP32 workload moved about 112 KiB and commonly had one tile/core. Multi-stage buffering needs real cross-tile work to overlap; a larger machine does not make double buffering or full-core launch automatically useful.

## Preserve scoped gains and honest negatives

Examples from the case:

- Raw C math had about2.15% improvement in a large-input pilot, while the full-workload change was only about−0.38% with small-input regressions. Keep the local signal; it is not an all-case win.
- Four rows/core made small vector cases about38–42% faster locally; eight rows/core made them20–52% slower. Do not interpolate core-grain performance.
- StandardIo specialization improved all six FP32 points in both directions in one full run, but Half regressions made its aggregate about+0.50%. Isolate supported regimes before recombining.
- The final FP32 StandardIo/Vector4 combination was about−7.69% locally overall, with small FP32 cases−40.47%/−42.53%; many other points had opposing order effects. Do not say every point improved.
- Repeated local middle-size gains did not transfer to the target evaluation environment. The reason was not established; neither environment's measurements erase the other.

Classify observed, confirmed, inconclusive, regressed and untested separately. Choose specialization from legal metadata, never known input values or answers. A valid partial gain deserves a regime-specific next experiment; an unresolved correctness failure does not deserve a timing-based promotion.

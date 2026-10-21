# Trustworthy performance engineering

## Define the quantity being optimized

Name the execution boundary: device task duration, graph latency, host API latency, end-to-end application latency, compilation time or experiment throughput. Keep these in separate fields. Python wall time around JIT and launch is not kernel duration.

Freeze the workload distribution and aggregate before measuring. A geometric mean of per-case latency ratios weights workloads differently from a ratio of total time or a business-weighted mean. Do not choose the estimator after seeing which looks best.

Record device/runtime/backend, actual entry, input/output/attribute metadata, initialization, synchronization, collector/PMU options, warmup/active counts, target filters, launch geometry and failure handling. Compare all fields between arms.

## Calibrate the measuring instrument

Run same-code A/A controls when introducing or changing the runner, collector, process lifetime, cache state or entry path. Moving process boundaries or enabling counters can change observed latency even when device arithmetic is identical. Measure variability on the actual stack; no fixed percentage is a universal noise floor.

Distinguish independent repeats from multiple samples within one initialized process. Retain order and environmental observations. A small effect needs enough comparable evidence to distinguish it from the protocol's variability.

## Freeze data as well as metadata

Generate a case once from canonical metadata/seed or preserve its stored input. Every arm and order direction reads the same bytes; hash storage representation and recheck input preservation after capture. An advancing global RNG changes data when case order reverses.

For dtype isolation, retain the same conceptual input and deliberately quantize the changed field. Changing output dtype, threshold dtype or presence can select another workload. A default FLOAT-output timing does not establish a HALF-output optimization.

## Freeze a runner, then audit its calls

One possible protocol is:

```text
precheck call and output validation
W warmup calls
collector start -> M measured calls -> collector finalize
postcheck output validation and required synchronization/teardown
```

Choose W and M for the actual task and variability; these symbols are not fixed defaults. Record whether a postcheck reads an existing output or launches another call. Derive expected task/sample identities from actual receipts and collector behavior instead of assuming fixed TaskIDs. A graph or fused operator can map calls to tasks differently.

Bind executor and workspace reuse explicitly. A runner recreating its executor cannot establish permanent-executor performance. Initialization reuse can improve test throughput while leaving warmed kernel duration unchanged. Calibrate process-model changes with A/A and preserve equivalent conditions in A/B; cold-start objectives need cold-start tests.

When comparing native ACLNN and framework callers under a deadline, use the same stored input and artifact and explicitly match their synchronization budgets. A default-sync pass does not establish a timed-call pass. A timeout is a failed timed call, not a valid latency sample or proof of failure on another chip.

The [resident-worker policy](workflow.md#reuse-a-resident-npu-worker-for-compatible-validation) can reduce repeated setup for compatible validation. It does not remove fresh-process or exclusive-capture requirements of the measurement protocol.

## Pair and reverse the experiments

A useful schedule is:

```text
A forward -> B forward -> B reverse -> A reverse
```

Mirror case order and retain input bytes and runner mode. A paired randomized schedule may be more appropriate for another workload; keep its ordering and estimator explicit.

Preserve every raw active duration, including slow samples and failed cases. Report central tendency and spread for each direction. Do not discard contrary samples or use a minimum as typical latency; preserve multimodal behavior.

For equal-size direction groups with positive means `A_f,A_r,B_f,B_r`, one descriptive estimator is:

```text
r_case = (B_f+B_r)/(A_f+A_r)
change_percent = 100*(r_case-1)
geometric_mean_ratio = exp(mean(log(r_case)))
```

This is not a significance test. Report each direction's ratio too; opposing effects must not disappear in the aggregate. For unequal weights/counts, use the predeclared appropriate estimator.

Use pilots to reject obvious regressions or locate regimes, then test the whole target workload and independently confirm promising changes. A final combination needs its own evidence.

## Audit the raw target rows

Derive expectations from the actual implementation and collector:

- Required raw report/CSV files, exporter status and hashes.
- Complete active sample count, correct task/step selection, no missing or duplicate rows.
- Correct operator, device, task/core class, shape, dtype, optionality and scalar attributes.
- Block count and mixed topology consistent with **that arm's** tiling.
- Positive finite durations, runner completion and collector finalization.
- Actual pre/post output checks and unchanged inputs.

A pure vector kernel and a mixed Cube/Vector kernel legitimately need different topology expectations. Do not hard-code one operator's core class or mixed-block count into a general auditor. Include negative controls for altered row count, task identity, geometry, duration, input digest and output metadata.

A summary pass flag or inherited label is not an independent raw-row audit. If capture fails or times out, save partial diagnostics and mark completeness unconfirmed. Stop the affected group, reconcile owned processes/runtime state and follow the [failure policy](workflow.md#7-make-failures-informative). Do not aggregate only surviving cases.

## Isolate measurement from experiment machinery

Compilation, instrumentation, other device tests and compression can contend with capture. Use one task-scoped exclusion mechanism across relevant entrypoints for the full capture lifetime: warmup, active calls, collector finalization, required checks and owned-child completion. A file lock or explicit scheduler serialization can suffice; do not invent a competing lock that bypasses an existing job.

Follow [queue handoff](workflow.md#overlap-cpu-and-npu-work-when-their-dependencies-permit): pause competing admissions and establish completion before capture. A resident context may remain only if idle state is acknowledged and its retained resource state is allowed and matched across arms. A protocol requiring fresh processes must retire it first. Locks coordinate owned jobs, not unknown tenants or system services; record load/clock/thermal observations and their limits.

Keep ownership through asynchronous report/CSV finalization. On exceptions, contain owned children within that exclusion using one bounded shutdown allowance. Releasing a parent lock while its profiler child is alive breaks isolation.

Bounded-parallel CPU export can follow completed capture and capture-child exit. Use isolated processes when an auditor mutates module globals per arm; threads can cross-contaminate geometry. Report export throughput separately from kernel speed.

Outside exclusive latency capture, compatible CPU preparation/build/analysis may overlap correctness validation under the [resource policy](workflow.md#resource-utilization-by-phase). Label timings from such overlap as loaded-workflow observations and collect an isolated comparison for an isolated-latency claim. Never overwrite an executing script, artifact or output directory.

## Interpret hardware counters carefully

Use [focused profiling](mindstudio-tools.md#collect-focused-operator-evidence-then-confirm-latency) to establish actual target selection, supported metrics and replay. Simulator/model estimates and replayed instruction metrics are different evidence from independent native timing.

Read the actual fields before claiming a metric is absent. Stable vector-pipe time with varying total duration suggests investigating other control/transfer paths, but does not identify a particular instruction as the cause. Scalar, Vector and MTE intervals can overlap; do not sum them into total duration. `Duration-AIV` is not automatically CPU launch time. Source API counts are not machine instruction counts.

Calculate bytes moved, logical/padded rows, rows per core, tile count, active cores, live stages and expected occupancy for each regime. Multi-stage buffering requires work that can actually overlap. A small one-tile workload can lose from extra staging or full-core launch. Test a bounded legal configuration space instead of extrapolating from hardware peak specifications.

## Preserve scoped gains and honest negatives

Report per-case/per-direction behavior before an aggregate. A large-input gain can coexist with fixed-cost small-input regressions. More rows/core, cores or stages need not produce monotonic speedups. A dtype-specific improvement can disappear when unrelated paths are combined.

Retain useful scoped effects and test legal metadata specializations, then retest their combination. Preserve differences between environments rather than erasing one result; matching chip or SDK labels alone do not establish comparable callers and conditions.

Classify results as observed, independently confirmed, inconclusive, regressed or untested. Specialize by supported metadata rather than known values or expected answers. An unresolved correctness or safety failure prevents a timing-based promotion.

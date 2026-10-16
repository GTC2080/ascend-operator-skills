# Independent correctness and memory diagnostics

## Build an oracle independent of the optimized path

Use a simple CPU/reference implementation that explicitly follows the contract. Avoid sharing the kernel's indexing, tiling or transformed numerical expression with the oracle. For exact binary outputs, validate shape, dtype, byte count, value domain and elementwise equality; `allclose` alone can accept the wrong interface.

The geometry example used separate NumPy FP32 ufuncs for Sub/Mul/Add/Add after storage quantization. HALF thresholds were first rounded to HALF and then converted to FP32 for the oracle. The original unquantized random value is not the actual device input.

For approximate operators, define justified absolute/relative/residual/orthogonality criteria from their mathematical contract. Do not silently tighten or loosen them to fit a backend. Special values, empty dimensions, unsupported layouts and invalid input behavior follow the operator's own contract.

## A test matrix derived from failure mechanisms

Cover the cross-product that can change the execution path, using representative and adversarial cases rather than an arbitrary universal case count:

| Axis | Examples |
| --- | --- |
| Logical size | minimum; vector/alignment/tile/core boundary−1, boundary, boundary+1; maximum |
| Storage/compute | every supported coordinate/input dtype; separately threshold/output metadata |
| Optionality | truly absent, present zero, present nonzero, supported broadcast |
| Numeric boundaries | exact equality, predecessor/successor floats, cancellation, near-one attributes, extrema |
| Output patterns | all 0, all 1, mixed patterns, tails producing a1 |
| Invocation state | changed content at same addresses; changed scalar attributes; executor policies |
| Memory geometry | legal alignment offsets, tails, canaries and nonaliasing requirements |
| Rejection behavior | wrong rank/dtype/shape/broadcast; unsupported stride/alias; inconsistent optional descriptors; invalid attributes; checked size/tiling/resource limits |

Invalid API cases must follow the contract's error behavior before unsafe launch; do not use a device fault as input validation. For shared-update/reduction operators, add atomic/partial-output initialization, ordering and collision cases instead of imposing pointwise unique-store rules.

The studied small Compare bug passed B1 because the reference happened to be0, while larger small cases incorrectly became all 0. Include tiny cases requiring1 and mixed outputs; a successful first smoke can be accidental.

FP32 near-one constants and separate-multiply-add counterexamples are particularly valuable for a strict comparator. Do not replace a contractually exact comparison with epsilon or FMA to make tests pass.

## Validate the validator

- Cross-check a new runner/adapter against an already verified baseline and another trusted caller where feasible.
- Deliberately corrupt an output and ensure the checker rejects it; check shape and dtype failures too.
- Check serialized fixtures round-trip to the intended dtype, bytes and values.
- Use unique case keys including metadata or a digest. A repeated name used as a dict/NPZ key can overwrite a different threshold case.
- Preflight actual fixture availability and runner argv, not just a CLI's listed choices. Translate dtype names deliberately: a JSON `float32` may not match a runner token `fp32`.
- Do not let a callable fall back to the CPU reference or let the test adapter compute/repair outputs. Record the actual entry/library selected.
- Keep test logs outside an output directory whose fresh-output guard rejects preexisting files.

A host import/preparation failure means the device case did not run. A CPU model of logical lanes cannot settle physical padded reads. Test harness success is a separate result from operator success.

## Same-address freshness tests

Hold allocation addresses and metadata fixed. Change only the intended value field and choose values making expected output change. Update device contents through the real copy/synchronization route before the next invocation. Verify after every call.

Test independently:

1. Threshold values toggling the predicate.
2. Coordinates/anchors changing selected fields and decisions.
3. Runtime attributes near difficult floating-point boundaries.
4. Output-buffer reuse and necessary overwrite of every logical element.

Record what stayed fixed: allocations, descriptors, stream, API handles, workspace and/or executor. If each launch recreates the executor, state that; it does not establish one-executor reuse. Include both patterns only where the API supports them.

Use input digests before and after a batch to detect accidental mutation. Hash fixtures by their actual storage representation. Do not generate positive and reverse-order workloads from one advancing RNG stream: each case must retain the same bytes.

## Build real instrumentation

Use the installed build route's supported sanitizer mechanism. Capture real compiler/link commands and inspect actual device artifacts. A flag accepted by the shell may be ignored by target filtering, applied after package creation, or fail to link its runtime.

Version-scoped case: the CANN9 ASC/asc_opc project needed kernel options `-sanitizer;-g` before package generation. Late/nonmatching SoC filters produced no active device instrumentation. Injecting only lower-level `--cce-enable-sanitizer` generated calls but failed linkage on missing `__sanitizer_report_*` runtime. The working route had nonempty `.init_array_sanitizer_file_mapping`, `.debug_info` and `.debug_line` sections in its device ELFs. Use this as a diagnostic recipe for that route, not mandatory section names for every backend.

Keep instrumented artifacts out of normal performance measurement. Instrumentation can change code generation and timing. A normal build's precision pass does not validate an instrumented library's output, or vice versa.

## Each requested tool must really execute

For memcheck, initcheck, racecheck and synccheck as supported by the current target, retain a per-case record that establishes:

1. Expected runner and instrumented library identities.
2. Correct storage dtype, allocation bytes, optionality and launch geometry.
3. The requested tool's target start for the kernel.
4. A matching tool completion for the same target and no substantive diagnostics.
5. Runner completion and valid exact/tolerated output after the real call.
6. Full raw stdout/log/output and an honest pass/fail/not-run count.

`exit=0` is insufficient. The first case study had hundreds of memcheck entries and an initcheck error despite successful process exit. `No active sanitizer tool` or ignored instrumentation is **not checked**, even when outputs are correct. Memcheck may work without the instrumentation required by other tools; its clean result is not proof they ran.

A permissions advisory about a result directory is a different category from illegal access or synchronization errors. Preserve and classify it; do not claim “no warnings” or automatically label the kernel faulty. Conversely, do not exempt substantive warnings by grouping them with harmless operational advisories.

## Diagnose a warning, do not explain it away

Preserve the first offending instruction/source, memory interval, access size, tool/version and exact metadata. Compare the installed implementation with version-matched documentation. A documented limitation forms a hypothesis; it does not establish that a particular error is a false positive.

Use minimal isolation experiments while retaining semantics:

- Normal versus Counter only after confirming the actual selected overload/mode.
- Complete predicate initialization versus valid-bit-only initialization.
- Explicit buffer lifetimes and temporaries versus SDK-managed allocation.
- One stage/core versus many when isolating ownership or dependency issues.
- Actual HALF threshold/output versus a default FLOAT runner.

Observed limitations matter: count→Normal did not resolve the later HALF scalar Select size2 scratch read at the studied UB location. That failure remained unresolved. Do not inherit safety from a FLOAT path or claim an SDK defect without closure.

For sync warnings, prove whether writes overlap and whether each wait has a corresponding producer. A redundant-wait fix should follow a revised dependency graph and fresh validation, not blind event deletion.

## Coverage is a matrix, not an adjective

Record exact tested source/library, tools, shapes and dtype/presence/output combinations. “30 instrumented checks passed” describes 30 checks, not every legal input. A changed implementation cannot inherit all its parent's coverage merely because it keeps the same operator name.

Keep failures, partial logs and untested branches in the handoff. A timeout or missing tool completion is incomplete; do not merge it into a pass count. Continue permitted analysis, but keep the candidate ineligible for adoption until blocking precision/memory/synchronization issues are resolved.

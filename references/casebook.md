# Troubleshooting patterns for Ascend C and TileLang

Use this catalogue to choose a falsifiable next check from an observed symptom. Each row describes a possible mechanism and a repair/validation method, not a diagnosis established by the symptom alone. Examples are portable engineering patterns; no private project files, run identifiers or unpublished benchmark results are required.

## Contract, build identity and validation

| Symptom or trap | Mechanism to test | Repair and required check |
| --- | --- | --- |
| New source but apparently old behavior | Fresh device resources and embedded registry payload differ | Verify every required fresh/staged/embedded route; rebuild in an independent directory |
| A dtype flag seems sufficient | Storage metadata, scalar attributes and output dtype follow different branches | Inspect actual allocation bytes and API descriptors; test each supported combination |
| Diagnostic process exits successfully | Tools emitted errors or did not execute their target | Read target start/completion and raw diagnostics separately from exit status |
| An optimization is measured through the wrong entry | Default output or compatibility branch differs from the claim | Bind the actual caller and metadata to the measured path |
| Wrapper changes appear slightly faster | Device instructions may be unchanged | Compare device text, constants, relocations and host geometry; run same-code controls |
| Renaming an overload does not change a warning | The selected implementation still uses the same mode | Inspect installed overload/lowering and isolate actual count/repeat/tail behavior |
| Logical predicates look initialized | A consumer reads a wider physical predicate region | Define the full physical read range and test mixed values and tails |
| A faster test harness is treated as a faster kernel | Process initialization or repeated setup was removed | Calibrate the harness on a known baseline with corrupt-output controls; separate setup time |
| Individually promising changes regress when combined | Safety/layout fixes alter the final data path | Validate and measure the final combination, not the sum of isolated pilot gains |

See [build identity](build-identity.md) and [independent correctness](correctness-sanitizers.md).

## Memory, tiling and numerical boundaries

| Symptom or trap | Mechanism to test | Repair and required check |
| --- | --- | --- |
| Direct tiling reads seem simpler | SDK macros may encode static as well as dynamic semantics | Prove host/device layout and each required template route before bypassing macros |
| Skipping aligned zeros gives an unstable win | Padding may still be physically consumed | Prove defined read ranges and confirm the gain independently |
| Scalar/vector counter changes look favorable | Pipelines overlap and counters do not equal total duration | Use field definitions and independent total timing |
| A HALF-aware runner compiles but does not link | Required SDK host dependency is absent | Inspect final linkage, then test true two-byte storage and metadata |
| UB guard passes while regions overlap | Alignment gaps, reserved output or scratch were omitted | Derive the maximum live byte end and update all offsets/guards together |
| Scalar Select scratch warning persists | Changing count to normal mode did not establish valid scratch state | Inspect actual scratch lifetime/width and dtype-specific tool coverage; retain unresolved diagnostics |
| A tiny comparison test passes only when expected output is zero | A short-length path may process no full repeats | Include tiny inputs requiring ones and mixed results; inspect repeat/tail lowering |
| Small-path output is correct but mask diagnostics fail | Upper mask state may remain stale | Restore complete mask state and rerun precision plus instrumentation |
| Only valid predicate bits are cleared | Physical Select-readable bytes remain undefined | Initialize the complete consumer read width |
| HALF-to-FLOAT expansion corrupts rows | Element size changed but stride/capacity did not | Recompute source/destination units and physical extents after conversion |
| A wait is reported redundant | Initialization paths overlap or dependency ownership is wrong | Repair the dependency graph before removing events, then revalidate |
| GM aggregate copy is rejected | Host C++ syntax does not prove device address-space support | Use a supported qualified load route; do not erase qualifiers to silence the error |
| A serialized test silently disappears | Nonunique names overwrite cases with different attributes | Use complete metadata/digest keys and round-trip stored bytes |
| Same code changes speed when process structure changes | Initialization, cache or collector protocol changed | Calibrate A/A before interpreting A/B |
| Compression/export runs during a microbenchmark | Shared CPU, I/O or device resources contaminate capture | Hold one capture exclusion through finalization and owned-child completion |
| Smaller code is reported as an instruction-cache fix | Text size and counters alone do not identify causality | Compare actual artifacts and controlled timing; label the mechanism unconfirmed until tested |

See [Ascend C invariants](ascendc-invariants.md), [performance](performance.md) and [MindStudio](mindstudio-tools.md).

## TileLang frontend, code generation, caches and AOT

| Symptom or trap | Mechanism to test | Repair and required check |
| --- | --- | --- |
| Module imports but command is missing | Python package and launcher PATH differ | Resolve the installed launcher before reinstalling |
| A parser rejects postponed annotations | The installed frontend expects evaluated objects | Check version-specific parsing, use supported syntax and actually compile |
| Backward-aligned tail windows overlap | Multiple ordinary stores own the same output | Use unique tile bases and supported tail transfers, or prove owned/masked stores |
| A two-dimensional singleton output copies incorrectly | Generated copy/helper units differ from assumed shape semantics | Inspect emitted indexing and test a supported continuous representation |
| Conditional copy extent produces invalid C++ | Lowering places a declaration in an argument list | Try explicit full/tail branches and compile multi-tile boundaries |
| A near-one scalar changes decisions | Literal formatting or ABI conversion changed FP32 bits | Check bit patterns through host, generated source and device input |
| JIT works but a fresh-process cache reload fails | Cached symbolic bindings are incomplete or stale | Test a private cache and cold reload; bypassing a cache is not repairing serialization |
| Scalar allocation/indexing fails in the parser | A returned object is a BufferLoad rather than an expected buffer | Inspect parser/IR and use supported public forms; avoid making an internal escape a portable API |
| A consumer sees the scalar initializer instead of the GM value | AIC and AIV hold distinct scalar state | Put producer and consumer in the supported execution scope; waits do not share registers |
| Per-job environment variables do not switch cache | Import-time constants/singletons already fixed the real cache | Set configuration before first import or isolate processes; read effective state back |
| AOT exports pair with the wrong wrapper | Incomplete keys or differing optional-pointer ABI | Key by complete dtype/presence/target/shape metadata and verify the actual function signature |
| Extracting a helper breaks compilation or changes code | Transitive declarations, overloads or device attributes were lost | Preserve the minimal dependency closure, ordering, attributes and upstream license |
| Static UB rewrite passes a CPU model | Pattern matching did not establish device lifetimes | Restrict/reject unsupported forms, inspect generated code and run device safety checks |
| Workspace query cannot find tiling | The template's host registration route is incomplete | Verify its actual separately deployed or OBJECT-linked host tiling route |
| Every case fails before launch after adapting a script | Import-time globals or host preparation are missing | Validate the adapter on the known baseline; do not alter numerical expectations |
| A CLI accepts a compatibility flag | The case list may never execute that branch | Inspect actual dispatched cases, dtype metadata and outputs |
| AOT reduces text substantially without a speedup | Launch, transfer or fixed geometry dominates | Measure the complete intended path; syntax and code size do not imply saturation |

See [TileLang](tilelang.md) and [backend installation](tilelang-installation.md). Symptoms must be reproduced on the installed version before calling them compiler defects.

## Low-level primitives, porting and structural optimization

| Symptom or trap | Mechanism to test | Repair and required check |
| --- | --- | --- |
| A newer-architecture header fails at a low-bit type | An unrelated newer feature entered the include closure | Isolate the needed supported mechanism; one header error does not rule out ordinary MAD |
| A matrix primitive compiles and packages | Operands/layout/accumulator were never initialized and executed | Build one complete initialized tile and compare outputs before a compatibility claim |
| Raw vector math fails after a high-level Cast/Gather | Caller-to-first-raw-operation dependency is missing | Prove and insert the supported boundary event; test the full caller |
| A large-input pilot improves but aggregate is flat | Fixed overhead or other regimes regress | Retain the scoped signal, test relevant regimes and confirm a legal specialization |
| Scalar GM output stays wrong after an extra wait | Ownership, address or unsupported store path is unresolved | Isolate the actual store and bounds; do not label a cache cause or promote timing |
| Ratio-one algebra changes a strict decision | Separate rounding loses a small endpoint before cancellation | Use the explicit FP32 counterexample and preserve the declared operation sequence |
| A replacement passes binary outputs but its rounding is unknown | Typical comparisons hide differing intermediate values | Capture FP32 intermediates and use fused/separate negative controls before the complete path |
| Ordinary DMA is selected from n alone | Base/core/tile addresses violate an independent alignment condition | Prove address and byte-granularity conditions separately; retain a legal tail fallback |
| A transfer-to-vector wait is used before a scalar read | The actual consumer belongs to a different pipeline | Prove MTE-to-S or V-to-S availability for GetValue as required by the target |
| Manual synchronization works only for busy cores | Helper IDs or empty-loop set/wait counts were omitted | Audit all reserved IDs and zero/one/multi-iteration event paths |
| A dtype-specific I/O path is combined with a small-shape grain change | Their dispatch and fixed costs interact | Preserve untouched branches and validate/measure the final metadata-driven combination |
| Few logical scalars use a wider transfer | UB staging must define the physical transaction width | Initialize that width and write only permitted GM bytes |
| More rows/core or more cores become slower | Grain, occupancy and fixed costs interact nonlinearly | Sweep bounded legal configurations on the real workload |
| A local gain does not transfer to another environment | Chip, caller, clock, compiler or process state differs | Preserve both results and establish comparable bindings before assigning a cause |
| One dtype wins while another regresses | Their I/O and conversion paths differ | Specialize only understood metadata regimes and retest the combination |
| An aggregate win hides opposing order effects | Drift or unstable regimes cancel in the mean | Preserve per-case/per-direction samples and independently confirm |
| Sanitizer invocation reports no active tool | Instrumentation was absent or filtered out | Rebuild using the actual supported route and require target start/finish |
| A lower-level sanitizer flag generates unresolved calls | Runtime/link/package integration is incomplete | Use the build system's full diagnostic pipeline |
| Result-directory permission advisory is mixed with access errors | Operational and kernel diagnostics have different meanings | Preserve both categories; do not call substantive memory errors harmless |
| Parallel offline export gets faster | CPU tool throughput improved after capture | Keep that result separate from kernel latency; isolate mutable auditor state |

See [library mechanisms](deepgemm-tilekernels.md) and [910B adaptation](910b-porting.md).

## Eigensolvers and difficult numerical operators

| Symptom or trap | Mechanism to test | Repair and required check |
| --- | --- | --- |
| Mathematical checks pass but direct Q comparison fails | Sign, phase, ordering or invariant-basis ambiguity | Compare the appropriate representation/subspace without changing submitted output |
| Sign alignment still leaves component error | Earlier reduction/solve/backtransform stage differs | Compare captured H/T/Z and the same actual T before changing final layout |
| Relative reconstruction passes but a small root is wrong | Large spectrum hides absolute W error | Preserve an independent small-root oracle and absolute tolerance |
| More secular iterations cannot find a bracket | Origin and endpoint expressions refer to different rounded points | Freeze coordinate/endpoint bits and propagate the first child failure |
| Column normalization passes but full Q is nonorthogonal | Cross-column errors survive unit norms | Check the full Gram matrix; evaluate a justified skew/polar correction |
| Refinement target is unchanged | Eligibility silently skipped because of a numerical-domain condition | Record actual apply/skip per matrix/wave and test the intended target |
| A wider reference changes the verdict on identical NPU output | The new oracle is not accurate for the sensitive family | Restore analytic/high-precision/interval routing and negative controls |
| A final status is clean despite NaNs | Earlier child failure or undefined workspace propagated | Record the first producing node and physical buffer lifetime |
| GE fails before a native kernel that works | Registration or inference metadata has a separate contract | Fix that caller layer and keep runtime shape validation strict |
| A later healthy process is used to erase a timeout | Different runs establish different facts | Preserve the original failure and validate any candidate repair separately |
| A small-matrix sign fix does not help general sizes | Specialized and recursive paths have different conventions | Audit each branch and compare same-T and original-A results separately |
| Ordinary columns match but inherited columns do not | Boundary-vector normalization or source mapping differs | Trace active/deflated classes and recursive phase propagation |
| A more accurate leaf regresses the full result | Intermediate ordering/rounding changes downstream representation | Validate complete eigenpairs and first-divergence stages, not only leaf arithmetic |
| A normal call faults before phase writeback | Eligibility construction may execute an unnecessary failing path | Isolate it, prove an equivalent predicate and rerun the original normal NPU call |
| A direction guide is mistaken for a wider solver | Only narrow ordering metadata was repaired | Keep value/magnitude/unaffected-branch invariants and qualify actual device arithmetic |
| Scaled Rayleigh evaluation changes units across lanes | Common scale was not published before a collective sum | Publish one scale and validate compensated accumulation plus overflow-safe product order |
| A helper named FMA fails a cancellation control | Actual overload separately rounds multiply and add | Probe exact operand bits and inspect the real implementation; do not infer semantics from a name |
| A residual certificate accepts the wrong result | Estimator bias, rounding or output-slot association was omitted | Bound the computed quantity and reject wrong-root/slot controls |
| A large-value argmin returns its initial index | A finite magic sentinel is smaller than every candidate | Initialize from a validated datum and test index as well as value |
| Ordinary residual K damages full orthogonality | K is not pairwise skew after finite rounding | Derive paired K, preserve its rounding order and validate full Gram/reconstruction |
| Refinement leaves the target unchanged at subnormal Q | Blanket domain rejection skipped the update | Preserve Qorig, test a justified Qwork domain and observe actual apply/skip |
| Only some columns survive a rejected refinement | The candidate publishes before its collective decision | Reduce reason flags and restore the entire original matrix on a numerical skip |
| Exterior guards pass but an internal region is corrupted | Live scratch intervals overlap within the allocation | Prove all live byte ranges and publication; test finite and NaN poison |
| A strict rescore fails only at large scales | Validator products/norms overflowed before promotion | Promote stored operands before arithmetic and keep display floors out of predicates |
| No representable W meets a tiny-scale criterion | Storage spacing dominates the requested error budget | Construct a format-bound example and separate contract feasibility from ordinary algorithm failures |

The detailed [correctness](eigh-correctness.md), [numerics/memory](eigh-numerics-and-memory.md) and [refinement](eigh-residual-refinement.md) guides explain the reasoning and complete-validation boundaries.

For a complete accepted baseline, use the [accepted optimization patterns](eigh-accepted-optimizations.md) to choose between projection-based direction calibration, exact arithmetic, small-matrix specialization and parallel deflation preparation. Match the current live bottleneck; successive guide acceleration and guide removal are alternative stages, not additive speedups.

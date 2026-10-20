# Five-round casebook: tested observations and open questions

All device observations below belong to the910B2/CANN9.0.0 development case unless another version is identified. R5's TileLang observations concern its historical0.1.1.10 wheel. Counts, sizes, addresses, tiling constants and profiler IDs are illustrative evidence, not defaults for a new operator. Cases are condensed here; detailed mechanisms are in the topic references.

## R1–R2: contract, identity and complete physical state

| Case | Trigger and observation | Action or remaining boundary |
| --- | --- | --- |
| C01 stale packaging | Incremental build had new fresh kernel resources and old embedded registry payload | Fresh independent builds; enumerate/check every expected route, including missing ones |
| C02 metadata mismatch | FP16 coordinates did not identify actual threshold/output dtype | Separate documented FLOAT contract from additional HALF compatibility; inspect real allocation/metadata |
| C03 exit0 diagnostics | B4095 each dtype had306 memcheck entries and an initcheck entry despite exit0 | Read raw logs and each tool completion; precision/exit status cannot clear memory failures |
| C04 misleading measurement path | Initial performance used a standard FLOAT-output path, while another compatibility path existed | Measure the actual claimed entry/output metadata |
| C05 wrapper-only change | FP32 mask-source simplification produced three byte-identical device objects | Do not assign about1% timing variation to unchanged device instructions |
| C06 count still Counter | Replacing source syntax with ordinary count API did not remove diagnostic behavior | Read installed overload; explicit Normal repeat/tail isolated this version's behavior |
| C07 incomplete predicate state | Defining valid logical bits did not define the entire Select-readable mask storage | Initialize the physical read range and check mixed0/1/tails |
| C08 efficient test runner | One process reused the independent cases through actual ACLNN calls | Calibrate on known baseline and inject wrong-output negative controls; report initialization separately |
| C09 final combination not automatically fastest | Late safety/layout fixes were combined with only one final independent timing | Reserve confirmation for final source; record local best and selected source separately |

## R3–R4: narrowing hypotheses and measuring the right mechanism

| Case | Trigger and observation | Action or remaining boundary |
| --- | --- | --- |
| C10 tiling macro bypass | Direct dynamic8B tiling reads reduced text and two paired runs improved | Applies to that dynamic template only; static tiling semantics not proved equivalent |
| C11 aligned zero-skip | First tiny local improvement disappeared in confirmation | Do not promote an inconclusive change; CPU valid-lane model cannot clear padded initcheck needs |
| C12 HALF dummy broadcast | Changed scalar/vector counters but total gain did not persist | Counters overlap; lower Scalar is not automatically lower Duration |
| C13 true HALF runner | Syntax-only succeeded but linking required SDK libnnopbase | Check final link;2B H2D+ACL_FLOAT16+quantized oracle establishes the actual path |
| C14 hidden UB gap | New region crossed an old reserved-output gap not in the host guard | Compute highest live byte end including gaps/scratch, not sum of logical sizes |
| C15 HALF scalar Select | Count and Normal forms both reported initcheck size2 at SDK scratch UB0x2e000 | Unresolved; location is not proof of SDK bug/false positive; no eligible speed claim |
| C16 packed Compare tiny length | B1 zero-reference smoke passed; B31/32/33/63 incorrectly became0 | Inspected count implementation yielded zero full repeats below64FP32; add tiny1/mixed cases |
| C17 mask high half | SPR/small path precision passed but memcheck found inconsistent high mask state | New source restored state and needed fresh validation; cannot inherit parent safety |
| C18 “full valid mask” | Skipping complete64B initialization still produced size56 initcheck | Valid predicate bits and physical Select-readable bytes are separate |
| C19 Half strided expansion |32B Half row became64B Float row; copied stride/capacity was wrong | Derive address formulas and units anew after Cast |
| C20 redundant wait | Strided Half B33 reported redundant wait flags | Rework initialization to remove overlap first; remove only graph-proven unnecessary waits |
| C21 aggregate GM copy | Device compiler rejected copying a GM struct to local aggregate | Host C++ validity does not establish device address-space support |
| C22 fixture overwrite | Same case name/different threshold collided in serialized keys | Use unique keys and round-trip bytes/metadata checks |
| C23 timing protocol drift | Same G changed about+45.84% with process boundaries; PMU also affected it | Same-code controls before changing runner/profiler; no universal noise constant |
| C24 compression overlap | Could not establish isolation from archive compression | Invalidate affected gain claims; one exclusion through the capture job and its capture-specific child lifetimes |
| C25 misleading code/counters | Smaller text or lower Scalar did not establish total speed/causality | Keep machine-code evidence, counters and measured duration as distinct facts |

## R5: TileLang frontend, compiler, cache and AOT

| Case | Trigger and observation | Action or remaining boundary |
| --- | --- | --- |
| T01 installed module/CLI mismatch | Cython import succeeded but launcher missing from task PATH | Inspect real package/launcher; avoid reinstalling without diagnosed absence |
| T02 string annotations | Old parser rejected postponed tensor annotations | Version-specific syntactic repair, then actual compilation; not universal Python advice |
| T03 tail overlap | Backward full-width tail windows gave multiple writers | Unique tile bases and legal tail transfer lengths; CPU coverage plus device diagnostics |
| T04 2D singleton output | Helper read every eighth Float beyond intended buffer; B33 had29 mismatches | Inspect generated copy/helper units; use verified continuous representation |
| T05 copy extent syntax | Conditional extent emitted a declaration inside C++ arguments | Explicit full/tail branches; compile multi-tile boundary shapes |
| T06 ratio literal loss |0x3f7fffff→decimal literal→0x3f7ffffe;44/65 errors | Verify scalar bits through ABI/literal; true runtime FP32 fixed that path |
| T07 cache reload | First JIT/same-process reuse worked; new-process symbolic-shape reload failed | Private fresh cache isolated the fault, did not repair reload |
| T08 alloc_var parser | Buffer name was already a BufferLoad; indexing assignment failed | Inspect parser/IR; internal Var escape not a portable API recommendation |
| T09 AIC/AIV ownership | GM threshold read on AIC, AIV consumed its own initialized0;44/65 errors | Explicit expert vector scope/route, then revalidate; waits do not share scalar registers |
| T10 worker cache singleton | Per-job env changes did not change imported module/singleton cache | Fix cache before first worker import, read back actual state, bind manifests by key |
| T11 AOT key/ABI | Sorted records could pair wrong dtype/presence export; absent pointer differs | Explicit full combination keys and exact function ABI |
| T12 helper extraction | Source order, overloads, licenses and inline/device attributes mattered | Minimal transitive closure preserving declarations; corrected inline produced identical device sections |
| T13 static UB rewrite | Narrow known patterns could be transformed, arbitrary code could not | Reject dynamic/unknown/overlap cases; CPU pass is not SDK lifetime/device safety proof |
| T14 missing host tiling | Actual workspace query failed with missing tiling function | Stage and hash host library as well as kernel resources |
| T15 adapter host errors | Imported module lacked globals initialized under main;130 host errors before launch | Correct adapter layer; validate baseline and real device entry with no fallback |
| T16 precision flag coverage | Smoke CLI accepted compatibility flag but did not execute HALF cases | Inspect actual case list/counts; a flag is not coverage |
| T17 code-size optimism | AOT text shrank greatly and precision passed without a final baseline speed win | Inspect fixed path/geometry; DSL and code size do not establish saturation |

## R5: raw primitives and structural optimization

| Case | Trigger and observation | Action or remaining boundary |
| --- | --- | --- |
| L01 full950 header probe | First compiler error was unknown float4_e2m1x2_t on910B/CANN9 | Full wrapper incompatible as-is; does not prove ordinary MAD unsupported |
| L02 minimal MAD probe | BF16 asc_mmad compile/link/payload passed, operands uninitialized, never launched | Compile compatibility only; no numeric or timing claim |
| L03 raw C math entrance RAW |92/130 precision;38 failures allFP16 | Add caller Cast/Gather→rawV dependency, then130/130 and freshness passed |
| L04 raw C local gain | Large pilot about−2.15%, full workload about−0.38% with regressions | Preserve scoped signal; test a regime-specific combination instead of denying it |
| L05 scalar GM store |34/130 failures persisted after extra completion barrier | Root cause open; do not label cache/hardware cause or benchmark as eligible |
| L06 scalar UB staging | Correct scalar experiment needed complete32B UB even with4logical floats | Separate logical grain and physical defined/read width; Half fallback separate |
| L07 nonmonotonic core grain | Vector4 small cases about−38% to−42%; Vector8 about+20% to+52% | Sweep actual geometry empirically; no linear interpolation |
| L08 medium grain portability | Two local full runs improved about6.75%/6.13%, target-environment gain did not transfer | Preserve both observations, leave unknown cause open |
| L09 I/O specialization | FP32 gains with Half regressions made combined aggregate about+0.50% | Specialize the understood dtype path, restore unaffected behavior and retest combination |
| L10 final combination | Local all 12 about−7.69%; two smallFP32 about−40.47%/−42.53% | Other cases/order effects remained; do not claim all-case stable improvement |
| L11 inactive sanitizer | Exit0/correct output despite No active sanitizer tool or ignored flag | Count as not checked; rebuild via actual supported instrumentation route |
| L12 lower-level flag linkage | Instrumentation calls existed but sanitizer runtime unresolved | Use build system's full diagnostic pipeline, inspect commands/artifacts/tool start+finish |
| L13 directory permission advisory | Final requested tools ran, only0755 result-directory advisory | Preserve/classify advisory; not “no warnings” and not illegal-access proof |
| L14 offline export speed | Six isolated CPU processes sped export after NPU capture | Tool throughput only; avoid thread-shared auditor globals |

## Eigensolver case: valid mathematics and reference phase are separate

The [eigh correctness case](eigh-correctness.md) adds a separate, mechanism-based study: a 150-record mathematical/direct-comparison discrepancy; an n2-only sign rule; leaf, deflation and root-pole differences; a device-stage success followed by a complete-call runtime failure; a cancellation-damaged host oracle; and a narrowly tested NPU phase guide. At the 2026-10-20 snapshot, 136 complete candidate NPU calls / 984 matrix records passed, with two independent builds and a third carried runtime. External acceptance, a locally untested target chip and full sanitizer clearance remained open. These observations do not establish the external reference's identity or a universal sign convention.

### Later Round12 observations: preserve the layer of evidence

| Observation | Reusable decision |
| --- | --- |
| A legal n512/U example passed mathematical checks but had a sign-aligned component error about 1.514e-4; actual H×Z already contained it, while the final Cube product added only about 2.992e-7 | Localize the concrete difference before changing layout; a later normal-NPU residual correction fixed this local example, not a confirmed external input/checker |
| A normal template's host tiling was an OBJECT linked into its API, with no separate host `.so` | Derive package completeness from actual targets/linkage; do not copy another template's library requirement |
| The 910B3 all-distinct batch5 deadline probe returned 507046 after execute; separately authorized fresh health later passed | Preserve both results. This did not establish the 910B4 official failure cause or cancel the deadline failure |
| Default collection had checked application calls plus internal replay; complete `0`…`4` CSV exports were audited separately | Count real application receipts and collected tasks separately; missing reports do not identify a numerical or timeout cause |
| Retiring historical hardlinks changed retained aliases' ctime; frozen-content rehashing resolved the guard, and old sample sets were intentionally removed | Keep the repair process and retention ledger, but stop claiming old runners can replay absent data |

The later local candidate completed full (420 calls), all-size (1024 calls), targeted (34 cases), native (8 calls) and Default (15 application calls) suites across 910B2/910B3. These overlapping suites are not a unique-matrix count. At the last saved 2026-10-20 15:00 UTC official observation, the new submission was still Running; local qualification was not external PASS, and NumPy/backend identity remained unconfirmed.

## Open questions deliberately not converted to rules

- Exact root cause of the old scalar GM corruption.
- Whether the historical HALF scalar Select scratch diagnostic is a kernel/SDK/tool-model defect.
- A general repair for the old symbolic-shape disk-cache reload.
- Why some diagnostic device bytes changed with build directories.
- Why measured local improvements did not all transfer to a different target environment.
- Runtime numerical/performance behavior of the unexecuted MAD probe.
- Full safety of arbitrary generated-code/TPipe transformations.
- Performance impact of the early bank-group/field-stride hypothesis and intermediate capacity stairs on a new target.

Revisit an old route only when a new implementation, version, hypothesis or coverage difference gives a concrete reason. A new author or experiment name does not make an old failure disappear.

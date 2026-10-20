# Eigh: numerical, workspace and framework failure mechanisms

Use this companion to the [eigh correctness case](eigh-correctness.md) for small-eigenvalue failures at large scales, secular-root failures, workspace corruption, generated-code surprises or GE-only failures. These are historical observations on the studied CANN9/910B implementations, not universal SDK defects or a replacement eigensolver. The [provenance record](eigh-provenance.json) distinguishes checked archive members from current files. No historical script is an instruction to rerun or deploy it.

## Classify the failing layer before choosing a repair

Separate: fixture/oracle failure; host registration or shape inference; workspace/initialization; solver convergence/bracketing; eigenvalue accuracy; global Q orthogonality/reconstruction; reference representation; and external acceptance. A NaN is a symptom until its first producing stage is known. A real local fix can leave the external result unchanged; preserve both conclusions.

Follow the actual entry and invoked methods, not a design note, helper name or unused constant. One audit found an unused `kMaxIters=11`, a parent refinement method absent from the large path, and comments inconsistent with the effective deflation formula. Check actual arithmetic options before blaming HF32 or a primitive that the current path never calls. A fast matrix-multiply component or a correct tridiagonal solve does not establish a correct or faster complete original-A eigensolver.

## 1. Large scales, near-zero roots and arithmetic primitives

**Reconstruction can hide a bad small eigenvalue.** In an exact-zero-root family, a complete device candidate returned small roots around 0.1859, 194949 and 1.2776e10 at input scales 2^80, 2^100 and 2^116. Orthogonality and relative reconstruction passed; three of 17 cases failed W alone. Scale-relative matrix residuals do not replace the absolute part of the eigenvalue tolerance.

**Do not repair that by clipping small roots to zero.** Other admissible high-scale families had genuine nonzero roots near ±0.03217 or ±0.000122517. A norm-relative “near zero” rule could erase them and fail the absolute W check. The recorded nonzero construction/proof was CPU evidence, not a completed NPU regression for every such input. Keep exact-zero and small-nonzero negative controls separate.

**Every lane needs the same numerical state before a collective reduction.** A tree-preparation path changed scale only on lane0. A later distributed Rayleigh sum could therefore combine different scales. The repaired path restored common input scale, used compensated Rayleigh evaluation, and multiplied normalized factors before rescaling to avoid an overflowing `qn*scale` intermediate. One n128/U error decreased from about 16.48 times tolerance to 0.003576 times tolerance, with saved Q bit-identical. The complete local regression passed; external feedback still did not improve. This was a scoped eigenvalue repair, not evidence against all remaining causes.

**Measure primitive semantics; names are not contracts.** A helper called `FmaScalar` actually matched separately rounded multiply-plus-add. In two real-device 512-row probes, 313 rows differed from intended single-rounding IEEE fma. The exact control `(1+2^-23)*(1-2^-23)-1` should produce -2^-46 under the investigated fused contract; the old helper returned zero. Sqrt and vector Div probes also had separate one-ULP discrepancies. Bind operand bits, reference rounding and the actual primitive/overload. Fixing the FMA helper passed complete local regression but did not establish the external WA cause. Do not generalize a software-wrapper defect into a claim that every native FMA or compiler transformation is wrong.

**A certificate must cover the computed quantity and its output slot.** Exact-rational analysis of 96 saved roots showed that dropping Rayleigh-estimate bias eta could falsely accept a negative control. Including eta made the investigated CPU certificate useful, but device rounding bounds, root-index association and full-output coverage were still unproved. A certificate for a nearby unique root does not identify which sorted W slot should receive it. Report CPU feasibility separately from a device runtime certificate.

**Avoid finite magic sentinels.** Initializing `minAbs=1e30` can leave index0 selected when every legal absolute eigenvalue exceeds 1e30. Initialize from a validated datum or another contractually justified identity, and verify the selected index. The historic report proved a static/CPU indexing counterexample, not that its newly constructed matrix had already failed on an NPU.

## 2. Secular brackets and failure propagation

A legal batch of 65 n512/U matrices failed in one position. Extracting that matrix and invoking it alone reproduced the failure, so batch geometry was not the sufficient cause. The first recorded failure was an internal node of size128, not necessarily the final root node.

The solver chose its origin from an absolute FP32 midpoint but checked its bracket with left-pole plus a half-gap shift. Those algebraically equivalent expressions rounded to approximately 7.0477943420 and 7.0477941036. Their function evaluations had opposite signs, about +9.696 and -3.481. Origin selection and endpoint verification were evaluating different representable points. More iterations cannot repair that inconsistent bracket. Freeze the coordinate representation and endpoint bits across origin choice, sign checks, shifts and iteration updates; use one-step neighbors and boundary controls to test the repair.

Track the first failing node/status and the data it produced. In that case, a zero child column propagated through parent nodes, and final normalization used `1/sqrt(0)`, creating NaNs. All-NaN W was also an explicit failure marker. A clean root-node status array did not negate an earlier child failure. Distinguish directly captured state from reconstructed transient ABI state when explaining causality.

## 3. Workspace ownership, physical tails and address units

| Failure mechanism | Required reasoning and bounded observation |
| --- | --- |
| Mailbox capacity smaller than physical writers | At p64, Meta held 64 floats but 16 lanes wrote 8 each, requiring 128. Later mailboxes overwrote Partial. A fix changed real Meta capacity to `max(p,128)` and updated host total size, kernel stride, declarations and base steps together. Enlarging a descriptor alone does not allocate bytes. Enumerate supported n and groups against one layout formula. |
| Pipeline wait mistaken for a collective barrier | Per-core `PIPE_ALL` did not establish that other cores had finished reading shared metadata. Derive producers, consumers, scope and lifetime for each shared interval; local completion is not inter-core publication. |
| Logical masking after a physical full-width load | A runtime-n solver's downstream stage read 512 columns before masking. Inactive workers had not initialized their owned tail columns. The corrected version explicitly defined those physical tail regions before synchronization; mathematical agreement alone had not exposed the defect. |
| Byte address confused with element index | In the studied raw LocalTensor binding helper, float offsets were supplied to a byte-address field, overlapping two rows. Correct that binding with `offset*sizeof(float)`, while keeping logical count in elements. Inspect the exact constructor/offset API; do not multiply ordinary element indexing indiscriminately. |
| UB alignment confused with GM permission | A 32-byte-aligned UB allocation does not authorize rounded-up GM reads or writes. Use the actual valid GM length, supported padded-copy semantics and a separately sufficient UB capacity for tails. |
| SDK/system workspace mistaken for application arena | A sampled allocation had a 16MiB system prefix. Dumping its first 7.4MiB yielded irrelevant zeros; the application arena began later. Establish query bytes, host user capacity, kernel entry pointer and content correlations. Never copy that prefix size into other SDKs or clear unknown system-owned storage. |

Canaries catch only the regions they guard. An overlapping live workspace buffer can corrupt another legal allocation without touching an exterior canary. Prove the highest read/written byte and overlapping lifetimes, not just sums of tensor sizes or “inside allocated memory.”

A poison study found four tile-end words retaining finite poison after inverse transform. Masking made one finite-poison mathematical test pass while internal storage was still contaminated; NaN poison propagated further because zero times NaN is NaN. Masks do not initialize unread bytes. The report proposed event-order controls but did not directly capture the initialization endpoint or establish a compiler-internal missing synchronization instruction. Preserve that uncertainty. A successful instrumented build does not erase a normal-build reproduction, and vice versa.

## 4. Generated code and mathematical checks

An old TileLang source branch `if tau < 0: tangent = -tangent` disappeared from generated C++. The 2×2 input `[[3,1],[1,1]]` retained an orthogonal G yet had reconstruction error about 0.6249. Storing the signed coefficient in a UB slot made the expected branch appear in generated code. Another independent bug used Q block stride `B*16` instead of `B*n`, causing overlap and unwritten elements even at n64. Inspect each generated indexing/sign mechanism, not just source syntax or successful compilation.

Column normalization is not global Q orthogonality. A legal n512/U input with gap around 1.20 times the required minimum passed W and reconstruction but had absolute Frobenius orthogonality about 1.06316e-4, exceeding 1e-4. Wider-gap passing cases did not close that failure. If a polar/orthogonalization stage is proposed, recheck reconstruction and W/Q pairing on the real device; CPU postprocessing is only diagnostic evidence.

For a later component-error repair, [residual refinement](eigh-residual-refinement.md) records why ordinary FP32 K also failed global orthogonality, how pair-skew rounding and separate Qwork/Qorig were qualified, and when exact common scaling requires whole-Q fallback. That complete-device evidence does not transfer to an arbitrary refinement or relax the checks above.

Test the original-A complete entry after backtransform and refinement. The historical root-only, tridiagonal-vector and translated full-solver prototypes were different artifacts with different scopes. Their source, compiler route, actual API and complete-call output needed fresh binding; a stage pass did not transfer automatically.

## 5. Validation arithmetic and representability

Promote stored arrays to the oracle's compute dtype **before** products, matrix multiplication and norms. A 36-case high-scale runner performed `q*w`, matmul and norms in FP32: some ratios became `inf/inf -> NaN`, while a finite numerator divided by an overflowing denominator misleadingly became zero. Strict recomputation of the actual saved arrays in FP64 passed those 36 cases. Casting a final scalar or an already overflowed intermediate cannot recover the calculation.

Keep display conventions out of acceptance predicates. `residual/max(norm,1e-30)` can display a convenient ratio, but using that denominator floor to decide acceptance can falsely pass a zero input with nonzero reconstruction. Evaluate the contract's original inequality, including zero-norm behavior; keep reporting-only ratios separately labeled.

Check the feasibility of requested output storage independently of algorithm quality. A CPU proof for `epsilon*[[0,1],[1,2]]`, epsilon=2^-149, found that FP32 W could not meet the requested 1e-4 relative reconstruction even with nearly orthogonal Q. This bounds that specific format/contract case; it neither excuses ordinary-scale failures nor permits skipping other solvable subnormal inputs or changing tolerances. Combine such proofs with the [frozen-oracle controls](eigh-correctness.md#6-freeze-and-test-the-oracle-as-carefully-as-the-kernel), not silent fixture removal.

## 6. GE shape inference is a distinct caller contract

First establish a complete framework test entry: required input mappings, operator prototype/graph registration, attributes and matching host libraries. An initial GE adapter lacked registration. Switching to positional getters then exposed an empty attribute table; changing the numerical kernel would not have fixed it.

After registration, a valid `[2,3,3]` invocation exercised concrete shape inference, unknown dimensions `[-1,-1,-1]`, and range lower bounds `[0,0,0]`. Reusing runtime “all dimensions >=1” validation rejected that shape-range lower bound before execution. The minimal correction handled inference metadata under its own framework convention, while actual runtime inputs still required legal positive dimensions. Do not globally allow zero-sized runtime inputs or weaken launch checks to accommodate inference metadata.

The corrected GE result matched the original ACLNN W/Q bits on the tested call, and same-process revisits were separately tested. External feedback did not improve. Distinguish framework reachability, numerical validity and external acceptance. Likewise, descriptor capacity such as 96 bytes and a serialized tiling structure's `sizeof` such as 88 bytes are different quantities; verify actual serialized layout and consumption before calling the difference an overrun.

## Selected historical evidence

The following members are relative to the old case's round11 archive. Read only needed text members after verifying them; do not extract or execute the whole old round. Exact sizes/digests and verification scope are recorded in [eigh-provenance.json](eigh-provenance.json).

| Topic | Archive member |
| --- | --- |
| First internal secular bracket failure and NaN propagation | `codex-tests/contract-multibatch-failure-002/node3-root-cause-001.md` |
| Exact-zero and nonzero small-root controls | `codex-tests/highscale-actual009-independent-review-001/README.md`; `codex-tests/pro012-nonzero-negative-controls-001/README.md` |
| Rayleigh scaling, arithmetic order and certificate limits | `codex-tests/rayleigh-rebuild030-001/README.md`; `codex-tests/rayleigh-certificate032-001/README.md` |
| Actual primitive/FMA behavior | `codex-tests/leaf-primitives056-001/README.md`; `codex-tests/ieee-leaf-fma057-001/README.md` |
| Shared metadata capacity | `codex-tests/leaf015-n3-meta128-001/README.md` |
| LocalTensor byte binding | `codex-tests/raw037-native-polar-001/attempt002/layout-independent-review-002.md` |
| Application arena and poison limits | `codex-tests/native-jacobi-tail-review-001/failure-n33-LU-001/poison-four-word-finding-001.md` |
| Lost branch, block stride and validator floor | `codex-tests/block-jacobi-code-review-001/review.md` |
| Overflowing host validator and strict rescore | `codex-tests/interior-k-highscale-36-device-001/ERRATUM-F64-RESCORE-001.md` |
| Near-gap orthogonality failure | `codex-tests/raw037-neargap-orth-failure-001/README-001.md` |
| Effective precision policy and finite sentinel | `codex-tests/precision-policy-audit-001/report-001.md`; `codex-tests/nearzero-minabs040-001/README.md` |
| Minimum-subnormal format boundary | `codex-tests/structured-direct-sum-001/minsubnormal-output-format-boundary-001.md` |
| GE registration and inference ranges | `codex-tests/host-tiling037-001/README.md`; `codex-tests/infer-range038-001/README.md` |
| Physical tail initialization | Preserved note `results/round12/handoff-evidence/reference-notes/codex-tests/sturm-twisted-runtime068-001/README.md` relative to the case project |

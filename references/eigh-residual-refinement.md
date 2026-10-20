# Eigh: residual refinement without losing the validated solution

Read this when complete NPU eigenpairs satisfy the mathematical contract but a reproducible **component error remains after whole-column sign alignment**. Use [eigh correctness](eigh-correctness.md) for caller, phase and oracle checks, and [numerics and memory](eigh-numerics-and-memory.md) for cancellation, arithmetic and workspace failures. This is a scoped repair mechanism, not a replacement eigensolver or a guarantee of agreement with an unavailable checker.

The inspected normal candidate kept the existing decomposition, phase rules, W and small-n path, then corrected the complete post-polar Q on the NPU. Its local complete-call and protocol checks passed. External evaluation was still pending at the inspected snapshot; the external reference implementation was unknown. A NumPy comparison was an independently pinned diagnostic, not a confirmed description of that reference.

## Separate a component error from a phase error

Keep the actual stored FP32 input, UPLO, W and signed Q unchanged while comparing:

- Original mathematical checks: W accuracy, complete absolute Frobenius orthogonality and original-A reconstruction, separately for every batch matrix.
- Direct signed Q, absolute Q and whole-column-sign-aligned Q differences against a specified reference. Record the reference backend, library hash, input conversion and compute/storage dtypes.
- Parent-to-candidate column dots. A component correction may change Q bits; positive dots check the intended direction preservation without pretending the parent FP32 result is an independent high-precision oracle.

In one saved n512/U blocked, permuted, high-scale case, sign alignment still left a maximum component error of about `1.51423e-4`. The two investigated CPU backends agreed after alignment to about `2.6e-13`. All problematic components were inside their correct input graph components, so zeroing entries outside components and renormalizing was an ineffective repair. Mathematical decomposition validity and this reference component comparison were different conclusions.

Capture normal-path H, the actual reduced T, Z and the final matrix product before assigning blame. For that case, FP64 multiplication of the **captured** H and Z already reproduced the component error. The final device matrix multiply differed from this product by only about `3e-7`; the existing polar stage changed it only slightly. Replacing Z with a CPU solution of the **same captured T**, while holding H fixed, reduced the aligned error. This isolated a useful refinement direction; it did not prove one hidden test's cause or that Householder rounding was irrelevant.

Do not merge this finding with a surviving phase counterexample. A separate column lay very close to a deflation threshold; accurate-root substitutions did not change the actual branch flags. Changing the threshold or hard-flipping a particular size/column would not follow from the component-error evidence. Residual refinement preserves the chosen phase rather than repairing such a mismatch.

## Derive the correction and test the unsymmetrized failure

Let `D = diag(W)` and let `A` mean the symmetric completion of the selected triangle of the stored input. With an approximately orthonormal Q, form

```text
R = A Q - Q D
C = Qᵀ R
Kij = Cij / (Wj - Wi), i != j; Kii = 0
Qtrial = Q + Q K
```

The sign follows from cancelling the first-order off-diagonal residual in the spectral basis: `Cij + (Wi - Wj) Kij = 0`. An opposite-sign negative control made the saved error worse. This derivation is an approximation when Q is not exactly orthonormal; finite arithmetic and small gaps still require validation. W is deliberately unchanged, so this is not an eigenvalue-accuracy repair.

An ordinary FP32 K looked satisfactory on the first structured cases but failed complete orthogonality on additional dense data: one n512 case reached about `1.43e-4` against the unchanged `1e-4` absolute bound. Column normalization and common scaling did not fix it. Expand the corpus before turning a CPU counterfactual into device code.

The selected repair explicitly made K skew-symmetric. In exact arithmetic, the first-order Gram perturbation is `K + Kᵀ`, which cancels for skew K when the starting Q is orthonormal. This is a reason to test the construction, not a proof that the finite result meets the contract.

For each `i < j`, freeze the actual rounding sequence:

```text
a = fp32(Cij / fp32(Wj - Wi))
b = fp32(Cji / fp32(Wi - Wj))
s = fp32(fp32(a - b) * fp32(0.5))
Kij = s; Kji = sign-bit-XOR(s); Kii = positive zero
```

One owner computes each pair. Copy the lower value by sign-bit XOR, including signed zero. Do not silently replace the two divisions with `(Cij + Cji) / (2*(Wj-Wi))`: algebraic equality does not preserve this FP32 rounding sequence. The studied CPU controls included a rewrite negative control. Keep global orthogonality and reconstruction checks after the update; no extra polar stage was added to make this selected variant pass.

## Compute a less cancellation-prone residual

Use the same exact power-of-two scale for selected input entries and W. With `As = A*2^-E` and `Ws = W*2^-E`, compute the equivalent residual as

```text
Rij = ((As - diag(As)) Qwork)ij + (Asii - Wsj) Qworkij
C = Qworkᵀ R
delta = Qwork K
Qtrial = Qorig + delta
```

This avoids subtracting two large diagonal-dominated matrix products. It was more stable on the saved FP32 corpus than ordinary `As*Q - Q*Ws`. Keep the order of the diagonal difference, product and residual addition explicit when that order is part of the evaluated variant.

Choose one E from the maximum absolute selected-input/W value, publish it to all participants, and recompute it for every active batch wave. The studied revision used the bit-derived `frexp` exponent clamped to `[-126,126]`; this range is an implementation choice, not a universal scaling rule. A common exact scale cancels between C and the eigenvalue gap in K. Scaling A and W differently, or mixing scaled and unscaled residual terms, changes the correction.

Its integer scaling helper preserved signed zero, normalized a subnormal source mantissa when needed, and supported a nonzero result only when that scaled result was normal and finite. A nonzero subnormal or overflow result was explicitly ineligible; it was not rounded to zero and called exact. A broad exponent range can therefore make an otherwise legal matrix skip refinement. Check the selected triangle only: ignored-triangle NaNs must not affect the scale, finite tests or arithmetic.

## Keep Qwork separate from immutable Qorig

The original post-polar Q must survive until the entire correction is accepted. Use a separate Qwork for arithmetic operands. On the studied path, nonzero subnormal Qwork entries were explicitly replaced by **the same signed zero**, while Qorig retained every original bit. The final update was `Qorig + Qwork*K`, followed by positive column normalization; it was not `Qwork + Qwork*K`.

The first source revision rejected a whole matrix whenever Q contained a subnormal. That made the target input skip the intended repair: its actual Q had 14 such entries. Working-Q FTZ was therefore tested as a single-variable CPU change before the rejection was removed. Across 28 saved matrices, unchanged mathematical, Decimal, W-bit and parent-direction gates still passed. The discarded working values had tiny total norm in that corpus; this does not justify globally ignoring subnormals or flushing A/W indiscriminately.

CPU increasing-k multiply/add loops did not establish the exact accumulation behavior of the device MMAD. The normal implementation reused its existing full-precision FP32 Cube path with HF32 disabled, then qualified actual complete outputs. Do not label a CPU arithmetic model as NPU execution or implement a CPU solver fallback.

## Accept or restore the whole matrix

The inspected implementation required finite selected A/W/Q, supported exact A/W scaling, finite nonzero off-diagonal denominators, finite paired K and trial values, and finite positive column norms. It did not add an arbitrary gap-size or K-size cutoff. These eligibility checks do not establish convergence for every nonzero gap; the complete mathematical checks remain mandatory.

Reduce numerical reason flags across all owners before publishing any final Q. Any ineligible numerical condition restores **the entire saved Qorig**, not a mixture of corrected and original columns. Preserve W bits and the established small-n path. Restoring a nonfinite Qorig must still fail the ordinary checker; fallback is not a way to turn an invalid parent into a pass. Memory, synchronization, API identity and deployment errors are failures, not numerical skip reasons.

Expose a bounded apply/skip receipt tied to the current matrix index, shape, exponent, reason and actual loaded artifact. The target counterexample must report **applied** and improve against the frozen reference; an unchanged skipped Q is not a successful repair. Extreme-range controls must prove whole-Q bit preservation when ineligible. In a multi-wave group, a single reused receipt may describe only the last active wave; do not generalize it to earlier matrices.

## Preserve publication and ownership while reusing scratch

Place the update after the existing post-polar result is complete and before final output publication. Prove the old decomposition scratch slots are dead before reusing them. In the investigated design, three existing operand/result matrices carried the three products; a distinct slot held immutable Qorig. Metadata and reason lines had separate owners. These are lifetime roles, not portable offsets to copy into another operator.

Each stage needs a producer/consumer and physical-write proof:

1. Publish the common scale and defined A/W tails before any Cube read.
2. Keep the completed C immutable while pair owners construct the upper K; synchronize before lower owners read those values.
3. Form the full skew matrix and publish Qwork before computing delta.
4. Gather original and delta columns without overwriting live UB values. Column owners write complete aligned rows of a transpose; row owners publish final rows only after normalization and the reduced apply/skip decision.

Whole aligned rows avoided scattered cross-core partial-line writes. Bound both GM tails and UB gather/row lifetimes; UB alignment alone does not permit rounded-up GM access. Initialize physically read padded rows and columns. All mixed collective barriers remain unconditional, including inactive groups; guard only the work they surround. The inspected implementation had 19 barriers in its wave, but another implementation must derive its own synchronization rather than copy that count.

## Qualify the new behavior without weakening the old checks

Preserve original oracle routing. A general FP64 eigensolver can be inaccurate for a very small root of a huge matrix; the saved outward-Decimal interval cases continued to use their frozen scorer. Promote stored arrays before validation arithmetic, retain warnings and investigate nonfinite intermediates. Signed/absolute/aligned reference comparisons are diagnostics unless the actual acceptance contract says otherwise.

The local evidence progressed from CPU counterfactuals to normal, identity-bound NPU calls:

| Evidence | Inspected scope and limit |
| --- | --- |
| CPU arithmetic controls | 28 unique saved matrices; 112 skew variants, then a working-Q FTZ-only check. No new NPU call or CPU operator fallback. |
| Frozen NPU repair corpus | 34 unique cases, including the new component-error case, old precision/sign examples and extreme-range skips. Original independent assessment, W bits, parent direction, physical guards and apply/skip receipts passed. |
| Complete saved-corpus regression | 420 calls / 3283 matrix records; original mathematical and state checks passed with default synchronization. |
| Size/UPLO corpus | 1024 calls / 1024 matrices, one L/U sample at every n=1…512. This is not exhaustive spectral or batch coverage. |
| Native entry and Default protocol | Native 8 calls / 24 matrices and Default 15 application calls / 45 matrices passed their recorded checks. These are protocol/correctness evidence, not comparable performance measurements. |

On the actual normal NPU entry, the saved n512/U counterexample was applied and its maximum aligned error decreased from about `1.51423e-4` to `6.68382e-9`; maximum absolute-Q error was about `3.88170e-9`. Original W bits, orthogonality and reconstruction passed. Direct signed NumPy comparison could still differ greatly because parent phases were intentionally retained. This is a repaired local counterexample, not identification of the external failing matrix.

Keep real failures separate. A distinct batch of five different n512 matrices timed out under an explicit 3000ms wait on one investigated 910B3 configuration, even though the original repeated-input batch passed. No failed output was read or relabeled as numerically qualified. This did not establish the cause of an external numerical WA on an untested 910B4. Default-synchronized full regressions likewise do not prove every input meets a three-second deadline.

Changing Q magnitudes intentionally requires a narrowly updated candidate comparator: preserve W bits, small-path signed Q bits, exact known-skip Q bits, input/guards, original mathematical bounds and positive parent column dots. Keep independent component-error targets separate. Same-address restoration compares against that candidate's first **actual** successful output, not a generated expected Q. Never postprocess device outputs in the adapter to manufacture a pass.

Finally bind the normal source, actual compiled device resources, API, generated entry, inputs and complete outputs. A diagnostic journal build or a CPU gate cannot qualify a normal release. External acceptance still requires its own terminal result and accepted-source readback. The inspected snapshot had no official all-pass result and no established performance improvement.

## Selected case provenance

Paths are relative to the original case's round directory; they are optional historical provenance, not dependencies shipped with this skill. The source and scalar controls were inspected, not copied as an implementation. Selected inspected file hashes are in [refinement provenance](eigh-refinement-provenance.json). Current retained outputs are in the round archive or explicitly carried fixtures. Historical arrays explicitly retired before archival cannot be recovered from that archive; do not claim their old runners remain reproducible.

| Topic | Historical material |
| --- | --- |
| Component-error isolation and rejected ordinary K | `phase-progress366-372.md`; `second-owner312-001/spectral-correction372-001/`; `skew-spectral-qualification378-001/` in that owner directory |
| Working-Q FTZ and domain controls | `second-owner312-001/ftz-spectral-qualification379-001/`; `experiments/phase-spectral-offdiag376-001/design376-002.md` |
| Actual normal-path stage and repair assessment | `experiments/phase-float-only305-001/third-owner312-001/normal294-stages374-001/`; `remaining22-capture395-001/root-final-assessment410-001.json` under that owner directory |
| Complete outputs and protocol scope | `phase-progress395.md`, `phase-progress396-403.md`, `phase-progress404-414.md`, `phase-progress415-420.md`, `phase-progress421-424.md` |

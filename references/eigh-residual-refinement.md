# Eigh: residual refinement with preserved directions and explicit fallback

Use this optional method when complete NPU eigenpairs satisfy their mathematical gates but reproducible component errors remain after diagnostic direction alignment. First apply [caller, reference and staged diagnosis](eigh-correctness.md). This is an approximate refinement mechanism to evaluate against your operator's contract, not a replacement eigensolver or a universally convergent correction.

## Establish the error before choosing refinement

Keep stored A, UPLO, W and signed Q fixed. Check original-A reconstruction and full orthogonality, then compare signed, absolute and direction-aligned Q against an independently specified reference. Record reference backend, arithmetic precision and storage conversion. A parent's Q is useful for detecting regressions, but is not an independent accuracy oracle.

Capture actual H, T and Z where the solver uses reduction. If a high-accuracy product of captured H and Z already reproduces the component error, changing only the final matrix multiplication or output layout is not the first supported repair. Replace Z with an independent solution of the **same captured T**, holding H fixed, as a diagnostic counterfactual. It does not qualify a device implementation.

Check proposed sparsity shortcuts against the actual error locations. Zeroing Q outside disconnected input components and renormalizing cannot fix errors already inside the correct components; it can also perturb a valid decomposition. Compare unchanged stored outputs before choosing that repair.

Keep threshold-sensitive phase/deflation discrepancies separate. A component correction that preserves column direction does not repair an independently demonstrated phase mismatch. Do not hard-flip a size/column or alter a deflation threshold from component-error evidence alone.

## Derive the first-order correction

For real symmetric A and approximately orthonormal Q, let `D=diag(W)` and form

```text
R = A Q - Q D
C = Q.T R
Kij = Cij / (Wj - Wi), i != j; Kii = 0
Qtrial = Q + Q K
```

The sign follows from `Cij + (Wi-Wj)*Kij = 0`, cancelling a first-order off-diagonal residual. Test the opposite-sign expression as a negative control. This analysis neglects higher-order terms, assumes a sufficiently accurate starting decomposition, and does not guarantee convergence near small gaps. W remains unchanged, so this is not an eigenvalue-accuracy repair.

Ordinary finite-precision K need not be skew-symmetric. Normalizing each updated column cannot remove all cross-column Gram errors. To cancel the first-order perturbation `K+K.T`, evaluate a paired skew construction and retain the full orthogonality gate.

For each `i<j`, one explicit FP32 evaluation order is:

```text
a = fp32(Cij / fp32(Wj-Wi))
b = fp32(Cji / fp32(Wi-Wj))
s = fp32(fp32(a-b) * fp32(0.5))
Kij = s
Kji = sign_bit_xor(s)
Kii = positive_zero
```

Give each pair one owner. The sign-bit operation makes lower/upper entries exact negatives, including signed zero. Algebraically rewriting the two divisions as one expression can change FP32 rounding; treat that rewrite as another candidate. Skew K removes a first-order term, not second-order error or finite-arithmetic error, so full mathematical validation remains necessary.

## Reduce cancellation with a common scale

Use one exact power-of-two scale for A and W. For `As=A*2^-E`, `Ws=W*2^-E`, evaluate the residual as

```text
Rij = ((As-diag(As))*Qwork)ij + (Asii-Wsj)*Qworkij
C = Qwork.T R
delta = Qwork K
Qtrial = Qorig + delta
```

This separates diagonal cancellation from the matrix product. The common scale cancels between C and the eigenvalue gap in K in exact arithmetic. Scaling A and W differently, mixing units or changing operation order creates a different method.

Derive E from finite selected-triangle A entries and W, then publish it to every participant for each active matrix/wave. Verify that every required scaled value is represented exactly in the actual arithmetic domain. A bit-based scaler can preserve signed zero, normalize a subnormal source mantissa and reject unsupported nonzero subnormal or overflowing results; it must not round a nonzero result to zero and call the scale exact. Test its actual supported range. An exponent clamp alone does not establish exactness, and eligibility may skip an otherwise legal matrix. Ignore an unselected triangle only when the input contract permits that behavior.

## Preserve Qorig and model subnormal behavior

Keep the complete original post-transform Q immutable until the whole update is accepted. Qwork is a separate arithmetic operand, not a substitute for that original result.

If the target arithmetic flushes subnormal operands, reproduce that behavior in the model and check the implications. An explicitly chosen working-copy FTZ variant may replace subnormal Qwork values with the **same signed zero**, while retaining Qorig bits. Its final addition must be `Qorig+delta`, not `Qwork+delta`. Qualify that numerical choice on the allowed input domain; it does not justify flushing A, W or output values indiscriminately.

Rejecting every Q containing a subnormal can make the target counterexample silently skip refinement. Therefore require an apply/skip observation for the intended failing input. Compare ordinary, FTZ-aware and domain-rejection controls before implementing the selected device variant. CPU dot loops do not establish device MMAD accumulation, contraction or HF32 behavior: validate the actual normal NPU path.

## Accept or restore the whole matrix

Define eligibility explicitly: finite required inputs, supported exact scaling, valid off-diagonal denominators, finite paired K and trial values, and finite positive column norms. Near-gap convergence may require additional justified safeguards; a nonzero gap alone is insufficient. Any cutoff must come from the actual numerical contract and evidence, not a copied constant.

Reduce numerical reason flags before publishing the final Q. An ineligible update restores the **entire saved Qorig**, not a mixture of corrected and original columns. A nonfinite original still fails ordinary validation. Memory, API, deployment and synchronization failures must remain failures rather than skip reasons.

Tie bounded apply/skip observations to matrix identity, wave, exponent, reason and artifact. The intended counterexample must report an actual update and improve against its independent target. Ineligible controls must prove complete original-Q bit preservation. A single reused receipt describing the final wave does not prove all earlier waves applied.

## Reuse scratch only after proving lifetimes and publication

Place refinement after the original decomposition/backtransform is complete and before final output publication. Reserve a distinct immutable Qorig region. Reuse old scratch only after its last reader, including asynchronous pipeline readers, has completed.

For each product and transform, define physical operand/padding ranges, metadata ownership and a supported publication boundary. Keep C immutable while pair owners form upper K, synchronize before reading it for lower K, and publish the completed K/Qwork before delta. When gathering columns into UB, do not overwrite live row/column operands. Use supported ownership/alignment patterns for partial physical lines; derive them from the target rather than copying offsets or barrier counts.

All required collective barriers must be reached by inactive participants too. Guard data work, not the collective itself, according to the actual synchronization API. Verify GM tails and UB capacities separately.

## Validate the mechanism and its complete implementation

Use a small progression of falsifiable controls:

1. Original Q; opposite-sign correction; ordinary K versus pair-skew K. Preserve complete orthogonality and reconstruction checks.
2. Scaled versus unscaled arithmetic where both are representable; one common scale for A/W versus a deliberately inconsistent-unit negative control.
3. Applied target inputs, benign dense inputs, clustered spectra, exact skips, extreme supported scales and subnormal operands.
4. CPU model, bounded device-stage observations, then the normal complete NPU entry with source/API/device/input identities.

Preserve independent high-precision/interval oracles for sensitive roots. For an intentionally unchanged W, require W bits to remain equal; preserve unaffected small-path bits and exact known-skip Q. Check parent column dots when direction preservation is intended, separately from reference component error. After positive normalization, still test full Q orthogonality and original-A reconstruction.

Exercise changing values at the same allocations, supported executor modes, inactive groups and multiple waves. For restoration tests, compare against this candidate's first actual successful output on the same data, not a generated or parent Q that intentionally differs after refinement. Include actual caller/synchronization budgets: a default-synchronized success does not prove a shorter timed-call deadline. Do not read outputs after a failed execute/wait or erase that failure with a later healthy process.

An improved local counterexample, a complete NPU pass, diagnostic coverage, external acceptance and comparable performance are distinct conclusions. Measure refinement's added work only after preserving all required correctness gates; never repair device output inside the adapter or report CPU modeling as NPU execution.

# Eigh: caller contracts, reference conventions and staged diagnosis

Use this guide when a symmetric eigensolver passes one checker but fails another, when eigenvector directions differ, or when a numerical component passes in isolation but the complete NPU operator fails. For small-root accuracy, root bracketing, scratch memory and framework failures, read [numerics and memory](eigh-numerics-and-memory.md). For component errors remaining after direction alignment, read [residual refinement](eigh-residual-refinement.md).

The notation below uses a real symmetric matrix, eigenvalues W and eigenvectors in the columns of Q. For a complex Hermitian contract, use conjugate transposes and unit-complex phase alignment. Supported dtypes, shapes, tolerances and permitted implementation routes must come from the actual operator specification and target SDK.

## 1. Freeze the contract and inspect the real caller

Record the generated API's parameter/output order, tensor shapes, strides, storage offsets, allocation sizes, optional attributes, workspace query, executor ownership, synchronization and readback. Compare the native/framework caller with the test adapter before changing the kernel.

Construct A_eff from the selected triangle of the **stored input**. Averaging both triangles, or evaluating the unquantized generator input, checks a different problem. Where allowed, poison the ignored triangle to reveal accidental reads. Validate every batch matrix separately:

| Quantity | What to establish |
| --- | --- |
| W | Required storage dtype, finite values, specified ordering, and `abs(W-W_ref) <= atol + rtol*abs(W_ref)` with declared tolerances |
| Orthogonality | The contract's full-matrix norm of `Q.T Q-I`; do not divide an absolute Frobenius bound by n or batch size |
| Reconstruction | The contract's inequality for `A_eff-Q diag(W) Q.T`, with explicit zero-norm behavior |
| Residual | `A_eff Q-Q diag(W)` as an additional diagnostic; it does not replace the other gates |
| Legal inputs | Each supported dimension, the product of batch dimensions, dtype, layout, scale and any required spectral-gap condition **after storage conversion** |

A row-major byte store into a strided output view can transpose the logical Q. Orthogonality may survive while reconstruction fails. Inspect actual descriptors and writes; if the route lacks stride support, use a supported adaptation or reject unsupported metadata according to the contract. Do not transpose every output to fit unexplained external feedback.

Distinguish reused addresses, reused workspace capacity and executor reuse. Test only reuse modes supported by the API, and record which mode actually executed. Read outputs after successful device completion; preserve inputs and physical guard checks.

## 2. Separate mathematics, representation and acceptance

These are different conclusions:

1. W, orthogonality and reconstruction satisfy the mathematical contract.
2. The returned representation agrees with a specified reference's ordering, direction or basis convention.
3. The complete implementation meets the project's external acceptance gate.

For a self-contained sign example, let `A=[[2,1],[1,2]]`, `W=[1,3]` and `Q=1/sqrt(2)*[[1,1],[-1,1]]`. Replacing either column by its negative preserves `Q diag(W) Q.T`. An elementwise Q comparison can reject that equally valid decomposition.

For diagnostic comparison of real, normalized columns, align a candidate column by the sign of its dot product with the corresponding reference column. Keep direct signed, absolute and aligned differences separately. Near a zero dot, report direction ambiguity. For repeated or clustered eigenvalues, compare the relevant invariant subspaces/projectors rather than forcing one column assignment. Alignment belongs in diagnostic analysis unless the public interface itself defines a canonicalization; never alter device outputs in an adapter to manufacture acceptance.

A largest-component-positive convention in a specialized small-matrix branch need not occur in the general path. Audit each branch before generalizing a fix. An unknown checker's error fraction does not reveal its backend, hidden shape or wrong columns. A local NumPy/LAPACK comparison is a named reference, not proof that an external system uses it.

FP32 inputs and outputs do not identify a reference's internal precision. Pin the reference implementation and numerical backend. Check public examples against the actual input, comparison and permitted-library constraints before adopting their method.

## 3. Locate the first divergent stage, not just the final sign

For a Householder/divide-and-conquer solver, save one reproducible input and inspect:

| Stage | Questions that distinguish causes |
| --- | --- |
| Input/scaling | Which stored bits and selected triangle were read? Is the scale shared by all participants? |
| Householder | What H and actual tridiagonal T were produced, under which arithmetic order? |
| Leaves | What rotation, W/Q ordering and direction convention ran on the device? |
| Deflation | Which columns are active or inherited? Are coupling vectors normalized and source columns mapped correctly? |
| Merge | How are poles, permutations, root brackets and phase metadata associated? |
| Backtransform | Does captured Z solve the captured T, and does HZ reproduce the complete normal Q? |

Compare Z with a reference for the **same captured T**, then compare HZ with the result for original A. This separates tridiagonal solving from reduction/backtransform differences. Close child poles can exchange order after rounding even when each intermediate remains mathematically plausible. Recomputing only the final dot product more accurately cannot undo an earlier ordering decision.

Treat ordinary active columns and inherited/deflated columns separately. Missing a coupling-vector normalization can cross a deflation threshold; for a merge whose boundary vector requires a `1/sqrt(2)` factor, omitting it changes the branch as well as the magnitude. A direction rule inferred from ordinary columns can therefore fail for inherited ones. Trace source-column mappings and normalization at every recursive level.

Materializing leaf multiplications can improve agreement with one arithmetic model while changing complete-solver phases elsewhere. Likewise, an alternative mathematically valid Loewner/secular-vector formula or a tiny-coupling phase rule can fail under recursive propagation. Test complete eigenpairs across active/inherited classes, not only leaves. Increasing only final-dot precision cannot undo an earlier pole order or branch decision. Use the first differing stage to choose the next controlled experiment.

## 4. Use real NPU isolation, then return to a normal complete operator

CPU models can analyze captured inputs, operands and device stages; they do not execute or qualify the NPU candidate. Hold source, launch geometry, batch structure and input bytes fixed while changing the diagnostic control. Selecting a journal stage by changing batch size confounds the experiment.

For a runtime fault, isolate the first executed region with bounded stage controls. In a root-eligibility calculation, constructing unused emulated-wide-float arrays can introduce a failing path even though only a boolean classification is required. Derive an equivalent integer/bit predicate, check its domain and boundary truth table, then test it on the original normal NPU call. A volatile loop counter is not a substitute for this isolation. An equivalent rewrite removing a fault is useful evidence, but does not by itself identify a compiler-internal defect; bind generated code and actual device artifacts before assigning that cause.

After a stage fix, run the original failing input through the normal complete entry, including inactive groups, nonmultiple batches and subsequent waves. A Q buffer reused as a journal is not a valid eigensolver output. Keep prefix kernels, encoded diagnostic selectors and journal-output builds out of a release.

## 5. Make a narrowly supported numerical repair

Choose the comparator invariants from what the repair intentionally changes:

- A direction-only repair should preserve W and Q magnitudes, plus signed Q on unaffected branches.
- A [residual correction](eigh-residual-refinement.md) intentionally changes Q components. Preserve required mathematical gates, W if unchanged by design, unaffected-path bits, and intended column directions; do not require unchanged absolute Q everywhere.
- A repair of a root estimate must additionally preserve sorted eigenvalue/column association and resolve its targeted eigenvalue error.

When phase metadata depends on a rounding-sensitive pole order, a higher-precision Householder/Sturm guide can test that explanation. One narrow design computes only the required pole-order/left-count metadata and preserves the FP32 value solver, deflation policy and unrelated direction rules. A root-only guide cannot repair an already divergent internal node. Prove its scope before changing writeback.

If the target lacks the required native wide arithmetic, an integer-emulated guide is a separate implementation option, not evidence that a native double dtype works. Qualify actual NPU arithmetic, cost, capacity and lifetime, and validate W/magnitude/unaffected-branch invariants. A CPU guide or dtype documentation does not establish native support. Do not substitute an entire reference solver or host fallback for the required operator.

For scratch reuse, derive byte intervals and live ranges for H, T, guide records, flags and normal-solver buffers. Assign one writer per ordinary record and publish data before readers proceed. Inactive participants must still obey collective-barrier semantics. Recompute temporary metadata for changed input and every wave. Offsets and barrier counts come from this implementation, not another project's layout.

Pointer-like macro declarations need ordinary C/C++ declarator scrutiny: a macro expanding to `T*` does not make every name in `MACRO a,b;` a pointer. Use separate declarations where appropriate and inspect the first compiler error, including address-space qualifiers.

## 6. Freeze and test the oracle as carefully as the kernel

Keep each adversarial family's reference method and tolerances when changing runners. A general float64 eigensolver can lose the absolute accuracy of a tiny root beside a large spectrum. Use analytic values, independently derived high precision, or outward interval bounds where justified. A higher nominal dtype alone is not an accuracy certificate.

Run the validated baseline through a new adapter before adopting it. If old/new device input, W and Q are byte-identical while the verdict changes, examine oracle routing, storage conversion, norms and indexing first. Inject wrong eigenvalues, nonorthogonal Q and incorrect W/Q pairing separately and require rejection. Restore a damaged checker without weakening its thresholds.

Investigate numerical-library warnings with a bounded control: use simple known-answer operations and an independent accumulation route, retain finite/nonfinite checks, and compare the actual saved data. A finite result in one warning-producing call does not justify suppressing warnings globally or upgrading unrelated software.

Check whether requested output storage can satisfy extreme-scale/subnormal criteria independently of the solver. Document a representability limitation with a concrete construction or bound; do not silently remove an input class or change tolerance.

## 7. Bind every conclusion to source, payload, caller and input

Use the [build identity chain](build-identity.md). Separate independent builds from devices running a carried binary. For cross-device comparison, use identical stored inputs and the normal API, and report every differing compiler, framework and numerical mode. Matching CANN versions do not establish chip-only equivalence.

Derive regression points from actual specialized sizes, guide boundaries, tree/tile boundaries, L/U, active/inherited columns, large and tiny scales, and spectral-gap boundaries. Exercise changing data at the same addresses and batches spanning multiple active groups/waves. Check input preservation and guard regions. Preserve the strict oracle for each family.

Report full calls, matrix instances, columns and checks separately; these counts can overlap. One input at every size is not exhaustive spectrum or state coverage.

## 8. Keep sanitizer and release boundaries visible

Apply [instrumentation and coverage checks](correctness-sanitizers.md#each-requested-tool-must-really-execute). Valid mathematics, exterior canaries and an address within an allocation do not settle internal ownership or races. A timeout, missing completion or unresolved diagnostic is not a passed tool run.

Freeze the normal complete candidate and the evidence required by the project. Recheck accepted source and concurrent delivery changes before promotion. Keep numerical accuracy, diagnostic coverage, external acceptance and performance as separate states. This skill provides operator-engineering methods; account, submission, monitoring and server-power procedures belong to the relevant environment.

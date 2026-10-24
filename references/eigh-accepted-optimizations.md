# Eigh optimization patterns from accepted implementations

Use this guide when optimizing a complete symmetric eigensolver that already has an accepted NPU baseline. These patterns were used in a sequence of implementations with actual terminal external acceptance. They are engineering recipes, not portable performance claims or a certificate for new code. Project receipts and private source remain outside this package.

Start with [eigensolver correctness](eigh-correctness.md) for mathematical validity, reference direction and external acceptance. Use [numerics and memory](eigh-numerics-and-memory.md) for secular roots and workspace, and [residual refinement](eigh-residual-refinement.md) for component errors that remain after sign alignment. Do not describe a new residual/Cube fusion as accepted merely because an earlier implementation passed.

## Choose a change by its actual cost

| Measured cost | Pattern used in accepted implementations | Condition to preserve |
| --- | --- | --- |
| Full product matrices in a symmetric guide update | Compute one triangle and publish its mirror directly | Rounded operand order, signed zero, unique writers and DMA bounds |
| Excessive root iterations used only to order child poles | Refine overlapping root intervals in stages | Enclosure, strict separation and immutable classification inputs |
| Reconstructing a second full set of guide vectors for column signs | Propagate an adjoint/projection through existing transforms | Eigenpair correspondence, direction margin and complete fallback |
| Software arithmetic inside an auxiliary guide | Vectorize only the qualified FP32 region | Exceptional-domain handling, vector tails and the actual guide consumer |
| Expensive software floating-point division and square root | Replace scalar primitives with exact integer algorithms | Special values, normalization, remainder/sticky bits and final rounding |
| Serial small-matrix work or a duplicated small solve | Cooperative guide steps or an integrated small eigensolver | Shape/batch dispatch, complete W/Q and existing precision postpasses |
| An independent large guide whose consumers can use native metadata | Remove the redundant producer/consumer protocol | Native readiness, ordering metadata and every remaining reader |
| Serial initialization and child-basis packing before deflation | Distribute rows, chunks and column blocks across vector lanes | Physical ownership, local DMA completion and a common mixed-core barrier |

Several rows are successive alternatives. For example, accelerating an independent guide and later removing it are different candidates; their gains cannot be added. Profile the current accepted implementation before transplanting an earlier optimization.

## Symmetry can remove storage as well as arithmetic

For a symmetric rank-two update of the form

```text
A'[i,j] = A[i,j] - (v[i]*w[j] + v[j]*w[i]),
```

compute only `j >= i`. The owner of `(i,j)` publishes both the upper value and its lower counterpart. This can avoid materializing and rereading two full product matrices.

The algebra does not prove bitwise equivalence. A previous lower-row path may evaluate the two products in the reverse order; cancellation can expose different signed zeros. Retain the original lower calculation where that distinction is observable, or establish that the operator's actual contract permits the change. Do not remove a direction-sensitive operation solely because it is zero mathematically.

Assign each triangular pair to one writer. Prove the strided lower-column stores, partial final blocks and padded UB source bytes separately from logical matrix bounds. Keep existing producer/consumer barriers until their dependencies have been rederived. Less storage traffic does not itself justify a smaller workspace allocation.

## Refine order information only as far as its consumer needs

A guide may need child-pole order rather than full-accuracy root values. Suppose each root has an enclosing interval `[l_i,u_i]`. For roots from opposite children,

```text
u_i < l_j  =>  root_i < root_j.
```

If the intervals are strictly disjoint, any representative inside each interval preserves that cross-child order. Touching endpoints do not establish strict order.

An accepted approach first formed coarse intervals, classified cross-child overlap, refined only flagged intervals, then used the original full refinement for unresolved overlap. The classification read an immutable snapshot. Flags had separate storage, and all participants crossed common barriers before refinement and reclassification. Reading intervals while other lanes overwrite them changes the algorithm.

This shortcut applies only when the downstream consumer needs ordering. It cannot replace root accuracy in the returned W, a secular denominator or another consumer that uses pole magnitudes. Derive the enclosure from the actual Sturm/bracketing routine, including equal roots and endpoint conventions; do not assume that an iteration count is an error certificate.

## Compute the projection needed for direction calibration

Let a reference-compatible reduction give `A = H T H^T` and `T Z = Z D`. A reference vector is `H z_j`. Its alignment with a candidate vector can be evaluated as

```text
(H z_j)^T q_j = z_j^T (H^T q_j).
```

This moves the candidate through the adjoint transforms instead of reconstructing an independent `H Z` merely to take column dot products. Propagating the required projection through the leaf rotation sequence can also avoid materializing the leaf eigenvector matrix. Preserve the actual transform order, rotation orientation, UPLO mapping and eigenpair sorting.

Use a direction decision only when its computed margin exceeds a justified error bound. Bounds depend on conversion error, transform count, coefficient norms, accumulation and exceptional values. A threshold observed to work for one small-size range is not a universal certificate. If the bounded path is ineligible or ambiguous, reload the original input/candidate state and run the complete NPU guide fallback; do not continue from partially transformed scratch.

Column signs remain separate from mathematical correctness. Pure sign changes or bit differences against an older Q are diagnostics, not additional mathematical rejection rules. Repeated eigenvalues may need subspace reasoning rather than independent sign decisions. External acceptance of the new direction convention still requires its own result.

This pattern saves duplicated work inside a complete W/Q implementation. It does not authorize returning only some eigenpairs or replacing the output solver with a phase-only helper.

## Narrow mixed precision to an auxiliary region

One accepted intermediate change vectorized a guide's row update while retaining the native value solver and the guide's downstream consumer. It deliberately changed arithmetic to FP32; it was not bitwise equivalent to the original guide trajectory. A later accepted implementation removed that independent large guide, so this optimization is useful only while the guide remains live.

Before adapting it:

- Identify exactly which guide output reaches the native solver. A coarse ordering hint and a value used in root evaluation need different error arguments.
- Check conversions and products for nonfinite and subnormal values. Route unsupported values through the original arithmetic, with the original signed-zero cancellation handling.
- Define every padded vector operand. Round the active length to the API's actual processing granularity and prove both UB capacity and valid GM byte counts.
- Preserve scalar-to-vector, vector-to-scalar and MTE dependencies. Separate multiplies/adds/subtracts cannot silently become a fused expression if their rounding matters.

Checking only final finiteness is insufficient: a finite but changed intermediate may alter root order or a branch. Qualify the complete candidate across its own domain and measure its whole-operator cost. An earlier guide's acceptance does not qualify the vectorized version.

## Accelerate exact software arithmetic without changing the numerical contract

### Quotient digits with a corrected high-word estimate

For a normalized binary64 significand divisor `b` and remainder `r`, assume

```text
2^52 <= b < 2^53,  0 <= r < b.
x = r * 2^11
D = floor(b / 2^32)
estimate = floor(floor(x / 2^32) / D)
```

Here `x < 2^64`, `2^20 <= D < 2^21`, and the true next quotient digit is `floor(x/b)`, at most 2047. Write `b = D*2^32 + d`, with `0 <= d < 2^32`. Since `floor(x/2^32) >= floor(x/b)*D`, the estimate never undershoots the integer digit. Conversely,

```text
floor(x/2^32)/D <= x/b + (x/b)*d/(D*2^32).
```

Its excess over `x/b` is less than `2048/D < 1`, so it is at most one too high. One exact correction suffices:

```text
product = estimate * b
if product > x:
    estimate -= 1
    product -= b
digit = estimate
r = x - product
```

The estimate is at most 2048, so its product with `b` still fits unsigned 64 bits. Append five eleven-bit digits after the initial leading quotient bit. The resulting 56-bit working quotient and final nonzero-remainder sticky bit can feed the unchanged rounding/packing routine.

The proof concerns normalized significands. Keep sign extraction, NaN/Inf/zero handling, subnormal normalization, exponent adjustment and underflow/overflow packing intact. Before device use, compare digits, remainders and complete divisions against the original routine, including boundary values and negative controls. CPU equivalence establishes the integer algorithm, not the target compiler or NPU result.

### Radix-256 input for an integer square root

A digit-by-digit square root can consume eight radicand bits and produce four root bits per iteration. If an accumulated prefix satisfies `N = root^2 + remainder`, appending byte `c` gives

```text
N' = 256*N + c
base = 16*root
available = 256*remainder + c
```

Choose `digit` in `[0,15]` such that `2*base*digit + digit^2 <= available`, subtract that amount and set the new root to `base + digit`. Four descending bit trials implement the digit selection with shifts, comparisons and subtraction.

Preserve the original exponent normalization and final packer. A nonzero remainder supplies sticky information; dropping it changes rounding at boundaries. Prove every shift and trial product fits the chosen integer width. Test exact squares, their neighbors, exponent parity, subnormals, zeros, infinities and NaNs against the original primitive before whole-operator qualification.

These changes run inside the NPU implementation. They do not require a CPU fallback or an external complete eigendecomposition.

## Specialize small matrices without creating a second full solve

Two accepted stages addressed different small-matrix costs. One distributed guide initialization, matrix updates and projection application across vector lanes while preserving the original complete output solver. A later integrated path generated complete W and Q from one small reduction/leaf solve and retained its numerical fallbacks and precision postpasses.

For an integrated path, carrying the transform initialized to identity has a different role from carrying an already computed candidate Q for calibration. Track that distinction explicitly. Form the complete output vectors in the required orientation; do not treat a diagonal projection used for signs as an eigenvector matrix.

Keep the original input available until eligibility is final. Extreme-scale W can fail even when direction tests pass. Preserve structured-input and near-zero postpasses, their output ordering and exceptional behavior. End scalar-array lifetimes before reusing the same local storage for a postpass.

Use separate dispatch evidence for dedicated tiny sizes, the selected small range, multiple batches and the large path. A source-identical large branch can still compile with different resource use after a new class is added. Measure cooperative overhead on tiny matrices; more participating cores is not automatically faster.

## Remove an independent guide only after tracing its consumers

A later accepted large-size path used the native reduction/root metadata and removed the independent Householder guide plus its interval/pole publications. This was a dependency change, not permission to skip direction handling. Native phase metadata, relevant small guides, native failure handling and output postprocessing remained.

Trace every guide read, readiness flag and temporary arena before deleting producers. Disabling a readiness flag must prevent stale journal reads; remaining native producers must define all packed rows and padding consumed by Cube operations. Prove child-before-parent dependencies and metadata disjointness, including storage reused after a previous stage.

If reference compatibility for the replacement has not been established, retain the guide. Source analysis and mathematical validity alone do not certify the native direction convention. Re-run the candidate's complete NPU and external acceptance checks. Do not add together gains measured before and after removal of the same guide.

## Parallelize preparation around a serial deflation stage

Deflation may remain serial while its setup scales across vector lanes. Distribute output-zero rows, contiguous scratch chunks and child-basis column blocks using disjoint cyclic ownership. Let the same owner clear and populate each destination column. A small UB transpose tile can turn child row slices into packed basis columns.

Handle the final row/column tile using the actual child extent, not the parent padded size. Define unused tile bytes that a physical transfer may touch. Wait for MTE2 before scalar reads and for MTE3 before reusing the source tile. A local pipe barrier does not establish cross-core visibility.

Before lane zero enters the original deflation routine, all required AIC/AIV participants, including inactive work groups, must reach the common mixed-core barrier. Do not place that barrier under a lane-specific branch. Preserve later node barriers unless their dependencies are separately proved.

Measure the complete operator by shape and batch. Preparation can improve large matrices while slightly regressing small ones; retain those regressions in the decision rather than reporting only a favorable average.

## Keep compilation, packaging and acceptance as separate results

Retaining a few deliberate `noinline` boundaries can control compiler expansion in a large arithmetic-heavy translation unit. Build independent generated targets within measured CPU/RAM limits, and reuse already qualified artifacts when the relevant source/build identity is unchanged. Do not infer a compile-time gain from a device speedup, or assume a build-system `-j` value splits one compiler optimization pass.

Comment compaction solved a different problem: serialized submission size. Count the actual request body, including duplicated source fields and JSON encoding. A request-size rejection does not prove an illegal algorithm or a forbidden keyword.

If ordinary comments are compacted, preserve licenses, directives, literals, escaped physical lines and line-sensitive semantics. Check preprocessing-token equivalence with negative controls. This can justify carefully scoped reuse of prior evidence; it does not establish a newly built binary identity. External compilation/acceptance still belongs to the submitted source. Arbitrary variable renaming or removing copyright notices is not an optimization strategy.

For promotion, bind the exact candidate source, normal build, loaded artifact, inputs, complete outputs and independently checked results. Check mathematical accuracy, input/state handling, memory/synchronization coverage and paired whole-operator performance separately. A parent or two independently successful components do not qualify a new combination.

Scoped sanitizer success and physical guards do not prove full-domain safety. Preserve warnings, unsupported coverage and failed runtime synchronization as separate evidence; an external Pass cannot erase them. Query the actual terminal external result and every required checkpoint before calling the candidate accepted. Never map official checkpoint timings to matrix sizes without an actual case mapping, or compare local profiler latency with official timings as if they were the same measurement.

# Eigh: numerical, workspace and framework failure mechanisms

Use this companion to [eigh correctness](eigh-correctness.md) for small-eigenvalue errors at large scales, secular-root failures, workspace corruption, generated-code surprises and framework-only failures. The examples below are self-contained illustrations and diagnostic recipes, not claims that a particular SDK release has a defect.

## Classify the failing layer before choosing a repair

Separate fixture/oracle failure, registration/inference, workspace initialization, convergence/bracketing, W accuracy, full-Q orthogonality/reconstruction, reference representation and external acceptance. Follow the invoked methods and generated code: unused iteration constants, unreachable refinements and stale comments do not describe the active path. Verify actual numerical modes before blaming HF32 or a primitive the caller never executes.

## 1. Large scales, near-zero roots and arithmetic primitives

**Relative reconstruction can hide a bad small eigenvalue.** For `A=M*[[1,1],[1,1]]`, the exact eigenvalues are `[0,2M]`. With exact orthonormal eigenvectors, replacing the zero eigenvalue by epsilon produces relative Frobenius reconstruction error `abs(epsilon)/(2*abs(M))`. That can be tiny while the absolute error of the small eigenvalue is unacceptable. Check W independently of reconstruction.

**Do not clip small roots to zero.** A small root can be genuinely nonzero. Keep exact-zero and small-nonzero controls with known answers, evaluate both at supported scales after input quantization, and retain the absolute term in the W criterion. A norm-relative threshold does not establish a zero eigenvalue.

**Every lane must share the same scale before a collective reduction.** Publishing scale only on one lane can mix units in a distributed Rayleigh sum. Derive the common scale, broadcast/publish it before use, and retain compensated or otherwise justified accumulation. Reorder products only within the required numerical contract; forming normalized factors before rescaling can avoid an overflowing intermediate even when the final value is finite.

**Test arithmetic primitives with operand bits.** A function named FMA may wrap separately rounded operations. The FP32 operands `a=1+2^-23`, `b=1-2^-23`, `c=-1` give exact `a*b+c=-2^-46`. A correctly rounded fused FP32 operation preserves that result; separately rounding the product to FP32 first gives zero. Use a target-supported probe to determine which behavior the actual overload implements. Test division and square root near rounding boundaries too. A software-wrapper discrepancy does not prove every native instruction or compiler is wrong.

**Certificates must identify both quantity and slot.** A root/residual certificate must include bias of the computed Rayleigh estimate as well as arithmetic rounding; a bound derived after silently dropping that bias can accept a wrong-root negative control. It must also associate the certified root with the correct sorted W slot and Q column. An exact CPU feasibility result is not a device-side certificate.

**Avoid finite magic sentinels.** If `minAbs=1e30` initializes an argmin, values all larger than that sentinel may leave the wrong index selected. Initialize from a validated element or a contractually suitable identity; test both the selected index and value.

## 2. Secular brackets and failure propagation

Extract a failing batch matrix and rerun it alone before assigning the cause to batching. Capture the first failing internal node, not only the final root status.

Origin selection and endpoint checks must evaluate the same representable coordinates. In finite precision, an absolute midpoint reconstructed through a pole-plus-shift expression can differ from the stored midpoint. A sign change between those evaluations can invalidate the supposed bracket; extra iterations do not repair inconsistent endpoints. Keep one coordinate representation and endpoint bits through origin choice, sign tests, shifts and updates. Test adjacent representable values and root/pole boundaries.

Propagate child failures explicitly. A zero child vector can pass into a parent and later produce `1/sqrt(0)` and NaNs during normalization. A clean final status array cannot overrule an earlier failed child. Separate directly captured state from a reconstructed transient structure when explaining the cause.

## 3. Workspace ownership, physical tails and address units

| Failure mechanism | Repair and validation |
| --- | --- |
| Mailbox smaller than its physical writers | For L lanes writing K entries, prove capacity at least L*K, including padding. For example, 16 writers of 8 values need 128 slots, regardless of a smaller logical problem size. Update allocation, host size, kernel stride, declarations and offsets together. |
| Pipeline completion mistaken for a collective barrier | A local pipeline wait does not by itself publish data across cores. Derive producer/consumer scope and the required supported synchronization. |
| Mask applied after a full-width read | Initialize every physically read tail before the consuming load or operation; logical masking afterward cannot define unread bytes. Include inactive workers and padded rows/columns. |
| Byte address confused with element index | Verify the exact binding/offset API. Convert element offsets to bytes only for byte-address fields; ordinary element indexing must remain in elements. |
| UB alignment mistaken for GM access permission | Derive valid GM length, supported tail-copy behavior and sufficient UB capacity independently. Alignment alone cannot authorize rounded-up GM accesses. |
| Runtime-owned workspace mistaken for the user arena | Establish query bytes, the kernel-entry pointer and any documented user offset from the actual wrapper/ABI. Do not clear or scan a guessed prefix. |

Canaries cover only their guarded boundaries. Two overlapping live regions inside the same allocation can corrupt each other without touching an exterior canary. Prove highest accessed byte, ownership and overlapping lifetimes.

Use finite and NaN poison controls where supported. Multiplying by a zero mask does not clear NaN (`0*NaN` is NaN). A finite-poison test can accidentally pass while internal state remains uninitialized. Capture initialization/publication endpoints before claiming a missing compiler barrier. Normal and instrumented builds each need their own actual output checks.

## 4. Generated code and mathematical checks

Inspect whether a source sign branch survives lowering and reaches the intended core. For a 2x2 rotation, an incorrect sign can preserve orthogonality while breaking `A=Q diag(W) Q.T`. Use a self-contained matrix such as `[[3,1],[1,1]]`, whose eigenvalues are `2-sqrt(2)` and `2+sqrt(2)`. If a signed local coefficient disappears from generated code, an explicitly supported UB-backed intermediate can help test whether preserving that store/load changes lowering. Inspect the emitted branch and real normal output; that workaround is not a universal parser contract.

Derive strides from tensor geometry. A hard-coded tile width in place of the actual matrix leading dimension can cause overlapping blocks and unwritten elements. Test multiple tiles, boundary sizes and supported layouts; compilation success is not an indexing proof.

Column normalization is not global orthogonality: the two unit columns `[1,0].T` and `[cos(theta),sin(theta)].T` are strongly nonorthogonal for small theta. Check the complete Gram matrix. Any polar/refinement stage must also preserve reconstruction and W/Q pairing. See [residual refinement](eigh-residual-refinement.md) for a skew correction and its limits.

Run the original-A entry after backtransform and refinement. Root-only, tridiagonal and full-solver probes validate different scopes and need distinct source/artifact/caller identities.

## 5. Validation arithmetic and representability

Promote stored arrays to a suitable oracle dtype **before** multiplication, matmul and norms. An FP32 validator can overflow into `inf/inf -> NaN`, or report zero when only its denominator overflows. Casting the final scalar cannot recover the lost computation. Check finite intermediates and cross-check representative high-scale cases with an independent method.

Keep display floors out of acceptance predicates. `residual/max(norm,floor)` may be a reporting ratio, but a denominator floor can falsely accept nonzero reconstruction of zero A. Evaluate the original contract inequality and its explicit zero-norm rule.

A concrete storage stress test is `A=epsilon*[[0,1],[1,2]]`, with epsilon equal to the minimum positive FP32 subnormal. Its exact eigenvalues are `epsilon*(1-sqrt(2))` and `epsilon*(1+sqrt(2))`. FP32 W lies on integer multiples of epsilon here. Even allowing exactly orthonormal Q, the nearest stored eigenvalues leave a relative Frobenius reconstruction lower bound `(sqrt(2)-1)/sqrt(3)`, about 0.239. This illustrates a format limit rather than an ordinary solver bug; a contract allowing nonorthogonal Q needs its own corresponding bound.

Determine whether requested output storage can represent an acceptable result. Near subnormal spacing, a reference computed at higher precision and then quantized may itself fail the requested reconstruction bound. Verify this with explicit stored inputs and quantized outputs or a bound, retain unresolved contract implications, and do not silently exclude otherwise legal inputs. Combine these checks with [oracle controls](eigh-correctness.md#6-freeze-and-test-the-oracle-as-carefully-as-the-kernel).

## 6. GE shape inference is a distinct caller contract

Establish the operator prototype, input/attribute mapping, graph registration and matching host objects before changing kernel arithmetic. A missing registration or empty attribute table can stop execution before the numerical path is reached.

Framework unknown dimensions and shape-range lower bounds have their own conventions. A metadata descriptor containing unknown values or zero lower bounds is not necessarily a concrete zero-sized runtime input. Handle inference descriptors according to the framework while retaining the operator's runtime shape checks.

Compare reachable GE and native API calls on identical stored inputs and required reuse modes. Registration success, numerical correctness and external acceptance are separate results. Likewise, serialized tiling `sizeof`, descriptor capacity and consumed bytes are different quantities; inspect actual serialization before calling their difference an overrun.

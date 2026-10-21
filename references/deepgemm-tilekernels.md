# DeepGEMM, TileKernels and reusable kernel ideas

For an operational sequence from dependency checks to initialized device validation, use the [910B adaptation procedure](910b-porting.md). This reference extracts reusable mechanisms from pinned public implementations; it does not certify target compatibility.

## Separate architecture, API and algorithm compatibility

Before reusing a kernel library, check its pinned source, supported device, compiler/SDK, Python/framework/backend versions, numerical modes, build system and runtime entry. A library can be a valuable design reference without being installable on the target.

| Studied component | Evidence boundary |
| --- | --- |
| DeepGEMM-Ascend `3a35326271b069b8b5bf1a754435acd6cc91575b` | README targets950/CANN9.20, Python3.10+, C++20-capable environment |
| TileKernels `c1cf914a82e6901c679445f872051ce44ac2cc63` | README lists950/CANN9.2+, TileLang0.1.15+, Python3.12+ and PyTorch2.13+; separate NVIDIA backend |
| TileLang Ascend reviewed public source | Consult the selected commit's backend and requirements, then verify the installed wheel independently |

These rows document inspected versions; they are not a permanent support matrix. Do not assume a newer README describes an old installed wheel. Do not call TileKernels CUDA-only: the inspected source includes real Ascend implementations. Sources and exact URLs are in `sources.md`.

## DeepGEMM-Ascend's lightweight approach

The useful separation is:

```text
shape/layout/stage description
  → constrained copy + synchronization + MAD primitives
  → small specialized kernel
  → explicit epilogue and workload-specific configuration
```

Extract the relevant idea before importing a whole framework. A small vector operator with existing static UB offsets may need no additional descriptor layer. Abstraction is helpful when it removes real error-prone address/layout duplication while preserving a visible lowering to hardware operations.

### Shape-carrying descriptors

The reviewed [tile pointer implementation](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/tile_ptr.hpp) makes shape/layout/stage information available for address computation and specialization. Transfer compile-time invariants and a small interface, not unsupported types or chip constants.

For an adaptation, expose enough to prove:

- Element/storage type, physical memory space and layout orientation.
- Tile dimensions, padded storage, alignment and bytes per stage.
- Address of each stage and bounds within its owning allocation.
- Which quantities are metadata constants and which remain runtime values.
- A compiler-visible inline lowering and no accidental hot-path dynamic allocation.

Inspect generated code to confirm folding/inlining. An API library or source-size change is insufficient proof of reduced device work.

### Primitive wrappers and event directions

The [copy/MAD wrappers](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/copy.hpp) remain close to hardware operations. The [synchronization layer](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/sync.hpp) makes pipeline direction and stage explicit.

Transfer a clear dataflow vocabulary, event ownership and final-store completion. Do not infer that raw C intrinsics inherit an Ascend C wrapper's implicit dependencies: protect the Cast/Gather-to-first-raw-operation boundary as well as dependencies inside the replacement.

### Model fixed issue cost as well as bandwidth

The reviewed [heuristics](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/csrc/jit_kernels/heuristics.hpp) include load-issue costs as well as data volume. This motivates measuring transfer count, issue/synchronization overhead and useful bytes separately for tiny operators. Its calibration numbers, including a 64-cycle term, are not measured constants for 910B.

Fit any new cost model to the current chip, compiler, workload and protocol. Use it to choose experiments, not as a substitute for actual measurements. Fewer bytes can still be slower if they require more instructions or events.

### Pipelining, sparse loads and epilogues

Study multi-stage/coroutine organization when there is real work to overlap, enough on-chip capacity and a proven ownership graph. Sparse loading is useful only when the algorithm has exploitable sparse access and the address/issue overhead is justified. A one-tile-per-core vector workload may offer no pipeline opportunity.

Fuse a vector epilogue only when its semantics and data lifetime match the operation. Count its dtype conversion, mask/padding, memory and synchronization requirements. An upstream high-throughput GEMM does not prove a strict-comparison epilogue is cheap or numerically equivalent.

## Validate MAD compatibility in stages

Separate ordinary MAD, MX/low-bit instructions, register-vector APIs and layout wrappers. A full newer-chip include tree can fail on a type such as `float4_e2m1x2_t` even when a required ordinary MAD primitive has a supported target equivalent. Conversely, removing that type does not establish compatibility for all remaining dependencies.

First compile and link a native target-supported control, then add a minimal descriptor/wrapper. Include actual target flags and memory qualifiers. That proves compatibility only for the compiled invocation. Before execution, initialize correctly laid-out operands and padding, define accumulation mode, complete transfers/events, and check independent numeric outputs. Never launch an uninitialized compile probe.

Pointer-based vector APIs and register-vector APIs can belong to different target routes behind similar umbrella headers. Resolve the installed target's implementation instead of importing another architecture's names or feature assumptions.

A newer-header failure does not prove that 910B lacks ordinary FP32 matrix multiplication. [CANN's HF32 documentation](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/900/API/ascendcopapi/atlasascendc_api_07_0258.html) distinguishes rounded HF32 input mode from regular FP32 matrix multiplication. Inspect the installed signature and explicitly validate the selected numerical mode.

## Preserve rounding when considering a matrix reformulation

A scalar contract can require Sub/Mul/Add/Add with FP32 rounding after each step, followed by strict comparison; see the [worked example](ascendc-invariants.md#exact-semantics-are-an-implementation-constraint). Expanding it into a matrix expression can change rounding, accumulation and input modes. Multiple MADs also introduce layout, L1/L0 transfers and comparison costs. Prove the arithmetic and complete dataflow before benchmarking such a reformulation.

For a genuine matrix-heavy operator, use a separate acceptance plan: initialize correctly laid-out operands, verify all precision modes and tails, validate accumulation/layout and then measure. Do not force matrix machinery into a latency-bound vector problem because it has impressive throughput elsewhere.

## TileKernels: concrete ideas to reuse

The inspected source has host dispatch and backend-specific kernel code. Read each relevant host/kernel/test trio, rather than assuming the common Python API selects the same implementation on every platform.

| Observed source pattern | Transferable method | Boundary |
| --- | --- | --- |
| `quant/cast_kernel.py` uses dtype and divisibility information | A small set of metadata-driven specializations | Prove the divisibility assumption for actual shapes |
| `quant/cast_asc.py` separates tail work and stages UB reuse | Keep the steady path simple; explicit lifetime/tail ownership | Extra stages need actual overlap and diagnostics |
| `engram/engram_hash_asc.py` organizes per-token work in its SIMT route | Fuse work per logical row; bound valid rows | Do not assume identical SIMT facilities on an older chip/backend |
| `transform/rope_asc.py` couples field layout and register computation | Co-design extraction, interleaving and arithmetic | Register instructions and fused arithmetic are chip/numerical-mode specific |
| `config.py` distinguishes Cube/Vector resources | Derive block rows from the actual memory/resource budget | Do not copy950 UB constants to910B |
| Testing utilities have their own timer protocol | Preserve correctness and report benchmark settings | Their default warmup/repeat settings are not interchangeable with another protocol |

Each row describes the pinned source, not a promise to preserve those paths in future versions. Link to it in `sources.md`; do not bundle entire upstream kernels without need. If code is actually reused, preserve the upstream license and version notice as required.

## A compact library-reuse decision

Before adopting an idea, answer:

1. Does it match the mathematical operation and required precision/order?
2. Is it supported by this exact chip/compiler/backend, not only a nearby version?
3. Does it change the real device dataflow or only source spelling?
4. What new memory, layout, synchronization or runtime dependencies arise?
5. Can a minimal initialized prototype validate the relevant mechanism?
6. Does the improvement survive the actual framework boundary, full workload and a fair normal-binary measurement?

Report code review, compilation, device correctness and performance as different results. High-quality library code is a strong source of hypotheses and structure, not a warranty that this kernel uses all available performance.

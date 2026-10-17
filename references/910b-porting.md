# Adapting DeepGEMM and TileKernels to 910B

Use this procedure when a useful upstream mechanism targets a newer chip or software stack. It is an engineering plan, **not a completed 910B port or a promise that either package can be installed unchanged**. The [reviewed snapshots](deepgemm-tilekernels.md#separate-architecture-api-and-algorithm-compatibility) target Ascend 950. A newer source revision needs its own compatibility review.

Read the relevant path: [common preparation](#1-common-preparation), [DeepGEMM MAD/Cube](#2-deepgemm-mad-and-cube-path), [TileKernels/TileLang](#3-tilekernels-and-tilelang-path), then [acceptance](#4-acceptance-and-handoff). Reuse the [installation guide](tilelang-installation.md) for environment commands; do not duplicate or replace it with an unconditional package install.

## 1. Common preparation

### Fix the target, contract and reuse level

Record the actual 910B variant, compiler target, driver/runtime, resolved CANN SDK, Python ABI/CPU architecture, framework pair, TileLang distribution/backend and source commits. Collect these from the execution environment and installed-version documentation. Host CPU count does not establish NPU core count. Preserve the working environment and baseline; test a different stack in an isolated task environment before changing the project runtime.

Select one operator or mechanism and its numerical contract. Choose the smallest appropriate reuse level:

| Reuse level | When to choose it | Required outcome |
| --- | --- | --- |
| Unmodified package | The selected release actually supports the complete target stack | Import, representative real-device calls and integration pass; a README or successful installation alone is insufficient |
| Minimal mechanism port | The algorithm fits and equivalent target primitives exist, but upstream headers, imports or scheduling do not fit | A small target-specific implementation with explicit layout, events, guards and tests |
| Idea-based implementation | New-chip instructions or dependencies prevent useful source reuse | Implement the specialization, dataflow or pipeline idea using supported TileLang or Ascend C; identify it as a rewrite |

Do not present the latter two as full library compatibility. Do not spoof a 950 architecture, invent unsupported types with typedefs, lower dependency minimums without investigation, or suppress compiler checks to make a build pass. Emulating low-bit arithmetic through supported types is a separate algorithm candidate requiring the original packing, scaling and rounding semantics; changing FP4/FP8 storage to BF16 is not an equivalent port.

### Build a compatibility map before a full build

Trace the selected entry through dispatch, imports/includes, kernel, helper/configuration and tests. For each required operation record:

```text
upstream commit + entry/file/symbol:
required dtype / layout / memory space / instruction / numerical mode:
target SDK header or backend lowering + version + signature:
target resource bounds and copy/alignment units:
proposed action: reuse / replace / emulate / reject
evidence: reviewed / compiled / linked / device-correct / safety-checked / measured
probe or test artifact + failure or uncovered cases:
```

Keep unresolved rows visible. Distinguish a missing Python API, missing SDK overload, unsupported instruction, layout mismatch and incompatible arithmetic; each needs a different fix. An empty header search is a search result for that SDK and scope, not proof that every supported API route is absent.

Use progressively stronger probes: import/include → compile/link → **initialized** device computation → complete operator → safety and performance. A minimal probe should isolate one mechanism. Save its command, target, inputs and artifact hashes. Never launch a compile-only kernel with uninitialized L0 operands.

## 2. DeepGEMM MAD and Cube path

1. **Choose a matrix workload and a supported type first.** Read the selected kernel with [tile descriptors](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/tile_ptr.hpp), [copy/MAD wrappers](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/copy.hpp) and [events](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/sync.hpp). Begin with an ordinary FP16 or BF16 dense GEMM only after checking the target's actual operand/accumulator support. For a vector operator, extract useful metadata or transfer-cost ideas instead of adding Cube work without a valid algorithm.

2. **Separate ordinary MAD from newer features.** Make independent map rows for ordinary matrix multiplication, MX/low-bit types and instructions, register-vector epilogues, copy/layout operations and pipeline mechanisms. The historical full-header probe failed first at `float4_e2m1x2_t`; removing that name alone does not establish compatibility for the remaining headers. Inspect transitive includes and isolate only the required ordinary-MAD path. Preserve upstream notices when copying code.

3. **Establish a native SDK control, then a thin-wrapper probe.** Use a target-supported SDK example/template with its real target flags, memory qualifiers, alignment, operand layouts, initialization flags and signatures. Compile/link that control before wrapping its primitive. A raw `asc_mmad` invocation and an Ascend C `Mmad` wrapper can have different signatures and surrounding obligations; inspect the installed release instead of copying a 950 argument list. Then add the smallest shape/layout descriptor and verify packaging with the [identity guide](build-identity.md). If the control fails, diagnose the SDK/target first; if only the wrapper fails, narrow its dependencies.

4. **Turn the compile probe into one complete initialized tile.** Implement the target-supported equivalent of this conceptual dataflow; it is not an API call sequence:

   ```text
   initialized host operands → GM → L1 → correctly laid-out L0A/L0B
     → MAD with defined accumulator initialization → L0C
     → SDK-supported writeback/conversion → GM → host comparison
   ```

   Prove physical strides, fractal ordering, padded sizes and each stage's allocation bounds. Initialize padding that the instruction can consume. State producer/consumer event directions, wait before buffer reuse, and complete final writeback before return. Start with one core, one tile, one stage and no fused epilogue or atomic accumulation. Use zeros, identity-like operands, distinct row/column patterns and signed/cancellation cases to expose layout and initialization errors; an all-ones result alone is weak evidence. Synchronize and check runtime errors before accepting output.

5. **Validate numerical mode, then grow coverage.** Fix input, product, accumulation and output types, contraction and permitted tolerance before comparison. For FP32, explicitly check regular versus HF32 input mode using the installed-version API; [HF32 documentation](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/900/API/ascendcopapi/atlasascendc_api_07_0258.html) does not imply identical arithmetic. Use an independent reference with the intended arithmetic, not a second call into the candidate. Add multiple K tiles with defined first-tile initialization/subsequent accumulation, then M/N/K tails, transpose/layout variants and repeated changed inputs. Exact intermediate rounding or a different reduction order may invalidate the matrix reformulation even when typical random tests pass.

6. **Add pipeline and epilogue mechanisms separately.** Size L1/L0/UB, scratch and live stages from the actual target, not 950 constants. Add a second stage only after multiple tiles exist and overlap has a falsifiable benefit. Draw ownership/events for each stage; recheck every buffer lifetime after scheduling changes. Reimplement an unavailable register epilogue through supported vector operations when its semantics can be preserved, accounting for extra transfers and mixed Cube/Vector synchronization. Do not carry over coroutine or cross-core protocols unless their required mechanisms are supported and validated.

7. **Integrate and calibrate on 910B.** Preserve public shapes, optional C/bias, output dtype, executor/workspace lifetime and dynamic inputs for the chosen entry. Mark unsupported entries explicitly instead of claiming library-wide support. Keep JIT architecture and cache identity tied to the actual target/toolchain, or use a verified native integration. Refit tile/core/stage choices and transfer-issue costs through bounded experiments; do not reuse 950 calibration or peak-throughput claims. Include packing, conversion and launch costs when the caller's metric includes them.

**Historical stopping point:** ordinary BF16 `asc_mmad` compiled and linked on 910B2/CANN 9.0.0, with packaging identity checked. It was never initialized and launched, so steps 4–7 remain a proposed procedure for this adaptation. The separately tested raw vector C API candidate is not evidence of a working MAD port. See [the probe record](deepgemm-tilekernels.md#what-the910b-mad-probes-actually-proved).

## 3. TileKernels and TileLang path

1. **Select the Ascend entry and follow its complete dependency path.** Inspect host dispatch, backend kernel and tests together. For example, the reviewed [cast dispatch](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/quant/cast_kernel.py), [Ascend cast](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/quant/cast_asc.py) and [test file](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tests/quant/test_per_token_cast.py) show different parts of the contract. Trace package initialization and transitive imports too: this dispatch imports a CUDA module, and common configuration references low-bit type symbols at import time. A target can fail before selecting the desired kernel. For an authorized minimal port, isolate those dependencies in task-owned code; do not patch the shared installed package or assume an unused branch is harmless.

2. **Get a compatible backend working independently.** Follow [TileLang installation and verification](tilelang-installation.md): match Python ABI/CPU architecture, CANN, torch/torch_npu and the actual Ascend compiler backend; set a private cache before first import. Pass an official small initialized vector example on the target before importing TileKernels. The reviewed TileKernels package minimums differ from the historical 910B stack. A working older TileLang wheel does not satisfy newer APIs, while a newer wheel does not automatically make 950 kernels portable. Keep a full-package installation and a mechanism rewrite as separate routes.

3. **Probe the kernel's actual language features.** Map imports, dtype symbols, SIMT/SIMD scopes, register operations, copies, reductions, atomics and explicit events to the installed backend's supported lowering. Compile minimal probes and inspect generated source and compiler target. A supported `T.Parallel` or basic copy does not prove a new `SimtVF`/register interface works. If the source cannot be lowered, replace only the unsupported mechanism with supported tile/vector operations or choose the [Ascend C route](workflow.md#backend-selection-by-workload-and-stage). Report a numeric or hardware blocker when no equivalent exists; spelling changes alone do not repair it.

4. **Recalculate launch geometry and storage.** Replace [configuration assumptions](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/config.py) with verified target values: Cube/Vector core geometry, UB capacity, alignment, scratch and compiler reservations. Do not assume a fixed Vector-to-Cube core ratio from a helper. Derive block rows from the maximum live footprint, including padding, predicates and all stages. Guard divisibility specializations with actual metadata, preserve a valid tail path and prove unique output ownership. Keep runtime tensor values out of host specialization keys.

5. **Build one complete conservative kernel.** Begin with one supported dtype, one simple tile path and explicit tails; then add the required branches. For a cast-like adaptation, verify input extraction, conversion rounding/saturation and store bytes before adding double buffering. For RoPE-like work, verify field interleaving and contraction against the actual formula before fusing operations. Inspect [generated TileLang code](tilelang.md) for stores, scope, masks, buffer reuse and synchronization. Any manual export transformation becomes a distinct candidate with new source/binary identity.

6. **Restore the intended host behavior and tests.** Check output dtype/shape, strides, broadcasting, scale/quantization metadata, supported shapes, stream behavior and autograd only where the chosen public API requires them. Run upstream tests that apply, and add an independent oracle and adversarial cases rather than weakening unsupported tests to pass. For a subset port, reject or use an explicitly validated fallback for uncovered metadata. Test same-address value changes and specialization/cache reuse. If packaging needs AOT or ACLNN, validate that new caller separately from JIT correctness.

7. **Tune the proven target implementation.** Explore justified tile, core and pipeline variants with resource limits from step 4. Retain the best valid baseline and measure under the same caller, cache conditions and protocol. Include JIT/setup separately from steady-state execution. Keep supported specializations with demonstrated scoped gains; do not copy the upstream default timer or claim that TileLang source implies saturation. Complete the common acceptance gates below before promotion.

**Historical stopping point:** the TileKernels Ascend sources were reviewed and their ideas informed local experiments. TileKernels itself was not installed or executed in the case project. Local TileLang geometry-kernel results validate those particular kernels, not TileKernels package compatibility on 910B.

## 4. Acceptance and handoff

Promote only the exact supported subset whose evidence passes these gates:

| Gate | Evidence to retain | Does not establish |
| --- | --- | --- |
| Environment/import | Exact package/backend paths, versions and target; required entry imports | Device execution or complete library support |
| Compile/link/identity | Fresh command/config, generated source, target artifacts and integration hashes | Initialized operands, correct layouts or runtime selection |
| Device correctness | Independent expected outputs, actual caller, numerical mode, all supported branches/tails and changed-value repeats | Race freedom or speed |
| Safety | Actual instrumented memory/synchronization checks for supported cases; unresolved coverage stated | Universal safety outside that coverage |
| Performance | Normal binary, comparable baseline, raw samples, repeated paired results and setup/integration costs | Other-chip peaks or gains on untested workloads |

Use the existing [correctness/sanitizer](correctness-sanitizers.md) and [performance](performance.md) protocols. During setup and correctness work, follow the [CPU/NPU queue policy](workflow.md#overlap-cpu-and-npu-work-when-their-dependencies-permit) so independent builds, reference preparation, device validation and result analysis can overlap in both directions. Publish immutable candidate artifacts before device dispatch; never replace an active job's package or kernel files. Formal performance capture needs its prescribed isolated window.

Deliver the upstream commit/license, compatibility map, exact supported operator/metadata subset, small adaptation diff, reproducible build/run entry, target resources, source-to-binary identity, independent outputs, diagnostics, raw timing, failed probes and baseline rollback. Mark unsupported features and each unfinished gate. If a mechanism cannot be ported usefully, preserve the useful design lesson and the specific blocker without labelling it a successful port.

# TileLang Ascend: development and failure isolation

## Version boundary

The hands-on case used 910B2/CANN9.0.0, Linux aarch64, Python3.11.15, torch2.7.1+cpu, torch-npu2.7.1.post4 and the official `0.1.1.10+ubuntu.20.4.cann900` TileLang Ascend wheel. These are historical tested coordinates, not recommended latest dependencies.

The separately reviewed upstream snapshot was commit `1d5daf0385156cbe0c499a16c10935c5190642a4`, on the `ascendc_pto` route. Current documentation, old wheel and generated helper headers can differ. Inspect the actual imported module, signatures, parser and codegen. In the old wheel, `T.tile.*` existed while some top-level conveniences and a `jit(compile_flags=...)` parameter did not.

An official vector-add smoke confirms installation and that simple call chain. It says nothing about dynamic shapes, tail copies, optional scalars, strict rounding, AOT integration or the performance of your operator.

## Setup on a new server

If TileLang is absent or incompatible, follow [installation and verification](tilelang-installation.md): inventory the target, reuse or isolate a compatible Python environment, select an official Ascend wheel or a pinned source build, then verify import/compiler/device behavior separately. Loading this skill does not install dependencies or authorize server access. The historical wheel above is a reproduction coordinate, not a default for new machines.

## 1. Keep frontend, generated code and execution separate

At each revision retain:

```text
Python/DSL source + backend commit/wheel/config
→ parsed IR + generated Ascend C
→ helper closure + compiler options + device artifacts
→ actual callable/ABI and entry topology
→ device outputs + diagnostics + normal-binary measurements
```

Use the installed version's supported source-inspection API; the reviewed upstream guide documents `get_kernel_source()`. Check generated shape assumptions, pointer/stride arithmetic, masks, padding, events, constants, scalar scope and kernel core guards.

The compiler is part of the implementation. “All four operations appear in Python” does not prove the device executes them with the intended rounding and ownership. A debug tensor or uninitialized output containing NaN does not by itself establish which writes ran.

## 2. Pass tensors with the declared representation

If a kernel declares flat GM tensors, pass real contiguous flattened views. Retain the original AoS interpretation in the independent oracle. Record physical allocation, stride and logical return shape. A callable may allocate padded storage and return a legitimate logical view; the tester must not silently crop a wrong return value into correctness.

Inspect `T.copy` lowering rather than inferring it from a logical shape. The studied `[tile,1]` UB output generated a helper invocation equivalent to64 small blocks with UB stride32B, reading `res[0],res[8],...,res[504]` from a64-float buffer. B33 had29 mismatches, including25 nonbinary values. One-dimensional continuous UB/GM representation corrected that specific layout error.

For every helper invocation, interpret template and runtime parameters using the actual helper definition. Mark byte/block/element units and derive physical last addresses. A shape-correct reference and allocated UB large enough in total do not excuse undefined per-buffer reads.

## 3. Tail compilation is its own test matrix

Use valid full/tail ownership. Do not shift a writable tail backward without proving legal reads and unique plain-store ownership; backward-aligned reads or correctly masked owned stores may be valid. Compile single-tile, multi-tile, exactly divisible and tail1 shapes, not only one small smoke.

In the old backend, a conditional copy extent produced invalid C++ with a local declaration inside the helper argument list, such as `copy_gm_to_ub(..., int32_t condval; ...)`. B33 compilation did not predict B65/B129. Explicit full/tail branches fixed the relevant generated syntax; overlapping fallback windows were not an acceptable repair.

When possible, keep one shared compute body between input and output tail branches. Check actual generated code after doing so; the parser may lower seemingly equivalent syntax differently.

## 4. Inspect parser semantics, not only type annotations

The old TVMScript frontend did not accept postponed string tensor annotations in the tested pattern; removing `from __future__ import annotations` allowed real compilation. This is a version-scoped parser failure, not a universal prohibition on that Python feature.

Its `T.alloc_var` local Buffer was bound by the parser as a BufferLoad. Indexing the bound name again for assignment failed with `Expected Buffer but got BufferLoad`; bare-name assignment produced the intended BufferStore. Passing the underlying Var and passing a BufferLoad also took different scalar-printing paths.

Do not canonize an internal escape such as `.buffer.data` as a portable public API. Inspect parser→IR→codegen for the installed release, then verify the value on the device. Compiling a scalar expression proves neither its value nor its execution core.

## 5. Check scalar attributes bit by bit

The original ratio `0x3f7fffff` was printed as decimal `9.999999e-01f`, which compiled to `0x3f7ffffe`: one ULP lost before arithmetic. B65 failed44/65 rows for both coordinate dtypes.

Include the full attribute round trip in numerical testing: Python value → specialization key/literal or ABI → generated constant/parameter → device value. Test near-one, cancellation, equality and adjacent decision values. Exact intermediate arithmetic cannot compensate for an incorrectly transmitted attribute.

The tested fix used a true runtime FP32 scalar, passing a Python `float` representing a previously quantized FP32 value as required by that adapter. Other possible routes, such as supported hexadecimal literals/bitcasts, require actual backend verification. Do not use epsilon or change the input domain to conceal the failure.

## 6. AIC and AIV do not share local scalar registers

Automatic mixed scheduling placed a threshold GM read on AIC while vector Adds consumed an AIV-local scalar still initialized to0. At B65/FP16 with threshold2,44/65 rows were wrong—the same count as the unrelated ratio-literal defect.

Inspect AIC/AIV guards, register/UB ownership, core mapping and the scope of each read/use. A cross-core wait does not copy a local scalar variable. Do not add meaningless synchronization to an ownership error.

The tested expert candidate made vector ownership explicit with `T.Scope("V")` and disabled that version's `TL_ASCEND_AUTO_CV_COMBINE`. It subsequently passed the stated precision/freshness tests. This was a version-specific experiment, not a recommendation to disable automatic synchronization or combination globally. Manual scheduling requires a new complete dependency graph and diagnostics.

Exporting MIX code to a pure-AIV entry requires reproving core-ID/subblock mapping and BlockDim. Removing guards mechanically can duplicate or omit work.

## 7. Compiler-managed mask state is conditional analysis

The reviewed upstream implementation tracks vector mode and mask payload, reuses a proven state and invalidates/merges it at uncertain calls or control flow. Read the [pinned mask design](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/docs/ascend/compiler_managed_vector_mask.md) before treating it as a model.

Transfer the idea of whole-path state analysis, not “remove every ResetMask.” Verify current helper side effects, casts, count/repeat behavior and unsupported `isSetMask` parameters. Source-level mask deduplication can generate exactly the same device code as the baseline.

Gather interfaces are not interchangeable: the reviewed tile gather uses byte-offset indices, unlike this case's GatherMask. PTO and Ascend C routes also have different restrictions. Select the actual backend before interpreting its API contracts.

## 8. Test all three cache lifecycles

Check independently:

1. First compile and first execution.
2. Repeated calls with changed shapes/attributes/data in one process.
3. A new process reloading the persistent cache.

The old wheel compiled and reused some dynamic kernels successfully in-process, but cross-process reload failed Cython symbolic-shape binding with `Unfounded symbolic var: n_boxes`. A fresh private cache isolated the issue and allowed the stated precision matrix. It did **not** fix or validate the broken reload route.

Record cache key assumptions, source/backend/configuration/target and instrumentation separation. AOT can avoid that particular Cython layer; it still requires its own full integration verification.

## 9. Set worker cache before the first import

In that wheel `TILELANG_CACHE_DIR` became a module constant at import and KernelCache had singleton state. Changing `os.environ` per job in a reused worker did not switch the real cache, making reported provenance incorrect.

For bounded parallel export:

- Use an appropriate fresh-process model; do not fork a parent with initialized device state without backend support.
- Set each worker's unique cache before the first backend import and keep it fixed for that worker.
- Read back module/instance cache directories and assert agreement with the manifest.
- Write each job to an independent output; map results by explicit configuration keys, not completion order.
- On failure stop new dispatch, wait for started children and retain partial sources/failure records; do not manufacture a complete success manifest.
- A genuinely loaded temporary library can live outside the persistent cache. Record the real path/hash rather than forcing an assumed location.

The 16-configuration/four-worker export took about 54 seconds in this case. This is tooling throughput, not a kernel improvement.

## 10. AOT is an independent delivery chain

Only choose AOT when the target framework needs it or it serves the measured design. Native TileLang is also a valid route where the runtime supports it; an existing Ascend C template does not prove another backend is prohibited.

For AOT:

1. Freeze the DSL source and backend environment.
2. Actually compile each selected dtype/presence/geometry specialization.
3. Record configuration key, exported symbol, precise argument order/types, dimension derivation, generated-source and loaded-library hashes.
4. Select exported functions by that full key. Do not zip alphabetically sorted records with a differently ordered combination list.
5. Check optional-input ABI; an absent threshold entry may have one fewer GM pointer.
6. Wrap to the target entry mechanically and describe every change to ABI, launch mapping and validation guards.
7. Stage the framework host tiling and device resources; verify actual library/OPP binding.
8. Rerun real entry precision, input freshness, instrumented checks and normal-binary performance.

Generated AOT source can be independent of Python/Cython at execution. Verify that the actual test did not import/JIT/fallback to TileLang if claiming that property. Compilation/export success is not a substitute for real framework execution.

## 11. Preserve helper meaning when extracting generated code

If making a self-contained helper closure:

- Trace the transitive called-symbol set, including overloads, variable templates, namespace/using and dependencies.
- Preserve declarations in their actual source order; name-sorting can place templates after use.
- Keep upstream license notices in valid C++ comments and record source versions. Do not embed raw license prose as C++ tokens.
- Preserve the full device/inline declaration contract. The studied `CATLASS_DEVICE` included `__forceinline__ [aicore]`; a shorter replacement lost part of it.
- Recompile and compare allocated/relocation sections after the change.

In this case the corrected inline spelling changed the API-library hash but left the device allocated/relocation content identical. It was not evidence of a faster kernel. Do not copy an entire external framework when a small proven closure or the original dependency is sufficient.

## 12. Static UB rewriting must reject unknown input

Removing TPipe/TBuf can be considered only after establishing all relevant allocator/helper/lifetime uses. A safe narrow transformer accepts known constant buffer declarations, one receiver, exactly understood InitBuffer/Destroy order and constant legal offsets. Reject unknown tails, receivers, duplicate initialization, dynamic offsets, overlap, misalignment and overflow.

Maintain byte offsets versus element counts, API scratch reservations, actual maximum required bytes and host guard. Verify generated function body and complete function hashes separately by reading back the written output. CPU transformation checks do not prove device lifetime/safety or SDK independence.

Do not copy the case's fixed UB capacity, guard, conversion count or16-function specialization count. Fresh build, real entry precision, instrumentation and performance are still necessary for each transformed candidate.

## 13. Evaluate the entire execution path

The TileLang AOT experiments substantially shrank device text after structural changes and passed broad precision, yet did not establish a final performance win over the native baseline. DSL choice and high-quality reference kernels do not guarantee saturation.

Inspect fixed setup, dynamic dispatch, TPipe/helper work, field extraction, padded conversions, masks, synchronization, launch geometry and actual device artifacts. Benchmark the same framework boundary and output metadata. Keep first-JIT, steady-state call, disk reload, export throughput and device latency as distinct measurements.

# TileLang Ascend: development and failure isolation

## Version boundary

Record the installed chip, CANN, Python ABI/CPU architecture, Torch/TorchNPU pair, TileLang wheel/backend and source commit. The frontend, helper headers and generated device code are version-specific. Do not assume a current source example describes a different installed wheel.

The [reviewed public source snapshot](sources.md#tilelang-ascend) is commit `1d5daf0385156cbe0c499a16c10935c5190642a4`. Inspect the actual imported module, signatures, parser and codegen: a backend can expose `T.tile.*` without a corresponding top-level convenience, and its `jit` may not accept another release's options.

An official vector-add smoke confirms installation and that simple call chain. It says nothing about dynamic shapes, tail copies, optional scalars, strict rounding, AOT integration or the performance of your operator.

## Setup on a new server

If TileLang is absent or incompatible, follow [installation and verification](tilelang-installation.md): inventory the target, reuse or isolate a compatible Python environment, select an official Ascend wheel or pinned source build, then verify import/compiler/device behavior separately. Loading this skill does not install dependencies or authorize server access.

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

Inspect `T.copy` lowering rather than inferring it from a logical shape. A singleton dimension can select a strided helper rather than a contiguous transfer. As an address counterexample, copying 64 single-float blocks from a 64-float buffer with a 32-byte source increment reads indices `0,8,...,504`, beyond that buffer. Trace the actual helper units and final address. If the operation is logically contiguous, a one-dimensional continuous UB/GM representation can avoid the mistaken stride; recheck tails and write ownership.

For every helper invocation, interpret template and runtime parameters using the actual helper definition. Mark byte/block/element units and derive physical last addresses. A shape-correct reference and allocated UB large enough in total do not excuse undefined per-buffer reads.

## 3. Tail compilation is its own test matrix

Use valid full/tail ownership. Do not shift a writable tail backward without proving legal reads and unique plain-store ownership; backward-aligned reads or correctly masked owned stores may be valid. Compile single-tile, multi-tile, exactly divisible and tail1 shapes, not only one small smoke.

If a conditional copy extent generates invalid C++, for example a local declaration inside `copy_gm_to_ub(..., int32_t condval; ...)`, inspect the generated argument expression and try explicit full/tail branches supported by that backend. Compile both divisible and tail geometries. An overlapping output window is not an acceptable repair for a frontend limitation.

When possible, keep one shared compute body between input and output tail branches. Check actual generated code after doing so; the parser may lower seemingly equivalent syntax differently.

## 4. Inspect parser semantics, not only type annotations

If tensor annotations reach TVMScript as strings and the installed frontend cannot parse them, test evaluated annotations without `from __future__ import annotations`. Verify real compilation. This is a targeted parser diagnosis, not a universal prohibition on that Python feature.

If `T.alloc_var` binding produces a BufferLoad rather than a Buffer, indexing that bound name again can fail with a Buffer/BufferLoad mismatch. Inspect the parsed IR and the installed frontend's supported assignment form. Passing the underlying Var and a BufferLoad may also select different scalar-printing paths; validate the generated value instead of guessing from Python syntax.

Do not canonize an internal escape such as `.buffer.data` as a portable public API. Inspect parser→IR→codegen for the installed release, then verify the value on the device. Compiling a scalar expression proves neither its value nor its execution core.

## 5. Check scalar attributes bit by bit

A scalar-literal counterexample is the FP32 value `0x3f7fffff`: printing it as decimal `9.999999e-01f` rounds on recompilation to `0x3f7ffffe`, losing one ULP before arithmetic. Check the backend's actual formatting and device bits. One ULP can flip a strict predicate near its boundary.

Include the full attribute round trip in numerical testing: Python value → specialization key/literal or ABI → generated constant/parameter → device value. Test near-one, cancellation, equality and adjacent decision values. Exact intermediate arithmetic cannot compensate for an incorrectly transmitted attribute.

A supported runtime FP32 scalar can preserve a previously quantized FP32 value through the adapter's declared ABI. Supported exact hexadecimal literals or bitcasts are other possibilities; verify their actual generated and device representation. Do not use epsilon or change the input domain to conceal a transmission error.

## 6. AIC and AIV do not share local scalar registers

In mixed scheduling, a threshold GM read can execute on AIC while vector Adds consume an AIV-local scalar still at its default value. That is an ownership/lowering hypothesis to test by comparing generated guards and the scalar's producer and consumer, rather than assuming a numerical formula is wrong.

Inspect AIC/AIV guards, register/UB ownership, core mapping and the scope of each read/use. A cross-core wait does not copy a local scalar variable. Do not add meaningless synchronization to an ownership error.

If the installed backend supports explicit vector ownership, a scope such as `T.Scope("V")` may make the intended producer/consumer placement explicit. Inspect supported pass controls before experimenting with `TL_ASCEND_AUTO_CV_COMBINE`; never disable scheduling or synchronization globally as a generic fix. Any manual schedule needs complete dependencies, real precision/freshness checks and diagnostics.

Exporting MIX code to a pure-AIV entry requires reproving core-ID/subblock mapping and BlockDim. Removing guards mechanically can duplicate or omit work.

## 7. Compiler-managed mask state is conditional analysis

The reviewed upstream implementation tracks vector mode and mask payload, reuses a proven state and invalidates/merges it at uncertain calls or control flow. Read the [pinned mask design](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/docs/ascend/compiler_managed_vector_mask.md) before treating it as a model.

Transfer the idea of whole-path state analysis, not “remove every ResetMask.” Verify current helper side effects, casts, count/repeat behavior and unsupported `isSetMask` parameters. Source-level mask deduplication can generate exactly the same device code as the baseline.

Gather interfaces are not interchangeable: the reviewed tile gather uses byte-offset indices, which is a different contract from GatherMask. PTO and Ascend C routes also have different restrictions. Select the actual backend before interpreting its API contracts.

## 8. Test all three cache lifecycles

Check independently:

1. First compile and first execution.
2. Repeated calls with changed shapes/attributes/data in one process.
3. A new process reloading the persistent cache.

If first compilation and in-process reuse succeed but persistent-cache reload fails symbolic-shape binding, isolate a fresh private cache and compare all three lifecycles. A fresh cache can bypass a broken entry; it does not repair or validate the cross-process reload route. Preserve the failing configuration and backend version.

Record cache key assumptions, source/backend/configuration/target and instrumentation separation. AOT can avoid that particular Cython layer; it still requires its own full integration verification.

## 9. Set worker cache before the first import

If `TILELANG_CACHE_DIR` is captured at import and KernelCache has singleton state, changing `os.environ` per job in a reused worker will not switch the actual cache. Set the cache before import and read back the active module/instance paths; otherwise reported artifact provenance may be wrong.

For bounded parallel export:

- Choose worker count from the [actual server resource budget](workflow.md#resource-utilization-by-phase) and independent export jobs; verify actual concurrency rather than using a fixed count.
- Use an appropriate fresh-process model; do not fork a parent with initialized device state without backend support.
- Set each worker's unique cache before the first backend import and keep it fixed for that worker.
- Read back module/instance cache directories and assert agreement with the manifest.
- Write each job to an independent output; map results by explicit configuration keys, not completion order.
- On failure stop new dispatch, wait for started children and retain partial sources/failure records; do not manufacture a complete success manifest.
- A genuinely loaded temporary library can live outside the persistent cache. Record the real path/hash rather than forcing an assumed location.

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
- Preserve the full device/inline declaration contract. For example, a macro expanding to `__forceinline__ [aicore]` must retain both properties; verify the definition at the selected source revision.
- Recompile and compare allocated/relocation sections after the change.

A helper-declaration correction can change the API-library hash while leaving device allocated/relocation content identical. Compare both levels before claiming a kernel improvement. Do not copy an entire external framework when a small proven closure or the original dependency is sufficient.

## 12. Static UB rewriting must reject unknown input

Removing TPipe/TBuf can be considered only after establishing all relevant allocator/helper/lifetime uses. A safe narrow transformer accepts known constant buffer declarations, one receiver, exactly understood InitBuffer/Destroy order and constant legal offsets. Reject unknown tails, receivers, duplicate initialization, dynamic offsets, overlap, misalignment and overflow.

Maintain byte offsets versus element counts, API scratch reservations, actual maximum required bytes and host guard. Verify generated function body and complete function hashes separately by reading back the written output. CPU transformation checks do not prove device lifetime/safety or SDK independence.

Derive UB capacity, host guards, conversion extents and specialization keys for the current kernel; no fixed counts transfer automatically. Fresh build, real entry precision, instrumentation and performance remain necessary for each transformed candidate.

## 13. Evaluate the entire execution path

Structural AOT changes can shrink device text without improving the measured full call. Source size, DSL choice and high-quality reference kernels do not establish hardware saturation or a speedup.

Inspect fixed setup, dynamic dispatch, TPipe/helper work, field extraction, padded conversions, masks, synchronization, launch geometry and actual device artifacts. Benchmark the same framework boundary and output metadata. Keep first-JIT, steady-state call, disk reload, export throughput and device latency as distinct measurements.

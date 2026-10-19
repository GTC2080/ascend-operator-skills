# Build, package and runtime identity

## Identity chain

Track this complete chain for each candidate and build mode:

```text
source + configuration + compiler/SDK/target
  → generated code + compile/link commands
  → fresh host tiling library + device objects/config
  → staged vendor host/kernel resources
  → API library embedded resources
  → runner's resolved libraries + runtime OPP route
  → actual input metadata and target profiler tasks
```

A same-named folder, successful exit or modified `libcust_opapi.so` is not enough. An early incremental build in the case study contained new fresh resources and stale registry payloads simultaneously; its results could not be assigned to the claimed source.

## Fresh build procedure

1. Freeze a manifest of all source/configuration files, including required framework files and any generated helper. `scripts/source_manifest.py` can create/verify a source-only snapshot outside that source root.
2. Select a new, initially nonexistent/empty build directory. Do not empty someone else's build to make it “fresh.” Record normal versus diagnostic mode, architecture, compiler options, environment and build command.
3. Run the project build and inspect complete compilation/linkage, not just syntax checks. Store actual generated commands and artifact hashes.
4. Enumerate expected resources and packaging branches from this generated template. Compare files, sizes and hashes across fresh, staged and embedded forms.
5. Compare fresh host tiling with its staged vendor library as well. A kernel OPP tree without its tiling function can fail before device execution.
6. Bind the runner/helper identities and intended runtime environment. Then validate actual calls.

In one AOT integration failure, `GetWorkspaceSize` returned561002 and the runtime said `Do not find tiling func`. Fresh kernel resources existed; the vendor host tiling library had not been staged. The studied template used `op_tiling/lib/linux/aarch64/libcust_opmaster_rt2.0.so`. That exact path is a case-specific clue, not a default for every SDK.

## Optional embedded-payload audit

The bundled helper is read-only and uses Python standard library. It supports ELF64 little-endian symbol-table resources and this template layout:

```text
build/libcust_opapi.so
build/op_kernel/ascendc_kernels/binary/...
build/tmp/vendors/<vendor>/op_impl/ai_core/tbe/kernel/...
```

Run from the skill root after selecting the real build path:

```bash
python3 scripts/verify_embedded_kernel.py /path/to/build --require-kernel-routes direct registry
```

It compares fresh `.o`/`.json` files with staged files and `_binary_*` symbols embedded in the API library. Configuration resources use the registry route in this template. Required missing routes fail. Change route expectations only after inspecting the project's actual packaging mechanism.

An unsupported ELF/layout is a limitation or failure, never a passed check. This helper does not inspect the host tiling library, source provenance, dynamic runtime dispatch or memory correctness; perform those separate checks. A stripped library or another backend may need its own native audit.

## Resolved runtime binding

Run A and B in controlled independent processes when same-named registration or dynamic libraries could collide. Set each arm's intended OPP/library environment. Inspect resolved paths and hashes, including dynamic-loader search behavior and RPATH/RUNPATH. Setting `LD_LIBRARY_PATH` does not prove that it wins.

Otherwise, compatible candidates may follow the [resident-worker policy](workflow.md#reuse-a-resident-npu-worker-for-compatible-validation). Independent processes still share the task's host budget and device ownership rules; do not launch a replacement while a previous job or failed runtime remains active. Process separation does not protect a shared mutable package/OPP directory, and an idle resident context can still affect a new measurement's resource state.

If a frozen runner cannot rebind because of its linkage, link another runner from exactly the same frozen source and flags against B, then verify again. Do not change runner behavior while fixing linkage.

Report the evidence level precisely:

- Environment configuration: intended route only.
- Loader-resolution preflight such as `ldd`: resolved startup dependencies under that environment, not every later `dlopen` or actual process mapping.
- Runtime diagnostic/mapping: stronger observation of the loaded path when available.
- Device/task or bounded dispatch tracing: observation of executed target where supported.

The case's final reports contain loader preflight and bound-library SHA, not process mapping sampling. Do not relabel that evidence as an observed runtime map. Avoid executing loader diagnostics on arbitrary untrusted binaries; inspect provenance and use static project-native alternatives where appropriate.

## Device code comparisons

For wrapper/control/mask changes, compare real device objects before expensive NPU measurement. Record `.text`, constants, allocated sections, relocations and relevant symbols. Library hash changes may reflect host metadata, paths or build packaging rather than device instructions.

If device allocated/relocation sections, host tiling, constants and launch behavior are unchanged, do not label a tiny timing change a new kernel optimization. If only `.text` matches, investigate other changed sections/host geometry before concluding equivalence.

Smaller text is a useful observation, not proof of instruction-cache causality. Same text size does not mean identical bytes. LLVM IR is not machine ISA; do not present `-emit-llvm` output as disassembly when the compiler lacks a usable assembly route.

## Framework and runner integration

Verify generated API parameter order, optional pointers, workspace/executor ownership and return status before launch. Framework registration and inference metadata form a separate caller contract: prove the prototype/input/attribute mappings before changing getters, and do not apply runtime positive-dimension rules to a framework's unknown or shape-range lower-bound descriptors. Keep actual launch validation strict; the [eigh GE example](eigh-numerics-and-memory.md#6-ge-shape-inference-is-a-distinct-caller-contract) records both layers. A C++ syntax-only check does not prove final linkage: the HALF-aware runner needed the SDK's `libnnopbase` dependency before it could execute.

Separate actual input storage bytes from coordinate type assumptions. For a real HALF threshold check, verify2-byte allocation/H2D, `ACL_FLOAT16` metadata, quantized independent reference and a runner completion marker. Keep default FLOAT checks separately identified.

Record the exact allocation/handle/executor reuse policy. Reusing workspace capacity does not imply reusing an executor. In the studied native runner, each launch prepared a new executor; its same-address tests did not prove a reusable-executor optimization.

Changing a test adapter can introduce host errors before the device is called. An imported profiler helper relied on a `torch` global initialized only under `__main__`; all 130 tests first failed in the host adapter. Classify that layer correctly, repair the adapter, and then perform real device validation. Do not “fix” output expectations to compensate.

## Normal and instrumented builds

Use separate immutable normal and diagnostic directories and caches. Bind both to their source/configuration, but allow their device bytes to differ. Instrumentation metadata and actual tool execution must be checked on the diagnostic build; performance belongs to the normal build.

If build paths alone change diagnostic device bytes, retain the identities and report that cause is unknown. Do not automatically attribute it to nondeterminism or inherit an earlier diagnostic pass. Final combination or ABI changes require fresh evidence, even when their components previously passed.

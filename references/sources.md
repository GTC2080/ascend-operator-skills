# Public sources and version scope

This package contains original engineering instructions and self-contained counterexamples. The public sources below explain API contracts and reusable implementation patterns; they do not certify a new deployment or measured speedup. External libraries and examples retain their own licenses. Recheck installed releases before applying API or compatibility details.

## Portable skill format

- [Agent Skills specification](https://agentskills.io/specification): SKILL.md metadata, relative resources and progressive disclosure.
- [Client integration guide](https://agentskills.io/integrate-skills): discovery/load mechanisms and cross-client directory conventions. It does not guarantee every client implements native skills.

## TileLang Ascend

Reviewed public source snapshot: `1d5daf0385156cbe0c499a16c10935c5190642a4`. Match the installed wheel/backend to its own source rather than assuming it matches this snapshot.

- [README and version requirements](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/README.md).
- [Official release assets](https://github.com/tile-ai/tilelang-ascend/releases): select a wheel for the actual Python ABI, CPU architecture and CANN/backend; release tags and wheel versions can differ.
- [Wheel build script](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/build_wheel_ascend.sh), [source build script](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/install_ascend.sh), and [source environment](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/set_env.sh): commands and side effects used in the installation guide; reread at the selected ref.
- [Official vector-add smoke](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/examples/elementwise/elementwise_add.py) and [cache inspection API](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/tilelang/cache/__init__.py): small-device verification and private-cache checks.
- [TorchNPU supported versions and installation](https://github.com/Ascend/pytorch): match framework, adapter and CANN instead of upgrading them independently.
- [Programming guide](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/docs/TileLang-Ascend%20Programming%20Guide.md): source inspection and execution concepts.
- [Compiler-managed vector masks](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/docs/ascend/compiler_managed_vector_mask.md).
- [Ascend code generator](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/src/target/codegen_ascend.cc).
- [Tile gather API](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/docs/api_docs/T.tile.gather.md): byte-index and backend restrictions.
- [Elementwise pipeline example](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/examples/elementwise/elementwise_add_pipeline.py): stage organization, not proof for unrelated tails/rounding.

Parser/cache/layout/scalar failure recipes are conditional diagnostics. Inspect the generated code and reproduce the symptom on the installed backend before attributing a defect to it.

Source review and installation instructions are distinct from an actual server installation and NPU validation.

## DeepGEMM-Ascend

Reviewed snapshot: `3a35326271b069b8b5bf1a754435acd6cc91575b`.

- [README](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/README.md): supported platform/toolchain and library scope.
- [Tile pointer/layout descriptor](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/tile_ptr.hpp).
- [Copy and MAD wrappers](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/copy.hpp).
- [Pipeline synchronization](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/sync.hpp).
- [Configuration heuristics](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/csrc/jit_kernels/heuristics.hpp): library-calibrated costs, not910B constants.
- [BF16 kernel](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/bf16_gemm.hpp).

A pinned implementation is a source of API and dataflow hypotheses. It does not validate an adaptation on another chip; distinguish source review, compilation, initialized device correctness and performance.

## TileKernels

Reviewed snapshot: `c1cf914a82e6901c679445f872051ce44ac2cc63`.

- [README](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/README.md): separate NVIDIA/Ascend requirements.
- [Host cast dispatch](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/quant/cast_kernel.py).
- [Ascend cast implementation](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/quant/cast_asc.py).
- [Ascend Engram hash](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/engram/engram_hash_asc.py).
- [Ascend RoPE](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/transform/rope_asc.py).
- [Resource configuration](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/config.py).
- [Benchmark utilities](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/testing/pytest/benchmark.py).

The linked public source organization informs dispatch, specialization, layout and pipeline hypotheses. It supplies no measured speedup for a different operator or target.

### 910B adaptation procedure

The [910B guide](910b-porting.md) derives a staged engineering procedure from the pinned library sources. Read the READMEs, DeepGEMM copy/MAD wrapper, TileKernels cast dispatch/kernel/configuration and [per-token cast tests](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tests/quant/test_per_token_cast.py). Transitive imports and import-time low-bit symbols are part of compatibility even when the requested kernel uses another path. The guide itself is not a package installation, initialized MAD execution, TileKernels device run or performance result.

## Ascend API and diagnostics

### CANNBot knowledge provider

Reviewed on 2026-10-18 at `ef37bed1bbec2782cb07d2b086e80361fc0ea3c0`, obtained through the public Git transport of [CANN's repository](https://gitcode.com/cann/cannbot-knowledge). The [integration guide](cannbot-knowledge.md) is an optional consumer adapter, not a bundled copy or an installation claim.

- [README](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/README.md) and [LICENSE](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/LICENSE): repository roles and CANN Open Software License Agreement 2.0; upstream material is not relicensed under this package's MIT terms.
- [Knowledge Query](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/knowledge-query/SKILL.md), [CLI](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/knowledge-query/references/cli.md) and [parser](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/knowledge-query/scripts/knowledge_query.py): index readiness, filters, matching and result/error semantics.
- [Ascend C API consumer](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/ascendc-api-knowledge-query/SKILL.md), [resource evidence](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/ascendc-api-knowledge-query/references/evidence-check.md) and [platform identification](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/knowledge-query/references/platform-identification.md): full-card reading, source/SDK component roots and target mapping.
- [TileLang index](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/knowledge/ops/tilelang/index.md), the pinned Git tree and [DataCopyPad card](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/knowledge/ops/ascendc/apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md): observed coverage and an example of platform-specific overload restrictions. Only the card's metadata and relevant declaration/mode sections were reviewed here; no new SDK or device support is inferred.
- [Installation and usage](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/docs/installation_and_usage.md) and [operator-development recipe](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/recipes/operator_development.md): provider setup effects and its relationship to actual engineering validation.

The query interface and selected source material were inspected; no upstream installer, index build, native lookup, SDK compilation or NPU experiment was run for this integration. External knowledge/tool execution remains separate from this package's offline checks.

### API and diagnostic references

- [CANN9.0 HF32 mode](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/900/API/ascendcopapi/atlasascendc_api_07_0258.html): numerical mode distinction; use installed-version signature.
- [CANN9.0 Select](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/900/API/ascendcopapi/atlasascendc_api_07_0070.html): public dtype/mask/scratch contract, independently check installed helper.
- [Ascend mssanitizer guide](https://github.com/Ascend/mssanitizer/blob/master/docs/zh/user_guide/mssanitizer_user_guide.md): tool execution and limitations. Master is evolving; pin the actual tool/release used in a new project.
- [Ascend profiler data guide](https://github.com/Ascend/msopprof/blob/master/docs/en/user_guide/msopprof_performance_data.md): field meaning; exported fields remain collector/version-specific.
- [Official UB bank-conflict example](https://gitcode.com/cann/asc-devkit/blob/master/examples/01_simd_cpp_api/05_best_practices/04_memory_access/bank_conflict_ub/README.md): layout hypothesis source, not measured evidence of this operator's dominant bottleneck.

### MindStudio 26.0.0 documentation

Reviewed on 2026-10-19 at `e5538cc1437535f503ae0d61e6c7624a088ff36c` in [mindstudio-docs/26.0.0](https://github.com/mindstudio-docs/26.0.0/tree/e5538cc1437535f503ae0d61e6c7624a088ff36c). The [tool workflow](mindstudio-tools.md) is an original, attributed engineering synthesis. Selected manuals and relevant sections were inspected; this is not a claim to have reviewed every tool or tested the documented features on 910B.

- [msOT toolchain overview](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msot/README.md) and the pinned Git tree: tool roles and documentation coverage. The root index names tools whose documentation directories are absent in this snapshot; those entries do not supply usable command or compatibility evidence.
- [msKPP quick start](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mskpp/docs/zh/quick_start/mskpp_quick_start.md) and [installation](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mskpp/docs/zh/install_guide/mskpp_install_guide.md): modeling-library role, chip selection, generated reports and existing CANN integration.
- [msOpGen quick start](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopgen/docs/zh/quick_start/msopgen_quick_start.md): descriptors, target selection and new-project scaffolding.
- [msDebug quick start](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msdebug/docs/zh/quick_start/msdebug_quick_start.md): debug build/symbol binding, host switch and container limitations. The tutorial's privileged setup is not authorization to change a development host.
- [msSanitizer user guide](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mssanitizer/docs/zh/user_guide/mssanitizer_user_guide.md), [compiler/link/package configuration](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mssanitizer/docs/zh/user_guide/compile_option_config.md) and [installation](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/mssanitizer/docs/zh/install_guide/mssanitizer_install_guide.md): limited versus instrumented coverage, target/instruction restrictions, log overwrite and tool modes.
- [msOpProf board mode](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_user_guide.md), [calling routes](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_usage.md), [field definitions](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_performance_data.md) and [simulator mode](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/user_guide/msopprof_simulator_user_guide.md): CLI shapes, kernel selection, replay, metric/caller restrictions and separate evidence types.
- [msOpTuner installation and scope](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msoptuner/docs/zh/install_guide/msoptuner_install_guide.md): CATLASS and Atlas A2 context. Moving-dependency downloads, global credential storage and unrestricted build parallelism in that example are not adopted by this workflow.
- [Documentation license](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/LICENSE), [profiler license notice](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msopprof/docs/zh/legal/license_notice.md) and [debugger license notice](https://github.com/mindstudio-docs/26.0.0/blob/e5538cc1437535f503ae0d61e6c7624a088ff36c/msdebug/docs/zh/legal/license_notice.md): the reviewed documentation is CC BY 4.0; product-code terms are component-specific. Attribution belongs to the MindStudio documentation contributors. The local workflow condenses/adapts the linked material and does not relicense external content under MIT.

No upstream installer, generator, model, debugger, sanitizer, profiler or tuning search was executed for this documentation integration. No SDK build, device coverage or new speedup is claimed.

## Server resource planning

- [CMake build parallelism](https://cmake.org/cmake/help/latest/manual/cmake.1.html#cmdoption-cmake-build-parallel): explicit job limits and the default-only role of `CMAKE_BUILD_PARALLEL_LEVEL`; use the installed version's supported options.
- [Python CPU affinity](https://docs.python.org/3/library/os.html#os.sched_getaffinity) and [Linux cgroup v2 CPU limits](https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu-interface-files): allowed logical CPUs and quota are distinct inputs to a task budget.
- [Linux CPU topology discovery](https://man7.org/linux/man-pages/man1/lscpu.1.html) and [cgroup v2 memory limits](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files): visible topology and host memory are distinct from effective container allocations. Query the actual execution environment; unavailable fields remain unknown. These sources were rechecked for the hardware-discovery procedure on 2026-10-17; the documentation update does not represent a new server inventory or throughput experiment.
- [Reviewed TileLang setup build paths](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/setup.py) and [source build launcher](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/install_ascend.sh): version-scoped fractional CPU job limits, not a recommendation to keep every server half idle.
- [PyTorch process-start guidance](https://docs.pytorch.org/docs/2.14/notes/multiprocessing.html#poison-fork-in-multiprocessing): accelerator initialization before an unsafe fork can poison child processes. This general guidance does not establish support for every start method on every TorchNPU release; check the installed backend. Rechecked on 2026-10-17 for the resident-worker policy. The policy adds no new worker implementation, device execution or measured startup-saving claim.
- [Python process lifecycle](https://docs.python.org/3/library/multiprocessing.html#process-and-exceptions): waiting, exit status and termination requests have distinct semantics; terminating a process does not terminate its descendants. Rechecked on 2026-10-17 for worker retirement and capture handoff. Process-exit evidence does not itself prove accelerator work stopped; the installed backend needs its own completion/cleanup evidence.

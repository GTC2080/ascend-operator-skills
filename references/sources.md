# Sources and provenance

Prepared 2026-10-16. This package contains original engineering instructions and condensed observations; it does not bundle the external libraries or their performance tables. External examples retain their own licenses. Recheck installed releases before applying any API or compatibility detail.

## Portable skill format

- [Agent Skills specification](https://agentskills.io/specification): SKILL.md metadata, relative resources and progressive disclosure.
- [Client integration guide](https://agentskills.io/integrate-skills): discovery/load mechanisms and cross-client directory conventions. It does not guarantee every client implements native skills.

## TileLang Ascend

Reviewed source snapshot: `1d5daf0385156cbe0c499a16c10935c5190642a4`. This is distinct from the historical wheel used for device experiments.

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

The parser/cache/layout/scalar failures in this package were independently observed with the older0.1.1.10 wheel. They are not claims that the current upstream has those defects.

Installation sources and release metadata were rechecked on 2026-10-17. The new guide was checked offline; it does not record a new server installation or NPU run.

## DeepGEMM-Ascend

Reviewed snapshot: `3a35326271b069b8b5bf1a754435acd6cc91575b`.

- [README](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/README.md): supported platform/toolchain and library scope.
- [Tile pointer/layout descriptor](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/tile_ptr.hpp).
- [Copy and MAD wrappers](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/copy.hpp).
- [Pipeline synchronization](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/ascend/sync.hpp).
- [Configuration heuristics](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/csrc/jit_kernels/heuristics.hpp): library-calibrated costs, not910B constants.
- [BF16 kernel](https://github.com/deepseek-ai/DeepGEMM-Ascend/blob/3a35326271b069b8b5bf1a754435acd6cc91575b/deep_gemm/include/deep_gemm/bf16_gemm.hpp).

The minimal ordinary MAD compile probe and raw C arithmetic tests are local case evidence. The upstream library did not validate those adaptations on this910B target for us.

## TileKernels

Reviewed snapshot: `c1cf914a82e6901c679445f872051ce44ac2cc63`.

- [README](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/README.md): separate NVIDIA/Ascend requirements.
- [Host cast dispatch](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/quant/cast_kernel.py).
- [Ascend cast implementation](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/quant/cast_asc.py).
- [Ascend Engram hash](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/engram/engram_hash_asc.py).
- [Ascend RoPE](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/transform/rope_asc.py).
- [Resource configuration](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/config.py).
- [Benchmark utilities](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tile_kernels/testing/pytest/benchmark.py).

These implementations were source-reviewed, not installed or executed in the case project. Their source organization informed hypotheses rather than supplying measured speedups for our operator.

### 910B adaptation procedure

The [910B guide](910b-porting.md) is an engineering procedure derived from the pinned library sources and the case's limited probes. On 2026-10-17, their READMEs, the DeepGEMM copy/MAD wrapper, TileKernels cast dispatch/kernel/configuration and [per-token cast tests](https://github.com/deepseek-ai/TileKernels/blob/c1cf914a82e6901c679445f872051ce44ac2cc63/tests/quant/test_per_token_cast.py) were rechecked. In particular, transitive imports and import-time low-bit symbols are part of the compatibility surface, even when the requested kernel uses another path. The procedure was reviewed offline; no new package installation, initialized MAD execution, TileKernels device run or performance result is claimed.

## Ascend API and diagnostics

- [CANN9.0 HF32 mode](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/900/API/ascendcopapi/atlasascendc_api_07_0258.html): numerical mode distinction; use installed-version signature.
- [CANN9.0 Select](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/900/API/ascendcopapi/atlasascendc_api_07_0070.html): public dtype/mask/scratch contract, independently check installed helper.
- [Ascend mssanitizer guide](https://github.com/Ascend/mssanitizer/blob/master/docs/zh/user_guide/mssanitizer_user_guide.md): tool execution and limitations. Master is evolving; pin the actual tool/release used in a new project.
- [Ascend profiler data guide](https://github.com/Ascend/msopprof/blob/master/docs/en/user_guide/msopprof_performance_data.md): field meaning; exported fields remain collector/version-specific.
- [Official UB bank-conflict example](https://gitcode.com/cann/asc-devkit/blob/master/examples/01_simd_cpp_api/05_best_practices/04_memory_access/bank_conflict_ub/README.md): layout hypothesis source, not measured evidence of this operator's dominant bottleneck.

## Server resource planning

- [CMake build parallelism](https://cmake.org/cmake/help/latest/manual/cmake.1.html#cmdoption-cmake-build-parallel): explicit job limits and the default-only role of `CMAKE_BUILD_PARALLEL_LEVEL`; use the installed version's supported options.
- [Python CPU affinity](https://docs.python.org/3/library/os.html#os.sched_getaffinity) and [Linux cgroup v2 CPU limits](https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu-interface-files): allowed logical CPUs and quota are distinct inputs to a task budget.
- [Reviewed TileLang setup build paths](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/setup.py) and [source build launcher](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/install_ascend.sh): version-scoped fractional CPU job limits, not a recommendation to keep every server half idle.

## Local case evidence map

Raw project artifacts are not bundled: they may contain machine-specific logs, large binaries or unrelated operational information. The skill works without them. Case observations were checked against the following original relative records; their selected content hashes are recorded in [provenance.json](provenance.json). The hashes identify the inspected snapshot, not a signature or independently reproduced experiment.

| Topic | Original evidence, relative to the case project |
| --- | --- |
| Independent oracle and rounding counterexamples | `code/test/verify_npu.py`, `code/test/verify_batch.py` |
| Early precision/memory/packaging conclusions | `results/round2/REVIEW.md`, `results/round3/REVIEW.md` |
| Mask/strided/HALF Select failures | R4 archive members `round4/status.json`, `round4/validation/half-select-sdk-review.json`, `round4/validation/r4_small-mask-debug-candidate-v2.json` |
| Same-code protocol controls | R4 archive `round4/validation/process-boundary-control-summary.json`, `profiler-metric-control-summary.json`, `native-g-control-float-v2-summary.json`, `native-g-control-float-v3-summary.json` under the same validation prefix |
| Raw timing audit and negative controls | R4 archive `round4/run_native_abba_v3.py`, `round4/validation/timing-auditor-negative-controls.json` |
| DSL layout/dynamic/cache review | R5 archive `validation/output-dma-review.md`, `validation/dynamic_v2-review.md` |
| DSL scalar ownership/ABI | R5 archive `candidates/tilelang_dynamic_v7c_scalar_threshold/operator.py`, `aot/README.md`, `aot/prepare_payload_v3.py` |
| Export worker and static UB transformation | R5 archive `validation/export_generic_geometry_v2.py`, `aot/prepare_static_ub_payload_v1.py` |
| AOT generated device identity and later real precision/freshness | R5 archive `validation/aot_v1-v2-device-sections.json`, `validation/dynamic_v7c_aot_export_v1/manifest.json`, `validation/cloud-selected-v7c-v1/round5/validation/tilelang_aot_v7c_full_v1/manifest.json`, `validation/cloud-selected-v7c-v1/round5/validation/tilelang_aot_v7c_same_address_v1.json` |
| MAD/library analysis | R5 archive `notes/deepgemm-mad-910b-review.md`, `notes/deepgemm-ascend-review.md`, `notes/tilekernels-910b-review.md` |
| Native binding, capture and parallel export | R5 archive `validation/profile_native_variant_v10.py` |
| Final precision/freshness/diagnostics/latency | `results/round5/final/precision.json`, `same-address.json`, `coordinate-updates.json`, `sanitizer-summary.json`, `native-all12.json`, `candidate-summary.json` in that final directory |

The casebook excludes account, remote submission, instance operation and application-session history. Performance numbers are descriptive local observations, with uncertainty retained. Reproduce relevant checks against the new project's own implementation and target before adopting an optimization.

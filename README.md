# Ascend Operator Skills

[![Validate](https://github.com/GTC2080/ascend-operator-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/GTC2080/ascend-operator-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A portable [Agent Skills](https://agentskills.io/specification) package for designing, implementing, reviewing and tuning Huawei Ascend operators with **Ascend C and TileLang Ascend**.

It distills five rounds of real operator development into a concise skill entry, twelve detailed reference manuals, 56 version-scoped case studies, and two dependency-free Python audit tools. It includes practical lessons from **DeepGEMM-Ascend** and **TileKernels**, with explicit boundaries between inspected source, compiled probes, device validation and measured performance.

**中文：** 面向全球开发者的昇腾算子开发技能，整理真实开发中关于数值语义、UB/DMA、mask、同步、TileLang生成代码、JIT/AOT、内存检测与性能实验的经验。只有算子开发内容，附[中文导入说明](INSTALL.md#中文使用说明)。

## Start here

- [SKILL.md](SKILL.md) — the agent entrypoint and reference routing.
- [INSTALL.md](INSTALL.md) — native skill import and Markdown fallback.
- [Casebook](references/casebook.md) — 56 successes, failures and unresolved questions.
- [Validation](VALIDATION.md) — executed offline checks and their limits.
- [Sources](references/sources.md) — version-pinned upstream references and evidence provenance.
- [Releases](https://github.com/GTC2080/ascend-operator-skills/releases) — importable ZIP and SHA-256 checksum.

## Import

Download a release ZIP and preserve the `ascend-operator-engineering/` directory, including its resources. Import the complete folder using your harness's supported skill mechanism.

For a client that scans project `.agents/skills/`, one option is:

```bash
git clone https://github.com/GTC2080/ascend-operator-skills.git .agents/skills/ascend-operator-engineering
```

Reload the client's skill catalog as required, then ask it to use `ascend-operator-engineering`. Clients without native skill support can load the entry and relevant Markdown references as task instructions. Discovery and invocation syntax are client-specific; universal native harness compatibility has not been tested.

Example request:

> Use ascend-operator-engineering to review this kernel's contract, generated code, memory ownership and synchronization, then propose a minimal validation and paired-performance plan. Do not run device work without the task's authorization.

## What it covers

| Area | Included guidance |
| --- | --- |
| Contract and architecture | Storage/compute dtype, exact rounding, shape/layout/alias validation, tiling and checked bounds |
| Backend selection | Stage- and workload-based TileLang/Ascend C preferences, deployment feasibility and evidence for switching |
| Server utilization | Actual CPU/quota/memory budgets, overlapping CPU/NPU-ready queues, host orchestration headroom, nested-thread control and isolated latency windows |
| Ascend C | UB capacity and scratch, DMA units, masks, producer/consumer dependencies and final writeback |
| Build and integration | Fresh/staged/embedded identities, host tiling, loaded libraries, ACLNN and executor policy |
| Correctness and diagnostics | Independent oracle, boundary/negative cases, same-address updates, actual mssanitizer activation |
| Performance | Same-code controls, raw-row audits, paired/reversed experiments, noise, contention and scoped gains |
| TileLang Ascend | [Server installation and verification](references/tilelang-installation.md), frontend/codegen failures, scalar bits, AIC/AIV scope, caches, export workers and AOT adaptation |
| Library reuse | DeepGEMM MAD/descriptors/pipelines and TileKernels specialization, with a [step-by-step 910B adaptation procedure](references/910b-porting.md), chip/version constraints and acceptance gates |

Historical device observations concern **910B2 / CANN 9.0.0** and an older TileLang Ascend wheel. They are debugging evidence, not permanent API contracts, current-version bug claims or performance guarantees. Recheck the target SDK and pinned sources before applying them.

## Offline tools and tests

Python **3.9+**, standard library only; no NPU, SDK, account or network service is required for these checks:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/source_manifest.py create /path/to/operator-source /path/to/new-manifest.json
python3 scripts/source_manifest.py verify /path/to/operator-source /path/to/new-manifest.json
python3 scripts/verify_embedded_kernel.py /path/to/build --require-kernel-routes direct registry
```

The embedded-resource checker supports one documented ELF64 little-endian Ascend C layout. Passing it proves packaging consistency only; it does not establish runtime selection, precision, memory safety or speed. See [the identity guide](references/build-identity.md).

CI runs the offline unit tests and checks the distributed manifest and Markdown links. It does not run historical NPU experiments or install/test every harness.

## Contributing

Provide a minimal reproduction, exact chip/toolchain/backend versions and clearly separated observations versus hypotheses. Add a meaningful regression check for tool changes. Keep case-specific constants version-scoped and unresolved failures visible. Update `MANIFEST.json` to match changed distributed files; do not rewrite historical validation records as if a new experiment had occurred.

Never include credentials, private machine logs, personal paths or unrelated operational workflows. Preserve upstream licenses when actually reusing code; this repository links to external implementations rather than bundling them.

## License

[MIT](LICENSE). External libraries and documentation retain their own licenses. This project is an independent engineering guide, not an official release of Huawei, TileLang or DeepSeek.

# Portable import / 可移植导入

The skill uses the open [Agent Skills format](https://agentskills.io/specification): a directory named `ascend-operator-engineering` with `SKILL.md` and relative resources. It contains no required MCP server, proprietary tool name, model selection, login or network service. The instructions are English so they can be shared internationally; the agent can answer in the user's language.

## Import into a skills-aware harness

1. Extract the ZIP, preserving its top-level `ascend-operator-engineering/` directory and all resources.
2. Use the harness's supported skill-import mechanism, or place that complete directory in its configured skill search directory.
3. Where the client supports it, a project `.agents/skills/` directory is a cross-client convention. The format itself does not mandate this location; consult the client documentation. Do not assume that copying files makes a running client refresh its catalog.
4. Reload the catalog as that client requires. Ask the agent to use `ascend-operator-engineering`, then verify that it reads this package's `SKILL.md` and resolves its references. Mention/slash syntax differs by client.

These are standard-format compatibility instructions, not a claim that every proprietary harness has been tested. Discovery, tool availability, permissions and model behavior remain client-specific. See the official [integration guide](https://agentskills.io/integrate-skills).

## Harness without a native skills loader

Provide `SKILL.md` as task instructions and attach the relevant `references/` files. If it supports file access, provide the complete folder and its actual location instead. When it has no command execution, the agent can perform a document/source review and state which checks require a compiler, Python or target NPU. It must not claim execution.

## Optional offline checks

From the extracted skill directory, with Python 3.9 or later:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/source_manifest.py create /path/to/operator-source /path/to/new-manifest.json
python3 scripts/source_manifest.py verify /path/to/operator-source /path/to/new-manifest.json
```

The manifest command hashes a source tree without executing its code. Choose a source-only root; it is not a cache collector. The optional packaging audit requires this specific generated layout:

```bash
python3 scripts/verify_embedded_kernel.py /path/to/fresh-build --require-kernel-routes direct registry
```

Use the routes actually required by the template. Passing the packaging audit is not runtime, precision, sanitizer or performance validation. No SDK installation or NPU access is performed by these offline checks.

## 中文使用说明

解压后，把完整的 `ascend-operator-engineering` 文件夹导入工具支持的 skills 入口，或放到该工具配置的技能目录。不要只复制 `SKILL.md`，详细手册与脚本也要保留。支持 `.agents/skills/` 的工具可用项目级目录；不支持原生 skill 的工具可直接加载入口和相关参考文档作为任务上下文。

可以这样调用：“使用 ascend-operator-engineering，先核对算子的输入输出契约和已有工程，给出最小可验证实现，完成真实构建、精度、内存和性能证据闭环。”也可只要求离线审查、TileLang排障或性能实验设计，不需要每次跑完整流程。

经验涵盖五轮真实开发，并明确标记910B2/CANN9.0.0及旧版TileLang的适用边界。包内没有个人路径、账户、提交接口、租赁、关机或桌面操作流程。技能结构与脚本检查通过也不能保证任意客户端自动发现或未来每次正确执行。

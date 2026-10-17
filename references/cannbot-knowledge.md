# Use CANNBot knowledge as an optional evidence source

Use [CANN's cannbot-knowledge repository](https://gitcode.com/cann/cannbot-knowledge) to find relevant API contracts, operator implementations and diagnostic knowledge before making a decision that needs that evidence. Keep this skill's contract, hardware discovery, backend selection, correctness and performance workflow as the engineering framework. The provider is optional; importing this skill does not install it or make its tools a runtime dependency.

Reviewed on 2026-10-18 at commit `ef37bed1bbec2782cb07d2b086e80361fc0ea3c0`. This package links to the external tools/cards rather than redistributing them. Read the selected revision's instructions when using a different version.

## Choose the right source and establish real coverage

| Need | Upstream entry and boundary |
| --- | --- |
| Operator implementation, ACLNN versus Direct entry, failure or optimization evidence | `knowledge-query`; select the relevant task mode and existing knowledge scope/Profile |
| Ascend C API declaration, overload, parameters and related includes | `ascendc-api-knowledge-query`, which uses the same Query index; this specialized entry is not the ACLNN/operator-analysis route |
| TileLang syntax, code generation or newer-chip mechanisms | Check actual coverage first, then retain this package's [TileLang](tilelang.md), [backend selection](workflow.md#backend-selection-by-workload-and-stage) and [910B adaptation](910b-porting.md) sources where the provider has no applicable cards |

At the reviewed tree, `knowledge/ops/tilelang/` contains only its index, which states there are no reviewed cards yet. A registered category or a README capability list is not proof of technical coverage. This observation does not establish the coverage of a newer revision. Native `discover` reports indexed coverage; its separate dimension counts do not establish every platform/technology combination.

Knowledge ingestion, trace production and repository Lint serve knowledge maintenance. They are not additional mandatory stages for implementing an operator, and using a card does not authorize uploading project artifacts or contributing to the external repository.

## Prepare a compatible consumer without changing the device environment

Use an existing prepared, version-recorded full checkout and the Python environment that satisfies its requirements. The checkout root contains `knowledge/`, `.agents/skills/` and `governance/`; `knowledge/` alone is the Bundle root, not the repository root. Copying one skill directory loses dependencies and does not establish a complete installation.

If setup is needed, inspect the selected revision's [installation guide](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/docs/installation_and_usage.md) and actual installer. Setup can install Python packages, restore external documentation/source archives, prepare a SQLite index and create project client entries. Keep these effects within the authorized task/environment; do not run an installer merely because a lookup is unavailable. This documentation integration performed no provider installation or index build.

Run lookup tooling as CPU-side work outside the resident NPU worker, preserving its fixed framework/backend/cache configuration. Budget lookup, index preparation and resource restoration under the [shared resource policy](workflow.md#resource-utilization-by-phase); heavy preparation belongs outside formal latency capture. Reuse a ready provider instead of repeatedly cloning or rebuilding it.

## Query the actual target, then read the chosen evidence

1. Establish the target product from supplied deployment/build evidence or the [execution-machine inventory](workflow.md#hardware-discovery-before-resource-allocation) when device work requires it. The agent's local CPU or NPU is not automatically the target. Map the product using the provider's current Registry and [platform-identification reference](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/.agents/skills/knowledge-query/references/platform-identification.md). Preserve the mapping evidence; do not infer it from a single architecture macro, memory size or directory name. Set `CB_PLATFORM` to the confirmed registered ID, with no fixed platform default.
2. Verify index readiness with `discover`, then ask one bounded question. Use the exact identifier for literal matching; a whole natural-language sentence is a different literal string. The following commands require `CB_REPO` and `CB_PYTHON` to be the confirmed absolute checkout/interpreter paths. They use the CLI inspected at the pinned revision:

   ```bash
   : "${CB_REPO:?Set the prepared full checkout path}"
   : "${CB_PYTHON:?Set the provider Python interpreter path}"
   : "${CB_PLATFORM:?Set the confirmed registered target ID}"
   CB_QUERY="$CB_REPO/.agents/skills/knowledge-query/scripts/knowledge_query.py"
   test -f "$CB_QUERY" || exit 1
   "$CB_PYTHON" "$CB_QUERY" --knowledge-root "$CB_REPO" discover --json || exit 1
   "$CB_PYTHON" "$CB_QUERY" --knowledge-root "$CB_REPO" search \
     --query "DataCopyPad" --domain ops --technology ascendc --type apis \
     --platform "$CB_PLATFORM" --status stable --match literal -k 5 --text
   ```

   This is an API lookup example, not a claim about every DataCopyPad overload on that target. Use general Query for Operator/ACLNN analysis and existing Profile IDs such as `operators`; do not invent filters. At this revision, Query has no CANN-version filter. Repeated platform flags mean intersection, so compare platforms through separate queries when studying differences.
3. Select relevant results and read their complete frontmatter/body. Titles, rankings and snippets are discovery aids. Follow returned continuations when a reader paginates; neither the first page nor a line count proves full reading. With the matching API consumer available, one supported entry is:

   ```bash
   : "${CB_CARD:?Set the selected absolute local_path}"
   "$CB_PYTHON" "$CB_REPO/.agents/skills/ascendc-api-knowledge-query/scripts/resolve_resources.py" \
     read --card "$CB_CARD"
   ```

4. Check the actual overload, data path, dtype, units, numerical mode, alignment, workspace/scratch, synchronization and version restrictions against the operator contract. A card can list several platforms while restricting a particular mode to a newer chip; the pinned [DataCopyPad example](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/knowledge/ops/ascendc/apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md) illustrates this pattern. A top-level platform match does not validate every branch, and `stable` is not a test result.
5. Follow only links needed for the decision, resolve conflicts before using a formula or parameter, then return to the actual implementation and verification plan. A new diagnostic signal can justify another bounded lookup. Do not replace initialized device tests, sanitizer coverage or paired measurements with knowledge-card status.

## Keep source paths and version evidence distinct

| Evidence field | Correct base and check |
| --- | --- |
| Search `local_path` | Already absolute; read the selected card, not a similarly named file |
| Relative card link / leading `/` knowledge link | Current card directory / `knowledge/` Bundle root, respectively |
| Local `sources[].resource` | Full knowledge repository root; inspect the registered source and its revision |
| API `source_headers` | The actual CANN Ascend C component root used by this build; the field already includes `include/` |

Prefer the matching upstream resolver for source/header/link paths, then open the resolved file and inspect the relevant context. Resolving a path does not mean reading its contents. Do not substitute another SDK installation or a sample for a missing fixed-source file.

Bind knowledge claims to the provider commit, card identity/hash and source revision. A pinned knowledge commit does not freeze a separately restored rolling documentation archive. Record the actual source snapshot/hash and the installed component version when they matter; mark missing source/header evidence as unread. Compare the selected signature and macro branch with the current build's SDK rather than assuming a path named `latest` identifies a release. Reading a declaration also does not prove a device invocation compiled or ran.

## Distinguish missing knowledge from a failed lookup

At the reviewed CLI, exit `0` can contain zero matches; exit `2` represents input/index/configuration errors. Missing, stale or corrupt indexes are not zero-hit evidence. Stop that provider lookup and preserve the error; its consumer does not silently rebuild an index or replace a failed query with a whole-tree scan. A permission denial is not a reason to retry the same denied access through another route.

After a valid exact-name API query has zero stable matches for the confirmed target, the native workflow separately searches unlocated drafts with the same identifier, domain/technology and literal matching, `--include-unlocated --status draft`, and **no platform flag**. This is only a lead whose platform remains unverified, not evidence of support or a substitute for initially identifying the target. Keep it separate from target-specific results and audit receipts. A limit of five returned results is not an exhaustive API or caller count.

If the provider is absent or unusable, state that it supplied no verified evidence. Continue the authorized core workflow with independently available project files, installed-version SDK documentation/headers or other primary sources where those suffice; retain unresolved decisions instead of inventing card results or API availability. Provider setup is a separate action, not an implicit dependency installation.

For a small lookup, a concise source note is enough. When the project requires retrieval audit, use the matching upstream receipt/state tools and a new task-owned output path; do not overwrite an existing receipt. Record the decision, confirmed target, provider/index identity, cards actually read, source/header evidence, conflicts and the actual compile/device/diagnostic/performance state. Retrieval evidence and execution evidence remain separate.

## Licensing and integration boundary

The pinned upstream [LICENSE](https://gitcode.com/cann/cannbot-knowledge/blob/ef37bed1bbec2782cb07d2b086e80361fc0ea3c0/LICENSE) is **CANN Open Software License Agreement 2.0**, not this package's MIT license. This adapter contains original integration instructions and links; it bundles no upstream skills, knowledge cards, scripts or restored archives. Upstream material retains its own terms. Any future copying or redistribution needs its own scope/license/notice review; do not label that material MIT merely because this repository is MIT.

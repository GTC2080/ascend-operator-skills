# Validation of this skill package

Initial version 1.0.0 was validated on 2026-10-16. This document describes those skill and offline-tool checks, not a new device validation of the historical kernels. Versions 1.0.1–1.0.2 update repository branding/links and version metadata; the independent check identities below identify the original reviewed snapshot. Current distributed-file integrity is recorded in MANIFEST.json.

## Executed checks

- Skill frontmatter/name validation passed with the local skill-creator validator. Frontmatter deliberately uses a conservative subset: name, description, license and string metadata. Environment requirements are in the body so an older validator that rejects the optional compatibility field can still load it.
- Internal Markdown resource links were resolved; required resources exist. The entry loads detailed material on demand.
- Eighteen standard-library unit tests passed under Python3.9.6. They cover exact-tree manifest success, modified/missing/extra source, unsafe paths, symlinks, no overwrite, synthetic ELF parsing, stale staged/embedded resources, missing required routes, absent device objects, truncated/unsupported ELF and unsafe vendor input.
- Independent CLI exercise verified create/exact-verify exit0; changed/added/removed files exit1 with correct classification; repeated create exit2 while the original manifest remained byte-identical.
- The ELF parser read a real archived Ascend C API library with14embedded resources and matched the previously used checker's resource hashes. This was offline parsing, not device execution or full runtime-route proof.
- An independent skill exercise correctly withheld adoption for an inactive-sanitizer/one-run0.8% scenario, and separately diagnosed invalid TileLang tail codegen and AIC/AIV scalar ownership. It relied on this package without proprietary tools or original project artifacts.
- The final reviewed entry, performance reference, scripts and tests were bound to their hashes before packaging. No bytecode/cache artifacts or scratch test directories are distributed.
- A targeted scan found no personal machine paths, known private instance/session identifiers, credentials or remote-submission endpoints. This is a scoped inspection, not a formal privacy/security certification.

Independent final check identities:

| File | SHA-256 |
| --- | --- |
| SKILL.md |787c1c8581eba2949a9e20b110408dd3b3ccf6063be54abf25c69fb0157e8bc4 |
| references/performance.md |f324a9b68894431d97f313d029efc03bb3f5a5ab93ebff244d79de23b6c7d265 |
| scripts/source_manifest.py |5159616d4cf8aa82379fff56a07dc1a8efb937058160266b0542033c4c8018f1 |
| scripts/verify_embedded_kernel.py |567e5690d6fc099d1b12833df4a7f8b55ee96658af85a40aee5f51eb014832e0 |
| tests/test_source_manifest.py |df876ae25a105bc1ad38d6d8feddfee7f4664403df95171dcb91d1dedf7119f6 |
| tests/test_embedded_kernel.py |9b680931420cd8aafcb1859eda35efd32dd79d9b8fb9459a1c43ab9aadede8a7 |

## Limits

No NPU, remote server, compiler build, SDK installation, account or deployment operation was performed while creating this package. Historical performance/memory observations were transcribed from locally inspected evidence; raw machine-specific evidence is not redistributed and the observations were not independently rerun for this release.

No matrix of proprietary harness clients was installed or tested. Standard-format import and a Markdown fallback are documented; discovery, automatic activation and model behavior remain client-specific. Passing these checks cannot guarantee future agent decisions, universal compatibility or performance improvements.

`MANIFEST.json` lists all other distributed files with bytes/SHA. ZIP members are read back and checked against that manifest during packaging; the external `.zip.sha256` identifies the whole ZIP. Hashes provide integrity/provenance when compared to a trusted copy, not authentication by themselves.

## Eigh case update, 2026-10-20

The new conditional references distinguish mathematical checks, reference phase, complete NPU execution and pending external acceptance. They record numerical, workspace, generated-code, oracle and GE failure mechanisms without distributing private kernels or raw account/machine logs. Sixteen current evidence snapshots and 22 selected archive members have recorded digests; selected archived member contents were checked against their manifest without extraction or execution.

For this documentation update, the existing 18 offline audit-tool tests passed. The source and staged skill entries passed frontmatter validation; local resource files and anchors were checked. Eight independent read-only scenario exercises covered phase overgeneralization, damaged oracles, carried binaries, monitoring cancellation, GE ranges, physical tails, validator overflow and interrupted archives. The review prompted a direct archive-entry route and a clarification that current user scope takes precedence over old carryover plans. This is observed guidance validation, not a guarantee of future model behavior.

Existing first-operator diagnostic-tool guidance was preserved. Audit/runtime scripts were unchanged. No new compiler build, NPU experiment, external-evaluation query/submission or performance measurement was run for this skill update. Historical complete-call successes, unfinished sanitizer coverage and pending external results retain their original scope.

## Later Round12 refinement update, version 1.0.3

The added residual-refinement reference distinguishes a post-alignment component error from phase disagreement, explains the rejected ordinary-K and subnormal-skip variants, and records the selected pair-skew correction, exact common scaling, immutable original Q and whole-matrix fallback. It links its source-scoped normal-NPU evidence without distributing private source or outputs. Twenty-two selected file digests match the verified round-archive inventory. Historical arrays intentionally retired before archival are explicitly unavailable, even though the repair process remains documented.

The update also clarifies OBJECT-linked host tiling, actual application calls versus profiler replay, failed-call output/teardown limits, process ownership through capture finalization, and cross-round path rebinding. The existing 18 offline audit-tool tests passed and the updated entry passed frontmatter validation. Audit scripts and tests are unchanged. The earlier first-operator and MindStudio guidance remains in place.

Four independent read-only scenario exercises distinguished residual component errors from phase flips, accepted the legitimate OBJECT route conditionally on actual registration/runtime evidence, preserved separate collection/deadline failures, and handled hardlink metadata changes plus intentional data retirement without inventing reproducibility. The responses retained unknown acceptance and missing worker-specific fatal-exit implementation as limitations. Internal resource/anchor checks resolved 125 local links. These observed exercises do not guarantee future decisions.

These are documentation and offline-tool checks. No new compiler build, NPU call, external-evaluation query/submission or latency measurement was performed for this release. The later local candidate's complete-call successes do not establish external all-pass acceptance, the identity of its reference backend, complete sanitizer clearance or a measured performance improvement.

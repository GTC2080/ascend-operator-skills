# Validate this portable skill package

This package contains operator-engineering guidance, public source references and two standard-library audit tools. It has no dependency on the author's project directories, experiment logs, private evidence indexes or NPU accounts.

## Checks available to every user

With Python 3.9 or later, run from the package root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The 18 bundled tests cover source-manifest exact/missing/extra/changed files, unsafe paths, symlinks, no overwrite, and synthetic ELF resource parsing, stale/missing required routes and unsupported/truncated input. Their fixtures are created in temporary directories; no private source or archived library is needed.

`MANIFEST.json` records every other distributed file's size and SHA-256. Check the exact member set and each digest when verifying an import/release. The repository CI runs the offline tests on Python 3.9 and 3.12 and checks the distributed manifest and local Markdown resource links.

The skill-creator frontmatter validator is an optional authoring check when that tool is available. It is not a runtime dependency. It checks format, not whether a model makes correct engineering decisions.

## Public-content checks

Before publication, inspect both the source tree and the actual release ZIP:

- Every relative resource reference resolves inside the package; public citations identify accessible upstream sources, with version limits where needed.
- No private project evidence map, local archive/experiment path, machine/account identifier, credential or private-log digest is distributed.
- Examples state their complete inputs, equations or assumptions instead of asking readers to locate an unpublished file.
- Chip/version-specific API guidance remains scoped; algorithms and debugging recipes do not claim universal target support or unpublished performance wins.

Keep project-specific run logs and evidence ledgers in that project's own records. Hashes of unavailable private files do not make a public example independently reproducible. The package manifest and pinned public-source commits serve a different purpose: readers can obtain the referenced content and verify those identities themselves.

## Validation limits

Offline tests establish their specific file/ELF behavior, not device execution, numerical accuracy, memory/synchronization safety, installed SDK support, backend correctness or latency. No NPU run or new performance result is implied by installing or validating this package.

The embedded-payload helper supports the ELF layout described in [build identity](references/build-identity.md). It does not inspect every backend, host registration route or runtime dispatch. An unsupported layout must remain unsupported, not be labeled passed.

Harness discovery, invocation and model behavior are client-specific. Resolving resources and passing tests cannot guarantee every future agent decision or every proprietary client's behavior. Evaluate target support and complete operator behavior in the actual deployment environment.

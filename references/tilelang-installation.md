# TileLang Ascend installation and verification

Use this guide when a development server lacks a usable TileLang Ascend environment. It covers the Ascend C/PTO route, not every upstream backend. Recheck the selected release's instructions before execution. Preparing documentation alone does not authorize installation, remote access or device jobs; an authorized operator-development task can include the necessary task-local setup without repeated approval.

The upstream sources below were inspected at `1d5daf0385156cbe0c499a16c10935c5190642a4` on 2026-10-17. The procedure has not been newly executed on a server as part of this documentation update. Keep installation, import, compilation, device execution and operator validation as separate claims.

## 1. Inventory before installing

Check the actual execution container and shell, not just its host's advertised hardware:

```bash
uname -m
cat /etc/os-release
npu-smi info
python3 -V
python3 -m pip --version
python3 -m pip show tilelang torch torch-npu Cython
```

A missing package can make the last command fail; classify that result. Record CPU architecture, OS/glibc, Python executable and ABI, actual CANN/compiler path/version, torch/torch_npu versions and NPU visibility. Locate the installed SDK's version information instead of guessing a universal version-file path. Record only relevant values, not credentials or a complete environment dump.

If a compatible TileLang environment already works, reuse it and proceed to verification. Before an import probe, apply the private-cache setup in section 5. If `import tilelang` succeeds, also inspect its version and module path: the generic TileLang package and the Ascend variant may share the import/distribution name. Do not choose an unqualified `pip install tilelang` without establishing which build and backend it will install.

At the inspected snapshot, the [upstream README](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/README.md) states CANN at least 8.3.RC1 and torch-npu at least 2.6.0.RC1; its source build scripts require Python at least 3.10. These lower bounds do not establish compatibility for every combination. Release wheels impose their own Python ABI, CANN/backend, OS and architecture requirements. The skill's Python 3.9 audit-tool minimum does not apply to TileLang installation.

If the driver, SDK or framework is missing/broken, first select a supported base image or resolve that specific prerequisite using the [TorchNPU compatibility guidance](https://github.com/Ascend/pytorch). Installing TileLang alone cannot supply a working NPU driver. Do not repair this by blindly upgrading the shared framework, changing drivers or using sudo pip.

## 2. Select an environment and initialize CANN

Use an existing suitable project environment, or create a task-owned environment. When the base Python already has a verified torch/torch_npu pair, one option is:

```bash
python3 -m venv --system-site-packages "$TL_TASK_ROOT/.venv-tilelang" || exit 1
source "$TL_TASK_ROOT/.venv-tilelang/bin/activate" || exit 1
command -v python python3 pip
python -m pip --version
```

`TL_TASK_ROOT` is a new, absolute, task-owned directory selected by the caller. This option inherits base-package visibility and is not hermetic. Preserve the framework versions and inspect the actual import paths. For an absent or incompatible base stack, use an isolated environment and an explicitly compatible torch/torch_npu pair; do not inherit a broken stack. Reuse an existing Conda environment where appropriate instead of creating another one automatically.

Set `TL_CANN_ROOT` to the real toolkit directory confirmed on this server, then initialize it in the same shell that will build and run kernels:

```bash
test -r "$TL_CANN_ROOT/set_env.sh" || exit 1
source "$TL_CANN_ROOT/set_env.sh" || exit 1
export ASCEND_HOME_PATH="$TL_CANN_ROOT"
```

Resolve SDK symlinks before recording the version. Recheck the selected interpreter and pip after sourcing CANN; reactivate the task environment if the SDK changed their resolution. Confirm the required compiler and dynamic libraries are discoverable. A separate SSH invocation does not inherit this shell's exports; initialize them in the actual remote task script too. Do not edit global shell startup files for a task-local installation.

For a verified existing framework, create a new constraints file to prevent an installation from silently replacing that pair:

```bash
TL_CONSTRAINTS="$TL_TASK_ROOT/torch-stack.constraints.txt"
python - "$TL_CONSTRAINTS" <<'PY' || exit 1
from importlib.metadata import version
from pathlib import Path
import sys

lines = [f"{name}=={version(name)}" for name in ("torch", "torch-npu")]
with Path(sys.argv[1]).open("x", encoding="utf-8") as stream:
    stream.write("\n".join(lines) + "\n")
PY
```

Missing framework metadata is a prerequisite failure. Review the constraints and the resolver plan. If installed pip supports `--dry-run`, use it before installation; otherwise review the selected wheel metadata and dependencies. Resolve a conflict explicitly rather than adding `--force-reinstall` or skipping unresolved dependencies.

## 3. Prefer an official matching wheel

Select one asset from the [official releases](https://github.com/tile-ai/tilelang-ascend/releases). Check the complete wheel filename and release notes against this target:

- `cp311-cp311` and `cp312-cp312` target different Python ABIs.
- `linux_aarch64` and `linux_x86_64` target different server CPU architectures; a Mac's architecture is not the remote server's ABI.
- CANN/backend labels such as `cann900`, `cann910` or `npuir` are not interchangeable. Verify release documentation and wheel metadata, including OS/glibc assumptions.
- A release tag can differ from the wheel's package version. Record both, the exact asset URL and digest. The newest release is not automatically the right one.

Download the chosen asset over normal verified HTTPS to a task-owned directory. `TL_WHEEL_URL`, `TL_WHEEL` and `TL_WHEEL_SHA256` must describe that one selected asset; do not use a wildcard over several downloaded wheels:

```bash
curl --fail --location --proto '=https' --proto-redir '=https' \
  --output "$TL_WHEEL" "$TL_WHEEL_URL" || exit 1
printf '%s  %s\n' "$TL_WHEEL_SHA256" "$TL_WHEEL" | sha256sum --check - || exit 1
python -m pip install --constraint "$TL_CONSTRAINTS" "$TL_WHEEL" || exit 1
python -m pip check
```

Compare against a publisher-provided asset digest when available. If none is published, record the official origin and computed SHA with that limitation; a locally computed hash alone is not publisher verification. Inspect wheel metadata before installation. If a wheel is incompatible, do not rename it or remove ABI checks to force it through pip.

On an offline server, transfer the chosen wheel and its required, compatible dependency wheelhouse from an authorized source. Verify hashes after transfer, then use local-only resolution:

```bash
python -m pip install --no-index --find-links "$TL_WHEELHOUSE" \
  --constraint "$TL_CONSTRAINTS" "$TL_WHEEL" || exit 1
python -m pip check
```

Missing dependency wheels are an incomplete wheelhouse. Do not use `--no-deps` merely to make installation appear successful. Avoid repeated large downloads when verified local assets already exist.

## 4. Source build when no suitable wheel exists

Choose a reviewed full commit as `TL_REF` and a fresh, task-owned `TL_SOURCE_DIR`. Reuse an existing matching clean checkout if available. Check source/build requirements, compiler tools, disk, memory, network access and available time before starting a build.

```bash
git clone --branch ascendc_pto --no-checkout \
  https://github.com/tile-ai/tilelang-ascend.git "$TL_SOURCE_DIR" || exit 1
git -C "$TL_SOURCE_DIR" checkout --detach "$TL_REF" || exit 1
git -C "$TL_SOURCE_DIR" submodule update --init --recursive || exit 1
git -C "$TL_SOURCE_DIR" rev-parse HEAD
git -C "$TL_SOURCE_DIR" submodule status --recursive
```

Pin the parent before initializing submodules. Inspect the selected [build script](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/build_wheel_ascend.sh), `requirements-build.txt`, `requirements.txt` and `setup.py`. At the reviewed snapshot, the wheel script installs requirements, updates/patches TVM and removes `dist`, `build` and `tilelang.egg-info` inside its checkout. Use a dedicated checkout where these side effects are safe; do not run it in an unrelated or shared source tree.

Confirm `python`, `python3` and `pip` resolve to the selected environment: upstream scripts call these names directly. Bound build parallelism using options/environment actually supported by that revision. Do not overlap a build with device performance capture.

Apply the [server resource policy](workflow.md#resource-utilization-by-phase) instead of automatically accepting reduced parallelism. At the reviewed snapshot, `install_ascend.sh` and a `setup.py` build path calculate half the visible CPU count; another path uses three quarters. Check the actual path in use and the reason for its memory guard. Prefer a supported job override. If none exists and the allocation/memory budget permits more jobs, a minimal reviewed patch to job selection in the task-owned build checkout is an option; record the patch and actual commands. An explicit `make -jN` or CMake `-jN` will not be replaced merely by setting `CMAKE_BUILD_PARALLEL_LEVEL`. Preserve all configuration, TVM patches and build/error checks.

For the reviewed wheel-building route:

```bash
cd "$TL_SOURCE_DIR" || exit 1
PIP_CONSTRAINT="$TL_CONSTRAINTS" bash ./build_wheel_ascend.sh || exit 1
```

Capture full build logs and the real exit status. The upstream build owns its TVM patches; do not bypass a patch failure. Enable optional LLVM/shared-memory/coverage paths only when required and supported on the actual architecture. In particular, inspect download architecture selection before copying an LLVM flag from another platform's instructions.

After a successful build, select the one newly produced wheel, record its filename and SHA, and install it with the same interpreter and constraints as in section 3. Do not install an old wheel left in another output directory.

The alternative [source-tree build](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/install_ascend.sh) uses `bash install_ascend.sh`, followed by `source set_env.sh` from that checkout. At this revision, `set_env.sh` prepends the source root to `PYTHONPATH` and sets `ACL_OP_INIT_MODE=1`. This route deliberately imports from the source checkout; it is different from a wheel installation. Use the selected release's required runtime initialization for the wheel route too, while checking that it does not unintentionally shadow the installed wheel. Record the actual module path in both cases.

## 5. Verify import, compiler and device execution

Use the same shell, interpreter and runtime initialization as the intended operator tests. For a wheel installation, verify outside the source checkout so the working directory cannot silently shadow the installed package. Before any TileLang import, select a fresh task-only cache and disable automatic cache clearing for this shell and its child processes:

```bash
export TILELANG_CACHE_DIR="$TL_TASK_ROOT/cache-smoke"
export TILELANG_CLEAR_CACHE=0
python - <<'PY' || exit 1
import shutil
import sys
import tilelang
import torch
import torch_npu

print("python:", sys.executable)
print("tilelang:", getattr(tilelang, "__version__", "unknown"), tilelang.__file__)
print("torch:", torch.__version__, torch.__file__)
print("torch_npu:", torch_npu.__version__, torch_npu.__file__)
print("cython CLI:", shutil.which("cython"))
assert torch.npu.is_available(), "NPU not visible to this environment"
print("visible NPU count:", torch.npu.device_count())
PY
```

This checks imports and visibility, not a TileLang compilation or device kernel. Inspect actual compiler discovery/commands when compiling. A missing Cython executable can coexist with an installed Cython module: confirm its scripts directory and correct the task-local PATH if needed. Reinstalling the same package does not establish that PATH is correct.

Next run a small official example matching the installed release/backend, with a real output assertion and a finite time limit. The reviewed [vector-add example](https://github.com/tile-ai/tilelang-ascend/blob/1d5daf0385156cbe0c499a16c10935c5190642a4/examples/elementwise/elementwise_add.py) accepts `--m` and `--n`; `128 x 256` fits its fixed blocks. For a different wheel, inspect that version's example first rather than assuming this snapshot's syntax works.

The reviewed example explicitly clears the kernel cache, regardless of the automatic-clearing setting. Confirm the installed backend actually uses the private directory selected above before running that example:

```bash
python - <<'PY' || exit 1
import os
from pathlib import Path
import tilelang.cache

expected = Path(os.environ["TILELANG_CACHE_DIR"]).resolve()
actual = Path(tilelang.cache.get_cache_dir()).resolve()
assert actual == expected, (actual, expected)
print("verified private smoke cache:", actual)
PY
python "$TL_EXAMPLE" --m 128 --n 256
```

`TL_EXAMPLE` is the reviewed, version-matched local example file. If cache introspection differs, inspect that installed version before executing its cache-clearing example. Never clear a shared cache as an installation diagnostic. Environment changes after the first import may not change cache singletons; use a new process with its environment set beforehand.

Require successful compilation, actual NPU execution and the example's output comparison. Then verify in a new process; if the intended workload relies on persistent-cache reload, test that route with an example that does not clear the cache. A first-run success cannot validate a route erased by the example itself. Finally run the actual operator's precision, tails, runtime updates, diagnostics and performance gates from the [TileLang development guide](tilelang.md).

## 6. Diagnose and hand off

| Symptom | First check |
| --- | --- |
| Wheel rejected by pip | Exact Python ABI, CPU/OS tags, backend and CANN compatibility; do not rename the wheel |
| Imports succeed but no NPU | Container/device visibility, driver/framework pair and same-shell SDK initialization |
| Package exists but wrong code is imported | Interpreter, working directory, PYTHONPATH and wheel/source provenance |
| Missing Cython/compiler/shared library | Actual executable/library discovery in this shell; distinguish package installation from PATH |
| Resolver changes the working framework | Constraints and wheel requirements; isolate or choose a compatible asset |
| Source build fails | First substantive build error, pinned submodules/patches, requirements and tool versions |
| Smoke works but operator fails | Frontend, layout, scalar, scope, cache or integration layer; use operator-specific validation |

Record the exact target stack, environment/interpreter, wheel URL/version/SHA or source/submodule refs, dependency constraints, initialization, imported module path, compiler commands and smoke logs/results. Distinguish installed, imported, compiled, device-tested and unresolved. Keep only task-owned environment/cache/build resources eligible for later cleanup; do not delete shared SDKs, frameworks or caches to make setup look clean.

#!/usr/bin/env bash
set -euo pipefail

section() {
  printf '\n[%s]\n' "$1"
}

version_or_missing() {
  local command_name="$1"
  shift
  if command -v "$command_name" >/dev/null 2>&1; then
    "$@" 2>&1 | head -n 3
  else
    printf '%s\n' "missing: ${command_name}"
  fi
}

section "run"
printf 'timestamp_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'hostname=%s\n' "$(hostname)"
printf 'working_directory=%s\n' "$(pwd)"

section "system"
uname -a

section "toolchain"
version_or_missing python3 python3 --version
version_or_missing docker docker --version
version_or_missing git git --version

section "ascend"
if command -v npu-smi >/dev/null 2>&1; then
  npu-smi info
else
  printf '%s\n' "missing: npu-smi"
fi

for variable_name in ASCEND_HOME_PATH ASCEND_TOOLKIT_HOME; do
  if [[ -n "${!variable_name:-}" ]]; then
    printf '%s=set\n' "$variable_name"
  else
    printf '%s=unset\n' "$variable_name"
  fi
done

section "python_packages"
python3 - <<'PY'
from importlib import import_module

for package_name in ("torch", "torch_npu", "vllm", "vllm_omni"):
    try:
        module = import_module(package_name)
    except Exception as exc:  # Environment inspection must continue after one failure.
        print(f"{package_name}=unavailable ({type(exc).__name__}: {exc})")
        continue
    print(f"{package_name}={getattr(module, '__version__', 'unknown')}")
PY

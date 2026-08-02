#!/usr/bin/env bash
set -euo pipefail

# Gate 0 is read-only with respect to the environment. It only creates a run
# directory under RUN_ROOT and records versions/configuration.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_root="${RUN_ROOT:-$repo_root/reports/runs}"
run_id="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-gate0}"
run_dir="$run_root/$run_id"
upstream_dir="${VLLM_OMNI_DIR:-/vllm-workspace/vllm-omni}"
deploy_config="${DEPLOY_CONFIG:-$upstream_dir/vllm_omni/deploy/minicpmo_4_5.yaml}"
require_npu="${REQUIRE_NPU:-1}"
require_source="${REQUIRE_SOURCE:-1}"

mkdir -p "$run_dir"

printf '%s\n' "run_id=$run_id" | tee "$run_dir/manifest.txt"
printf '%s\n' "repo_root=$repo_root" | tee -a "$run_dir/manifest.txt"
printf '%s\n' "upstream_dir=$upstream_dir" | tee -a "$run_dir/manifest.txt"
printf '%s\n' "deploy_config=$deploy_config" | tee -a "$run_dir/manifest.txt"

date -u +%Y-%m-%dT%H:%M:%SZ | tee "$run_dir/timestamp.txt"
hostname | tee "$run_dir/hostname.txt"
pwd | tee "$run_dir/working-directory.txt"
uname -a | tee "$run_dir/uname.txt"
python3 --version 2>&1 | tee "$run_dir/python-version.txt"
git --version 2>&1 | tee "$run_dir/git-version.txt"

if command -v npu-smi >/dev/null 2>&1; then
  npu-smi info 2>&1 | tee "$run_dir/npu-smi.txt"
  npu_status=0
else
  printf '%s\n' 'npu-smi not found' | tee "$run_dir/npu-smi.txt"
  npu_status=127
fi

python3 -m pip freeze 2>&1 | sort | grep -Ei \
  'torch|vllm|ascend|transformers|huggingface|stepaudio|librosa' \
  | tee "$run_dir/python-packages.txt" || true

python3 - "$run_dir/python-imports.txt" <<'PY'
from importlib import import_module
from pathlib import Path
import sys

output = Path(sys.argv[1])
lines = []
for name in ("torch", "torch_npu", "vllm", "vllm_ascend", "vllm_omni"):
    try:
        module = import_module(name)
        lines.append(f"{name}={getattr(module, '__version__', 'unknown')}")
    except Exception as exc:
        lines.append(f"{name}=ERROR {type(exc).__name__}: {exc}")
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
PY

if [[ -d "$upstream_dir/.git" ]]; then
  {
    git -C "$upstream_dir" status --short --branch
    git -C "$upstream_dir" rev-parse HEAD
    git -C "$upstream_dir" describe --tags --always --dirty
  } 2>&1 | tee "$run_dir/upstream-git.txt"
else
  printf '%s\n' "upstream source not found: $upstream_dir" | tee "$run_dir/upstream-git.txt"
  source_status=1
fi

if [[ -f "$deploy_config" ]]; then
  cp "$deploy_config" "$run_dir/deploy-config.yaml"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$run_dir/deploy-config.yaml" | tee "$run_dir/deploy-config.sha256"
  else
    shasum -a 256 "$run_dir/deploy-config.yaml" | tee "$run_dir/deploy-config.sha256"
  fi
else
  printf '%s\n' "deploy config not found: $deploy_config" | tee "$run_dir/deploy-config.txt"
  deploy_status=1
fi

if [[ "$require_npu" == "1" && "$npu_status" -ne 0 ]]; then
  printf '%s\n' "Gate 0: FAIL (NPU inspection unavailable; run on HiDevLab)"
  exit 2
fi

if [[ "$require_source" == "1" && "${source_status:-0}" -ne 0 ]]; then
  printf '%s\n' "Gate 0: FAIL (vLLM-Omni source checkout unavailable)"
  exit 3
fi

if [[ "$require_source" == "1" && "${deploy_status:-0}" -ne 0 ]]; then
  printf '%s\n' "Gate 0: FAIL (MiniCPM-o deploy config unavailable)"
  exit 4
fi

printf '%s\n' "Gate 0: collected run artifacts in $run_dir"

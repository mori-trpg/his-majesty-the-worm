#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
STATE_DIR="${SKILL_DIR}/.state"
SUMMARY_FILE="${STATE_DIR}/summary.env"
FILES_FILE="${STATE_DIR}/files.tsv"

usage() {
  cat <<'EOF'
Usage:
  run_state.sh start --targets <file1> <file2> ...
  run_state.sh update --file <path> --status <running|pass|blocked|failed> [--critical-fixed N] [--minor-fixed M] [--remaining-critical R]
  run_state.sh end
  run_state.sh status
EOF
}

now_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

ensure_state_dir() {
  mkdir -p "${STATE_DIR}"
}

load_summary() {
  ACTIVE=0
  PENDING_COUNT=0
  UNRESOLVED_CRITICAL_TOTAL=0
  STARTED_AT=""
  ENDED_AT=""
  UPDATED_AT=""
  if [[ -f "${SUMMARY_FILE}" ]]; then
    # shellcheck disable=SC1090
    . "${SUMMARY_FILE}"
  fi
}

write_summary() {
  local active="$1"
  local pending="$2"
  local unresolved="$3"
  local started="$4"
  local ended="$5"

  cat > "${SUMMARY_FILE}" <<EOF
ACTIVE=${active}
PENDING_COUNT=${pending}
UNRESOLVED_CRITICAL_TOTAL=${unresolved}
STARTED_AT='${started}'
ENDED_AT='${ended}'
UPDATED_AT='$(now_utc)'
EOF
}

recalculate_counters() {
  if [[ ! -f "${FILES_FILE}" ]]; then
    echo "0 0"
    return
  fi
  awk -F '\t' '
    NR == 1 { next }
    {
      if ($2 == "pending" || $2 == "running") pending += 1
      unresolved += ($5 + 0)
    }
    END { printf "%d %d\n", pending + 0, unresolved + 0 }
  ' "${FILES_FILE}"
}

cmd_start() {
  shift
  if [[ "${1:-}" != "--targets" ]]; then
    usage
    exit 1
  fi
  shift
  if [[ "$#" -lt 1 ]]; then
    echo "start requires at least one target" >&2
    exit 1
  fi

  ensure_state_dir
  local ts
  ts="$(now_utc)"

  {
    printf "file\tstatus\tcritical_fixed\tminor_fixed\tremaining_critical\tupdated_at\n"
    for target in "$@"; do
      printf "%s\tpending\t0\t0\t0\t%s\n" "${target}" "${ts}"
    done
  } > "${FILES_FILE}"

  write_summary 1 "$#" 0 "${ts}" ""
  printf '{"ok":true,"action":"start","targets":%d}\n' "$#"
}

cmd_update() {
  shift
  local file=""
  local status=""
  local critical_fixed=0
  local minor_fixed=0
  local remaining_critical=0

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --file)
        file="${2:-}"
        shift 2
        ;;
      --status)
        status="${2:-}"
        shift 2
        ;;
      --critical-fixed)
        critical_fixed="${2:-0}"
        shift 2
        ;;
      --minor-fixed)
        minor_fixed="${2:-0}"
        shift 2
        ;;
      --remaining-critical)
        remaining_critical="${2:-0}"
        shift 2
        ;;
      *)
        echo "unknown argument: $1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [[ -z "${file}" || -z "${status}" ]]; then
    echo "update requires --file and --status" >&2
    exit 1
  fi
  case "${status}" in
    running|pass|blocked|failed) ;;
    *)
      echo "invalid status: ${status}" >&2
      exit 1
      ;;
  esac

  ensure_state_dir
  if [[ ! -f "${FILES_FILE}" ]]; then
    echo "run-state not initialized; call start first" >&2
    exit 1
  fi

  local ts tmp_file
  ts="$(now_utc)"
  tmp_file="$(mktemp)"

  awk -F '\t' -v OFS='\t' \
    -v target="${file}" \
    -v status="${status}" \
    -v critical_fixed="${critical_fixed}" \
    -v minor_fixed="${minor_fixed}" \
    -v remaining_critical="${remaining_critical}" \
    -v ts="${ts}" '
    BEGIN { updated = 0 }
    NR == 1 { print; next }
    $1 == target {
      print target, status, critical_fixed, minor_fixed, remaining_critical, ts
      updated = 1
      next
    }
    { print }
    END {
      if (!updated) {
        print target, status, critical_fixed, minor_fixed, remaining_critical, ts
      }
    }
  ' "${FILES_FILE}" > "${tmp_file}"
  mv "${tmp_file}" "${FILES_FILE}"

  load_summary
  local pending unresolved
  read -r pending unresolved < <(recalculate_counters)
  write_summary 1 "${pending}" "${unresolved}" "${STARTED_AT:-${ts}}" "${ENDED_AT:-}"

  printf '{"ok":true,"action":"update","file":"%s","status":"%s","pending":%d,"unresolved_critical_total":%d}\n' \
    "${file}" "${status}" "${pending}" "${unresolved}"
}

cmd_end() {
  ensure_state_dir
  load_summary

  local pending unresolved ts
  read -r pending unresolved < <(recalculate_counters)
  ts="$(now_utc)"
  write_summary 0 "${pending}" "${unresolved}" "${STARTED_AT:-${ts}}" "${ts}"
  printf '{"ok":true,"action":"end"}\n'
}

cmd_status() {
  load_summary
  printf 'ACTIVE=%s\n' "${ACTIVE:-0}"
  printf 'PENDING_COUNT=%s\n' "${PENDING_COUNT:-0}"
  printf 'UNRESOLVED_CRITICAL_TOTAL=%s\n' "${UNRESOLVED_CRITICAL_TOTAL:-0}"
  printf 'STARTED_AT=%s\n' "${STARTED_AT:-}"
  printf 'ENDED_AT=%s\n' "${ENDED_AT:-}"
  printf 'UPDATED_AT=%s\n' "${UPDATED_AT:-}"
  if [[ -f "${FILES_FILE}" ]]; then
    printf '\n'
    cat "${FILES_FILE}"
  fi
}

if [[ "$#" -lt 1 ]]; then
  usage
  exit 1
fi

case "$1" in
  start) cmd_start "$@" ;;
  update) cmd_update "$@" ;;
  end) cmd_end "$@" ;;
  status) cmd_status ;;
  *)
    usage
    exit 1
    ;;
esac

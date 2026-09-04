#!/bin/zsh
# Run the pinned Pi harness with fresh, per-run configuration and state.
#
#   npm ci
#   export QUNXIA_LLM_BASE_URL=https://api.openai.com/v1
#   export QUNXIA_LLM_API_KEY=sk-...
#   export QUNXIA_LLM_MODEL=openai-compatible/gpt-5
#   ./Scripts/play-agent.sh -p "play the opening"
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"

: "${QUNXIA_LLM_BASE_URL:?set QUNXIA_LLM_BASE_URL, e.g. http://localhost:11434/v1}"
: "${QUNXIA_LLM_MODEL:?set a full provider/model reference, e.g. local-openai/qwen3-vl:32b}"

if [[ "$QUNXIA_LLM_MODEL" != */* || "$QUNXIA_LLM_MODEL" == */ || "$QUNXIA_LLM_MODEL" == /* ]]; then
  print -u2 "QUNXIA_LLM_MODEL must include non-empty provider and model names, e.g. local-openai/qwen3-vl:32b"
  exit 2
fi
MODEL_REF="$QUNXIA_LLM_MODEL"

PI_BIN="$ROOT/node_modules/.bin/pi"
API="${QUNXIA_API:-http://127.0.0.1:8765}"
API="${API%/}"
API_SUPPLIED=0
[[ -n "${QUNXIA_API:-}" ]] && API_SUPPLIED=1
if [[ "$API_SUPPLIED" == "1" ]]; then
  STATUS_URL="$API/screen?format=png&spectate=1"
else
  STATUS_URL="$API/screen?format=png"
fi
KEY="${QUNXIA_LLM_API_KEY:-local}"
# Empty overrides let the preparation step use the explicit model definition.
INPUT="${QUNXIA_LLM_INPUT:-}"
CTX="${QUNXIA_LLM_CONTEXT:-}"
MAX_TOKENS="${QUNXIA_LLM_MAX_TOKENS:-}"
LLM_API="${QUNXIA_LLM_API:-}"
REASONING="${QUNXIA_LLM_REASONING:-}"
SUPPORTS_REASONING_EFFORT="${QUNXIA_LLM_SUPPORTS_REASONING_EFFORT:-}"
THINKING="${QUNXIA_THINKING:-}"
PROFILE="${QUNXIA_PI_PROFILE:-strict}"
BENCH_LANG="${QUNXIA_BENCH_LANG:-zh}"
RUNS_DIR="${QUNXIA_RUNS_DIR:-$ROOT/.runs/pi}"
RUN_ID="${QUNXIA_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
RESUME="${QUNXIA_RESUME:-0}"

if [[ ! "$RUN_ID" =~ '^[A-Za-z0-9][A-Za-z0-9._-]*$' ]]; then
  print -u2 "QUNXIA_RUN_ID may contain only letters, digits, dot, underscore and hyphen"
  exit 2
fi
if [[ "$RESUME" != "0" && "$RESUME" != "1" ]]; then
  print -u2 "QUNXIA_RESUME must be 0 or 1"
  exit 2
fi
if [[ ! -x "$PI_BIN" ]]; then
  print -u2 "Pinned Pi is not installed. Run: npm ci"
  exit 1
fi
if ! node -e 'const [major, minor] = process.versions.node.split(".").map(Number); process.exit(major > 22 || (major === 22 && minor >= 19) ? 0 : 1)'; then
  print -u2 "Pi 0.84.4 requires Node >=22.19.0; found $(node --version)"
  exit 1
fi
PI_VERSION="$(node -p 'require(process.argv[1]).dependencies["@earendil-works/pi-coding-agent"]' "$ROOT/package.json")"
ACTUAL_PI_VERSION="$("$PI_BIN" --version)"
if [[ "$ACTUAL_PI_VERSION" != "$PI_VERSION" ]]; then
  print -u2 "Expected Pi $PI_VERSION, found $ACTUAL_PI_VERSION. Run: npm ci"
  exit 1
fi

PROFILE_PROMPT="$(node "$ROOT/Scripts/read-pi-profile.mjs" "$ROOT/pi-agent/profiles.json" "$PROFILE")"
BENCH_HELP_URL=""
if [[ "$PROFILE_PROMPT" == "session-help" ]]; then
  if [[ "$API_SUPPLIED" == "0" ]]; then
    print -u2 "benchmark profiles require an explicit QUNXIA_API session URL"
    exit 2
  fi
  BENCH_HELP_URL="$API/help?lang=$BENCH_LANG"
fi

# Preserve the recorded model, tool and session settings while accepting output
# options and a prompt.
USER_ARGS=()
while (( $# > 0 )); do
  case "$1" in
    -p|--print)
      USER_ARGS+=("$1")
      shift
      ;;
    --mode)
      if (( $# < 2 )); then
        print -u2 "$1 requires a value"
        exit 2
      fi
      if [[ "$2" != "text" && "$2" != "json" ]]; then
        print -u2 "--mode must be text or json in the isolated runner"
        exit 2
      fi
      USER_ARGS+=("$1" "$2")
      shift 2
      ;;
    --mode=*)
      print -u2 "Pi requires '--mode text' or '--mode json'; --mode=... is not supported"
      exit 2
      ;;
    --thinking|--thinking=*)
      print -u2 "set QUNXIA_THINKING instead of passing $1; the resolved level is recorded in run.json"
      exit 2
      ;;
    --)
      shift
      for argument in "$@"; do
        if [[ "$argument" == @* ]]; then
          print -u2 "file arguments are disabled in the isolated runner: $argument"
          exit 2
        fi
      done
      USER_ARGS+=(-- "$@")
      break
      ;;
    @*)
      print -u2 "file arguments are disabled in the isolated runner: $1"
      exit 2
      ;;
    -*)
      print -u2 "unsupported Pi option in isolated runner: $1"
      exit 2
      ;;
    *)
      USER_ARGS+=("$1")
      shift
      ;;
  esac
done

mkdir -p "$RUNS_DIR"
RUNS_DIR="$(cd "$RUNS_DIR" && pwd -P)"
RUN_DIR="$RUNS_DIR/$RUN_ID"
HARNESS_DIRTY=0
[[ -n "$(git status --porcelain 2>/dev/null)" ]] && HARNESS_DIRTY=1

env \
  QUNXIA_ROOT="$ROOT" \
  QUNXIA_RUN_DIR="$RUN_DIR" \
  QUNXIA_RUN_ID="$RUN_ID" \
  QUNXIA_PI_PROFILE="$PROFILE" \
  QUNXIA_PI_VERSION="$PI_VERSION" \
  QUNXIA_BENCH_LANG="$BENCH_LANG" \
  QUNXIA_BENCH_HELP_URL="$BENCH_HELP_URL" \
  QUNXIA_LLM_BASE_URL="$QUNXIA_LLM_BASE_URL" \
  QUNXIA_MODEL_REF="$MODEL_REF" \
  QUNXIA_LLM_INPUT_JSON="$INPUT" \
  QUNXIA_LLM_CONTEXT="$CTX" \
  QUNXIA_LLM_MAX_TOKENS="$MAX_TOKENS" \
  QUNXIA_LLM_API="$LLM_API" \
  QUNXIA_LLM_REASONING="$REASONING" \
  QUNXIA_LLM_SUPPORTS_REASONING_EFFORT="$SUPPORTS_REASONING_EFFORT" \
  QUNXIA_THINKING="$THINKING" \
  QUNXIA_API="$API" \
  QUNXIA_HARNESS_DIRTY="$HARNESS_DIRTY" \
  QUNXIA_RESUME="$RESUME" \
  node "$ROOT/Scripts/prepare-pi-run.mjs" >/dev/null

CONFIG_DIR="$RUN_DIR/config"
SESSION_DIR="$RUN_DIR/sessions"
WORKSPACE_DIR="$RUN_DIR/workspace"
TOOLS="$(node -e 'const fs=require("node:fs"); const p=JSON.parse(fs.readFileSync(process.argv[1])); process.stdout.write(p.tools.join(","))' "$RUN_DIR/run.json")"
SCALE="$(node -e 'const fs=require("node:fs"); const p=JSON.parse(fs.readFileSync(process.argv[1])); process.stdout.write(String(p.scale))' "$RUN_DIR/run.json")"
OBSERVE_AFTER_ACTION="$(node -e 'const fs=require("node:fs"); const p=JSON.parse(fs.readFileSync(process.argv[1])); process.stdout.write(p.observeAfterAction ? "1" : "0")' "$RUN_DIR/run.json")"
THINKING_LEVEL="$(node -e 'const fs=require("node:fs"); const p=JSON.parse(fs.readFileSync(process.argv[1])); process.stdout.write(p.model.thinkingLevel || "")' "$RUN_DIR/run.json")"
EXTENSIONS=()
while IFS= read -r extension; do
  EXTENSIONS+=(--extension "$CONFIG_DIR/$extension/index.ts")
done < <(node -e 'const fs=require("node:fs"); const p=JSON.parse(fs.readFileSync(process.argv[1])); process.stdout.write(`${p.extensions.join("\n")}\n`)' "$RUN_DIR/run.json")

print "Pi $PI_VERSION | run $RUN_ID | profile $PROFILE"
print "Run state: $RUN_DIR"

if [[ "${QUNXIA_PREPARE_ONLY:-0}" == "1" ]]; then
  exit 0
fi

# Bring a default local game up when needed. For an explicitly supplied API,
# wait for that isolated backend rather than starting an unrelated local game.
if ! curl -sf -m 2 -o /dev/null "$STATUS_URL"; then
  if [[ "$API_SUPPLIED" == "0" ]]; then
    print "starting the game..."
    "$ROOT/Scripts/run.sh" >"$RUN_DIR/game.log" 2>&1 &
  else
    print "waiting for the supplied game API..."
  fi
  for _ in {1..90}; do
    curl -sf -m 2 -o /dev/null "$STATUS_URL" && break
    sleep 1
  done
  curl -sf -m 2 -o /dev/null "$STATUS_URL" || {
    print -u2 "the game API did not become ready at $STATUS_URL"
    if [[ "$API_SUPPLIED" == "0" ]]; then
      print -u2 "see $RUN_DIR/game.log"
    fi
    exit 1
  }
  if [[ "$API_SUPPLIED" == "0" ]]; then
    print "waiting for the title screen..."
    curl -sf -m 60 -X POST "$API/wait?image=0" -d '{"ms":14000}' >/dev/null || true
  fi
fi

RESUME_ARGS=()
[[ "$RESUME" == "1" ]] && RESUME_ARGS+=(--continue)
THINKING_ARGS=()
[[ -n "$THINKING_LEVEL" ]] && THINKING_ARGS+=(--thinking "$THINKING_LEVEL")

cd "$WORKSPACE_DIR"
exec env \
  PI_CODING_AGENT_DIR="$CONFIG_DIR" \
  PI_OFFLINE=1 \
  QUNXIA_API="$API" \
  QUNXIA_SCALE="$SCALE" \
  QUNXIA_OBSERVE_AFTER_ACTION="$OBSERVE_AFTER_ACTION" \
  QUNXIA_LLM_API_KEY="$KEY" \
  "$PI_BIN" \
    --model "$MODEL_REF" \
    --session-dir "$SESSION_DIR" \
    --name "$RUN_ID" \
    --no-extensions \
    "${EXTENSIONS[@]}" \
    --no-skills \
    --no-context-files \
    --tools "$TOOLS" \
    "${THINKING_ARGS[@]}" \
    "${RESUME_ARGS[@]}" \
    "${USER_ARGS[@]}"

#!/usr/bin/env bash
# Zweitbewertung: exportierte Klassifikationsstapel an Gemini (Antigravity-CLI agy).
# Sequentiell, auf belkis-home. Kein paralleles agy.
set -euo pipefail

MODEL='Gemini 3.8 Flash (High)'
MODE='plan'
PRINT_TIMEOUT='1400s'
PAUSE_SECONDS=2
MAX_ATTEMPTS=3
# Ein argv-Argument darf auf Linux höchstens MAX_ARG_STRLEN (32 Seiten, 131072 Bytes) lang sein.
# Darunter geht der Prompt über --print, sonst über stdin. agy behandelt "--print -" als Text "-",
# liest den Prompt aber von stdin, wenn --print fehlt (agy --help, am 2026-10-14 geprüft).
MAX_INLINE_BYTES=100000
PREFIX='Verwende KEINE Werkzeuge, keine Befehle, keine Dateien, keine URLs. Antworte ausschließlich mit dem verlangten JSON.'

usage() {
  cat <<'EOF'
Aufruf: agy_second_rater.sh [--dry-run] VERZEICHNIS

VERZEICHNIS ist P mit P/<arm>/<run>/batch_<n>.json
(Felder system, user, expected_ids, kind; von backend/scripts/export_rater_prompts.py).
Jede Stapeldatei geht an Gemini. Die Rohantwort liegt daneben als batch_<n>.answer.txt.
Vorhandene plausible Antworten (enthalten „{“, nicht „no output produced“) werden übersprungen.
--dry-run zeigt nur, was gesendet würde.
EOF
}

die() {
  printf '%s\n' "$*" >&2
  exit 2
}

plausible_answer() {
  local file=$1
  [[ -f $file && -s $file ]] || return 1
  grep -F -q -- '{' "$file" || return 1
  if grep -F -q -- 'no output produced' "$file"; then
    return 1
  fi
  return 0
}

write_prompt_file() {
  local json=$1 dest=$2
  local system user
  if ! jq -e '(.system | type == "string") and (.user | type == "string")' "$json" >/dev/null; then
    return 1
  fi
  system=$(jq -r '.system' "$json")
  user=$(jq -r '.user' "$json")
  {
    printf '%s\n\n' "$PREFIX"
    printf '%s\n\n' "$system"
    printf '%s\n' "$user"
  } >"$dest"
}

log_progress() {
  local rel=$1 duration=$2 result=$3
  printf '%s\t%s\t%s\t%s\n' "$(date -Iseconds)" "$rel" "${duration}s" "$result" | tee -a "$LOG_FILE"
}

invoke_agy() {
  local prompt_file=$1 out=$2 err=$3
  local bytes work prompt rc
  bytes=$(stat -c '%s' "$prompt_file")
  work=$(mktemp -d)
  rc=0
  # Leeres Arbeitsverzeichnis: plan-Modus soll das Repo nicht als Werkzeugziel sehen.
  if (( bytes > MAX_INLINE_BYTES )); then
    (
      cd "$work"
      agy --model "$MODEL" --mode "$MODE" --print-timeout "$PRINT_TIMEOUT"
    ) <"$prompt_file" >"$out" 2>"$err" || rc=$?
  else
    prompt=$(<"$prompt_file")
    (
      cd "$work"
      agy --model "$MODEL" --mode "$MODE" --print-timeout "$PRINT_TIMEOUT" --print "$prompt" </dev/null
    ) >"$out" 2>"$err" || rc=$?
  fi
  rm -rf "$work"
  return "$rc"
}

answer_rejected() {
  local out=$1 err=$2 rc=$3
  if grep -F -q -- 'no output produced' "$out" "$err"; then
    printf '%s\n' 'no output produced'
    return 0
  fi
  if ! grep -F -q -- '{' "$out"; then
    printf '%s\n' 'kein JSON'
    return 0
  fi
  if (( rc != 0 )); then
    printf '%s\n' "Exit ${rc}"
    return 0
  fi
  return 1
}

dry_run=0
PROMPT_DIR=''
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) dry_run=1; shift ;;
    -h | --help) usage; exit 0 ;;
    --) shift; break ;;
    -*) die "Unbekannte Option: $1" ;;
    *)
      [[ -z $PROMPT_DIR ]] || die "Nur ein Verzeichnis angeben."
      PROMPT_DIR=$1
      shift
      ;;
  esac
done

[[ -n $PROMPT_DIR ]] || { usage >&2; exit 2; }
[[ -d $PROMPT_DIR ]] || die "Kein Verzeichnis: $PROMPT_DIR"
command -v jq >/dev/null 2>&1 || die "jq fehlt."
if [[ $dry_run -eq 0 ]]; then
  command -v agy >/dev/null 2>&1 || die "agy fehlt. Die Antigravity-CLI wird auf belkis-home erwartet."
fi
PROMPT_DIR=$(cd "$PROMPT_DIR" && pwd)
LOG_FILE=$PROMPT_DIR/agy.log

if [[ $dry_run -eq 0 ]] && ! touch "$LOG_FILE"; then
  die "Log nicht schreibbar: $LOG_FILE"
fi

mapfile -d '' found < <(find "$PROMPT_DIR" -type f -name 'batch_*.json' -print0 | LC_ALL=C sort -z)
batches=()
for json in "${found[@]}"; do
  base=$(basename "$json")
  if [[ $base =~ ^batch_[0-9]+\.json$ ]]; then
    batches+=("$json")
  fi
done

ok_count=0
fail_count=0
skip_count=0
dry_count=0
calls_done=0

for json in "${batches[@]}"; do
  rel=${json#"$PROMPT_DIR"/}
  answer=${json%.json}.answer.txt

  if plausible_answer "$answer"; then
    skip_count=$((skip_count + 1))
    if [[ $dry_run -eq 1 ]]; then
      printf 'Datei: %s\nAktion: übersprungen (vorhandene Antwort)\n\n' "$rel"
    else
      log_progress "$rel" 0 "übersprungen"
    fi
    continue
  fi

  prompt_file=$(mktemp)
  if ! write_prompt_file "$json" "$prompt_file"; then
    fail_count=$((fail_count + 1))
    if [[ $dry_run -eq 1 ]]; then
      printf 'Datei: %s\nAktion: fehlgeschlagen (system oder user fehlt)\n\n' "$rel"
    else
      log_progress "$rel" 0 "fehlgeschlagen (system oder user fehlt)"
    fi
    rm -f "$prompt_file"
    continue
  fi

  if [[ $dry_run -eq 1 ]]; then
    bytes=$(stat -c '%s' "$prompt_file")
    if (( bytes > MAX_INLINE_BYTES )); then
      weg="stdin (${bytes} Bytes)"
    else
      weg="--print (${bytes} Bytes)"
    fi
    printf 'Datei: %s\n' "$rel"
    printf 'Aktion: senden\n'
    printf 'Modell: %s\n' "$MODEL"
    printf 'Modus: %s\n' "$MODE"
    printf 'Timeout: %s\n' "$PRINT_TIMEOUT"
    printf 'Übergabe: %s\n' "$weg"
    printf '%s\n' '--- Prompt ---'
    cat "$prompt_file"
    printf '%s\n\n' '--- Ende ---'
    dry_count=$((dry_count + 1))
    rm -f "$prompt_file"
    continue
  fi

  succeeded=0
  attempt=1
  while (( attempt <= MAX_ATTEMPTS )); do
    if (( calls_done > 0 )); then
      sleep "$PAUSE_SECONDS"
    fi
    calls_done=$((calls_done + 1))
    printf 'sende %s (Versuch %s/%s)\n' "$rel" "$attempt" "$MAX_ATTEMPTS"
    out=$(mktemp)
    err=$(mktemp)
    start=$(date +%s)
    rc=0
    invoke_agy "$prompt_file" "$out" "$err" || rc=$?
    end=$(date +%s)
    duration=$((end - start))
    why=''
    if why=$(answer_rejected "$out" "$err" "$rc"); then
      if (( attempt == MAX_ATTEMPTS )); then
        partial=${answer}.partial
        cat "$err" "$out" >"$partial"
        mv "$partial" "$answer"
        if plausible_answer "$answer"; then
          rm -f "$answer"
        fi
        log_progress "$rel" "$duration" "fehlgeschlagen nach ${MAX_ATTEMPTS} Versuchen (${why})"
        fail_count=$((fail_count + 1))
      else
        log_progress "$rel" "$duration" "verworfen (${why}), Versuch ${attempt}/${MAX_ATTEMPTS}"
      fi
    else
      partial=${answer}.partial
      cat "$out" >"$partial"
      mv "$partial" "$answer"
      log_progress "$rel" "$duration" "ok"
      ok_count=$((ok_count + 1))
      succeeded=1
    fi
    rm -f "$out" "$err"
    if (( succeeded == 1 )); then
      break
    fi
    attempt=$((attempt + 1))
  done
  rm -f "$prompt_file"
done

if [[ $dry_run -eq 1 ]]; then
  printf 'Zusammenfassung: %s würden gesendet, %s fehlgeschlagen, %s übersprungen\n' \
    "$dry_count" "$fail_count" "$skip_count"
else
  summary="Zusammenfassung: ${ok_count} ok, ${fail_count} fehlgeschlagen, ${skip_count} übersprungen"
  printf '%s\n' "$summary"
  printf '%s\t%s\t%s\t%s\n' "$(date -Iseconds)" "-" "0s" "$summary" >>"$LOG_FILE"
fi

if (( fail_count > 0 )); then
  exit 1
fi
exit 0

#!/usr/bin/env bash
# E2E im offiziellen Playwright-Image: dieselben Browser (inkl. WebKit/iPhone) und Schriften wie auf GitHub.
# Läuft auf einer Kopie der versionierten Dateien; zurück kommen nur Referenzbilder (bei --update-snapshots) und der Report.
# Aufruf: e2e/docker-test.sh [playwright-Argumente], z. B. e2e/docker-test.sh --update-snapshots
set -uo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
IMG=mcr.microsoft.com/playwright:v1.63.0-noble
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
(cd "$ROOT" && git ls-files -co --exclude-standard -z | xargs -0 cp --parents -t "$WORK")
docker run --rm --ipc=host -u "$(id -u):$(id -g)" -e HOME=/tmp -e CI=1 \
  -v "$WORK":/work -w /work "$IMG" \
  bash -c "cd frontend && npm ci --no-audit --no-fund --loglevel=error && cd ../e2e && npm ci --no-audit --no-fund --loglevel=error && npx playwright test $*"
rc=$?
if [[ " $* " == *" --update-snapshots "* ]]; then
  rsync -a --delete "$WORK/e2e/tests/visual.spec.ts-snapshots/" "$ROOT/e2e/tests/visual.spec.ts-snapshots/"
fi
rm -rf "$ROOT/e2e/playwright-report" && cp -r "$WORK/e2e/playwright-report" "$ROOT/e2e/playwright-report" 2>/dev/null
exit $rc

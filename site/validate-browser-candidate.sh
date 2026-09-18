#!/usr/bin/env bash
# Vercel preview trigger: browser evidence for frozen candidate.
set -euxo pipefail

cp "$0" /tmp/jarvis-validate-browser.sh
cd ..
git checkout --detach 28f3785c24d1cb50905bc0af0f6586a2999ae027
test "$(git rev-parse HEAD)" = "28f3785c24d1cb50905bc0af0f6586a2999ae027"

npm install --no-audit --no-fund
npm run test:browser:install
python tooling/validate_v020_plan4.py \
  --gate browser-ui \
  --report reports/v020-plan4-browser-ui-linux.json

echo "===BROWSER_UI_REPORT==="
cat reports/v020-plan4-browser-ui-linux.json

mkdir -p site/.validation
cp reports/v020-plan4-browser-ui-linux.json site/.validation/browser-ui-linux.json

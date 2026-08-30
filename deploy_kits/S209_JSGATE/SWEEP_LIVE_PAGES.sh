#!/bin/bash
# Sweep every served page on the VPS for un-parseable inline JavaScript.
# READ-ONLY. Exit 0 = all pages parse, 1 = one refused, 2 = gate could not run.
# Run any time; it changes nothing.
UI=${1:-/root/finance/finance_ui}
echo "Sweeping $UI"
python3 "$(dirname "$0")/js_gate.py" "$UI"/*.html

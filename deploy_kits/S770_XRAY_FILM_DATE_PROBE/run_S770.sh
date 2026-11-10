#!/bin/bash
# S770_XRAY_FILM_DATE_PROBE -- READ-ONLY probe. Starts in the background and returns at once; the report comes by mail.
# It adds tesseract-ocr (apt) and Pillow (into /root/wa/venv) only if they are missing; it changes no /root file,
# no database row, nothing on Drive. Output: /root/s770_probe/report.txt (no names, no IDs) and one mail.
set -u
K="$(cd "$(dirname "$0")" && pwd)"
O=/root/s770_probe
mkdir -p "$O" && chmod 700 "$O"
cp -p "$K/probe_s770.py" "$O/probe_s770.py"
(
  command -v tesseract >/dev/null 2>&1 || { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq tesseract-ocr; }
  /root/wa/venv/bin/python3 -c "import PIL" 2>/dev/null || /root/wa/venv/bin/python3 -m pip install -q pillow
  nice -n 15 ionice -c3 /root/wa/venv/bin/python3 -B "$O/probe_s770.py"
) > "$O/run.log" 2>&1 < /dev/null &
disown
echo "S770_PROBE: STARTED -- read-only; the report comes by mail in about 15-20 minutes"

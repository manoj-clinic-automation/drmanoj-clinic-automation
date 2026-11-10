#!/bin/bash
# S770_XRAY_FILM_DATE_PROBE v2 -- READ-ONLY probe. Readies an OCR tool (about 1-3 minutes, in front of you), then runs the
# probe in the background and returns; the report comes by mail. It changes no /root file, no database row, nothing on Drive.
# OCR: tesseract-ocr (apt) when it installs; otherwise RapidOCR in its OWN venv /root/s770_probe/ocrv (never /root/wa/venv).
set -u
K="$(cd "$(dirname "$0")" && pwd)"
O=/root/s770_probe
mkdir -p "$O" && chmod 700 "$O"
cp -p "$K/probe_s770.py" "$O/probe_s770.py"
PY=/root/wa/venv/bin/python3
if ! command -v tesseract >/dev/null 2>&1; then
  echo "S770: installing tesseract-ocr ..."
  timeout 240 apt-get install -y -q tesseract-ocr > "$O/apt.log" 2>&1 || { timeout 240 apt-get update -q >> "$O/apt.log" 2>&1; timeout 240 apt-get install -y -q tesseract-ocr >> "$O/apt.log" 2>&1; }
  command -v tesseract >/dev/null 2>&1 && echo "S770: tesseract ready" || echo "S770: tesseract did not install -- $(grep -E '^E:' "$O/apt.log" | tail -1 | cut -c1-150)"
fi
if ! command -v tesseract >/dev/null 2>&1; then
  if [ ! -x "$O/ocrv/bin/python3" ] || ! "$O/ocrv/bin/python3" -c "import rapidocr_onnxruntime" 2>/dev/null; then
    echo "S770: setting up RapidOCR in its own folder (1-3 minutes) ..."
    rm -rf "$O/ocrv"
    { python3 -m venv "$O/ocrv" || "$PY" -m venv "$O/ocrv"; } > "$O/venv.log" 2>&1
    "$O/ocrv/bin/python3" -m pip install -q --disable-pip-version-check rapidocr_onnxruntime >> "$O/venv.log" 2>&1
  fi
  if "$O/ocrv/bin/python3" -c "import rapidocr_onnxruntime" 2>/dev/null; then
    PY="$O/ocrv/bin/python3"; echo "S770: RapidOCR ready"
  else
    echo "S770: RapidOCR did not install -- $(tail -1 "$O/venv.log" | cut -c1-150)"
  fi
fi
S770_HELPER_PY=/root/wa/venv/bin/python3 nohup nice -n 15 ionice -c3 "$PY" -B "$O/probe_s770.py" > "$O/run.log" 2>&1 < /dev/null &
disown
echo "S770_PROBE: STARTED -- read-only; the report comes by mail in about 10 minutes"

#!/usr/bin/env python3
"""
followup_receiver.py  —  Gap A, Piece 1  (VPS "catcher")
--------------------------------------------------------
The ONLY job of this service: catch the Staff_Action_Today workbook that the
clinic-PC tracker app uploads, and drop it into the follow-up inbox folder.

Design rules honoured:
  - One service, one job (walled-off port 8100, own systemd unit).
  - Secret-protected: only a caller who knows FU_UPLOAD_SECRET may upload.
  - Accepts ONLY .xlsx (rejects everything else).
  - Writes into INBOX_DIR, atomically (temp file -> rename), never elsewhere.
  - No patient data is parsed or logged here; it only stores the file.
  - Read of secret comes from /root/wa/.env style env var, never hard-coded.

Endpoints:
  GET  /fu-ping     -> liveness check (no secret needed), returns "ok"
  POST /fu-upload   -> multipart form: field "file" (.xlsx) + header X-FU-Secret
"""
import os
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

INBOX_DIR = Path(os.environ.get("FU_INBOX_DIR", "/root/wa/followup-inbox"))
SECRET    = os.environ.get("FU_UPLOAD_SECRET", "")
MAX_MB    = 25  # a Staff_Action workbook is ~40 KB; 25 MB is a generous ceiling

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+\.xlsx$")


@app.route("/fu-ping", methods=["GET"])
def fu_ping():
    return "ok", 200


@app.route("/fu-upload", methods=["POST"])
def fu_upload():
    # 1) secret check
    if not SECRET or request.headers.get("X-FU-Secret", "") != SECRET:
        return jsonify(error="unauthorized"), 401

    # 2) file presence
    f = request.files.get("file")
    if f is None or f.filename == "":
        return jsonify(error="no file"), 400

    # 3) name / type check — only .xlsx, no path tricks
    name = os.path.basename(f.filename)
    if not _SAFE_NAME.match(name):
        return jsonify(error="only .xlsx filenames allowed"), 400

    # 4) atomic write: temp then rename
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    final = INBOX_DIR / name
    tmp   = INBOX_DIR / (name + ".part")
    f.save(str(tmp))
    os.replace(str(tmp), str(final))

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    size  = final.stat().st_size
    return jsonify(ok=True, stored=name, bytes=size, at=stamp), 200


if __name__ == "__main__":
    # Dev only. In production gunicorn serves this on 127.0.0.1:8100.
    app.run(host="127.0.0.1", port=8100)

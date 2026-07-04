#!/usr/bin/env python3
"""
push_to_vps.py  —  Gap A, Piece 3 helper (clinic PC side)
---------------------------------------------------------
One job: after the tracker generates the daily Staff_Action_Today workbook,
upload THAT file to the VPS catcher over HTTPS so the VPS can push it to the
Google Sheet on its own timer — no Windows watcher, no login dependency.

Safety:
  - NEVER raises. Any failure returns (False, "reason"); the caller logs it
    and carries on. Report generation can never be broken by an upload hiccup.
  - Secret is read from a local gitignored file 'fu_upload.env' sitting next
    to this script (KEY=VALUE line: FU_UPLOAD_SECRET=...). Never hard-coded.
  - Sends ONLY the one .xlsx workbook, nothing else.
"""
import os

VPS_URL = "https://followup.dr-manoj.in/fu-upload"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, "fu_upload.env")


def _read_secret():
    """Read FU_UPLOAD_SECRET from the local env file. Returns '' if missing."""
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("FU_UPLOAD_SECRET="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def upload_workbook(xlsx_path, timeout=30):
    """
    Upload one .xlsx workbook to the VPS catcher.
    Returns (ok: bool, message: str). Never raises.
    """
    try:
        import requests
    except Exception:
        return (False, "VPS upload skipped: 'requests' library not available.")

    if not xlsx_path or not os.path.exists(xlsx_path):
        return (False, "VPS upload skipped: workbook file not found.")

    secret = _read_secret()
    if not secret:
        return (False, "VPS upload skipped: no FU_UPLOAD_SECRET in fu_upload.env.")

    fname = os.path.basename(xlsx_path)
    try:
        with open(xlsx_path, "rb") as fh:
            resp = requests.post(
                VPS_URL,
                headers={"X-FU-Secret": secret},
                files={"file": (fname, fh,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                timeout=timeout,
            )
        if resp.status_code == 200:
            return (True, "Uploaded to VPS \u2713 (" + fname + ")")
        return (False, "VPS upload failed: HTTP %d" % resp.status_code)
    except Exception as e:
        return (False, "VPS upload error (non-fatal): %s" % e)


if __name__ == "__main__":
    # Manual test:  python push_to_vps.py <path-to-xlsx>
    import sys
    if len(sys.argv) < 2:
        print("usage: python push_to_vps.py <path-to-Staff_Action_Today.xlsx>")
        sys.exit(0)
    ok, msg = upload_workbook(sys.argv[1])
    print(("OK: " if ok else "FAIL: ") + msg)

#!/usr/bin/env python3
"""
sarvam_ocr.py  --  shared Sarvam Document AI helper (A-D16)

A single, dependency-isolated module reusable by ANY VPS app (the Asset Register,
the scanner app, and future apps). It wraps Sarvam's Document AI:
  - extract(path, schema)  -> schema-based key/value extraction  (bills, IDs, forms)
  - digitise(path)         -> full-document OCR text (markdown)

Design rules:
  * NEVER crash the caller. Missing SDK, missing key, or any API error returns
    (None, "skipped"|"failed") -- the host app keeps working, manual entry stays.
  * NO hardcoded HTTP endpoints -- the official `sarvamai` SDK owns the job
    lifecycle (create -> poll -> results). Endpoints can change server-side.
  * Config from the environment only:
        SARVAM_API_KEY   (required for any live call; absent => everything skips)
        SARVAM_LANGUAGE  (optional, default "en-IN")
  * Each importing app must `pip install sarvamai` in ITS OWN python.

Status vocabulary (matches the Asset Register's ocr_status column):
    done | failed | skipped
"""
import os
import json

API_KEY = os.environ.get("SARVAM_API_KEY", "").strip()
DEFAULT_LANGUAGE = os.environ.get("SARVAM_LANGUAGE", "en-IN").strip() or "en-IN"

# Formats Sarvam Document AI accepts.
OCR_EXT = {"pdf", "jpg", "jpeg", "png"}

# A-D17 v2: the clinic bill schema (assets + consumables superset).
# Passed to extract() as a JSON *string* (Sarvam requirement). Tune against real
# bills during live verification; unknown fields simply come back empty.
DEFAULT_BILL_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor":       {"type": "string", "description": "supplier / seller name"},
        "bill_no":      {"type": "string", "description": "invoice or bill number"},
        "bill_date":    {"type": "string", "description": "invoice date"},
        "total_amount": {"type": "number", "description": "grand total payable"},
        "items": {
            "type": "array",
            "description": "one entry per line item on the bill",
            "items": {
                "type": "object",
                "description": "a single line item",
                "properties": {
                    "item_name": {"type": "string", "description": "product / item name or description"},
                    "pack_size": {"type": "string", "description": "pack / unit size, e.g. '30 tests'"},
                    "quantity":  {"type": "number", "description": "quantity of packs / units"},
                    "rate":      {"type": "number", "description": "unit / pack rate"},
                    "amount":    {"type": "number", "description": "line total amount"},
                    "make":      {"type": "string", "description": "asset make / brand"},
                    "model":     {"type": "string", "description": "asset model"},
                    "serial_no": {"type": "string", "description": "asset serial number"},
                    "batch":     {"type": "string", "description": "consumable batch / lot number"},
                    "expiry":    {"type": "string", "description": "consumable expiry date"},
                    "hsn":       {"type": "string", "description": "HSN / SAC code"},
                },
            },
        },
    },
}

_TERMINAL_OK = {"completed", "partially_completed"}
_TERMINAL_BAD = {"failed", "rejected"}


def available():
    """True only if the SDK is importable AND a key is configured."""
    if not API_KEY:
        return False
    try:
        import sarvamai  # noqa: F401
    except Exception:
        return False
    return True


def _ext(path):
    return path.rsplit(".", 1)[1].lower() if "." in path else ""


def _client():
    from sarvamai import SarvamAI
    return SarvamAI(api_subscription_key=API_KEY)


def _file_arg(path):
    import mimetypes
    name = os.path.basename(path)
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(path, "rb") as fh:
        data = fh.read()
    return [(name, data, mime)]


def _run_job(start_call, get_results, timeout=180, poll=3):
    """Shared poll loop. start_call() -> response with .job_id; returns the
    results object on success or raises on terminal failure/timeout."""
    import time
    client, resp = start_call()
    job_id = getattr(resp, "job_id", None) or (resp.get("job_id") if isinstance(resp, dict) else None)
    if not job_id:
        raise RuntimeError("no job_id in start response")
    waited = 0
    status = getattr(resp, "status", None)
    while status not in _TERMINAL_OK and status not in _TERMINAL_BAD:
        if waited >= timeout:
            raise TimeoutError("doc_ai job %s timed out after %ss" % (job_id, timeout))
        time.sleep(poll)
        waited += poll
        status = client.doc_ai.get_status(job_id).status
    if status in _TERMINAL_BAD:
        raise RuntimeError("doc_ai job %s ended %s" % (job_id, status))
    return get_results(client, job_id)


def extract(path, schema=None, language=None, timeout=180, poll=3):
    """Schema-based extraction. Returns (data, status).
    data is the structured result (usually a dict) on success, else None."""
    if not available():
        return None, "skipped"
    if _ext(path) not in OCR_EXT or not os.path.exists(path):
        return None, "skipped"
    schema_json = json.dumps(schema if schema is not None else DEFAULT_BILL_SCHEMA)
    lang = language or DEFAULT_LANGUAGE

    def _start():
        client = _client()
        resp = client.doc_ai.extract(
            file=_file_arg(path), schema=schema_json,
            language=lang, output_format="json")
        return client, resp

    def _results(client, job_id):
        return client.doc_ai.get_results(job_id)

    try:
        res = _run_job(_start, _results, timeout=timeout, poll=poll)
        data = getattr(res, "result", None)
        if data is None and isinstance(res, dict):
            data = res.get("result")
        return data, ("done" if data is not None else "failed")
    except Exception:
        return None, "failed"


def digitise(path, language=None, output_format="md", timeout=180, poll=3):
    """Full-document OCR. Returns (text, status)."""
    if not available():
        return None, "skipped"
    if _ext(path) not in OCR_EXT or not os.path.exists(path):
        return None, "skipped"
    lang = language or DEFAULT_LANGUAGE

    def _start():
        client = _client()
        resp = client.doc_ai.digitise(
            file=_file_arg(path), language=lang, output_format=output_format)
        return client, resp

    def _results(client, job_id):
        return client.doc_ai.get_results(job_id)

    try:
        res = _run_job(_start, _results, timeout=timeout, poll=poll)
        docs = getattr(res, "documents", None)
        if docs is None and isinstance(res, dict):
            docs = res.get("documents")
        text = None
        if docs:
            parts = []
            for d in docs:
                t = getattr(d, "text", None) or (d.get("text") if isinstance(d, dict) else None)
                if t:
                    parts.append(t)
            text = "\n\n".join(parts) if parts else None
        return text, ("done" if text else "failed")
    except Exception:
        return None, "failed"

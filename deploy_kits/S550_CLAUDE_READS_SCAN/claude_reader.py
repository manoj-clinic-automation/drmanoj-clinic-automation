#!/usr/bin/env python3
"""claude_reader.py -- S550 (D723): Claude reads a scanned paper of the scan app.

The scan app's background reading (asset_register._bg_extract) asks this module first; when it answers nothing, Sarvam reads
as before. Standard library only (the service runs the system python3, F-53); Pillow is used only if present, to shrink a
large phone photo.

- The key: a root-only file outside the app folder (KEY_FILE), typed by the owner at a hidden prompt by the installer. The
  environment variable ANTHROPIC_API_KEY is used only when that file is absent. Never in the repository, a log, a page or
  the database.
- The switch: settings 'read.claude' -- 'on' (default once a key exists) / 'off' (the owner's tap) / 'stopped:<why>' (set
  here when the key is refused or the credit has run out; Sarvam reads from then on, by itself).
- Every reading is kept in claude_reading (one row per paper): only the listed fields, never a person's name (who a paper
  is made out to is kept as a kind -- clinic / doctor / patient / other -- never as a name). A later failure never replaces
  a good reading.
- A daily limit on CALLS (settings 'read.claude_daily_cap', default 400), counted per call in settings 'read.calls.<day>'.
"""
import base64, datetime as _dt, json, os, re, sqlite3, time, urllib.error, urllib.request

VERSION = "S550.2"
KEY_FILE = os.environ.get("SCANAPP_ANTHROPIC_KEY_FILE", "/root/.scanapp_secrets/anthropic.key")
API_URL = os.environ.get("SCANAPP_ANTHROPIC_URL", "https://api.anthropic.com/v1/messages")
MODELS = ("claude-sonnet-5-5", "claude-haiku-5-5")      # the first that exists is kept in settings 'read.claude_model'
MAX_BYTES = 23 * 1024 * 1024                              # under the 32 MB request limit once encoded
IMAGE_MAX = 3_700_000                                     # the API takes about 5 MB of photo once encoded
DAILY_CAP = 400
IMAGE_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
TIMEOUT = 120
MADE_OUT = ("clinic", "doctor", "patient", "other")

PROMPT = """You are reading ONE scanned paper received by a small orthopaedic clinic in Bareilly, India: a supplier's bill or tax
invoice, a delivery challan, a rough estimate slip (often handwritten), a quotation, or some other document. Read it carefully,
including handwriting. Return ONLY one JSON object, no prose, exactly these keys:

{"doc_kind": "tax_invoice" | "bill" | "estimate" | "challan" | "quotation" | "other",
 "vendor": the supplier's business name as printed (string or null),
 "vendor_phone": the supplier's phone from the header (string or null),
 "vendor_email": the supplier's email (string or null),
 "bill_no": the bill / invoice / challan / estimate number (string or null),
 "bill_date": the paper's own date as YYYY-MM-DD (Indian papers write day first: 05/10/26 is 2026-10-05; null if unreadable),
 "total_amount": the grand total payable in rupees as a number (null when the paper carries no amounts, as most challans),
 "made_out_to": "clinic" | "doctor" | "patient" | "other" | null  (who the paper is addressed to -- a KIND only, never a name),
 "handwritten": true or false,
 "items": [{"name": string, "qty": number or null, "unit": string or null, "rate": number or null, "amount": number or null,
            "make": string or null, "model": string or null, "serial": string or null, "batch": string or null,
            "expiry": "YYYY-MM-DD" or null, "hsn": string or null}]}

Rules: never guess -- use null for anything you cannot read. Numbers without commas or currency signs. One item per line of
goods; do not invent items. NEVER write any person's name anywhere in the answer (no patient, no doctor, no staff) --
"made_out_to" carries only the kind."""


# ---------------------------------------------------------------------------------------------- settings and the key
def _db(db_path):
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, "
                "ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
    con.commit()


def setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if r and r[0] is not None else default
    except sqlite3.Error:
        return default


def set_setting(con, key, value):
    con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))
    con.commit()


def _key():
    try:
        with open(KEY_FILE, encoding="utf-8") as fh:
            k = fh.read().strip()
            if k:
                return k
    except OSError:
        pass
    return (os.environ.get("ANTHROPIC_API_KEY") or "").strip()


def key_present():
    return bool(_key())


def state(con):
    """('on'|'off'|'stopped:<why>'|'no key'). 'on' is the default once a key exists."""
    if not key_present():
        return "no key"
    return (setting(con, "read.claude", "on") or "on").strip().lower()


def available(db_path):
    try:
        con = _db(db_path)
        try:
            return state(con) == "on"
        finally:
            con.close()
    except Exception:                                                # noqa: BLE001
        return False


def _day():
    return _dt.datetime.now().strftime("%Y-%m-%d")


def calls_today(con):
    try:
        return int(setting(con, "read.calls." + _day(), "0") or 0)
    except ValueError:
        return 0


readings_today = calls_today                                        # the owner's card shows calls made today


def cap(con):
    v = _num(setting(con, "read.claude_daily_cap", None))
    return DAILY_CAP if v is None else int(v)


def _count_call(con):
    k = "read.calls." + _day()
    con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?, '0')", (k,))
    con.execute("UPDATE settings SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT) WHERE key=?", (k,))
    con.commit()


# ---------------------------------------------------------------------------------------------- the call
def _post(body, key):
    """One HTTPS call to the Messages API. Returns (http_status, parsed_json_or_None, short_text). The walk replaces this.
    The text never carries an exception's own words (they could echo a header)."""
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            t = r.read().decode("utf-8", "replace")
            return r.status, json.loads(t), ""
    except urllib.error.HTTPError as e:
        t = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(t), ""
        except ValueError:
            return e.code, None, ""
    except Exception as e:                                           # noqa: BLE001
        return 0, None, type(e).__name__


def _smaller(raw, ext):
    """A phone photo over the API's image limit: made smaller with Pillow when the box has it; else returned as it is."""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((2400, 2400))
        out = io.BytesIO()
        for q in (85, 70, 55):
            out = io.BytesIO()
            im.save(out, "JPEG", quality=q)
            if out.tell() <= IMAGE_MAX:
                break
        return out.getvalue(), "jpg"
    except Exception:                                                # noqa: BLE001
        return raw, ext


def _block(path):
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    with open(path, "rb") as fh:
        raw = fh.read()
    if len(raw) > MAX_BYTES:
        return None, "file too large"
    if ext in IMAGE_TYPES and len(raw) > IMAGE_MAX:
        raw, ext = _smaller(raw, ext)
        if len(raw) > IMAGE_MAX:
            return None, "photo too large to send"
    data = base64.b64encode(raw).decode("ascii")
    if ext == "pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}}, None
    if ext in IMAGE_TYPES:
        return {"type": "image", "source": {"type": "base64", "media_type": IMAGE_TYPES[ext], "data": data}}, None
    return None, "not a PDF or a photo"


def _json_from(text):
    text = (text or "").strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        v = json.loads(m.group(0))
        return v if isinstance(v, dict) else None
    except ValueError:
        return None


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").replace("₹", "").replace("Rs", "").strip())
    except ValueError:
        return None


def _txt(v, n=200):
    if v is None or isinstance(v, (dict, list)):
        return None
    s = " ".join(str(v).split())[:n]
    return s or None


def _date(v):
    """YYYY-MM-DD, only a plausible one (2015 .. next year); else None."""
    s = str(v or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return None
    try:
        d = _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
    if d.year < 2015 or d.year > _dt.date.today().year + 1:
        return None
    return d.isoformat()


def clean(data):
    """Only the listed fields, each of its own type. A free-text note is never kept."""
    if not isinstance(data, dict):
        return None
    kind = _txt(data.get("doc_kind"), 20)
    mo = _txt(data.get("made_out_to"), 20)
    hw = data.get("handwritten")
    out = {"doc_kind": kind if kind in ("tax_invoice", "bill", "estimate", "challan", "quotation", "other") else None,
           "vendor": _txt(data.get("vendor")), "vendor_phone": _txt(data.get("vendor_phone"), 40),
           "vendor_email": _txt(data.get("vendor_email"), 80), "bill_no": _txt(data.get("bill_no"), 60),
           "bill_date": _date(data.get("bill_date")), "date_as_read": _txt(data.get("bill_date"), 20),
           "total_amount": _num(data.get("total_amount")), "made_out_to": mo if mo in MADE_OUT else None,
           "handwritten": hw if isinstance(hw, bool) else None, "items": []}
    for it in (data.get("items") if isinstance(data.get("items"), list) else []):
        if not isinstance(it, dict) or not _txt(it.get("name")):
            continue
        out["items"].append({"name": _txt(it.get("name")), "qty": _num(it.get("qty")), "unit": _txt(it.get("unit"), 30),
                             "rate": _num(it.get("rate")), "amount": _num(it.get("amount")), "make": _txt(it.get("make"), 80),
                             "model": _txt(it.get("model"), 80), "serial": _txt(it.get("serial"), 80),
                             "batch": _txt(it.get("batch"), 40), "expiry": _txt(it.get("expiry"), 20), "hsn": _txt(it.get("hsn"), 20)})
        if len(out["items"]) >= 200:
            break
    return out


def to_bill(data):
    """A reading in the shape asset_register._map_bill gives: (hdr, items)."""
    d = clean(data) or {}
    hdr = {k: d.get(k) for k in ("vendor", "vendor_phone", "vendor_email", "bill_no", "bill_date", "total_amount")}
    items = [{"name": it["name"], "qty": it["qty"], "pack": it["unit"], "rate": it["rate"], "amount": it["amount"],
              "make": it["make"], "model": it["model"], "serial": it["serial"], "batch": it["batch"], "expiry": it["expiry"],
              "hsn": it["hsn"]} for it in d.get("items", [])]
    return hdr, items


def _record(con, bid, model, ok, kind, data, error):
    """One row per paper. A failure never replaces a good reading."""
    if bid is None:
        return
    at = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ok:
        con.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data, error) VALUES(?,?,?,1,?,?,NULL)",
                    (bid, at, model, kind, json.dumps(data, ensure_ascii=False)))
    else:
        con.execute("INSERT OR IGNORE INTO claude_reading(bill_id, at, model, ok, error) VALUES(?,?,?,0,?)", (bid, at, model, error))
        con.execute("UPDATE claude_reading SET at=?, error=? WHERE bill_id=? AND ok=0", (at, error, bid))
    con.commit()


def read(path, bid=None, db_path=None):
    """Read one paper. Returns the cleaned reading (dict) or None. Records it. Never raises."""
    db_path = db_path or os.environ.get("ASSETS_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets.db")
    try:
        con = _db(db_path)
    except Exception:                                                # noqa: BLE001
        return None
    try:
        ensure(con)
        if state(con) != "on":
            return None
        blk, why = _block(path)
        if blk is None:
            _record(con, bid, None, False, None, None, why)
            return None
        key = _key()
        first = setting(con, "read.claude_model")
        models = ([first] if first in MODELS else []) + [m for m in MODELS if m != first]
        last_err, unavailable = "", 0
        for i, model in enumerate(models):
            body = {"model": model, "max_tokens": 8000,
                    "messages": [{"role": "user", "content": [blk, {"type": "text", "text": PROMPT}]}]}
            for attempt in range(3):
                if calls_today(con) >= cap(con):
                    _record(con, bid, None, False, None, None, "the day's limit reached")
                    return None
                _count_call(con)
                code, js, text = _post(body, key)
                if code == 200 and js:
                    if js.get("stop_reason") == "max_tokens":
                        _record(con, bid, model, False, None, None, "the paper is too long to read in one answer")
                        return None
                    out = "".join(c.get("text", "") for c in (js.get("content") or []) if isinstance(c, dict))
                    data = clean(_json_from(out))
                    if data is None:
                        last_err = "the answer was not readable"
                        break                                        # the next model
                    if unavailable == i and first != model:          # every model before this one does not exist: keep this one
                        set_setting(con, "read.claude_model", model)
                    _record(con, bid, model, True, data.get("doc_kind"), data, None)
                    return data
                err = js.get("error") if isinstance(js, dict) and isinstance(js.get("error"), dict) else {}
                low = ((err.get("message") or "") + " " + (err.get("type") or "")).lower()
                if code in (401, 403) or "authentication" in low or "permission" in low:
                    set_setting(con, "read.claude", "stopped:the key was refused")
                    _record(con, bid, model, False, None, None, "key refused")
                    return None
                if code == 402 or "credit" in low or "billing" in low or "balance" in low or "usage limit" in low:
                    set_setting(con, "read.claude", "stopped:the credit has run out")
                    _record(con, bid, model, False, None, None, "credit")
                    return None
                if code == 404 or (code == 400 and "model" in low):
                    last_err = "model %s not available" % model
                    unavailable += 1
                    break                                            # the next model
                if code in (429, 500, 502, 503, 529, 0):
                    last_err = "busy (%s)" % (code or text or "no answer")
                    time.sleep(3 * (attempt + 1))
                    continue
                _record(con, bid, model, False, None, None, "HTTP %s %s" % (code, (err.get("message") or "")[:120]))
                return None                                          # the paper itself was refused: not worth the next model
        _record(con, bid, None, False, None, None, last_err or "no answer")
        return None
    except Exception as e:                                           # noqa: BLE001
        try:
            _record(con, bid, None, False, None, None, type(e).__name__)
        except Exception:                                            # noqa: BLE001
            pass
        return None
    finally:
        con.close()


def read_bill(path, bid=None, db_path=None):
    """For _bg_extract: (hdr, items) when Claude read something useful, else None (Sarvam then reads)."""
    data = read(path, bid=bid, db_path=db_path)
    if not data:
        return None
    hdr, items = to_bill(data)
    if not (hdr.get("vendor") or hdr.get("total_amount") or items):
        return None
    return hdr, items


# ---------------------------------------------------------------------------------------------- the installer's live test
def _made_up_pdf():
    lines = ["MADE-UP TEST TRADERS", "Bill No: T-77    Date: 05/01/2026", "Cotton roll 500 g   Qty 2   Rate 50   Amount 100",
             "Total Rs 100"]
    y, ops = 760, []
    for ln in lines:
        ops.append("BT /F1 14 Tf 60 %d Td (%s) Tj ET" % (y, ln))
        y -= 30
    stream = "\n".join(ops).encode("latin-1")
    objs = [b"<</Type/Catalog/Pages 2 0 R>>", b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>",
            b"<</Length %d>>stream\n" % len(stream) + stream + b"\nendstream", b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    return out


def selftest(db_path, work_dir):
    """Read a made-up bill (no person, no real supplier) and say in one line whether Claude reads. Prints no key."""
    p = os.path.join(work_dir, "s550_selftest.pdf")
    with open(p, "wb") as fh:
        fh.write(_made_up_pdf())
    con = _db(db_path)
    try:
        ensure(con)
        if not key_present():
            return False, "no key stored"
        if state(con).startswith("stopped"):
            set_setting(con, "read.claude", "on")                    # a fresh install with a fresh key starts again
        if state(con) == "off":
            return False, "Claude is switched OFF on the admin card -- switch it ON there"
    finally:
        con.close()
    data = read(p, bid=None, db_path=db_path)
    con = _db(db_path)
    try:
        st, model = state(con), setting(con, "read.claude_model", "")
    finally:
        con.close()
    if data and "MADE-UP" in str(data.get("vendor") or "").upper():
        return True, "Claude read the made-up test bill (%s; total %s)" % (model or MODELS[0], data.get("total_amount"))
    return False, "Claude did not read the test bill (%s)" % st

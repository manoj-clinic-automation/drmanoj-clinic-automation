#!/usr/bin/env python3
"""claude_reader.py -- S550 (D723): Claude reads a scanned paper of the scan app.

The scan app's background reading (asset_register._bg_extract) asks this module first; when it answers nothing, Sarvam reads
as before. Standard library only (the service runs the system python3, F-53); a large phone photo is shrunk for the reader
with Pillow -- in this process when it imports, else the venv python's (TURN_PY), as turn_file does (S649, F-1003). The stored
scan is never changed; only the copy sent to the reader is smaller.

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

VERSION = "S550.3"   # S618: + check_scan / lie_pass (how each page lies; upright on the server) -- read() is unchanged
                     # S649 (F-1003): a photo over IMAGE_MAX is shrunk by the venv python when this one has no Pillow
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


def _refused_words(low):
    """F-1404 (S833): a refused key, named -- 'the key has expired' when the answer says so, else that it was refused (an
    expired or a revoked key reads the same). reader_watch.py tells the owner the words, at once."""
    return "the key has expired" if "expir" in (low or "") else "the key was refused (expired or revoked)"


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


_SMALL_SRC = ("import io, sys\n"
              "from PIL import Image\n"
              "lim = int(sys.argv[1])\n"
              "im = Image.open(io.BytesIO(sys.stdin.buffer.read())).convert('RGB')\n"
              "im.thumbnail((2400, 2400))\n"
              "out = io.BytesIO()\n"
              "for q in (85, 70, 55):\n"
              "    out = io.BytesIO()\n"
              "    im.save(out, 'JPEG', quality=q)\n"
              "    if out.tell() <= lim:\n"
              "        break\n"
              "sys.stdout.buffer.write(out.getvalue())\n")


def _smaller(raw, ext):
    """A phone photo over the API's image limit: made smaller with Pillow -- in this process when it imports, else with the
    venv python's (TURN_PY; S649, F-1003: the service python has no Pillow, and the photo used to go out whole and be refused).
    Returned as it is when neither can do it (the caller then says 'photo too large to send')."""
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
    except ImportError:
        pass                                                         # S649: no Pillow here -- the venv python's below
    except Exception:                                                # noqa: BLE001
        return raw, ext
    try:
        import subprocess as _sp                                     # noqa: PLC0415
        if os.path.exists(TURN_PY):
            r = _sp.run([TURN_PY, "-I", "-c", _SMALL_SRC, str(IMAGE_MAX)], input=raw, capture_output=True, timeout=90)
            if r.returncode == 0 and r.stdout[:3] == b"\xff\xd8\xff":
                return r.stdout, "jpg"
    except Exception:                                                # noqa: BLE001
        pass
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
                    set_setting(con, "read.claude", "stopped:" + _refused_words(low))
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


# ---------------------------------------------------------------------------------------------- S618: how each page lies, upright on the server
# Kit S618_SCAN_QUALITY (22-Oct-2026). After a pharmacy paper is read, a SHORT second question: which way the text of each page runs,
# whether the whole bill is in the scan, whether its total line shows, whether it can be read. Its own prompt and its own call path --
# never read()'s model loop or _record: it writes neither claude_reading nor settings 'read.claude_model'. Each call is counted by
# _count_call against cap(con). The answer is kept in scan_lie, keyed by the FILE checked (a merged page 2 is a new file: checked again).
# A page whose text does not run upright is turned by its /Rotate into a NEW file (the old one stays), set by compare-and-set.
CHECK_MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5")    # Haiku; Sonnet once when Haiku's answer cannot be read
CHECK_MAX_TOKENS = 4000                                      # the model thinks before it answers
TEXT_TOP = {"top": 0, "right": 270, "bottom": 180, "left": 90}   # the edge the top of the letters faces -> the CLOCKWISE turn that rights it
LIE_DDL = ("CREATE TABLE IF NOT EXISTS scan_lie(bill_id INTEGER NOT NULL, file TEXT NOT NULL, at TEXT, model TEXT, pages_json TEXT, "
           "whole_bill INTEGER, totals_visible INTEGER, legible INTEGER, note TEXT, blur_kept INTEGER, rotated_to TEXT, PRIMARY KEY(bill_id, file))")
TURN_PY = os.environ.get("S618_TURN_PY", "/root/wa/venv/bin/python3")      # has pypdf and Pillow (the service python has neither)
LIE_SKIP_SUBGROUPS = ("personal", "resume", "patient_paper")

CHECK_PROMPT = """You are checking ONE phone scan of a paper received by a pharmacy: a supplier's bill or tax invoice, a delivery challan, or something else. Do not copy the items. Judge only how the paper lies in the scan and whether the scan can be used. Return ONLY one JSON object, no prose:

{"pages": [{"text_top": "top" | "right" | "bottom" | "left"}],
 "whole_bill": true or false,
 "totals_visible": true or false,
 "legible": true or false,
 "note": "a few words, or empty"}

"pages": one entry for every page of the file, in order. "text_top" says which EDGE of the page, as you see it, the TOP of the printed letters points to:
  "top"    = the text reads normally, lines running left to right;
  "right"  = the page lies sideways and the lines run DOWN the page, top to bottom (the tops of the letters face the right edge);
  "left"   = the page lies sideways and the lines run UP the page, bottom to top (the tops of the letters face the left edge);
  "bottom" = the text is upside down.
"whole_bill": false ONLY when a part of the bill that matters is cut off by the edge of the scan: the top half with the supplier's heading, the item lines, the amounts column, or only a corner of the bill shown. A clipped margin, a few letters clipped at an edge, a hand or fingers over the footer, or a slight tilt do NOT count: then true.
"totals_visible": true when the bill's grand total / net amount line is inside the scan and can be read, or when the paper carries no amounts at all (as most challans); false when that line is cut off or hidden.
"legible": true when a person could read the item lines and their amounts; false when the scan is too blurred, smeared or dark to read them.
"note": what is wrong in a few words (never a name or a number), or "" when nothing is."""


def _pdf_pages(raw):
    """Pages of a PDF by its page objects (jsPDF and pypdf write them plainly); None when they are packed out of sight."""
    n = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", raw or b""))
    return n or None


def _bool01(v):
    return 1 if v is True else 0 if v is False else None


def _clean_lie(d, npages=None):
    """The check's answer, only its own fields: {pages: [{turn}], whole_bill, totals_visible, legible, note}; None when unusable."""
    if not isinstance(d, dict) or not isinstance(d.get("pages"), list):
        return None
    pages = []
    for p in d["pages"]:
        t = TEXT_TOP.get(str((p or {}).get("text_top") if isinstance(p, dict) else p).strip().lower())
        if t is None:
            return None
        pages.append({"turn": t})
    if not pages:
        return None
    if npages:
        pages = (pages + [{"turn": 0}] * npages)[:npages]       # a page the answer left out is left as it lies
    return {"pages": pages, "whole_bill": d.get("whole_bill") if isinstance(d.get("whole_bill"), bool) else None,
            "totals_visible": d.get("totals_visible") if isinstance(d.get("totals_visible"), bool) else None,
            "legible": d.get("legible") if isinstance(d.get("legible"), bool) else None, "note": _txt(d.get("note"), 160) or ""}


def check_scan(path, db_path=None):
    """S618: how each page of one scan lies. {pages: [{turn: 0|90|180|270}], whole_bill, totals_visible, legible, note, model} or None.
    Its own call path: Haiku, Sonnet once when the answer cannot be read; 429 / 5xx tried again as read() does; every call counted
    against cap(con). Never records a reading, never changes a setting. Never raises."""
    db_path = db_path or os.environ.get("ASSETS_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets.db")
    try:
        con = _db(db_path)
    except Exception:                                                # noqa: BLE001
        return None
    try:
        if state(con) != "on":
            return None
        blk, why = _block(path)
        if blk is None:
            return None
        npages = None
        if path.lower().endswith(".pdf"):
            with open(path, "rb") as fh:
                npages = _pdf_pages(fh.read())
        key = _key()
        for model in CHECK_MODELS:
            body = {"model": model, "max_tokens": CHECK_MAX_TOKENS,
                    "messages": [{"role": "user", "content": [blk, {"type": "text", "text": CHECK_PROMPT}]}]}
            for attempt in range(3):
                if calls_today(con) >= cap(con):
                    return None
                _count_call(con)
                code, js, text = _post(body, key)
                if code == 200 and js:
                    out = "".join(c.get("text", "") for c in (js.get("content") or []) if isinstance(c, dict) and c.get("type") == "text")
                    d = _clean_lie(_json_from(out), npages)
                    if d is None:
                        break                                    # Sonnet, once
                    d["model"] = model
                    return d
                if code in (429, 500, 502, 503, 529, 0):
                    time.sleep(3 * (attempt + 1))
                    continue
                err = js.get("error") if isinstance(js, dict) and isinstance(js.get("error"), dict) else {}
                if code == 404 or (code == 400 and "model" in ((err.get("message") or "") + " " + (err.get("type") or "")).lower()):
                    break                                        # this model is not there: the next one
                return None                                      # refused (key, credit, the paper): no second model for a refusal
        return None
    except Exception:                                                # noqa: BLE001
        return None
    finally:
        con.close()


_TURN_SRC = ("import sys\n"
             "dst, src, turns = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]\n"
             "if src.lower().endswith('.pdf'):\n"
             "    from pypdf import PdfReader, PdfWriter\n"
             "    w = PdfWriter()\n"
             "    for i, p in enumerate(PdfReader(src).pages):\n"
             "        t = turns[i] if i < len(turns) else 0\n"
             "        if t:\n"
             "            p.rotate(t)\n"
             "        w.add_page(p)\n"
             "    w.write(open(dst, 'wb'))\n"
             "else:\n"
             "    from PIL import Image\n"
             "    im = Image.open(src)\n"
             "    fmt = im.format or 'JPEG'\n"
             "    im.rotate(-turns[0], expand=True).save(dst, fmt, quality=92)\n")


def turn_file(upload_dir, stored, turns):
    """The scan with each page turned CLOCKWISE by its turn, as a NEW stored file 'bill_<hex>_u.<ext>' (the old file stays).
    A PDF by its pages' /Rotate (lossless), a photo with Pillow -- in this process when they import, else the venv python's.
    Returns the new name, or None when it cannot be done."""
    if not stored or not any(turns or []):
        return None
    stem, ext = os.path.splitext(stored)
    ext = ext.lower()
    if ext not in (".pdf", ".jpg", ".jpeg", ".png"):
        return None
    name, k = "%s_u%s" % (stem, ext), 1
    while os.path.exists(os.path.join(upload_dir, name)):
        k += 1
        name = "%s_u%d%s" % (stem, k, ext)
    src, dst = os.path.join(upload_dir, stored), os.path.join(upload_dir, name)
    arg = ",".join(str(int(t)) for t in turns)
    try:
        if ext == ".pdf":
            from pypdf import PdfReader, PdfWriter                   # noqa: PLC0415
            w = PdfWriter()
            for i, p in enumerate(PdfReader(src).pages):
                t = turns[i] if i < len(turns) else 0
                if t:
                    p.rotate(t)
                w.add_page(p)
            with open(dst, "wb") as fh:
                w.write(fh)
        else:
            from PIL import Image                                    # noqa: PLC0415
            im = Image.open(src)
            im.rotate(-turns[0], expand=True).save(dst, im.format or "JPEG", quality=92)
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            return name
    except ImportError:
        pass
    except Exception:                                                # noqa: BLE001
        _rm(dst)
        return None
    try:
        import subprocess as _sp                                     # noqa: PLC0415
        if os.path.exists(TURN_PY):
            r = _sp.run([TURN_PY, "-c", _TURN_SRC, dst, src, arg], capture_output=True, timeout=90)
            if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0:
                return name
    except Exception:                                                # noqa: BLE001
        pass
    _rm(dst)
    return None


def _rm(p):
    try:
        if p and os.path.exists(p):
            os.remove(p)
    except OSError:
        pass


def _lie_audit(con, bid, who, action, detail):
    con.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
                (bid, _dt.datetime.now().strftime("%Y-%m-%d %H:%M"), who, action, json.dumps(detail or {}, ensure_ascii=False)[:500]))


def lie_pass(db_path, upload_dir, bid, who="server (S618 upright)"):
    """S618: check one pharmacy scan's CURRENT file and turn it upright. Guarded here, at the moment of the call: lane 'pharmacy', not set
    aside, not a joined page, not a person's paper, no check of this file yet (scan_lie). The new file is set by compare-and-set
    (UPDATE ... WHERE source_stored=<the file checked>); when a join changed the file meanwhile, the current file is checked and turned
    instead (once more), else the turn is audited and skipped. Returns a word: turned / checked / skipped:<why> / failed. Never raises."""
    try:
        con = _db(db_path)
    except Exception:                                                # noqa: BLE001
        return "failed"
    try:
        con.execute(LIE_DDL)
        con.commit()
        for _attempt in (1, 2):
            b = con.execute("SELECT id, lane, status, page_of, source_stored, subgroup FROM bills WHERE id=?", (bid,)).fetchone()
            if not b:
                return "skipped:no bill"
            if (b["lane"] or "") != "pharmacy":
                return "skipped:lane"
            if (b["status"] or "") == "rejected" or b["page_of"]:
                return "skipped:set aside"
            if (b["subgroup"] or "") in LIE_SKIP_SUBGROUPS or not b["source_stored"]:
                return "skipped:not asked"
            f = b["source_stored"]
            r = con.execute("SELECT model FROM scan_lie WHERE bill_id=? AND file=?", (bid, f)).fetchone()
            if r and r["model"]:
                return "skipped:checked"
            res = check_scan(os.path.join(upload_dir, f), db_path=db_path)
            if res is None:
                return "failed"
            at = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            vals = (at, res["model"], json.dumps(res["pages"]), _bool01(res["whole_bill"]), _bool01(res["totals_visible"]),
                    _bool01(res["legible"]), res["note"])
            con.execute("INSERT OR IGNORE INTO scan_lie(bill_id, file) VALUES(?,?)", (bid, f))
            con.execute("UPDATE scan_lie SET at=?, model=?, pages_json=?, whole_bill=?, totals_visible=?, legible=?, note=? WHERE bill_id=? AND file=?",
                        vals + (bid, f))
            con.commit()
            turns = [p["turn"] for p in res["pages"]]
            if not any(turns):
                return "checked"
            new = turn_file(upload_dir, f, turns)
            if not new:
                _lie_audit(con, bid, who, "upright_failed", {"pages": turns, "file": f})
                con.commit()
                return "checked"
            cur = con.execute("UPDATE bills SET source_stored=? WHERE id=? AND source_stored=?", (new, bid, f))
            if cur.rowcount == 1:
                bk = con.execute("SELECT blur_kept FROM scan_lie WHERE bill_id=? AND file=?", (bid, f)).fetchone()
                con.execute("UPDATE scan_lie SET rotated_to=? WHERE bill_id=? AND file=?", (new, bid, f))
                con.execute("INSERT OR IGNORE INTO scan_lie(bill_id, file, at, model, pages_json, whole_bill, totals_visible, legible, note, blur_kept) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?)", (bid, new, at, "upright copy of " + f, json.dumps([{"turn": 0} for _t in turns]),
                                                          vals[3], vals[4], vals[5], vals[6], bk["blur_kept"] if bk else None))
                _lie_audit(con, bid, who, "upright", {"pages": turns, "from": f, "to": new})
                con.commit()
                return "turned"
            con.rollback()
            _lie_audit(con, bid, who, "upright_raced", {"pages": turns, "checked": f, "kept": new})
            con.commit()
        return "skipped:raced"
    except Exception:                                                # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                            # noqa: BLE001
            pass
        return "failed"
    finally:
        con.close()


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


# ---- S750 (08-Nov-2026, the Sanjeevni chat's session 406, kit S750_MONTH_END; PLANNED on board/_numbers v1066, the Scan App chat told at the close) ----
#  A dealer's MONTH SUMMARY on the pharmacy lane (D849 / F-1175): the intake's 'summary' tick lands the scan as kind='Summary',
#  doc_kind='summary'; this reader reads it as a summary, never as a bill -- every bill line it lists (number, date, amount), every
#  credit note or payment line, the period and the closing total -- and records it in claude_reading with doc_kind='summary'.
#  read_summary() is called where read_bill() is called today, for kind='Summary' only (asset_register, S750). Nothing else changes:
#  read(), clean(), to_bill() and the bill prompt are untouched; a summary reading never writes vendor / bill_no / total onto the bills row
#  by to_bill() (the finance side reads claude_reading itself); summary_to_bill() lends only the dealer's name and figure. No person's name is asked for or kept.

SUMMARY_PROMPT = """You are reading ONE scanned paper received by a small pharmacy in Bareilly, India: a supplier's (dealer's) MONTHLY
SUMMARY of what the pharmacy bought from them -- also called a statement of account, ledger, outstanding statement or bill list. It lists
the bills (invoices) of a period with their dates and amounts, sometimes credit notes, purchase returns or payments received, and a total
or closing balance. Read it carefully, including handwriting. Return ONLY one JSON object, no prose, exactly these keys:

{"is_summary": true or false  (false when the paper is a single bill, a challan or something else -- then leave the rest null),
 "dealer": the supplier's business name as printed (string or null),
 "period_from": "YYYY-MM-DD" or null, "period_to": "YYYY-MM-DD" or null  (Indian papers write day first: 05/10/26 is 2026-10-05),
 "lines": [{"kind": "bill" | "credit" | "payment" | "other",
            "no": the bill / credit note / reference number as printed (string or null),
            "date": "YYYY-MM-DD" or null,
            "amount": the line's amount in rupees as a positive number (null if unreadable)}],
 "total_bills": the sum of the bills as printed (number or null),
 "closing": the closing balance / total payable as printed (number or null),
 "opening": any opening balance carried in (number or null),
 "handwritten": true or false}

Rules: one entry per printed line; never invent a line and never add lines up yourself -- copy the printed totals; numbers without commas or
currency signs; use null for anything you cannot read; a line that reduces what is owed (a credit note, a return, a payment, 'by cash',
'by NEFT', 'Cr') is kind 'credit' or 'payment', a bill ('Dr', 'invoice', 'sale') is kind 'bill'. NEVER write any person's name anywhere in
the answer (no owner, no staff, no customer) -- the dealer's business name only."""

SUMMARY_KINDS = ("bill", "credit", "payment", "other")


def clean_summary(data):
    """Only the listed fields, each of its own type; at most 400 lines. A free-text note is never kept."""
    if not isinstance(data, dict):
        return None
    hw = data.get("handwritten")
    iss = data.get("is_summary")
    out = {"doc_kind": "summary", "is_summary": iss if isinstance(iss, bool) else None, "dealer": _txt(data.get("dealer")),
           "period_from": _date(data.get("period_from")), "period_to": _date(data.get("period_to")),
           "total_bills": _num(data.get("total_bills")), "closing": _num(data.get("closing")), "opening": _num(data.get("opening")),
           "handwritten": hw if isinstance(hw, bool) else None, "lines": []}
    for ln in (data.get("lines") if isinstance(data.get("lines"), list) else []):
        if not isinstance(ln, dict):
            continue
        k = _txt(ln.get("kind"), 12)
        amt = _num(ln.get("amount"))
        if amt is not None:
            amt = abs(amt)
        out["lines"].append({"kind": k if k in SUMMARY_KINDS else "other", "no": _txt(ln.get("no"), 60), "date": _date(ln.get("date")),
                             "date_as_read": _txt(ln.get("date"), 20), "amount": amt})
        if len(out["lines"]) >= 400:
            break
    return out


def read_summary(path, bid=None, db_path=None):
    """Read one paper as a dealer's month summary. Returns the cleaned reading (dict, doc_kind 'summary') or None. Records it in
    claude_reading exactly as read() records a bill (the same key, state, cap, models, retries). Never raises."""
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
                    "messages": [{"role": "user", "content": [blk, {"type": "text", "text": SUMMARY_PROMPT}]}]}
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
                    data = clean_summary(_json_from(out))
                    if data is None:
                        last_err = "the answer was not readable"
                        break                                        # the next model
                    if unavailable == i and first != model:
                        set_setting(con, "read.claude_model", model)
                    _record(con, bid, model, True, "summary", data, None)
                    return data
                err = js.get("error") if isinstance(js, dict) and isinstance(js.get("error"), dict) else {}
                low = ((err.get("message") or "") + " " + (err.get("type") or "")).lower()
                if code in (401, 403) or "authentication" in low or "permission" in low:
                    set_setting(con, "read.claude", "stopped:" + _refused_words(low))
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
                return None
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


def summary_to_bill(data):
    """What a summary reading lends the bills row (asset_register S750): the dealer's name and its figure -- no items, no bill number."""
    d = data or {}
    fig = d.get("closing") if d.get("closing") is not None else d.get("total_bills")
    return {"vendor": d.get("dealer"), "vendor_phone": None, "vendor_email": None, "bill_no": None, "bill_date": d.get("period_to"), "total_amount": fig}, []
# ---- S750 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S754 (08-Nov-2026, the Scan App chat's session 409, kit S754_SUMMARY_RECOGNISE; PLANNED on board/_numbers v1088) ----
#  THE OWNER (17:27 IST 08-Nov, superseding D870's 'staff rescan it'): staff scan a dealer's month summary on the pharmacy lane like any
#  bill -- tick or no tick; the system recognises it. Four things, all in this appended section (nothing above it is edited):
#  1. read_pharmacy(): the ONE call for a pharmacy-lane paper scanned without a tick. The bill prompt with one more paragraph: decide
#     first whether the paper is a dealer's statement; a statement is answered in the summary shape, a bill in the bill shape. The
#     reading is recorded as read() / read_summary() record theirs (claude_reading, doc_kind 'summary' for a statement).
#  2. The dealer is the SELLER on the letterhead, never the buyer (Sanjeevni Medicos, the pharmacy itself, in any spelling): the prompt
#     says so, and clean_summary() drops a buyer's name to null by the S439 rule (copied in from scan_checks_s441.is_buyer).
#  3. The period from the bills: an 'as on' / printing date is not the period. When the period is missing, a single day or the 'as on'
#     date, the period is the month most of the listed bills fall in (first to last day); the read period is kept beside it. A printed
#     period is kept as printed. summary_to_bill() then lends that last day as bill_date (unchanged code).
#  4. Keys only added to the reading, none renamed or dropped: continued, as_on, period_by ('paper' | 'bills'), period_from_as_read,
#     period_to_as_read, dealer_was_buyer, recognised (true when read_pharmacy found the statement, no tick).
#  read(), clean(), to_bill(), read_bill(), read_summary(), summary_to_bill() and the bill PROMPT are untouched; SUMMARY_PROMPT and
#  clean_summary are re-bound here (read_summary() reads both names when it is called).
import difflib as _s754_difflib

KIT_S754 = "S754_SUMMARY_RECOGNISE"

S754_SELLER_RULE = """The dealer is the SELLER: the business whose name is printed on the letterhead at the top, who sends the statement. The
paper is made out TO the pharmacy, Sanjeevni Medicos (also spelt Sanjeevni Medicose, Sanjivani, Sanjeevani) -- that is the BUYER: never give
it as the dealer, in any spelling. When no seller's name is printed, "dealer" is null."""

S754_PERIOD_RULE = """"period_from" / "period_to" are the period the statement covers, as printed. A printing date or an 'as on' date is NOT
the period: put it in "as_on" and leave the period null unless a period is printed."""

S754_EXTRA_KEYS = """ "as_on": the 'as on' / printing date as "YYYY-MM-DD" or null,
 "continued": true when this page carries no heading, no seller letterhead and no buyer block -- it only continues a table from an earlier
 page; otherwise false,"""

SUMMARY_PROMPT = SUMMARY_PROMPT + "\n\nAlso, two more keys in the same object:\n{" + S754_EXTRA_KEYS.rstrip(",") + "}\n\n" + S754_SELLER_RULE + "\n" + S754_PERIOD_RULE

PHARMACY_PROMPT = PROMPT + """

THIS PAPER CAME IN ON THE PHARMACY LANE, so it may instead be a dealer's STATEMENT. Decide that FIRST.
A STATEMENT lists SEVERAL bills (invoices) of a period, each with its own bill number, date and amount, under a heading such as statement,
statement of account, sales statement, due list, sales book, ledger, transaction register, outstanding or bill list, with a period or an
'as on' date and a total or closing balance. A single bill or tax invoice -- ONE bill number, item lines with quantity and rate -- is never a
statement, even when it also shows earlier dues.
- A single bill, invoice, challan or anything else: answer in the shape above, with one more key, "is_summary": false.
- A STATEMENT: do NOT answer in the shape above. Answer instead with ONLY this JSON object:
{"is_summary": true,
 "dealer": the seller's business name as printed (string or null),
 "period_from": "YYYY-MM-DD" or null, "period_to": "YYYY-MM-DD" or null  (Indian papers write day first: 05/10/26 is 2026-10-05),
""" + S754_EXTRA_KEYS + """
 "lines": [{"kind": "bill" | "credit" | "payment" | "other",
            "no": the bill / credit note / reference number as printed (string or null),
            "date": "YYYY-MM-DD" or null,
            "amount": the line's amount in rupees as a positive number (null if unreadable)}],
 "total_bills": the sum of the bills as printed (number or null),
 "closing": the closing balance / total payable as printed (number or null),
 "opening": any opening balance carried in (number or null),
 "handwritten": true or false}
For a statement: one entry per printed line; never invent a line and never add lines up yourself -- copy the printed totals; a line that
reduces what is owed (a credit note, a return, a payment, 'by cash', 'by NEFT', 'Cr') is kind 'credit' or 'payment', a bill ('Dr',
'invoice', 'sale') is kind 'bill'.
""" + S754_SELLER_RULE + "\n" + S754_PERIOD_RULE + """
NEVER write any person's name anywhere in the answer (no owner, no staff, no customer, no patient)."""

# the S439 buyer rule, copied in (scan_checks_s441.is_buyer = purchase_app._is_buyer_s439), so the reader and the two checks agree
_S754_STOP = frozenset(("PVT", "PRIVATE", "LTD", "LIMITED", "MS", "PL", "EXTN", "EXT", "AND", "CO", "THE",
                        "BAREILLY", "BAREILL", "BAREIL", "BAREI"))
_S754_TRADE = ("PHARMACEUTICALS", "PHARMACEUTICAL", "PHARMA", "MEDICAL", "MEDICALS", "MEDICOS", "MEDICOSE", "AGENCIES",
               "AGENCY", "SURGICALS", "SURGICAL", "FORMULATIONS", "DISTRIBUTORS", "ENTERPRISES", "TRADERS", "SCIENTIFIC",
               "CHEMIST", "DRUGGIST", "DRUG", "HOUSE", "CENTRE", "AID", "WHOLE", "SALE", "WHOLESALE", "BROS", "STORES",
               "HEALTHCARE")
_S754_BUYER = ("SANJEEVNI", "SANJEEVANI", "SANJIVANI")
_S754_CITY_TAILS = ("BAREILLY", "BAREILL", "BAREIL", "BAREI", "BARE", "BAR", "BA")


def _s754_sim(a, b):
    if a == b:
        return 1.0
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a)):
        return 0.9
    return _s754_difflib.SequenceMatcher(None, a, b).ratio()


def _s754_trade(w):
    return (w in _S754_TRADE) or any(_s754_sim(w, g) >= 0.85 for g in _S754_TRADE)


def _s754_tokens(s):
    t = re.sub(r"\bM\s*/\s*S\b\.?", " ", str(s or "").upper())
    out, run = [], ""
    for w in re.findall(r"[A-Z]+", t):
        if len(w) == 1:
            run += w
            continue
        if len(run) > 1:
            out.append(run)
        run = ""
        out.append(w)
    if len(run) > 1:
        out.append(run)
    while len(out) > 1 and out[-1] in _S754_CITY_TAILS:
        out.pop()
    return [w for w in out if w not in _S754_STOP]


def is_buyer_name(name):
    """True when a name read as the dealer is the pharmacy itself (the buyer), by the S439 rule."""
    toks = _s754_tokens(name)
    if not toks:
        return False
    for t in toks:
        if t.startswith(("SANJEEV", "SANJIV", "SANJEV")) or max(_s754_sim(t, x) for x in _S754_BUYER) >= 0.8:
            return True
    return (not [t for t in toks if not _s754_trade(t)]) and any(t.startswith("MEDICOS") for t in toks)


def _s754_month_end(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    nxt = _dt.date(y + (m == 12), (m % 12) + 1, 1)
    return (nxt - _dt.timedelta(days=1)).isoformat()


def _s754_period(out):
    """The period from the bills (in place). The month most of the listed bills fall in (a tie: the later month); bill lines first,
    any dated line when no bill line is dated. Taken when the read period is missing, one day, or the 'as on' date; a printed
    period is kept. period_by says which: 'paper' (as read) or 'bills'."""
    dated = [ln["date"] for ln in out.get("lines") or [] if ln.get("kind") == "bill" and ln.get("date")]
    if not dated:
        dated = [ln["date"] for ln in out.get("lines") or [] if ln.get("date")]
    pf, pt = out.get("period_from"), out.get("period_to")
    if not dated:
        out["period_by"] = "paper" if (pf or pt) else None
        return out
    count = {}
    for d in dated:
        count[d[:7]] = count.get(d[:7], 0) + 1
    top = max(count.items(), key=lambda kv: (kv[1], kv[0]))[0]
    need = (pf is None or pt is None or pf == pt or bool(out.get("as_on") and pt == out.get("as_on")))
    if not need:
        out["period_by"] = "paper"
        return out
    out["period_from_as_read"], out["period_to_as_read"] = pf, pt
    out["period_from"], out["period_to"] = top + "-01", _s754_month_end(top)
    out["period_by"] = "bills"
    return out


_clean_summary_before_s754 = clean_summary


def clean_summary(data):                                             # noqa: F811 -- S754: the seller only; the period from the bills
    out = _clean_summary_before_s754(data)
    if out is None:
        return None
    c = data.get("continued")
    out["continued"] = c if isinstance(c, bool) else None
    out["as_on"] = _date(data.get("as_on"))
    if out.get("dealer") and is_buyer_name(out["dealer"]):
        out["dealer"] = None                                         # the buyer's name is never the dealer; the Sanjeevni side finds it from the bills
        out["dealer_was_buyer"] = True
    try:
        _s754_period(out)
    except Exception:                                                # noqa: BLE001 -- the period stays as read
        pass
    return out


def clean_pharmacy(data):
    """The combined answer: a statement -> clean_summary (+ recognised); anything else -> clean() (the bill reading, as before)."""
    if not isinstance(data, dict):
        return None
    if data.get("is_summary") is True:
        out = clean_summary(data)
        if out is not None:
            out["is_summary"] = True
            out["recognised"] = True
        return out
    return clean(data)


def read_pharmacy(path, bid=None, db_path=None):
    """S754: ONE call for a pharmacy-lane paper scanned without a tick. Returns the cleaned reading -- a summary (doc_kind 'summary',
    is_summary true, recognised true) or a bill (as read() returns) -- or None. Recorded in claude_reading exactly as read() and
    read_summary() record theirs (the same key, state, daily cap, models, retries). Never raises."""
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
                    "messages": [{"role": "user", "content": [blk, {"type": "text", "text": PHARMACY_PROMPT}]}]}
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
                    data = clean_pharmacy(_json_from(out))
                    if data is None:
                        last_err = "the answer was not readable"
                        break                                        # the next model
                    if unavailable == i and first != model:
                        set_setting(con, "read.claude_model", model)
                    _record(con, bid, model, True, data.get("doc_kind"), data, None)
                    return data
                err = js.get("error") if isinstance(js, dict) and isinstance(js.get("error"), dict) else {}
                low = ((err.get("message") or "") + " " + (err.get("type") or "")).lower()
                if code in (401, 403) or "authentication" in low or "permission" in low:
                    set_setting(con, "read.claude", "stopped:" + _refused_words(low))
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
                return None
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
# ---- S754 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S783 (11-Nov-2026, Sanjeevni session 426, kit S783_SCAN_LINE_EXTRAS; the owner's word 05:51 IST: "Add the scanner lines") ------
#  A pharmacy-lane bill read by read_pharmacy() gives four more figures on each item line -- free goods, MRP, discount (%) and GST (%) --
#  so the Purchase bills page (finance provisional_s781) shows them beside the line. Only PHARMACY_PROMPT asks for them, and only
#  clean_pharmacy() keeps them (numbers or null) on a bill's items in claude_reading.data. read(), PROMPT, clean(), to_bill(), bill_items,
#  dealer statements, challans and claude_reread's re-reads are unchanged (they never carry the four figures).
#  The longer answer: a pharmacy reading may use up to S783_MAX_TOKENS; if a very long bill still runs out, it is asked once more with
#  the prompt as it was before S783 -- so no bill that read before S783 fails because of it.
#  Papers already read are not read again. Planned on the board (D646) by the Sanjeevni chat; the Scan App chat owns this file.
S783_ITEM_KEYS = ("free", "mrp", "discount", "gst")
S783_MAX_TOKENS = 16000
_S783_PROMPT_BEFORE = PHARMACY_PROMPT
PHARMACY_PROMPT = PHARMACY_PROMPT + """

For a single bill (not a statement), give each item four more keys, read from that line of the bill:
 "free": the free quantity given on the line (number or null), "mrp": the MRP per unit in rupees (number or null),
 "discount": the line's discount in percent (number or null), "gst": the line's GST rate in percent, CGST and SGST added (number or null).
Numbers only, no % sign. Never guess -- null for any you cannot read on that line."""


def _s783_num(v):
    if isinstance(v, str):
        v = v.replace("%", "").strip()
    return _num(v)


_clean_pharmacy_before_s783 = clean_pharmacy


def clean_pharmacy(data):                                            # noqa: F811 -- S783: + free / mrp / discount / gst on a bill's items
    out = _clean_pharmacy_before_s783(data)
    if not out or not isinstance(data, dict) or out.get("doc_kind") == "summary" or out.get("is_summary"):
        return out
    raw = [it for it in (data.get("items") if isinstance(data.get("items"), list) else []) if isinstance(it, dict) and _txt(it.get("name"))]
    for it, src in zip(out.get("items") or [], raw):                 # the same order and filter as clean() itself
        for k in S783_ITEM_KEYS:
            it[k] = _s783_num(src.get(k))
    return out


_post_before_s783 = _post


def _s783_with_prompt(body, text, max_tokens):
    msgs = []
    for m in body.get("messages") or []:
        content = []
        for c in m.get("content") or []:
            content.append(dict(c, text=text) if isinstance(c, dict) and c.get("type") == "text" and c.get("text") == PHARMACY_PROMPT else c)
        msgs.append(dict(m, content=content))
    return dict(body, messages=msgs, max_tokens=max_tokens)


def _post(body, key):                                                # noqa: F811 -- S783: the pharmacy reading's longer answer
    try:
        is_ph = any(isinstance(c, dict) and c.get("text") == PHARMACY_PROMPT for m in (body.get("messages") or []) for c in (m.get("content") or []))
    except Exception:                                                # noqa: BLE001
        is_ph = False
    if not is_ph:
        return _post_before_s783(body, key)
    code, js, text = _post_before_s783(_s783_with_prompt(body, PHARMACY_PROMPT, max(int(body.get("max_tokens") or 0), S783_MAX_TOKENS)), key)
    if code == 200 and isinstance(js, dict) and js.get("stop_reason") == "max_tokens":
        return _post_before_s783(_s783_with_prompt(body, _S783_PROMPT_BEFORE, max(int(body.get("max_tokens") or 0), S783_MAX_TOKENS)), key)
    return code, js, text
# ---- S783 end -------------------------------------------------------------------------------------------------------------------------

#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""scan_checks_s441.py -- kit S441_SCAN_RATE (session 287, 01-Oct-2026, D643 · F-666 · F-667). Lives in /root/shared:
the asset app (the scanning side) and the finance app (Purchase orders, "Scan ka kaam") both import it.

THE OWNER, 01-Oct-2026: staff never wait and never answer questions while scanning. The server checks AFTER the fact:
  * a FORGOTTEN PAGE is joined to its bill by itself -- the same person, within a few minutes, the same bill number (or a
    page with no bill header at all), and a page that does not look like the one before it. Both stamps resolve to the bill.
  * a SURE DOUBLE SCAN is set aside by itself -- the same supplier, the same bill-number digit tail and the amount within
    2%. The paper is kept (status 'rejected' + dup_of, exactly what S409's guard writes), never deleted, and so stays out
    of every count and every pack.
  * a NEAR MATCH, or a LIKELY WRONG LANE (a known pharmacy supplier scanned in the clinic lane), becomes ONE question on
    the existing "Scan ka kaam" list (Purchase orders), which Shavez AND reception both see. The first answer settles it,
    and who answered is shown.
  * the shared "Reception" login says once per sitting who is working (WHO_JS below); every stamp, order sent and
    arrival marked then carries that name.

THE RULES ARE S439's, COPIED IN, NOT IMPORTED. _bill_tails / _vendor_sim below are purchase_app._bill_tails_s439 and
purchase_app._vendor_sim_s439 with their constants, byte-for-byte in behaviour; the kit's walk holds the two against each
other over every vendor name and bill number on the box. Importing purchase_app (6,000 lines, a Flask blueprint, the
finance app's whole import tree) into the asset app's process is the risk this avoids -- the S313 precedent.

ONE WRITER PER DATABASE. Everything that writes assets.db here is called by the asset app (after each OCR read, on the
intake page, from its answer route, and by the installer's first pass). The finance app only READS the questions.

Standard library only. No patient name, no number, no secret (F-185).
"""
import datetime as _dt
import difflib as _difflib
import json as _json
import os as _os
import re as _re
import sqlite3 as _sqlite3

VERSION = "S441.1"

# ------------------------------------------------------------------ the shared Reception login: who is working
WHO_SHARED_LOGINS = ("reception",)
WHO_NAMES = (("shivani", "Shivani"), ("alisha", "Alisha"), ("darpan", "Darpan"), ("sukhveer", "Sukhveer"), ("shavez", "Shavez"))
WHO_COOKIE = "clinic_who"
WHO_IDLE_SECONDS = 1800          # "remembered until 30 minutes idle"


def is_shared_login(username):
    return str(username or "").strip().lower() in WHO_SHARED_LOGINS


def who_name(cookies):
    """The person the shared login says is working (the cookie the picker sets), or None."""
    try:
        v = str((cookies or {}).get(WHO_COOKIE) or "").strip().lower()
    except Exception:                                          # noqa: BLE001
        return None
    for k, label in WHO_NAMES:
        if v == k:
            return label
    return None


def who_label(username, display_name, cookies):
    """What a stamp / an order / an answer records as WHO. A personal login: its own name, unchanged. The shared login:
    'Shivani (Reception)' when a name was chosen, else the login's own name as before."""
    if is_shared_login(username):
        n = who_name(cookies)
        if n:
            return "%s (Reception)" % n
    return display_name or username or ""


WHO_JS = r"""<script>/* S441 (D643): the shared Reception login -- "Kaun kaam kar raha hai?" once per sitting */
(function(){
 if(!window.WHO_SHARED||window.__whoS441)return; window.__whoS441=1;
 var NAMES=__NAMES__, CK="__COOKIE__", IDLE=__IDLE__;
 function get(){var m=document.cookie.match(new RegExp("(?:^|; )"+CK+"=([^;]*)"));var v=m?decodeURIComponent(m[1]):"";for(var i=0;i<NAMES.length;i++){if(NAMES[i][0]===v)return NAMES[i];}return null;}
 function dom(){var h=location.hostname||"";return /(^|\.)dr-manoj\.in$/.test(h)?"; domain=.dr-manoj.in":"";}
 function put(v,age){document.cookie=CK+"="+encodeURIComponent(v)+"; path=/; max-age="+age+"; samesite=lax"+dom()+(location.protocol==="https:"?"; secure":"");}
 function chip(p){var c=document.getElementById("who441");if(!c){c=document.createElement("div");c.id="who441";
   c.style.cssText="position:fixed;left:10px;bottom:14px;z-index:9998;background:#1f3864;color:#fff;border-radius:20px;padding:8px 14px;font:600 15px system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.3)";
   document.body.appendChild(c);}
  c.innerHTML="&#128100; "+p[1]+' &middot; <a href="#" style="color:#ffd76a">badlo</a>';
  c.lastChild.onclick=function(e){e.preventDefault();put("",0);ask();};}
 function ask(){if(document.getElementById("whoask441"))return;var o=document.createElement("div");o.id="whoask441";
  o.style.cssText="position:fixed;inset:0;z-index:9999;background:rgba(10,20,40,.92);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:16px";
  var h='<div style="color:#fff;font:700 24px system-ui,sans-serif;margin-bottom:8px;text-align:center">Kaun kaam kar raha hai?</div>';
  NAMES.forEach(function(p){h+='<button type="button" data-k="'+p[0]+'" style="width:min(340px,90vw);min-height:64px;font:700 22px system-ui,sans-serif;border:0;border-radius:12px;background:#fff;color:#1f3864">'+p[1]+'</button>';});
  o.innerHTML=h;document.body.appendChild(o);
  Array.prototype.forEach.call(o.querySelectorAll("button"),function(b){b.onclick=function(){var k=b.getAttribute("data-k");put(k,IDLE);o.parentNode.removeChild(o);var p=get();if(p){chip(p);}try{window.dispatchEvent(new Event("clinicwho"));}catch(e){}};});}
 function touch(){var p=get();if(p){put(p[0],IDLE);chip(p);}else{var c=document.getElementById("who441");if(c)c.parentNode.removeChild(c);ask();}}
 var last=0;["click","touchstart","keydown"].forEach(function(ev){window.addEventListener(ev,function(){var n=Date.now();if(n-last>20000){last=n;touch();}},true);});
 document.addEventListener("visibilitychange",function(){if(!document.hidden)touch();});
 if(document.body){touch();}else{document.addEventListener("DOMContentLoaded",touch);}
})();</script>""".replace("__NAMES__", _json.dumps([list(p) for p in WHO_NAMES])).replace("__COOKIE__", WHO_COOKIE).replace("__IDLE__", str(WHO_IDLE_SECONDS))


def who_script(username):
    """The picker for a page served to the shared login; '' for everyone else."""
    return ("<script>window.WHO_SHARED=true;</script>" + WHO_JS) if is_shared_login(username) else ""


# ------------------------------------------------------------------ S439's rules, copied in (see the header)
S439_FY_RE = _re.compile(r"(?<!\d)20\d\d\s*[-/]\s*(?:20)?\d\d(?!\d)")
S439_STOP = frozenset(("PVT", "PRIVATE", "LTD", "LIMITED", "MS", "PL", "EXTN", "EXT", "AND", "CO", "THE",
                       "BAREILLY", "BAREILL", "BAREIL", "BAREI"))
S439_TRADE = ("PHARMACEUTICALS", "PHARMACEUTICAL", "PHARMA", "MEDICAL", "MEDICALS", "MEDICOS", "MEDICOSE", "AGENCIES",
              "AGENCY", "SURGICALS", "SURGICAL", "FORMULATIONS", "DISTRIBUTORS", "ENTERPRISES", "TRADERS", "SCIENTIFIC",
              "CHEMIST", "DRUGGIST", "DRUG", "HOUSE", "CENTRE", "AID", "WHOLE", "SALE", "WHOLESALE", "BROS", "STORES",
              "HEALTHCARE")
S439_BUYER = ("SANJEEVNI", "SANJEEVANI", "SANJIVANI")
S439_NAME_MIN = 0.80
S439_SIM_MIN = 0.70
_CITY_TAILS = ("BAREILLY", "BAREILL", "BAREIL", "BAREI", "BARE", "BAR", "BA")
_trade_memo = {}


def bill_tails(s):
    """= purchase_app._bill_tails_s439: the digit runs of a bill number, zeros dropped, the LAST run first."""
    t = str(s if s is not None else "")
    runs = [r.lstrip("0") for r in _re.findall(r"\d+", S439_FY_RE.sub(" ", t))]
    runs = [r for r in runs if r]
    if not runs:
        runs = [r for r in (x.lstrip("0") for x in _re.findall(r"\d+", t)) if r]
    if not runs:
        return []
    out = [runs[-1]]
    for r in reversed(runs[:-1]):
        if len(r) >= 3 and r not in out:
            out.append(r)
    return out


def _tok_sim(a, b):
    if a == b:
        return 1.0
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a)):
        return 0.9
    return _difflib.SequenceMatcher(None, a, b).ratio()


def _trade_word(w):
    if w not in _trade_memo:
        _trade_memo[w] = (w in S439_TRADE) or any(_tok_sim(w, g) >= 0.85 for g in S439_TRADE)
    return _trade_memo[w]


def vendor_tokens(s):
    """= purchase_app._vendor_tokens_s439."""
    t = _re.sub(r"\bM\s*/\s*S\b\.?", " ", str(s or "").upper())
    out, run = [], ""
    for w in _re.findall(r"[A-Z]+", t):
        if len(w) == 1:
            run += w
            continue
        if len(run) > 1:
            out.append(run)
        run = ""
        out.append(w)
    if len(run) > 1:
        out.append(run)
    while len(out) > 1 and out[-1] in _CITY_TAILS:
        out.pop()
    return [w for w in out if w not in S439_STOP]


def vendor_sim(a, b):
    """= purchase_app._vendor_sim_s439, over token lists."""
    if not a or not b:
        return 0.0
    an = [t for t in a if not _trade_word(t)]
    bn = [t for t in b if not _trade_word(t)]
    if not an or not bn or max(_tok_sim(x, y) for x in an for y in bn) < S439_NAME_MIN:
        return 0.0

    def side(p, q):
        num = den = 0.0
        for t in p:
            w = 0.3 if _trade_word(t) else 1.0
            num += w * max(_tok_sim(t, u) for u in q)
            den += w
        return num / den
    return (side(a, b) + side(b, a)) / 2.0


def is_buyer(toks):
    """= purchase_app._is_buyer_s439."""
    for t in toks:
        if t.startswith(("SANJEEV", "SANJIV", "SANJEV")) or max(_tok_sim(t, x) for x in S439_BUYER) >= 0.8:
            return True
    return (not [t for t in toks if not _trade_word(t)]) and any(t.startswith("MEDICOS") for t in toks)


# ------------------------------------------------------------------ the pass
PAGE_MINUTES = 5                 # a forgotten page: scanned by the same person within this many minutes of its bill
SURE_PCT = 0.02                  # "the amount within 2%"
NEAR_DAYS = 30                   # a near match without a readable bill number is looked for this far back only
WINDOW_DAYS = 90                 # S409's own window
LANE_SIM = 0.85                  # a clinic-lane scan whose supplier is this close to a Marg pharmacy supplier is asked about
FP_SAME_PAPER = 6                # = asset_register.DUP_NEAR: coarse bits at or under which two images are the same paper
SETTLE_MINUTES = 10              # a scan with no OCR verdict is judged once it is this old
PAGES_FROM = _os.environ.get("S441_PAGES_FROM", "2026-10-01")   # pages are joined only for scans made under the new flow;
#                                 history keeps its one-page bills (the old flow's multi-page step existed, unseen -- F-667)
FIN_DB = _os.environ.get("FINANCE_DB_FOR_SCANS", "/root/finance/finance.db")

DDL = (
    "CREATE TABLE IF NOT EXISTS scan_check_s441 (bill_id INTEGER PRIMARY KEY, verdict TEXT NOT NULL, other_id INTEGER, "
    "detail TEXT, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS scan_question (id INTEGER PRIMARY KEY AUTOINCREMENT, bill_id INTEGER NOT NULL, kind TEXT NOT NULL, "
    "cand_id INTEGER, detail TEXT, asked_at TEXT NOT NULL, answer TEXT, answered_by TEXT, answered_at TEXT, UNIQUE(bill_id, kind))",
)
BILL_COLS = (("scanned_by", "TEXT"), ("client_token", "TEXT"), ("page_of", "INTEGER"))


def now_ist():
    """The asset app's own clock convention (_now_ist: the server's local time, which is IST)."""
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure(db):
    have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    for col, typ in BILL_COLS:
        if col not in have:
            db.execute("ALTER TABLE bills ADD COLUMN %s %s" % (col, typ))
    for d in DDL:
        db.execute(d)
    db.execute("CREATE INDEX IF NOT EXISTS ix_bills_client_token ON bills(client_token)")


def _f(v):
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None


def _amount_close(a, b):
    a, b = _f(a), _f(b)
    if a is None or b is None or a <= 0 or b <= 0:
        return False
    return abs(a - b) <= SURE_PCT * max(a, b) + 0.005


def _ham(a, b):
    try:
        if not a or not b or len(a) != len(b):
            return 64
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except (TypeError, ValueError):
        return 64


def _when(s):
    try:
        return _dt.datetime.strptime(str(s or "")[:16].replace("T", " "), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _at(b):
    """When a scan was made: submitted_at (the asset app writes it in IST); created_at is SQLite's UTC default."""
    return _when(b["submitted_at"]) or ((_when(b["created_at"]) + _dt.timedelta(hours=5, minutes=30)) if _when(b["created_at"]) else None)


def _person(b):
    return (b["scanned_by"] or b["submitted_by"] or "").strip().lower()


def _audit(db, bid, action, detail, who="server (S441)"):
    try:
        db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
                   (bid, now_ist(), who, action, _json.dumps(detail or {}, ensure_ascii=False)[:500]))
    except _sqlite3.Error:
        pass


def _verdict(db, bid, verdict, other=None, detail=""):
    db.execute("INSERT OR REPLACE INTO scan_check_s441 (bill_id, verdict, other_id, detail, at) VALUES (?,?,?,?,?)",
               (bid, verdict, other, str(detail)[:300], now_ist()))


def _fin_ro(path=None):
    p = path or FIN_DB
    try:
        if not p or not _os.path.exists(p):
            return None
        con = _sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=2)
        con.execute("SELECT 1")
        return con
    except Exception:                                          # noqa: BLE001
        return None


def _finance_facts(fin_path=None):
    """(the Marg pharmacy suppliers as token lists, the scans S439 has linked to a Marg bill). Empty when unreachable."""
    sup, linked = [], set()
    con = _fin_ro(fin_path)
    if con is None:
        return sup, linked
    try:
        seen = set()
        for (s,) in con.execute("SELECT DISTINCT supplier FROM purchase_bill WHERE supplier IS NOT NULL"):
            toks = vendor_tokens(s)
            key = " ".join(toks)
            if toks and key not in seen:
                seen.add(key)
                sup.append((s, toks))
        for (a,) in con.execute("SELECT asset_bill_id FROM purchase_scan_link"):
            linked.add(int(a))
    except _sqlite3.Error:
        pass
    finally:
        con.close()
    return sup, linked


def _settled(b, now):
    """OCR has spoken: read / empty / failed, or no OCR at all and the scan is old enough."""
    st = b["ocr_status"]
    if st in ("read", "empty", "failed"):
        return True
    if st == "reading":
        w = _at(b)
        return bool(w and now - w > _dt.timedelta(minutes=60))      # a read lost to a restart
    w = _at(b)
    return bool(w and now - w > _dt.timedelta(minutes=SETTLE_MINUTES))


MERGE_PY = _os.environ.get("S441_MERGE_PY", "/root/wa/venv/bin/python3")      # has pypdf (S440's gate proves it)
_MERGE_SRC = ("import sys\nfrom pypdf import PdfReader, PdfWriter\nw = PdfWriter()\n"
              "for src in sys.argv[2:]:\n    [w.add_page(p) for p in PdfReader(src).pages]\n"
              "w.write(open(sys.argv[1], 'wb'))\n")


def _merge_pdf(upload_dir, head, page):
    """The forgotten page appended to its bill's PDF, as a NEW stored file (both originals stay). pypdf in this process,
    else the venv python's. None when it cannot be done (not two PDFs) -- the link alone then carries the page."""
    if not upload_dir or not head["source_stored"] or not page["source_stored"]:
        return None
    if not (head["source_stored"].lower().endswith(".pdf") and page["source_stored"].lower().endswith(".pdf")):
        return None
    import secrets as _secrets                                 # noqa: PLC0415
    name = "bill_%s.pdf" % _secrets.token_hex(8)
    dst = _os.path.join(upload_dir, name)
    srcs = [_os.path.join(upload_dir, head["source_stored"]), _os.path.join(upload_dir, page["source_stored"])]
    try:
        from pypdf import PdfReader, PdfWriter                 # noqa: PLC0415
        w = PdfWriter()
        for src in srcs:
            for pg in PdfReader(src).pages:
                w.add_page(pg)
        with open(dst, "wb") as fh:
            w.write(fh)
        return name
    except ImportError:
        pass
    except Exception:                                          # noqa: BLE001
        return None
    try:
        import subprocess as _sp                               # noqa: PLC0415
        if _os.path.exists(MERGE_PY):
            r = _sp.run([MERGE_PY, "-c", _MERGE_SRC, dst] + srcs, capture_output=True, timeout=60)
            if r.returncode == 0 and _os.path.exists(dst) and _os.path.getsize(dst) > 0:
                return name
    except Exception:                                          # noqa: BLE001
        pass
    return None


def _join_page(db, page, head, upload_dir, why):
    merged = _merge_pdf(upload_dir, head, page)
    if merged:
        _audit(db, head["id"], "s441_page_merged", {"page": page["id"], "page_stamp": page["stamp_no"], "before": head["source_stored"], "after": merged})
        db.execute("UPDATE bills SET source_stored=? WHERE id=?", (merged, head["id"]))
    if head["total_amount"] in (None, "") and page["total_amount"] not in (None, ""):
        db.execute("UPDATE bills SET total_amount=? WHERE id=?", (page["total_amount"], head["id"]))   # the total sits on the last page
    db.execute("UPDATE bills SET status='rejected', page_of=?, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",
               (head["id"], "page 2 of %s (joined automatically)" % (head["stamp_no"] or "#%d" % head["id"]),
                "server (S441 forgotten page)", now_ist(), page["id"]))
    _audit(db, page["id"], "s441_page_joined", {"to": head["id"], "to_stamp": head["stamp_no"], "how": why, "merged": bool(merged)})
    _verdict(db, page["id"], "page", head["id"], why)


def _set_aside(db, dup, first, why):
    db.execute("UPDATE bills SET status='rejected', dup_of=?, dup_flag='yes', dup_why=?, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",
               (first["id"], why, "duplicate of %s" % (first["stamp_no"] or "#%d" % first["id"]), "server (S441 double-scan rule)", now_ist(), dup["id"]))
    _audit(db, dup["id"], "duplicate", {"of": first["id"], "of_stamp": first["stamp_no"], "how": why, "kit": "S441"})
    _verdict(db, dup["id"], "double", first["id"], why)


def _ask(db, bid, kind, cand, detail):
    cur = db.execute("INSERT OR IGNORE INTO scan_question (bill_id, kind, cand_id, detail, asked_at) VALUES (?,?,?,?,?)",
                     (bid, kind, cand, str(detail)[:300], now_ist()))
    if cur.rowcount:
        _audit(db, bid, "s441_question", {"kind": kind, "cand": cand, "detail": detail})
    return bool(cur.rowcount)


def _refused_pair(db, a, b):
    """A person already said these two are different papers (S409's 'Not duplicate' or an S441 answer)."""
    r = db.execute("SELECT 1 FROM scan_question WHERE kind='twin' AND answer='different' AND "
                   "((bill_id=? AND cand_id=?) OR (bill_id=? AND cand_id=?))", (a, b, b, a)).fetchone()
    return bool(r)


def run_pass(db, only=None, upload_dir=None, fin_path=None, now=None, limit_days=WINDOW_DAYS):
    """One pass over the scans of the last 90 days that have not been judged yet (or only bill `only`). Writes assets.db
    through `db` (the asset app's own connection) and commits. Returns the counts."""
    ensure(db)
    now = now or _dt.datetime.now()
    since = (now.date() - _dt.timedelta(days=limit_days)).isoformat()
    db.row_factory = _sqlite3.Row
    rows = [dict(r) for r in db.execute("SELECT * FROM bills WHERE stamp_no IS NOT NULL AND "
                                        "substr(COALESCE(submitted_at, created_at, ''),1,10)>=? ORDER BY id", (since,))]
    done = {r[0] for r in db.execute("SELECT bill_id FROM scan_check_s441")}
    suppliers, linked = _finance_facts(fin_path)
    out = dict(checked=0, page=0, double=0, twin=0, lane=0, clear=0, waiting=0)
    by_id = {r["id"]: r for r in rows}
    toks = {r["id"]: vendor_tokens(r["vendor"]) for r in rows}
    tails = {r["id"]: bill_tails(r["bill_no"]) for r in rows}
    for b in rows:
        if only is not None and b["id"] != only:
            continue
        if b["id"] in done or b["status"] == "rejected" or b["page_of"]:
            continue
        if not _settled(b, now):
            out["waiting"] += 1
            continue
        out["checked"] += 1
        done.add(b["id"])
        bw = _at(b)
        lane = b["lane"] or "clinic"
        tb, vb = tails[b["id"]], toks[b["id"]]
        no_header = not (b["vendor"] or "").strip() and not (b["bill_no"] or "").strip()
        # 1 -- a forgotten page: the same person, minutes before, the same lane, the same bill number or no header here
        joined = False
        for a in (reversed(rows) if str(b["submitted_at"] or "")[:10] >= PAGES_FROM else ()):
            if a["id"] >= b["id"]:
                continue
            aw = _at(a)
            if not aw or not bw:
                continue
            gap = bw - aw
            if gap > _dt.timedelta(minutes=PAGE_MINUTES):
                break
            if gap < _dt.timedelta(0):
                continue
            head = by_id.get(a["page_of"]) if a["page_of"] else a
            if head is None or head["status"] == "rejected":
                continue
            if _person(a) != _person(b) or (a["lane"] or "clinic") != lane:
                continue
            same_no = bool(tb and set(tb) & set(tails[head["id"]] + tails[a["id"]]))
            if not (same_no or (no_header and (b["total_amount"] not in (None, "") or b["ocr_status"] == "read"))):
                continue
            if _ham(a["fpc"], b["fpc"]) <= FP_SAME_PAPER:          # the same paper again: not a page (S409 / the double rule)
                continue
            _join_page(db, b, head, upload_dir, "same person within %d min, %s" % (PAGE_MINUTES, "same bill number" if same_no else "no bill header"))
            b.update(status="rejected", page_of=head["id"])
            out["page"] += 1
            joined = True
            break
        if joined:
            continue
        # 2 -- a sure double / 3 -- a near match
        best_sure, best_near = None, None
        for a in rows:
            if a["id"] == b["id"] or a["status"] == "rejected" or a["page_of"]:
                continue
            if a["id"] > b["id"] and a["id"] not in done:
                continue                                            # a later scan is judged on its own turn
            ta, va = tails[a["id"]], toks[a["id"]]
            common = set(tb) & set(ta)
            same_tail = bool(common)
            close = _amount_close(a["total_amount"], b["total_amount"])
            if not (same_tail or close):
                continue
            if b["dup_flag"] == "no" or _refused_pair(db, a["id"], b["id"]):
                continue
            sim = vendor_sim(va, vb) if (va and vb) else 0.0
            same_vendor = sim >= S439_SIM_MIN
            aw = _at(a)
            recent = bool(aw and bw and abs((bw - aw).days) <= NEAR_DAYS)
            long_tail = same_tail and max(len(x) for x in common) >= 2
            if same_vendor and same_tail and close:
                if best_sure is None or a["id"] < best_sure["id"]:
                    best_sure = a
            elif (same_vendor and long_tail) or (same_vendor and close and (not tb or not ta) and recent) \
                    or (long_tail and close and max(len(x) for x in common) >= 3 and (not va or not vb)):
                if best_near is None or a["id"] < best_near["id"]:
                    best_near = a
        if best_sure is not None:
            keep, drop = best_sure, b
            if b["id"] in linked and best_sure["id"] not in linked:
                keep, drop = b, best_sure                        # the scan S439 linked to a Marg bill is the one kept
            if drop["status"] == "approved":                     # an approved clinic bill is never set aside by a rule
                if _ask(db, b["id"], "twin", best_sure["id"], "same supplier, bill number and amount -- one is approved"):
                    out["twin"] += 1
                _verdict(db, b["id"], "twin_q", best_sure["id"], "sure, but approved")
            else:
                _set_aside(db, drop, keep, "S441 sure: supplier + bill-number tail + amount within 2%")
                drop.update(status="rejected", dup_of=keep["id"])
                out["double"] += 1
                if drop["id"] != b["id"]:
                    _verdict(db, b["id"], "clear", None, "kept; %d set aside" % drop["id"])
            continue
        if best_near is not None:
            if _ask(db, b["id"], "twin", best_near["id"], "near: %s / %s / %s" % (
                    (b["vendor"] or "-")[:40], (b["bill_no"] or "-")[:20], b["total_amount"])):
                out["twin"] += 1
            _verdict(db, b["id"], "twin_q", best_near["id"], "near match")
            continue
        # 4 -- a likely wrong lane: a known Marg pharmacy supplier, scanned in the clinic lane, not yet approved
        if lane == "clinic" and b["status"] == "draft" and vb and suppliers and not is_buyer(vb):
            top, sc = None, 0.0
            for name, st in suppliers:
                s_ = vendor_sim(vb, st)
                if s_ > sc:
                    top, sc = name, s_
            if top is not None and sc >= LANE_SIM:
                known_clinic = any(a["id"] != b["id"] and (a["lane"] or "clinic") == "clinic" and a["status"] == "approved"
                                   and toks[a["id"]] and vendor_sim(toks[a["id"]], vb) >= S439_SIM_MIN for a in rows)
                if not known_clinic:                             # the owner has never approved this supplier as a clinic bill
                    if _ask(db, b["id"], "lane", None, "the supplier looks like Marg's %s (%.2f)" % (top, sc)):
                        out["lane"] += 1
                    _verdict(db, b["id"], "lane_q", None, top)
                    continue
        _verdict(db, b["id"], "clear")
        out["clear"] += 1
    db.commit()
    return out


# ------------------------------------------------------------------ the questions, read by Purchase orders and answered in the asset app
def open_questions(adb, days=60):
    """[{q, kind, bill: {...}, cand: {...} or None, asked_at}] -- the questions nobody has answered (assets.db, read only)."""
    out = []
    try:
        adb.row_factory = _sqlite3.Row
        since = (_dt.date.today() - _dt.timedelta(days=days)).isoformat()
        qs = adb.execute("SELECT * FROM scan_question WHERE answer IS NULL AND substr(asked_at,1,10)>=? ORDER BY id", (since,)).fetchall()
        for q in qs:
            b = adb.execute("SELECT * FROM bills WHERE id=?", (q["bill_id"],)).fetchone()
            if b is None or (b["status"] == "rejected" and q["kind"] == "twin") or b["page_of"]:
                continue
            c = adb.execute("SELECT * FROM bills WHERE id=?", (q["cand_id"],)).fetchone() if q["cand_id"] else None
            out.append(dict(q=q["id"], kind=q["kind"], asked_at=q["asked_at"], detail=q["detail"], bill=_brief(b), cand=_brief(c) if c else None))
    except _sqlite3.Error:
        return []
    return out


def answered_recent(adb, days=2):
    out = []
    try:
        adb.row_factory = _sqlite3.Row
        since = (_dt.date.today() - _dt.timedelta(days=days)).isoformat()
        for q in adb.execute("SELECT q.*, b.stamp_no FROM scan_question q JOIN bills b ON b.id=q.bill_id WHERE q.answer IS NOT NULL "
                             "AND substr(q.answered_at,1,10)>=? ORDER BY q.answered_at DESC LIMIT 30", (since,)):
            out.append(dict(q=q["id"], kind=q["kind"], stamp=q["stamp_no"], answer=q["answer"], by=q["answered_by"], at=(q["answered_at"] or "")[11:16]))
    except _sqlite3.Error:
        return []
    return out


def _brief(b):
    return dict(id=b["id"], stamp=b["stamp_no"] or "#%d" % b["id"], vendor=b["vendor"] or "", bill_no=b["bill_no"] or "",
                amount=b["total_amount"], lane=b["lane"] or "clinic", status=b["status"], by=(b["scanned_by"] or b["submitted_by"] or ""),
                at=(b["submitted_at"] or b["created_at"] or "")[:16])


ANSWERS = {"twin": ("same", "different"), "lane": ("pharmacy", "stay")}


def answer(db, qid, ans, who):
    """The first answer settles it. -> (ok, message). twin/same: the newer paper set aside as a duplicate of the other;
    twin/different: both kept (and S409's amber, if any, cleared). lane/pharmacy: the draft moves to the pharmacy lane
    (captured); lane/stay: nothing moves."""
    ensure(db)
    db.row_factory = _sqlite3.Row
    q = db.execute("SELECT * FROM scan_question WHERE id=?", (qid,)).fetchone()
    if q is None:
        return False, "no_such_question"
    if q["answer"]:
        return True, "already: %s (%s)" % (q["answer"], q["answered_by"] or "")
    if ans not in ANSWERS.get(q["kind"], ()):
        return False, "bad_answer"
    b = db.execute("SELECT * FROM bills WHERE id=?", (q["bill_id"],)).fetchone()
    if b is None:
        return False, "no_such_bill"
    cur = db.execute("UPDATE scan_question SET answer=?, answered_by=?, answered_at=? WHERE id=? AND answer IS NULL", (ans, who, now_ist(), qid))
    if not cur.rowcount:
        db.commit()
        return True, "already"
    if q["kind"] == "twin":
        c = db.execute("SELECT * FROM bills WHERE id=?", (q["cand_id"],)).fetchone()
        if ans == "same" and c is not None:
            keep, drop = (c, b) if c["id"] < b["id"] else (b, c)
            if drop["status"] == "approved":
                keep, drop = drop, keep
            if drop["status"] != "rejected" and drop["status"] != "approved":
                _set_aside(db, drop, keep, "S441 person: the same paper (%s)" % who)
        else:
            db.execute("UPDATE bills SET dup_flag='no' WHERE id=? AND (dup_flag IS NULL OR dup_flag IN ('','maybe'))", (b["id"],))
            _audit(db, b["id"], "not_duplicate", {"cand": q["cand_id"], "how": "S441 Scan ka kaam"}, who)
    elif q["kind"] == "lane" and ans == "pharmacy" and b["status"] == "draft":
        db.execute("UPDATE bills SET lane='pharmacy', kind='Pharmacy', status='captured' WHERE id=?", (b["id"],))
        _audit(db, b["id"], "relane", {"from": b["lane"] or "clinic", "to": "pharmacy", "status": "captured", "via": "S441 Scan ka kaam"}, who)
    _audit(db, b["id"], "s441_answer", {"q": qid, "kind": q["kind"], "answer": ans}, who)
    db.commit()
    return True, "ok"


if __name__ == "__main__":                                    # the installer's first pass: python3 scan_checks_s441.py pass <assets.db> <uploads>
    import sys as _sys
    if len(_sys.argv) >= 3 and _sys.argv[1] == "pass":
        _db = _sqlite3.connect(_sys.argv[2], timeout=30)
        r = run_pass(_db, upload_dir=(_sys.argv[3] if len(_sys.argv) > 3 else None))
        print("S441 pass", _json.dumps(r, sort_keys=True))
        n = _db.execute("SELECT COUNT(*) FROM scan_question WHERE answer IS NULL").fetchone()[0]
        print("S441 open questions", n)
    else:
        print("usage: scan_checks_s441.py pass <assets.db> [uploads dir]")

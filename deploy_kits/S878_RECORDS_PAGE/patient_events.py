#!/usr/bin/env python3
# =============================================================================
#  patient_events.py  ·  v1.0  ·  kit S876_HUB_RECORD_INLINE  ·  Session 483 (Sanjeevni), 18-Nov-2026 (D1007)
#
#  ONE PATIENT'S RECORD AS EVENTS, NEWEST FIRST, IN WORDS.
#  His words (S482, 14:23-14:34; S483 15:25 on the mock-up https://claude.ai/artifact/Q9RmY4keBZFa9H3p9ebgBc):
#  from a bill or a return on the Hub, the patient's record opens inline -- consulted (with what was paid at
#  the clinic), X-ray, procedure, blood test, bought medicines, returned, exchanged -- each with its paper one tap
#  under it; a return joined to the bill it returns and shown ONCE, on its own date; a return and a new
#  bill on one day read as one "Exchanged"; a bill with the same medicines and quantities as a bill of
#  the day before flagged; quantities in words ("1 strip 5 tablets"), never "1:5".
#
#  THE ONE READER.  This module is the single place that turns a clinic ID into its story.  The
#  parent's records page (/finance/records/p/<cid>, records.py -- F-1466) is to read events() from
#  here rather than build a second story.  records.py is READ ONLY to this kit: its tables are read
#  with the same rules (the pharmacy SURE rule: a line checked by a person or matched at >= 0.95,
#  never a bill in an open identity dispute; walk-in / name-only bills never reach an ID).
#
#  Read-only: no table is written.  Every threshold is a setting (setting table):
#    patient_events.same_bill_days  (default 1)  -- a bill is compared with this patient's bills of
#                                                   the same day and up to N days before
#    patient_events.recent_days     (default 5)  -- visit days shown open; the rest behind "earlier"
#  Doors (checker = the owner; the Hub is his page):
#    GET /finance/sanjeevni/api/patient-events/healthz
#    GET /finance/sanjeevni/api/patient/<cid>/record
#  Mounted by sanjeevni_day.init (as hub_cash).  Stdlib + Flask only.
# =============================================================================
import datetime as dt
import re
import sqlite3

from flask import Blueprint, jsonify

VERSION = "1.0"
KIT = "S876_HUB_RECORD_INLINE"
bp = Blueprint("patient_events", __name__)
_db = _require = None
_unit = "medical"

SURE_CONF = 0.95            # the same rule as records.SURE_CONF (read from records when it is loaded)
RECORDS_URL = "/finance/records"
CID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]{0,23}$")
SECTION = {"consult": ("consult", "🩺", "Consulted"), "revisit": ("consult", "🩺", "Free revisit"),
           "concession": ("consult", "🩺", "Free / concession visit"), "xray": ("xray", "🦴", "X-ray"),
           "proc": ("proc", "🩹", "Procedure")}
FILE_WORD = {"xray": "X-ray film", "blood": "Blood report", "scan": "MRI / CT", "other": "Paper"}
ORDER = {"consult": 0, "visit": 0, "dx": 0.5, "xray": 1, "proc": 2, "blood": 3, "paper": 4, "hospital": 5,   # S878: dx
         "bought": 6, "exchanged": 7, "returned": 8}


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


# ------------------------------------------------------------------ small helpers
def _rows(con, sql, args=()):
    cur = con.execute(sql, args)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def _cols(con, t):
    try:
        return {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}
    except sqlite3.Error:
        return set()


def _setting_int(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        v = int(str(r[0]).strip()) if r and str(r[0]).strip() else default
        return v if 0 <= v <= 60 else default
    except (sqlite3.Error, TypeError, ValueError):
        return default


def _sure():
    try:
        import records                                       # the parent's module, only its constant
        return float(getattr(records, "SURE_CONF", SURE_CONF))
    except Exception:                                         # noqa: BLE001
        return SURE_CONF


def rs(p):
    if p is None:
        return None
    v = abs(int(round(p / 100.0)))
    s = str(v)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return s


def _d(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10])
    except ValueError:
        return None


def dmy(iso):
    d = _d(iso)
    return d.strftime("%d-%b") if d else str(iso or "")


def _mode(m):
    m = (m or "").strip()
    return {"cash": "cash", "upi": "UPI", "card": "card"}.get(m.lower(), m)


def _plural(n, word):
    return "%s %s%s" % (n, word, "" if n == 1 else ("es" if word.endswith(("ch", "sh")) else "s"))


def _num(x):
    f = float(x)
    return int(f) if f == int(f) else round(f, 2)


def qty_words(qty_raw, pack, item=""):
    """A Marg quantity in words: '1:5' with pack '1*10' -> '1 strip 5 tablets'; '3.0' with pack '2ML' on an
    injection -> '3 injections'; '1.0' '100ML' -> '1 bottle'. Never the raw 'strips:tabs' code."""
    q = str(qty_raw or "").strip()
    p = str(pack or "").upper()
    name = str(item or "").upper()
    try:
        if ":" in q:
            s, t = q.split(":", 1)
            try:
                s, t = _num(s or 0), _num(t or 0)
            except (TypeError, ValueError):
                return "quantity not readable"
            parts = []
            if s:
                parts.append(_plural(s, "strip"))
            if t:
                parts.append(_plural(t, "tablet"))
            return " ".join(parts) or "none"
        n = _num(q or 0)
    except (TypeError, ValueError):
        return "quantity not readable"
    if "VAIL" in p or "VIAL" in p:
        noun = "vial"
    elif "ML" in p:
        m = re.search(r"(\d+(?:\.\d+)?)", p)
        ml = float(m.group(1)) if m else 0
        noun = "injection" if ("INJ" in name or 0 < ml <= 10) else "bottle"
    elif "GM" in p:
        noun = "tube" if any(w in name for w in ("GEL", "CREAM", "OINT", "CRM")) else "pack"
    elif "SACH" in name:
        noun = "sachet"
    elif "SYRINGE" in name:
        noun = "syringe"
    elif "SPRAY" in name:
        noun = "spray"
    else:
        noun = "piece"
    return _plural(n, noun)


def line_value_p(qty_raw, pack, rate_p):
    """A Marg line's value in paise (the amount on a line is the strip rate) -- sanjeevni_day's rule."""
    try:
        import sanjeevni_day
        return sanjeevni_day.line_value_p(qty_raw, pack, rate_p)
    except Exception:                                         # noqa: BLE001
        pass
    try:
        per = 1
        p = str(pack or "")
        if "*" in p:
            per = int(float(p.split("*")[-1].strip())) or 1
        q = str(qty_raw or "").strip()
        if ":" in q:
            s, t = q.split(":", 1)
            units = float(s or 0) + float(t or 0) / per
        else:
            units = float(q or 0)
        return int(round(units * int(rate_p or 0)))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def bill_key(no):
    """A bill number's order: its letters, then its trailing digits as a NUMBER (A999 before A1000)."""
    m = re.match(r"^(.*?)(\d+)$", str(no or ""))
    return (m.group(1), int(m.group(2))) if m else (str(no or ""), -1)


def _units(qty_raw, pack):
    """The quantity as a number of tablets (or pieces) -- for comparing two lines."""
    try:
        per = 1
        p = str(pack or "")
        if "*" in p:
            per = int(float(p.split("*")[-1].strip())) or 1
        q = str(qty_raw or "").strip()
        if ":" in q:
            s, t = q.split(":", 1)
            return round(float(s or 0) * per + float(t or 0), 3)
        return round(float(q or 0), 3)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


# ------------------------------------------------------------------ the record
def person(con, cid):
    if _has(con, "patient_ref"):
        r = _rows(con, "SELECT name, merged_into FROM patient_ref WHERE clinic_id=? "
                       "ORDER BY (merged_into IS NULL OR merged_into='') DESC, id LIMIT 1", (cid,))
        if r:
            return {"name": r[0]["name"] or "", "merged": r[0]["merged_into"] or ""}
    if _has(con, "clinic_day_line"):
        d = _rows(con, "SELECT patient FROM clinic_day_line WHERE clinic_id=? AND patient<>'' "
                       "ORDER BY business_date DESC LIMIT 1", (cid,))
        if d:
            return {"name": d[0]["patient"], "merged": ""}
    return {"name": "", "merged": ""}


def _file(f):
    return {"name": FILE_WORD.get(f["kind"], f["kind"] or "Paper") + ((" · " + f["file_name"]) if f.get("file_name") else ""),
            "url": ("%s/file/%d" % (RECORDS_URL, int(f["id"]))) if f.get("drive_id") else None}


def _pharmacy(con, cid):
    if not (_has(con, "sale_item") and _has(con, "patient_ref") and _has(con, "day_entry")):
        return []
    disputed = set()
    if _has(con, "identity_dispute"):
        disputed = {str(r["bill_no"]) for r in _rows(con, "SELECT bill_no FROM identity_dispute WHERE status='open' AND clinic_id=?", (cid,))}
    rows = _rows(con, """
        SELECT s.service, s.source_ref bill, s.amount_p, s.mode, d.business_date day
        FROM sale_item s JOIN patient_ref p ON p.id = s.patient_ref_id JOIN day_entry d ON d.id = s.day_entry_id
        WHERE p.clinic_id = ? AND s.service IN ('pharmacy','pharmacy_return')
          AND ((s.verified_by IS NOT NULL AND s.verified_by <> '') OR s.confidence >= ?)
        ORDER BY d.business_date DESC, s.source_ref DESC""", (cid, _sure()))
    out, seen = [], set()
    has_lines = _has(con, "sale_line_item")
    for r in rows:
        k = (str(r["bill"]), r["day"])
        if str(r["bill"]) in disputed or k in seen:
            continue
        seen.add(k)
        lines = []
        if has_lines:
            for l in _rows(con, "SELECT item_name, item_key, pack, qty_raw, amount_p FROM sale_line_item "
                                "WHERE bill_no=? AND business_date=? ORDER BY seq", (r["bill"], r["day"])):
                vp = line_value_p(l["qty_raw"], l["pack"], l["amount_p"])
                lines.append(dict(item=l["item_name"] or "", key=l["item_key"] or (l["item_name"] or "").upper(),
                                  qty=qty_words(l["qty_raw"], l["pack"], l["item_name"]),
                                  units=_units(l["qty_raw"], l["pack"]), value_p=vp, note=""))
        out.append(dict(bill=str(r["bill"]), day=r["day"], amount_p=abs(int(r["amount_p"] or 0)), mode=_mode(r["mode"]),
                        is_return=(r["service"] == "pharmacy_return"), lines=lines))
    return out


def _lines_open(label, lines):
    return {"label": label, "lines": [dict(item=l["item"], qty=l["qty"],
                                           value=(rs(l["value_p"]) if l.get("value_p") is not None else None),
                                           note=l.get("note") or "") for l in lines]}


def _list_words(lines, n=2):
    parts = ["%s of %s" % (l["qty"], l["item"].title()) for l in lines[:n]]
    if len(lines) > n:
        parts.append("%d more" % (len(lines) - n))
    return ", ".join(parts)


def events(con, cid, unit="medical"):
    """The patient's record as {header, days:[{date, events:[...]}]}, newest first. Read-only."""
    cid = str(cid or "").strip()
    ev = []                                                   # dicts with day, kind, ...

    def add(day, kind, icon, head, text="", money_p=None, sign="", sub="", opens=None, flag=None, ref=""):
        """head = the bold words, text = the rest -- both PLAIN text (the page escapes them)."""
        if not day:
            return None
        e = dict(day=str(day)[:10], kind=kind, icon=icon, head=head, text=text, sub=sub,
                 money=(rs(money_p) if money_p else None), sign=sign, opens=opens or [], flag=flag, ref=ref)
        ev.append(e)
        return e

    # ---- the clinic: Docterz's day lines (and visit dates Docterz's list knows)
    by_day = {}
    if _has(con, "clinic_day_line"):
        for r in _rows(con, "SELECT business_date d, section, amount_p, mode FROM clinic_day_line WHERE clinic_id=? "
                            "ORDER BY business_date DESC, section", (cid,)):
            kind, icon, word = SECTION.get(r["section"], ("consult", "🩺", (r["section"] or "Visit").title()))
            amt = int(r["amount_p"] or 0)
            e = add(r["d"], kind, icon, word, "", abs(amt) or None, sign="−" if amt < 0 else "", sub=_mode(r["mode"]) if amt else "")
            by_day.setdefault((str(r["d"])[:10], kind), e)
    if _has(con, "patient_visit"):
        have = {d for d, _ in by_day}
        for r in _rows(con, "SELECT DISTINCT visit_date d FROM patient_visit WHERE clinic_id=?", (cid,)):
            if r["d"] and str(r["d"])[:10] not in have:
                by_day[(str(r["d"])[:10], "consult")] = add(r["d"], "visit", "🩺", "Visit")
                have.add(str(r["d"])[:10])
    # ---- S878 (the parent): the diagnosis of each visit day and the follow-up advised (dx_feed's dx_visit, from the
    # Docterz clinical data report) -- one line, so the Hub's inline record shows it too (his word 16:12, 18-Nov)
    if _has(con, "dx_visit"):
        for r in _rows(con, "SELECT visit_date d, diagnosis_raw, std_dx, category, follow_up_date FROM dx_visit "
                            "WHERE clinic_id=? ORDER BY visit_date DESC", (cid,)):
            dx = (r["std_dx"] or "").strip()
            raw = (r["diagnosis_raw"] or "").strip()
            if dx.lower().startswith("other") and raw:
                dx = raw
            dx = dx or raw
            fu = str(r["follow_up_date"] or "")[:10]
            if not dx and not fu:
                continue
            add(r["d"], "dx", "📋", dx or "Diagnosis not written",
                (" (" + raw + ")") if raw and dx and raw.lower() != dx.lower() else "",
                sub=" · ".join(x for x in ((r["category"] or ""), ("follow-up advised " + dmy(fu)) if fu else "") if x))
    # ---- the slips: their items go under the day's line (X-ray / procedure names; the OPD slip one tap under)
    if _has(con, "slip") and _has(con, "slip_item"):
        for s in _rows(con, "SELECT id, series, slip_no, day FROM slip WHERE clinic_id=? AND state='ok' ORDER BY day DESC, id DESC", (cid,)):
            if not s["day"]:
                continue
            day = str(s["day"])[:10]
            items = _rows(con, "SELECT kind, name, side FROM slip_item WHERE slip_id=? ORDER BY sort, id", (s["id"],))
            text = "Slip %s%s" % (s["slip_no"], (" · " + ", ".join((i["name"] or i["kind"] or "") + (" " + i["side"] if i["side"] else "")
                                                             for i in items)) if items else "")
            for kind in ("xray", "proc"):
                names = [(i["name"] or "") + (" " + i["side"] if i["side"] else "") for i in items if i["kind"] == kind and i["name"]]
                if not names:
                    continue
                e = by_day.get((day, kind))
                if e is None:
                    e = by_day[(day, kind)] = add(day, kind, SECTION[kind][1], SECTION[kind][2])
                e["text"] += " — " + ", ".join(names).lower()
            host = by_day.get((day, "consult")) or by_day.get((day, "xray")) or by_day.get((day, "proc"))
            if host is None:
                host = by_day[(day, "consult")] = add(day, "visit", "🩺", "Visit", " (slip only)")
            host["opens"].append({"label": "the slip", "text": text})
    # ---- the papers: X-ray films under the day's X-ray; blood reports under the day's blood test; the rest their own line
    files = []
    if _has(con, "record_file"):
        files = _rows(con, "SELECT * FROM record_file WHERE clinic_id=? AND state='ok' ORDER BY day DESC, id DESC", (cid,))
    ev_files = {}
    for f in files:
        if str(f.get("note") or "").startswith("event "):
            ev_files.setdefault(str(f["note"])[6:].strip(), []).append(f)
    blood_days = {}
    if _has(con, "blood_order"):
        for o in _rows(con, "SELECT day, outcome FROM blood_order WHERE clinic_id=? AND state='ok' ORDER BY day DESC", (cid,)):
            out = {"not_tested": " — not tested", "lab_missed": " — the lab missed it"}.get(o["outcome"] or "", "")
            blood_days[str(o["day"])[:10]] = add(o["day"], "blood", "🧪", "Blood test", " ordered" + out)
    if _has(con, "lab_report"):
        for r in _rows(con, "SELECT substr(received_at,1,10) d FROM lab_report WHERE clinic_id=? ORDER BY received_at DESC", (cid,)):
            got = r["d"]
            if not got:
                continue
            host = None
            for d in sorted(blood_days, reverse=True):
                if d <= got:
                    host = blood_days[d]
                    break
            if host is not None and "report received" not in host["text"]:
                host["text"] += "; report received %s" % dmy(got)
            elif host is None:
                blood_days[got] = add(got, "blood", "🧪", "Blood report", " received")
    for f in files:
        if str(f.get("note") or "").startswith("event "):
            continue
        day = str(f["day"])[:10]
        if f["kind"] == "xray":
            e = by_day.get((day, "xray"))
            if e is None:
                e = by_day[(day, "xray")] = add(day, "xray", "🦴", "X-ray", " (film filed)")
            o = next((x for x in e["opens"] if x.get("files") is not None and x["label"] == "the X-ray films"), None)
            if o is None:
                o = {"label": "the X-ray films", "files": []}
                e["opens"].append(o)
            o["files"].append(_file(f))
        elif f["kind"] == "blood":
            e = blood_days.get(day)
            if e is None:
                e = blood_days[day] = add(day, "blood", "🧪", "Blood report", " filed")
            e["opens"].append({"label": "the report", "files": [_file(f)]})
        else:
            add(day, "paper", "📄", FILE_WORD.get(f["kind"], "Paper"), opens=[{"label": "the paper", "files": [_file(f)]}])
    for e in ev:                                              # "2 films filed" on an X-ray line
        if e["kind"] == "xray":
            n = sum(len(o.get("files") or []) for o in e["opens"])
            if n and "film filed" not in e["text"]:
                e["sub"] = (e["sub"] + " · " if e["sub"] else "") + _plural(n, "film") + " filed"
    # ---- hospital and surgery (the doctor's own events)
    if _has(con, "record_event"):
        for h in _rows(con, "SELECT id, day, hospital, what, note FROM record_event WHERE clinic_id=? AND state='ok' "
                            "ORDER BY day DESC, id DESC", (cid,)):
            fl = [_file(f) for f in ev_files.get(str(h["id"]), [])]
            add(h["day"], "hospital", "🏥", (h["what"] or "Hospital").strip(), "", sub=" · ".join(x for x in (h["hospital"], h["note"]) if x),
                opens=[{"label": "the papers", "files": fl}] if fl else [])

    # ---- the pharmacy
    ph = _pharmacy(con, cid)
    bills = [b for b in ph if not b["is_return"]]             # newest first
    rets = [b for b in ph if b["is_return"]]
    def holds(b, cn):                                         # the bill bought at least what came back of a shared medicine
        got = {}
        for l in b["lines"]:
            got[l["key"]] = got.get(l["key"], 0) + (l["units"] or 0)
        return any(l["key"] in got and (l["units"] is None or got[l["key"]] >= l["units"]) for l in cn["lines"])
    for cn in rets:                                           # a return's home: the latest bill on or before it that holds it
        keys = {l["key"] for l in cn["lines"]}
        cands = [b for b in bills if b["day"] <= cn["day"] and keys & {l["key"] for l in b["lines"]}]
        whole = [b for b in cands if b["day"] == cn["day"] and holds(b, cn) and {l["key"] for l in b["lines"]} <= keys]
        earlier = [b for b in cands if b["day"] < cn["day"] and holds(b, cn)]
        same = [b for b in cands if b["day"] == cn["day"] and holds(b, cn)]
        cn["home"] = (whole or earlier or same or cands or [None])[0]
        if cn["home"]:
            for l in cn["home"]["lines"]:
                back = [x for x in cn["lines"] if x["key"] == l["key"]]
                if back:
                    l["note"] = (l["note"] + "; " if l["note"] else "") + "%s returned %s" % (back[0]["qty"], dmy(cn["day"]))
    paired = set()
    for cn in rets:                                           # Exchanged: bought, gave some back, took other medicines -- all one day
        home = cn["home"]
        if home is None or home["day"] != cn["day"]:
            continue                                          # old medicines brought back: a plain return beside that day's bill
        keys = {l["key"] for l in cn["lines"]}
        if not ({l["key"] for l in home["lines"]} <= keys and holds(home, cn)
                and all(sum(x["units"] or 0 for x in cn["lines"] if x["key"] == l["key"]) >= (l["units"] or 0) for l in home["lines"])):
            continue                                          # part of the bill came back -- a plain return
        took = next((b for b in sorted(bills, key=lambda x: bill_key(x["bill"]))
                     if b["day"] == cn["day"] and b is not home and id(b) not in paired
                     and bill_key(b["bill"]) > bill_key(home["bill"]) and not (keys & {l["key"] for l in b["lines"]})), None)
        if took is not None:
            paired.add(id(took))
            cn["exchanged"] = took
            took["exchanged"] = cn
            home["exchanged"] = cn
    same_days = _setting_int(con, "patient_events.same_bill_days", 1)

    def sig(b):
        return sorted((l["key"], l["units"]) for l in b["lines"])
    for b in bills:
        if b.get("exchanged"):
            continue
        n = len(b["lines"])
        flag = None
        if b["lines"]:
            mine = sig(b)
            bd = _d(b["day"])
            for o in bills:
                if o is b or not o["lines"]:
                    continue
                od = _d(o["day"])
                if not (bd and od):
                    continue
                gap = (bd - od).days
                earlier = gap > 0 or (gap == 0 and bill_key(o["bill"]) < bill_key(b["bill"]))
                if earlier and gap <= same_days and sig(o) == mine:
                    settled = []
                    for twin in (b, o):                       # the returns that came back against either bill, summed
                        back = [cn for cn in rets if cn.get("home") is twin]
                        if back and all(sum(x["units"] or 0 for cn in back for x in cn["lines"] if x["key"] == l["key"]) >= (l["units"] or 0)
                                        for l in twin["lines"]):
                            settled = back
                            break
                    flag = {"tone": "mut" if settled else "warn",
                            "text": "Same medicines as the %s bill %s — same items, same quantities. %s" % (
                                dmy(o["day"]), o["bill"],
                                ("Taken back by %s." % ", ".join("%s of %s" % (cn["bill"], dmy(cn["day"])) for cn in sorted(settled, key=lambda c: (c["day"], bill_key(c["bill"]))))) if settled else "Billed twice?")}
                    break
        add(b["day"], "bought", "💊", "Bought medicines", (" — " + _plural(n, "medicine")) if n else "",
            b["amount_p"], sub=b["mode"], opens=[_lines_open("bill " + b["bill"], b["lines"])] if b["lines"]
            else [{"label": "bill " + b["bill"], "text": "The medicine lines of this bill are not in Marg's export."}],
            flag=flag, ref=b["bill"])
    for cn in rets:
        took = cn.get("exchanged")
        if took is not None:
            first = cn["home"]
            diff = took["amount_p"] - cn["amount_p"]
            add(cn["day"], "exchanged", "⇄", "Exchanged", " — returned %s; took %s instead" % (
                _list_words(cn["lines"]) or "medicines", _list_words(took["lines"]) or "other medicines"),
                abs(diff) or None, sign=("+" if diff > 0 else ("−" if diff < 0 else "")),
                sub="first bill %s ₹%s" % (first["bill"], rs(first["amount_p"])),
                opens=[_lines_open("first bill " + first["bill"], first["lines"]), _lines_open("credit note " + cn["bill"], cn["lines"]),
                       _lines_open("new bill " + took["bill"], took["lines"])],
                ref=first["bill"] + " · " + cn["bill"] + " · " + took["bill"])
            continue
        home = cn.get("home")
        n = len(cn["lines"])
        head = ("Returned " + _plural(n, "medicine")) if n else "Returned medicines"
        words = (" — " + _list_words(cn["lines"])) if cn["lines"] else ""
        sub = ("from the %s bill %s" % (dmy(home["day"]), home["bill"])) if home else (
            "no earlier bill of this patient holds these medicines" if cn["lines"] else "its medicine lines are not in Marg's export")
        add(cn["day"], "returned", "↩", head, words, cn["amount_p"], sign="−", sub=sub,
            opens=[_lines_open("credit note " + cn["bill"], cn["lines"])] if cn["lines"] else [], ref=cn["bill"])

    # ---- by day, newest first
    days = {}
    for e in ev:
        days.setdefault(e["day"], []).append(e)
    out_days = []
    for d in sorted(days, reverse=True):
        es = sorted(days[d], key=lambda e: ORDER.get(e["kind"], 9))
        dd = _d(d)
        out_days.append(dict(date=d, dmy=dmy(d), dow=dd.strftime("%a") if dd else "", events=es))
    for x in out_days:
        for e in x["events"]:
            e.pop("day", None)
    clinic_days = sorted({d for (d, _k) in by_day})
    p = person(con, cid)
    return dict(cid=cid, name=p["name"], merged=p["merged"],
                first_seen=dmy(min(days)) if days else "", visit_days=len(clinic_days),
                days=out_days, recent_days=_setting_int(con, "patient_events.recent_days", 5),
                full_url="%s/p/%s" % (RECORDS_URL, cid))


def is_patient_id(cid):
    """A real clinic ID carries a digit; 'WALK-IN' (patient_ref's catch-all) and 'WA...' walk-in IDs (records.py's rule) are no patient."""
    c = str(cid or "").strip().upper()
    return bool(c) and c != "WALK-IN" and not c.startswith("WA") and any(ch.isdigit() for ch in c)


def _mobiles(cid):
    try:
        import sanjeevni_day
        return (sanjeevni_day.mobiles_by_cid({cid}) or {}).get(cid) or []
    except Exception:                                         # noqa: BLE001
        return []


# ------------------------------------------------------------------ the doors
@bp.route("/finance/sanjeevni/api/patient-events/healthz")
def api_healthz():
    return jsonify(ok=True, kit=KIT, version=VERSION)


@bp.route("/finance/sanjeevni/api/patient/<cid>/record")
def api_record(cid):
    u, err = _require("checker")
    if err:
        return err
    cid = str(cid or "").strip()
    if not CID_RE.match(cid):
        return jsonify(ok=False, error="bad_id", message="not a clinic ID"), 400
    if not is_patient_id(cid):
        return jsonify(ok=False, error="walk_in", message="a walk-in has no record of its own"), 400
    con = _db()
    try:
        r = events(con, cid, _unit)
    except Exception as ex:                                   # noqa: BLE001 -- the panel says so in words
        return jsonify(ok=False, error="read_failed", message="the record could not be read (%s)" % type(ex).__name__), 500
    r["mobiles"] = _mobiles(cid)
    r["ok"] = True
    return jsonify(r)

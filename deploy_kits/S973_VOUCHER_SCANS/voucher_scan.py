#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  voucher_scan.py  ·  v1.0  ·  kit S973_VOUCHER_SCANS  ·  Session 540 (Sanjeevni)  ·  27-Nov-2026
#
#  KIT C OF S534_FINAL_BUILD_PLAN (D1091 plan 2.4; his 'Proceed' 18:42 IST 27-Nov on S538_KIT_C_DESIGN): MARG STOCK VOUCHERS SCANNED.
#  A printed Marg Stock Issue (L000045) / Stock Receive (AD00045) voucher scanned on the PHARMACY lane is filed by the Scan App as kind
#  'Stock voucher' (its S973 block; the reader knows the kind). This module reads those scans (assets.db, READ ONLY) and:
#   * THE PRINT ASKS (table stock_voucher_scanask) -- a voucher's print is asked only on need:
#       why 'claim': Amir answered 'Pehle bana chuka hoon' on a claim card (voucher_inquiry, kit B) -> ONE print card on his page:
#                    'Print diya -- reception ko' (one tap; reception gets the line + ONE push) . 'Khud scan karein' (the intake link);
#       why 'cut'  : a line of Marg's Stock Issue / Receive report whose cut name fits more than one item (voucher_judge.marg_lines
#                    'ambiguous'), dated on or after stock.scan_ask_from -> the same print card for that voucher number.
#   * A SCAN SETTLES: a claim whose item (and quantity) the scan holds -> closed 'scan B-xxxx'; a typed voucher whose scan lacks the
#     item -> back to Amir (voucher_inquiry's next round); a cut line -> its full name written into mi_voucher_name (source 'scan B-xxxx').
#   * THE REGISTER ROUTE STAYS SECOND: voucher_judge.ask_registers skips a voucher while its 'cut' print ask is open (scan_open).
#   * No scan within stock.inq_question_days days of the card (or of 'Print diya') -> a claim goes to the owner's call; a cut ask closes
#     and the one-item registers are asked as before.
#  Switch: setting stock.voucher_scan = off -> no print card is made (kit B's road: 'Pehle bana chuka hoon' straight to his call).
#  Every write is idempotent (unique keys, compare-and-set on state); every entry point is fail-soft and never raises into a page.
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import threading

VERSION = "1.0"
KIT = "S973_VOUCHER_SCANS"
HERE = os.path.dirname(os.path.abspath(__file__))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SWITCH_KEY = "stock.voucher_scan"
FROM_KEY = "stock.scan_ask_from"
QDAYS_KEY = "stock.inq_question_days"
DOERS_KEY = "porders.rescan_doers"
DOERS_DEFAULT = "reception,alisha,shivani"                    # porders_s454.S618_DOERS
SV_KIND = "Stock voucher"
OPEN = ("card", "printed")
DDL = ("CREATE TABLE IF NOT EXISTS stock_voucher_scanask (id INTEGER PRIMARY KEY, why TEXT NOT NULL, ref TEXT NOT NULL, kind TEXT, no TEXT, "
       "day TEXT, item TEXT, units INTEGER, pack INTEGER, made_at TEXT NOT NULL, job_key TEXT, printed_at TEXT, printed_by TEXT, told INTEGER, "
       "state TEXT NOT NULL, bill_id INTEGER, stamp TEXT, closed_at TEXT, closed_how TEXT, UNIQUE (why, ref))",)


# ------------------------------------------------------------------ small things
def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def today():
    return dt.datetime.now(IST).date().isoformat()


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().upper())


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (t,)).fetchone() is not None


def setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if (r and r[0] is not None and str(r[0]).strip() != "") else default
    except sqlite3.Error:
        return default


def on(con):
    return str(setting(con, SWITCH_KEY, "on")).strip().lower() != "off"


def qdays(con):
    try:
        v = int(str(setting(con, QDAYS_KEY, "2")).strip())
        return v if 1 <= v <= 14 else 2
    except (TypeError, ValueError):
        return 2


def ensure(con):
    for d in DDL:
        con.execute(d)
    con.execute("CREATE INDEX IF NOT EXISTS ix_s973_scanask_state ON stock_voucher_scanask (state)")


def _audit(con, action, after, who):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("stock_voucher_scanask", 0, action, None, json.dumps(after, sort_keys=True, default=str), who or "", now()))
    except Exception:                                         # noqa: BLE001
        pass


def vno(s, kind=None):
    """A printed / typed voucher number -> Marg's form (L000045 / AD00045); '' when it is not one. A bare number needs the kind."""
    t = re.sub(r"[\s\-/.]", "", str(s or "").upper())
    m = re.fullmatch(r"(L|AD)0*(\d{1,6})", t)
    if m:
        return ("L%06d" if m.group(1) == "L" else "AD%05d") % int(m.group(2))
    if kind and re.fullmatch(r"\d{1,6}", t):
        return ("L%06d" if kind == "ISSUE" else "AD%05d") % int(t)
    return ""


def kind_of(no):
    return "ISSUE" if str(no or "").startswith("L") else "RECEIVE" if str(no or "").startswith("AD") else ""


def dm(iso):
    s = str(iso or "")
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) >= 10 else s


def _VJ():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import voucher_judge                                      # noqa: PLC0415
    return voucher_judge


def _age_days(stamp):
    try:
        t = dt.datetime.fromisoformat(str(stamp)[:19].replace(" ", "T"))
        return (dt.datetime.now(IST).replace(tzinfo=None) - t).total_seconds() / 86400.0
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------------ the scans (assets.db, READ ONLY)
def _assets_path():
    pa = sys.modules.get("purchase_app")
    p = getattr(pa, "_assets_db", None) if pa is not None else None
    return p or os.environ.get("ASSETS_DB") or "/root/assetapp/assets.db"


def _aday(s):
    s = str(s or "").strip()
    m = re.fullmatch(r"(\d{2})[-/.](\d{2})[-/.](\d{4})", s[:10])
    if m:
        return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
    return s[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s[:10]) else ""


def scans(path=None):
    """[dict(id, stamp, no, kind, day, at, lines=[dict(name, qty, batch)])] -- every Stock voucher scan not set aside. None when assets.db is
    unreachable. READ ONLY."""
    p = path or _assets_path()
    if not p or not os.path.exists(p):
        return None
    try:
        a = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=5)
    except sqlite3.Error:
        return None
    out = []
    try:
        cols = {r[1] for r in a.execute("PRAGMA table_info(bills)")}
        sel = [c for c in ("id", "stamp_no", "bill_no", "bill_date", "submitted_at", "created_at", "status", "dup_of") if c in cols]
        rows = [dict(zip(sel, r)) for r in a.execute("SELECT %s FROM bills WHERE kind=? ORDER BY id" % ", ".join(sel), (SV_KIND,))]
        have_cr = _has(a, "claude_reading")
        for r in rows:
            if str(r.get("status") or "") == "rejected" or r.get("dup_of"):
                continue
            vt, rno, lines = "", "", []
            if have_cr:                                       # the reading first: it keeps the quantity as printed ('6:11')
                c = a.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1", (r["id"],)).fetchone()
                try:
                    d = json.loads(c[0]) if c and c[0] else {}
                except ValueError:
                    d = {}
                vt = str(d.get("voucher_type") or "").upper()
                rno = str(d.get("bill_no") or "")
                lines = [dict(name=norm(i.get("name")), qty=(i.get("qty_printed") if i.get("qty_printed") not in (None, "") else i.get("qty")),
                              batch=str(i.get("batch") or "")) for i in (d.get("items") or []) if isinstance(i, dict) and norm(i.get("name"))]
            if not lines:
                lines = [dict(name=norm(n), qty=q, batch=str(b or "")) for n, q, b in
                         a.execute("SELECT item_name, quantity, batch FROM bill_items WHERE bill_id=? ORDER BY id", (r["id"],)) if norm(n)]
            no = vno(rno) or vno(r.get("bill_no"))           # review: the number PRINTED on the paper wins over the link's
            kind = kind_of(no) or (vt if vt in ("ISSUE", "RECEIVE") else "")
            out.append(dict(id=int(r["id"]), stamp=str(r.get("stamp_no") or "#%d" % int(r["id"])), no=no, kind=kind, day=_aday(r.get("bill_date")),
                            at=str(r.get("submitted_at") or r.get("created_at") or "")[:19], lines=lines))
    except sqlite3.Error:
        return None
    finally:
        a.close()
    return out


def _units(qty, pack):
    """The quantities a printed quantity can mean: '6:11' -> 6*pack+11; 6 -> {6, 6*pack} (Marg prints loose units or packs)."""
    p = max(int(pack or 1), 1)
    s = str(qty if qty is not None else "").strip()
    m = re.fullmatch(r"(\d+)\s*:\s*(\d+)", s)
    if m:
        return {int(m.group(1)) * p + int(m.group(2))}
    try:
        f = float(s)
    except ValueError:
        return set()
    if f != int(f) or f < 0:
        return set()
    return {int(f), int(f) * p}


def _q(v):
    """A printed quantity in plain words: 9.0 -> '9'."""
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)
    except (TypeError, ValueError):
        return str(v if v is not None else "")


def _holds(VJ, forms, line):
    """The scan line is the item: its full printed name equals one of the item's forms, or one is the cut of the other."""
    n = line["name"]
    return n in forms or VJ.name_match(forms, n) or any(VJ._prefix(n, f) for f in forms)


# ------------------------------------------------------------------ the print asks
def _job(con, key, subject, text_hi):
    ts = now()
    cur = con.execute("INSERT OR IGNORE INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                      (key, "ask", subject, text_hi, "printed", ts, "S973 (the voucher's print)", ts))
    return cur.rowcount == 1


def _withdraw(con, key):
    if not key:
        return 0
    ts = now()
    return con.execute("UPDATE amir_job SET said_at=?, said_by='system', said_what='withdrawn', done_at=?, done_how='withdrawn' WHERE key=? AND done_at IS NULL",
                       (ts, ts, key)).rowcount or 0


def card_text(why, no, day, item):
    v = ("voucher %s (%s)" % (no, dm(day)) if day else "voucher %s" % no) if no else "jo voucher aapne banaya tha"
    if why == "cut":
        return "Marg ki report mein %s ka naam kata hua hai (%s). Is %s ka print nikaliye aur reception ko dijiye — ya khud scan kariye." % (v, item, "voucher")
    return "Aapne kaha voucher pehle bana chuka hai (%s). Uska print nikaliye aur reception ko dijiye — ya khud scan kariye (%s)." % (item, v)


def open_ask(con, why, ref, kind, no, day, item, units=None, pack=None):
    """ONE print ask + ONE card on Amir's page. -> the ask id, or None when it exists already (never two). The caller commits."""
    ensure(con)
    cur = con.execute("INSERT OR IGNORE INTO stock_voucher_scanask (why, ref, kind, no, day, item, units, pack, made_at, state) VALUES (?,?,?,?,?,?,?,?,?,'card')",
                      (why, str(ref), kind, no or "", day or "", item, units, pack, now()))
    if cur.rowcount != 1:
        return None
    sid = cur.lastrowid
    key = "S973:prt:%d:%s" % (sid, no or "")                  # amir_day draws the card's scan link from the key alone
    if not _job(con, key, item, card_text(why, no, day, item)):
        con.execute("DELETE FROM stock_voucher_scanask WHERE id=?", (sid,))
        return None
    con.execute("UPDATE stock_voucher_scanask SET job_key=? WHERE id=?", (key, sid))
    _audit(con, "s973_ask", dict(id=sid, why=why, ref=ref, no=no, item=item), "system")
    return sid


def close_ask(con, sid, how, bill=None, stamp=None):
    r = con.execute("SELECT job_key, state FROM stock_voucher_scanask WHERE id=?", (sid,)).fetchone()
    if not r or r[1] not in OPEN:
        return False
    if not con.execute("UPDATE stock_voucher_scanask SET state='closed', closed_at=?, closed_how=?, bill_id=COALESCE(?, bill_id), stamp=COALESCE(?, stamp) "
                       "WHERE id=? AND state=?", (now(), how[:120], bill, stamp, sid, r[1])).rowcount:
        return False
    _withdraw(con, r[0])
    _audit(con, "s973_close", dict(id=sid, how=how, stamp=stamp), "system")
    return True


def ask_of(con, why, ref):
    if not _has(con, "stock_voucher_scanask"):
        return None
    r = con.execute("SELECT id, why, ref, kind, no, day, item, units, pack, made_at, job_key, printed_at, state, stamp, closed_how FROM stock_voucher_scanask "
                    "WHERE why=? AND ref=?", (why, str(ref))).fetchone()
    return dict(zip(("id", "why", "ref", "kind", "no", "day", "item", "units", "pack", "made_at", "job_key", "printed_at", "state", "stamp", "closed_how"), r)) if r else None


def scan_open(con, kind, no, day):
    """True while a 'cut' print ask of this voucher is open: the one-item register route waits (plan 2.4)."""
    try:
        return bool(_has(con, "stock_voucher_scanask") and con.execute(
            "SELECT 1 FROM stock_voucher_scanask WHERE why='cut' AND ref=? AND state IN ('card','printed')", ("%s:%s:%s" % (kind, no, day),)).fetchone())
    except sqlite3.Error:
        return False


def timed_out(con, a):
    d = qdays(con)
    return _age_days(a.get("printed_at") or a.get("made_at")) >= d


# ------------------------------------------------------------------ a scan for a claim (voucher_inquiry calls it)
def claim_scan(con, a, forms, units, pack, S=None):
    """The scan that answers a claim's print ask: ('hit', scan) the scan holds the item at the asked quantity . ('qty', scan, printed) the item
    is on it at another quantity . ('miss', scan) the voucher Amir named is scanned and lacks the item . None: nothing yet."""
    S = scans() if S is None else S
    if not S:
        return None
    VJ = _VJ()
    made = str(a.get("made_at") or "")
    no = a.get("no") or ""
    lo = ""
    try:
        lo = (dt.date.fromisoformat(str(a.get("day") or "")[:10]) - dt.timedelta(days=1)).isoformat()   # the judge's own rule: day >= ask day - 1
    except ValueError:
        pass
    best = None
    for s in S:
        if s["kind"] and s["kind"] != a.get("kind"):
            continue
        if no and s["no"] != no:
            continue
        late = not s["at"] or s["at"][:16] >= made[:16]      # the scan app stamps to the minute
        if not no and not late:
            continue                                          # a numberless claim: only a scan made after its card
        if lo and s["day"] and s["day"] < lo:
            continue
        held = [ln for ln in s["lines"] if _holds(VJ, forms, ln)]
        if held:
            if any(int(units) in _units(ln["qty"], pack) for ln in held):
                return ("hit", s)
            best = best or ("qty", s, ", ".join(_q(ln["qty"]) if ln["qty"] not in (None, "") else "not readable" for ln in held))
        elif no and s["lines"] and late:                      # review M2: only a scan made after THIS card says 'it lacks the item'
            best = best or ("miss", s)
    return best


# ------------------------------------------------------------------ a scan names a cut line
def name_cut(con, a, lines, S=None):
    """a: the cut ask; lines: Marg's report lines of that voucher still ambiguous [dict(n, printed, ambiguous=[full names], qty, units, per)].
    -> ('named', scan, k) . ('unclear', scan) . None (no scan of that voucher yet). Writes mi_voucher_name (the caller commits)."""
    S = scans() if S is None else S
    if not S:
        return None
    VJ = _VJ()
    for s in S:
        if s["no"] != a["no"] or (s["kind"] and s["kind"] != a["kind"]) or (s["day"] and a.get("day") and s["day"] != a["day"]):
            continue
        k = 0
        by_cut = {}
        for ln in sorted(lines, key=lambda x: int(x.get("n") or 0)):
            by_cut.setdefault(ln["printed"], []).append(ln)
        plan = []
        for cut, L in by_cut.items():
            cands = {norm(c) for ln in L for c in (ln.get("ambiguous") or [])}
            hits = []
            for sl in s["lines"]:
                m = sorted(c for c in cands if sl["name"] == c or VJ._prefix(sl["name"], c) or VJ._prefix(c, sl["name"]))
                if m:
                    hits.append((sl, m))
            if len(hits) != len(L) or any(len(m) != 1 for _sl, m in hits) or len({m[0] for _sl, m in hits}) != len(hits):
                return ("unclear", s)
            for ln, (sl, m) in zip(L, hits):
                pu = _units(sl["qty"], ln.get("per") or 1)
                if pu and ln.get("units") is not None and int(ln["units"]) not in pu:
                    return ("unclear", s)
                plan.append((ln, m[0]))
        VJ.ensure_names(con, seed=False)
        for ln, full in plan:
            if con.execute("INSERT OR IGNORE INTO mi_voucher_name (kind, no, n, printed, item, source, at) VALUES (?,?,?,?,?,?,?)",
                           (a["kind"], a["no"], int(ln["n"]), ln["printed"], full, "scan %s" % s["stamp"], dt.datetime.now().isoformat(timespec="seconds"))).rowcount:
                k += 1
            else:                                             # review S4: a name already there must be this one, or the scan settles nothing
                ex = con.execute("SELECT item FROM mi_voucher_name WHERE kind=? AND no=? AND n=?", (a["kind"], a["no"], int(ln["n"]))).fetchone()
                if not ex or norm(ex[0]) != norm(full):
                    return ("unclear", s)
        return ("named", s, k)
    return None


def cut_lines(con):
    """{(kind, no, day): [Marg's ambiguous lines]} dated on or after stock.scan_ask_from, none already asked by the register route."""
    frm = setting(con, FROM_KEY, "")
    if not frm:
        return {}
    VJ = _VJ()
    out = {}
    asked = set()
    if _has(con, "mi_voucher_regask"):
        asked = {(k, no, int(n)) for k, no, n in con.execute("SELECT kind, no, n FROM mi_voucher_regask")}
    for x in VJ.marg_lines(con):
        if not x.get("ambiguous") or not x.get("day") or x["day"] < frm or (x["kind"], x["no"], int(x.get("n") or 0)) in asked:
            continue
        out.setdefault((x["kind"], x["no"], x["day"]), []).append(x)
    return out


def cut_asks(con, pushes=None):
    """Open a print ask for every new cut voucher; settle / close the open ones. -> dict(counts). The caller holds no transaction."""
    out = dict(asked=0, named=0, closed=0)
    if not on(con):
        return out
    ensure(con)
    con.commit()
    C = cut_lines(con)
    S = None
    for (kind, no, day), L in sorted(C.items()):
        ref = "%s:%s:%s" % (kind, no, day)
        a = ask_of(con, "cut", ref)
        if a is None:
            items = sorted({ln["printed"] for ln in L})
            if open_ask(con, "cut", ref, kind, no, day, ", ".join(items)[:200]) is not None:
                out["asked"] += 1
                if pushes is not None:
                    pushes.append(("Voucher ka print chahiye", "%s — Marg mein naam kata hua" % no, "/finance/amir", "s973"))
            con.commit()
    if not _has(con, "stock_voucher_scanask"):
        return out
    for row in con.execute("SELECT why, ref FROM stock_voucher_scanask WHERE why='cut' AND state IN ('card','printed') ORDER BY id").fetchall():
        a = ask_of(con, *row)
        k = tuple(a["ref"].split(":", 2))
        L = C.get(k)
        if not L:
            if close_ask(con, a["id"], "named meanwhile -- nothing to scan"):
                out["closed"] += 1
            con.commit()
            continue
        if S is None:
            S = scans() or []
        res = name_cut(con, a, L, S)
        if res and res[0] == "named":
            close_ask(con, a["id"], "named by scan %s" % res[1]["stamp"], res[1]["id"], res[1]["stamp"])
            out["named"] += res[2]
        elif res and res[0] == "unclear":
            close_ask(con, a["id"], "scan %s unclear -- Marg's Stock Register asked" % res[1]["stamp"], res[1]["id"], res[1]["stamp"])
            out["closed"] += 1
        elif timed_out(con, a):
            close_ask(con, a["id"], "no scan in %d days -- Marg's Stock Register asked" % qdays(con))
            out["closed"] += 1
        con.commit()
    return out


# ------------------------------------------------------------------ 'Print diya' (amir_day calls it at once) and reception
def _doers(con):
    return [x.strip().lower() for x in str(setting(con, DOERS_KEY, DOERS_DEFAULT)).split(",") if x.strip()]


def _push_reception(con, title, body):
    sent = 0
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import order_rules as _OR                             # noqa: PLC0415
        res = []

        def _go():
            for u in _doers(con):
                try:
                    res.append(_OR._push(u, dict(kind="porders", title=title, body=body, url="/finance/porders/s454/billkaam", tag="s973", ttl=21600, renotify=True)))
                except Exception:                             # noqa: BLE001
                    res.append((0, 1))
        th = threading.Thread(target=_go, daemon=True)
        th.start()
        th.join(10)
        sent = sum(int(a or 0) for a, _b in list(res))
    except Exception:                                         # noqa: BLE001
        pass
    _audit(con, "s973_push", dict(to=_doers(con), title=title, body=body, sent=sent), "system")
    return sent


def after_print(con, job_id, who="amir"):
    """Amir tapped 'Print diya -- reception ko' on the card: the ask waits for reception's scan; ONE push to the reception logins. Never raises."""
    try:
        r = con.execute("SELECT key, said_at FROM amir_job WHERE id=?", (int(job_id),)).fetchone()
        m = re.match(r"^S973:prt:(\d+):[A-Z0-9]{0,8}$", str(r[0] if r else ""))
        if not m:
            return False
        sid = int(m.group(1))
        if not con.execute("UPDATE stock_voucher_scanask SET state='printed', printed_at=?, printed_by=? WHERE id=? AND state='card'",
                           (str(r[1] or now()), who, sid)).rowcount:
            con.rollback()
            return False
        a = con.execute("SELECT item, no FROM stock_voucher_scanask WHERE id=?", (sid,)).fetchone()
        con.execute("UPDATE stock_voucher_scanask SET told=1 WHERE id=?", (sid,))
        _audit(con, "s973_printed", dict(id=sid, who=who), who)
        con.commit()
        _push_reception(con, "Stock voucher scan karna hai", "%s — Amir ne print diya" % ((a[1] + " · ") if a and a[1] else "") + (a[0] if a else ""))
        con.commit()
        return True
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_scan: after_print stopped: %s" % str(ex)[:200], file=sys.stderr)
        return False


def intake_link(no, back):
    from urllib.parse import urlencode                        # noqa: PLC0415
    q = [("lane", "pharmacy")] + ([("bill_no", no)] if no else []) + [("from", back)]
    return "/scanapp/intake?" + urlencode(q)


def reception_lines(con):
    """Reception's lines on 'Aaj ka bill kaam': every print Amir handed over that no scan answers yet. READ ONLY. Never raises."""
    out = []
    try:
        if not _has(con, "stock_voucher_scanask"):              # a print already handed over is shown even with the switch off (review S8)
            return out
        rows = con.execute("SELECT id, why, kind, no, day, item, printed_at, made_at FROM stock_voucher_scanask WHERE state='printed' ORDER BY printed_at, id").fetchall()
        if not rows:
            return out
        S = scans() or []
        for sid, why, kind, no, day, item, pat, made in rows:
            if no and any(s["no"] == no and ((why == "cut" and (not s["day"] or not day or s["day"] == day))
                                             or (why != "cut" and (not s["at"] or s["at"][:16] >= str(made or "")[:16]))) for s in S):
                continue                                      # scanned: the next sync settles it
            if not no and any(s["at"] and s["at"][:16] >= str(pat or "")[:16] and (not s["kind"] or s["kind"] == kind) for s in S):
                continue
            out.append(dict(id=sid, why=why, no=no or "", item=item or "", at=str(pat or "")))
    except Exception as ex:                                   # noqa: BLE001
        print("voucher_scan: reception_lines stopped: %s" % str(ex)[:200], file=sys.stderr)
    return out


def view(con):
    """The owner's page: the open print asks and the last 20 closed. READ ONLY."""
    if not _has(con, "stock_voucher_scanask"):
        return []
    out = []
    for r in con.execute("SELECT id, why, no, day, item, state, made_at, printed_at, closed_at, closed_how, stamp FROM stock_voucher_scanask "
                         "ORDER BY (state='closed'), id DESC LIMIT 60").fetchall():
        out.append(dict(zip(("id", "why", "no", "day", "item", "state", "made_at", "printed_at", "closed_at", "closed_how", "stamp"), r)))
    return out

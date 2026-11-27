#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  voucher_inquiry.py  ·  v1.0  ·  kit S971_AMIR_BY_HIMSELF  ·  Session 538 (Sanjeevni)  ·  27-Nov-2026
#
#  KIT B OF S534_FINAL_BUILD_PLAN (D1090, D1091; his 'ok' on mock-ups v7/v9, his 'proceed' 15:10 IST 27-Nov): AMIR BY HIMSELF.
#  The writes the voucher judge (voucher_judge.py, read only) never makes:
#   * THE CLAIM CARD (plan 2.2): Amir tapped done on a correction and Marg's NEWER Stock Issue / Receive report still lacks it -> back on his
#     card by itself: 'Ab bana diya' (the next report decides) . 'Pehle bana chuka hoon' (-> the owner's list: the print-and-scan of that
#     voucher comes with kit C). Still missing after 'Ab bana diya' and the next report -> the owner's list. Only taps on or after the
#     install day (setting stock.claim_from): nothing old reaches Amir.
#   * THE EXPORT LINE: a done tap waiting for a newer report -> ONE line on the owner's list, however many wait.
#   * THE INQUIRY (plan 2.5): a voucher nobody asked for, dated on or after his rule date (stock.voucher_rule_from): (a) the system looks
#     first -- an ask it answers (the judge: keyed before the ask) . an issue and a receive that cancel (the judge) . a move between two
#     batches of one item . Marg equal to the shelf after it -> explained, closed, counted; (b) else ONE question on Amir's card, five
#     one-tap answers; (c) each answer its own check: a mistake -> the exact reversal on his card, closed by the next report . a count
#     difference -> a recount on Darpan's next list (agrees -> explained; not -> the reversal to Amir + a line on the owner's list) . a
#     batch fix -> the next Batch Stock export (the Expiry watch judges batches every night) . damaged / expiry -> the owner's one tap;
#     (d) the owner's list only when the path ends unsettled: 'Pata nahi', no answer in stock.inq_question_days days, a recount that
#     disagrees -> Reverse or Close (his OK, an optional line); (e) the tally, his only.
#   * THE LOSS REGISTER (his word 17:17 IST 27-Nov): every desk write-off kept with its count, its group, its value at cost and at MRP
#     frozen at the tap, Marg's voucher once keyed; month totals; the 06-Sep full count's frozen runs beside; the pursued items' ends.
#  Every write is idempotent (unique keys, compare-and-set on state); a sync is fail-soft and never raises into a page.
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import threading

VERSION = "1.0"
KIT = "S971_AMIR_BY_HIMSELF"
HERE = os.path.dirname(os.path.abspath(__file__))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
RULE_KEY = "stock.voucher_rule_from"
QDAYS_KEY = "stock.inq_question_days"
CLAIM_KEY = "stock.claim_from"
BATCH_KEY = "stock.inq_batch_check"
CANCEL_KEY = "stock.voucher_cancel_days"
EARLY_KEY = "stock.voucher_early_days"
SYNC_KEY = "stock.inq_synced_at"
RECOUNT_DAYS = 7                                             # a recount the inquiry asked and Darpan has not made in this many days -> the owner's list
SYNC_EVERY = 300                                             # seconds: Amir's page and the Hub sync at most this often; the owner's desk always
AMIR = "amir"
ANS = ("vmistake", "vcount", "vbatch", "vdump", "unknown")   # amir_day.S814_ANS carries their Hindi words
CLM_ANS = ("made", "already")
OPEN_INQ = ("asked", "recount", "batch", "dump", "yours", "reversing", "early")   # early: told as an ask keyed before it was asked -- watched every sync
SETTINGS = (dict(k=RULE_KEY, label="Rule date: a voucher nobody asked for starts the inquiry from", kind="date", default=""),
            dict(k=QDAYS_KEY, label="Days before Amir's unanswered question reaches your list", kind="int", default=2, lo=1, hi=14),
            dict(k=CANCEL_KEY, label="An issue and a receive of the same item and quantity cancel within (days)", kind="int", default=7, lo=0, hi=30),
            dict(k=EARLY_KEY, label="A voucher keyed before the system asked still answers the ask within (days)", kind="int", default=7, lo=0, hi=30),
            dict(k=BATCH_KEY, label="Wrong-batch check against Marg's Batch Stock (the Expiry watch, every night)", kind="onoff", default="on"),
            dict(k=CLAIM_KEY, label="Amir's done taps checked against Marg's newer report from", kind="date", default=""))

DDL = ("CREATE TABLE IF NOT EXISTS stock_voucher_claim (id INTEGER PRIMARY KEY, ask_ref TEXT NOT NULL, round INTEGER NOT NULL DEFAULT 1, kind TEXT, "
       "item TEXT, units INTEGER, pack INTEGER, ask_text TEXT, src TEXT, done_day TEXT, typed TEXT, made_at TEXT NOT NULL, job_key TEXT, answer TEXT, "
       "answered_at TEXT, state TEXT NOT NULL, closed_at TEXT, closed_how TEXT, closed_by TEXT, note TEXT, UNIQUE (ask_ref, round))",
       "CREATE TABLE IF NOT EXISTS stock_voucher_inquiry (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, no TEXT NOT NULL, day TEXT, lines_json TEXT, "
       "made_at TEXT NOT NULL, state TEXT NOT NULL, job_key TEXT, answer TEXT, answered_at TEXT, rec_json TEXT, rev_json TEXT, how_json TEXT, "
       "disagree INTEGER NOT NULL DEFAULT 0, closed_at TEXT, closed_how TEXT, closed_by TEXT, note TEXT, UNIQUE (kind, no, day))",
       "CREATE TABLE IF NOT EXISTS stock_inquiry_job (job_key TEXT PRIMARY KEY, inquiry_id INTEGER, kind TEXT, item TEXT, pack INTEGER, units INTEGER, made_at TEXT)")


# ------------------------------------------------------------------ small things
def now():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def today():
    return dt.datetime.now(IST).date().isoformat()


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (t,)).fetchone() is not None


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().upper())


def dm(iso):
    s = str(iso or "")
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) >= 10 else s


def dmy(iso):
    s = str(iso or "")[:10]
    return "%s-%s-%s" % (s[8:10], s[5:7], s[:4]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else s


def _VJ():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import voucher_judge                                      # noqa: PLC0415 -- beside this file
    return voucher_judge


def _SW():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import stock_watch                                        # noqa: PLC0415
    return stock_watch


def ensure(con):
    for d in DDL:
        con.execute(d)
    con.execute("CREATE INDEX IF NOT EXISTS ix_s971_claim_state ON stock_voucher_claim (state)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_s971_inq_state ON stock_voucher_inquiry (state)")


def setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if (r and r[0] is not None and str(r[0]).strip() != "") else default
    except sqlite3.Error:
        return default


def int_setting(con, key):
    spec = next(s for s in SETTINGS if s["k"] == key)
    try:
        v = int(str(setting(con, key, spec["default"])).strip())
        return v if spec["lo"] <= v <= spec["hi"] else spec["default"]
    except (TypeError, ValueError):
        return spec["default"]


def _audit(con, action, after, who):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("stock_voucher_inquiry", 0, action, None, json.dumps(after, sort_keys=True, default=str), who or "", now()))
    except Exception:                                         # noqa: BLE001
        pass


def set_setting(con, key, value, who):
    """The page's settings (his, no code to change them). -> (ok, message)."""
    spec = next((s for s in SETTINGS if s["k"] == key), None)
    if spec is None:
        return False, "Not a setting of this page."
    v = str(value if value is not None else "").strip()
    if spec["kind"] == "date":
        if v:
            m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", v)
            v = "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else v
            try:
                d = dt.date.fromisoformat(v)
            except ValueError:
                return False, "A date, please (dd-mm-yyyy)."
            if d.isoformat() > today():
                return False, "Not a day still to come."
            v = d.isoformat()
        elif key == CLAIM_KEY:
            return False, "This one keeps a date."
    elif spec["kind"] == "int":
        try:
            n = int(v)
        except ValueError:
            return False, "A whole number, please."
        if not spec["lo"] <= n <= spec["hi"]:
            return False, "Between %d and %d, please." % (spec["lo"], spec["hi"])
        v = str(n)
    else:
        v = "on" if v.lower() in ("on", "1", "yes", "true") else "off"
    old = setting(con, key, "")
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, v, "S971: the owner's setting on the Stock check page"))
    _audit(con, "s971_setting", dict(key=key, old=old, new=v), who)
    con.commit()
    return True, "Saved: %s = %s." % (spec["label"], (dmy(v) if spec["kind"] == "date" and v else (v or "not set")))


def settings_view(con):
    out = []
    for s in SETTINGS:
        v = setting(con, s["k"], s["default"])
        if s["kind"] == "int":
            v = int_setting(con, s["k"])
        out.append(dict(k=s["k"], label=s["label"], kind=s["kind"], v=(dmy(v) if s["kind"] == "date" and v else v),
                        raw=v, lo=s.get("lo"), hi=s.get("hi")))
    return out


def _words(con, item, units, pack, lang="hi"):
    """Quantity words through the one function (qty_words via stock_watch.qw); plain strips/tabs if it cannot be read."""
    try:
        SW = _SW()
        sp = SW.Spine()
        packing = (SW.item_info(con, sp, item) or {}).get("packing") or ""
        return SW.qw(int(units), int(pack or 1), packing, item, lang)
    except Exception:                                         # noqa: BLE001
        p = max(int(pack or 1), 1)
        u = int(units)
        if p == 1:
            return "%d nag" % u
        s, g = divmod(u, p)
        return ("%d patte" % s if s else "") + (" + " if s and g else "") + ("%d goli" % g if g else "") or "0"


def _push(con, title, body, url, tag):
    """One push to Amir's phone (order_rules._push: the same Web Push; ORDER_PUSH_STUB for a walk). Never raises; at most 8 s."""
    res = []
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import order_rules as _OR                             # noqa: PLC0415
        payload = dict(kind="amir", title=title, body=body, url=url, tag=tag, ttl=21600, renotify=True)

        def _go():
            try:
                res.append(_OR._push(AMIR, payload))
            except Exception:                                 # noqa: BLE001
                res.append((0, 1))
        th = threading.Thread(target=_go, daemon=True)
        th.start()
        th.join(8)
    except Exception:                                         # noqa: BLE001
        pass
    s = sum(int(a or 0) for a, _b in list(res))
    _audit(con, "s971_push", dict(to=AMIR, title=title, body=body, sent=s), "system")
    return s


def _job(con, key, kind, subject, text_hi, sub_hi, by):
    """One amir_job row (shown at once). -> its id, or None when the key exists (never two)."""
    ts = now()
    cur = con.execute("INSERT OR IGNORE INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                      (key, kind, subject, text_hi, sub_hi, ts, by, ts))
    return cur.lastrowid if cur.rowcount == 1 else None


def _withdraw_job(con, key, who="system"):
    """An open card line taken off Amir's card (done_how 'withdrawn': it asks nothing, the judge skips it). -> 1 / 0."""
    ts = now()
    return con.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what='withdrawn', done_at=?, done_how='withdrawn' WHERE key=? AND done_at IS NULL",
                       (ts, who, ts, key)).rowcount or 0


def _answer(con, key):
    """(code, said_at) of Amir's answer to an ask job, or (None, None)."""
    r = con.execute("SELECT said_what, said_at, done_how FROM amir_job WHERE key=?", (key,)).fetchone()
    if not r or r[2] == "withdrawn" or not r[0]:
        return None, None
    return str(r[0]).split("|", 1)[0], str(r[1] or "")


def _newest_export(con):
    """The newest Stock Issue / Receive report's export moment, 'YYYY-MM-DD HH:MM:SS' ('' when none)."""
    try:
        r = con.execute("SELECT MAX(exported) FROM mi_voucher_file WHERE ok=1").fetchone()
    except sqlite3.Error:
        return ""
    e = str((r or [""])[0] or "")
    m = re.match(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})", e)
    return "%s-%s-%s %s:%s:%s" % m.groups() if m else ""


def _export_after(con, kind, at):
    """True when a sound report of this kind was exported after `at` (a stamp) AND covers its day (review S7: a report to yesterday
    cannot hold a voucher made today)."""
    try:
        for e, to in con.execute("SELECT exported, date_to FROM mi_voucher_file WHERE ok=1 AND kind=?", (kind,)):
            m = re.match(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})", str(e or ""))
            if m and "%s-%s-%s %s:%s:%s" % m.groups() > str(at or "") and _VJ()._day(to) >= str(at or "")[:10]:
                return True
    except sqlite3.Error:
        pass
    return False


# ------------------------------------------------------------------ the sync (fail-soft; every step its own short commit)
def sync_maybe(con, force=False):
    """Amir's page and the Hub: at most once in SYNC_EVERY seconds; never inside a caller's open transaction. Never raises."""
    try:
        if con.in_transaction:
            return None
        if not (setting(con, RULE_KEY, "") or setting(con, CLAIM_KEY, "") or _open_rows(con)):
            return None                                       # nothing set, nothing open: a read stays a read (review S6)
        if not force:
            last = setting(con, SYNC_KEY, "")
            if last:
                try:
                    age = (dt.datetime.now(IST).replace(tzinfo=None) - dt.datetime.fromisoformat(last)).total_seconds()
                    if 0 <= age < SYNC_EVERY:
                        return None
                except ValueError:
                    pass
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (SYNC_KEY, dt.datetime.now(IST).replace(tzinfo=None, microsecond=0).isoformat(), "S971: the last sync"))
        con.commit()
        return sync(con)
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_inquiry: sync stopped: %s" % str(ex)[:200], file=sys.stderr)
        return None


def _open_rows(con):
    try:
        return bool(_has(con, "stock_voucher_inquiry") and con.execute("SELECT 1 FROM stock_voucher_inquiry WHERE state IN (%s) LIMIT 1"
                                                                        % ",".join("'%s'" % s for s in OPEN_INQ)).fetchone())
    except sqlite3.Error:
        return False


def sync(con, day=None, push=True):
    """One pass over the claims and the inquiry. -> dict(counts). Writes only rows of its own and amir_job lines of its own keys."""
    VJ = _VJ()
    if not (setting(con, RULE_KEY, "") or setting(con, CLAIM_KEY, "") or _open_rows(con)):
        return dict(ok=True, why="no dates set -- nothing to do")   # nothing written: a read stays a read
    ensure(con)
    con.commit()
    J = VJ.judge(con, day or today())
    if not J.get("ok"):
        return dict(ok=False, why="no report")
    RR = VJ.record_rows(con)
    out = dict(ok=True, claims=0, questions=0, reversals=0, closed=0)
    pushes = []
    _sync_claims(con, J, RR, out, pushes)
    _sync_inquiry(con, J, RR, out, pushes)
    if push and pushes:                                       # ONE push a sync, however many cards it put on his page
        if len(pushes) == 1:
            _push(con, *pushes[0])
        else:
            _push(con, "Marg ke %d kaam" % len(pushes), "; ".join(p[1] for p in pushes[:3]) + (" ..." if len(pushes) > 3 else ""), "/finance/amir", "s971")
        con.commit()
    return out


def _forms_of(VJ, a):
    f = set(a.get("forms") or {norm(a["item"])})
    if a.get("match"):
        f.add(norm(a["match"]["item"]))
    return f


def _sync_claims(con, J, RR, out, pushes):
    VJ = _VJ()
    since = setting(con, CLAIM_KEY, "")
    by_ref = {}
    for a in J["asks"]:                                       # one claim per ASK (a count batch holds several items: never by its group)
        if a["src"] in ("count", "job") and not a.get("superseded"):
            by_ref[a["id"]] = a
    # 1 · the open claims: closed by Marg's report, moot by the whole item, answered by Amir
    for cid, ref, rnd, st, key, ans_at, kind in con.execute("SELECT id, ask_ref, round, state, job_key, answered_at, kind FROM stock_voucher_claim "
                                                            "WHERE state IN ('card','made','yours') ORDER BY id").fetchall():
        a = by_ref.get(ref)
        ts = now()
        if a is None or a["state"] not in ("not_in_marg", "beyond"):
            how = "in Marg" if (a and a["state"] in ("in_marg", "part", "wrong_batch")) else "no longer asked"
            if con.execute("UPDATE stock_voucher_claim SET state='closed', closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state=?",
                           (ts, how, cid, st)).rowcount:
                if key:
                    _withdraw_job(con, key)
                out["closed"] += 1
            con.commit()
            continue
        V = VJ.whole_item(VJ.record_for(RR, _forms_of(VJ, a)), a["item"])
        if st == "card" and V["v"] in ("settled", "held"):
            if con.execute("UPDATE stock_voucher_claim SET state='closed', closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state='card'",
                           (ts, "Marg agrees with the shelf today -- nothing to key" if V["v"] == "settled" else V["word"][:80], cid)).rowcount:
                _withdraw_job(con, key)
                out["closed"] += 1
            con.commit()
            continue
        if st == "card":
            code, at = _answer(con, key)
            if code == "made":
                con.execute("UPDATE stock_voucher_claim SET state='made', answer='made', answered_at=? WHERE id=? AND state='card'", (at, cid))
            elif code == "already":
                con.execute("UPDATE stock_voucher_claim SET state='yours', answer='already', answered_at=? WHERE id=? AND state='card'", (at, cid))
            con.commit()
        elif st == "made" and a["state"] == "not_in_marg" and _export_after(con, kind, ans_at):
            con.execute("UPDATE stock_voucher_claim SET state='yours' WHERE id=? AND state='made'", (cid,))
            con.commit()
    # 2 · new claims: a done tap on or after the claim date that a newer report lacks
    if not since:
        return
    for ref, a in by_ref.items():
        if a["state"] != "not_in_marg" or not a.get("done_day") or a["done_day"] < since:
            continue
        if con.execute("SELECT 1 FROM stock_voucher_claim WHERE ask_ref=?", (ref,)).fetchone():
            continue                                          # one claim per ask; a further round only by his 'Back to Amir'
        V = VJ.whole_item(VJ.record_for(RR, _forms_of(VJ, a)), a["item"])
        if V["v"] in ("settled", "held"):
            continue
        _new_claim(con, a, 1, out, pushes)


def _claim_text(con, a):
    q = _words(con, a["item"], a["units"], a["pack"])
    who = ("Aapne %s (%s) bataya tha; Marg ki report mein is voucher par yeh item nahi hai." % (a["typed"], dm(a["done_day"])) if a.get("typed")
           else "Aapne %s ko 'Kar diya' bataya tha; Marg ki nayi report mein yeh voucher nahi hai." % dm(a["done_day"]))
    return "STOCK %s %s — %s. %s" % (a["kind"], q, a["item"], who)


def _new_claim(con, a, rnd, out, pushes):
    VJ = _VJ()
    ts = now()
    cur = con.execute("INSERT OR IGNORE INTO stock_voucher_claim (ask_ref, round, kind, item, units, pack, ask_text, src, done_day, typed, made_at, state) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,'card')", (a["id"], rnd, a["kind"], a["item"], int(a["units"]), int(a["pack"] or 1),
                                                                VJ._ask_line(a), VJ._src_word(a), a.get("done_day"), a.get("typed") or "", ts))
    if cur.rowcount != 1:
        con.rollback()
        return None
    cid = cur.lastrowid
    key = "S971:clm:%d" % cid
    if _job(con, key, "ask", a["item"], _claim_text(con, a), ",".join(CLM_ANS), "S971 (Marg's newer report lacks it)") is None:
        con.rollback()
        return None
    con.execute("UPDATE stock_voucher_claim SET job_key=? WHERE id=?", (key, cid))
    _audit(con, "s971_claim", dict(claim=cid, item=a["item"], ask=a["id"], round=rnd), "system")
    con.commit()
    out["claims"] += 1
    pushes.append(("Marg ka voucher nahi mila", "%s — Marg ki report mein nahi hai" % a["item"], "/finance/amir", "s971-clm"))
    return cid


# ------------------------------------------------------------------ the inquiry
def _unasked_by_voucher(J, rule):
    V = {}
    for ln in J["lines"]:
        if ln.get("day") and ln["day"] >= rule:
            V.setdefault((ln["kind"], ln["no"], ln["day"]), dict(day=ln["day"], lines=[]))["lines"].append(ln)
    return V


def _explain(con, J, RR, kind, no, day, rule, cancel_days, used=None):
    """({line key: how}, left, early): every line of the voucher the system explains, the lines it cannot, and the lines told only as an open
    ask keyed before it was asked (second look M1: one ask answers ONE line -- `used` across the sync; such a row stays open, re-judged)."""
    used = set() if used is None else used
    early = []
    VJ = _VJ()
    how, left = {}, []
    early_days = int_setting(con, EARLY_KEY)
    mine = [ln for ln in J["lines"] if ln["kind"] == kind and ln["no"] == no and ln.get("day") == day]
    free = [ln for ln in J["lines"] if ln.get("state") == "unasked"]
    open_asks = [a for a in J["asks"] if a["state"] in ("waiting", "not_in_marg", "beyond", "gap") and a["src"] in ("count", "job")]
    for ln in mine:
        if ln.get("state") == "twice":                        # keyed twice is not an explanation: Amir is asked (a duplicate -> 'Galti se bana')
            left.append(ln)
            continue
        if ln.get("state") != "unasked":
            how[ln["key"]] = {"asked": "answers an ask", "cancel": "keyed and undone -- no effect",
                              "sum": "answers two asks in one line"}.get(ln.get("state"), "judged: " + str(ln.get("word") or ln.get("state")))
            continue
        pair = next((y for y in free if y is not ln and y["kind"] != ln["kind"] and norm(y["item"]) == norm(ln["item"]) and int(y["units"]) == int(ln["units"])
                     and VJ.bnorm(y.get("batch")) != VJ.bnorm(ln.get("batch")) and y.get("day") and ln.get("day")
                     and abs((dt.date.fromisoformat(y["day"]) - dt.date.fromisoformat(ln["day"])).days) <= cancel_days), None)
        if pair:
            how[ln["key"]] = "a move between two batches of one item (with %s %s)" % (pair["no"], dm(pair["day"]))
            continue
        R = VJ.record_for(RR, {norm(ln["item"])})
        if R is not None and R.get("gap_units") is not None and abs(float(R["gap_units"])) < 0.5 and R.get("state") not in ("consumable", "marg_behind", "no_shelf"):
            how[ln["key"]] = "Marg equals the shelf after it (Marg %s)" % VJ.st(int(round(float(R.get("marg_units") or 0))), int(R.get("pack") or 1))
            continue
        # an open ask it answers, keyed before the system asked: the same kind, item and units, within early_days before the ask, and AFTER the
        # figure the ask was measured against (review M1: never a line already inside Marg's figure). Told here; the judge never takes it.
        fit = None
        for a in open_asks:
            if a["id"] in used or a["kind"] != ln["kind"] or int(a["units"]) != int(ln["units"]) or not VJ.name_match(set(a.get("forms") or {norm(a["item"])}), ln["item"]):
                continue
            if not a.get("day") or ln["day"] >= a["day"] or (dt.date.fromisoformat(a["day"]) - dt.date.fromisoformat(ln["day"])).days > early_days:
                continue
            Ra = VJ.record_for(RR, set(a.get("forms") or {norm(a["item"])}))
            if Ra is None or not Ra.get("base_day") or ln["day"] <= str(Ra["base_day"])[:10]:
                continue
            fit = a
            break
        if fit:
            used.add(fit["id"])
            early.append(ln["key"])
            how[ln["key"]] = "looks like the ask of %s (%s) keyed before it was asked -- watched: once that ask is in Marg by another line, this one is asked of Amir" % (
                dm(fit["day"]), VJ._ask_line(fit))
            continue
        left.append(ln)
    return how, left, early


def _q_text(kind, no, day, lines):
    items = ", ".join("%s %s" % (ln["item"], _qtext(ln)) for ln in lines)
    return "%s (%s): STOCK %s — %s. System ne yeh nahi maanga tha. Kyon banaya?" % (no, dm(day), kind, items)


def _qtext(ln):
    per = max(int(ln.get("per") or 1), 1)
    u = int(ln["units"])
    if per == 1:
        return "%d nag" % u
    s, g = divmod(u, per)
    return ("%d patte" % s if s else "") + (" " if s and g else "") + ("%d goli" % g if g else "") or "0"


def _sync_inquiry(con, J, RR, out, pushes):
    rule = setting(con, RULE_KEY, "")
    cancel_days = int_setting(con, CANCEL_KEY)
    qdays = int_setting(con, QDAYS_KEY)
    byv = _unasked_by_voucher(J, rule) if rule else {}
    rows = {(r[1], r[2], r[9]): r for r in con.execute("SELECT id, kind, no, state, job_key, answered_at, rec_json, rev_json, made_at, day "
                                                       "FROM stock_voucher_inquiry").fetchall()}
    keys = set(byv) | {k for k, r in rows.items() if r[3] in OPEN_INQ}      # review S1: an open row is followed whatever became of the rule date
    used = set()                                              # second look M1: one open ask explains ONE line, oldest voucher first
    for key in sorted(keys, key=lambda k: (k[2], k[0], k[1])):
        kind, no, day = key
        v = byv.get(key) or dict(day=day, lines=[ln for ln in J["lines"] if ln["kind"] == kind and ln["no"] == no and ln.get("day") == day])
        r = rows.get(key)
        if r is None and not any(ln.get("state") == "unasked" for ln in v["lines"]):
            continue                                          # every line was asked: nothing to inquire
        if r is not None and r[3] not in OPEN_INQ:
            continue                                          # explained / reversed / closed: never judged again, never draws on an ask (re-look M1)
        ts = now()
        lim_q = (dt.datetime.now(IST) - dt.timedelta(days=qdays)).strftime("%Y-%m-%d %H:%M:%S")
        draws = r is None or (r[3] == "early" and str(r[8] or "") > lim_q)   # only a new row or a young 'early' row is told by an open ask
        how, left, early = _explain(con, J, RR, kind, no, day, rule, cancel_days, used if draws else set())
        if not draws and early:                               # re-look M1: every other row keeps its real lines (an old 'early' one is asked)
            left += [ln for ln in J["lines"] if ln["key"] in early]
            for k in early:
                how.pop(k, None)                              # re-look S2: no stale 'watched' words on a line now asked
            early = []
        if r is None:
            st = "asked" if left else ("early" if early else "explained")
            cur = con.execute("INSERT OR IGNORE INTO stock_voucher_inquiry (kind, no, day, lines_json, made_at, state, how_json, closed_at, closed_how, closed_by) "
                              "VALUES (?,?,?,?,?,?,?,?,?,?)", (kind, no, day, json.dumps([_lrow(ln) for ln in v["lines"] if ln.get("state") == "unasked"]),
                                                               ts, st, json.dumps(how), ts if st == "explained" else None,
                                                               "explained by the system" if st == "explained" else None, "system" if st == "explained" else None))
            if cur.rowcount != 1:
                con.rollback()
                continue
            iid = cur.lastrowid
            if st == "asked":
                jk = "S971:inq:%d" % iid
                if _job(con, jk, "ask", no, _q_text(kind, no, day, left), ",".join(ANS), "S971 (a voucher nobody asked for)") is None:
                    con.rollback()
                    continue
                con.execute("UPDATE stock_voucher_inquiry SET job_key=? WHERE id=?", (jk, iid))
                out["questions"] += 1
                pushes.append(("Stock voucher ka sawaal", "%s (%s): kyon banaya?" % (no, dm(day)), "/finance/amir", "s971-inq"))
            _audit(con, "s971_inquiry", dict(id=iid, kind=kind, no=no, day=day, state=st, how=how), "system")
            con.commit()
            continue
        iid, _k, _n, st, jk, ans_at, rec, rev, made_at, _d = r
        if st == "early":                                     # second look M1: re-judged every sync
            if left:                                          # the ask it looked like is answered by another line, or gone: asked of Amir now
                jk = "S971:inq:%d" % iid
                if con.execute("UPDATE stock_voucher_inquiry SET state='asked', how_json=?, made_at=?, job_key=? WHERE id=? AND state='early'",
                               (json.dumps(how), ts, jk, iid)).rowcount and _job(con, jk, "ask", no, _q_text(kind, no, day, left), ",".join(ANS),
                                                                                "S971 (a voucher nobody asked for)") is not None:
                    out["questions"] += 1
                    pushes.append(("Stock voucher ka sawaal", "%s (%s): kyon banaya?" % (no, dm(day)), "/finance/amir", "s971-inq"))
                    con.commit()
                else:
                    con.rollback()
            elif not early:
                con.execute("UPDATE stock_voucher_inquiry SET state='explained', how_json=?, closed_at=?, closed_how='explained by the system', closed_by='system' "
                            "WHERE id=? AND state='early'", (json.dumps(how), ts, iid))
                con.commit()
            else:
                con.execute("UPDATE stock_voucher_inquiry SET how_json=? WHERE id=? AND state='early'", (json.dumps(how), iid))
                con.commit()
            continue
        if st == "asked":
            if not left and not early:                        # explained since: the question leaves the card by itself
                if con.execute("UPDATE stock_voucher_inquiry SET state='explained', how_json=?, closed_at=?, closed_how='explained by the system', closed_by='system' "
                               "WHERE id=? AND state='asked'", (json.dumps(how), ts, iid)).rowcount:
                    _withdraw_job(con, jk)
                    out["closed"] += 1
                con.commit()
                continue
            code, at = _answer(con, jk)
            if code:
                if not left:                                  # never an answer with no lines to act on (re-look M1)
                    lj = con.execute("SELECT lines_json FROM stock_voucher_inquiry WHERE id=?", (iid,)).fetchone()
                    left = json.loads((lj[0] if lj else None) or "[]")
                _on_answer(con, iid, kind, no, code, at, left, out)
            continue
        if st == "recount":
            _check_recount(con, iid, kind, no, rec, RR, left, ans_at, out)
        elif st == "batch":
            if _batch_after(con, ans_at):
                con.execute("UPDATE stock_voucher_inquiry SET state='explained', closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state='batch'",
                            (ts, "a batch fix -- the newer Batch Stock is in; the Expiry watch judges the batches every night", iid))
                con.commit()
        elif st == "reversing":
            _check_reversal(con, J, iid, rev, out)
    lim = (dt.datetime.now(IST) - dt.timedelta(days=qdays)).strftime("%Y-%m-%d %H:%M:%S")
    con.execute("UPDATE stock_voucher_inquiry SET disagree=2 WHERE state='asked' AND disagree=0 AND made_at<=?", (lim,))
    con.commit()


def _lrow(ln):
    return dict(key=ln["key"], kind=ln["kind"], no=ln["no"], n=ln.get("n"), day=ln["day"], item=ln["item"], units=int(ln["units"]),
                per=int(ln.get("per") or 1), batch=ln.get("batch") or "")


def _pid_max(con, item):
    try:
        r = con.execute("SELECT MAX(id) FROM stock_point WHERE item_norm=?", (_SW().norm_name(item),)).fetchone()
        return int(r[0] or 0) if r else 0
    except Exception:                                         # noqa: BLE001
        return 0


def _on_answer(con, iid, kind, no, code, at, left, out):
    if code == "vmistake":
        if con.execute("UPDATE stock_voucher_inquiry SET state='reversing', answer=?, answered_at=? WHERE id=? AND state='asked'", (code, at, iid)).rowcount:
            _reverse(con, iid, kind, no, left, "Amir: galti se bana")
            out["reversals"] += 1
        con.commit()
    elif code == "vcount":
        rec = {ln["key"]: dict(item=ln["item"], pid=_pid_max(con, ln["item"])) for ln in left}   # review S2: kept with the state, one commit
        if not con.execute("UPDATE stock_voucher_inquiry SET state='recount', answer=?, answered_at=?, rec_json=? WHERE id=? AND state='asked'",
                           (code, at, json.dumps(rec), iid)).rowcount:
            con.rollback()
            return
        con.commit()
        SW = _SW()
        for x in rec.values():
            try:
                SW.ask(con, x["item"], "S971 inquiry", sp=SW.Spine(), mode=None)    # commits by itself
            except Exception:                                 # noqa: BLE001
                pass
    elif code == "vbatch" and str(setting(con, BATCH_KEY, "on")) == "off":
        con.execute("UPDATE stock_voucher_inquiry SET state='explained', answer=?, answered_at=?, closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state='asked'",
                    (code, at, now(), "a batch fix -- your batch check is off", iid))
        con.commit()
    elif code in ("vbatch", "vdump", "unknown"):
        st = {"vbatch": "batch", "vdump": "dump", "unknown": "yours"}[code]
        con.execute("UPDATE stock_voucher_inquiry SET state=?, answer=?, answered_at=? WHERE id=? AND state='asked'", (st, code, at, iid))
        con.commit()


def _batch_after(con, at):
    try:
        r = con.execute("SELECT MAX(at) FROM stock_batch_now").fetchone()
        return bool(r and r[0] and str(r[0]).replace("T", " ")[:19] > str(at or ""))
    except sqlite3.Error:
        return False


def _check_recount(con, iid, kind, no, rec, RR, left, ans_at, out):
    """The recount answers once the stock of record stands on a count of Darpan's made AFTER the question was answered (by the count's own
    id, never by clocks: review S11)."""
    VJ = _VJ()
    try:
        R0 = json.loads(rec or "{}")
    except ValueError:
        R0 = {}
    res, waiting = {}, False
    for k, x in R0.items():
        R = VJ.record_for(RR, {norm(x["item"])})
        hit = None
        if R is not None and R.get("base_kind") in ("spot", "darpan") and R.get("base_at"):
            try:
                hit = con.execute("SELECT id FROM stock_point WHERE item_norm=? AND id>? AND substr(replace(at,' ','T'),1,16)=substr(replace(?,' ','T'),1,16) "
                                  "AND source IN ('spot','darpan')", (_SW().norm_name(x["item"]), int(x.get("pid") or 0), str(R["base_at"]))).fetchone()
            except sqlite3.Error:
                hit = None
        if not hit or R.get("gap_units") is None:            # second look S3: no figure to judge yet -- still waiting, never 'disagrees'
            waiting = True
            continue
        res[k] = abs(float(R["gap_units"])) < 0.5
    ts = now()
    if waiting or not R0:
        lim = (dt.datetime.now(IST) - dt.timedelta(days=RECOUNT_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        if str(ans_at or "") and str(ans_at) <= lim:          # review S2: a recount never made reaches him
            con.execute("UPDATE stock_voucher_inquiry SET disagree=3 WHERE id=? AND state='recount' AND disagree=0", (iid,))
            con.commit()
        return
    if all(res.values()):
        con.execute("UPDATE stock_voucher_inquiry SET state='explained', closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state='recount'",
                    (ts, "Darpan's recount agrees with Marg after the voucher -- explained", iid))
        con.commit()
        return
    bad = [ln for ln in left if ln["key"] in res and not res[ln["key"]]]
    if not bad:                                               # re-look S1: the lines that disagree, from the row itself when no longer 'nobody asked'
        lj = con.execute("SELECT lines_json FROM stock_voucher_inquiry WHERE id=?", (iid,)).fetchone()
        bad = [x for x in json.loads((lj[0] if lj else None) or "[]") if x.get("key") in res and not res[x["key"]]]
    if not bad:
        con.execute("UPDATE stock_voucher_inquiry SET state='explained', closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state='recount'",
                    (ts, "explained since -- no line is left to reverse", iid))
        con.commit()
        return
    if con.execute("UPDATE stock_voucher_inquiry SET state='reversing', disagree=1 WHERE id=? AND state='recount'", (iid,)).rowcount:
        _reverse(con, iid, kind, no, bad, "Darpan's recount does not agree")
        out["reversals"] += 1
    con.commit()


def _reverse(con, iid, kind, no, lines, why):
    """The exact reversal of each line on Amir's card (one card per voucher, one 'Marg mein kar diya'); units in stock_inquiry_job. The key
    carries the voucher's day: Marg's numbers start again every year (review S10)."""
    opp = "RECEIVE" if kind == "ISSUE" else "ISSUE"
    keys = []
    for i_, ln in enumerate(lines):
        key = "S971:rev:%s:%s:%s:%s" % (kind, no, str(ln["day"]).replace("-", ""), ln.get("n") or i_ + 1)
        q = _qtext(ln)
        if _job(con, key, "tap", ln["item"], "%s — Marg mein STOCK %s kijiye: %s" % (ln["item"], opp, q),
                "%s (%s) ulta kariye" % (no, dm(ln["day"])), "S971 (%s)" % why) is not None:
            con.execute("INSERT OR REPLACE INTO stock_inquiry_job (job_key, inquiry_id, kind, item, pack, units, made_at) VALUES (?,?,?,?,?,?,?)",
                        (key, iid, opp, ln["item"], int(ln.get("per") or 1), int(ln["units"]), now()))
        keys.append(key)
    con.execute("UPDATE stock_voucher_inquiry SET rev_json=? WHERE id=?", (json.dumps(keys), iid))
    _audit(con, "s971_reverse", dict(id=iid, no=no, keys=keys, why=why), "system")


def _check_reversal(con, J, iid, rev, out):
    try:
        keys = json.loads(rev or "[]")
    except ValueError:
        keys = []
    if not keys:
        return
    st = {}
    for a in J["asks"]:
        for k in a.get("jobs") or [a.get("ref")]:
            if k in keys:
                st[k] = a["state"]
    if keys and all(st.get(k) == "in_marg" for k in keys):
        con.execute("UPDATE stock_voucher_inquiry SET state='reversed', closed_at=?, closed_how='reversed in Marg', closed_by='system' WHERE id=? AND state='reversing'",
                    (now(), iid))
        out["closed"] += 1
        con.commit()


# ------------------------------------------------------------------ the owner's taps (the desk's door calls these)
def act(con, act_, ref, who, note=""):
    """claim: back . cclose ; inquiry: reverse . close . dumpok. -> (ok, message)."""
    ensure(con)
    note = re.sub(r"\s+", " ", str(note or "")).strip()[:200]
    try:
        rid = int(ref)
    except (TypeError, ValueError):
        return False, "Which row?"
    ts = now()
    if act_ in ("back", "cclose"):
        r = con.execute("SELECT id, ask_ref, round, state, job_key FROM stock_voucher_claim WHERE id=?", (rid,)).fetchone()
        if not r or r[3] != "yours":
            return False, "That row no longer waits for you -- the page reads again."
        if act_ == "cclose":
            con.execute("UPDATE stock_voucher_claim SET state='closed', closed_at=?, closed_how='your OK', closed_by=?, note=? WHERE id=? AND state='yours'", (ts, who, note, rid))
            _audit(con, "s971_claim_close", dict(id=rid, note=note), who)
            con.commit()
            return True, "Closed with your OK."
        J = _VJ().judge(con)
        a = next((x for x in J["asks"] if x["id"] == r[1]), None)
        if a is None or a["state"] != "not_in_marg":
            return False, "Marg's report has it now, or it is no longer asked -- nothing sent."
        if not con.execute("UPDATE stock_voucher_claim SET state='closed', closed_at=?, closed_how='back to Amir', closed_by=? WHERE id=? AND state='yours'", (ts, who, rid)).rowcount:
            con.rollback()
            return False, "Already done."
        o, p = dict(claims=0), []
        nid = _new_claim(con, a, int(r[2]) + 1, o, p)
        for t in p:
            _push(con, *t)
        con.commit()
        return (True, "Back on Amir's card.") if nid else (False, "Not sent.")
    r = con.execute("SELECT id, kind, no, state, job_key, lines_json, rev_json, day, rec_json, disagree FROM stock_voucher_inquiry WHERE id=?", (rid,)).fetchone()
    if not r:
        return False, "That row is gone -- the page reads again."
    iid, kind, no, st, key, lj, rev, vday, rec, dis = r
    lines = json.loads(lj or "[]")
    if act_ == "dumpok":
        if st != "dump":
            return False, "That row no longer waits for your OK."
        con.execute("UPDATE stock_voucher_inquiry SET state='closed', closed_at=?, closed_how='damaged / expiry -- your OK', closed_by=?, note=? WHERE id=? AND state='dump'",
                    (ts, who, note, iid))
        _audit(con, "s971_inq_dumpok", dict(id=iid, no=no), who)
        con.commit()
        return True, "%s closed as damaged / expiry, with your OK." % no
    if act_ == "reverse":
        if not (st in ("yours", "dump") or (st == "asked" and dis == 2) or (st == "recount" and dis == 3)):
            return False, "That row no longer offers Reverse -- the page reads again."
        if not con.execute("UPDATE stock_voucher_inquiry SET state='reversing', closed_by=? WHERE id=? AND state=?", (who, iid, st)).rowcount:
            con.rollback()
            return False, "Already done."
        if key:
            _withdraw_job(con, key, who)
        J = _VJ().judge(con)
        left = [ln for ln in J["lines"] if ln["kind"] == kind and ln["no"] == no and ln.get("day") == vday and ln.get("state") in ("unasked", "twice")] or \
               [dict(key=x["key"], kind=x["kind"], no=x["no"], n=x.get("n"), day=x["day"], item=x["item"], units=x["units"], per=x["per"]) for x in lines]
        _reverse(con, iid, kind, no, left, "your Reverse")
        con.commit()
        if st == "recount":                                   # second look S2: the recount leaves Darpan's list too
            _withdraw_recount(con, rec, who)
        _push(con, "Marg mein theek kariye", "%s ulta kariye" % no, "/finance/amir", "s971-rev")
        con.commit()
        return True, "The reversal of %s is on Amir's card -- the next report closes it." % no
    if act_ == "close":
        if st not in OPEN_INQ:
            return False, "That row is already closed."
        if not con.execute("UPDATE stock_voucher_inquiry SET state='closed', closed_at=?, closed_how='your OK', closed_by=?, note=? WHERE id=? AND state=?",
                           (ts, who, note, iid, st)).rowcount:
            con.rollback()
            return False, "Already done."
        n = _withdraw_job(con, key, who) if key else 0
        for k in json.loads(rev or "[]"):
            n += _withdraw_job(con, k, who)
        if st == "recount":                                   # review S11: his Close takes the inquiry's recount off Darpan's list too
            _withdraw_recount(con, rec, who)
        _audit(con, "s971_inq_close", dict(id=iid, no=no, note=note, withdrawn=n), who)
        con.commit()
        return True, "%s closed with your OK%s." % (no, (" -- %d line%s taken off Amir's card" % (n, "" if n == 1 else "s")) if n else "")
    return False, "Unknown button."


def _withdraw_recount(con, rec, who):
    SW = _SW()
    for x in json.loads(rec or "{}").values():
        for (aid,) in con.execute("SELECT id FROM stock_watch_ask WHERE item_norm=? AND by='S971 inquiry' AND done_at IS NULL", (SW.norm_name(x["item"]),)).fetchall():
            try:
                SW.withdraw_ask(con, aid, who)
            except Exception:                                 # noqa: BLE001
                pass


def withdraw_writeoff(con, item, who, key=None):
    """S969's red 'not to be keyed' row: his desk write-off of the item, not yet keyed by Amir, taken off Amir's card -- the one the row
    names (review S9). -> (ok, message)."""
    r = con.execute("SELECT d.id, d.job_key FROM stock_desk_action d JOIN amir_job a ON a.key=d.job_key WHERE d.kind='writeoff' AND d.item_norm=? "
                    "AND a.done_at IS NULL AND (? IS NULL OR d.job_key=?) ORDER BY d.id DESC LIMIT 1", (norm(item), key, key)).fetchone()
    if not r:
        return False, "Amir has already tapped it done, or it is gone -- nothing withdrawn."
    if not _withdraw_job(con, r[1], who):
        con.rollback()
        return False, "Already withdrawn."
    con.execute("INSERT INTO stock_desk_action (kind, item, item_norm, box, day, at, by, note) VALUES ('withdraw',?,?,'way',?,?,?,?)",
                (item, norm(item), today(), now().replace(" ", "T"), who, "withdrew %s" % r[1]))
    _audit(con, "s971_withdraw_writeoff", dict(item=item, key=r[1]), who)
    con.commit()
    return True, "Withdrawn: %s is off Amir's card -- not to be keyed." % item


# ------------------------------------------------------------------ the owner's views (the desk, the Hub)
def export_need(con, J):
    """The ONE export line: done taps waiting for a newer report, and claims answered 'Ab bana diya' with no report since."""
    wait = [a for a in J["asks"] if a["state"] == "beyond" and a.get("done_day") and a["src"] in ("count", "job")]
    made = []
    if _has(con, "stock_voucher_claim"):
        made = [r[0] for r in con.execute("SELECT item FROM stock_voucher_claim WHERE state='made'")]
    n = len({a["group"] for a in wait}) + len(made)
    if not n:
        return None
    R = J.get("reports") or {}
    frm = min([v[0] for v in R.values() if v and v[0]] or [""])
    items = sorted({a["item"] for a in wait} | set(made))
    return dict(n=n, frm=dm(frm), to=dm(today()), items=items[:8],
                text="Take Marg's Stock Issue + Stock Receive (%s → today): %d correction%s Amir made wait%s for a newer report -- %s." % (
                    dm(frm), n, "" if n == 1 else "s", "s" if n == 1 else "", ", ".join(items[:4]) + (" and more" if len(items) > 4 else "")))


INQ_WORD = dict(early="keyed before the ask -- watched", asked="question on Amir's card", recount="recount on Darpan's next list", batch="waits for the next Batch Stock export",
                dump="damaged / expiry -- your OK", yours="your call", reversing="reversal on Amir's card", reversed="reversed in Marg",
                explained="explained", closed="closed")
ANS_EN = dict(vmistake="made by mistake", vcount="a count difference", vbatch="a batch fix", vdump="damaged / expiry", unknown="'Pata nahi' (does not know)")


def claims_view(con):
    if not _has(con, "stock_voucher_claim"):
        return []
    out = []
    for r in con.execute("SELECT id, item, ask_text, src, done_day, typed, made_at, state, answer, answered_at, round, closed_at, closed_how, ask_ref FROM stock_voucher_claim "
                         "WHERE state IN ('card','made','yours') ORDER BY id").fetchall():
        cid, item, ask, src, dd, typed, made, st, ans, aat, rnd, _c, _h, aref = r
        path = [["ok", "Asked: %s (%s); Amir tapped done %s%s." % (ask, src, dm(dd), (" and noted %s" % typed) if typed else "")],
                ["ok", "Marg's newer Stock %s report does not hold it -- back on Amir's card by itself %s%s." % (
                    "Issue" if "Issue" in ask else "Receive", dm(made), (" (round %d)" % rnd) if rnd > 1 else "")]]
        if st == "card":
            path.append(["now", "On Amir's card: 'Ab bana diya' or 'Pehle bana chuka hoon'."])
        elif st == "made":
            path.append(["now", "Amir %s: made it now -- the next Stock Issue / Receive report decides (asked on your list)." % dm(aat)])
        else:
            path.append(["bad", ("Amir %s: already made it -- Marg's report does not show it. Your call: Back to Amir, or Close. (The voucher's print and scan come with the next kit.)"
                                 if ans == "already" else "Amir made it %s -- Marg's newer report still does not show it. Your call: Back to Amir, or Close.") % dm(aat)])
        out.append(dict(id=cid, ask_ref=aref, item=item, fig=ask, state=st, path=path, acts=(["back", "cclose"] if st == "yours" else []),
                        tags=[["red" if st == "yours" else "amb", {"card": "on Amir's card -- not in Marg", "made": "Amir: made now -- next report",
                                                                    "yours": "your call"}[st]]]))
    return out


def inquiry_view(con, rule):
    """Box 4's rows (vouchers after the rule date): open first; the explained / closed folded; the tally of the month."""
    if not _has(con, "stock_voucher_inquiry"):
        return [], [], dict(month="", explained=0, reversed=0, closed=0, open=0)
    rows, done = [], []
    month = today()[:7]
    qd = int_setting(con, QDAYS_KEY)
    T = dict(month=month, explained=0, reversed=0, closed=0, open=0)
    for r in con.execute("SELECT id, kind, no, day, lines_json, made_at, state, job_key, answer, answered_at, rec_json, rev_json, how_json, disagree, closed_at, "
                         "closed_how, closed_by, note FROM stock_voucher_inquiry ORDER BY day DESC, no DESC").fetchall():
        iid, kind, no, day, lj, made, st, key, ans, aat, rec, rev, hj, dis, cat, chow, cby, note = r
        lines = json.loads(lj or "[]")
        how = json.loads(hj or "{}")
        if str(day or "")[:7] == month:
            T[{"explained": "explained", "reversed": "reversed", "closed": "closed"}.get(st, "open")] += 1
        path = [["ok", "Marg's %s %s of %s: %s -- nobody asked for it (your rule date %s)." % (
            "Issue" if kind == "ISSUE" else "Receive", no, dm(day), "; ".join("%s %s" % (x["item"], _qtext(x)) for x in lines), dmy(rule))]]
        mine = {x["key"]: x["item"] for x in lines}
        for k, h in how.items():
            if k not in mine:
                continue
            path.append(["ok", "System: %s -- %s." % (mine[k], h)])
        if st != "explained" or not how:
            if key:
                path.append(["ok", "Asked on Amir's card %s: 'Kyon banaya?'" % dm(made)])
            if ans:
                path.append(["ok", "Amir %s: %s." % (dm(aat), ANS_EN.get(ans, ans))])
        late = st == "asked" and dis == 2
        nowline = {"asked": ("bad", "No answer in %d day%s -- yours now: Reverse or Close (the question stays on his card)." % (qd, "" if qd == 1 else "s")) if late else ("now", "Waiting for Amir's answer."),
                   "recount": (("bad", "No recount in %d days -- yours now: Reverse or Close." % RECOUNT_DAYS) if dis == 3 else
                               ("now", "A recount of %s at the head of Darpan's next list -- agrees with Marg: explained; not: the reversal to Amir." %
                                (", ".join(sorted({x["item"] for x in json.loads(rec or "{}").values()})) or "the items"))),
                   "batch": ("now", "Waits for the next Batch Stock export; the Expiry watch judges the batches every night and asks Amir itself."),
                   "dump": ("now", "Damaged / expiry: your one tap (OK) closes it."),
                   "early": ("now", "Watched: it looks like Amir keyed an open ask before it was asked. Once that ask is in Marg by another line, this voucher is asked of Amir."),
                   "yours": ("bad", "Amir does not know why -- yours now: Reverse or Close."),
                   "reversing": ("bad" if dis == 1 else "now", ("Darpan's recount does not agree -- " if dis == 1 else "") +
                                 "the reversal is on Amir's card; the next report closes it."),
                   "reversed": ("ok", "Reversed in Marg -- closed by the report."),
                   "explained": ("ok", "Explained -- closed by itself."),
                   "closed": ("ok", "Closed%s%s." % ((" by " + str(cby)) if cby and cby != "system" else "", (" -- " + note) if note else ""))}.get(st)
        if nowline:
            path.append(list(nowline))
        acts = (["reverse", "close"] if (late or st == "yours" or (st == "recount" and dis == 3)) else ["dumpok", "reverse", "close"] if st == "dump"
                else ["close"] if st in ("asked", "recount", "batch", "reversing", "early") else [])
        red = late or st == "yours" or (st == "reversing" and dis == 1) or (st == "recount" and dis == 3)
        row = dict(id=iid, kind=kind, no=no, day=dm(day), iso=day, state=st, path=path, acts=acts, items=[x["item"] for x in lines],
                   fig="; ".join("%s %s" % (x["item"], _qtext(x)) for x in lines),
                   tags=[["red" if red else ("grn" if st in ("explained", "reversed", "closed") else "amb"), ("no answer -- yours" if late else INQ_WORD.get(st, st))]],
                   lines=lines)
        (done if st in ("explained", "reversed", "closed") else rows).append(row)
    rows.sort(key=lambda x: (0 if x["tags"][0][0] == "red" else 1, x["iso"] or ""), reverse=False)
    return rows, done, T


def owner_lines(con):
    """The Hub's Needs-you (amir_day.needs_you_lines carries them): the export line, the claims and inquiries that are his. Fail-soft."""
    out = []
    try:
        sync_maybe(con)
        VJ = _VJ()
        J = VJ.judge(con)
        if J.get("ok"):
            e = export_need(con, J)
            if e:
                out.append(dict(cls="warn", target="stock", href="/finance/stockcheck/#dk2", text=e["text"]))
        if _has(con, "stock_voucher_claim"):
            ys = [r[0] for r in con.execute("SELECT item FROM stock_voucher_claim WHERE state='yours' ORDER BY id")]
            if ys:
                out.append(dict(cls="bad", target="stock", href="/finance/stockcheck/#dk2",
                                text="Amir's correction still not in Marg's report -- your call: %s" % ", ".join(ys[:4]) + (" and more" if len(ys) > 4 else "")))
        if _has(con, "stock_voucher_inquiry"):
            rs = con.execute("SELECT no, state, disagree FROM stock_voucher_inquiry WHERE (state='asked' AND disagree=2) OR state IN ('yours','dump') "
                             "OR (state='reversing' AND disagree=1) OR (state='recount' AND disagree=3) ORDER BY day").fetchall()
            if rs:
                out.append(dict(cls="bad", target="stock", href="/finance/stockcheck/#dk4",
                                text="Voucher nobody asked for -- yours: %s" % ", ".join("%s (%s)" % (r[0], {"asked": "no answer", "yours": "Pata nahi", "dump": "damaged / expiry",
                                                                                                              "reversing": "recount disagrees", "recount": "no recount"}[r[1]]) for r in rs[:4])))
    except Exception as ex:                                   # noqa: BLE001
        print("voucher_inquiry: owner_lines stopped: %s" % str(ex)[:200], file=sys.stderr)
    return out


# ------------------------------------------------------------------ the loss register (his word 17:17 IST 27-Nov)
def value_of(con, item, units, pack):
    """(cost_p, mrp_p) of `units` of the item: cost from stock_rate (paise per unit, the purchase side), MRP from the typed MRP (per unit)
    else the spine's MRP (per strip / piece). None for a figure that cannot be read."""
    cost = mrp = None
    u = int(units or 0)
    try:
        r = con.execute("SELECT rate_p FROM stock_rate WHERE item=?", (item,)).fetchone()
        if r and r[0]:
            cost = int(round(float(r[0]) * u))
    except sqlite3.Error:
        pass
    try:
        r = con.execute("SELECT mrp_p FROM stock_mrp_manual WHERE item=?", (item,)).fetchone()
        if r and r[0]:
            mrp = int(round(float(r[0]) * u))
    except sqlite3.Error:
        pass
    if mrp is None:
        try:
            sp = _SW().Spine()
            m = sp.mrp_p(item) if getattr(sp, "ok", False) else None
            if m:
                mrp = int(round(float(m) * u / max(int(pack or 1), 1)))
        except Exception:                                     # noqa: BLE001
            pass
    return cost, mrp


def ensure_value_cols(con):
    if not _has(con, "stock_desk_action"):
        return
    cols = {r[1] for r in con.execute("PRAGMA table_info(stock_desk_action)")}
    for c, t in (("cost_p", "INTEGER"), ("mrp_p", "INTEGER"), ("priced", "TEXT")):
        if c not in cols:
            con.execute("ALTER TABLE stock_desk_action ADD COLUMN %s %s" % (c, t))


def backfill_values(con, word):
    """The installer: the write-offs made before this kit priced once, at install (the column 'priced' says so). -> n."""
    ensure_value_cols(con)
    n = 0
    for i, item, u, pk in con.execute("SELECT id, item, units, pack FROM stock_desk_action WHERE kind='writeoff' AND priced IS NULL").fetchall():
        c, m = value_of(con, item, u, pk)
        con.execute("UPDATE stock_desk_action SET cost_p=?, mrp_p=?, priced=? WHERE id=?", (c, m, word, i))
        n += 1
    con.commit()
    return n


def rupees(p):
    if p is None:
        return "—"
    v = int(p)
    s = "%d.%02d" % (abs(v) // 100, abs(v) % 100)
    w, f = s.split(".")
    if len(w) > 3:
        head, tail = w[:-3], w[-3:]
        head = ",".join(re.findall(r"\d{1,2}(?=(?:\d{2})*$)", head))
        w = head + "," + tail
    return ("−" if v < 0 else "") + "₹" + w + "." + f


def losses(con, J=None):
    """THE LOSS REGISTER: months (newest first), each with its lines and totals; the full-count runs; the pursued items. Read only."""
    VJ = _VJ()
    out = dict(months=[], runs=[], pursued=[])
    if _has(con, "stock_desk_action"):
        J = J or VJ.judge(con)
        jst = {}
        for a in J.get("asks") or []:
            for k in (a.get("jobs") or [a.get("ref")]):
                if str(k or "").startswith("S969:wo:"):
                    jst[k] = a
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_desk_action)")}
        vc = "cost_p, mrp_p, priced" if "cost_p" in cols else "NULL, NULL, NULL"
        M = {}
        for (i, item, pack, units, pid, pat, q, e, batch, key, box, day, at, by, cost, mrp, priced) in con.execute(
                "SELECT id, item, pack, units, point_id, point_at, qty_units, expected_units, batch, job_key, box, day, at, by, %s FROM stock_desk_action "
                "WHERE kind='writeoff' ORDER BY at, id" % vc).fetchall():
            jr = con.execute("SELECT done_at, done_how FROM amir_job WHERE key=?", (key,)).fetchone() if key else None
            wd = bool(jr and jr[1] == "withdrawn")
            a = jst.get(key)
            src = ""
            if pid:
                s = con.execute("SELECT source FROM stock_point WHERE id=?", (int(pid),)).fetchone()
                src = {"darpan": "Darpan", "spot": "spot morning"}.get((s or [""])[0], (s or [""])[0] or "")
            if wd:
                marg = "withdrawn %s -- not keyed" % dm(jr[0])
            elif a and a["state"] == "in_marg" and a.get("match"):
                marg = "%s %s" % (a["match"]["no"], dm(a["match"]["day"]))
            elif jr and jr[0]:
                marg = "Amir done %s -- %s" % (dm(jr[0]), "the next report decides" if (a and a["state"] == "beyond") else ("not in Marg's report" if a and a["state"] == "not_in_marg" else "waits for the report"))
            else:
                marg = "on Amir's card"
            ln = dict(id=i, day=dmy(day), item=item, q=VJ.st(int(units or 0), int(pack or 1)), count=("%s %s: counted %s, Marg %s" % (
                src or "count", dm(pat), VJ.st(int(round(float(q))), int(pack or 1)) if q is not None else "—", VJ.st(int(round(float(e))), int(pack or 1)) if e is not None else "—")) if pat else "—",
                group=("within the allowance" if box == "allow" else "your call"), cost=cost, mrp=mrp, cost_t=rupees(cost), mrp_t=rupees(mrp),
                priced=priced or "", marg=marg, withdrawn=wd, batch=batch or "", by=by or "")
            m = M.setdefault(str(day)[:7], dict(month=str(day)[:7], lines=[], n=0, cost=0, mrp=0, allow_cost=0, call_cost=0, unpriced=0))
            m["lines"].append(ln)
            if not wd:
                m["n"] += 1
                m["cost"] += cost or 0
                m["mrp"] += mrp or 0
                m["allow_cost" if box == "allow" else "call_cost"] += cost or 0
                m["unpriced"] += 1 if cost is None else 0
        for k in sorted(M, reverse=True):
            m = M[k]
            y, mo = k.split("-")
            m.update(label=dt.date(int(y), int(mo), 1).strftime("%B %Y"), cost_t=rupees(m["cost"]), mrp_t=rupees(m["mrp"]), allow_t=rupees(m["allow_cost"]),
                     call_t=rupees(m["call_cost"]))
            out["months"].append(m)
        for item, at, pid, units, pack in con.execute("SELECT item, at, point_id, units, pack FROM stock_desk_action WHERE kind='pursue' ORDER BY at DESC").fetchall():
            nx = con.execute("SELECT at, gap_units FROM stock_point WHERE item_norm=? AND at>? AND source IN ('spot','darpan') AND COALESCE(status,'') NOT IN "
                             "('superseded','recount','recounted') ORDER BY at LIMIT 1", (_SW().norm_name(item), str(at))).fetchone()
            end = ("waiting for Darpan's recount" if not nx else ("count error -- the recount agrees with Marg (%s)" % dm(nx[0])) if (nx[1] is None or abs(float(nx[1])) < 0.5)
                   else "still short at the recount (%s: %s) -- back to you" % (dm(nx[0]), VJ.st(int(round(-float(nx[1]))), int(pack or 1))))
            out["pursued"].append(dict(item=item, day=dmy(str(at)[:10]), q=VJ.st(int(units or 0), int(pack or 1)), end=end))
    if _has(con, "stock_writeoff_run"):
        for i, cid, at, n, mrp, cost, unp in con.execute("SELECT id, count_id, at, lines_n, mrp_p, cost_p, unpriced FROM stock_writeoff_run ORDER BY at").fetchall():
            out["runs"].append(dict(id=i, count_id=cid, day=dmy(str(at)[:10]), n=n, cost_t=rupees(cost), mrp_t=rupees(mrp), unpriced=unp))
    return out

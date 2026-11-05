#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_hand_change.py -- S706_HAND_CHANGE_WATCH (05-Nov-2026, Sanjeevni session 386; D828).

THE OWNER, 05-Nov-2026 10:05-10:36 IST: the stock differences "point to some unauthorized and unwanted activity ... changing the stocks
without my knowledge"; "make it tell me the next morning, naming the item and the day and the quantities shifted"; "this table ... goes to my
stock expiry page as a section on top, collapsed, with an alert so I open when needed".

WHAT IT FINDS: a change of Marg's stock that nothing in the system explains -- no sale, no sale return, no purchase, no purchase return, no
filed voucher of Amir's.  Per item, over Marg's daily closings (spine.db sp_close), E = Marg - the spine's own balance - Amir's filed vouchers
to that day.  A step in E between two closings is a shift.  NOT a hand change:
  * a purchase bill the system holds that Marg's closing did not have yet (the step equals minus one, two or three purchase lines of the
    last week) -- remembered as OWED, and Marg's later catch-up (a rise) pays it off first;
  * a step undone by the opposite step within the next three closings (a voucher filed a day late, a late keying);
  * two items moving the same quantity in opposite directions on the same closing whose names hold the same letters -- a RENAME in Marg
    (kept as kind 'rename': no stock moved, not announced).
A FALL is judged as soon as the closing's sales are in (the next morning).  A RISE is judged only once the purchase reports cover that day
(a delivery keyed before its bill reached the server must never be called a hand change).  Nothing before hand.from_day is judged.
Everything is recomputed from the spine at every refresh; a row that is no longer found (a late voucher, a late purchase return) is marked
'explained'; a row whose E has come back to its value before the shift is 'put right'.

WRITES ONLY its own table marg_hand_change and its setting rows.  Reads spine.db and finance.db's filed vouchers READ-ONLY (spine_build's own
reader).  Called by owner_notice's five-minute tick (refresh, only when the spine was rebuilt); the owner's Expiry watch page reads the table.

    /root/wa/venv/bin/python3 -B marg_hand_change.py show            (the rows)
    /root/wa/venv/bin/python3 -B marg_hand_change.py dry             (what it finds now; writes nothing)
    /root/wa/venv/bin/python3 -B marg_hand_change.py refresh         (recompute and store)
OFF: /root/finance/_off/ALL_OFF, /root/finance/spine/OFF, or the setting hand.on = off.
"""
import bisect
import collections
import datetime as dt
import itertools
import json
import os
import re
import sqlite3
import sys

KIT = "S706_HAND_CHANGE_WATCH"
HERE = os.path.dirname(os.path.abspath(__file__))
SPINE_DIR = os.path.join(HERE, "spine")
LIVE_DB = "/root/finance/finance.db"
SPINE_DB = os.environ.get("SPINE_DB") or os.path.join(SPINE_DIR, "spine.db")
RULES = os.path.join(SPINE_DIR, "spine_rules.json")
OFF_FLAGS = (os.path.join(HERE, "_off", "ALL_OFF"), os.path.join(SPINE_DIR, "OFF"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
PAGE = "/finance/sanjeevni/expiry"
TOL = 0.5

SETTINGS = (
    ("hand.on", "on", "S706: Marg stock changed with no bill, sale or voucher -- found, kept for the Expiry watch, told next morning (on / off)"),
    ("hand.from_day", "2026-10-01", "S706: no shift before this day is judged"),
    ("hand.new_days", "3", "S706: a row found within this many days counts as NEW on the page's red badge"),
    ("hand.built_seen", "", "S706: the spine build last read (set by the refresh)"),
    ("hand.since", "", "S706: set by the first fill -- rows found then are the history: on the page, never announced"),
)

SCHEMA = ("CREATE TABLE IF NOT EXISTS marg_hand_change (id INTEGER PRIMARY KEY, k20 TEXT NOT NULL, item TEXT NOT NULL, kind TEXT NOT NULL, "
          "day_from TEXT NOT NULL, day_to TEXT NOT NULL, marg_from REAL, marg_to REAL, system_moved REAL, shift REAL NOT NULL, pair_item TEXT, "
          "found_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', status_at TEXT, hist INTEGER NOT NULL DEFAULT 0, UNIQUE (k20, day_to, kind))")

# The owner's table of 05-Nov (S386, from S705's read of the live spine): why and the remedy, in his words-level English, by Marg's 20-letter key.
NOTES = {
    "ANKLE BINDER TYNOR X": ("Renamed in Marg around 10 Oct (TYNOR XL to XL TYNOR); the system sees two items.", "Mine: join the two names. Nets to zero; no Marg change."),
    "ANKLE BINDER XL TYNO": ("Renamed in Marg around 10 Oct (TYNOR XL to XL TYNOR); the system sees two items.", "Mine: join the two names. Nets to zero; no Marg change."),
    "VFER 500": ("Renamed in Marg 27-28 Oct (VFER 500 to V FER 500).", "Mine: join the names. The -14 left is Amir's earlier voucher, already explained."),
    "V FER 500": ("Renamed in Marg 27-28 Oct (VFER 500 to V FER 500).", "Mine: join the names. The -14 left is Amir's earlier voucher, already explained."),
    "CARTILOX SACHET": ("Changed by hand in Marg, 3 to 0 (24-25 Oct); no bill, sale or voucher.", ""),
    "CAST SHOE L TYNOR": ("Changed by hand in Marg, 1 to 0 (24-25 Oct); Amir's voucher was filed on size M.", ""),
    "EXLAIN A": ("Changed by hand in Marg, 12 to 0 (24-25 Oct).", ""),
    "RUNVACE TP": ("Changed by hand in Marg, 2 to 0 (24-25 Oct).", ""),
    "KNEE SUPPORT L HINGE": ("Changed by hand in Marg, 4 to 2 (24-25 Oct).", ""),
    "KNEE SUPPORT M HINGE": ("Changed by hand in Marg, 3 to 2 (24-25 Oct).", ""),
    "KNEE IMMOBILIZER L U": ("Changed by hand in Marg, 0 to 1 (24-25 Oct).", ""),
    "KNEE IMMOBILIZER M T": ("The sale of 24 Oct did not reduce Marg's stock.", ""),
    "CCM": ("Amir's voucher says -3; Marg moved -2.", ""),
    "ENZOMAC OINTMENT": ("Amir's voucher was filed on ENZOMAC PLUS, not the ointment.", ""),
    "GLI-ME SR1": ("Marg was below zero (-27: sold more than ever bought), then reset to 0 by hand.", "Shelf count decides. The purchase was never entered under this name."),
    "NORTIMER TAB": ("Marg was below zero (-9), then reset to 81 by hand.", "Shelf count decides. The purchase was never entered under this name."),
    "POWERGESIC 200 PATCH": ("Marg was below zero (-1), then reset by hand.", "Shelf count decides. The purchase was never entered under this name."),
}
NOTES_TO = "2026-11-04"          # the cold review's S5: the owner's table explains the shifts up to S705's read, not a later one
REMEDY = ("Count the shelf. Shelf = Marg: Marg is right, I record it in the system (nothing in Marg). Shelf = the system: Amir puts it back "
          "with one Marg voucher. Neither: it goes to your Loss desk.")
REMEDY_RENAME = "Mine: join the two names. No stock moved; no Marg change."


def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0)


def stamp(t):
    return t.strftime("%Y-%m-%d %H:%M:%S")


def K(n):
    return re.sub(r"\s+", " ", (n or "").strip())[:20].strip()


def dmon(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%d-%s" % (d.day, d.strftime("%b"))
    except ValueError:
        return str(iso or "")


def num(x):
    x = round(float(x or 0), 3)
    return ("%d" % x) if x == int(x) else ("%g" % x)


def snum(x):
    x = round(float(x or 0), 3)
    return ("+" if x > 0 else "") + num(x)


def setting(con, key):
    default = next((d for k, d, _n in SETTINGS if k == key), "")
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        return default
    return default if r is None or r[0] is None else str(r[0])


def ensure(con):
    con.execute(SCHEMA)
    for k, v, note in SETTINGS:
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    con.commit()


def off(con=None):
    for p in OFF_FLAGS:
        if os.path.exists(p):
            return os.path.basename(p)
    if con is not None and setting(con, "hand.on").strip().lower() != "on":
        return "hand.on"
    return ""


def _anagram(a, b):
    sa, sb = sorted(re.sub(r"[^A-Z0-9]", "", (a or "").upper())), sorted(re.sub(r"[^A-Z0-9]", "", (b or "").upper()))
    return bool(sa) and sa == sb


def _vouchers(finance_db):
    """Amir's filed vouchers {name: [(iso day, units)]} through the spine's own reader (S704; read-only, fail-soft -> {})."""
    if not finance_db:
        return {}
    path = list(sys.path)
    try:
        if SPINE_DIR not in sys.path:
            sys.path.insert(0, SPINE_DIR)
        import spine_build                                        # noqa: PLC0415
        return dict(spine_build.filed_vouchers(finance_db))
    except Exception:                                             # noqa: BLE001
        return {}
    finally:
        sys.path[:] = path


def _days(a, b):
    """ISO days a..b inclusive ('' or a bad date -> [])."""
    try:
        x, y = dt.date.fromisoformat(str(a)[:10]), dt.date.fromisoformat(str(b)[:10])
    except ValueError:
        return []
    return [(x + dt.timedelta(days=j)).isoformat() for j in range(0, (y - x).days + 1)] if y >= x else []


def _amir_days(finance_db):
    """Amir's punched days (amir_day) -- only he keys purchases and returns in Marg.  None when unreadable: then every day counts as his."""
    if not finance_db:
        return None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % finance_db, uri=True, timeout=30)
        try:
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_day'").fetchone():
                return None
            return {str(r[0])[:10] for r in con.execute("SELECT day FROM amir_day")}
        finally:
            con.close()
    except sqlite3.Error:
        return None


def _filed_count(finance_db):
    """How many voucher batches the spine's reader should return (B3; R2's N4: the reader's own rule -- the newest row of each batch carries
    a number, the batch is not voided, it has lines).  -1 when unreadable."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % finance_db, uri=True, timeout=30)
        try:
            have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"stock_voucher_entered", "stock_voucher_line"} <= have:
                return 0 if "stock_voucher_entered" not in have else (
                    1 if con.execute("SELECT 1 FROM stock_voucher_entered WHERE TRIM(COALESCE(marg_voucher_no,'')) <> '' LIMIT 1").fetchone() else 0)
            state = {}
            for cid, rno, kind, bno, vno in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no FROM stock_voucher_entered ORDER BY id"):
                state[(cid, rno, kind, bno)] = vno
            void = set()
            if "stock_voucher_void" in have:
                void = {tuple(r) for r in con.execute("SELECT count_id, round_no, kind, batch_no FROM stock_voucher_void")}
            lines = {tuple(r) for r in con.execute("SELECT DISTINCT count_id, round_no, kind, batch_no FROM stock_voucher_line WHERE item <> ''")}
            return sum(1 for k, v in state.items() if str(v or "").strip() and k not in void and k in lines)
        finally:
            con.close()
    except sqlite3.Error:
        return -1


def compute(spine_path=SPINE_DB, finance_db=LIVE_DB, from_day="2026-10-01", rules_path=RULES):
    """-> (rows, info).  Reads only.  rows: dicts k20, item, kind ('hand' | 'rename'), day_from, day_to, marg_from, marg_to, system_moved,
    shift, pair_item, settled.  Raises RuntimeError when Amir's filed vouchers cannot be read (nothing may be judged without them).
    A closing step is JUDGED only when: the sale exports cover every day of its window (an accepted SALE_BILLWISE range -- Sundays too);
    for a RISE, and for a FALL whose window holds an Amir day (only he keys purchases and returns), the purchase exports (bill-wise AND
    item-wise) cover the window and the week before it.  A closing printed with under 90% of its neighbours' items is skipped (a partial
    print).  Unjudged steps still pair renames, so a rename's falling half is never told alone."""
    sp = sqlite3.connect("file:%s?mode=ro" % spine_path, uri=True, timeout=30)
    try:
        meta = {r[0]: r[1] for r in sp.execute("SELECT key, value FROM sp_meta")}
        names = {}
        for k, n in sp.execute("SELECT k20, name FROM sp_item ORDER BY last_seen"):
            names[k] = n or k
        alias = {a: t for a, t, kind in sp.execute("SELECT alias, k20, kind FROM sp_alias") if kind != "rename_family"}
        try:
            fam = json.load(open(rules_path)).get("families", {}) or {}
        except (OSError, ValueError):
            fam = {}

        def Z(n):
            k = K(n)
            k = alias.get(k, k)
            t = fam.get(k, k)
            return t if isinstance(t, str) else k
        op = sp.execute("SELECT MIN(date) FROM sp_move WHERE kind='OPENING'").fetchone()[0] or "0000"
        cnt = {d: n for d, n in sp.execute("SELECT as_on, COUNT(*) FROM sp_close WHERE as_on > ? GROUP BY as_on", (op,))}
        allc = sorted(cnt)
        closings = []
        for i, d in enumerate(allc):                               # the cold review's S4: a partial print is not a closing
            nb = sorted(cnt[x] for x in allc[max(0, i - 3):i] + allc[i + 1:i + 4])
            med = nb[len(nb) // 2] if nb else 0
            if med and cnt[d] < 0.9 * med:
                continue
            closings.append(d)
        M = collections.defaultdict(dict)
        keep = set(closings)
        for d, k, u in sp.execute("SELECT as_on, k20, units FROM sp_close WHERE as_on > ?", (op,)):
            if d in keep:
                M[k][d] = float(u or 0)
        moves = collections.defaultdict(list)
        purch = collections.defaultdict(list)
        rets = collections.defaultdict(list)
        for k, d, kind, u in sp.execute("SELECT k20, date, kind, units FROM sp_move"):
            moves[k].append((d, float(u or 0)))
            if kind == "PURCHASE" and (u or 0) > 0:
                purch[k].append((d, float(u)))
            elif kind == "PURCHASE_RETURN" and (u or 0) < 0:
                rets[k].append((d, -float(u)))

        def cover(fams):
            out = set()
            for a, b in sp.execute("SELECT date_from, date_to FROM sp_export WHERE ok=1 AND family IN (%s)" % ",".join("?" * len(fams)), fams):
                out.update(_days(a, b))
            return out
        sale_cov = cover(("SALE_BILLWISE",))
        pur_cov = cover(("PURCHASE_BILLWISE",)) & cover(("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE"))
    finally:
        sp.close()
    filed = _filed_count(finance_db) if finance_db else 0
    vraw = _vouchers(finance_db)
    if filed < 0 or (filed > 0 and not vraw):
        raise RuntimeError("Amir's filed vouchers could not be read (%s batches on file) -- nothing judged" % filed)
    V = collections.defaultdict(list)
    for vname, rows in vraw.items():
        for vd, vu in rows:
            if vd and vd > op:
                V[Z(vname)].append((vd, float(vu or 0)))
    amir = _amir_days(finance_db)
    n = len(closings)
    win = [[]] + [_days((dt.date.fromisoformat(closings[i - 1]) + dt.timedelta(days=1)).isoformat(), closings[i]) for i in range(1, n)]
    sales_ok = [False] + [bool(win[i]) and all(x in sale_cov for x in win[i]) for i in range(1, n)]
    pur_ok = [False] + [all(x in pur_cov for x in _days((dt.date.fromisoformat(closings[i - 1]) - dt.timedelta(days=7)).isoformat(), closings[i]))
                        for i in range(1, n)]
    amir_in = [True] + [amir is None or any(x in amir for x in win[i]) for i in range(1, n)]
    cand = []
    for k in set(M) | {k for k in moves if any(d > op for d, _u in moves[k])}:
        mv = sorted(moves.get(k, []))
        vv = sorted(V.get(k, []))
        mvd, mvc = [d for d, _u in mv], list(itertools.accumulate(u for _d, u in mv))
        vvd, vvc = [d for d, _u in vv], list(itertools.accumulate(u for _d, u in vv))
        E, m_, s_ = [], [], []
        for d in closings:
            i_m, i_v = bisect.bisect_right(mvd, d), bisect.bisect_right(vvd, d)
            s = mvc[i_m - 1] if i_m else 0.0
            v = vvc[i_v - 1] if i_v else 0.0
            m = M.get(k, {}).get(d, 0.0)
            E.append(m - s - v)
            m_.append(m)
            s_.append(s + v)
        steps = [(i, round(E[i] - E[i - 1], 3)) for i in range(1, n) if abs(E[i] - E[i - 1]) >= TOL]
        skip = set()
        for x, (i, dlt) in enumerate(steps):                      # a step undone within the next three closings
            if i in skip:
                continue
            for j, dj in steps[x + 1:]:
                if j > i + 3:
                    break
                if j not in skip and abs(dlt + dj) < TOL:
                    skip.update((i, j))
                    break
        owed = owed_r = 0.0
        for i, dlt in steps:
            if i in skip or not sales_ok[i]:
                continue
            d1 = closings[i]
            lo = (dt.date.fromisoformat(closings[i - 1]) - dt.timedelta(days=7)).isoformat()

            def hit(lst):
                pl = [u for pd, u in lst if lo < pd <= d1]
                return len(pl) <= 12 and any(abs(abs(dlt) - sum(c)) < TOL for r in (1, 2, 3) for c in itertools.combinations(pl, r))
            if dlt < 0:
                pay = min(owed_r, -dlt)                            # Marg takes a return in later than its bill date
                owed_r -= pay
                dlt = round(dlt + pay, 3)
                if dlt > -TOL:
                    continue
                if hit(purch.get(k, [])):                          # a bill the system holds that Marg's closing did not have yet
                    owed += -dlt
                    continue
                judged = pur_ok[i] or not amir_in[i]
            else:
                pay = min(owed, dlt)
                owed -= pay
                dlt = round(dlt - pay, 3)
                if dlt < TOL:
                    continue
                if hit(rets.get(k, [])):                           # a return the system holds that Marg has not taken yet
                    owed_r += dlt
                    continue
                judged = pur_ok[i]
            if d1 < from_day:
                continue
            cand.append(dict(k20=k, item=names.get(k, k), day_from=closings[i - 1], day_to=d1, marg_from=m_[i - 1], marg_to=m_[i],
                             system_moved=round(s_[i] - s_[i - 1], 3), shift=dlt, e_before=E[i - 1], e_now=E[-1] if E else 0.0,
                             kind="hand" if judged else "wait", pair_item=""))
    by_day = collections.defaultdict(list)
    for c in cand:
        by_day[c["day_to"]].append(c)
    for d, cs in by_day.items():
        if len(cs) > 400:
            continue
        for a, b in itertools.combinations(cs, 2):
            if a["kind"] != "rename" and b["kind"] != "rename" and abs(a["shift"] + b["shift"]) < TOL and _anagram(a["item"], b["item"]):
                a["kind"] = b["kind"] = "rename"
                a["pair_item"], b["pair_item"] = b["item"], a["item"]
    cand = [c for c in cand if c["kind"] != "wait"]
    for c in cand:
        c["settled"] = abs(c.pop("e_now") - c.pop("e_before")) < TOL
    cand.sort(key=lambda c: (c["day_to"], c["item"]))
    judged_to = max([closings[i] for i in range(1, n) if sales_ok[i]] or [""])
    return cand, dict(built=meta.get("built", ""), closings=len(closings), skipped=len(allc) - len(closings), judged_to=judged_to,
                      last_pur=max(pur_cov) if pur_cov else "", op=op, amir_days=("unreadable: every day counts as his" if amir is None
                                                                                   else len(amir)), vouchers=filed)


def refresh(con, spine_path=SPINE_DB, finance_db=None, now=None, force=False):
    """Recompute and store; only when the spine was rebuilt since the last read (or force).  Never raises -> dict."""
    try:
        ensure(con)
        o = off(con)
        if o:
            return {"ok": True, "off": o}
        if not os.path.exists(spine_path):
            return {"ok": True, "skip": "no spine"}
        sp = sqlite3.connect("file:%s?mode=ro" % spine_path, uri=True, timeout=30)
        try:
            built = (sp.execute("SELECT value FROM sp_meta WHERE key='built'").fetchone() or [""])[0]
        finally:
            sp.close()
        if not force and built and built == setting(con, "hand.built_seen"):
            return {"ok": True, "same": built}
        if finance_db is None:
            finance_db = _main_path(con)
        first = not con.execute("SELECT 1 FROM marg_hand_change LIMIT 1").fetchone() and not setting(con, "hand.since")
        rows, info = compute(spine_path, finance_db, setting(con, "hand.from_day") or "2026-10-01")
        now = now or now_ist()
        t = stamp(now)
        found = set()
        new = 0
        for r in rows:
            found.add((r["k20"], r["day_to"], r["kind"]))
            cur = con.execute("INSERT OR IGNORE INTO marg_hand_change (k20, item, kind, day_from, day_to, marg_from, marg_to, system_moved, "
                              "shift, pair_item, found_at, status, status_at, hist) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (r["k20"], r["item"], r["kind"], r["day_from"], r["day_to"], r["marg_from"], r["marg_to"], r["system_moved"],
                               r["shift"], r["pair_item"], t, "put right" if r["settled"] else "open", t, 1 if first else 0))
            new += cur.rowcount or 0
            if not cur.rowcount:
                con.execute("UPDATE marg_hand_change SET item=?, day_from=?, marg_from=?, marg_to=?, system_moved=?, shift=?, pair_item=?, "
                            "status=CASE WHEN status=? THEN status ELSE ? END, status_at=CASE WHEN status=? THEN status_at ELSE ? END "
                            "WHERE k20=? AND day_to=? AND kind=?",
                            (r["item"], r["day_from"], r["marg_from"], r["marg_to"], r["system_moved"], r["shift"], r["pair_item"],
                             "put right" if r["settled"] else "open", "put right" if r["settled"] else "open",
                             "put right" if r["settled"] else "open", t, r["k20"], r["day_to"], r["kind"]))
        gone = 0
        edge = min(info["judged_to"] or "", info["last_pur"] or "")
        for rid, k, d, kind, st in con.execute("SELECT id, k20, day_to, kind, status FROM marg_hand_change").fetchall():
            if (k, d, kind) not in found and st != "explained" and d <= edge:     # the cold review's S6: only inside what is judged now
                con.execute("UPDATE marg_hand_change SET status='explained', status_at=? WHERE id=?", (t, rid))
                gone += 1
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    ("hand.built_seen", built, next(n for k, _d, n in SETTINGS if k == "hand.built_seen")))
        if first:                                                 # the first fill is the history: shown on the page, never announced, never 'new'
            con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                        ("hand.since", t, next(n for k, _d, n in SETTINGS if k == "hand.since")))
        con.commit()
        return {"ok": True, "built": built, "rows": len(rows), "new": new, "explained": gone, "judged_to": info["judged_to"],
                "last_pur": info["last_pur"]}
    except Exception as e:                                        # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return {"ok": False, "error": ("%s: %s" % (e.__class__.__name__, e))[:200]}


def _main_path(con):
    try:
        for r in con.execute("PRAGMA database_list").fetchall():
            if str(r[1]) == "main":
                return str(r[2] or "")
    except sqlite3.Error:
        pass
    return ""


# ------------------------------------------------------------------ what the owner sees
def rows_for_page(con):
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='marg_hand_change'").fetchone():
        return []
    con2 = con
    out = []
    for r in con2.execute("SELECT id, k20, item, kind, day_from, day_to, marg_from, marg_to, system_moved, shift, pair_item, found_at, status, "
                          "status_at, hist FROM marg_hand_change ORDER BY day_to DESC, item").fetchall():
        out.append(dict(zip(("id", "k20", "item", "kind", "day_from", "day_to", "marg_from", "marg_to", "system_moved", "shift", "pair_item",
                             "found_at", "status", "status_at", "hist"), tuple(r))))
    return out


def is_new(con, r, today, days=None):
    """Found after the first fill and within hand.new_days days -> the page's red badge."""
    hs = setting(con, "hand.since")
    try:
        days = int(days if days is not None else (setting(con, "hand.new_days") or 3))
    except ValueError:
        days = 3
    return bool(hs) and not r.get("hist") and r["found_at"][:10] >= (today - dt.timedelta(days=days)).isoformat()


def why_of(r):
    note = (NOTES.get(r["k20"]) or NOTES.get(K(r["item"]))) if str(r.get("day_to") or "") <= NOTES_TO else None
    if note and note[0]:
        return note[0]
    if r["kind"] == "rename":
        return "Renamed in Marg (%s): the same quantity left one name and arrived on the other." % (r.get("pair_item") or "")
    moved = float(r.get("system_moved") or 0)
    return ("Marg went %s to %s between %s and %s; the system moved %s (sales, bills and vouchers) — %s unexplained."
            % (num(r["marg_from"]), num(r["marg_to"]), dmon(r["day_from"]), dmon(r["day_to"]), snum(moved) if moved else "nothing",
               snum(r["shift"])))


def remedy_of(r):
    note = (NOTES.get(r["k20"]) or NOTES.get(K(r["item"]))) if str(r.get("day_to") or "") <= NOTES_TO else None
    if note and note[1]:
        return note[1]
    return REMEDY_RENAME if r["kind"] == "rename" else REMEDY


def message_groups(con, since, now, hours=36):
    """{found_at: [rows]} of kind 'hand', found after `since`, not the first fill (the history), within `hours` -- for owner_notice."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='marg_hand_change'").fetchone():
        return {}
    hs = setting(con, "hand.since")
    if not hs:
        return {}
    since = str(since or "~")
    floor = stamp(now - dt.timedelta(hours=hours))
    g = collections.OrderedDict()
    recent = (now.date() - dt.timedelta(days=10)).isoformat()     # S2 / R2's N2: a shift older than ten days found late is on the page, not told
    for r in con.execute("SELECT item, day_from, day_to, marg_from, marg_to, shift, found_at FROM marg_hand_change WHERE kind='hand' "
                         "AND status='open' AND hist=0 AND found_at > ? AND found_at >= ? AND day_to >= ? ORDER BY found_at, day_to, item",
                         (since or "~", floor, recent)).fetchall():
        g.setdefault(r[6], []).append(dict(item=r[0], day_from=r[1], day_to=r[2], marg_from=r[3], marg_to=r[4], shift=r[5]))
    return g


def message_line(r):
    return "%s: %s → %s (%s), between %s and %s" % (r["item"], num(r["marg_from"]), num(r["marg_to"]), snum(r["shift"]),
                                                     dmon(r["day_from"]), dmon(r["day_to"]))


def _connect(db, ro=False):
    return sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30) if ro else sqlite3.connect(db, timeout=30)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else ""
    db = os.environ.get("FINANCE_DB", LIVE_DB)
    if "--db" in argv:
        db = argv[argv.index("--db") + 1]
    spine = SPINE_DB
    if "--spine" in argv:
        spine = argv[argv.index("--spine") + 1]
    if cmd == "dry":
        con = _connect(db, ro=True)
        rows, info = compute(spine, db, setting(con, "hand.from_day") or "2026-10-01")
        print("S706 dry -- spine built %s; judged to %s; purchases covered to %s; %d closings (%d partial skipped); Amir days read %s; "
              "voucher batches %s" % (info["built"][:16], info["judged_to"], info["last_pur"], info["closings"], info["skipped"],
                                      info["amir_days"], info["vouchers"]))
        for r in rows:
            print("  %-6s %-30s %s -> %s  Marg %s -> %s  system %s  shift %s%s%s" % (
                r["kind"], r["item"][:30], r["day_from"], r["day_to"], num(r["marg_from"]), num(r["marg_to"]), snum(r["system_moved"]),
                snum(r["shift"]), ("  pair " + r["pair_item"]) if r["pair_item"] else "", "  (put right)" if r["settled"] else ""))
        print("S706 dry END -- %d row(s); nothing written" % len(rows))
        return 0
    if cmd == "refresh":
        con = _connect(db)
        print(json.dumps(refresh(con, spine, force=True), ensure_ascii=False))
        return 0
    if cmd == "show":
        con = _connect(db)
        ensure(con)
        for r in rows_for_page(con):
            print("%-10s %-6s %-30s %s->%s  %s  found %s" % (r["status"], r["kind"], r["item"][:30], r["day_from"], r["day_to"],
                                                           snum(r["shift"]), r["found_at"]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

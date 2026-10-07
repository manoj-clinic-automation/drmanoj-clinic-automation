#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s494.py -- kit S494_AMIR_JOBS_NOTICE_FLAGS (D686; F-765, F-767, F-771).

Four files of /root/finance are BUILT FROM THE LIVE BYTES by anchored edits: each anchor must occur exactly once in what the edits
before it left, else the build stops and nothing is written. Nothing here opens a database or the network.

    python3 -B make_s494.py --finance /root/finance --out DIR      -> DIR/<the four files>

  order_sheet.py    Part A (F-767): _can_push(); _sheet_notice keeps the text 'pending' when this process cannot push;
                    send_pending_notices() sends it from the tick (venv) -- same day, fresh, twice at most; cron_pass runs it
                    after the sheets; one setting order.sheet_notice_max_min (SETTINGS, seeded by ensure()).
  stock_watch.py    Part B (F-771): needs_you_lines -- the spot-count line once, the newest (that loop only).
  shelf_figure.py   Part C (F-765): rejudge() -- a first flag of the last stock.gap_rejudge_days days that a later report explains is
                    cleared, its later copies with it; never raises one. Called at the top of record_gaps, fail-soft.
  amir_day.py       Part D (D686): the table amir_job; Amir's one-time Marg jobs on his Marg sudhar card (the owner's words);
                    the tap (one form field on the step's own POST); the system's own part (_s494_refresh); the owner's lines;
                    _s446_left's one English line; the setting amir.job_wait_days.
"""
import argparse
import hashlib
import io
import os
import sys

KIT = "S494_AMIR_JOBS_NOTICE_FLAGS"
FROM = {
    "order_sheet.py": "16f21a6515a1317e1f6e31cb0a280513",
    "stock_watch.py": "4fc0f6017825975e75ebacfdc2f122d2",
    "shelf_figure.py": "0d836de54672f3e624fcc763311ab22c",
    "amir_day.py": "08d058a765278d6e119e70f8f0adeedd",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rd(p):
    with io.open(p, "rb") as fh:
        return fh.read()


def edit(name, src, pairs):
    """Anchored edits: every OLD must occur exactly once in what the edits before it left."""
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            raise SystemExit("!! %s: anchor %d occurs %d times, not once -- nothing built (%r)" % (name, i, n, old[:90]))
        src = src.replace(old, new)
    return src


# ================================================================================================================== Part A
SHEET_FUNCS = r'''

# ==========================================================================================================================================
# S494_AMIR_JOBS_NOTICE_FLAGS (07-Oct-2026, F-767) -- THE ARRIVAL NOTICE IS SENT BY A PROCESS THAT CAN SEND IT.
#   The web service runs /usr/bin/python3, which has no pywebpush: ring_common.send_push imports it inside its try, so in the web process
#   every phone answered 'failed' with no exception (06-Oct 15:40:43: 0 sent everywhere). _sheet_notice now keeps the text as
#   'pending' when this process cannot push, and order_rules' ten-minute tick (the venv, 05:00-21:50) sends it through cron_pass:
#   never on a later day, never once order.sheet_notice_max_min minutes have passed since the sheet was taken, never on another
#   order.source, and never more than twice (a send that failed everywhere is tried once more, and carries 'retried').
#   ORDER_PUSH_NONE (a walk's "web process") / ORDER_PUSH_STUB (the walk's file) serve the walk; the service never sets them.
# ==========================================================================================================================================
def _can_push():
    """Can THIS process send a Web Push? False under ORDER_PUSH_NONE; True under ORDER_PUSH_STUB; else only if pywebpush imports."""
    if os.environ.get("ORDER_PUSH_NONE"):
        return False
    if os.environ.get("ORDER_PUSH_STUB"):
        return True
    try:
        import pywebpush                                      # noqa: F401,PLC0415 -- the venv has it; /usr/bin/python3 does not
        return True
    except Exception:                                         # noqa: BLE001
        return False


def _s494_notice_shape(nt):
    """'pending', 'failed' (every login 0 sent, one failed at least, never retried / lapsed / dropped) or None."""
    if not isinstance(nt, dict) or any(k in nt for k in ("retried", "lapsed", "dropped")):
        return None
    if nt.get("pending") is True:
        return "pending"
    s = nt.get("sent")
    if not isinstance(s, dict) or not s:
        return None
    try:
        if all(int((v or {}).get("sent") or 0) == 0 for v in s.values()) and any(int((v or {}).get("failed") or 0) > 0 for v in s.values()):
            return "failed"
    except (AttributeError, TypeError, ValueError):
        return None
    return None


def send_pending_notices(con):
    """The tick's sender (S494 A.3): each order sheet whose arrival notice is pending, or failed everywhere once -- lapsed when it was
    taken on an earlier day or more than order.sheet_notice_max_min minutes ago; dropped on another order.source; left for the tick when
    this process cannot push; else the STORED text sent to order.notice_to. Returns the number of rows sent. Fail-soft per row."""
    out = 0
    try:
        rows = con.execute("SELECT id, taken_at, notice FROM order_sheet WHERE notice IS NOT NULL AND notice <> '' ORDER BY id").fetchall()
    except sqlite3.Error:
        return 0
    for sid, taken, raw in rows:
        try:
            try:
                nt = json.loads(raw)
            except (TypeError, ValueError):
                continue
            shape = _s494_notice_shape(nt)
            if not shape:
                continue

            def put(d):
                con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(d), sid))
                con.commit()
            t0 = _dtm(taken)
            if str(taken or "")[:10] != today().isoformat() or t0 is None \
                    or (now() - t0).total_seconds() / 60.0 > int_setting(con, "order.sheet_notice_max_min"):
                nt.update(lapsed=True, pending=False)
                put(nt)
                continue
            if source(con) != "marg_sheet":
                nt.update(dropped="source", pending=False)
                put(nt)
                continue
            if not _can_push():
                continue                                      # this process cannot: the tick will
            text = nt.get("text") or ""
            if not text:
                continue
            import order_rules                                # noqa: PLC0415
            to = [x.strip().lower() for x in order_rules._setting(con, "order.notice_to").split(",") if x.strip()]
            payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True,
                           ts=int(dt.datetime.now().timestamp() * 1000))
            sent = {}
            for u in to:
                try:
                    a, b = order_rules._push(u, payload)
                    sent[u] = dict(sent=a, failed=b)
                except Exception as e:                        # noqa: BLE001
                    sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
            new = dict(text=text, sent=sent, at=now_iso(), first_at=nt.get("first_at") or nt.get("at"), pending=False)
            if shape == "failed":
                new["retried"] = True
            put(new)
            out += 1
        except Exception as e:                                # noqa: BLE001 -- one row never stops the others
            print("order_sheet: notice of sheet %s not sent (%s)" % (sid, str(e)[:120]), file=sys.stderr)
    return out
# ---- S494 (Part A) end -------------------------------------------------------------------------------------------------------------------
'''


def build_order_sheet(src):
    return edit("order_sheet.py", src, [
        ('    "stock.gap_min_packs": ("1", "S454 P3 (9.3): a change of the gap between the shelf figure and Marg smaller than this many packs of the item "\n'
         '                                 "is not counted"),\n}\n',
         '    "stock.gap_min_packs": ("1", "S454 P3 (9.3): a change of the gap between the shelf figure and Marg smaller than this many packs of the item "\n'
         '                                 "is not counted"),\n'
         '    "order.sheet_notice_max_min": ("60", "Order sheet arrived: minutes after which the arrival notice is no longer sent"),   # S494 (F-767)\n}\n'),
        ('    text = "Darpan ki order sheet aa gayi: %d supplier, %d dawa." % (n[1], n[0])\n    try:\n        import order_rules',
         '    text = "Darpan ki order sheet aa gayi: %d supplier, %d dawa." % (n[1], n[0])\n'
         '    if not _can_push():                                       # S494 (F-767): the web process cannot push -- the tick sends it\n'
         '        con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(dict(text=text, pending=True, at=now_iso())), sid))\n'
         '        con.commit()\n'
         '        return\n'
         '    try:\n        import order_rules'),
        ('        con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(dict(text=text, error=str(e)[:100])), sid))\n    con.commit()\n',
         '        con.execute("UPDATE order_sheet SET notice=? WHERE id=?", (json.dumps(dict(text=text, error=str(e)[:100])), sid))\n    con.commit()\n'
         + SHEET_FUNCS),
        ('    for name, fn in (("sheets", load_pending), ("withdrawn", withdraw_late), ("refresh", refresh)):\n',
         '    for name, fn in (("sheets", load_pending), ("notices", send_pending_notices), ("withdrawn", withdraw_late), ("refresh", refresh)):   # S494: notices\n'),
    ])


# ================================================================================================================== Part B
def build_stock_watch(src):
    return edit("stock_watch.py", src, [
        ('        for n in notices(con, "owner"):\n'
         '            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():\n'
         '                out.append(',
         '        spot_seen = False                                      # S494 (F-771): one spot-count line -- the newest (notices: newest first)\n'
         '        for n in notices(con, "owner"):\n'
         '            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():\n'
         '                if n["kind"] == "spot_missed":\n'
         '                    if spot_seen:\n'
         '                        continue\n'
         '                    spot_seen = True\n'
         '                out.append('),
    ])


# ================================================================================================================== Part C
REJUDGE = r'''def _s494_ddmm_hm(ts):
    s = str(ts or "").replace("T", " ")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if len(s) >= 16 else s


def rejudge(con, sp=None):
    """S494 (F-765): A FLAG IS JUDGED AGAIN WHEN LATER EVIDENCE ARRIVES. record_gaps judges a closing once, when Marg's closing-stock report
    lands -- often before that day's sale or purchase report has reached the spine. Every first flag (an ORIGIN: flagged, its why written by
    record_gaps for its own closing -- 'Marg moved ... on <its own as_on>') of a closing within stock.gap_rejudge_days days of the newest is
    worked out again exactly as record_gaps works it, from the stored rows and the spine as it is now; when its move is now explained
    (|move - vouchers| < stock.gap_min_packs packs) it is cleared, and every later copy of it (the same item, flagged, the same why) with it.
    ONE DIRECTION ONLY: it never raises a flag and never touches an unflagged row, an approximate row or a flag whose origin lies before the
    window (the spine's evidence can shrink for a while -- F-737). Nothing is written when nothing clears. Returns the rows cleared."""
    if not _has(con, "s454_shelf_gap"):
        return 0
    newest = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap").fetchone()[0]
    if not newest:
        return 0
    try:
        days = int(float(_setting(con, "stock.gap_rejudge_days", "7")))
    except ValueError:
        days = 7
    try:
        lo = (dt.date.fromisoformat(str(newest)[:10]) - dt.timedelta(days=days)).isoformat()
    except ValueError:
        return 0
    origins = [r for r in con.execute("SELECT as_on, item, marg, pack, why, at FROM s454_shelf_gap WHERE flagged=1 AND approx=0 AND as_on>=? "
                                      "AND why LIKE 'Marg moved %' ORDER BY as_on, item", (lo,)).fetchall()
               if (" on %s" % r[0]) in str(r[4] or "")]
    if not origins:
        return 0
    sp = sp or _sw().Spine()
    if not sp.ok:
        return 0
    try:
        mins = float(_setting(con, "stock.gap_min_packs", "1"))
    except ValueError:
        mins = 1.0
    stamp = dt.datetime.now().replace(microsecond=0).strftime("%d-%m %H:%M")
    clear = []
    for d, item, marg, pack, why, at in origins:                   # pass 1: each origin, oldest closing first
        prev = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap WHERE as_on<?", (d,)).fetchone()[0]
        if not prev or marg is None:
            continue
        p = con.execute("SELECT marg FROM s454_shelf_gap WHERE as_on=? AND item=?", (prev, item)).fetchone()
        if not p or p[0] is None:
            continue
        sold, ret, bought = movements(sp, item, prev, d, incl_from=False)
        move = float(marg) - float(p[0]) - (bought - sold + ret)
        vch = filed_vouchers(con, item, prev, d)
        pk = int(pack or 1)
        thr = mins * (pk if pk > 1 else 1)
        if thr > 0 and abs(move - vch) < thr:
            clear.append((d, item, why, move, vch, "explained by a report that arrived later (first flagged %s; judged again %s)" % (_s494_ddmm_hm(at), stamp)))
    if not clear:
        return 0
    n = 0
    try:
        for d, item, why, move, vch, new_why in clear:
            n += con.execute("UPDATE s454_shelf_gap SET flagged=0, marg_move=?, voucher=?, why=? WHERE as_on=? AND item=? AND flagged=1 AND approx=0",
                             (move, vch, new_why, d, item)).rowcount or 0
        for d, item, why, move, vch, new_why in clear:                # pass 2: its copies, matched on the origin's why as it stood
            n += con.execute("UPDATE s454_shelf_gap SET flagged=0, why=? WHERE item=? AND as_on>? AND flagged=1 AND approx=0 AND why=?",
                             (new_why, item, d, why)).rowcount or 0
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return n


'''


def build_shelf_figure(src):
    return edit("shelf_figure.py", src, [
        ("def record_gaps(con, sp=None):\n", REJUDGE + "def record_gaps(con, sp=None):\n"),
        ("    con.execute(GAP_DDL)\n    as_on, snap = latest_snapshot(con)\n",
         "    con.execute(GAP_DDL)\n"
         "    try:                                                      # S494 (F-765): first judge again what later reports explain\n"
         "        rejudge(con, sp)\n"
         "    except Exception:                                         # noqa: BLE001 -- never stops the closing's own rows\n"
         "        pass\n"
         "    as_on, snap = latest_snapshot(con)\n"),
    ])


# ================================================================================================================== Part D
AMIR_BLOCK = r'''


# ==========================================================================================================================================
# S494_AMIR_JOBS_NOTICE_FLAGS (07-Oct-2026, D686) -- AMIR'S ONE-TIME MARG JOBS ON HIS OWN CARD, EACH GONE WHEN ITS WORK IS DONE.
#   * amir_job: one row per job the owner sets (kind category: an item's category in Marg; vendor_bill: a vendor's bill to scan for its
#     bank details; tap: an entry to make in Marg). A row is on his card from show_from until said (his tap) or done (proved / tapped).
#   * The system's own part (_s494_refresh, where _s444_self_clear runs): the category rows come onto his card with his rename list
#     (stage B / C / done), never before; Marg's newest category list read by the spine proves them -- or brings one back when it still
#     shows another category; a vendor's row is done once its bank details are on record or a scan is linked to one of its Marg bills.
#   * His card (_s446_card): 'Ek baar ke kaam' and the owner's approved words, after the count's lines, before the monthly packs. Each
#     button is its own small form posting job=<value> to the step being shown; the step's POST reads it FIRST and sends him back there.
#   * The owner (English): bank details to type, a bill not found, an item the category list does not carry, jobs left
#     amir.job_wait_days days. Advisory, like the rest of Marg sudhar: GATE_STEPS, _ready_to_close and the day's close are untouched.
# ==========================================================================================================================================
S494_KIT = "S494_AMIR_JOBS_NOTICE_FLAGS"
S494_DDL = ("CREATE TABLE IF NOT EXISTS amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, "
            "text_hi TEXT, sub_hi TEXT, created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, "
            "done_at TEXT, done_how TEXT)")
S494_KINDS = {"category": 0, "vendor_bill": 1, "tap": 2}
S494_CAT_TYPE = "CATEGORY_WISE_ITEM_LIST"
S494_JOBS = (
    ("cat:BRACE TYLOR UNISON", "category", "BRACE TYLOR UNISON", None, None),
    ("cat:SKIN TRACTION HOPE", "category", "SKIN TRACTION HOPE", None, None),
    ("cat:TENNIS ELBOW L HOPE", "category", "TENNIS ELBOW L HOPE", None, None),
    ("cat:TENNIS ELBOW M HOPE", "category", "TENNIS ELBOW M HOPE", None, None),
    ("vbill:AGARWAL SURGICALS AND MEDICALS", "vendor_bill", "AGARWAL SURGICALS AND MEDICALS", None, None),
    ("vbill:RAMA MEDICOSE", "vendor_bill", "RAMA MEDICOSE", None, None),
    ("vbill:KUSHAGRA MEDICAL AGENCY", "vendor_bill", "KUSHAGRA MEDICAL AGENCY", None, None),
    ("pay:KEDAR-JULY", "tap", "KEDAR PHARMACEUTICAL", "KEDAR PHARMACEUTICAL: ₹310 cash payment ki entry Marg mein kijiye.",
     "July 2026 ka purana balance band karne ke liye."),
)
S494_OPEN = "show_from IS NOT NULL AND done_at IS NULL AND said_at IS NULL"


def _s494_ensure(cx):
    cx.execute(S494_DDL)


def s494_seed_jobs(cx, by="S494"):
    """The installer's seed (S494 4.2): the eight rows, INSERT OR IGNORE by key -- an item name not in stock_item_section (Orthotics) or a
    vendor not in purchase_bill is not seeded and is named; then show_from = now on any unsaid, open vendor / tap row of `by` with none
    (a re-install after a restore brings them back). Returns dict(seeded, missing, shown)."""
    _s494_ensure(cx)
    now = _stamp()
    seeded, missing = 0, []
    for key, kind, subject, thi, shi in S494_JOBS:
        if kind == "category":
            found = cx.execute("SELECT 1 FROM stock_item_section WHERE item=? AND section='Orthotics'", (subject,)).fetchone()
        elif kind == "vendor_bill":
            found = cx.execute("SELECT 1 FROM purchase_bill WHERE supplier_norm=? LIMIT 1", (subject,)).fetchone()
        else:
            found = True
        if not found:
            missing.append(key)
            continue
        cur = cx.execute("INSERT OR IGNORE INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                         (key, kind, subject, thi, shi, now, by, (None if kind == "category" else now)))
        seeded += cur.rowcount or 0
    shown = cx.execute("UPDATE amir_job SET show_from=? WHERE created_by=? AND kind IN ('vendor_bill', 'tap') AND said_at IS NULL AND done_at IS NULL "
                       "AND show_from IS NULL", (now, by)).rowcount or 0
    cx.commit()
    return dict(seeded=seeded, missing=missing, shown=shown)


def _s494_spine():
    try:
        import stock_watch                                     # noqa: PLC0415 -- never spine_read.Spine: it raises when the spine is missing
        sp = stock_watch.Spine()
        return sp if sp.ok else None
    except Exception:                                          # noqa: BLE001
        return None


def _s494_cat(sp, item, md5=None):
    """Marg's category of an item by its exact name: in one list (its md5), else the newest by as_on. None when there is none."""
    if md5:
        r = sp.q("SELECT value FROM sp_item_fact WHERE fact='category' AND name=? AND source_md5=? LIMIT 1", item, md5)
    else:
        r = sp.q("SELECT value FROM sp_item_fact WHERE fact='category' AND name=? ORDER BY as_on DESC LIMIT 1", item)
    v = str(r[0]["value"] or "").strip() if r else ""
    return v or None


def _s494_label(cx, sp):
    """The orthotic label: the most common newest category among the Orthotics names (the category jobs' items left out); None with
    fewer than ten names carrying one. -> (label, how many names it rests on)."""
    skip = {r[0] for r in cx.execute("SELECT subject FROM amir_job WHERE kind='category'")}
    count, order = {}, []
    for (nm,) in cx.execute("SELECT item FROM stock_item_section WHERE section='Orthotics' ORDER BY item").fetchall():
        if nm in skip:
            continue
        v = _s494_cat(sp, nm)
        if v:
            if v not in count:
                order.append(v)
            count[v] = count.get(v, 0) + 1
    n = sum(count.values())
    if n < 10:
        return None, n
    best = max(order, key=lambda k: (count[k], -order.index(k)))
    return best, n


def _s494_lists(cx, sp):
    """(newest, newest_read): Marg's VERIFIED category lists by received_at (the stamps normalised) -- the newest of all, and the newest
    the spine has read (a category fact carries its md5). Each a dict(md5, at, day) or None. Judged by the md5, never by the list's day."""
    out = []
    for md5_, rec, dfrom, dto in cx.execute("SELECT md5, received_at, date_from, date_to FROM mi_file WHERE type=? AND verdict='VERIFIED'",
                                            (S494_CAT_TYPE,)).fetchall():
        at = _norm_ts(rec)
        if at:
            out.append(dict(md5=md5_, at=at, day=(str(dto or "")[:10] or str(dfrom or "")[:10] or at[:10])))
    out.sort(key=lambda x: x["at"], reverse=True)
    newest = out[0] if out else None
    read = None
    for x in out:
        if sp.q("SELECT 1 AS x FROM sp_item_fact WHERE fact='category' AND source_md5=? LIMIT 1", x["md5"]):
            read = x
            break
    return newest, read


def _s494_bank(cx, vendor):
    try:
        return cx.execute("SELECT 1 FROM purchase_vendor_contact WHERE vendor_norm=? AND COALESCE(acct_no,'') <> '' AND COALESCE(ifsc,'') <> ''",
                          (vendor,)).fetchone() is not None
    except Exception:                                          # noqa: BLE001
        return False


def _s494_scanned(cx, vendor):
    try:
        return cx.execute("SELECT 1 FROM purchase_scan_link l JOIN purchase_bill b ON b.id = l.bill_id WHERE b.supplier_norm = ? LIMIT 1",
                          (vendor,)).fetchone() is not None
    except Exception:                                          # noqa: BLE001
        return False


def _s494_refresh(cx):
    """The system's own part (S494 4.3), where _s444_self_clear runs: fail-soft, idempotent, writes only when a row changes."""
    try:
        _s494_ensure(cx)
        rows = cx.execute("SELECT id, kind, subject, show_from, said_at FROM amir_job WHERE done_at IS NULL").fetchall()
        if not rows:
            return 0
        now = _stamp()
        n = 0
        cats = [r for r in rows if r[1] == "category"]
        if cats:
            if any(r[3] is None for r in cats):                # shown together with his rename list -- never before the vouchers are proved
                try:
                    import stock_app                           # noqa: PLC0415
                    st = stock_app.amir_stage(cx)
                except Exception:                              # noqa: BLE001
                    st = None
                if st and st.get("stage") in ("B", "C", "done"):
                    n += cx.execute("UPDATE amir_job SET show_from=? WHERE kind='category' AND show_from IS NULL AND done_at IS NULL", (now,)).rowcount or 0
            sp = _s494_spine()
            label = _s494_label(cx, sp)[0] if sp else None
            if label:
                newest, read = _s494_lists(cx, sp)
                for jid, _k, item, _show, said in cats:
                    cat = _s494_cat(sp, item, read["md5"] if read else None)
                    if cat is not None and cat.upper() == label.upper():
                        n += cx.execute("UPDATE amir_job SET done_at=?, done_how='seen in Marg' WHERE id=? AND done_at IS NULL", (now, jid)).rowcount or 0
                        continue
                    if said and newest and read and newest["md5"] == read["md5"] and newest["at"] > (_norm_ts(said) or ""):
                        if cat is not None:                    # that list shows it under another category: back on his card
                            n += cx.execute("UPDATE amir_job SET said_at=NULL, said_by=NULL, said_what=NULL WHERE id=?", (jid,)).rowcount or 0
        for jid, kind, vendor, _show, _said in rows:
            if kind != "vendor_bill":
                continue
            how = "bank details on record" if _s494_bank(cx, vendor) else ("scan linked" if _s494_scanned(cx, vendor) else None)
            if how:
                n += cx.execute("UPDATE amir_job SET done_at=?, done_how=? WHERE id=? AND done_at IS NULL", (now, how, jid)).rowcount or 0
        if n:
            cx.commit()
        return n
    except Exception:                                          # noqa: BLE001
        try:
            cx.rollback()
        except Exception:                                      # noqa: BLE001
            pass
        return 0


def _s494_jobs(cx):
    """His open jobs -- shown, not done, not said -- by kind (category, vendor_bill, tap). [] on ANY error: _s446_state has no try."""
    try:
        _s494_ensure(cx)
        rows = [dict(id=int(r[0]), key=r[1], kind=r[2], subject=r[3], text_hi=r[4], sub_hi=r[5])
                for r in cx.execute("SELECT id, key, kind, subject, text_hi, sub_hi FROM amir_job WHERE " + S494_OPEN + " ORDER BY id").fetchall()
                if r[2] in S494_KINDS]
        rows.sort(key=lambda j: (S494_KINDS[j["kind"]], j["id"]))
        if any(j["kind"] == "category" for j in rows):
            sp = _s494_spine()
            label = _s494_label(cx, sp)[0] if sp else None
            for j in rows:
                if j["kind"] == "category":
                    j["label"] = label
        for j in rows:
            if j["kind"] == "vendor_bill":
                b = cx.execute("SELECT bill_no, bill_date FROM purchase_bill WHERE supplier_norm=? ORDER BY bill_date DESC, id DESC LIMIT 1",
                               (j["subject"],)).fetchone()
                j["bill"] = (b[0], b[1]) if b else None
        return rows
    except Exception:                                          # noqa: BLE001
        return []


def _s494_lines(jobs):
    """The card's lines (the owner's approved words, S494 4.4): under one small heading 'Ek baar ke kaam'. [] with no job."""
    if not jobs:
        return []
    out = ["<div class=line id=s494jobs><span class=sub><b>Ek baar ke kaam</b></span></div>"]
    cats = [j for j in jobs if j["kind"] == "category"]
    if cats:
        head = ("In %d item ki category Marg mein ORTHOTIC kijiye" % len(cats)) if len(cats) > 1 else "Is item ki category Marg mein ORTHOTIC kijiye"
        lab = cats[0].get("label")
        out.append("<div class=line><span class=big>%s</span><br><span class=sub>%s</span>%s"
                   "<form method=post><input type=hidden name=job value=cat><button class=btn>Kar diya</button></form></div>"
                   % (_esc(head), _esc(" · ".join(j["subject"] for j in cats)),
                      ("<br><span class=sub>%s</span>" % _esc("Marg mein is category ka naam: %s" % lab)) if (lab and lab.strip().upper() != "ORTHOTIC") else ""))
    vs = [j for j in jobs if j["kind"] == "vendor_bill"]
    if vs:
        head = (("In %d vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye" % len(vs)) if len(vs) > 1
                else "Is vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye")
        out.append("<div class=line><span class=big>%s</span><br><span class=sub>Bill nikaal kar reception (Alisha / Shivani) se scan karwaiye.</span></div>"
                   % _esc(head))
        for j in vs:
            b = j.get("bill")
            t = ("%s — bill %s (%s)" % (j["subject"], b[0], _ddmmyyyy(b[1]))) if b else j["subject"]
            out.append("<div class=line><span class=big>%s</span>"
                       "<form method=post><input type=hidden name=job value='scan:%d'><button class='btn plain'>Scan ho gaya</button></form>"
                       "<form method=post><input type=hidden name=job value='nf:%d'><button class='btn quiet'>Bill nahi mila</button></form></div>"
                       % (_esc(t), j["id"], j["id"]))
    for j in jobs:
        if j["kind"] != "tap":
            continue
        out.append("<div class=line><span class=big>%s</span>%s"
                   "<form method=post><input type=hidden name=job value='tap:%d'><button class=btn>Kar diya</button></form></div>"
                   % (_esc(j.get("text_hi") or j["subject"]), ("<br><span class=sub>%s</span>" % _esc(j["sub_hi"])) if j.get("sub_hi") else "", j["id"]))
    return out


def _s494_tap(cx, who, val):
    """A tap on his card (S494 4.5): 'cat' (every shown, open category row), 'scan:<id>' / 'nf:<id>' (a vendor_bill row), 'tap:<id>' (a
    tap row). A row not shown, not open, of another kind, or not a number changes nothing. One audit row per row changed."""
    try:
        val = str(val or "").strip()
        now = _stamp()
        if val == "cat":
            hit = [(r[0], r[1], "done") for r in cx.execute("SELECT id, key FROM amir_job WHERE kind='category' AND " + S494_OPEN).fetchall()]
        else:
            m = re.match(r"^(scan|nf|tap):(\d{1,9})$", val)
            if not m:
                return 0
            kind = "tap" if m.group(1) == "tap" else "vendor_bill"
            r = cx.execute("SELECT id, key FROM amir_job WHERE id=? AND kind=? AND " + S494_OPEN, (int(m.group(2)), kind)).fetchone()
            hit = [(r[0], r[1], "not_found" if m.group(1) == "nf" else "done")] if r else []
        for jid, key, what in hit:
            if val.startswith("tap:"):
                cx.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what=?, done_at=?, done_how='tap' WHERE id=?", (now, who, what, now, jid))
            else:
                cx.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what=? WHERE id=?", (now, who, what, jid))
            _s444_audit(cx, who, "job", key, {"tapped": val, "said": what, "kit": S494_KIT})
        if hit:
            cx.commit()
        return len(hit)
    except Exception:                                          # noqa: BLE001
        try:
            cx.rollback()
        except Exception:                                      # noqa: BLE001
            pass
        return 0


def _s494_owner_lines(con):
    """The owner's lines (S494 4.6) -- English, target checks-marg, each gone by itself. [] on any error."""
    out = []
    try:
        if not _table_exists(con, "amir_job"):
            return out
        for _jid, vendor, said_what, done_how in con.execute("SELECT id, subject, said_what, done_how FROM amir_job WHERE kind='vendor_bill' ORDER BY id").fetchall():
            if _s494_bank(con, vendor):
                continue
            if done_how == "scan linked":
                out.append(dict(cls="warn", target="checks-marg", text="Bank details to type for %s -- its bill is scanned" % vendor))
            elif done_how is None and said_what == "done":
                out.append(dict(cls="warn", target="checks-marg", text="Bank details to type for %s -- Amir says its bill is scanned" % vendor))
            elif done_how is None and said_what == "not_found":
                out.append(dict(cls="warn", target="checks-marg", text="Amir could not find a bill of %s -- its bank details are still needed" % vendor))
        said = con.execute("SELECT subject, said_at FROM amir_job WHERE kind='category' AND said_what='done' AND said_at IS NOT NULL AND done_at IS NULL "
                           "ORDER BY id").fetchall()
        if said:
            sp = _s494_spine()
            if sp and _s494_label(con, sp)[0]:
                newest, read = _s494_lists(con, sp)
                if newest and read and newest["md5"] == read["md5"]:
                    for item, at in said:
                        if newest["at"] > (_norm_ts(at) or "") and _s494_cat(sp, item, newest["md5"]) is None:
                            out.append(dict(cls="info", target="checks-marg",
                                            text="%s is not on Marg's category list of %s -- its category could not be proved" % (item, _s444_ddmm(newest["day"]))))
        wait = _s444_setting(con, "amir.job_wait_days")
        old = []
        for subject, show in con.execute("SELECT subject, show_from FROM amir_job WHERE " + S494_OPEN + " ORDER BY show_from, id").fetchall():
            dd = _s444_days_since(show)
            if dd is not None and dd >= wait:
                old.append((subject, show, dd))
        if old:
            out.append(dict(cls="warn", target="checks-marg", text="Amir's one-time Marg jobs not done: %d -- since %s (%d days): %s"
                            % (len(old), _s444_ddmm(old[0][1]), old[0][2], ", ".join(x[0] for x in old[:3]))))
    except Exception:                                          # noqa: BLE001
        return out
    return out
# ---- S494_AMIR_JOBS_NOTICE_FLAGS end -----------------------------------------------------------------------------------------------------
'''


def build_amir_day(src):
    return edit("amir_day.py", src, [
        ('"amir.proof_wait_hours": 48, "amir.refused_keep_hours": 36}                     # S488\n',
         '"amir.proof_wait_hours": 48, "amir.refused_keep_hours": 36,                      # S488\n'
         '                 "amir.job_wait_days": 10}                                                         # S494 (D686)\n'),
        ('"amir.refused_keep_hours": "S488: hours a refused report stays on the owner\'s Needs-you list (kept past midnight)"}\n',
         '"amir.refused_keep_hours": "S488: hours a refused report stays on the owner\'s Needs-you list (kept past midnight)",\n'
         '              "amir.job_wait_days": "Amir\'s one-time Marg jobs: days before your Needs-you list names them"}     # S494 (D686)\n'),
        ("    _s444_self_clear(cx)                                 # S444: his own corrections clear themselves once Marg shows the paper's amount\n",
         "    _s444_self_clear(cx)                                 # S444: his own corrections clear themselves once Marg shows the paper's amount\n"
         "    _s494_refresh(cx)                                    # S494 (D686): his one-time Marg jobs -- shown, proved, reopened by the system\n"),
        ('    if request.method == "POST":\n        if n == 5:\n            _save_bills(cx, day, user, request.form)\n',
         '    if request.method == "POST":\n'
         '        if request.form.get("job"):                     # S494 (D686): a one-time job tapped on his card -- FIRST, for every step\n'
         '            _s494_tap(cx, user, request.form.get("job"))\n'
         '            return _go(n)\n'
         '        if n == 5:\n            _save_bills(cx, day, user, request.form)\n'),
        ("        _s444_self_clear(con)\n        # (a) the salt list owed\n",
         "        _s444_self_clear(con)\n        _s494_refresh(con)                                     # S494 (D686)\n        # (a) the salt list owed\n"),
        ("        out.extend(_s446_owner_lines(con))\n",
         "        out.extend(_s446_owner_lines(con))\n        out.extend(_s494_owner_lines(con))                     # S494 (D686): Amir's one-time Marg jobs\n"),
        ("    return dict(stage=st, packs=_s446_packs(cx), watch=_s446_watch(cx),\n",
         "    return dict(stage=st, packs=_s446_packs(cx), watch=_s446_watch(cx), jobs=_s494_jobs(cx),     # S494: [] on any error\n"),
        ('    for m in s.get("packs") or []:\n        lines.append("<div class=line><span class=big>Mahine ka pack',
         '    lines.extend(_s494_lines(s.get("jobs") or []))        # S494 (D686): his one-time Marg jobs -- after the count, before the packs\n'
         '    for m in s.get("packs") or []:\n        lines.append("<div class=line><span class=big>Mahine ka pack'),
        ('        out.append("SALT WISE ITEM LIST not received (Excel)")\n    return out\n\n\ndef _s446_summary_rows(w):\n',
         '        out.append("SALT WISE ITEM LIST not received (Excel)")\n'
         '    if s.get("jobs"):                                         # S494 (D686): the owner\'s English\n'
         '        out.append("one-time Marg jobs: %d open" % len(s["jobs"]))\n'
         '    return out\n\n\ndef _s446_summary_rows(w):\n'),
        ("# ---- S488_DATES_AND_WAITS end ---------------------------------------------------------------------------------------------------------\n",
         "# ---- S488_DATES_AND_WAITS end ---------------------------------------------------------------------------------------------------------\n"
         + AMIR_BLOCK),
    ])


BUILD = {"order_sheet.py": build_order_sheet, "stock_watch.py": build_stock_watch, "shelf_figure.py": build_shelf_figure,
         "amir_day.py": build_amir_day}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for name in sorted(FROM):
        raw = rd(os.path.join(a.finance, name))
        if md5(raw) != FROM[name]:
            raise SystemExit("!! %s is %s, not its FROM pin %s -- nothing built" % (name, md5(raw), FROM[name]))
        new = BUILD[name](raw.decode("utf-8")).encode("utf-8")
        compile(new, name, "exec")
        built[name] = new
    os.makedirs(a.out, exist_ok=True)
    for name, b in sorted(built.items()):
        with io.open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s -> %s  (%+d lines)" % (name, FROM[name][:8], md5(b), b.count(b"\n") - rd(os.path.join(a.finance, name)).count(b"\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

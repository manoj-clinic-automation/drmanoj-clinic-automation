#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s488.py -- kit S488_DATES_AND_WAITS (F-753, F-754).

Nine files of /root/finance are BUILT FROM THE LIVE BYTES by anchored edits: each anchor must occur exactly once in what the edits
before it left, else the build stops and nothing is written. Nothing here opens a database or the network.

    python3 -B make_s488.py --finance /root/finance --out DIR      -> DIR/<the nine files>

  stock_app.py      A.1-A.6 (dates as dates: api_drift, _r_stock, readiness against the purchase exports' reach, api_now, api_losses);
                    B.1 (_s446_proof, state export: since / why / closing_day / closing_at); B.2b (_s436_board_extra's last line)
  darpan_app.py     A.7 (the pipeline's stock leg: the newest snapshot by date)
  owner_sheets.py   A.8 (the parent's file -- consumable_items' fallback: the newest snapshot by date; this one statement only)
  stock_watch.py    A.9 (item_info: the snapshot row by date -- one line, as it was)
  shelf_figure.py   A.10 (filed_vouchers: the newest entry of each batch, its day as a date -- F-754)
  amir_day.py       B.2 (Amir's card), B.2b (his day's two lines), B.3 (the owner's lines, the 48-hour warn), B.4 (a refusal kept past midnight)
  item_check.py     D.1 (a learnt name can be struck and put back; a struck pair is never learnt again)
  purchase_app.py   D.2 (the Items check block only: Wrong / Put back, POST api/items/strike, the doctor only)
  reports_tile.py   C.1 (the owner's three lists: each limit from its setting row, the read guarded)
"""
import argparse
import hashlib
import io
import os
import sys

KIT = "S488_DATES_AND_WAITS"
FROM = {
    "stock_app.py": "7e159de737c0ec03cea890053f1bcd58",
    "darpan_app.py": "5bfabbecf1e0fbf86ff142e3cd07543e",
    "owner_sheets.py": "8b1aea31fc1d7dd231fbb45f87c2c6d2",
    "stock_watch.py": "6d4d660f20a0e441fb1082597e5fd96c",
    "shelf_figure.py": "23c34ebb1149996e1053c26573077460",
    "amir_day.py": "709f20c1078cbcb36fc1108e452c40c1",
    "item_check.py": "9000e3768086e0935d88bec8c8b1cd07",
    "purchase_app.py": "254b77939ca40d20e46509a678bcb5d8",
    "reports_tile.py": "ea15aacbb6a00131d3f02664b0c1df42",
}
KEY = "substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2)"          # Marg's dd-mm-yyyy as a sortable yyyymmdd (rule 0.1)


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


# ------------------------------------------------------------------------------------------------------------------------ stock_app.py
STOCK_BLOCK = '''

# ==========================================================================================================================================
# S488_DATES_AND_WAITS (06-Oct-2026, F-753) -- dates compared as dates; a waiting proof says since when and for what.
#   * Marg's dd-mm-yyyy is compared through a key wherever a day is sorted, maxed or bounded here (api_drift, _r_stock, readiness,
#     api_now, api_losses). readiness's "stock ahead of purchases" warning follows the purchase exports' reach (MAX period_to of the
#     exports in force), not the last bill's date: a Sunday with no bill is not a day the purchases are behind. On a day no purchase
#     export comes, the warning stands -- true by the rule (a day with no purchase looks like a day not exported).
#   * _s446_proof, state "export" only, adds keys and nothing else: since (the last voucher's stamp), why (no_closing | no_figure |
#     pur_behind | no_before | rebased), closing_day (as stored) and closing_at (the EARLIEST Marg push of that day after the vouchers,
#     never the nightly re-push). The verdict, the pairing rule and the cache key do not change.
#   * _s436_board_extra's last proof line says the same reason in Roman Hindi; with no reason to be had, today's words.
# ==========================================================================================================================================
S488_KIT = "S488_DATES_AND_WAITS"
S488_TAIL_HI = {"no_figure": "closing stock aa gaya \\u2014 server ka hisaab banna baaki (bikri report ke baad)",
                "pur_behind": "closing stock aa gaya \\u2014 purchase report nikalni baaki",
                "no_before": "closing stock aa gaya \\u2014 jaanch system ki taraf se ruki hai",
                "rebased": "closing stock aa gaya \\u2014 jaanch system ki taraf se ruki hai"}


def _s488_purchase_reach(con):
    """The day the purchase exports in force reach (ISO), or '' when none is known."""
    try:
        r = con.execute("SELECT MAX(substr(period_to,1,10)) FROM purchase_export WHERE superseded_by IS NULL").fetchone()
        return str((r[0] if r else "") or "")
    except Exception:                                          # noqa: BLE001
        return ""


def _s488_first_push(con, day, last_at, fallback=None):
    """The EARLIEST received_at after last_at among the day's Marg closing-stock pushes (stock_feed rows whose source is marg)."""
    best = None
    for src, at in con.execute("SELECT source, MIN(received_at) FROM stock_feed WHERE as_on=? AND substr(received_at,1,19) > ? GROUP BY source",
                               (day, str(last_at or "")[:19])):
        if _feed_kind(src) == "marg" and at and (best is None or str(at) < best):
            best = str(at)
    return best or fallback


def _s488_why(con, feeds, before, after, last_at):
    """{since, why, closing_day, closing_at} for a proof in state export -- the reason, never the decision. {} when it cannot be had."""
    try:
        out = dict(since=last_at)
        lk = str(last_at)[:10].replace("-", "")
        day = None
        if after and not before:
            why, day = "no_before", after[0]
        elif after and before:
            why, day = "rebased", after[0]
        else:
            M = [x for x in sorted({k[0] for k in feeds}, key=_proof_day_key) if (x, "marg") in feeds
                 and _proof_day_key(x) >= lk and feeds[(x, "marg")]["received_at"][:19] > last_at]
            if not M:
                why = "no_closing"
            else:
                day = M[0]
                if (day, "expected") not in feeds:
                    why = "no_figure"
                elif _proof_pur_to(feeds[(day, "expected")]["source"]) < _proof_day_key(day):
                    # our figure of that day lacks its purchases: the purchase export is owed -- unless the exports already reach the day,
                    # when our figure is merely not recomputed yet (02-10 read pur_to=01-10 for 22 hours after exports to 04-10 had come)
                    why = "pur_behind" if _s488_purchase_reach(con).replace("-", "") < _proof_day_key(day) else "no_figure"
                else:
                    why = "no_before" if not before else "no_figure"
        out["why"] = why
        if why != "no_closing":
            out["closing_day"] = day
            out["closing_at"] = _s488_first_push(con, day, last_at, feeds.get((day, "marg"), {}).get("received_at"))
        return out
    except Exception:                                          # noqa: BLE001 -- the reason is a help: without it the card says today's words
        return {}


def _s488_stage_proof(st):
    """The proof whose reason Amir is told: stage A's, or stage C's first lot waiting for an export. None otherwise."""
    st = st or {}
    if st.get("stage") == "A":
        return (st.get("A") or {}).get("proof")
    if st.get("stage") == "C":
        wl = (st.get("C") or {}).get("waiting_export") or []
        return (wl[0] or {}).get("proof") if wl else None
    return None


def _s488_tail_hi(pr):
    """The Roman Hindi tail for a closing that has arrived ('' for no_closing, no reason, or any other state)."""
    pr = pr or {}
    return S488_TAIL_HI.get(pr.get("why"), "") if pr.get("state") == "export" else ""
# ---- S488_DATES_AND_WAITS end ---------------------------------------------------------------------------------------------------------
'''


def build_stock_app(src):
    return edit("stock_app.py", src, [
        # A.1 api_drift: the per-item series in date order across a month end
        ("    for (as_on, item) in sorted(byday):\n",
         "    for (as_on, item) in sorted(byday, key=lambda k: (_proof_day_key(k[0]), k[1])):   # S488 (F-753): a day sorts as a date\n"),
        # A.2 api_drift's feeds list: newest day first, by date
        ('"FROM stock_feed GROUP BY as_on, source ORDER BY as_on DESC, source"',
         '"FROM stock_feed GROUP BY as_on, source ORDER BY %s DESC, source"' % KEY),
        # A.3 _r_stock: the newest day of each feed, by date
        ('            if cur is None or (as_on, v["received_at"]) > (cur["as_on"],\n'
         '                                                           cur["processed_at"]):\n',
         '            if cur is None or (_proof_day_key(as_on), v["received_at"]) > (_proof_day_key(cur["as_on"]),   # S488 (F-753)\n'
         '                                                                           cur["processed_at"]):\n'),
        # A.4 readiness: the stock day against the purchase exports' reach, both as dates
        ('    if stk.get("marg") and pur.get("bill_date") and \\\n'
         '            stk["marg"]["as_on"] > pur["bill_date"]:\n'
         '        warn.append("The stock figure is for %s but purchases are known only to "\n'
         '                    "%s. Count after the purchase export, not before it."\n'
         '                    % (_r_dmy(stk["marg"]["as_on"]), _r_dmy(pur["bill_date"])))\n',
         '    reach = _s488_purchase_reach(con) or str(pur.get("bill_date") or "")[:10]   # S488 (F-753): the exports\' reach, as a date\n'
         '    if stk.get("marg") and reach and \\\n'
         '            _dmy_to_iso(stk["marg"]["as_on"])[:10] > reach:\n'
         '        warn.append("The stock figure is for %s but purchases are known only to "\n'
         '                    "%s. Count after the purchase export, not before it."\n'
         '                    % (_r_dmy(stk["marg"]["as_on"]), _r_dmy(reach)))\n'),
        # A.5 api_now: the newest day by date (Stock now read 30-09-2026 all October)
        ("    days = sorted({d for (d, k) in latest})\n",
         "    days = sorted({d for (d, k) in latest}, key=_proof_day_key)          # S488 (F-753): the newest day by date, not by text\n"),
        # A.6 api_losses: found_on (dd-mm-yyyy) between two ISO days -- four statements, each anchored on its own SELECT line
        ('"SELECT cause, COUNT(*) n, SUM(-diff) units, SUM(COALESCE(-value_p,0)) value_p "\n'
         '        "FROM stock_diff WHERE diff<0 AND found_on BETWEEN ? AND ? "\n',
         '"SELECT cause, COUNT(*) n, SUM(-diff) units, SUM(COALESCE(-value_p,0)) value_p "\n'
         '        "FROM stock_diff WHERE diff<0 AND substr(found_on,7,4)||\'-\'||substr(found_on,4,2)||\'-\'||substr(found_on,1,2) BETWEEN ? AND ? "\n'),
        ('"SELECT item, COUNT(*) times, SUM(-diff) units, SUM(COALESCE(-value_p,0)) value_p "\n'
         '        "FROM stock_diff WHERE diff<0 AND found_on BETWEEN ? AND ? "\n',
         '"SELECT item, COUNT(*) times, SUM(-diff) units, SUM(COALESCE(-value_p,0)) value_p "\n'
         '        "FROM stock_diff WHERE diff<0 AND substr(found_on,7,4)||\'-\'||substr(found_on,4,2)||\'-\'||substr(found_on,1,2) BETWEEN ? AND ? "\n'),
        ('"WHERE diff>0 AND found_on BETWEEN ? AND ?"',
         '"WHERE diff>0 AND substr(found_on,7,4)||\'-\'||substr(found_on,4,2)||\'-\'||substr(found_on,1,2) BETWEEN ? AND ?"'),
        ('"SELECT item, COUNT(*) times FROM stock_diff WHERE found_on BETWEEN ? AND ? "',
         '"SELECT item, COUNT(*) times FROM stock_diff WHERE substr(found_on,7,4)||\'-\'||substr(found_on,4,2)||\'-\'||substr(found_on,1,2) BETWEEN ? AND ? "'),
        # B.1 _s446_proof: the reason, never the decision
        ("    _S446_PROOF_CACHE[ck] = (now, res)\n    return res\n",
         "    if res.get(\"state\") == \"export\":                           # S488 (B.1): since when and for what -- keys added, nothing else\n"
         "        res.update(_s488_why(con, feeds, before, after, last_at))\n"
         "    _S446_PROOF_CACHE[ck] = (now, res)\n    return res\n"),
        # B.2b Amir's board: the proof line's last branch says the same reason
        ('            out["proof_hi"] = "Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye"\n',
         '            out["proof_hi"] = "Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye"\n'
         '            try:                                               # S488 (B.2b): the closing has come -- say what is awaited instead\n'
         '                _t488 = _s488_tail_hi(_s488_stage_proof(amir_stage(con, d["count_id"])))\n'
         '            except Exception:                                  # noqa: BLE001\n'
         '                _t488 = ""\n'
         '            if _t488:\n'
         '                out["proof_hi"] = "Abhi baaki — " + _t488\n'),
        # the block, at the end of the file
        ("# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------\n",
         "# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------\n"
         + STOCK_BLOCK),
    ])


# ----------------------------------------------------------------------------------------------------------------------- darpan_app.py
def build_darpan_app(src):
    return edit("darpan_app.py", src, [
        ('        r = con.execute("SELECT MAX(as_on) d, COUNT(DISTINCT as_on) n FROM "\n'
         '                        "stock_snapshot").fetchone()\n',
         '        r = con.execute("SELECT (SELECT as_on FROM stock_snapshot GROUP BY as_on ORDER BY "        # S488 (F-753): the newest by date\n'
         '                        "%s DESC LIMIT 1) d, "\n'
         '                        "COUNT(DISTINCT as_on) n FROM stock_snapshot").fetchone()\n' % KEY),
    ])


# ---------------------------------------------------------------------------------------------------------------------- owner_sheets.py
def build_owner_sheets(src):
    return edit("owner_sheets.py", src, [
        ('            as_on = con.execute("SELECT MAX(as_on) AS a FROM stock_snapshot").fetchone()["a"]\n',
         '            as_on = con.execute("SELECT (SELECT as_on FROM stock_snapshot GROUP BY as_on ORDER BY "      # S488: the newest by date\n'
         '                                "%s DESC LIMIT 1) AS a").fetchone()["a"]\n' % KEY),
    ])


# ----------------------------------------------------------------------------------------------------------------------- stock_watch.py
def build_stock_watch(src):
    return edit("stock_watch.py", src, [
        ('        r = con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE item=? ORDER BY as_on DESC LIMIT 1", (name,)).fetchone()\n',
         '        r = con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE item=? ORDER BY %s DESC LIMIT 1", (name,)).fetchone()\n'
         % KEY),
    ])


# ---------------------------------------------------------------------------------------------------------------------- shelf_figure.py
OLD_FILED = '''def filed_vouchers(con, item, d_from, d_to):
    """Units of the count's vouchers for this item that Amir filed in Marg between two closings (stock_voucher_line by round and batch,
    stock_voucher_entered.entered_on) -- the change Marg is EXPECTED to show without a sale or a purchase."""
    if not (_has(con, "stock_voucher_line") and _has(con, "stock_voucher_entered")):
        return 0.0
    try:
        r = con.execute("SELECT COALESCE(SUM(l.change),0) FROM stock_voucher_line l JOIN stock_voucher_entered e ON e.count_id=l.count_id AND e.round_no=l.round_no "
                        "AND e.kind=l.kind AND e.batch_no=l.batch_no WHERE l.item=? AND e.entered_on>? AND e.entered_on<=?", (item, d_from, d_to)).fetchone()
        return float(r[0] or 0)
    except sqlite3.Error:
        return 0.0
'''
NEW_FILED = '''def _s488_entry_day(entered_on, at):
    """S488 (F-754): the ISO day a voucher batch was filed -- entered_on when it reads as dd-mm-yyyy, dd/mm/yyyy or ISO, else the day of
    `at` (the entry's own stamp). None when neither is a date."""
    s = str(entered_on or "").strip()
    m = re.match(r"^(\\d\\d)[-/](\\d\\d)[-/](\\d{4})$", s)
    for cand in (("%s-%s-%s" % (m.group(3), m.group(2), m.group(1))) if m else s[:10] if re.match(r"^\\d{4}-\\d\\d-\\d\\d", s) else "",
                 str(at or "")[:10]):
        try:
            return dt.date.fromisoformat(cand).isoformat()
        except ValueError:
            continue
    return None


def filed_vouchers(con, item, d_from, d_to):
    """Units of the count's vouchers for this item that Amir filed in Marg between two closings (stock_voucher_line by round and batch,
    stock_voucher_entered) -- the change Marg is EXPECTED to show without a sale or a purchase.
    S488 (F-754): stock_voucher_entered is an append-only log -- the newest row (highest id) of each (count, round, kind, batch) is the
    batch's state, and a batch counts only while that row carries a voucher number (the rule _proof_state keeps). Its day is entered_on
    read as a date (dd-mm-yyyy, dd/mm/yyyy or ISO), else the day of `at`; it counts when d_from < day <= d_to (ISO days). Before S488 the
    dd-mm-yyyy text was compared with ISO days and no filed voucher was ever counted."""
    if not (_has(con, "stock_voucher_line") and _has(con, "stock_voucher_entered")):
        return 0.0
    lo, hi = str(d_from or "")[:10], str(d_to or "")[:10]
    if not hi:
        return 0.0
    try:
        state = {}
        for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                             "FROM stock_voucher_entered ORDER BY id"):
            state[(cid, rno, kind, bno)] = (vno, eon, at)
        filed = set()
        for k, (vno, eon, at) in state.items():
            day = _s488_entry_day(eon, at) if str(vno or "").strip() else None
            if day and lo < day <= hi:
                filed.add(k)
        if not filed:
            return 0.0
        tot = 0.0
        for cid, rno, kind, bno, ch in con.execute("SELECT count_id, round_no, kind, batch_no, change FROM stock_voucher_line WHERE item=?", (item,)):
            if (cid, rno, kind, bno) in filed:
                tot += float(ch or 0)
        return tot
    except sqlite3.Error:
        return 0.0
'''


def build_shelf_figure(src):
    return edit("shelf_figure.py", src, [(OLD_FILED, NEW_FILED)])


# -------------------------------------------------------------------------------------------------------------------------- amir_day.py
OLD_REFUSED = '''def _s444_refused_lines(cx):
    """A report refused TODAY, named the same day (the door's own refusals; the medical PC's refused texts stay on the PC
    and in Drive, which this server does not read)."""
    out = []
    if not _table_exists(cx, "mi_file"):
        return out
    seen = set()
    for typ, verdict, reason, pcv, at in cx.execute(
            "SELECT type, verdict, reason, pc_verdict, received_at FROM mi_file WHERE substr(received_at,1,10)=? "
            "AND (verdict <> 'VERIFIED' OR COALESCE(pc_verdict,'') = 'REFUSED') ORDER BY received_at", (_today(),)).fetchall():
        k = (typ or "?", _hhmm(at))
        if k in seen:
            continue
        seen.add(k)
        why = (reason or "").strip() or (("the medical PC refused it (%s)" % pcv) if pcv else (verdict or ""))
        out.append(dict(cls="warn", target="checks-marg",
                        text="Report refused today: %s at %s -- %s (Shavez / Amir to export it again)" % (typ or "unknown file", _hhmm(at), why[:120])))
    return out
'''
NEW_REFUSED = '''def _s444_refused_lines(cx):
    """A report refused in the last amir.refused_keep_hours hours (S488, B.4: a 23:30 refusal is no longer gone at midnight) -- one line
    per known type, its newest refusal, dropped once a VERIFIED file of that type arrives later; every unrecognised file (type NULL, ''
    or _UNKNOWN) together in ONE line. (The door's own refusals; the medical PC's refused texts stay on the PC and in Drive, which this
    server does not read.)"""
    out = []
    if not _table_exists(cx, "mi_file"):
        return out
    cut = (_now() - timedelta(hours=_s444_setting(cx, "amir.refused_keep_hours"))).strftime("%Y-%m-%d %H:%M:%S")
    known, unknown = {}, []
    for typ, verdict, reason, pcv, at in cx.execute(
            "SELECT type, verdict, reason, pc_verdict, received_at FROM mi_file WHERE substr(received_at,1,10) >= ? "
            "AND (verdict <> 'VERIFIED' OR COALESCE(pc_verdict,'') = 'REFUSED')", (cut[:10],)).fetchall():
        t = _norm_ts(at)
        if not t or t < cut:
            continue
        if typ in (None, "", "_UNKNOWN"):
            unknown.append(t)
        elif typ not in known or t >= known[typ][0]:
            known[typ] = (t, verdict, reason, pcv)
    today = _today()
    for typ in sorted(known, key=lambda k: known[k][0]):
        t, verdict, reason, pcv = known[typ]
        if any((_norm_ts(r[0]) or "") > t for r in cx.execute("SELECT received_at FROM mi_file WHERE type=? AND verdict='VERIFIED'", (typ,)).fetchall()):
            continue                                                   # exported again and verified: gone by itself
        why = (reason or "").strip() or (("the medical PC refused it (%s)" % pcv) if pcv else (verdict or ""))
        out.append(dict(cls="warn", target="checks-marg",
                        text="Report refused %s %s: %s -- %s (Shavez / Amir to export it again)"
                             % ("today" if t[:10] == today else _s444_ddmm(t), t[11:16], typ, why[:120])))
    if unknown:
        out.append(dict(cls="warn", target="checks-marg",
                        text="%d unrecognised file(s) refused since %s (newest %s)" % (len(unknown), _dm_hm(min(unknown)), max(unknown)[11:16])))
    return out
'''

AMIR_BLOCK = '''

# ==========================================================================================================================================
# S488_DATES_AND_WAITS (06-Oct-2026) -- a waiting card says since when and for what, and who acts (the owner's rule, audit 1 c).
#   * stock_app._s446_proof (state export) now carries why / since / closing_day / closing_at. Amir is never told to export something
#     that has already arrived, and never a reason that may be untrue: no_closing -> export (as before, with the vouchers' time);
#     no_figure -> the closing came, the server's own figure is made after the sale report, nothing for him; pur_behind -> the purchase
#     report to that day; no_before / rebased -> held on the system's side, nothing for him. No reason to be had -> today's words.
#   * The owner (English): the same reason as an ending; one warn line once a proof has waited amir.proof_wait_hours (48).
#   * _s444_refused_lines keeps a refusal amir.refused_keep_hours (36) -- past midnight -- and puts every unrecognised file in one line.
# ==========================================================================================================================================
S488_KIT = "S488_DATES_AND_WAITS"
S488_WHYS = ("no_closing", "no_figure", "pur_behind", "no_before", "rebased")
S488_TAIL_HI = {"no_figure": "closing stock aa gaya \\u2014 server ka hisaab banna baaki (bikri report ke baad)",
                "pur_behind": "closing stock aa gaya \\u2014 purchase report nikalni baaki",
                "no_before": "closing stock aa gaya \\u2014 jaanch system ki taraf se ruki hai",
                "rebased": "closing stock aa gaya \\u2014 jaanch system ki taraf se ruki hai"}


def _s488_proof(st):
    """The proof whose reason is told: stage A's, or stage C's first (oldest) lot waiting for an export. None otherwise."""
    st = st or {}
    if st.get("stage") == "A":
        return (st.get("A") or {}).get("proof")
    if st.get("stage") == "C":
        wl = (st.get("C") or {}).get("waiting_export") or []
        return (wl[0] or {}).get("proof") if wl else None
    return None


def _s488_why(pr):
    pr = pr or {}
    return pr.get("why") if (pr.get("state") == "export" and pr.get("why") in S488_WHYS) else None


def _s488_tail_hi(pr):
    """Roman Hindi, after 'Ginti #N: ' / 'Abhi baaki \\u2014 ': '' for no_closing or no reason (the caller keeps today's words)."""
    return S488_TAIL_HI.get(_s488_why(pr) or "", "")


def _s488_wait_html(pr):
    """What follows "... voucher Marg mein daal diye" on Amir's card, by the proof's reason. '' -> the caller keeps today's lines."""
    why = _s488_why(pr)
    if not why:
        return ""
    if why == "no_closing":
        return ("<span class='big bad'>Ab closing stock export kijiye</span><br>"
                "<span class=sub>Voucher %s par daale gaye. Uske baad ka closing stock abhi nahi aaya.</span>" % _esc(_dm_hm(pr.get("since"))))
    got = "<span class='big good'>Closing stock aa gaya &#10003; (%s)</span><br>" % _esc(_dm_hm(pr.get("closing_at")))
    day = _esc(str(pr.get("closing_day") or "")[:5])
    if why == "no_figure":
        return got + ("<span class=sub>Server ka %s ka apna hisaab abhi nahi bana &mdash; yeh bikri report ke baad banta hai. "
                      "Aapko abhi kuch nahi karna.</span>" % day)
    if why == "pur_behind":
        return got + ("<span class='big bad'>Ab purchase report nikaliye &mdash; %s tak ki</span><br>"
                      "<span class=sub>Purchase report aate hi server khud mila lega.</span>" % day)
    return got + "<span class=sub>Jaanch system ki taraf se ruki hai &mdash; Doctor sahab ko dikh raha hai. Aapko kuch nahi karna.</span>"


def _s488_ending(pr):
    """The owner's English ending for a waiting proof; '' when no reason can be had (the caller keeps today's words)."""
    why = _s488_why(pr)
    if not why:
        return ""
    if why == "no_closing":
        return "waiting for a closing-stock export since %s (Amir / Shavez)" % _dm_hm(pr.get("since"))
    head = "Marg's closing of %s arrived %s; " % (str(pr.get("closing_day") or "")[:5], _dm_hm(pr.get("closing_at")))
    if why == "no_figure":
        return head + ("waiting for our own figure for that day (made when its sale report lands \\u2014 Shavez; on a no-sale day, "
                       "the empty report)")
    if why == "pur_behind":
        return head + "waiting for a purchase export that reaches that day (Amir)"
    return head + "held on the system's side (no comparable export before the vouchers / figures re-based) \\u2014 for the chat"


def _s488_wait_line(cx, st):
    """The owner's warn line once the proof -- stage A's, or stage C's oldest waiting lot -- has waited amir.proof_wait_hours or more."""
    pr = _s488_proof(st)
    e = _s488_ending(pr)
    m = _mins_since((pr or {}).get("since")) if e else None
    if m is None:
        return None
    h = m // 60
    if h < _s444_setting(cx, "amir.proof_wait_hours"):
        return None
    return dict(cls="warn", target="stock", text="Count #%d: the voucher proof has waited %d hours \\u2014 %s" % (int(st["count_id"]), h, e))
# ---- S488_DATES_AND_WAITS end ---------------------------------------------------------------------------------------------------------
'''


def build_amir_day(src):
    return edit("amir_day.py", src, [
        # the two new settings (B.3, B.4) -- s444_seed_settings has no caller; the installer seeds the rows itself
        ('S444_DEFAULTS = {"amir.salt_owed_days": 2, "amir.self_exports": 2, "amir.claim_open_days": 7, "amir.voucher_visits": 2}\n',
         'S444_DEFAULTS = {"amir.salt_owed_days": 2, "amir.self_exports": 2, "amir.claim_open_days": 7, "amir.voucher_visits": 2,\n'
         '                 "amir.proof_wait_hours": 48, "amir.refused_keep_hours": 36}                     # S488\n'),
        ('              "amir.voucher_visits": "S444: Amir\'s visits without opening the count vouchers before the owner\'s line"}\n',
         '              "amir.voucher_visits": "S444: Amir\'s visits without opening the count vouchers before the owner\'s line",\n'
         '              "amir.proof_wait_hours": "S488: hours a count\'s voucher proof may wait before the owner\'s warn line",\n'
         '              "amir.refused_keep_hours": "S488: hours a refused report stays on the owner\'s Needs-you list (kept past midnight)"}\n'),
        # B.4
        (OLD_REFUSED, NEW_REFUSED),
        # B.2 the card: stage A's last branch
        ('            else:\n'
         '                lines.append("<div class=line><span class=\'big\'>Orthotic ke %d voucher Marg mein daal diye &#10003;</span><br>"\n'
         '                             "<span class=\'big bad\'>Ab closing stock export kijiye</span><br>"\n'
         '                             "<span class=sub>Server khud milayega ki Marg ab shelf ke barabar hai.</span></div>" % int(A.get("total") or 0))\n',
         '            elif _s488_wait_html(pr):                          # S488 (B.2): since when, for what, and whose turn it is\n'
         '                lines.append("<div class=line><span class=\'big\'>Orthotic ke %d voucher Marg mein daal diye &#10003;</span><br>%s</div>"\n'
         '                             % (int(A.get("total") or 0), _s488_wait_html(pr)))\n'
         '            else:\n'
         '                lines.append("<div class=line><span class=\'big\'>Orthotic ke %d voucher Marg mein daal diye &#10003;</span><br>"\n'
         '                             "<span class=\'big bad\'>Ab closing stock export kijiye</span><br>"\n'
         '                             "<span class=sub>Server khud milayega ki Marg ab shelf ke barabar hai.</span></div>" % int(A.get("total") or 0))\n'),
        # B.2 the card: stage C's waiting_export
        ('            elif C.get("waiting_export"):\n'
         '                lines.append("<div class=line><span class=big>Dawa ke voucher Marg mein daal diye &#10003;</span><br>"\n'
         '                             "<span class=\'big bad\'>Ab closing stock export kijiye</span></div>")\n',
         '            elif C.get("waiting_export") and _s488_wait_html(_s488_proof(st)):     # S488 (B.2)\n'
         '                lines.append("<div class=line><span class=big>Dawa ke voucher Marg mein daal diye &#10003;</span><br>%s</div>"\n'
         '                             % _s488_wait_html(_s488_proof(st)))\n'
         '            elif C.get("waiting_export"):\n'
         '                lines.append("<div class=line><span class=big>Dawa ke voucher Marg mein daal diye &#10003;</span><br>"\n'
         '                             "<span class=\'big bad\'>Ab closing stock export kijiye</span></div>")\n'),
        # B.3 _s446_left: stage A's sentence, stage C's when the lot is all entered and waits
        ('                out.append("count #%d stage A: waiting for the closing-stock export that proves the orthotic vouchers" % st["count_id"])\n',
         '                _e488 = _s488_ending(A.get("proof"))           # S488 (B.3)\n'
         '                out.append(("count #%d stage A: %s" % (st["count_id"], _e488)) if _e488 else\n'
         '                           "count #%d stage A: waiting for the closing-stock export that proves the orthotic vouchers" % st["count_id"])\n'),
        ('            out.append("count #%d stage C: %d medicine vouchers of this lot not entered" % (st["count_id"], len(C.get("today") or [])))\n',
         '            _e488 = _s488_ending(_s488_proof(st)) if (C.get("waiting_export") and not C.get("today")) else ""     # S488 (B.3)\n'
         '            out.append(("count #%d stage C: this lot\'s vouchers entered -- %s" % (st["count_id"], _e488)) if _e488 else\n'
         '                       "count #%d stage C: %d medicine vouchers of this lot not entered" % (st["count_id"], len(C.get("today") or [])))\n'),
        # B.3 _s446_owner_lines: stage A's tail, and the 48-hour warn line
        ('if pr == "wrong" else "waiting for the closing-stock export"))\n',
         'if pr == "wrong" else (_s488_ending(A.get("proof")) or "waiting for the closing-stock export")))   # S488 (B.3)\n'),
        ('        out.append(dict(cls="info", target="stock", text="Count #%d: %s" % (st["count_id"], t)))\n',
         '        out.append(dict(cls="info", target="stock", text="Count #%d: %s" % (st["count_id"], t)))\n'
         '        _w488 = _s488_wait_line(con, st)                       # S488 (B.3): the proof has waited amir.proof_wait_hours or more\n'
         '        if _w488:\n'
         '            out.append(_w488)\n'),
        # B.2b his day's two lines (stage A, stage C)
        ('                out.append("Ginti #%d: orthotic voucher ki jaanch ke liye closing stock export baaki" % cid)\n',
         '                _t488 = _s488_tail_hi(A.get("proof"))          # S488 (B.2b)\n'
         '                out.append(("Ginti #%d: %s" % (cid, _t488)) if _t488 else "Ginti #%d: orthotic voucher ki jaanch ke liye closing stock export baaki" % cid)\n'),
        ('                out.append("Ginti #%d: dawa voucher ki jaanch ke liye closing stock export baaki" % cid)\n',
         '                _t488 = _s488_tail_hi(_s488_proof(st))         # S488 (B.2b)\n'
         '                out.append(("Ginti #%d: %s" % (cid, _t488)) if _t488 else "Ginti #%d: dawa voucher ki jaanch ke liye closing stock export baaki" % cid)\n'),
        # the block, at the end of the file
        ("# ---- S454 part 2 end -----------------------------------------------------------------------------------------------------------------\n",
         "# ---- S454 part 2 end -----------------------------------------------------------------------------------------------------------------\n"
         + AMIR_BLOCK),
    ])


# ------------------------------------------------------------------------------------------------------------------------ item_check.py
ITEM_BLOCK = '''

# ------------------------------------------------------------------ S488 (06-Oct-2026, Part D): a wrongly learnt name can be struck
# The first learnt name wins for ever (INSERT OR IGNORE on supplier + printed name), and learn() re-reads every verified link at each
# compare -- so a wrong pairing could never be taken back. The owner's "Wrong" moves the active row into s454_item_name_struck (one
# transaction); learn() never learns a struck pair again, so a different item can be learnt for the same printed name in its place.
# "Put back" re-inserts the struck row itself (a new learnt_at) -- refused while another item is active for that printed name.
def strike(con, supplier_norm, scan_norm, by=None, marg_item=None):
    """-> (ok, message). The active row of (supplier, printed name) is copied into the struck table and deleted, in one transaction."""
    ensure(con)
    r = con.execute("SELECT scan_name, marg_item FROM s454_item_name WHERE supplier_norm=? AND scan_norm=?", (supplier_norm, scan_norm)).fetchone()
    if not r:
        return False, "This name is not learnt any more -- reload the page."
    if marg_item and r[1] != marg_item:
        return False, "This name is learnt for another item now -- reload the page."
    try:
        con.execute("INSERT OR REPLACE INTO s454_item_name_struck (supplier_norm, scan_norm, scan_name, marg_item, struck_at, struck_by) VALUES (?,?,?,?,?,?)",
                    (supplier_norm, scan_norm, r[0], r[1], now_iso(), by))
        con.execute("DELETE FROM s454_item_name WHERE supplier_norm=? AND scan_norm=?", (supplier_norm, scan_norm))
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return True, "Struck: it is no longer used, and will not be learnt again."


def unstrike(con, supplier_norm, scan_norm, marg_item):
    """-> (ok, message). The struck pair goes back into s454_item_name at once (a new learnt_at) and leaves the struck table, in one
    transaction -- refused while another item is active for that printed name (learn's INSERT OR IGNORE would drop it from both lists)."""
    ensure(con)
    r = con.execute("SELECT scan_name FROM s454_item_name_struck WHERE supplier_norm=? AND scan_norm=? AND marg_item=?",
                    (supplier_norm, scan_norm, marg_item)).fetchone()
    if not r:
        return False, "This pair is not struck -- reload the page."
    if con.execute("SELECT 1 FROM s454_item_name WHERE supplier_norm=? AND scan_norm=?", (supplier_norm, scan_norm)).fetchone():
        return False, "Another item is learnt for this name \\u2014 tap Wrong on that one first."
    try:
        con.execute("INSERT INTO s454_item_name (supplier_norm, scan_norm, scan_name, marg_item, bill_id, asset_bill_id, learnt_at) VALUES (?,?,?,?,NULL,NULL,?)",
                    (supplier_norm, scan_norm, r[0], marg_item, now_iso()))
        con.execute("DELETE FROM s454_item_name_struck WHERE supplier_norm=? AND scan_norm=? AND marg_item=?", (supplier_norm, scan_norm, marg_item))
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return True, "Put back: it is used again."


def struck(con):
    ensure(con)
    return [dict(supplier_norm=r[0], scan_norm=r[1], scan_name=r[2], marg_item=r[3], struck_at=r[4], struck_by=r[5]) for r in
            con.execute("SELECT supplier_norm, scan_norm, scan_name, marg_item, struck_at, struck_by FROM s454_item_name_struck ORDER BY supplier_norm, scan_norm, marg_item")]
'''


def build_item_check(src):
    return edit("item_check.py", src, [
        ("#  READ ONLY of the asset app's database. Nothing here prints a phone number, an account number or a key.\n",
         "#  READ ONLY of the asset app's database. Nothing here prints a phone number, an account number or a key.\n"
         "#  S488 (06-Oct-2026, Part D): the owner can strike a wrongly learnt name (s454_item_name_struck) and put it back; a struck pair is\n"
         "#  never learnt again.\n"),
        ('       "bill_id INTEGER, asset_bill_id INTEGER, learnt_at TEXT NOT NULL, PRIMARY KEY (supplier_norm, scan_norm))")\n',
         '       "bill_id INTEGER, asset_bill_id INTEGER, learnt_at TEXT NOT NULL, PRIMARY KEY (supplier_norm, scan_norm))")\n'
         'STRUCK_DDL = ("CREATE TABLE IF NOT EXISTS s454_item_name_struck (supplier_norm TEXT NOT NULL, scan_norm TEXT NOT NULL, scan_name TEXT, "   # S488\n'
         '              "marg_item TEXT NOT NULL, struck_at TEXT NOT NULL, struck_by TEXT, PRIMARY KEY (supplier_norm, scan_norm, marg_item))")\n'),
        ("def ensure(con):\n    con.execute(DDL)\n",
         "def ensure(con):\n    con.execute(DDL)\n    con.execute(STRUCK_DDL)                                   # S488 (D.1)\n"),
        ("        scans = SR.asset_scans(con) or {}\n",
         "        gone = {(r[0], r[1], r[2]) for r in con.execute(\"SELECT supplier_norm, scan_norm, marg_item FROM s454_item_name_struck\")}   # S488\n"
         "        scans = SR.asset_scans(con) or {}\n"),
        ("                if not sn or sn == name_norm(x[\"item\"]) or not names_akin(sn, x[\"item\"]):\n                    continue\n",
         "                if not sn or sn == name_norm(x[\"item\"]) or not names_akin(sn, x[\"item\"]):\n                    continue\n"
         "                if (b[\"supplier_norm\"], sn, x[\"item\"]) in gone:        # S488: a struck pair is never learnt again\n"
         "                    continue\n"),
        ('    return [dict(supplier_norm=r[0], scan_name=r[1], marg_item=r[2], learnt_at=r[3]) for r in\n'
         '            con.execute("SELECT supplier_norm, scan_name, marg_item, learnt_at FROM s454_item_name ORDER BY supplier_norm, scan_norm")]\n',
         '    return [dict(supplier_norm=r[0], scan_name=r[1], marg_item=r[2], learnt_at=r[3], scan_norm=r[4]) for r in      # S488: + scan_norm\n'
         '            con.execute("SELECT supplier_norm, scan_name, marg_item, learnt_at, scan_norm FROM s454_item_name ORDER BY supplier_norm, scan_norm")]\n'
         + ITEM_BLOCK),
    ])


# ---------------------------------------------------------------------------------------------------------------------- purchase_app.py
ITEMS_JS = ('\nS488_ITEMS_JS = """\n'
            'async function s488strike(b){ const j = await post(P + \'/api/items/strike\', {supplier_norm: b.dataset.s, scan_norm: b.dataset.n, '
            'marg_item: b.dataset.m, do: b.dataset.do}); if (j) location.reload(); }\n'
            '"""\n')
STRIKE_ROUTE = '''

@bp.route("/api/items/strike", methods=["POST"])
def api_s488_items_strike():
    """S488 (D.2): the doctor marks a learnt item name Wrong (do=strike) or puts a struck one back (do=back). JSON in, {ok, message} out."""
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):                                      # the owner's page (S454 11.1)
        return _refuse("This is for the doctor only.")
    b = request.get_json(silent=True) or {}
    sn, nm, mi, do = (str(b.get(k) or "").strip() for k in ("supplier_norm", "scan_norm", "marg_item", "do"))
    if not sn or not nm or do not in ("strike", "back") or (do == "back" and not mi):
        return jsonify(ok=False, error="malformed", message="supplier_norm, scan_norm and do = strike | back (marg_item to put back)"), 400
    con = _db()
    _ensure(con)
    IC = _s454_ic()
    ok, msg = IC.strike(con, sn, nm, _who(u), mi or None) if do == "strike" else IC.unstrike(con, sn, nm, mi)
    if ok:
        try:                                                   # as sarvam_compare does for a newly learnt name: judged again
            con.execute("DELETE FROM purchase_sarvam_check WHERE bill_id IN (SELECT id FROM purchase_bill WHERE supplier_norm=?)", (sn,))
        except sqlite3.Error:
            pass
        _audit(con, _who(u), "s488_item_name_" + do, nm[:60], dict(supplier_norm=sn, marg_item=mi))
        con.commit()
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
'''


def build_purchase_app(src):
    return edit("purchase_app.py", src, [
        ('    learnt = IC.learnt(con)\n'
         '    ln = "".join("<li>%s: “%s” = %s</li>" % (_esc(x["supplier_norm"]), _esc(x["scan_name"]), _esc(x["marg_item"])) for x in learnt)\n',
         '    learnt = IC.learnt(con)\n'
         '    _bt = \'<button style="font-size:12px;padding:2px 10px;margin-left:6px" onclick="s488strike(this)" data-s="%s" data-n="%s" data-m="%s" data-do="%s">%s</button>\'   # S488 (D.2)\n'
         '    ln = "".join("<li>%s: “%s” = %s %s</li>" % (_esc(x["supplier_norm"]), _esc(x["scan_name"]), _esc(x["marg_item"]),\n'
         '                                                  _bt % (_esc(x["supplier_norm"]), _esc(x.get("scan_norm")), _esc(x["marg_item"]), "strike", "Wrong"))\n'
         '                 for x in learnt)\n'
         '    gone = IC.struck(con)\n'
         '    ln_struck = ("<details><summary>Struck: %d</summary><ul>%s</ul></details>" % (len(gone), "".join(\n'
         '        "<li>%s: “%s” = %s %s</li>" % (_esc(x["supplier_norm"]), _esc(x["scan_name"]), _esc(x["marg_item"]),\n'
         '                                          _bt % (_esc(x["supplier_norm"]), _esc(x["scan_norm"]), _esc(x["marg_item"]), "back", "Put back"))\n'
         '        for x in gone)))\n'),
        ("            'page judges a name by them first.</div><ul>%s</ul></div>'\n"
         "            % (_esc(_month_name(month)), nav, _esc(head), \"\".join(rows) or '<div class=\"card\">Every bill of the month adds up.</div>', len(learnt), ln))\n",
         "            'page judges a name by them first. Tap Wrong on a name that is not the same item; it stops being used at once and can be put back.'\n"
         "            '</div><ul>%s</ul>%s</div>'\n"
         "            % (_esc(_month_name(month)), nav, _esc(head), \"\".join(rows) or '<div class=\"card\">Every bill of the month adds up.</div>', len(learnt), ln,\n"
         "               ln_struck))\n"),
        ('    return _page("Items check — %s" % _month_name(month), _s454_items_body(con, month, request.script_root + _url_prefix))\n',
         '    return _page("Items check — %s" % _month_name(month), _s454_items_body(con, month, request.script_root + _url_prefix), S488_ITEMS_JS)\n'
         + STRIKE_ROUTE),
        ("def _s454_items_body(con, month, prefix):\n",
         ITEMS_JS.lstrip("\n") + "\n\ndef _s454_items_body(con, month, prefix):\n"),
    ])


# ----------------------------------------------------------------------------------------------------------------------- reports_tile.py
TILE_BLOCK = '''# S488 (C.1): each list's overdue limit is a setting row (owner.salt_list_days 8, owner.item_lists_days 35); OWNER_LISTS keeps the constants
S488_LIST_KEYS = {"SALT_WISE_ITEM_LIST": "owner.salt_list_days", "CATEGORY_WISE_ITEM_LIST": "owner.item_lists_days", "ITEM_MASTER": "owner.item_lists_days"}


def _s488_list_limit(cx, typ, default):
    """The limit from its setting when the value is all digits, else the constant. Guarded: a database with no setting table (this
    file's own selftest) keeps the constant."""
    key = S488_LIST_KEYS.get(typ)
    if not key:
        return default
    try:
        r = cx.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        return default
    v = str((r[0] if r else "") or "").strip()
    return int(v) if v.isdigit() else default


'''


def build_reports_tile(src):
    return edit("reports_tile.py", src, [
        ("def owner_lists(cx, today):\n", TILE_BLOCK + "def owner_lists(cx, today):\n"),
        ("    for typ, label, limit in OWNER_LISTS:\n        last = _spine_last_as_on(typ)\n",
         "    for typ, label, limit in OWNER_LISTS:\n        limit = _s488_list_limit(cx, typ, limit)                # S488 (C.1)\n"
         "        last = _spine_last_as_on(typ)\n"),
    ])


BUILD = {"stock_app.py": build_stock_app, "darpan_app.py": build_darpan_app, "owner_sheets.py": build_owner_sheets,
         "stock_watch.py": build_stock_watch, "shelf_figure.py": build_shelf_figure, "amir_day.py": build_amir_day,
         "item_check.py": build_item_check, "purchase_app.py": build_purchase_app, "reports_tile.py": build_reports_tile}


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

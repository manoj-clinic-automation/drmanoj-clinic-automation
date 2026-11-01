#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s690.py -- kit S690_AMIR_BATCH_FIX (01-Nov-2026, Sanjeevni session 369).

    python3 -B make_s690.py <root> <outdir>      reads <root>/finance/expiry_watch.py and <root>/finance/amir_day.py,
                                                 writes both under <outdir>/finance/

WHY.  The owner, 30-Oct 18:29-23:30 and 31-Oct 13:11 ("MOCKUP IS GOOD"): Amir's "Marg mein in N dawaon ka batch theek karein" list told
him what was wrong, not what to do; it never changed after his fixes (the Batch Stock came once a month); and he is NEVER to open or edit
a sale bill.  The fix: a wrong batch is corrected by a Marg STOCK RECEIVE into the minus batch and a STOCK ISSUE from the batch that has
the stock (the system picks the earliest-expiry batch with stock; max 6 lines a voucher; split when short); he saves the Batch Stock
(whole store) at the end of every visit as the third export of step 4; the server rechecks within five minutes and tells him, line by
line, theek ho gaya / abhi baaki / Issue baaki (by name) / a partial print.  A no-batch sale lands on his card as the same pair.

WHAT.  Two files, anchored edits (each anchor must occur exactly once, else the builder refuses).
  expiry_watch.py (23e0a5bf):
    1. KIT line.
    2. compute(): the wrong lines carry the figures the pair needs -- below [batch, qty, named, units], has [batch, qty, expiry, units];
       a no-batch line carries the item's batches with stock too; the run keeps its lowered batches, its sales day and the items bought
       since (not persisted) for the fixes.
    3. run(): after the lines are written, fixes_judge (a NEW report judges every open row) then fixes_create (a row per minus batch no
       open row covers); the log line says how many.
    4. amir_rows(): the monthly Batch Stock card and the folded list go; the voucher pair, the confirmation and the done list come
       (fixes_rows).
    5. owner_page section 4: one line -- the vouchers asked of Amir, open / Receive done / done.
    6. The S690 block: stock_batch_fix, fixes_ensure / fixes_create / fixes_judge / fixes_rows, batch_stock_state, new_batch_stock.
    7. main(): run --if-new (the cron's five-minute pass).
  amir_day.py (a0907b74):
    1. KIT line.
    2. state(): S.batchstock = expiry_watch.batch_stock_state (fail-soft).
    3. _step4(): the third export's card under the pair's "Do report" card -- none (with the steps) / wait / ok / bad.  It never gates
       his day (D708 / D712: monthly work proved only by the next report).
"""
import hashlib
import os
import sys

FROM = {"finance/expiry_watch.py": "23e0a5bf92f9f697bfbbda87c91bdee5",
        "finance/amir_day.py": "a0907b74fb90584d9440551aa82f9928"}

S690_BLOCK = '''
# ==========================================================================================================================================
# S690_AMIR_BATCH_FIX (01-Nov-2026; the owner's rulings of 30-Oct, his "MOCKUP IS GOOD" of 31-Oct) -- a wrong batch is corrected by a
# voucher pair, never by a sale bill; the Batch Stock at the end of every visit confirms it.
#   * stock_batch_fix: one row per minus batch the watch names (a wrong/batch line's below, or a no-batch sale): the STOCK RECEIVE into the
#     minus batch and the STOCK ISSUE from the batch that has the stock (the earliest expiry with stock; split when short), FROZEN when
#     made (D542: a round is never re-edited; a later difference is a new row after the next report).
#   * fixes_create at every run; fixes_judge at a run whose Batch Stock is a NEW report: the Receive is done when the minus batch's printed
#     figure is no longer below zero; the Issue is done when the issue batch's printed figure has dropped by the voucher beyond its sales
#     between the two reports -> done / receive_only / issue_only / open.  An item bought between the reports is judged on the Receive.
#     Until the spine holds the report day's sales (sales_to >= the report's day) only the Receive is judged; the Issue waits for the
#     next run (the nightly, after the day's sale export) -- a fast mover's Issue is never called done on sales not yet counted.
#     A minus that moved while nothing of its rows was done: the rows are superseded and remade from the new report (one round).
#   * fixes_rows (Amir's card): the confirmation (a report judged in the last 24 h), the done list, the vouchers -- max VOUCHER_LINES a
#     voucher, the Receive set then the Issue set, numbered from 1.  his_line False: monthly work, never a gate (D708 / D712).
#   * batch_stock_state: step 4's third export -- none / wait / ok / bad, from mi_file and the newest run.
#   * new_batch_stock: run --if-new runs the watch only when a Batch Stock newer than the newest run has reached the door.
# ==========================================================================================================================================
FIX_KIT = "S690_AMIR_BATCH_FIX"
VOUCHER_LINES = 6
FIX_OPEN = ("open", "receive_only", "issue_only")


def fixes_ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS stock_batch_fix (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, k20 TEXT NOT NULL, "
                "item TEXT NOT NULL, pack INTEGER NOT NULL, minus_batch TEXT NOT NULL, units INTEGER NOT NULL, issue_batch TEXT NOT NULL, "
                "issue_printed INTEGER, issue_expiry TEXT, asked_run_id INTEGER NOT NULL, asked_md5 TEXT, asked_day TEXT, "
                "asked_at TEXT NOT NULL, status TEXT NOT NULL, judged_run_id INTEGER, judged_md5 TEXT, judged_at TEXT, done_at TEXT, note TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_stock_batch_fix_status ON stock_batch_fix (status, k20, minus_batch)")


def _fix_rows(con, where, args=()):
    cols = [d[0] for d in con.execute("SELECT * FROM stock_batch_fix LIMIT 0").description]
    return [dict(zip(cols, tuple(r))) for r in con.execute("SELECT * FROM stock_batch_fix WHERE " + where + " ORDER BY id", args)]


def _fix_same_batch(a, b):
    """The same batch typed differently: equal once upper-cased, stripped of spaces and punctuation and read with I as 1 and O as 0
    (GIF005003 = G1F005003), or the same digits, leading zeros aside, four or more (62607 = SL062607, TSF B1222 = TSF E1222)."""
    def norm(x):
        return re.sub(r"[^A-Z0-9]", "", str(x or "").upper()).replace("I", "1").replace("O", "0")
    def digs(x):
        return re.sub(r"[^0-9]", "", str(x or "")).lstrip("0")
    na, nb = norm(a), norm(b)
    if na and na == nb:
        return True
    da, db = digs(a), digs(b)
    return len(da) >= 4 and da == db


def _fix_issue_order(minus_batch, has):
    """The batches to issue from, in order: the SAME batch typed differently first (the digits agree, 4 or more; the larger stock
    first -- SYSFOL 62607 is SL062607, MEG QCS TSF B1222 is TSF E1222), then the earliest expiry with the larger stock first."""
    same = [h for h in has if _fix_same_batch(minus_batch, h[0])]
    rest = [h for h in has if h not in same]
    return (sorted(same, key=lambda h: (-int(h[3]), h[0]))
            + sorted(rest, key=lambda h: (h[2] or "9999-99", -int(h[3]), h[0])))


def fixes_create(con, rid, r, lines, at):
    """One row per minus batch the run names that no open row covers.  The Issue from the earliest-expiry batch with stock, split when
    that batch is short; what no batch can cover is left (the owner's page says so).  Returns [(item, minus batch, units, issue batch)]."""
    bt = r.get("_bt") or {}
    have = {(x["k20"], x["minus_batch"]) for x in _fix_rows(con, "status IN (?,?,?)", FIX_OPEN)}
    made = []
    for x in lines:
        if x.get("section") != "wrong" or x.get("part") not in ("batch", "nobatch"):
            continue
        info = x.get("info") or {}
        if isinstance(info, str):
            try:
                info = json.loads(info)
            except ValueError:
                info = {}
        pack = int(x.get("pack") or 1)
        has_all = [h for h in info.get("has", []) if len(h) >= 4 and int(h[3] or 0) > 0]
        if x["part"] == "batch":
            below = [(b[0] or "", -int(b[3])) for b in info.get("below", []) if len(b) >= 4 and int(b[3] or 0) < 0]
        else:
            below = [("", int(x.get("units") or 0))]
        left = {h[0]: int(h[3]) for h in has_all}
        for mb, need in below:
            if need <= 0 or (x["k20"], mb) in have:
                continue
            has = _fix_issue_order(mb, has_all)
            for h in has:
                if need <= 0:
                    break
                take = min(left.get(h[0], 0), need)
                if take <= 0:
                    continue
                pr = (bt.get((x["k20"], h[0])) or {}).get("printed")
                con.execute("INSERT INTO stock_batch_fix (kind, k20, item, pack, minus_batch, units, issue_batch, issue_printed, issue_expiry, "
                            "asked_run_id, asked_md5, asked_day, asked_at, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (x["part"], x["k20"], x["item"], pack, mb, take, h[0], pr, h[2] or "", rid, r.get("export_md5"),
                             r.get("_sales_after") or r.get("export_as_on") or "", at, "open"))
                left[h[0]] -= take
                need -= take
                made.append((x["item"], mb, take, h[0]))
            have.add((x["k20"], mb))
    return made


def fixes_judge(con, sp, alias, rid, r, at):
    """At a run whose Batch Stock is a NEW report (not the one a row was asked on, not one it was judged on): the printed figures decide."""
    md5, bt = r.get("export_md5"), r.get("_bt")
    if not md5 or not bt:
        return []
    new_after = r.get("_sales_after") or r.get("export_as_on") or ""
    caught_up = (r.get("sales_to") or "") >= new_after          # the spine holds the report day's sales: the Issue can be judged
    out = []
    for f in _fix_rows(con, "status IN (?,?,?) AND COALESCE(asked_md5,'')<>? AND COALESCE(judged_md5,'')<>?", FIX_OPEN + (md5, md5)):
        pm = (bt.get((f["k20"], f["minus_batch"])) or {}).get("printed", 0) or 0
        receive_done = pm >= 0
        if not caught_up:                                      # the Receive is read off the print now; the Issue waits for the sales
            st = "receive_only" if receive_done else "open"
            con.execute("UPDATE stock_batch_fix SET status=?, judged_run_id=?, judged_at=?, note=? WHERE id=?",
                        (st, rid, at, "issue pending the day's sales (%s)" % md5[:8], f["id"]))
            out.append((f["item"], f["minus_batch"], st + " (issue pending)"))
            continue
        pi_new = (bt.get((f["k20"], f["issue_batch"])) or {}).get("printed", 0) or 0
        pi_old = f.get("issue_printed")
        sold = 0
        try:
            for l in sp.execute("SELECT l.k20, l.batch, l.units, COALESCE(b.credit_note, 0) AS cn FROM sp_sale_line l "
                                "LEFT JOIN sp_sale_bill b ON b.date = l.date AND b.bill = l.bill WHERE l.date > ? AND l.date <= ?",
                                (f.get("asked_day") or "", new_after)):
                if alias.get(l["k20"], l["k20"]) == f["k20"] and nbatch(l["batch"]) == f["issue_batch"]:
                    sold += int(round(l["units"] or 0)) * (-1 if l["cn"] else 1)
        except sqlite3.Error:
            sold = 0
        try:                                                   # bought between the two reports: the Issue cannot be read off the figure
            bought_between = sp.execute("SELECT 1 FROM sp_move WHERE k20=? AND kind='PURCHASE' AND date > ? AND date <= ? LIMIT 1",
                                        (f["k20"], f.get("asked_day") or "", new_after)).fetchone() is not None
        except sqlite3.Error:
            bought_between = False
        if bought_between or pi_old is None:
            issue_done = receive_done                          # a re-supply moved the figure: the Receive alone is judged
        else:
            issue_done = pi_new <= int(pi_old) - sold - int(f["units"])
        st = "done" if (receive_done and issue_done) else ("receive_only" if receive_done else ("issue_only" if issue_done else "open"))
        units = int(f["units"])
        if st == "issue_only" and pm < 0:
            units = -pm                                        # the Receive still needed is the minus as it stands now, not the asked figure
        con.execute("UPDATE stock_batch_fix SET status=?, units=?, judged_run_id=?, judged_md5=?, judged_at=?, note=NULL, "
                    "done_at=CASE WHEN ?='done' THEN ? ELSE done_at END WHERE id=?", (st, units, rid, md5, at, st, at, f["id"]))
        out.append((f["item"], f["minus_batch"], st))
    # a minus batch whose figure MOVED while nothing of its rows was done: those rows are superseded, and fixes_create (next) makes the
    # current ones from this report -- one round, the figures of today (a row half done is never touched: D542)
    for k20, mb in {(f["k20"], f["minus_batch"]) for f in _fix_rows(con, "status='open' AND judged_run_id=?", (rid,))}:
        rows = _fix_rows(con, "k20=? AND minus_batch=? AND status IN (?,?,?)", (k20, mb) + FIX_OPEN)
        if any(x["status"] != "open" for x in rows):
            continue
        pm = (bt.get((k20, mb)) or {}).get("printed", 0) or 0
        if pm < 0 and -pm != sum(int(x["units"]) for x in rows):
            con.execute("UPDATE stock_batch_fix SET status='superseded', note=? WHERE k20=? AND minus_batch=? AND status='open'",
                        ("the minus moved to %d on %s; remade" % (pm, md5[:8]), k20, mb))
            out.append((rows[0]["item"], mb, "superseded"))
    return out


def _fix_chunks(lines):
    return [lines[i:i + VOUCHER_LINES] for i in range(0, len(lines), VOUCHER_LINES)]


def _fix_bname(b):
    return esc(b) if b else "bina batch"


def fixes_rows(con, today=None):
    """Amir's card rows (amir_day's shape): the confirmation line, the done list, the vouchers.  Nothing when there is nothing."""
    today = today or now_ist().date()
    if not _has(con, "stock_batch_fix"):
        return []
    try:
        opn = _fix_rows(con, "status IN (?,?,?)", FIX_OPEN)
        since = (now_ist() - dt.timedelta(hours=24)).replace(microsecond=0).isoformat()
        done = _fix_rows(con, "status='done' AND COALESCE(done_at,'')>=?", (since,))
        judged = con.execute("SELECT MAX(judged_at), MAX(judged_run_id) FROM stock_batch_fix WHERE COALESCE(judged_at,'')>=?", (since,)).fetchone()
    except sqlite3.Error:
        return []
    html = []
    if judged and judged[0]:
        hhmm = str(judged[0])[11:16]
        jr = con.execute("SELECT export_md5, at FROM stock_expiry_run WHERE id=?", (judged[1],)).fetchone() if judged[1] else None
        if jr:
            try:
                got = con.execute("SELECT received_at FROM mi_file WHERE md5=? LIMIT 1", (jr[0],)).fetchone()
                if got and got[0]:
                    hhmm = str(got[0])[11:16]
            except sqlite3.Error:
                pass
        pend = [x for x in opn if (x.get("judged_at") or "") >= since]
        html.append("<div class='line s690conf'><span class='big good'>Batch Stock mil gayi %s &#10003; &mdash; %d batch theek ho gaye, %d abhi baaki</span>"
                    % (esc(hhmm), len(done), len(pend)))
        if done:
            html.append("<div class=s690done style='background:#f2f9f4;border:1px solid #bfe0c6;border-radius:10px;padding:8px 12px;margin:8px 0 0'>"
                        "<b>Theek ho gaya &#10003;</b> (yeh line kal hat jayegi)<ul style='margin:6px 0 0;padding-left:20px'>%s</ul></div>"
                        % "".join("<li>%s &middot; <span style='font-family:monospace'>%s</span></li>" % (esc(x["item"]), _fix_bname(x["minus_batch"])) for x in done))
        if pend:
            li = []
            for x in pend:
                q = qty_txt(x["units"], x["pack"])
                if x["status"] == "receive_only" and str(x.get("note") or "").startswith("issue pending"):
                    li.append("<li><b>%s</b> &mdash; Receive ho gaya &#10003;; Issue ki jaanch kal subah (aaj ki sale ginne ke baad)</li>" % esc(x["item"]))
                elif x["status"] == "receive_only":
                    li.append("<li><b>%s</b> &mdash; Receive ho gaya &#10003;, Issue baaki: <span style='font-family:monospace'>%s</span> se <b>%s</b> issue karein</li>"
                              % (esc(x["item"]), esc(x["issue_batch"]), esc(q)))
                elif x["status"] == "issue_only":
                    li.append("<li><b>%s</b> &mdash; Issue ho gaya &#10003;, Receive baaki: <span style='font-family:monospace'>%s</span> mein <b>%s</b> receive karein</li>"
                              % (esc(x["item"]), _fix_bname(x["minus_batch"]), esc(q)))
                else:
                    li.append("<li><b>%s</b> &mdash; dono baaki: Receive <span style='font-family:monospace'>%s</span> %s &middot; Issue <span style='font-family:monospace'>%s</span> %s</li>"
                              % (esc(x["item"]), _fix_bname(x["minus_batch"]), esc(q), esc(x["issue_batch"]), esc(q)))
            html.append("<div class=s690open style='background:#fff8e6;border:1px solid #f0c36d;border-radius:10px;padding:8px 12px;margin:8px 0 0'>"
                        "<b>Abhi baaki</b><ul style='margin:6px 0 0;padding-left:20px'>%s</ul></div>" % "".join(li))
        html.append("</div>")
    if opn:
        rec = [(x["item"], x["minus_batch"], qty_txt(x["units"], x["pack"])) for x in opn if x["status"] in ("open", "issue_only")]
        iss = [(x["item"], x["issue_batch"], qty_txt(x["units"], x["pack"])) for x in opn if x["status"] in ("open", "receive_only")]
        chunks = [("STOCK RECEIVE", c) for c in _fix_chunks(rec)] + [("STOCK ISSUE", c) for c in _fix_chunks(iss)]
        vs = []
        for n, (kind, c) in enumerate(chunks, 1):
            body = "".join("<tr><td>%s</td><td><span style='font-family:monospace'>%s</span></td><td style='text-align:right;white-space:nowrap;font-weight:600'>%s</td></tr>"
                           % (esc(it), _fix_bname(b), esc(q)) for it, b, q in c)
            vs.append("<div class=s690v style='border:1px solid #cfe0ef;border-radius:10px;background:#f3f7fb;padding:8px 12px;margin:0 0 10px'>"
                      "<h3 style='margin:0 0 6px;font-size:16px'>Voucher %d &mdash; %s (%d line)</h3>"
                      "<table style='width:100%%;border-collapse:collapse;font-size:15px'>%s</table></div>" % (n, kind, len(c), body))
        new_ones = [x for x in opn if (x.get("asked_at") or "") >= since and not x.get("judged_at")]
        head = ("Kal ki sale se %d naya &mdash; voucher Marg mein daaliye" % len(new_ones)) if (new_ones and len(new_ones) == len(opn) and judged and judged[0]) \\
            else ("Batch theek karne ke %d voucher Marg mein daaliye" % len(chunks))
        html.append("<div class='line s690fix'><span class=big>%s</span>"
                    "<p class=sub style='margin:4px 0 10px'>Bill mat kholiye. Voucher jaisa likha hai waisa daaliye &mdash; batch bhi wahi chuniye jo likha hai. "
                    "Daal kar step 4 mein Batch Stock nikaaliye; jo theek ho gaya woh yahan se khud hat jayega. (Matra strip:tab)</p>%s"
                    "<p class=sub style='margin:0'>Dawa ki kul matra nahi badalti &mdash; sirf galat batch se sahi batch par jaati hai.</p></div>"
                    % (head, "".join(vs)))
    if not html:
        return []
    return [("batchfix", "".join(html), "batch vouchers: %d open, %d done in 24 h" % (len(opn), len(done)), False)]


def fixes_owner_line(con):
    """One line for the owner's page: the vouchers asked of Amir and where they stand."""
    if not _has(con, "stock_batch_fix"):
        return ""
    try:
        opn = _fix_rows(con, "status IN (?,?,?)", FIX_OPEN)
        nd = con.execute("SELECT COUNT(*), MAX(done_at) FROM stock_batch_fix WHERE status='done'").fetchone()
    except sqlite3.Error:
        return ""
    if not opn and not (nd and nd[0]):
        return ""
    half = [x for x in opn if x["status"] != "open"]
    bits = ["%d voucher line%s open with Amir" % (len(opn), "" if len(opn) == 1 else "s")]
    if half:
        bits.append("%d half done (%s)" % (len(half), ", ".join("%s: %s" % (x["item"], "Issue pending" if x["status"] == "receive_only" else "Receive pending") for x in half[:4])))
    if nd and nd[0]:
        bits.append("%d done, the last on %s" % (nd[0], dmon(str(nd[1] or "")[:10])))
    return '<p class="note">Batch fixes (S690): %s.</p>' % esc(" · ".join(bits))


def batch_stock_state(con, today=None):
    """Step 4's third export, from the door and the newest run: none | wait | ok | bad (+ at hh:mm, items, reason)."""
    today = today or now_ist().date()
    d = today.isoformat()
    try:
        r = con.execute("SELECT received_at, md5, server_name FROM mi_file WHERE type='BATCH_STOCK' AND verdict='VERIFIED' "
                        "AND (substr(stamp,1,8)=? OR substr(received_at,1,10)=?) ORDER BY received_at DESC LIMIT 1",
                        (d.replace("-", ""), d)).fetchone()
    except sqlite3.Error:
        r = None
    if not r:
        return dict(state="none")
    at = str(r[0])[11:16]
    run_, _sec = newest(con)
    if run_ and run_.get("export_md5") == r[1]:
        return dict(state="ok", at=at, items=run_.get("export_items") or 0, as_on=run_.get("export_as_on") or "")
    if run_ and str(run_.get("at") or "")[:19] > str(r[0])[:19]:
        note = run_.get("note") or ""
        if "filtered" in note and (r[2] or "")[:40] in note:
            return dict(state="bad", at=at, reason="poore store ki nahi thi")
        return dict(state="bad", at=at, reason="padhi nahi ja saki")
    return dict(state="wait", at=at)


def new_batch_stock(db):
    """True when a VERIFIED Batch Stock reached the door after the newest run (run --if-new)."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=10)
    except sqlite3.Error:
        return False
    try:
        if not _has(con, "mi_file"):
            return False
        r = con.execute("SELECT received_at, md5 FROM mi_file WHERE type='BATCH_STOCK' AND verdict='VERIFIED' ORDER BY received_at DESC LIMIT 1").fetchone()
        if not r:
            return False
        if not _has(con, "stock_expiry_run"):
            return True
        n = con.execute("SELECT at, export_md5 FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
        if not n:
            return True
        return str(r[0])[:19] > str(n[0])[:19] and n[1] != r[1]
    except sqlite3.Error:
        return False
    finally:
        con.close()

'''

EDITS_EW = [
    ('KIT = "S638_EXPIRY_WATCH"\n',
     'KIT = "S690_AMIR_BATCH_FIX"          # S638 built the watch; S690: the voucher pair, the Batch Stock every visit, the confirmation\n'),
    # compute: the figures the pair needs, kept on the run
    ('                    info=dict(below=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("_named") or ""] for b in neg],\n'
     '                              has=[[b["batch"] or "", qty_txt(b["units"], b["pack"])] for b in pos]))\n',
     '                    info=dict(below=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("_named") or "", int(b["units"])] for b in neg],\n'
     '                              has=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("expiry") or "", int(b["units"])] for b in pos]))\n'
     '        run["_bt"], run["_sales_after"], run["_bought"] = bt, sales_after, bought_since    # S690: for the fixes (never persisted)\n'),
    ('            add("wrong", part="nobatch", k20=k, item=k, batch="", expiry="", units=sum(w["units"] for w in ws), pack=1, packing="",\n'
     '                last_sale=max(w["date"] for w in ws), last_buy=None, info=dict(lines=len(ws), first=min(w["date"] for w in ws)))\n',
     '            bs = by_item.get(k) or []\n'
     '            add("wrong", part="nobatch", k20=k, item=(bs[0]["item"] if bs else k), batch="", expiry="", units=sum(w["units"] for w in ws),\n'
     '                pack=(bs[0]["pack"] if bs else 1), packing=(bs[0]["packing"] if bs else ""),\n'
     '                last_sale=max(w["date"] for w in ws), last_buy=None,\n'
     '                info=dict(lines=len(ws), first=min(w["date"] for w in ws),\n'
     '                          has=[[b["batch"] or "", qty_txt(b["units"], b["pack"]), b.get("expiry") or "", int(b["units"])] for b in bs if b["units"] > 0]))\n'),
    # run(): judge, then create
    ('                              x.get("info"), x["seq"]) for x in lines])\n'
     '        log("expiry_watch %s: run %d · export %s (as on %s) · %s · %s" % (KIT, rid, (r.get("export_name") or "none")[:70],\n'
     '                                                                         r.get("export_as_on") or "-", r.get("counts"), (r.get("note") or "")[:200]))\n',
     '                              x.get("info"), x["seq"]) for x in lines])\n'
     '        judged, made = [], []\n'
     '        try:                                                  # S690: the voucher pair -- a new report judges, the run names; never the run\'s own\n'
     '            with con:\n'
     '                fixes_ensure(con)\n'
     '                judged = fixes_judge(con, sp, alias, rid, r, r["at"])\n'
     '                made = fixes_create(con, rid, r, lines, r["at"])\n'
     '        except Exception as ex:                               # noqa: BLE001\n'
     '            log("expiry_watch %s: the fixes failed and were rolled back (%s: %s); the lists stand" % (KIT, type(ex).__name__, str(ex)[:120]))\n'
     '        log("expiry_watch %s: run %d · export %s (as on %s) · %s · fixes judged %d, new %d · %s" % (KIT, rid, (r.get("export_name") or "none")[:70],\n'
     '                                                                         r.get("export_as_on") or "-", r.get("counts"), len(judged), len(made), (r.get("note") or "")[:200]))\n'),
    # amir_rows: the card and the folded list go; the pair comes
    ('    today = today or now_ist().date()\n'
     '    rows = []\n'
     '    if not batch_stock_in(con, today):\n'
     '        rows.append(("batchstock", EXPORT_CARD_HI % dict(mon=MON[today.month]),\n'
     '                     "the month\'s Batch Stock (whole store) to export as text", False))\n'
     '    run_, sec = newest(con)\n',
     '    today = today or now_ist().date()\n'
     '    rows = []                                                 # S690: the Batch Stock is step 4\'s third export now (amir_day)\n'
     '    run_, sec = newest(con)\n'),
    ('        wr = [x for x in sec.get("wrong", []) if x["part"] == "batch"]\n'
     '        if wr:\n'
     '            li = "".join("<li>%s &mdash; minus: %s &middot; stock wala: %s</li>"\n'
     '                         % (esc(x["item"]), esc(", ".join("%s %s" % (b[0] or "bina batch", b[1]) for b in x["info"].get("below", []))),\n'
     '                            esc(", ".join("%s %s" % (b[0], b[1]) for b in x["info"].get("has", [])))) for x in wr)\n'
     '            rows.append(("batchfix", "<div class=\'line s638fix\'><details><summary class=big>Marg mein in %d dawaon ka batch theek karein"\n'
     '                         "</summary><ul>%s</ul></details></div>" % (len(wr), li), "batches to correct in Marg: %d" % len(wr), False))\n'
     '    return rows\n',
     '    rows.extend(fixes_rows(con, today))                       # S690: the voucher pair, the confirmation, the done list\n'
     '    return rows\n'),
    # owner page section 4: one line
    ('                  (\'<p class="note">Sold this month with no batch at all (%d items): %s.</p>\'\n'
     '                   % (len(nb), esc(", ".join("%s (%d)" % (x["item"], (x["info"] or {}).get("lines", 0)) for x in nb)))) if nb else ""))\n',
     '                  ((\'<p class="note">Sold this month with no batch at all (%d items): %s.</p>\'\n'
     '                   % (len(nb), esc(", ".join("%s (%d)" % (x["item"], (x["info"] or {}).get("lines", 0)) for x in nb)))) if nb else "")\n'
     '                  + fixes_owner_line(con)))\n'),
    # the block and main
    ('\ndef main(argv=None):\n',
     S690_BLOCK + '\ndef main(argv=None):\n'),
    ('    ap.add_argument("--date", default="")\n',
     '    ap.add_argument("--date", default="")\n'
     '    ap.add_argument("--if-new", action="store_true", help="S690: run only when a Batch Stock newer than the newest run has reached the door")\n'),
    ('    if a.cmd == "run":\n'
     '        return run(a.db, a.spine, a.archive, dt.date.fromisoformat(a.date) if a.date else None)\n',
     '    if a.cmd == "run":\n'
     '        if a.if_new and not new_batch_stock(a.db):\n'
     '            return 0\n'
     '        return run(a.db, a.spine, a.archive, dt.date.fromisoformat(a.date) if a.date else None)\n'),
]

AMIR_CARD = '''
def _s690_batchstock_card(S):
    """S690: step 4's third export -- the Batch Stock (whole store), saved AFTER the vouchers.  Never a gate."""
    b = getattr(S, "batchstock", None) or {}
    st = b.get("state") or "none"
    if st == "ok":
        line = ("<div class=line><span class='big good'>Batch Stock (poora store) &#10003;</span><br>"
                "<span class=sub>%s &middot; %s dawa &middot; %s baje &middot; batch sudhar ki jaanch ho gayi &mdash; "
                "<a href='/finance/amir/step/3'>step 3 dekhiye</a></span></div>"
                % (_esc(_ddmmyyyy(b.get("as_on")) if b.get("as_on") else ""), _esc(b.get("items") or 0), _esc(b.get("at") or "")))
        return "<div class=card><h2>Teesri report</h2>%s</div>" % line
    if st == "wait":
        return ("<div class=card><h2>Teesri report</h2><div class=line><span class='big warn'>Batch Stock (poora store) &hellip;</span><br>"
                "<span class=sub>Server par %s baje aa gayi &mdash; jaanch ho rahi hai (5 minute). Aapko kuch nahi karna.</span></div></div>"
                % _esc(b.get("at") or ""))
    if st == "bad":
        return ("<div class=card><h2 class=bad>Batch Stock poore store ki nahi thi &#10007;</h2><div class=line>"
                "<span class='big bad'>Batch Stock (poora store) &#10007;</span><br><span class=sub>%s baje ki report %s. "
                "Select Store mein <b>WHOLE</b> chun kar dobara nikaaliye.</span></div></div>" % (_esc(b.get("at") or ""), _esc(b.get("reason") or "")))
    return ("<div class=card><h2>Teesri report: Batch Stock (poora store)</h2>"
            "<div class=line><span class=big>Batch Stock (poora store)</span><br>"
            "<span class=sub>Abhi nikaali nahi gayi. Voucher daalne ke <b>BAAD</b> nikaaliye &mdash; isi se pata chalta hai kaun sa batch theek ho gaya.</span>"
            "<div style='background:#f3f7fb;border:1px solid #cfe0ef;border-radius:10px;padding:8px 12px;margin:8px 0 0;font-size:15px'><b>Tarika</b>"
            "<ol style='margin:6px 0 0;padding-left:20px'>"
            "<li>Marg main screen &rarr; <b>Stocks</b> &rarr; <b>Batch Stock</b></li>"
            "<li>Select Store &rarr; <b>WHOLE</b> &rarr; Enter</li>"
            "<li>Selected Company <b>No</b> &middot; Stock as on: jo date Marg dikhaye &middot; Stock Status <b>Available</b> &middot; "
            "Selected Salt <b>No</b> &middot; More Options <b>No</b> &rarr; <b>Accept</b></li>"
            "<li>Report menu &rarr; <b>A Stock Statement</b> &middot; Index On &rarr; <b>B Alphabatic</b></li>"
            "<li>Separate Printing <b>1 No</b>, dono Chr box khaali &rarr; Enter &rarr; <b>View</b></li>"
            "<li>Text mein save kijiye &mdash; jaise purchase report</li></ol></div></div></div>")

'''

EDITS_AD = [
    ('KIT = "S678_AMIR_PAIR_FROM_DOOR"                          # the kit that last placed this file (S533 built the page; S584 named it; '
     'S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner\'s 48-hour line; S638: the expiry '
     'watch\'s rows; S678: a report the server\'s own door holds is never "nahi aayi")',
     'KIT = "S690_AMIR_BATCH_FIX"                               # the kit that last placed this file (S533 built the page; S584 named it; '
     'S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner\'s 48-hour line; S638: the expiry '
     'watch\'s rows; S678: a report the server\'s own door holds is never "nahi aayi"; S690: the Batch Stock as step 4\'s third export)'),
    ('        S.expiry = expiry_watch.amir_rows(cx)\n'
     '    except Exception:                                          # noqa: BLE001\n'
     '        S.expiry = []\n',
     '        S.expiry = expiry_watch.amir_rows(cx)\n'
     '    except Exception:                                          # noqa: BLE001\n'
     '        S.expiry = []\n'
     '    S.batchstock = {}                                          # S690: step 4\'s third export (fail-soft)\n'
     '    try:\n'
     '        import expiry_watch                                    # noqa: PLC0415\n'
     '        S.batchstock = expiry_watch.batch_stock_state(cx)\n'
     '    except Exception:                                          # noqa: BLE001\n'
     '        S.batchstock = {}\n'),
    ('\ndef _step4(S):\n', AMIR_CARD + '\ndef _step4(S):\n'),
    ('    body = head + "<div class=card><h2>Do report</h2>%s</div>" % "".join(out)\n',
     '    body = head + "<div class=card><h2>Do report</h2>%s</div>" % "".join(out) + _s690_batchstock_card(S)    # S690\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build_one(rel, src_bytes, edits):
    if md5(src_bytes) != FROM[rel]:
        raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (rel, md5(src_bytes)[:8], FROM[rel][:8]))
    s = src_bytes.decode("utf-8")
    for i, (old, new) in enumerate(edits, 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: %s anchor %d occurs %d times (must be exactly once)" % (rel, i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, outdir = sys.argv[1], sys.argv[2]
    for rel, edits in (("finance/expiry_watch.py", EDITS_EW), ("finance/amir_day.py", EDITS_AD)):
        with open(os.path.join(root, rel), "rb") as fh:
            out = build_one(rel, fh.read(), edits)
        dst = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s %s -> %s (%d edits)" % (rel, FROM[rel][:8], md5(out)[:8], len(edits)))


if __name__ == "__main__":
    main()

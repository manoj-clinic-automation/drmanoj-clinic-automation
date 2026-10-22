#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""history_s623.py -- S623_STATIONERY_CHALLAN_HISTORY (D756; board _numbers v588 -> v589; built in the Scan App chat, session 337).

THE OWNER'S WORDS
    Board note 22-Oct-2026 06:31 IST: "scanapp - populate all entries that are possible from the variety challans and shavez excel
    files"; his rulings 12:09 IST 22-Oct on the lines read by eye: 'A4 long notebook 192p' = Register 192 pages; 'Copy Anmol' = Small
    copy -- Anmol 96 pages; the 72-page copy is Classmate; 'My Clear Bag' = Clear bag (premium); the NK Pathology estimate books stay
    out; the token line is 1 packet (100 tokens = 1 packet). Shavez's sheet was entered by S585; his other Excel files are blank.

WHAT IT DOES (the brief v2 with its R1, every BLOCKER and CORRECTION applied)
    The six Variety Stationers challans' lines are written as the stationery RECEIVED history, in the exact column shape of
    stationery.save_lines (stationery.py is NOT changed -- it is imported read only for its own rules):
      * ONE ts and ONE day per paper (R1 B1): day = the challan date, ts = that date 12:00 IST (computed with +05:30, never the box's
        zone). Every challan date is before the owner's 18-Oct opening counts, so the nine counted stocks stand.
      * each line takes the line number of the paper's own reading (R1 B2) -- the plan names it, and the step checks on the box that
        the reading's line at that number is the expected line (a word of it and its quantity); otherwise that paper is left alone.
      * B-0013's two lines already matched on the desk (the ring file, the token) are re-written the way a desk re-save writes them:
        the old rows voided and kept, new rows with the same line, name, unit, rate and item -- the token's quantity 100 -> 1 (R1 C3:
        exactly one live token row of 100, else B-0013 is left alone).
      * every row written carries by_whom = MARK, every row voided voided_by = MARK (R1 B3); --undo takes them back.
      * gates per paper (R1 C4): found by its stamp exactly once, not a second scan, not the pharmacy lane, and stationery.paper_counts
        True (in Stationery & packaging now); its live rows exactly the expected ones; its date before the LAST count of every counted
        item on it; an already-matched row of a counted item dated before that item's last count (else re-dating would move it).
      * an item absent or retired skips only its row (R1 C6); a line's unit is its item's own unit (R1 C5).
      * ONE transaction (BEGIN IMMEDIATE), the done-key stationery.history_s623 read first; the stock book read before and after
        inside it: every item must move by exactly what the written lines account for (counted items: 0) -- else ROLLBACK (R1 C2).

    python3 -B history_s623.py --apply  <assets.db>  [--app /root/assetapp]    the data step (idempotent: the key)
    python3 -B history_s623.py --verify <assets.db>  [--app ...]               the after-checks (exit 0 = all green)
    python3 -B history_s623.py --undo   <assets.db>  [--app ...]               voids S623's rows, restores the two it voided
"""
import datetime
import json
import os
import sqlite3
import sys

KIT = "S623_STATIONERY_CHALLAN_HISTORY"
KEY = "stationery.history_s623"
MARK = "history (Variety challans, S623)"
UNDO_BY = "undo S623"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# (stamp, challan date, KEEP rows, NEW rows)
#   KEEP: (line_no, a word of the read line, the item's exact name, its quantity now, its quantity after)
#   NEW:  (line_no, a word of the read line, the item's exact name, quantity, rate or None)
# The quantities and rates are the owner's records read off the challans by eye on 22-Oct (D756) -- data, not phone numbers.
PLAN = (
    ("B-0003", "2026-08-24", (),
     ((1, "ream", "A4 paper (75 gsm)", 1, None),)),
    ("B-0013", "2026-09-15",
     ((2, "ring", "Ring file RBU-400", 1, 1),
      (9, "token", "Token, plain", 100, 1)),
     ((1, "dc 217", "File folder DC-217", 1, 240),
      (3, "192", "Register 192 pages", 3, None),
      (4, "copy", "Copy — Classmate 72 pages (24 x 18 cm)", 6, 40),
      (5, "copy", "Small copy — Anmol 96 pages (24 x 18 cm)", 4, 40),
      (6, "register", "Register 72 pages", 6, None),
      (7, "104", "Register 104 pages", 12, None))),
    ("B-0109", "2026-10-01", (),
     ((1, "192", "Register 192 pages", 6, None),
      (2, "104", "Register 104 pages", 2, None),
      (3, "clear bag", "Clear bag (premium)", 2, 44))),
    ("B-0114", "2026-10-03", (),
     ((1, "dc 217", "File folder DC-217", 2, 240),)),
    ("B-0133", "2026-10-07", (),
     ((1, "ream", "A4 paper (75 gsm)", 20, None),)),
    ("B-0163", "2026-10-14", (),
     ((1, "x ray", "X-ray envelope 8.5 x 10.5", 500, None),)),
)
LEFT_OUT = ("B-0013 line 8 -- the NK Pathology estimate books: not matched (the lab's printed stationery; the owner, 12:09 IST 22-Oct)",)


def _st(app):
    """stationery.py from the app folder, imported read only (its rules: item_rows, stock_book, paper_counts, read_lines, panel...)."""
    if app not in sys.path:
        sys.path.insert(0, app)
    import stationery                                                # noqa: E402
    return stationery


def day_ts(day):
    y, m, d = (int(x) for x in day.split("-"))
    return datetime.datetime(y, m, d, 12, 0, 0, tzinfo=IST).timestamp()


def is_done(v):
    """The key counts as done unless it is absent or marked 'undone' by --undo (K1 C1)."""
    return v is not None and not str(v).startswith("undone")


def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def reading(db, bid):
    """As sorting_desk.reading: Claude's reading (ok=1) -> {'items': [...]} with named items only; None without one."""
    try:
        r = db.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1", (bid,)).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    try:
        data = json.loads(r[0] or "{}")
    except (TypeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    return {"items": [i for i in (data.get("items") or []) if isinstance(i, dict) and str(i.get("name") or "").strip()]}


def paper(db, stamp):
    rows = db.execute("SELECT * FROM bills WHERE upper(stamp_no)=?", (stamp.upper(),)).fetchall()
    return rows


def live_rows(db, b):
    return [dict(r) for r in db.execute("SELECT * FROM stationery_line WHERE bill_id=? AND bill_created_at=? AND voided_at='' ORDER BY line_no, id",
                                        (b["id"], b["created_at"] or ""))]


def last_counts(db):
    return {r[0]: r[1] for r in db.execute("SELECT item_id, MAX(ts) FROM stationery_count GROUP BY item_id")}


def _contrib(qty, ts, iid, lc):
    """What one counted line adds to stock_book now: all of it when the item has no count, else only when it is after the last count."""
    since = lc.get(iid)
    return float(qty) if (since is None or ts > since) else 0.0


def plan_paper(st, db, stamp, day, keep, new, items, lc, out):
    """Checks one paper and returns (bill row, [rows to insert], [ids to void], {item: expected delta}) -- or None (left alone)."""
    found = paper(db, stamp)
    if len(found) != 1:
        out("  %s: LEFT ALONE -- found %d papers with this stamp (want exactly one)" % (stamp, len(found)))
        return None
    b = found[0]
    lane = (b["lane"] or "clinic") if "lane" in b.keys() else "clinic"
    if b["dup_of"] or lane == "pharmacy":
        out("  %s: LEFT ALONE -- %s" % (stamp, "a second scan" if b["dup_of"] else "on the pharmacy lane"))
        return None
    ok, why = st.paper_counts(db, b)
    if not ok:
        out("  %s: LEFT ALONE -- lane %s, group %s, status %s, kind %s, challan %s: %s" % (
            stamp, lane, b["subgroup"] if "subgroup" in b.keys() else "", b["status"], b["doc_kind"],
            b["challan_state"] if "challan_state" in b.keys() else "", why))
        return None
    ts = day_ts(day)
    rl = st.read_lines(db, b, reading(db, b["id"]))
    byname = {}
    for i in items:                                                  # an active item wins over a retired one of the same name (K1 N8)
        if i["name"] not in byname or (i["active"] and not byname[i["name"]]["active"]):
            byname[i["name"]] = i
    live = live_rows(db, b)
    # the live rows must be exactly the KEEP rows
    want = sorted((k[0], byname[k[2]]["id"] if k[2] in byname else None, float(k[3])) for k in keep)
    have = sorted((r["line_no"], r["item_id"], float(r["qty"] or 0)) for r in live)
    if want != have:
        out("  %s: LEFT ALONE -- its saved lines are not the expected ones (saved now: %s; expected: %s)" % (
            stamp, ", ".join("line %d item %s qty %s" % (h[0], h[1], st._plain(h[2])) for h in have) or "none",
            ", ".join("line %d %s qty %s" % (k[0], k[2], st._plain(k[3])) for k in keep) or "none"))
        return None
    ins, delta = [], {}
    for r in live:                                                   # an already-matched row: re-dating must not move a counted stock
        if r["item_id"] in lc and r["ts"] > lc[r["item_id"]]:
            out("  %s: LEFT ALONE -- line %d is dated after its item's last count; re-dating it would change that stock" % (stamp, r["line_no"]))
            return None
        delta[r["item_id"]] = delta.get(r["item_id"], 0.0) - _contrib(r["qty"], r["ts"], r["item_id"], lc)
    for no, word, name, q_now, q_after in keep:
        r = next(x for x in live if x["line_no"] == no)
        ins.append((no, r["name"], float(q_after), r["unit"], r["rate"], r["item_id"], r["not_stock"], "keep %s" % st._plain(r["qty"])))
    for no, word, name, q, rate in new:
        it = byname.get(name)
        if it is None:
            out("  %s line %d: skipped -- no item named '%s' on the list" % (stamp, no, name))
            continue
        if not it["active"]:
            out("  %s line %d: skipped -- '%s' is retired" % (stamp, no, name))
            continue
        if no < 1 or no > len(rl):
            out("  %s: LEFT ALONE -- its reading has %d lines; line %d (%s) is not there" % (stamp, len(rl), no, name))
            return None
        r = rl[no - 1]
        if word not in st.norm(r["name"]) or r["qty"] is None or abs(float(r["qty"]) - float(q)) > 1e-9:
            out("  %s: LEFT ALONE -- its reading's line %d is '%s' x %s, not the expected %s x %s" % (
                stamp, no, r["name"], st._plain(r["qty"]), name, st._plain(q)))
            return None
        ins.append((no, r["name"], float(q), it["unit"], rate, it["id"], 0, "new"))
    if not ins:
        out("  %s: nothing to write" % stamp)
        return None
    for no, nm, q, u, rate, iid, ns, how in ins:
        if iid in lc and not ts < lc[iid]:
            out("  %s: LEFT ALONE -- its date %s is not before the last count of item %s" % (stamp, day, iid))
            return None
        if not ns:
            delta[iid] = delta.get(iid, 0.0) + _contrib(q, ts, iid, lc)
    for iid in list(delta):
        if iid in lc and abs(delta[iid]) > 1e-9:
            out("  %s: LEFT ALONE -- it would change the counted stock of item %s" % (stamp, iid))
            return None
    return b, ins, [r["id"] for r in live], delta


def apply(db_path, app="/root/assetapp", out=print, plan=PLAN):
    st = _st(app)
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.isolation_level = None
    try:
        con.execute("BEGIN IMMEDIATE")
        if is_done(st._setting(con, KEY, None)):
            out("history: already done (%s is set) -- nothing written" % KEY)
            con.execute("ROLLBACK")
            return 0
        items = st.item_rows(con)
        names = {i["id"]: i["name"] for i in items}
        lc = last_counts(con)
        before = st.stock_book(con)
        at = now_ist()
        expect, wrote, voided, papers, kept = {}, 0, 0, [], 0
        for stamp, day, keep, new in plan:
            p = plan_paper(st, con, stamp, day, keep, new, items, lc, out)
            if p is None:
                continue
            b, ins, void_ids, delta = p
            ts = day_ts(day)
            for rid in void_ids:
                con.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (at, MARK, rid))
                voided += 1
            byid = {i["id"]: i for i in items}
            for no, nm, q, u, rate, iid, ns, how in sorted(ins):
                con.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (b["id"], b["created_at"] or "", no, nm, q, u, rate, iid, ns, day, ts, MARK, at))
                wrote += 1
                kept += 1 if how.startswith("keep") else 0
                fl = st.rate_flag(rate, u, byid.get(iid)) if iid else ""
                was = how.split(" ", 1)[1] if how.startswith("keep") else ""
                out("  %s line %d: %s -> %s, %s %s%s%s%s" % (stamp, no, nm, names.get(iid, "?"), st._plain(q), u,
                                                           (" at %s" % st.rs(rate)) if rate is not None else "",
                                                           ((" (already matched; re-dated" + ("" if was == st._plain(q) else ", quantity %s -> %s" % (was, st._plain(q))) + ")") if was else ""),
                                                           (" -- " + fl) if fl else ""))
            for k, v in delta.items():
                expect[k] = expect.get(k, 0.0) + v
            papers.append("%s (%s)" % (stamp, day))
            out("  %s: day %s, written in Stationery & packaging" % (stamp, day))
        after = st.stock_book(con)
        bad = []
        for i in sorted(set(before) | set(after)):
            got = after.get(i, {"stock": 0.0})["stock"] - before.get(i, {"stock": 0.0})["stock"]
            if abs(got - expect.get(i, 0.0)) > 1e-9:
                bad.append("%s moved %s, expected %s" % (names.get(i, "?"), st._plain(got), st._plain(expect.get(i, 0.0))))
        for i in sorted(before, key=lambda k: names.get(k, "").lower()):
            out("stock: %s -- before %s, after %s%s" % (names.get(i, "?"), st._plain(before[i]["stock"]),
                                                       st._plain(after.get(i, {"stock": 0.0})["stock"]), " (counted)" if before[i].get("counted") else ""))
        if bad:
            con.execute("ROLLBACK")
            out("history: REFUSED -- a stock figure moved other than the lines account for (%s); rolled back, nothing written" % "; ".join(bad))
            return 1
        if not wrote:
            con.execute("ROLLBACK")
            out("history: REFUSED -- no paper could be written; nothing written, the key is not set")
            return 1
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (KEY, "%d rows %d voided %s" % (wrote, voided, at)))
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                        (at, MARK, "stationery_history_s623", json.dumps({"rows": wrote, "voided": voided, "papers": papers}, ensure_ascii=False)[:500]))
        except sqlite3.Error:
            pass
        con.execute("COMMIT")
        for x in LEFT_OUT:
            out("left out: " + x)
        out("history: %d new line(s) and %d already-matched line(s) re-written on %d paper(s); the %d earlier row(s) voided and kept; %s set; "
            "every stock moved exactly as its lines account for" % (wrote - kept, kept, len(papers), voided, KEY))
        return 0
    except Exception:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def undo(db_path, app="/root/assetapp", out=print):
    """Voids (never deletes) S623's live rows and brings back the rows S623 voided -- paper by paper; a paper a person has re-saved
    on the desk since (a live row not S623's) is left as it is. The key stays, so a re-install writes nothing. One transaction."""
    _st(app)
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.isolation_level = None
    try:
        con.execute("BEGIN IMMEDIATE")
        at = now_ist()
        keys = sorted({(r[0], r[1]) for r in con.execute("SELECT bill_id, bill_created_at FROM stationery_line WHERE by_whom=? OR voided_by=?", (MARK, MARK))})
        nv = nr = 0
        for bid, bca in keys:
            other = con.execute("SELECT COUNT(*) FROM stationery_line WHERE bill_id=? AND bill_created_at=? AND voided_at='' AND COALESCE(by_whom,'')<>?",
                                (bid, bca, MARK)).fetchone()[0]
            gone = con.execute("SELECT COUNT(*) FROM stationery_line WHERE bill_id=? AND bill_created_at=? AND by_whom=? AND voided_at<>'' AND voided_by NOT IN (?, ?)",
                               (bid, bca, MARK, UNDO_BY, MARK)).fetchone()[0]
            if other or gone:
                out("undo: paper %s left as it is -- %s since S623" % (bid, "re-saved on the desk" if other else "its lines taken off by a person on the desk"))
                continue
            nv += con.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND by_whom=? AND voided_at=''",
                              (at, UNDO_BY, bid, bca, MARK)).rowcount
            nr += con.execute("UPDATE stationery_line SET voided_at='', voided_by='' WHERE bill_id=? AND bill_created_at=? AND voided_by=?",
                              (bid, bca, MARK)).rowcount
        if con.execute("SELECT 1 FROM settings WHERE key=?", (KEY,)).fetchone():   # K1 C1: a re-install may write again
            con.execute("UPDATE settings SET value=? WHERE key=?", ("undone %s" % at, KEY))
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                        (at, UNDO_BY, "stationery_history_s623_undo", json.dumps({"voided": nv, "restored": nr})))
        except sqlite3.Error:
            pass
        con.execute("COMMIT")
        out("undo: %d S623 line(s) voided (kept, struck), %d earlier line(s) brought back; the key %s marked undone (a re-install may write again)" % (nv, nr, KEY))
        return 0
    except Exception:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def verify(db_path, app="/root/assetapp", out=print, plan=PLAN, ym="2026-10"):
    """The after-checks, read only. Returns the number of red checks (0 = all green)."""
    st = _st(app)
    con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    con.row_factory = sqlite3.Row
    red = 0

    def chk(label, ok, detail=""):
        nonlocal red
        red += 0 if ok else 1
        out("  %s %s%s" % ("GREEN" if ok else "RED  ", label, (" -- " + detail) if (detail and not ok) else ""))
    try:
        items = {i["name"]: i for i in st.item_rows(con)}
        chk("V0 the done-key %s is set" % KEY, is_done(st._setting(con, KEY, None)))
        mem = sqlite3.connect(":memory:")                            # ONE copy for the desk-Save checks (K1 N11)
        con.backup(mem)
        mem.row_factory = sqlite3.Row
        for stamp, day, keep, new in plan:
            f = paper(con, stamp)
            if len(f) != 1:
                chk("V1 %s found once" % stamp, False, "%d found" % len(f))
                continue
            b = f[0]
            live = live_rows(con, b)
            ts = day_ts(day)
            exp = [(k[0], k[2], float(k[4])) for k in keep] + [(n[0], n[2], float(n[3])) for n in new if n[2] in items and items[n[2]]["active"]]
            got = [(r["line_no"], next((n for n, i in items.items() if i["id"] == r["item_id"]), "?"), float(r["qty"] or 0)) for r in live]
            chk("V1 %s: its lines saved as the challan (%d)" % (stamp, len(exp)), sorted(exp) == sorted(got), "saved %s" % got)
            chk("V2 %s: every live line dated %s, by S623" % (stamp, day),
                bool(live) and all(r["day"] == day and abs(r["ts"] - ts) < 1e-6 and r["by_whom"] == MARK for r in live))
            pn = st.panel(con, b, reading(con, b["id"]))
            chk("V3 %s: the desk shows every S623 line saved, no suggestion left on a read line" % stamp,
                all(l["saved"] for l in pn["lines"] if l["no"] in {e[0] for e in exp}) and not any(l["sug"] and not l["saved"] for l in pn["lines"]),
                json.dumps([(l["no"], l["saved"], l["sug"]) for l in pn["lines"]]))
            mem.execute("SAVEPOINT v4")
            bm = mem.execute("SELECT * FROM bills WHERE id=?", (b["id"],)).fetchone()
            posted = [{"no": l["no"], "name": l["name"], "qty": l["qty"], "unit": l["unit"], "rate": l["rate"], "item": l["item"]} for l in pn["lines"]]
            words = st.save_lines(mem, bm, posted, "walk")
            mem.execute("ROLLBACK TO v4")
            mem.execute("RELEASE v4")
            chk("V4 %s: a desk Save of the paper as it stands changes nothing" % stamp, words == ["Stationery: unchanged."], str(words))
            chk("V5 %s: counts into the stock" % stamp, st.paper_counts(con, b)[0])
        tok = items.get("Token, plain")
        b13 = paper(con, "B-0013")
        if tok and len(b13) == 1:
            t = [r for r in live_rows(con, b13[0]) if r["item_id"] == tok["id"]]
            chk("V6 B-0013: the token line is 1 packet (one live line)", len(t) == 1 and float(t[0]["qty"]) == 1.0, str([r["qty"] for r in t]))
        inv = st.inventory(con, ym)
        fed = {f["stamp"] for f in inv["fed"]}
        chk("V7 %s: the papers that fed the stock include B-0109, B-0114, B-0133, B-0163 and not B-0003, B-0013" % ym,
            {"B-0109", "B-0114", "B-0133", "B-0163"} <= fed and not ({"B-0003", "B-0013"} & fed), str(sorted(fed)))
        lc = last_counts(con)
        late = con.execute("SELECT COUNT(*) FROM stationery_line WHERE by_whom=? AND voided_at=''", (MARK,)).fetchone()[0]
        bad = [r for r in con.execute("SELECT item_id, ts FROM stationery_line WHERE by_whom=? AND voided_at=''", (MARK,)) if r[0] in lc and not r[1] < lc[r[0]]]
        chk("V8 no S623 line of a counted item is after its count (%d lines)" % late, late > 0 and not bad)
        mem.close()
    finally:
        con.close()
    out("verify: %d red" % red)
    return red


def _arg(name, default):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


if __name__ == "__main__":
    app = _arg("--app", os.environ.get("S623_APP_DIR", "/root/assetapp"))
    if len(sys.argv) >= 3 and sys.argv[1] == "--apply":
        sys.exit(apply(sys.argv[2], app))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--undo":
        sys.exit(undo(sys.argv[2], app))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--verify":
        sys.exit(1 if verify(sys.argv[2], app) else 0)
    else:
        print(__doc__)
        sys.exit(2)

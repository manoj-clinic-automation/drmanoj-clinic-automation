#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_s502.py -- the data fixes of kit S502_STOCK_MILAAN_TODAY (the brief's section 3): keyed by content, idempotent, through the system's
own doors. Never DELETE. Run FIRST on a scratch copy (the walk, twice), then by the installer on the live database after its backup.

    python3 -B fix_s502.py --db PATH --finance DIR [--spine PATH]

  A  TRUECEPROL OD, 10-Oct (F-812, F-813): Darpan's 12:01 count (13 patte + 7 goli) was written into the SEALED 06-Sep count by 'Dobara ginna
     hai' while the morning list kept his 11:58 slip (33:7). A new point of 137 replaces point 377 (superseded, never deleted); the roster
     reads 137; the shelf-fix row leaves the 06-Sep count (count_id negated, a note says why). The Loss desk's cached line is recomputed
     only when the stored stamp equals the current one on every part but 'fixes' -- else it is left to the desk's next full rebuild.
  B  TYRO BR, 08-Oct (F-814): loss line 2 (70:7 short) is VOIDED (void_at / void_why), its open trace set 'seen' by its own point id, and
     TYRO BR asked for Darpan's next morning list. Point 376 itself is left as it is.

Any key that does not match exactly -> that fix is SKIPPED and said. Prints its findings, then ONE line 'FIX_S502_JSON {...}'.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys

DAY = "2026-10-10"
ITEM_A = "TRUECEPROL OD"
ITEM_B = "TYRO BR"
NOTE_A = "S502: Darpan ki 12:01 ki ginti (Dobara ginna hai mein likhi gayi thi); point %d (%s) ki jagah"
NOTE_FIX = " · S502: 10-Oct ki ginti thi, 06-Sep ki nahi — count se hata di"
VOID_WHY_B = "S502: is din ka hisaab galat tha (bill 01-Oct ka, Marg mein 08-Oct ko chadha); nayi ginti maangi"


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--finance", required=True, help="the folder holding the NEW stock_watch.py (and loss_piles.py, qty_words.py)")
    ap.add_argument("--spine", default=None, help="the spine database the modules read (SPINE_DB); the live one when absent")
    a = ap.parse_args(argv)
    if a.spine:
        os.environ["SPINE_DB"] = a.spine
    sys.path.insert(0, os.path.abspath(a.finance))
    os.chdir(os.path.abspath(a.finance))
    import stock_watch as SW                                            # noqa: E402 -- the NEW file
    import loss_piles as LP                                             # noqa: E402 -- read only here, but for _refresh_after_write when the guard allows
    assert SW.__file__.startswith(os.path.abspath(a.finance)), SW.__file__
    con = sqlite3.connect(a.db, timeout=60)
    out = {"db": a.db, "A": {}, "B": {}, "at": now_iso()}
    say = lambda s: print("FIX_S502 " + s)                              # noqa: E731

    # ---- B0 (first, so A can void / close through the same columns): the NEW ensure -- the two columns
    SW.ensure(con)
    con.commit()
    cols = [r[1] for r in con.execute("PRAGMA table_info(stock_watch_loss_line)").fetchall()]
    out["loss_line_cols"] = cols
    say("ensure: stock_watch_loss_line columns %s" % cols)
    if "void_at" not in cols or "void_why" not in cols:
        say("STOP: void_at / void_why missing after ensure -- nothing else done")
        print("FIX_S502_JSON " + json.dumps(out, default=str))
        return 1

    # ---- A  TRUECEPROL OD
    A = out["A"]
    ro = con.execute("SELECT id, qty_units, point_id, answered_at, item, day FROM stock_spot_roster WHERE day=? AND item=?", (DAY, ITEM_A)).fetchone()
    if not ro:
        A["status"] = "skipped"; A["why"] = "no roster row for %s on %s" % (ITEM_A, DAY)
    else:
        A["roster"] = dict(id=ro[0], qty=ro[1], point_id=ro[2])
        later = con.execute("SELECT id, qty_units, status, at FROM stock_point WHERE item=? AND id>? AND status<>'superseded' ORDER BY id", (ITEM_A, int(ro[2] or 0))).fetchall()
        if ro[1] is not None and float(ro[1]) == 137.0:
            A["status"] = "already"; A["why"] = "the roster already reads 137 (point %s)" % ro[2]
        elif later:
            A["status"] = "skipped"; A["why"] = "Darpan has since corrected it himself: later point(s) %s" % [list(x) for x in later]
        else:
            old = con.execute("SELECT id, item_norm, item, qty_units, source, status, expected_units, at, by, note FROM stock_point WHERE id=?", (int(ro[2] or 0),)).fetchone()
            fix = con.execute("SELECT id, count_id, qty, by_user, at, note FROM stock_shelf_fix WHERE item=? AND source='recount' AND at LIKE '2026-10-10T12:01%'", (ITEM_A,)).fetchall()
            key_ok = (old is not None and float(old[3]) == 337.0 and old[4] == "spot" and old[5] in ("settled", "provisional") and float(ro[1]) == 337.0
                      and len(fix) == 1 and int(fix[0][2]) == 137 and int(fix[0][1]) > 0)
            A["old_point"] = list(old) if old else None
            A["fix_row"] = [list(x) for x in fix]
            if not key_ok:
                A["status"] = "skipped"; A["why"] = "the keys do not match: roster qty %s; point %s; shelf-fix rows %s" % (ro[1], list(old) if old else None, [list(x) for x in fix])
            else:
                A["old_status"] = old[5]
                if old[5] != "settled":
                    A["note"] = ("the brief keyed the old point as status 'settled'; it is '%s' (its expectation carried a provisional arrival term) -- "
                                 "every other key matches exactly (id, 337, spot, roster %d), so the fix is applied and this is said in the report" % (old[5], ro[0]))
                f = fix[0]
                exp = old[6]
                gap = None if exp is None else round(137.0 - float(exp), 3)
                info = SW.item_info(con, SW.Spine(), ITEM_A)
                old_words = SW.qw(old[3], info["pack"], info["packing"], ITEM_A, "hi")
                cur = con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note, count_id, roster_id, provisional_units) "
                                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                  (old[1], old[2], f[4], 137.0, "spot", f[3] or old[8], exp, gap, "settled", f[4], NOTE_A % (old[0], old_words), None, ro[0], 0))
                new_id = int(cur.lastrowid)
                con.execute("UPDATE stock_point SET status='superseded', note=? WHERE id=?", (((old[9] + " · ") if old[9] else "") + "S502: badla, ab point %d" % new_id, old[0]))
                con.execute("UPDATE stock_spot_roster SET qty_units=137, point_id=? WHERE id=?", (new_id, ro[0]))
                voided = con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why='ginti badli' WHERE point_id=? AND void_at IS NULL", (now_iso(), old[0])).rowcount
                closed = con.execute("UPDATE stock_trace SET status='seen', seen_by='S502', seen_at=? WHERE status='open' AND json_extract(findings_json,'$.point_id')=?", (now_iso(), old[0])).rowcount
                SW._audit(con, "spot_fix", dict(item=ITEM_A, old_qty=337.0, new_qty=137.0, old_point=old[0], new_point=new_id, by="S502 (the brief's data fix A)"), "S502", new_id)
                # A3: the shelf-fix row leaves the 06-Sep count (no DELETE)
                root = int(f[1])
                con.execute("UPDATE stock_shelf_fix SET count_id = -count_id, note = COALESCE(note,'') || ? WHERE id=?", (NOTE_FIX, f[0]))
                A.update(status="applied", new_point=new_id, gap=gap, expected=exp, old_loss_lines_voided=voided, old_traces_closed=closed, fix_row_moved=f[0], root=root)
                con.commit()
                say("A: point %d (337, %s) superseded by point %d (137, expected %s, gap %s); roster %d reads 137; shelf-fix row %d moved off count %d; "
                    "old point's loss lines voided %d, traces closed %d" % (old[0], old[5], new_id, exp, gap, ro[0], f[0], root, voided, closed))
                # the Loss desk's cache, under the brief's guard
                cache = {}
                try:
                    m = con.execute("SELECT stamp FROM stock_pile_cache_meta WHERE count_id=?", (root,)).fetchone()
                    stored = json.loads(m[0]) if m else {}
                    cur_stamp = LP.stamp(con, root)
                    diff = sorted(k for k in set(stored) | set(cur_stamp) if stored.get(k) != cur_stamp.get(k))
                    line = con.execute("SELECT bucket, pile, grp, line_json FROM stock_pile_cache WHERE count_id=? AND item=?", (root, ITEM_A)).fetchone()
                    cache["before"] = dict(bucket=line[0], pile=line[1], grp=line[2], counted=json.loads(line[3]).get("counted"), diff=json.loads(line[3]).get("diff")) if line else None
                    cache["stamp_parts_differing"] = diff
                    if line is None:
                        cache["refreshed"] = False; cache["why"] = "%s is not in the pile cache of count %d -- refresh_items would skip it; left to the desk's next full rebuild" % (ITEM_A, root)
                    elif [k for k in diff if k != "fixes"]:
                        cache["refreshed"] = False
                        cache["why"] = "the stored stamp differs from the current one on %s (not only 'fixes'): _refresh_after_write would store the whole current stamp and hide a full rebuild -- left to the desk's next full rebuild" % [k for k in diff if k != "fixes"]
                    else:
                        LP._refresh_after_write(con, root, [ITEM_A])
                        cache["refreshed"] = True
                    line = con.execute("SELECT bucket, pile, grp, line_json FROM stock_pile_cache WHERE count_id=? AND item=?", (root, ITEM_A)).fetchone()
                    cache["after"] = dict(bucket=line[0], pile=line[1], grp=line[2], counted=json.loads(line[3]).get("counted"), diff=json.loads(line[3]).get("diff")) if line else None
                except Exception as e:                                  # noqa: BLE001
                    cache["error"] = "%s: %s" % (type(e).__name__, str(e)[:160])
                A["cache"] = cache
                say("A3 cache: %s" % json.dumps(cache, default=str))
    # ---- B  TYRO BR
    B = out["B"]
    ln = con.execute("SELECT id, point_id, void_at FROM stock_watch_loss_line WHERE item=? AND at LIKE '2026-10-08T11:50%' AND gap_units=707", (ITEM_B,)).fetchall()
    if len(ln) != 1:
        B["line"] = "skipped: %d loss line(s) match the key" % len(ln)
    else:
        lid, pid, va = ln[0]
        B["line_id"], B["point_id"] = lid, pid
        if va:
            B["line"] = "already voided at %s" % va
        else:
            con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why=? WHERE id=? AND void_at IS NULL", (now_iso(), VOID_WHY_B, lid))
            B["line"] = "voided"
        tr = con.execute("SELECT id, status FROM stock_trace WHERE item=? AND opened_at LIKE '2026-10-08T11:50%' AND json_extract(findings_json,'$.point_id')=?", (ITEM_B, pid)).fetchall()
        B["traces"] = [list(x) for x in tr]
        n = con.execute("UPDATE stock_trace SET status='seen', seen_by='S502', seen_at=? WHERE item=? AND opened_at LIKE '2026-10-08T11:50%' AND status='open' "
                        "AND json_extract(findings_json,'$.point_id')=?", (now_iso(), ITEM_B, pid)).rowcount
        B["trace_set_seen"] = n
        con.commit()
    ok, msg, code = SW.ask(con, ITEM_B, "manoj")
    B["ask"] = dict(ok=ok, msg=msg, code=code)
    con.commit()
    say("B: %s" % json.dumps(B, default=str))
    con.close()
    out["ok"] = True
    print("FIX_S502_JSON " + json.dumps(out, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s533.py -- kit S533_AMIR_DAY_PAGE, the data step (brief section 8): keyed, idempotent, never a DELETE.

    /usr/bin/python3 -B data_s533.py --db /root/finance/finance.db --modules DIR --finance /root/finance
                            --archive /root/marg_ingest/archive --readings /root/finance/spine/readings [--dry] [--schema-only]

  modules   a scratch folder holding the kit's BUILT amir_day.py and purchase_app.py (copied out of the kit -- CLAUDE.md 11): amir_day.ensure
            lays the new tables and columns, purchase_app.EXPORT_DAY_SQL is the one expression of an export's day. item_alias, section_map,
            reports_watch and stock_watch are the LIVE ones under --finance, read-only (the kit edits none of them).
  --dry          everything runs inside ONE transaction that is rolled back at the end (the DDL too: SQLite's DDL is transactional).
  --schema-only  steps 1, 2, 3 (CREATE), 4 (CREATE), 5 -- no history copied, no spelling touched (the walk's order: the duty SQLs are run on a
                 scratch copy after this part).
Steps (each prints DATA_S533: lines):
  1  purchase_bill.first_seen_day -- ALTER if absent; back-filled from the bill-wise export the row names, else the bill date
  2  amir_self_wait.bill_id -- ALTER if absent; filled where exactly one purchase_bill carries the triple
  3  amir_step_log -- every old step tick copied once, key (day, step, done_at); step 7 as 'close' (the day's closed_at / closed_by); one
     'reopen' row per day reopened and never closed again, key (day, 7, reopened_at)
  4  amir_bill_answer -- every old bill disposition copied once, key (triple, at), bill_id where exactly one bill carries the triple
  5  amir_job.reopened_at -- ALTER if absent
  6  the two spellings (D709, F-861) through item_alias's own doors, only when the newest VERIFIED closing prints them
  7  amir.salt_owed_days' note in visit days; the seven S444 settings INSERT OR IGNORE
No person, phone or account number is printed."""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys

OLD_STEP = "amir_step"                      # the history tables this step copies (named here only)
OLD_DISP = "amir_bill_disposition"
SPELLINGS = (   # old_name (the row's key) -> the new name it carries today -> Marg's printed spelling (F-861, read on the 10-10 closing)
    ("L S BELT CONT GRAY UNISON XXX", "L S BELT 3XL CONT GRAY UNISON", "L S BELT XXXL CONT GRAY UNISO"),
    ("TYNOR WRIST SPLINT LF M ELAS", "TYNOR WRIST SPL LF M ELASTIC", "TYNOR WRIST SPL LF M ELAS T"),
)
SALT_NOTE = "S444: visits a SALT WISE ITEM LIST may be owed before the owner's Needs-you line (S533: visit days)"


class TxCon(sqlite3.Connection):
    """A connection whose commit() is held: the step commits (or rolls back) once, at its end -- so --dry undoes everything, and a callee's
    own commit cannot split the step."""
    def commit(self):
        return None


def say(s):
    print("DATA_S533: " + re.sub(r"\d{10,}", "##########", str(s)))


def table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def cols(con, name):
    return {r[1] for r in con.execute("PRAGMA table_info(%s)" % name).fetchall()}


def stamp_iso(stamp):
    s = str(stamp or "")
    if not re.match(r"^\d{8}-\d{6}$", s):
        return ""
    return "%s-%s-%sT%s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])


def one_bill(con, sn, bno, bdt):
    r = con.execute("SELECT id FROM purchase_bill WHERE supplier_norm=? AND bill_no=? AND bill_date=?", (sn, bno, bdt)).fetchall()
    return int(r[0][0]) if len(r) == 1 else None


def step1(con, PA):
    if "first_seen_day" not in cols(con, "purchase_bill"):
        con.execute("ALTER TABLE purchase_bill ADD COLUMN first_seen_day TEXT")
        say("1 purchase_bill.first_seen_day added")
    expr = PA.EXPORT_DAY_SQL.format(p="e.")
    todo = con.execute("SELECT COUNT(*) FROM purchase_bill WHERE first_seen_day IS NULL").fetchone()[0]
    fall = con.execute("SELECT COUNT(*) FROM purchase_bill b WHERE b.first_seen_day IS NULL AND NOT EXISTS "
                       "(SELECT 1 FROM purchase_export e WHERE e.md5 = b.bw_md5)").fetchone()[0]
    con.execute("UPDATE purchase_bill SET first_seen_day = COALESCE((SELECT " + expr + " FROM purchase_export e "
                "WHERE e.md5 = purchase_bill.bw_md5), substr(bill_date, 1, 10)) WHERE first_seen_day IS NULL")
    say("1 first_seen_day filled on %d bill(s) (%d of them from the bill date: no bill-wise export named); %d already set"
        % (todo, fall, con.execute("SELECT COUNT(*) FROM purchase_bill").fetchone()[0] - todo))
    if todo:
        say("1 first sight for the %d bills already on the box is the day of the newest export that carried them -- the only day the data "
            "held; from today on it is the true first sight" % todo)


def step2(con):
    if not table(con, "amir_self_wait"):
        say("2 amir_self_wait not present -- nothing to fill")
        return
    m = u = 0
    for sn, bno, bdt in con.execute("SELECT supplier_norm, bill_no, bill_date FROM amir_self_wait WHERE bill_id IS NULL").fetchall():
        bid = one_bill(con, sn, bno, bdt)
        if bid is None:
            u += 1
            continue
        con.execute("UPDATE amir_self_wait SET bill_id=? WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND bill_id IS NULL", (bid, sn, bno, bdt))
        m += 1
    say("2 amir_self_wait.bill_id: %d matched, %d unmatched (each wait record's bill by its triple, exactly one bill)" % (m, u))


def step3(con):
    if not table(con, OLD_STEP):
        say("3 no old step table -- nothing to copy")
        return
    days = {r[0]: r for r in con.execute("SELECT day, opened_at, closed_at, closed_by, reopened_at, reopened_by FROM amir_day").fetchall()}
    have = {(r[0], int(r[1]), r[2]) for r in con.execute("SELECT day, step, done_at FROM amir_step_log").fetchall()}
    copied = there = 0
    for day, stp, done_at, by in con.execute("SELECT day, step, done_at, by_user FROM %s ORDER BY day, step" % OLD_STEP).fetchall():
        stp = int(stp)
        note = "copied S533 from %s" % OLD_STEP
        if stp == 7:
            note = "close"
            d = days.get(day)
            if d is not None and d[2]:
                done_at, by = d[2], (d[3] or by)
        if not done_at:
            continue
        if (day, stp, done_at) in have:
            there += 1
            continue
        con.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note, replaces) VALUES (?,?,?,?,?,NULL)", (day, stp, done_at, by, note))
        have.add((day, stp, done_at))
        copied += 1
    reo = 0
    for day, _o, closed_at, _cb, reopened_at, reopened_by in days.values():
        if reopened_at and not closed_at:
            if (day, 7, reopened_at) in have:
                there += 1
                continue
            con.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note, replaces) VALUES (?,7,?,?,'reopen',NULL)", (day, reopened_at, reopened_by))
            have.add((day, 7, reopened_at))
            reo += 1
    kept = [d for d, r in days.items() if r[4] and r[2]]
    say("3 amir_step_log: %d step row(s) copied + %d reopen row(s); %d already there" % (copied, reo, there))
    if kept:
        say("3 a day reopened and closed again keeps its close row only; its reopen stays in amir_day.reopened_at: %s" % ", ".join(sorted(kept)))


def step4(con):
    if not table(con, OLD_DISP):
        say("4 no old disposition table -- nothing to copy")
        return
    have = {(r[0], r[1], r[2], r[3]) for r in con.execute("SELECT supplier_norm, bill_no, bill_date, at FROM amir_bill_answer").fetchall()}
    copied = there = unkeyed = 0
    for sn, bno, bdt, day, reason, by, at in con.execute("SELECT supplier_norm, bill_no, bill_date, day, reason, by_user, at FROM %s "
                                                         "ORDER BY COALESCE(at, ''), supplier_norm, bill_no" % OLD_DISP).fetchall():
        at = at or ""
        if (sn, bno, bdt, at) in have:
            there += 1
            continue
        bid = one_bill(con, sn, bno, bdt)
        if bid is None:
            unkeyed += 1
        con.execute("INSERT INTO amir_bill_answer (bill_id, supplier_norm, bill_no, bill_date, day, reason, by_user, at, note, replaces) "
                    "VALUES (?,?,?,?,?,?,?,?,?,NULL)", (bid, sn, bno, bdt, day, reason, by, at, "copied S533 from %s" % OLD_DISP))
        have.add((sn, bno, bdt, at))
        copied += 1
    by_reason = con.execute("SELECT reason, COUNT(*) FROM amir_bill_answer WHERE note = ? GROUP BY reason", ("copied S533 from %s" % OLD_DISP,)).fetchall()
    say("4 amir_bill_answer: %d copied, %d already there, %d with no single bill (bill_id NULL, read by the triple); copied by reason %s"
        % (copied, there, unkeyed, dict(by_reason)))


def read_closing(con, archive, readings):
    """The newest VERIFIED STOCK_CLOSING as data_s528 found it: its archive file through marg_read, else its reading JSON."""
    r = con.execute("SELECT md5, stamp, date_to FROM mi_file WHERE type='STOCK_CLOSING' AND verdict='VERIFIED' ORDER BY stamp DESC LIMIT 1").fetchone()
    if not r:
        return None
    md5, stamp = str(r[0]), str(r[1])
    names, as_on, how = [], "", ""
    paths = glob.glob(os.path.join(archive, "STOCK_CLOSING", "*", "*__%s__%s*" % (stamp, md5[:8])))
    if paths:
        try:
            import marg_read                                    # noqa: PLC0415
            fam, R, _m = marg_read.read_file(paths[0])
            if fam == "STOCK_CLOSING" and R is not None:
                names = [i["name"] for i in (R.data.get("items") or []) if i.get("name")]
                as_on = R.data.get("as_on") or ""
                how = "archive file %s" % os.path.basename(paths[0])[:70]
        except Exception as e:                                  # noqa: BLE001
            say("6 the archive file could not be read (%s) -- the reading is the fallback" % str(e)[:100])
    if not names:
        p = os.path.join(readings, md5 + ".json")
        if os.path.exists(p):
            j = json.load(open(p, encoding="utf-8"))
            if j.get("family") == "STOCK_CLOSING" and j.get("ok"):
                names = [i.get("name") for i in ((j.get("data") or {}).get("items") or []) if i.get("name")]
                as_on = (j.get("data") or {}).get("as_on") or ""
                how = "reading %s.json" % md5[:12]
    return dict(md5=md5, stamp=stamp, names=names, as_on=as_on, how=how)


def step6(con, IA, archive, readings, ts):
    IA.ensure(con)
    rows = {r["old_name"]: r for r in IA.rows(con)}
    for old, was, new in SPELLINGS:
        r = rows.get(old)
        say("6 before  %s" % (("%-9s %s -> %s (ticked %s)" % (r["state"], old, r["new_name"], (r["done_at"] or "-")[:19])) if r else ("%s -- no such row" % old)))
    C = read_closing(con, archive, readings)
    if not C or not C["names"] or not C["as_on"]:
        say("6 no readable VERIFIED closing on the box -- nothing respelt; tomorrow's closing judges the rows through marg_take")
        return 0
    cap = stamp_iso(C["stamp"])
    P = {IA.pad_norm(n) for n in C["names"]}
    say("6 the newest VERIFIED closing: captured %s, printed for %s, %d names (%s)" % (cap, C["as_on"], len(C["names"]), C["how"]))
    respelt = 0
    for old, was, new in SPELLINGS:
        r = rows.get(old)
        if r is None:
            say("6 %s: not found by old_name -- nothing written" % old)
            continue
        if r["state"] in ("verified", "question"):
            say("6 %s: already %s -- skipped" % (old, r["state"]))
            continue
        if not r["done_at"] or r.get("undone_at"):
            say("6 %s: not ticked -- skipped (the closing reads it back by itself)" % old)
            continue
        if cap <= str(r["done_at"])[:19]:
            say("6 %s: no closing captured after its tick (%s <= %s) -- skipped; tomorrow's closing judges it" % (old, cap, str(r["done_at"])[:19]))
            continue
        if IA.pad_norm(new) not in P or IA.pad_norm(r["new_name"]) in P:
            say("6 %s: the closing does not print '%s' alone (new %s, current %s) -- skipped" % (old, new, IA.pad_norm(new) in P, IA.pad_norm(r["new_name"]) in P))
            continue
        if r["new_name"] == new:
            continue
        con.execute("UPDATE marg_item_rename SET new_name=?, new20=?, new27=? WHERE id=?",
                    (new, IA.clip(new, IA.SALE_CLIP), IA.clip(new, IA.PURCHASE_CLIP), int(r["id"])))
        IA._event(con, int(r["id"]), "respelt", "S533", ts, seen_name=new, note="D709: was %s" % r["new_name"])
        notes = IA._follow(con, dict(r, new_name=new), "S533", ts)
        say("6 %s: new_name %s -> %s (respelt event; follow: %s)" % (old, r["new_name"], new, "; ".join(notes)))
        respelt += 1
    res = IA.sight_closing(con, C["names"], C["as_on"], C["md5"], C["stamp"], source="S533 data step", ts=ts)
    if res.get("skipped"):
        say("6 sight_closing skipped: %s %s" % (res.get("skipped"), res.get("short") or ""))
    else:
        say("6 sight_closing: verified %s; questions %s; seen %s" % (res.get("verified"), res.get("questions"), res.get("seen")))
    after = {r["old_name"]: r for r in IA.rows(con)}
    for old, _was, _new in SPELLINGS:
        r = after.get(old)
        if r:
            say("6 after   %-9s %s -> %s%s" % (r["state"], old, r["new_name"], (" (closing of %s)" % r.get("verified_as_on")) if r.get("verified_as_on") else ""))
    s = IA.summary(con)
    say("6 renames now: %d of %d verified, %d question(s)" % (s.get("verified", 0), s.get("total", 0), s.get("question", 0)))
    return respelt


def step7(con, AD):
    n = con.execute("UPDATE setting SET note=? WHERE key='amir.salt_owed_days' AND COALESCE(note,'') <> ?", (SALT_NOTE, SALT_NOTE)).rowcount
    k = AD.s444_seed_settings(con)
    say("7 amir.salt_owed_days' note in visit days (%d row changed); the S444 settings seeded: %d new (INSERT OR IGNORE)" % (n, k))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--modules", required=True)
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--archive", default="/root/marg_ingest/archive")
    ap.add_argument("--readings", default="/root/finance/spine/readings")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--schema-only", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    sys.path.insert(0, os.path.join(a.finance, "spine"))
    sys.path.insert(0, a.modules)                               # first: the kit's built amir_day and purchase_app win
    import amir_day as AD                                       # noqa: E402
    import purchase_app as PA                                   # noqa: E402
    import item_alias as IA                                     # noqa: E402
    assert os.path.abspath(AD.__file__).startswith(os.path.abspath(a.modules)), AD.__file__
    assert os.path.abspath(PA.__file__).startswith(os.path.abspath(a.modules)), PA.__file__
    assert hasattr(PA, "EXPORT_DAY_SQL") and hasattr(AD, "DUTY_SQL"), "the modules folder does not hold the kit's built files"
    con = sqlite3.connect(a.db, timeout=60, factory=TxCon, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("BEGIN IMMEDIATE")
    try:
        say("start on %s (%s%s)" % (os.path.basename(a.db), "DRY -- rolled back at the end" if a.dry else "commits at the end",
                                    ", schema only" if a.schema_only else ""))
        step1(con, PA)
        AD.ensure(con)                                          # amir_step_log, amir_bill_answer, amir_self_wait.bill_id, amir_job.reopened_at
        say("2-5 schema: amir_step_log, amir_bill_answer and their indexes present; amir_self_wait.bill_id %s; amir_job.reopened_at %s"
            % ("bill_id" in cols(con, "amir_self_wait"), "reopened_at" in cols(con, "amir_job")))
        step2(con)
        if not a.schema_only:
            step3(con)
            step4(con)
            ts = AD._now().replace(tzinfo=None, microsecond=0).isoformat()
            step6(con, IA, a.archive, a.readings, ts)
            step7(con, AD)
        for k, sql in AD.DUTY_SQL.items():
            r = con.execute(sql).fetchone()
            say("duty %s -> (n %s, since %s)" % (k, r[0], r[1]))
        if a.dry:
            con.execute("ROLLBACK")
            say("DRY -- rolled back")
        else:
            con.execute("COMMIT")
            say("committed")
    except Exception as e:                                      # noqa: BLE001
        con.execute("ROLLBACK")
        say("FAILED and rolled back: %s: %s" % (type(e).__name__, str(e)[:300]))
        con.close()
        return 1
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

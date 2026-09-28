#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s436.py -- kit S436_STAFF_PAGES_CLEAN (D638). The owner's rulings of 28-Sep as DATA, on the live database after a green restart
(and on the walk's scratch copy first), each write audited and idempotent:
  3.1  every OPEN orthotic short line Darpan answered ('does not know' / 'broken or damaged') -> BILLING (sold, no bill was made), his name
       kept, the rule in the note; the two he has not answered -> BILLING by default ("rule D638 default -- Darpan ne nahi likha", tappable
       for him); the open extra lines with 'does not know' -> BILLED_NOT_GIVEN. Audit: stock_diff / cause_rule, by "rule D638, 28-Sep".
  3.2  stockmatch.close_by_rule(): the orthotic loss at selling price (one run, kind ortho_close), the lane words, the orthotic voucher
       round, the Needs-you line, the section-close row.
  3.3  the wrong-salt pairs: ETOZOX 90 <-> PARI CR 12.5, LACTOVAX SYP <-> LINVIZ 600, LACTOVAX SYP <-> FEBUTAL -> NO with the note
       "not a swap -- salt wrong in Marg" (a new stock_match row each, the newest wins; the answers were already NO).
  3.4a the four salt fixes -> purchase_salt_task, section 'change' (Item ka salt badliye), source 'S436-owner-28-Sep', b = Marg's salt today.

  seed_s436.py --app DIR --db PATH      (DIR = the finance folder carrying stockmatch.py v1.1 and loss_piles.py v2.3)
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys

RULE_WHO = "rule D638, 28-Sep"
OWNER = "owner (S436, said in chat 28-Sep)"
SALT_SOURCE = "S436-owner-28-Sep"
PAIRS = (("ETOZOX 90", "PARI CR 12.5"), ("LACTOVAX SYP", "LINVIZ 600"), ("LACTOVAX SYP", "FEBUTAL"))
PAIR_NOTE = "not a swap -- salt wrong in Marg (rule D638, 28-Sep)"
SALT_FIX = (("JARDIANCE 25", "EMPAGLIFLOZIN 25"), ("PARI CR 12.5", "PAROXETINE CR 12.5"),
            ("LACTOVAX SYP", "LAXATIVE (LACTULOSE)"), ("LINVIZ 600", "LINEZOLID 600"))   # LACTOVAX: Marg's own master says FEBUXOSTAT 40 (wrong) -> the brief's fallback


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def seed(db, app):
    sys.path.insert(0, app)
    os.environ["FINANCE_DB"] = db
    os.chdir(app)
    import finance_app as fa                                  # noqa: PLC0415 -- the copies beside the app, never the kit's
    import stock_app                                          # noqa: PLC0415
    import stockmatch                                         # noqa: PLC0415
    import loss_piles                                         # noqa: PLC0415
    with fa.app.test_request_context():
        con = stock_app._db()
        stock_app.ensure_schema(con)
        stock_app._pad_ensure(con)
        stockmatch.ensure_schema(con)
        loss_piles.ensure(con)
        root = stock_app._newest_root(con) or 1
        d = stock_app._pad_report_data(con, root)
        if d is None:
            print("   no count: nothing to seed")
            return 0
        ts = now_iso()
        # ---- 3.1 the causes, by rule
        n_conv = n_def = n_over = 0
        for l in stockmatch.lines_of(con, d):
            if not l["open"]:
                continue
            row = con.execute("SELECT cause, cause_by, cause_at, cause_note FROM stock_diff WHERE id=?", (l["diff_id"],)).fetchone()
            old_cause, old_by, old_note = (row[0] or "UNEXPLAINED"), (row[1] or ""), (row[3] or "")
            if l["side"] == "short":
                new = "BILLING"
                if old_cause in ("UNEXPLAINED", ""):
                    by, note = RULE_WHO, stockmatch.DEFAULT_NOTE
                else:
                    by, note = (old_by or RULE_WHO), "%s: sold without bill (was: %s by %s)" % (RULE_WHO, stock_app.CAUSE_LABEL.get(old_cause, old_cause), old_by or "-")
            else:
                new = "BILLED_NOT_GIVEN"
                if old_cause in ("UNEXPLAINED", ""):
                    by, note = RULE_WHO, stockmatch.DEFAULT_NOTE
                else:
                    by, note = (old_by or RULE_WHO), "%s: billed, not handed over (was: %s by %s)" % (RULE_WHO, stock_app.CAUSE_LABEL.get(old_cause, old_cause), old_by or "-")
            if old_cause == new and (old_note.startswith(RULE_WHO) or old_note.startswith(stockmatch.DEFAULT_NOTE) or old_note.startswith("S404")):
                continue                                       # already the rule's word (or Darpan's own tap of the same answer)
            con.execute("UPDATE stock_diff SET cause=?, cause_note=?, cause_by=?, cause_at=? WHERE id=?", (new, note, by, ts, l["diff_id"]))
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("stock_diff", l["diff_id"], "cause_rule", json.dumps(dict(cause=old_cause, by=old_by, note=old_note)),
                         json.dumps(dict(cause=new, by=by, note=note, item=l["item"], side=l["side"], rule="D638")), RULE_WHO, ts))
            if l["side"] == "short":
                if old_cause in ("UNEXPLAINED", ""):
                    n_def += 1
                else:
                    n_conv += 1
            else:
                n_over += 1
        con.commit()
        print("   causes by rule: %d short lines Darpan answered -> sold without bill; %d unanswered -> the same by default; %d extra lines -> billed, not handed over" % (n_conv, n_def, n_over))
        # ---- 3.3 the wrong-salt pairs (before the salt fixes take them off the matcher)
        for short, over in PAIRS:
            last = con.execute("SELECT answer, note FROM stock_match WHERE count_id=? AND short_item=? AND over_item=? ORDER BY id DESC LIMIT 1", (root, short, over)).fetchone()
            if last and last[0] == "NO" and "salt wrong" in (last[1] or ""):
                print("   pair %s <-> %s: already NO with the note" % (short, over))
                continue
            ok, msg, code = stock_app.match_answer(con, d, short, over, "NO", PAIR_NOTE, OWNER)
            print("   pair %s <-> %s: %s" % (short, over, msg if ok else ("not proposed today (%s) -- nothing written" % code)))
        # ---- 3.4a the salt fixes
        con.execute("""CREATE TABLE IF NOT EXISTS purchase_salt_task (id INTEGER PRIMARY KEY, section TEXT NOT NULL, seq INTEGER NOT NULL, a TEXT NOT NULL, b TEXT, c TEXT,
                       done INTEGER NOT NULL DEFAULT 0, done_by TEXT, done_at TEXT, answer TEXT, answer_by TEXT, answer_at TEXT, source_md5 TEXT, pushed_at TEXT, UNIQUE(section, a))""")
        marg = {}
        try:
            marg = {str(r[0] or "").strip().upper(): str(r[1] or "").strip() for r in con.execute("SELECT item_norm, salt FROM purchase_salt_marg")}
        except sqlite3.Error:
            pass
        seq = int(con.execute("SELECT COALESCE(MAX(seq),0) FROM purchase_salt_task WHERE section='change'").fetchone()[0] or 0)
        for item, new in SALT_FIX:
            now_ = marg.get(item.upper()) or ""
            row = con.execute("SELECT id, c, source_md5, COALESCE(done,0) FROM purchase_salt_task WHERE section='change' AND a=?", (item,)).fetchone()
            if row and row[1] == new and str(row[2] or "").startswith(SALT_SOURCE):
                print("   salt fix %s -> %s: already seeded" % (item, new))
                continue
            seq += 1
            if row:
                con.execute("UPDATE purchase_salt_task SET seq=?, b=?, c=?, source_md5=?, pushed_at=?, done=0, done_by=NULL, done_at=NULL WHERE id=?",
                            (seq, now_ or (row[1] or ""), new, SALT_SOURCE, ts, row[0]))
                tid = row[0]
            else:
                cur = con.execute("INSERT INTO purchase_salt_task (section, seq, a, b, c, source_md5, pushed_at) VALUES ('change',?,?,?,?,?,?)",
                                  (seq, item, now_ or "(Marg mein nahi)", new, SALT_SOURCE, ts))
                tid = int(cur.lastrowid)
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("purchase_salt_task", tid, "salt_fix_seed", json.dumps(dict(item=item, salt=now_)), json.dumps(dict(item=item, salt=new, text="%s: salt %s -> %s (the owner, 28-Sep)" % (item, now_ or "-", new))), OWNER, ts))
            print("   salt fix %s: %s -> %s" % (item, now_ or "-", new))
        con.commit()
        # ---- 3.2 the section closes by rule
        d = stock_app._pad_report_data(con, root)
        R = stockmatch.close_by_rule(con, d, RULE_WHO)
        if R is None:
            print("   orthotics NOT closed: a line is still open without a reason")
        elif R.get("already"):
            print("   orthotics already closed by rule: run %s, %d lines short, %s, round %s" % (R.get("id"), R.get("n_short"), stock_app._loss_rs(R.get("mrp_p") or 0), R.get("round_no")))
        else:
            print("   orthotics closed by rule: run %s -- %d lines short, %s at selling price (%d without a price), %d book corrections; round %s (%s lines) on Amir's board" % (
                R.get("id"), R.get("n_short"), stock_app._loss_rs(R.get("mrp_p") or 0), R.get("unpriced") or 0, R.get("n_fix"), R.get("made_round"), R.get("made_lines")))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))

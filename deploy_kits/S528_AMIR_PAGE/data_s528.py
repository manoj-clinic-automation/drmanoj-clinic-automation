#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s528.py -- kit S528_AMIR_PAGE, the data step (brief section 5): the ticked renames re-judged from the newest closing on the box.

    /usr/bin/python3 -B data_s528.py --db /root/finance/finance.db --modules DIR --finance /root/finance --archive /root/marg_ingest/archive
                            --readings /root/finance/spine/readings [--dry]       (the service python: it holds xlrd, as marg_take's reader needs)

  modules   a scratch folder holding the KIT's item_alias.py (copied out of deploy_kits/ -- CLAUDE.md 11); reports_watch, stock_watch and
            section_map are read from --finance beside it.
  Reads where marg_take._rename_verify reads: the newest VERIFIED STOCK_CLOSING row of mi_file whose stamp (ISO) is after MAX(done_at) of
  the ticked, unverified rows; its file under the archive (STOCK_CLOSING/<yyyy-mm>/..__<stamp>__<md5[:8]>.xls, read by spine/marg_read.read_file);
  the reading /readings/<md5>.json (family STOCK_CLOSING, ok, data.items[].name, data.as_on) is the fallback when the file is gone.
  Calls the kit's item_alias.sight_closing (the short-closing gate applies). Keyed and idempotent: a second run finds the rows verified or
  questioned and judges nothing twice (a question is written once per (row, event, seen name); seen_n once per printed day).
  Prints one line per ticked row (verified / question / both / collision / not seen) and the rename summary after. Skipped, with a line, when
  no such closing exists or when every ticked row is already verified or questioned. --dry rolls back.
  Never DELETE. The reverse (if the chat orders it) is in README.md. No person, phone or account number is printed."""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys


def stamp_iso(stamp):
    s = str(stamp or "")
    if not re.match(r"^\d{8}-\d{6}$", s):
        return ""
    return "%s-%s-%sT%s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--modules", required=True)
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--archive", default="/root/marg_ingest/archive")
    ap.add_argument("--readings", default="/root/finance/spine/readings")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    sys.path.insert(0, os.path.join(a.finance, "spine"))
    sys.path.insert(0, a.modules)                               # first: the kit's item_alias wins
    import item_alias                                           # noqa: E402
    assert os.path.abspath(item_alias.__file__).startswith(os.path.abspath(a.modules)), item_alias.__file__
    con = sqlite3.connect(a.db, timeout=60)
    item_alias.ensure(con)
    rows = item_alias.rows(con)
    ticked = [r for r in rows if r["done_at"] and not r.get("undone_at") and not r["verified_at"]]
    open_ = [r for r in ticked if r["state"] != "question"]
    print("DATA_S528: %d rename rows; %d ticked and not verified (%d of them already a question)" % (len(rows), len(ticked), len(ticked) - len(open_)))
    for r in rows:
        print("   before  %-9s %-31s -> %-30s %s" % (r["state"], r["old_name"], r["new_name"], (r["done_at"] or "")[:19]))
    if not open_:
        print("DATA_S528: nothing to judge (every ticked row is verified or a question) -- skipped")
        con.close()
        return 0
    max_done = max(str(r["done_at"])[:19] for r in open_)
    cands = con.execute("SELECT md5, stamp, date_to FROM mi_file WHERE type='STOCK_CLOSING' AND verdict='VERIFIED' ORDER BY stamp DESC").fetchall()
    newest = cands[0] if cands else None
    if not newest or stamp_iso(newest[1]) <= max_done:
        print("DATA_S528: no VERIFIED closing captured after the newest tick (%s; newest closing %s) -- skipped; tomorrow's closing judges through marg_take"
              % (max_done, newest[1] if newest else "none"))
        con.close()
        return 0
    md5, stamp = str(newest[0]), str(newest[1])
    names, as_on, how = [], "", ""
    paths = glob.glob(os.path.join(a.archive, "STOCK_CLOSING", "*", "*__%s__%s*" % (stamp, md5[:8])))
    if paths:
        try:
            import marg_read                                    # noqa: E402
            fam, R, _m = marg_read.read_file(paths[0])
            if fam == "STOCK_CLOSING" and R is not None:
                names = [i["name"] for i in (R.data.get("items") or []) if i.get("name")]
                as_on = R.data.get("as_on") or ""
                how = "archive file %s" % os.path.basename(paths[0])[:60]
        except Exception as e:                                  # noqa: BLE001
            print("   the archive file could not be read (%s) -- the reading is the fallback" % str(e)[:100])
    if not names:
        p = os.path.join(a.readings, md5 + ".json")
        if os.path.exists(p):
            j = json.load(open(p, encoding="utf-8"))
            if j.get("family") == "STOCK_CLOSING" and j.get("ok"):
                names = [i.get("name") for i in ((j.get("data") or {}).get("items") or []) if i.get("name")]
                as_on = (j.get("data") or {}).get("as_on") or ""
                how = "reading %s.json" % md5[:12]
    if not names or not as_on:
        print("DATA_S528: the closing %s (%s) has no readable names -- skipped" % (md5[:8], stamp))
        con.close()
        return 0
    print("DATA_S528: judging from the closing captured %s, printed for %s, %d names (%s); the newest tick %s" % (stamp_iso(stamp), as_on, len(names), how, max_done))
    res = item_alias.sight_closing(con, names, as_on, md5, stamp, source="S528 data step")
    if res.get("skipped"):
        print("DATA_S528: skipped -- %s %s" % (res.get("skipped"), res.get("short") or ""))
        con.rollback()
        con.close()
        return 0
    after = {r["id"]: r for r in item_alias.rows(con)}
    for r in ticked:
        x = after[r["id"]]
        q = x.get("question") or {}
        if x["state"] == "verified":
            line = "verified (Marg prints it; closing %s)" % (x.get("verified_as_on") or as_on)
        elif x["state"] == "question":
            line = "%s -- Marg prints '%s' (the owner's tap on Amir's board)" % (q.get("event"), q.get("seen_name"))
        else:
            line = "not seen (seen_n %s) -- tomorrow's closing judges it by itself" % x.get("seen_n")
        print("   after   %-31s -> %-30s %s" % (r["old_name"], r["new_name"], line))
    print("DATA_S528: summary after: %s" % {k: v for k, v in item_alias.summary(con).items() if k != "kit"})
    if a.dry:
        con.rollback()
        print("DATA_S528: DRY -- rolled back")
    else:
        con.commit()
        print("DATA_S528: committed")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

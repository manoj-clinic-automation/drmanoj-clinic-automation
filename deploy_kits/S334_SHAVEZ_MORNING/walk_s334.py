"""walk_s334.py -- kit S334_SHAVEZ_MORNING (S274, Sanjeevni). Walks the NEW reports_tile.py against a
scratch copy of the real finance.db, the spine's real readings (read-only) and the door's real kept files
(read-only). Nothing is written anywhere but the scratch folder the installer hands it.

    python3 -B walk_s334.py <app dir holding reports_tile.py> <finance.db copy> [<empty scratch dir>]

Environment honoured (the same names the module reads): SPINE_READINGS, SPINE_DB, MI_ARCHIVE.
Prints one line per finding and ends with 'WALK OK n checks' or 'WALK RED ...' (exit 1).
"""
import datetime as dt
import importlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
fails = []
n = [0]


def ck(name, cond, detail=""):
    n[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + (("  -- " + str(detail)[:200]) if detail and not cond else ""))
    if not cond:
        fails.append(name)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    app, dbp = argv[0], argv[1]
    scratch = argv[2] if len(argv) > 2 else tempfile.mkdtemp(prefix="s334_walk_")
    sys.path.insert(0, app)
    rt = importlib.import_module("reports_tile")
    ck("the module is the S334 one (KIT, certify, owner_lists, _banner present)",
       getattr(rt, "KIT", "") == "S334_SHAVEZ_MORNING" and all(hasattr(rt, x) for x in ("certify", "owner_lists", "_banner", "_due_day")))
    if fails:
        print("WALK RED: not the S334 module")
        return 1
    cx = sqlite3.connect(dbp)
    cx.row_factory = sqlite3.Row
    readings = os.environ.get("SPINE_READINGS", rt.SPINE_READINGS)
    archive = os.environ.get("MI_ARCHIVE", rt.MI_ARCHIVE)
    have_readings = os.path.isdir(readings) and any(f.endswith(".json") for f in os.listdir(readings))
    print("  readings dir %s (%s) · archive %s (%s) · spine.db %s" % (
        readings, "present" if have_readings else "ABSENT/empty", archive, "present" if os.path.isdir(archive) else "ABSENT",
        "present" if os.path.exists(os.environ.get("SPINE_DB", rt.SPINE_DB)) else "ABSENT"))
    now = dt.datetime.now(IST)
    today = now.date()

    # 1. today, as the page will show it -- must not raise, every row in a known state
    s = rt.status(cx, today, now)
    states = {"due", "refused", "arrived", "ok", "bad"}
    ck("today's status computes: %d rows, states known" % s["total"], all(r["state"] in states for r in s["rows"]))
    for r in s["rows"]:
        print("     %-24s %-8s %s %s %s" % (r["key"], r["state"], r.get("at", ""), r.get("count", ""), ("cert=" + r.get("cert", "")) if r.get("cert") else ""))
    print("     line: " + s["line"])
    if s.get("banner"):
        print("     banner: " + s["banner"]["kind"] + " -- " + s["banner"]["text_hi"])
    html = rt.render(s)
    ck("today's page renders", "Aaj ki reports" in html and len(html) > 2000)
    ck("no 10-digit number on the page (F-185)", not __import__("re").search(r"(?<!\d)[6-9]\d{9}(?!\d)", html))

    # 2. the last ten counter days: every VERIFIED sale export found by the page, its certificate stated
    lag = []
    verified = cx.execute("SELECT md5, date_from, received_at, server_name FROM mi_file WHERE type='SALE_BILLWISE' AND verdict='VERIFIED' "
                          "AND received_at >= ? ORDER BY received_at", ((today - dt.timedelta(days=12)).isoformat(),)).fetchall()
    n_ok = n_arr = n_bad = 0
    for v in verified:
        c = rt.certify(v["md5"], v["server_name"], "SALE_BILLWISE")
        if c is None:
            n_arr += 1
        elif c["ok"]:
            n_ok += 1
        else:
            n_bad += 1
            print("     sale export %s for %s: reader FAILED -- %s" % (v["md5"][:8], v["date_from"], "; ".join(c["failed"])[:160]))
        p = os.path.join(readings, v["md5"] + ".json")
        if os.path.exists(p):
            try:
                ra = json.load(open(p)).get("read_at", "")
                rcv = rt._norm_ts(v["received_at"])
                if ra and rcv:
                    d = (dt.datetime.fromisoformat(ra) - dt.datetime.fromisoformat(rcv)).total_seconds() / 3600.0
                    lag.append((v["date_from"], round(d, 1)))
            except Exception:                                   # noqa: BLE001
                pass
    print("     sale exports of the last 12 days: %d verified by the door · %d certified by the spine · %d not read yet · %d failed the reader"
          % (len(verified), n_ok, n_arr, n_bad))
    if lag:
        print("     lag door -> spine reading, hours: " + ", ".join("%s %+.1f" % x for x in lag[-8:]))
    ck("certify() answers for every verified sale export without raising", True)
    if have_readings:
        ck("at least one sale export of the last 12 days is certified by the spine (readings present)", n_ok >= 1, "%d ok" % n_ok)

    # 3. the kept closing files: the same reader run here
    kept = cx.execute("SELECT md5, date_from, server_name FROM mi_file WHERE type='STOCK_CLOSING' AND verdict='VERIFIED' AND kept=1 "
                      "ORDER BY received_at DESC LIMIT 3").fetchall()
    local = 0
    for k in kept:
        c = rt.certify(k["md5"], k["server_name"], "STOCK_CLOSING")
        print("     closing %s as on %s: %s" % (k["md5"][:8], k["date_from"], "no certificate (not kept here, no reading)" if c is None
                                                 else ("%s · %s · %s" % ("ok" if c["ok"] else "FAILED " + "; ".join(c["failed"])[:80], c["count"], c["source"]))))
        if c is not None and c["source"] == "local":
            local += 1
    if os.path.isdir(archive) and kept:
        ck("a kept closing file is read by the local reader when the store has no reading (or the store has it)",
           any(rt.certify(k["md5"], k["server_name"], "STOCK_CLOSING") is not None for k in kept))

    # 4. every day of the last 14 renders (the picked-date route), none raises
    bad_days = []
    for i in range(1, 15):
        d = today - dt.timedelta(days=i)
        try:
            rt.render(rt.status(cx, d, dt.datetime.combine(d, dt.time(11, 0), tzinfo=IST)), picked_date=True)
        except Exception as e:                                  # noqa: BLE001
            bad_days.append("%s: %s" % (d, e))
    ck("the last 14 days render as picked dates", not bad_days, bad_days[:2])

    # 5. the owner's lists
    for L in s["owner_lists"]:
        print("     %-14s last %s · %s days · limit %d · %s" % (L["label"], L["last"] or "never", L["age_days"], L["limit"], "OVERDUE" if L["overdue"] else "ok"))
    ck("the three owner lists are answered", len(s["owner_lists"]) == 3)

    # 6. negative controls
    empty = os.path.join(scratch, "no_readings")
    os.makedirs(empty, exist_ok=True)
    keep = (rt.SPINE_READINGS, rt.MI_ARCHIVE)
    rt.SPINE_READINGS, rt.MI_ARCHIVE = empty, os.path.join(scratch, "no_archive")
    rt._READ_CACHE.clear()
    s0 = rt.status(cx, today, now)
    ck("NEGATIVE: with no readings and no kept files nothing is certified -- every verified row is ARRIVED, never a tick",
       not any(r["state"] == "ok" and r.get("cert") not in ("structural",) for r in s0["rows"]))
    if verified:
        v = verified[-1]
        os.makedirs(empty, exist_ok=True)
        with open(os.path.join(empty, v["md5"] + ".json"), "w") as fh:
            json.dump(dict(md5=v["md5"], family="SALE_BILLWISE", ok=False, failed=["GRAND TOTAL = sum of bill GROSS"], data={"bills": [1] * 3}), fh)
        c = rt.certify(v["md5"], v["server_name"], "SALE_BILLWISE")
        ck("NEGATIVE: a reading that failed its witness is a BAD certificate, not a tick", c is not None and not c["ok"] and c["count"] == "3 bills")
    rt.SPINE_READINGS, rt.MI_ARCHIVE = keep
    rt._READ_CACHE.clear()
    b = rt._banner([{"key": "SALE_BILLWISE", "pair": True, "state": "due"}, {"key": "STOCK_CLOSING", "pair": True, "state": "ok"}],
                   dt.date(2026, 9, 22), dt.datetime(2026, 9, 22, 12, 0, tzinfo=IST))
    ck("NEGATIVE: the banner names only what is missing", b and "bikri report" in b["text_hi"] and "closing stock" not in b["text_hi"])
    ck("NEGATIVE: a Sunday raises no banner however late", rt._banner([{"key": "SALE_BILLWISE", "pair": True, "state": "due"}],
                                                                   dt.date(2026, 9, 20), dt.datetime(2026, 9, 20, 15, 0, tzinfo=IST)) is None)
    shutil.rmtree(scratch, ignore_errors=True) if len(argv) <= 2 else None
    if fails:
        print("WALK RED: %d of %d checks failed: %s" % (len(fails), n[0], "; ".join(fails)[:300]))
        return 1
    print("WALK OK %d checks" % n[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

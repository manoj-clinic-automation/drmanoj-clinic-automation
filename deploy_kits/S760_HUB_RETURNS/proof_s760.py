"""proof_s760.py -- kit S760_HUB_RETURNS: the hub's Returns card read on THIS box's real data. Read only: it reads a COPY of finance.db
and the LIVE spine (spine.db, opened mode=ro through spine_read -- SPINE_DB names it). Prints COUNTS only (no bill number, no medicine,
no patient) and the time the read takes.
  python3 proof_s760.py <finance dir under test> <shared dir> <finance.db> <scratch dir> [<spine.db, read only>]
Last line: 'PROOF S760: months N · needs N (Rs ..) · cant N · repeats N · history N · batch checks amber N red N not-asked N ·
hidden-rounding N · line = card N · spine yes|none · hub N.N s (light N.N s)'
or 'PROOF S760: STOP -- <why>' (the line and the card disagree; the hub read takes over 3 s; the read failed),
or, on the live files (no hub yet): 'PROOF S760 (the live files): no hub -- this month's pending under the S406 rule N'."""
import os, sqlite3, sys, time, warnings
warnings.filterwarnings("ignore")
fin, shared, db, scr = (os.path.abspath(x) for x in sys.argv[1:5])
spine = os.path.abspath(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] else ""
LIMIT_S = 3.0
os.makedirs(scr, exist_ok=True)
cp = os.path.join(scr, "proof760.db")
src = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
dst = sqlite3.connect(cp)
src.backup(dst)
src.close(); dst.close()
has_spine = bool(spine) and os.path.isfile(spine)
if has_spine:
    os.environ["SPINE_DB"] = spine                       # spine_read opens it file:...?mode=ro
else:
    os.environ["SPINE_DB"] = os.path.join(scr, "no_spine_here.db")
sys.path[:0] = [fin, os.path.join(fin, "spine"), shared]
os.chdir(scr)
import returns_kinds                                                  # noqa: E402
assert os.path.dirname(os.path.abspath(returns_kinds.__file__)) == fin
c = sqlite3.connect(cp, timeout=30)
c.row_factory = sqlite3.Row
if not hasattr(returns_kinds, "hub"):
    import datetime as dt
    m = dt.date.today().isoformat()[:7]
    n, p = returns_kinds.pending_count(c, "medical", m)
    print("PROOF S760 (the live files): no hub -- this month's pending under the S406 rule %d (Rs %s)" % (n, p / 100.0))
    sys.exit(0)
before = c.execute("SELECT COUNT(*) FROM cn_kind").fetchone()[0] if c.execute("SELECT 1 FROM sqlite_master WHERE name='cn_kind'").fetchone() else None
try:
    t0 = time.time()
    H = returns_kinds.hub(c, "medical")
    t_full = time.time() - t0
    t0 = time.time()
    HL = returns_kinds.hub(c, "medical", light=True)
    t_light = time.time() - t0
except Exception as e:                                                # noqa: BLE001
    print("PROOF S760: STOP -- the hub read failed: %r" % (e,))
    sys.exit(0)
after = c.execute("SELECT COUNT(*) FROM cn_kind").fetchone()[0] if before is not None else None
R = {r["key"]: r for m in H["months"] for r in m["rows"]}
print("spine: %s" % ("the live spine, read only" if has_spine else "none given (not the box) -- every return reads 'not examinable'"))
print("months (newest first, counts only):")
for m in H["months"]:
    print("  %s%s · %d returns · Rs %s · counter %s%% · fine %d · need your OK %d · can't be checked %d · discounted %d · large %d · rejected %d · non-cash %d (not in purchases %d)"
          % (m["label"], " (current)" if m["current"] else "", m["n"], m["p"] / 100.0, m["counter_pct"], m["fine"], m["need"],
             m["cant"], m["discounted"], m["large"], m["rejected"], m["noncash_n"], m["noncash_bad"]))
print("history: " + " · ".join("%s %d" % (x["label"], x["n"]) for x in H["history"]))
amber = red = notasked = unread = 0
for r in R.values():
    if r.get("amount_unread") and r["pending_ok"]:
        unread += 1
    for x in r["in_question"]:
        if x["verdict"] != "NEVER BOUGHT" or r["historical"]:
            continue
        if x["batch_sold"] is None:
            notasked += 1
        elif x["batch_sold"] > 0:
            amber += 1
        else:
            red += 1
print("needs your OK: %d · Rs %s · oldest %s · whole-return %d · amount could not be read %d"
      % (len(H["needs"]), H["pending_ok_p"] / 100.0, H.get("pending_oldest") or "-", sum(1 for k in H["needs"] if R[k]["whole"]), unread))
print("repeats: %d (the largest in %d of the waiting returns)" % (len(H["repeats"]), max([x["n"] for x in H["repeats"]] or [0])))
print("can't be checked yet: %d" % len(H["cant"]))
st = returns_kinds.settings(c)
raw_hidden = 0
for m in H["months"]:                                    # the F-1200 count: shortfalls the engine carries and the rounding line hides
    for n in returns_kinds._s760_notes(c, "medical", m["ym"], st["act_from"]):
        sf = n.get("refund_shortfall_p")
        if sf and returns_kinds.is_noise(st, sf, int(n.get("amount_p") or 0)):
            raw_hidden += 1
print("cn_kind rows before / after the reads: %s / %s" % (before, after))
print("time: the full read %.2f s · the light read (the Needs-you line) %.2f s · the limit %.0f s" % (t_full, t_light, LIMIT_S))
try:
    import sanjeevni_approvals as sa                                  # the Needs-you line, by the files under test
    assert os.path.dirname(os.path.abspath(sa.__file__)) == fin
    ln = sa._s760_returns_line(c, H["today"])
    line_n = (ln or {}).get("n", 0) if ln is not None else None
except Exception as e:                                                 # noqa: BLE001
    print("PROOF S760: STOP -- the Needs-you line did not answer: %r" % (e,))
    sys.exit(0)
if line_n != len(H["needs"]) or HL["needs"] != H["needs"]:
    print("PROOF S760: STOP -- the Needs-you line says %s, the card %d (the light read %d)" % (line_n, len(H["needs"]), len(HL["needs"])))
    sys.exit(0)
if before is not None and after != before:
    print("PROOF S760: STOP -- the read saved cn_kind rows (%s -> %s); the hub must write nothing" % (before, after))
    sys.exit(0)
if t_full > LIMIT_S:
    print("PROOF S760: STOP -- the hub read took %.1f s, over %.0f s" % (t_full, LIMIT_S))
    sys.exit(0)
print("PROOF S760: months %d · needs %d (Rs %s) · cant %d · repeats %d · history %d · batch checks amber %d red %d not-asked %d · hidden-rounding %d · line = card %d · spine %s · hub %.1f s (light %.1f s)"
      % (len(H["months"]), len(H["needs"]), H["pending_ok_p"] / 100.0, len(H["cant"]), len(H["repeats"]), len(H["history"]),
         amber, red, notasked, raw_hidden, line_n, "yes" if has_spine else "none", t_full, t_light))

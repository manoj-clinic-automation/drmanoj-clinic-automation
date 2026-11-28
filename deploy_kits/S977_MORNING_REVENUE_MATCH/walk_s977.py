#!/usr/bin/env python3
"""walk_s977.py -- kit S977 (K2a). Made-up data only (letters for IDs, no number of any patient). Usage: walk_s977.py FINANCE_DIR REAL_SCHEMA_DB"""
import sys, os, sqlite3, shutil, tempfile, datetime as dt
FIN, SCHEMA_DB = sys.argv[1], sys.argv[2]
sys.path.insert(0, FIN)
os.environ["EVCHK_LIVE_DB"] = "/nonexistent/live.db"
import day_check as dc, register_push as rp, docterz_pickup as dp
D = (dt.date.today() - dt.timedelta(days=1)).isoformat()
TMP = tempfile.mkdtemp(prefix="w977_")
PASS = FAIL = 0
def ok(name, cond, info=""):
    global PASS, FAIL
    if cond: PASS += 1; print("PASS", name)
    else: FAIL += 1; print("FAIL", name, info)
sch = sqlite3.connect(SCHEMA_DB)
DDL = [r[0] for r in sch.execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")]
n_db = 0
def fresh():
    global n_db
    n_db += 1
    p = os.path.join(TMP, "w%d.db" % n_db)
    c = sqlite3.connect(p); c.row_factory = sqlite3.Row
    for s in DDL:
        try: c.execute(s)
        except sqlite3.Error: pass
    c.execute("INSERT INTO clinic_day_revenue (business_date, source_file, source_id, source_mtime, taken_at, cons_count, cons_amount_p, "
              "xray_count, xray_amount_p, proc_count, proc_amount_p, total_count, total_amount_p, free_revisits, free_concession, "
              "f93_phantom_rows, tender_json) VALUES (?, 'f', 'i', 'm', ?, 0,0,0,0,0,0,0,0,0,0,0,'{}')", (D, D + " 20:00:00"))
    c.commit(); dc._done = False
    return c, p
SN = [0]
def line(c, sec, cid, amt, mode="Cash", pat="Walk Person"):
    SN[0] += 1
    c.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
              (D, sec, SN[0], pat + " " + cid, cid, amt * 100, mode))
def reg(c, **kw):
    cols = {k + "_p": v * 100 for k, v in kw.items()}
    c.execute("INSERT INTO clinic_register_day (business_date, %s) VALUES (?, %s)" % (", ".join(cols), ",".join("?" * len(cols))), (D, *cols.values()))
NO = [0]
def slip(c, series, cid, items=()):
    NO[0] += 1
    c.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, name_seen) VALUES (?,?,?,?,'ok',?)", (series, NO[0], D, cid, "Walk " + cid))
    sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    for i, (kind, name, price) in enumerate(items):
        c.execute("INSERT INTO slip_item (slip_id, kind, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,0)", (sid, kind, name, "", price * 100, i))
    return sid
def chk(c, rev=True):
    os.environ["DAYCHK_REVENUE"] = "1" if rev else "0"
    c.commit()
    return dc.check_day(c, D)
keys = lambda ch: [x["key"] for x in ch["cards"]]

# C1 equal
c, p = fresh(); line(c, "consult", "WKA", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA")
ch = chk(c)
ok("C1 equal: no card", ch["cards"] == [], keys(ch)); ok("C1 clean", dc.is_clean(ch)); ok("C1 left 0", ch["top"]["left"] == 0)
ok("C1 breakdown", dc.breakdown(ch).startswith("Register Rs 600 = Docterz Rs 600 + parchi bahar Rs 0"), dc.breakdown(ch))
ok("C1 rev flag", ch.get("rev") is True)
# C2 tender differs only
c, p = fresh(); line(c, "consult", "WKA", 600, "Cash"); reg(c, cons_upi=600); slip(c, "opd", "WKA")
ch = chk(c); ok("C2 tender only: no card under the revenue match", ch["cards"] == [], keys(ch))
ch0 = chk(c, rev=False); ok("C2 CONTROL: the old morning names it", len(ch0["cards"]) >= 1, keys(ch0))
ok("C2 no mode kind anywhere", not any(x["kind"] == "mode" or x["key"].split(":")[0] in ("modeany", "swap", "regupi", "bank") for x in ch["cards"]))
# C3 register more, an unbilled patient of the day
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 0); reg(c, cons_cash=600, xray_cash=500)
slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
ch = chk(c); nf = [x for x in ch["cards"] if x["key"].startswith("nf:")]
ok("C3 one nf card", len(nf) == 1, keys(ch)); ok("C3 amount 500", nf and nf[0]["amount"] == 50000)
ok("C3 section xray", nf and nf[0]["section"] == "xray", nf and nf[0].get("section"))
ok("C3 candidate = the unbilled patient", nf and [x[0] for x in nf[0]["cands"]] == ["WKB"], nf and nf[0].get("cands"))
ok("C3 staff card", nf and nf[0]["who"] == "docterz")
# C4 register less by one consultation
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=600)
slip(c, "opd", "WKA"); sb = slip(c, "opd", "WKB")
ch = chk(c); ls = [x for x in ch["cards"] if x["kind"] == "less"]
ok("C4 one 'less' card", len(ls) == 1, keys(ch)); ok("C4 key", ls and ls[0]["key"] == "less:consult:60000", ls and ls[0]["key"])
ok("C4 cands both", ls and sorted(x[0] for x in ls[0]["cands"]) == ["WKA", "WKB"])
okm, er = dc._s977_lessnp(c, D, ls[0], "WKZ", "shavez", True); ok("C4 a pick off the list refused", er and not okm)
okm, er = dc._s977_lessnp(c, D, ls[0], "WKB", "shavez", True); ok("C4 pick writes the radd", okm and not er, er)
ra = c.execute("SELECT slip_id, cancel_how, state FROM slip_adjust WHERE kind='cancel'").fetchall()
ok("C4 radd on WKB's slip, never_taken, pending", len(ra) == 1 and ra[0][0] == sb and ra[0][1] == "never_taken" and ra[0][2] == "pending", [tuple(r) for r in ra])
ch = chk(c); ok("C4 after the pick the day matches", ch["top"]["left"] == 0 and not any(x["kind"] == "less" for x in ch["cards"]), keys(ch))
ok("C4 refund row shown", len(ch["refunds"]) == 1)
# C4b the pick with no single slip refused
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA")
ch = chk(c); ls = [x for x in ch["cards"] if x["kind"] == "less"]
okm, er = dc._s977_lessnp(c, D, ls[0], "WKB", "shavez", True) if ls else ("", "no card")
ok("C4b no slip for the pick: refused", er and not okm, er)
# C4c review M4: two consultation lines of one patient, the gap the smaller -- the radd would take the other: refused
c, p = fresh(); line(c, "consult", "WKA", 800); line(c, "consult", "WKA", 300); line(c, "consult", "WKB", 600); reg(c, cons_cash=1400)
slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
ch = chk(c); ls = [x for x in ch["cards"] if x["kind"] == "less"]
okm, er = dc._s977_lessnp(c, D, ls[0], "WKA", "shavez", True) if ls else ("", "no card")
ok("C4c the card offers that patient", ls and [x[0] for x in ls[0]["cands"]] == ["WKA"], ls and ls[0].get("cands"))
ok("C4c a radd that would take the wrong bill is refused", er and not okm and c.execute("SELECT COUNT(*) FROM slip_adjust").fetchone()[0] == 0, (keys(ch), er))
# C4d review S9: a 'Found it' tick on the nf card asks for no re-export
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 0); reg(c, cons_cash=600, xray_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
ch = chk(c); k = [x["key"] for x in ch["cards"] if x["key"].startswith("nf:")][0]
dc.add_tick(c, D, k, "found", "shavez", pick="WKB"); ch = chk(c)
ok("C4d no 're-export' after a Found it", not ch.get("reexport") and "Re-export" not in dc.summary_en(ch), dc.summary_en(ch))
ok("C4d nf key without a tender", k == "nf:xray:50000", k)
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 0); reg(c, cons_cash=600, xray_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
dc.add_tick(c, D, "nf:cash:xray:50000", "found", "shavez", pick="WKB"); ch = chk(c)
ok("C4d a tick under the old key still counts (second look)", [x for x in ch["cards"] if x["key"].startswith("nf:")][0].get("tick"))
dc.undo_tick(c, D, "nf:xray:50000", "shavez")
for _t in dc.TENDERS: dc.undo_tick(c, D, "nf:%s:xray:50000" % _t, "shavez")
ch = chk(c); ok("C4d Undo clears an old-key tick (re-look)", not [x for x in ch["cards"] if x["key"].startswith("nf:")][0].get("tick"))
# C5 register less, not one bill
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
ch = chk(c); ok("C5 his line less:70000", keys(ch) == ["less:70000"] and ch["cards"][0]["who"] == "hand", keys(ch))
# C5b one head exactly one bill short, two other heads off and cancelling: no 'one patient' card (the heads do not agree)
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); line(c, "xray", "WKA", 500); line(c, "proc", "WKB", 500)
reg(c, cons_cash=600, xray_cash=600, proc_cash=400); slip(c, "opd", "WKA"); slip(c, "opd", "WKB")
slip(c, "xp", "WKA", [("xray", "Walk view", 500)]); slip(c, "xp", "WKB", [("proc", "Walk proc", 500)])
ch = chk(c); ok("C5b other heads off: his line, not reception's", [k for k in keys(ch) if k.startswith("less")] == ["less:60000"], keys(ch))
# C6 a slip Docterz lacks, the patient in Docterz, the register holds it
c, p = fresh(); line(c, "consult", "WKA", 600); reg(c, cons_cash=600, xray_cash=500); slip(c, "opd", "WKA"); slip(c, "xp", "WKA", [("xray", "Walk view", 500)])
ch = chk(c); ok("C6 no card", ch["cards"] == [], keys(ch)); ok("C6 kept outside by itself (top.nid)", ch["top"]["nid"] == 50000 and ch["top"]["left"] == 0, ch["top"])
ok("C6 note says so", any("kept outside Docterz by itself" in n[0] for n in ch["notes"]))
ch0 = chk(c, rev=False); ok("C6 CONTROL: the old morning asks for a Docterz entry", any(x["kind"] == "missing" for x in ch0["cards"]), keys(ch0))
# C6b neither billed nor in the register
c, p = fresh(); line(c, "consult", "WKA", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA"); slip(c, "xp", "WKA", [("xray", "Walk view", 500)])
ch = chk(c); ok("C6b no card, a note", ch["cards"] == [] and any("not billed, not in the register" in n[0] for n in ch["notes"]), keys(ch))
# C7 the evening owns parchi short
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "xray", "WKA", 500); reg(c, cons_cash=600, xray_cash=500)
slip(c, "opd", "WKA"); s7 = slip(c, "xp", "WKA", [("xray", "Walk view", 400)])
ch = chk(c); ok("C7 no evening: parchi card kept", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome) VALUES (1, ?, ?, 'missing')", (D, "2026-11-27 18:00:00"))
ch = chk(c); ok("C7 an evening before S972: card kept", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome, sent, shapes) VALUES (2, ?, ?, 'off', '', ?)", (D, D + " 20:05:00", "more:%d:xray" % s7))
ch = chk(c); ok("C7 an evening 'off' row told nobody: card kept", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome, sent, shapes) VALUES (3, ?, ?, 'missing', 'sent 1, failed 0, ntfy 0', ?)", (D, D + " 20:06:00", "more:%d:proc" % s7))
ch = chk(c); ok("C7 told about another kind of the slip: card kept", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome, sent, shapes) VALUES (4, ?, ?, 'missing', 'sent 1, failed 0, ntfy 0', ?)", (D, D + " 20:10:00", "more:%d:xray" % s7))
ch = chk(c); ok("C7 the widened evening ran: no morning card, a note", not any(x.get("pkind") == "parchi_short" for x in ch["cards"])
               and any("evening check" in n[0] for n in ch["notes"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome, sent, shapes) VALUES (5, ?, ?, 'missing', 'sent 0, failed 2, ntfy 0', ?)", (D, D + " 20:20:00", "more:%d:xray" % s7))
ch = chk(c); ok("C7 a later push that reached nobody: card back (second look)", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome, sent, shapes) VALUES (6, ?, ?, 'quiet', '', ?)", (D, D + " 20:30:00", "more:%d:xray" % s7))
ch = chk(c); ok("C7 'quiet' after a push to nobody: still back", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome, sent, shapes) VALUES (7, ?, ?, 'cleared', 'sent 1, failed 0, ntfy 0', '')", (D, D + " 20:40:00"))
ch = chk(c); ok("C7 the last export cleared, the slip changed after: card back", any(x.get("pkind") == "parchi_short" for x in ch["cards"]), keys(ch))
ch0 = chk(c, rev=False); ok("C7 switch off: card back", any(x.get("pkind") == "parchi_short" for x in ch0["cards"]))
# C7b a slip-side card the evening does not own stays (Docterz billed, no parchi)
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "xray", "WKA", 500); reg(c, cons_cash=600, xray_cash=500); slip(c, "opd", "WKA")
c.execute("INSERT INTO evening_check_push (export_id, day, at, outcome) VALUES (2, ?, ?, 'cleared')", (D, D + " 20:10:00"))
ch = chk(c); ok("C7b parchi_missing kept", any(x.get("pkind") == "parchi_missing" for x in ch["cards"]), keys(ch))

# C8 register_push: the clean push's sum, his push once per line
os.environ["DAYCHK_REVENUE"] = "1"
SENT, OWN = [], []
def fake_send(who, title, body, tag): SENT.append((tuple(who), title, body)); return (1, 0, 0), ""
rp._send = fake_send
dc.PUSHER = lambda who, title, body, url, tag: (OWN.append((tuple(who), title, body, url)) or (1, ""))
AT = dt.datetime.combine(dt.date.fromisoformat(D) + dt.timedelta(days=1), dt.time(9, 0))
c, p = fresh(); line(c, "consult", "WKA", 600); reg(c, cons_cash=600); slip(c, "opd", "WKA"); c.commit(); rp.LIVE_DB = p
w = rp.judge(c, D, push=True, at=AT, from_save=True)
ok("C8 clean push", "clean" in w and SENT and "Register Rs 600 = Docterz Rs 600" in SENT[-1][2], (w, SENT[-1:] if SENT else None))
ok("C8 no owner push on a clean day", OWN == [])
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB"); c.commit(); rp.LIVE_DB = p
rp.judge(c, D, push=True, at=AT, from_save=True)
ok("C8 his push once", len(OWN) == 1 and OWN[0][0] == ("manoj",) and "Rs 700 not explained" in OWN[0][1], OWN)
os_ = c.execute("SELECT owner_sent FROM register_push WHERE day=?", (D,)).fetchone()[0]
ok("C8 owner_sent kept (its lasting name)", os_ == "less", os_)
slip(c, "opd", "WKA"); c.commit()                         # review M1: a new staff line rewrites the row (open)
w2 = rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=2))
ok("C8 a new staff line does not re-push him", "open" in w2 and len(OWN) == 1, (w2, OWN))
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=5)); rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=10), from_save=True)
ok("C8 never twice", len(OWN) == 1, OWN)
ok("C8 not to the staff", not any("not explained" in s[1] for s in SENT))
OWN.clear(); c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB"); c.commit(); rp.LIVE_DB = p
os.environ["REGPUSH_OWNER"] = "0"; rp.judge(c, D, push=True, at=AT, from_save=True); os.environ.pop("REGPUSH_OWNER")
ok("C8 REGPUSH_OWNER=0: none", OWN == [], OWN)
OWN.clear(); c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB"); c.commit(); rp.LIVE_DB = p
w = rp.judge(c, D, push=True, at=AT + dt.timedelta(days=5))
ok("C8 an old day met first is seeded, not told", "seeded" in w and OWN == [], (w, OWN))
w = rp.judge(c, D, push=True, at=AT + dt.timedelta(days=5, minutes=5))
ok("C8 nor on the next sweep (review M2)", OWN == [], (w, OWN))
OWN.clear(); c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB"); c.commit(); rp.LIVE_DB = p
_pu = dc.PUSHER; dc.PUSHER = lambda who, title, body, url, tag: (OWN.append(title) and False) or (0, "no device of his took it")
rp.judge(c, D, push=True, at=AT, from_save=True); dc.PUSHER = _pu
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=5))
ok("C8 a failed send is tried again (review S6)", len(OWN) == 2, OWN)
ok("C8 _norm drops a less amount", rp._norm("less:consult:60000") == "less:consult" and rp._norm("nf:cash:xray:500") == "nf:cash:xray")

OWN.clear(); SENT.clear(); c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB"); c.commit(); rp.LIVE_DB = p
rp.QUIET = True; rp.judge(c, D, push=False, at=AT, from_save=True); rp.QUIET = False
ok("C8 the quiet sweep sends nothing", OWN == [] and SENT == [], (OWN, SENT))
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=5))
ok("C8 yesterday's unexplained gap still reaches him after the quiet sweep (second look)", len(OWN) == 1 and SENT == [], (OWN, SENT))
OWN.clear(); D0 = D; D = (dt.date.fromisoformat(D0) - dt.timedelta(days=3)).isoformat()
c, p = fresh(); line(c, "consult", "WKA", 600); line(c, "consult", "WKB", 600); reg(c, cons_cash=500); slip(c, "opd", "WKA"); slip(c, "opd", "WKB"); c.commit(); rp.LIVE_DB = p
rp.prev = None; rp.QUIET = True; rp.judge(c, D, push=False, at=AT, from_save=True); rp.QUIET = False
rp.judge(c, D, push=True, at=AT + dt.timedelta(minutes=5)); D = D0
ok("C8 an older day after the quiet sweep: never told", OWN == [], OWN)
# C9 docterz_pickup (F-1732): an empty report after the day's good one is not 'set aside'
dp.STORE = os.path.join(TMP, "store"); dp.identify = lambda raw: ("consultation", "", 0, "empty")
dp.export_day = lambda f, fb: D; dp._s868_off = lambda con, day: (False, "slips that day"); dp._s960_evening = lambda con, f: None
c, p = fresh()
c.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at) "
          "VALUES ('g1','n','2026-11-20T15:00:00','aa','consultation',?,10,'','current','','2026-11-20 20:56:00')", (D,)); c.commit()
st = dp.take(c, {"id": "e1", "name": "n", "modifiedTime": "2026-11-21T03:00:00"}, b"x", dry=False)
r = c.execute("SELECT status FROM docterz_export WHERE drive_id='e1'").fetchone()
ok("C9 empty after a good report: superseded", r and r[0] == "superseded", (st, r and r[0]))
c, p = fresh()
dp.take(c, {"id": "e2", "name": "n", "modifiedTime": "2026-11-21T03:00:00"}, b"y", dry=False)
r = c.execute("SELECT status FROM docterz_export WHERE drive_id='e2'").fetchone()
ok("C9 CONTROL: empty with no good report: still set aside", r and r[0] == "quarantined", r and r[0])
c, p = fresh()
c.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at) "
          "VALUES ('g1','n','m','aa','consultation',?,10,'','current','',?)", (D, D + " 21:00:00"))
c.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at) "
          "VALUES ('q1','n','m','bb','consultation',?,0,'','quarantined','EMPTY, yet x',?)", (D, AT.strftime("%Y-%m-%d 08:30:00"))); c.commit()
ws = dp.owner_lines(c, at=AT)
ok("C9 an old quarantined empty after a good one is not said", not any("set aside" in x for x in ws), ws)
print("WALK S977: %d PASS, %d FAIL" % (PASS, FAIL))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)

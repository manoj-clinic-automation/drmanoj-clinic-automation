"""synth_s874.py <finance dir under test> <finance.db COPY> -- kit S874 proof on COPIES: the day's own short (17-Oct 504 with Accept; a day
with entries / a written-off day: none); the full mobile on bills and returns from a MADE-UP Call Console mirror (no real number used);
no mirror -> the last four as before; the page's markers. Last line: 'SYNTH S874: n PASS, m FAIL'."""
import os, re, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
tmp = tempfile.mkdtemp(prefix="s874synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0


def ok(c, w):
    global P, F
    P, F = (P + 1, F) if c else (P, F + 1)
    print(("PASS " if c else "FAIL ") + w)


try:
    db = os.path.join(tmp, "f.db"); shutil.copy(DBC, db)
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    import sanjeevni_day as sd
    mirror = os.path.join(tmp, "console.db")
    sd.CONSOLE_DB = "/nonexistent/console.db"
    v = sd.day_view(con, "2026-11-12")
    rt = v["returns"]["list"]
    cid = next((x["clinic_id"] for x in rt if x["clinic_id"]), None)
    ok(cid is not None and all(not re.match(r"^[6-9]\d{9}$", str(x.get("mobile") or "")) for x in rt), "T1 without the mirror no full mobile is invented (last four at most)")
    mc = sqlite3.connect(mirror); mc.execute("CREATE TABLE patients (phone10 TEXT, clinic_id TEXT, name TEXT)")
    N1, N2 = "9" + "0" * 8 + "1", "9" + "0" * 8 + "2"              # made-up numbers, built here so no number sits in the file (F-185)
    mc.execute("INSERT INTO patients VALUES (?, ?, 'x')", (N1, cid)); mc.execute("INSERT INTO patients VALUES (?, ?, 'x')", ("+91 " + N2[:5] + " " + N2[5:], cid + ".0")); mc.commit(); mc.close()
    sd.CONSOLE_DB = mirror
    v = sd.day_view(con, "2026-11-12")
    r = next(x for x in v["returns"]["list"] if x["clinic_id"] == cid)
    ok(r["mobile"] == N1 and r["mobiles"] == [N1, N2], "T2 a return carries the mirror's full mobiles for its clinic ID (both spellings read)")
    s = next((x for x in v["sale"]["list"] if x.get("clinic_id") == cid), None)
    ok(s is None or s["mobile"] == N1, "T3 a sale bill of the same patient carries the same mobile")
    ok(all("mobiles" in x and "clinic_id" in x for x in v["sale"]["list"]), "T4 every bill carries the fields (empty when unknown)")
    v17 = sd.day_view(con, "2026-10-17")
    ok(v17["short"] == "504" and v17["short_p"] == 50400 and v17["can_accept"] is True, "T5 17-Oct names its own short 504 with Accept offered")
    con.execute("UPDATE darpan_kal_day SET owner_decision='accept', state='explained' WHERE business_date='2026-10-17'"); con.commit()
    v17b = sd.day_view(con, "2026-10-17")
    ok(v17b["short"] is None and v17b["written_off"] == "504", "T6 once accepted: no short, 504 written off")
    v14 = sd.day_view(con, "2026-11-14")
    ok(v14["short"] is None if v14.get("entries") else v14["short"] == "5,580", "T7 14-Nov: no short when its entries explain it (short 5,580 before them)")
    v12 = sd.day_view(con, "2026-11-12")
    ok(v12["short"] is None, "T8 an ordinary day names no short")
    h = open(os.path.join(code, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
    ok(h.count("KIT_S874_HUB_SHORT_MOBILE_CALL") == 1 and h.count("s874Mob(") == 3 and "s874Call(" in h and "/portal/console/api/call" in h and "short</b>" in h,
       "T9 the page: the mobile renderer on bills and returns, the Call door, the short line")
    ok("window.confirm" not in h[h.find("KIT_S869"):h.find("end KIT_S869")], "T10 still no confirm dialog in the block")
except Exception as ex:                                        # noqa: BLE001
    import traceback; traceback.print_exc(); F += 1; print("FAIL the proof raised: %r" % (ex,))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("SYNTH S874: %d PASS, %d FAIL" % (P, F))
sys.exit(0 if F == 0 else 1)

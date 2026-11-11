#!/usr/bin/python3
# walk_s791.py -- kit S791_XRAY_MATCH_RULES (S430, 11-Nov-2026, the parent; D906). Usage:
#   walk_s791.py <dir holding check_screens.py, records.py, owner_console.py> <a finance.db copy> [--control]
# Works on SCRATCH copies of the database only; prints counts and ok/BAD lines, never a patient's name, number or clinic ID.
# Data-shaped checks (the 11-Nov copy's categories) run only when S791_SHAPE=1. Last line "WALK OK n/n" | "WALK RED k of n" | "CONTROL: ...".
import importlib, json, os, re, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
SHAPE = os.environ.get("S791_SHAPE") == "1"
T = tempfile.mkdtemp(prefix="s791w."); DB = os.path.join(T, "f.db")
os.environ["FINANCE_DB"] = DB
for p in [x for x in os.environ.get("S791_LIBS", "").split(os.pathsep) if x] + [K]:
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
RES = []


def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))


def fresh():
    shutil.copyfile(SRC, DB)
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    return c


R = CS = OC = None
try:
    R = importlib.import_module("records"); CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 check_screens and records from the kit dir", os.path.dirname(os.path.abspath(CS.__file__)) == K and
       os.path.dirname(os.path.abspath(R.__file__)) == K)
    ck("A2 it is S791 (the rules, the payment gaps)", str(getattr(CS, "VERSION", "")).startswith("S791") and hasattr(CS, "_s791_decide")
       and hasattr(CS, "pgap_items"))
except Exception as e:  # noqa: BLE001
    ck("A import", False, repr(e)[:160])
try:
    OC = importlib.import_module("owner_console")
    ck("A3 owner_console from the kit dir, with the payment-gap line", os.path.dirname(os.path.abspath(OC.__file__)) == K and hasattr(OC, "_s791_pgap_line"))
except Exception as e:  # noqa: BLE001
    ck("A3 owner_console import", False, repr(e)[:160])
src = open(os.path.join(K, "check_screens.py"), encoding="utf-8").read()
ck("A4 no patient name or clinic-ID-shaped number in check_screens.py (F-1264)",
   "(a made-up example)" in src and not re.search(r"\b[A-Z]{5,}\b[^\n]{0,60}(?<![\w\\-])\d{4}(?![\d-])", src))

if CS is not None and hasattr(CS, "_s791_decide"):
    con = fresh()
    P = CS._parked(con); G0 = len(CS._groups(P))
    n = CS.s787_auto(con)
    A = {r["key"][3:]: dict(r) for r in R._rows(con, "SELECT * FROM record_check WHERE key LIKE 'xf:%'")}
    rule = {}
    for r in P:
        a = A.get(r["src_id"]) or {}
        m = re.match(r"system · S791 ([A-G]):", str(a.get("answered_by") or ""))
        if m:
            rule.setdefault(m.group(1), []).append(r)
    ck("B1 the rules give (%d answers; %s)" % (n, " ".join("%s %d" % (k, len(v)) for k, v in sorted(rule.items()))),
       n >= (20 if SHAPE else 0))
    bad = []
    for k, rows in rule.items():
        for r in rows:
            a = A[r["src_id"]]
            fr = R._s772_film(con, r["src_id"]); day = fr[0][0] if fr and fr[0] else r["day"]
            ppl = CS._people(con, CS._d(day, -1), CS._d(day, 1), {})
            if k in "BACD":
                ok = a["answer"] == "id_fixed" and a["note"] in ppl
            elif k == "E":
                ok = a["answer"] == "id_fixed" and bool(R._rows(con, "SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? "
                                                                   "AND day>=? AND day<=? LIMIT 1", (a["note"], CS._d(day, -1), CS._d(day, 1))))
            elif k == "F":
                ok = a["answer"] == "id_fixed" and R._known_id(con, a["note"]) and a["note"] not in CS._people(con, CS._d(day, -7), CS._d(day, 7), {})
            else:
                toks = R._s752_tokens(R.xray_stem(r["orig_name"]))
                ok = a["answer"] == "no_docterz" and not a["note"] and not any(
                    R._s782_alike(toks, R._s752_tokens(x["name"])) for x in R._rows(con, "SELECT name FROM patient_ref WHERE name<>''"))
            if not ok:
                bad.append(k)
    ck("B2 each answer is what its rule says (B/A/C/D: a patient who came that day +-1; E: his photo filed then; F: registered, "
       "no visit that week; G: nobody in the patient list)", not bad, ",".join(bad))
    ck("B3 a second pass gives nothing more", CS.s787_auto(con) == 0)
    G1 = len(CS._groups(CS._parked(con)))
    if SHAPE:
        ck("B4 (the 11-Nov copy) every rule of the plan acts: B A C D F G -- and the photos left for a person are few (%d of %d groups)"
           % (G1, G0), all(rule.get(k) for k in "BACDFG") and G1 <= 9)
    # ---- the guards, each on a fresh copy with a MADE-UP patient (S791W*), never a real one
    def rerun_answer(sid):
        CS.s787_auto(c2)
        x = c2.execute("SELECT answer, answered_by FROM record_check WHERE key=?", ("xf:" + sid,)).fetchone()
        return (x[0], str(x[1])) if x else ("", "")

    def visitor(c, day, name, section="xray", cid="S791W1"):
        sn = (c.execute("SELECT MAX(sn) FROM clinic_day_line").fetchone()[0] or 0) + 1000
        c.execute("INSERT INTO clinic_day_line (business_date, section, sn, clinic_id, patient) VALUES (?,?,?,?,?)", (day, section, sn, cid, name))
        c.commit()

    def fday(c, r):
        fr = R._s772_film(c, r["src_id"])
        return fr[0][0] if fr and fr[0] else r["day"]
    for k, label in (("A", "S1 a second patient of that name who came that day -> rule A does not decide"),
                     ("C", "S1c a second X-ray patient of that name that day -> rule C does not decide"),
                     ("D", "S2 a second visitor with that first name -> rule D does not decide")):
        if rule.get(k):
            r = rule[k][0]; c2 = fresh()
            stem = R.xray_stem(r["orig_name"])
            visitor(c2, fday(c2, r), stem if k != "D" else stem + " SITARAMW")
            ck(label, not rerun_answer(r["src_id"])[1].startswith("system · S791 " + k)); c2.close()
    if rule.get("B"):
        r = rule["B"][0]; c2 = fresh()
        visitor(c2, fday(c2, r), R.xray_stem(r["orig_name"]))
        ck("S3 the name is another X-ray patient's who came -> rule B (the number) does not decide", not rerun_answer(r["src_id"])[1].startswith("system · S791 B"))
        c2.close()
    for k, label in (("F", "S4 a second registered patient of that name -> rule F does not decide"),
                     ("G", "S5 the name now in the patient list -> not marked 'not registered'")):
        if rule.get(k):
            r = rule[k][0]; c2 = fresh()
            c2.execute("INSERT INTO patient_ref (clinic_id, name) VALUES (?,?)", ("S791W2", R.xray_stem(r["orig_name"]))); c2.commit()
            got = rerun_answer(r["src_id"])
            ck(label, not got[1].startswith("system · S791 " + k) and got[0] != "no_docterz"); c2.close()
    # ---- the payment gaps (G): his console, his page, Shavez's list, the explanation
    pg = CS.pgap_items(con)
    ck("P1 every 'Not in Docterz' X-ray not explained is a possible payment gap; counts() carries them (%d)" % len(pg),
       CS.counts(con)["pgap"] == len(pg) and len(pg) == len(CS.xray_queue(con, nodz_only=True)) and (len(pg) >= 1 if SHAPE else True))
    if OC is not None:
        try:
            ln = OC._s791_pgap_line(con)
            ck("P2 his console's Needs-you: a RED line while one waits", (ln is not None and ln.get("dot") == "b") if pg else ln is None, ln)
        except Exception as e:  # noqa: BLE001
            ck("P2 his console's line", False, repr(e)[:150])
    if pg:
        it = pg[0]
        rc = CS.answer(con, {"user": "reception", "roles": ["maker"]}, {"key": "pg:" + it["sid"], "a": "explained", "why": "staff"})[0]
        rb = CS.answer(con, {"user": "shavez", "roles": ["maker"]}, {"key": "pg:" + it["sid"], "a": "explained", "why": "nonsense"})[0]
        r1 = CS.answer(con, {"user": "shavez", "roles": ["maker"]}, {"key": "pg:" + it["sid"], "a": "explained", "why": "family"})
        r2 = CS.answer(con, {"user": "manoj", "roles": ["checker"]}, {"key": "pg:" + it["sid"], "a": "explained", "why": "free"}, en=True)[0]
        left = CS.pgap_items(con)
        ck("P3 explained by Shavez (one tap): it leaves the gaps, stays on 'Not in Docterz' with the word; reception may not (403); "
           "a word not on the list is refused (400); a second answer finds it closed (409)",
           rc == 403 and rb == 400 and r1[0] == 200 and r2 == 409 and len(left) == len(pg) - 1 and
           any(i["sid"] == it["sid"] and "explained: family" in i["reason_en"] for i in CS.xray_queue(con, nodz_only=True)))
        known = next((A[r["src_id"]]["note"] for k in "BACDF" for r in rule.get(k, [])), "")   # any real ID will do on a scratch copy
        if left and known:
            r3 = CS.answer(con, {"user": "shavez", "roles": ["maker"]}, {"key": "xf:" + left[0]["sid"], "a": "id_fixed", "new_id": known})
            ck("P4 billed: given an ID once registered, it leaves the gaps", r3[0] == 200 and len(CS.pgap_items(con)) == len(left) - 1)
    # ---- rule F's X-ray on Shavez's list to bill, once the photo is filed
    if rule.get("F"):
        r = rule["F"][0]; cid = A[r["src_id"]]["note"]; day = r["day"]
        con.execute("INSERT INTO record_file (clinic_id, kind, day, drive_id, file_name, mime, bytes, source, source_ref, note, added_by, added_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (cid, "xray", day, "S791WALKDRIVEID00", "walk", "image/jpeg", 0, "xray_inbox",
                                                         r["src_id"], "", "walk", "2026-11-11 00:00:00"))
        con.commit()
        xb = [i for i in CS.xbill_items(con) if i["cid"] == cid and i["day"] == day]
        ok1 = len(xb) == 1 and "no slip and no Docterz" in xb[0]["note_en"]
        r4 = CS.answer(con, {"user": "shavez", "roles": ["maker"]}, {"key": xb[0]["key"], "a": "slip_made"})[0] if xb else 0
        ck("X1 rule F: once filed, the X-ray is on Shavez's list to bill by itself, and 'slip made' closes it",
           ok1 and r4 == 200 and not [i for i in CS.xbill_items(con) if i["cid"] == cid and i["day"] == day])
    # ---- records: a photo given an ID is filed on the film's X-ray day (a re-upload days later)
    moved = [r for k in "BACDE" for r in rule.get(k, []) if (lambda fr: fr and fr[0] and fr[0][0] != r["day"])(R._s772_film(con, r["src_id"]))]
    if moved:
        c2 = fresh(); CS.s787_auto(c2)
        rows = {x["src_id"]: dict(x) for x in R._rows(c2, "SELECT * FROM xray_filing WHERE state='check'")}

        def fake_list(fid):
            if fid != R.setting(c2, "xray_check_id"):
                return [], ""
            return [{"id": s, "name": x["orig_name"], "imageMediaMetadata": {"time": str(x["file_time"]).replace("-", ":", 2)[:19]}}
                    for s, x in rows.items() if x["file_time"]], ""
        R.drive_list, keep = fake_list, R.drive_list
        R._db = lambda: c2
        try:
            items, notes = R.xray_actions(c2)
            got = {x["src_id"]: x["day"] for x in R._rows(c2, "SELECT src_id, day FROM xray_filing WHERE state='planned'")}
            far = [r for r in moved if not R._s772_near(r["day"], R._s772_film(c2, r["src_id"])[0], 2)]   # uploaded days after the film
            ok = all(s["src_id"] in got and R._s772_near(got[s["src_id"]], R._s772_film(c2, s["src_id"])[0], 1)
                     and got[s["src_id"]] in R._s772_xray_days(c2, A[s["src_id"]]["note"]) for s in far
                     if R._s772_xray_days(c2, A[s["src_id"]]["note"]))
            ck("R1 a photo uploaded again days later is filed on his X-ray day by the film's date, not the upload's (%d)" % len(far),
               ok and (len(far) >= 1 if SHAPE else True))
        except Exception as e:  # noqa: BLE001
            ck("R1 the filing plan with the film's day", False, repr(e)[:160])
        R.drive_list = keep
        c2.close()
    # ---- the pages render (his page with the red tile; Shavez's with the gap card)
    try:
        import flask  # noqa: PLC0415
        app = flask.Flask("s791walk")
        R._db = lambda: con
        R._gate = lambda *a, **k: ({"user": "manoj", "roles": ["checker"]}, None)
        with app.test_request_context("/finance/records/xray-check?tab=nodz"):
            h = CS.owner_page().get_data(as_text=True)
        m = re.search(r"var B=(\{.*?\}), TAB=B\.tab", h, re.S)
        bo = json.loads(m.group(1)) if m else {}
        with app.test_request_context("/finance/checks"):
            hs = CS.staff_page(con, {"user": "shavez", "roles": ["maker"]}, []).get_data(as_text=True)
        ms = re.search(r"var B=(\{.*?\}), IT=B\.items", hs, re.S)
        bs = json.loads(ms.group(1)) if ms else {}
        ck("W1 his page: the 'Not in Docterz' tab, each item with its payment-gap flag; the red tile and the explain buttons are there",
           bo.get("tab") == "nodz" and all("pg" in i for i in bo.get("nodz", [])) and "possible payment gap" in h and 'data-pg="family"' in h)
        ck("W2 Shavez's Check karein carries the gaps as photo cards with the explain buttons",
           sum(1 for i in bs.get("items", []) if i.get("pg")) == len(CS.pgap_items(con)) and "data-pg=\"staff\"" in hs)
        for nm_, page in (("his", h), ("Shavez's", hs)):
            js = re.findall(r"<script>(.*?)</script>", page, re.S)
            p = os.path.join(T, "p.js"); open(p, "w", encoding="utf-8").write("\n".join(js))
            if shutil.which("node"):
                ok = os.system("node --check %s >/dev/null 2>&1" % p) == 0
                ck("W3 %s page's script parses (node --check)" % nm_, ok)
    except ImportError:
        print("-- flask not here: the page checks are skipped")
    except Exception as e:  # noqa: BLE001
        ck("W the pages", False, repr(e)[:160])
    con.close()
shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))

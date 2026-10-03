#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p4.py -- kit S454_BILL_REGISTER, part 4 (S454 10: the medical PC tells the owner when it refuses a file). THE REAL finance app over
SCRATCH COPIES of finance.db, assets.db and the spine (backup API), one process per side, the app served on 127.0.0.1 for the watcher:

  NEW  the box + part 4's door (marg_door) and part 4's watcher (marg_watch S454)
  OLD  the box as it is and the watcher as it is (S397) -- the NEGATIVE CONTROL
  D  the door: a note writes ONE refused row with the reason (verdict and pc_verdict REFUSED); the same file again adds nothing; a bad key is
     refused; a note that carries a file, or any key beyond {name, md5, kind, reason}, is refused and writes nothing
  O  who reads it: the owner's "Report refused today"; the reports tile (a refused sale, the due day's sale missing on the copy); Darpan's
     card "Order sheet adhoori thi" for a refused order sheet
  W  end to end: a scratch watcher keeps a cut-off order sheet as refused and its note reaches the door over HTTP, with the address and the
     key marg_push.py reads; nothing of the file's content is in the row; the watcher's and the reader's own selftests pass
  S  the staff-eye walk (DUTY_MAP v5)
Its rows are keyed W454P4; no phone number or key in its output.

  --fin-new DIR --fin-old DIR --watch-new DIR --watch-old DIR --por DIR --db PATH --adb PATH --spine PATH --work DIR --duty-map FILE
"""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import threading

USERS = {"reception": "staff", "darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor", "shivani": "staff"}
TAG = "W454P4JSON "


def mask(s):
    return re.sub(r"\+?\d[\d\s-]{8,}\d", lambda m: "#" * 10 if len(re.sub(r"\D", "", m.group(0))) >= 10 else m.group(0), str(s))


def text_of(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h or "", flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def probe():
    SIDE = os.environ["SIDE"]
    FIN, POR, WDIR = os.environ["FINDIR"], os.environ["PORDIR"], os.environ["WATCHDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import marg_ingest as MI                                           # noqa: E402 -- the door's own module (marg_door put its folder on the path)
    MI.DB_DEFAULT = os.environ["FINANCE_DB"]                           # the walk's scratch copy, never the live database
    assert MI.DB_DEFAULT.startswith("/tmp/"), MI.DB_DEFAULT
    import amir_day                                                    # noqa: E402
    import reports_tile                                                # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    TOK = os.environ["FINANCE_MARG_TOKEN"]
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    out = {}
    # ---------------------------------------------------------------- D  the door
    def note(body, tok=TOK, extra=None):
        h = {"X-Finance-Marg": tok, "X-Marg-Note": "refused"}
        if extra is None:
            r = fc.post("/finance/api/marg-file", base_url=BASE, headers=h, json=body)
        else:
            r = fc.post("/finance/api/marg-file", base_url=BASE, headers=h, data=extra, content_type="multipart/form-data")
        return r.status_code, (r.get_json(silent=True) or {}).get("status")

    def rows(md5):
        return [dict(r) for r in db.execute("SELECT md5, type, verdict, pc_verdict, pc_type, reason, drive_name, drive_folder, size, kept, lines, source "
                                            "FROM mi_file WHERE md5=?", (md5,))]
    M1 = hashlib.md5(b"W454P4 order " + SIDE.encode()).hexdigest()
    M2 = hashlib.md5(b"W454P4 bad key").hexdigest()
    M3 = hashlib.md5(b"W454P4 extra key").hexdigest()
    M4 = hashlib.md5(b"W454P4 sale").hexdigest()
    out["D1"] = [note(dict(name="report.txt", md5=M1, kind="ORDER", reason="an order sheet without the '*** End of Report ***' line at the end (cut short?)")), rows(M1)]
    out["D2"] = [note(dict(name="report.txt", md5=M1, kind="ORDER", reason="again")), len(rows(M1))]
    out["D3"] = [note(dict(name="x.txt", md5=M2, kind="SALE", reason="r"), tok="not-the-key"), len(rows(M2))]
    out["D4"] = [note(dict(name="x.txt", md5=M3, kind="SALE", reason="r", text="the file's own lines")), len(rows(M3))]
    import io
    out["D5"] = [note(None, extra={"f": (io.BytesIO(b"PENDING ORDERS (PURCHASE)"), "report.txt"), "md5": M3}), len(rows(M3))]
    # ---------------------------------------------------------------- O  who reads it
    out["O_owner"] = [l["text"] for l in amir_day._s444_refused_lines(db) if "medical PC refused" in l["text"]]
    r = fc.get("/finance/darpan/kal/api/day", base_url=BASE, headers={"X-Clinic-User": "darpan", "X-Clinic-Role": ""})   # the card is drawn from this JSON
    osh = ((r.get_json(silent=True) or {}).get("order_sheet") or {})
    out["O_darpan"] = dict(status=r.status_code, adhoori=bool(osh.get("refused")), refused=osh.get("refused"))
    today = reports_tile._today() if hasattr(reports_tile, "_today") else dt.date.today()
    y_iso = reports_tile._due_day(today).isoformat()
    db.execute("DELETE FROM mi_file WHERE type='SALE_BILLWISE' AND verdict='VERIFIED' AND date_from<=? AND date_to>=?", (y_iso, y_iso))
    try:
        db.execute("DELETE FROM marg_push_staging WHERE survey_json LIKE ?", ('%"' + y_iso + '"%',))
    except sqlite3.Error:
        pass
    db.commit()
    out["O_tile_before"] = (reports_tile.status(db, today)["rows"][0] or {}).get("state")
    note(dict(name="report.txt", md5=M4, kind="SALE", reason="a bill-wise report, but without the '*** End of Report ***' line at the end (cut short?)"))
    st = reports_tile.status(db, today)
    out["O_tile"] = dict(state=st["rows"][0].get("state"), reason=st["rows"][0].get("reason"), line=st["line"])
    # ---------------------------------------------------------------- W  end to end: the watcher on a scratch folder, the app on 127.0.0.1
    from werkzeug.serving import make_server                           # noqa: E402
    srv = make_server("127.0.0.1", 0, fa.app, threaded=True)
    port = srv.server_port
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["MARG_PUSH_URL"] = "http://127.0.0.1:%d/finance/api/marg-file" % port
    w = os.path.join(os.environ["WORKDIR"], "watch_" + SIDE)
    shutil.copytree(WDIR, w)
    with open(os.path.join(w, "token.txt"), "w") as fh:
        fh.write(TOK)
    sys.path.insert(0, w)
    import marg_watch as MW                                            # noqa: E402
    import marg_push as MP                                             # noqa: E402
    import marg_txt as MT                                              # noqa: E402
    assert MW.__file__.startswith(w) and MP.__file__.startswith(w), (MW.__file__, MP.__file__)
    out["W_url_from_push"] = MP.URL.startswith("http://127.0.0.1:")
    room = os.path.join(w, "margfolder")
    os.makedirs(room)
    raw = MT.ORDER_SAMPLE[:MT.ORDER_SAMPLE.rindex(b"***")]
    src = os.path.join(room, "report.txt")
    open(src, "wb").write(raw)
    msgs = []
    MW.capture_text(src, os.path.join(w, "_spool"), set(), msgs.append)
    for t in threading.enumerate():
        if t.name == "refusal_note":
            t.join(90)
    tm = hashlib.md5(raw).hexdigest()
    rw = rows(tm)
    lines = [l.strip() for l in raw.decode("latin-1").splitlines() if len(l.strip()) >= 12
             and not l.strip().startswith("***") and set(l.strip()) - set("-= ")]       # the report's own furniture is not content
    out["W"] = dict(msgs=[mask(m) for m in msgs], rows=rw, content=[l[:30] for l in lines if rw and any(l in str(v) for v in rw[0].values())])
    srv.shutdown()
    for k in ("marg_watch.py", "marg_txt.py"):
        p = subprocess.run([sys.executable, "-B", os.path.join(w, k), "--selftest"], cwd=w, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
        out["W_selftest_" + k] = dict(rc=p.returncode, last=p.stdout.strip().splitlines()[-1:] if p.stdout.strip() else [],
                                      s454=len([l for l in p.stdout.splitlines() if "S454" in l and l.strip().startswith("OK")]),
                                      n=len([l for l in p.stdout.splitlines() if re.match(r"^\s*(OK|ok)\s", l)]))
    out["S"] = staff_eye(fc, BASE)
    print(TAG + json.dumps(out, default=str))


def staff_eye(fc, BASE):
    import portal as po                                                # noqa: PLC0415
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W454J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("reception", "darpan", "shavez", "amir", "manoj"):
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r.get_data(as_text=True))]
        rows = []
        mine = {who, (dm.get("shared") or {}).get(who)}
        for du in dm.get("duties") or []:
            if du.get("person") not in mine:
                continue
            row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None}
            sql = str(du.get("due_sql") or "").strip().rstrip(";")
            n = None
            if sql:
                try:
                    rr = ro.execute(sql).fetchone()
                    n = int((rr[0] if rr else 0) or 0)
                except Exception as e:                             # noqa: BLE001
                    n = "ERR " + str(e)[:80]
            row["due_n"] = n
            door, mark = du.get("door"), du.get("door_marker")
            if door and mark and isinstance(n, int) and n > 0 and str(door).startswith("/finance/"):
                path, body = str(door), ""
                ck = "clinic_sso=" + tok + ("; clinic_who=shivani" if who == "reception" else "")
                for _hop in range(4):
                    rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
                    if rr2.status_code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                        path = rr2.headers["Location"].replace(BASE, "")
                        continue
                    body = rr2.get_data(as_text=True)
                    break
                row["door_seen"] = mark in body
            rows.append(row)
        eye[who] = dict(status=r.status_code, duties=rows)
    ro.close()
    return eye


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--watch-new", "--watch-old", "--por", "--db", "--adb", "--spine", "--work", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    for p in (a.work, a.por):
        assert p.startswith("/tmp/"), "refusing a non-scratch path: " + p
    os.makedirs(a.work, exist_ok=True)
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:700] + "]") if got is not None else ""))
        if not cond:
            fails.append(label)

    def copydb(src, dst):
        s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W454P4 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                    # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])
    wtok = "w454p4-" + secrets.token_hex(16)                                # the walk's own key, never the live one

    def run(side, fin, wdir):
        dbp, adbp, spp = [os.path.join(a.work, "w454p4_%s_%s.db" % (side, x)) for x in ("fin", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WATCHDIR=wdir, WORKDIR=a.work, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store,
                   TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, FINANCE_MARG_TOKEN=wtok,
                   ORDER_PUSH_STUB=os.path.join(a.work, "push_%s.jsonl" % side), DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, W454J=json.dumps(dict(pw=pw)),
                   PORDERS_SOURCE="tables")
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "MARG_PUSH_URL"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l).replace(wtok, "<walk key>")[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    N = run("new", a.fin_new, a.watch_new)
    O = run("old", a.fin_old, a.watch_old)
    check("both probes ran to the end (NEW = after part 4, OLD = the box and the watcher as they are)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S454P4 RED -- a probe did not finish")
        return 1
    print("-- D  the door")
    (c1, s1), r1 = N["D1"]
    check("a note writes ONE row: refused by the medical PC, ORDER_PENDING, with the reason, no file kept (%s %s)" % (c1, s1),
          c1 == 200 and s1 == "NOTED" and len(r1) == 1 and r1[0]["verdict"] == "REFUSED" and r1[0]["pc_verdict"] == "REFUSED" and r1[0]["type"] == "ORDER_PENDING"
          and r1[0]["reason"].startswith("the medical PC refused it: an order sheet without") and r1[0]["kept"] == 0 and r1[0]["size"] == 0, r1)
    check("the same file's note again adds nothing (%s, rows %d)" % (N["D2"][0], N["D2"][1]), N["D2"][0] == [200, "ALREADY"] and N["D2"][1] == 1, N["D2"])
    check("a bad key is refused and writes nothing (%s)" % N["D3"], N["D3"][0][0] == 401 and N["D3"][1] == 0, N["D3"])
    check("a note with a key beyond {name, md5, kind, reason} is refused and writes nothing (%s)" % N["D4"], N["D4"][0] == [400, "REFUSED"] and N["D4"][1] == 0, N["D4"])
    check("a note that carries a file is refused and writes nothing (%s)" % N["D5"], N["D5"][0] == [400, "REFUSED"] and N["D5"][1] == 0, N["D5"])
    check("NEGATIVE: the box as it is writes no row for a note (it takes it for a file with no name and refuses it): %s" % O["D1"][0],
          O["D1"][0][0] == 400 and not O["D1"][1], O["D1"])
    print("-- O  who reads it")
    check("the owner's Needs-you: '%s'" % ((N["O_owner"] or [""])[0][:150]), any("ORDER_PENDING" in t for t in N["O_owner"]), N["O_owner"])
    check("Darpan's card reads the refusal ('Order sheet adhoori thi'; the card's own data, /finance/darpan/kal/api/day)",
          N["O_darpan"]["status"] == 200 and N["O_darpan"]["adhoori"], N["O_darpan"])
    check("NEGATIVE: on the box as it is neither shows (no row was written)", not O["O_owner"] and not O["O_darpan"]["adhoori"], [O["O_owner"], O["O_darpan"]])
    check("the reports tile, the due day's sale missing on the copy: the sale row reads refused with the PC's reason ('%s')" % (N["O_tile"]["reason"] or "")[:90],
          N["O_tile"]["state"] == "refused" and "medical PC refused" in (N["O_tile"]["reason"] or "") and O["O_tile"]["state"] != "refused", [N["O_tile"], O["O_tile"]])
    print("-- W  end to end")
    W = N["W"]
    check("the watcher's own address and key are marg_push's (the walk's server, the walk's key in token.txt)", N["W_url_from_push"], N["W_url_from_push"])
    check("a cut-off order sheet kept as refused by the watcher reaches the door over HTTP: one row, ORDER, its reason", len(W["rows"]) == 1
          and W["rows"][0]["pc_type"] == "ORDER" and "order sheet without" in W["rows"][0]["reason"] and any("note: the server has the refusal" in m for m in W["msgs"]),
          W)
    check("nothing of the file's content is in the row", not W["content"], W["content"])
    check("NEGATIVE: the watcher as it is (S397) keeps it on the PC and nobody hears: no row", not O["W"]["rows"] and not any("note:" in m for m in O["W"]["msgs"]), O["W"])
    sw, st = N["W_selftest_marg_watch.py"], N["W_selftest_marg_txt.py"]
    check("the watcher's own selftest passes with its new checks (%d OK, %d of them S454's; the old one: %d OK)" % (sw["n"], sw["s454"], O["W_selftest_marg_watch.py"]["n"]),
          sw["rc"] == 0 and sw["s454"] == 6 and sw["n"] == O["W_selftest_marg_watch.py"]["n"] + 6, [sw, O["W_selftest_marg_watch.py"]])
    check("the reader's own selftest passes (%s)" % st["last"], st["rc"] == 0, st)
    print("-- S  the staff-eye walk (DUTY_MAP v5)")
    bad = []
    for who, v in N["S"].items():
        for d in v["duties"]:
            if d.get("tile") and d.get("tile_seen") is False:
                bad.append("%s tile %s" % (who, d["tile"]))
            if isinstance(d.get("due_n"), str):
                bad.append("%s %s: %s" % (who, d["id"], d["due_n"]))
            if d.get("door_seen") is False:
                bad.append("%s %s due but its marker is not on the door" % (who, d["id"]))
    check("every login's tiles on its home; every due duty's marker on its door", not bad, bad)
    print("WALK_S454P4 %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())

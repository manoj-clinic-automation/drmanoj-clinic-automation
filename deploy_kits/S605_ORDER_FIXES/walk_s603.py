#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s603.py -- kit S603_AMIR_CALENDAR_SAFE (20-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s603.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --por <scratch /root/portal copy:
                            every .py but portal_config.py, tile_grants.json -- the walk writes its OWN secret and user store into it>
                            --duty-map <the kit's DUTY_MAP.json (v16)> --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s603.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --por ... --duty-map ...
The real finance app (and, for the staff-eye home, the real portal) in one process: the walk's own header session for the finance pages and
its own portal sign-in (a random secret, its own user store -- never the live ones). Its own rows by key (W603 / w603 ...), never by
counting; the live rows by key (18-Oct's visit, the 18-10 09:37 start capture, the answered salts of 04-Oct). The spine COPY is never written
by the code under test (bytes compared); the walk's synthetic spines are second copies. No phone number is printed (ten digits masked).
Sections follow the brief's section 4: the page dumps (10) run FIRST on the quiet copy; --old-dump compares with the OLD files' dumps;
--expect-red is the negative control: the same walk on the OLD files, every 'C:' check must be red. Prints 'WALK OK S603 ...'.
S605 (F-957): section 1 lays its OWN visit day (45 days ahead: step-2 taps, a receipt, the step-3 tap, by key) -- the live 18-Oct replay
read Amir's real day, which his next export cleared on the server; the controls and their expectations are the same."""
import argparse
import datetime as dt
import hashlib
import html as _html
import io
import json
import os
import re
import secrets
import sqlite3
import sys
import time

KIT = "S603_AMIR_CALENDAR_SAFE"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
FOUR = ("amir_day.py", "stock_app.py", "stock_watch.py", "amir_salts.py")
PEND = "6d7180602f42fc203810c71a21a66ed6"                      # the 18-10 09:37 start capture (pending / pur_short at the brief)
MARKER = "Salt aur naye item: list kholiye, Marg mein sudhaar kijiye, tick lagaiye"
S603_TEXTS = ("never reached the server", "re-export owed", "waits for a purchase export taken after it", "waits for Amir's purchase export")
RUN, FAILS, CTRL, OUT = [0], [], [], []


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:900] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def section(title, fn):
    say("-- %s" % title)
    try:
        fn()
    except Exception as e:                                     # noqa: BLE001
        import traceback
        check("C: section %s ran without an exception" % title[:40], False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-900:]))


def text_lines(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"</(div|p|li|tr|h\d|button|a|td|th)>|<br\s*/?>", "\n", s)
    out = []
    for l in s.split("\n"):
        t = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", l))).strip()
        if t:
            out.append(t)
    return out


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def w603(s):
    return "w603" + hashlib.md5(("S603 " + s).encode()).hexdigest()[:28]


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def read(fin, name):
    return open(os.path.join(fin, name), encoding="utf-8").read()


def fn_body(src, name):
    m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|# -{10,}|[A-Z_]+ = )|\Z)" % re.escape(name), src, flags=re.S | re.M)
    return m.group(0) if m else ""


def stamp_of(iso):
    """'2026-10-20 08:00:00' -> '20261020-080000'."""
    t = str(iso)[:19].replace("T", " ")
    return t[0:4] + t[5:7] + t[8:10] + "-" + t[11:13] + t[14:16] + t[17:19]


def portal_setup(por):
    """The walk's OWN portal secret and user store in the scratch portal folder (S444's shape): never the live ones. Returns (secret, pw)."""
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W603 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w603-walk-seed'\n" % secret)
    sys.path.insert(0, por)
    import clinic_users                                        # noqa: E402
    store = os.path.join(por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for u, role in ROLE.items():
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
        clinic_users.add_user(store, u, role, pw[u])
    sys.path.remove(por)
    sys.modules.pop("clinic_users", None)
    return secret, pw, store


def app_env(a, dbp, token, secret=None, store=None):
    por = os.path.abspath(a.por) if a.por else os.path.join(os.path.dirname(dbp), "nosso")
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por, RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="",
                      FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token, CLINIC_PORTAL_DIR=por, PYTHONDONTWRITEBYTECODE="1")
    if secret:
        os.environ.update(CLINIC_SSO_SECRET=secret, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"))
    if a.duty_map:
        os.environ["DUTY_MAP_JSON"] = os.path.abspath(a.duty_map)
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "SARVAM_API_KEY"):
        os.environ.pop(k, None)


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import amir_day as AD                                     # noqa: E402
    import amir_salts as AS                                   # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    new = hasattr(AD, "_export_fact")
    say("STATE %s: files %s; amir_day KIT %s; clock %s IST" % (label, "NEW (S603)" if new else "OLD", AD.KIT, AD._now().strftime("%Y-%m-%d %H:%M:%S")))
    rows = [tuple(r) for r in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso",
                                          ((dt.date.today() - dt.timedelta(days=21)).isoformat(),))]
    S = AD.state(con, "2026-10-18", "amir")
    say("STATE %s: _reexport_due(2026-10-18) = %s; the day closed: %s; step 4 reads %s" % (label, (S.reexport_due, S.reexport_since), bool(S.closed), [(e["kind"], e["state"], e.get("reason")) for e in S.exports]))
    lines = AD.needs_you_lines(con)
    s603 = [l["text"] for l in lines if any(t in l["text"] for t in S603_TEXTS)]
    say("STATE %s: amir_day.needs_you_lines: %d line(s); the S603 export-wait line(s): %s" % (label, len(lines), s603 or "none"))
    for l in lines:
        say("   [%s] %s" % (l.get("cls"), l.get("text")))
    try:
        r = SA.readiness(con)
        say("STATE %s: readiness()['warnings']: %s" % (label, r.get("warnings")))
    except Exception as e:                                    # noqa: BLE001
        say("STATE %s: readiness() failed: %s" % (label, str(e)[:200]))
    sp = SW.Spine()
    scl = SW.start_capture_lines(con, sp)
    say("STATE %s: stock_watch.start_capture_lines: %s" % (label, [l["text"] for l in scl] or "none"))
    dm = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8")) if a.duty_map else {}
    d = [x for x in dm.get("duties") or [] if x["id"] == "amir.salt_tasks"]
    if d:
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        say("STATE %s: duty amir.salt_tasks (DUTY_MAP.json v%s) due_sql on the copy -> %s" % (label, dm.get("version"), tuple(ro.execute(d[0]["due_sql"]).fetchone())))
        ro.close()
    say("STATE %s: amir_salts: open tasks %d, waiting (tab 2) %d" % (label, len(AS._open_tasks(con)), len(AS._waiting(con))))
    rows2 = [tuple(r) for r in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso",
                                           ((dt.date.today() - dt.timedelta(days=21)).isoformat(),))]
    say("STATE %s: stock_start_capture rows within 21 days: %d; moved by the reads above (readiness, start_capture_lines, needs-you): %s" % (label, len(rows2), rows != rows2))
    for r in rows2:
        say("   %s printed %s taken %s -> end %s: %s%s (checked %s)" % (r[0][:8], r[1], r[2], r[3], r[4], (" / " + r[5]) if r[5] else "", r[6]))
    con.rollback()
    con.close()
    say("STATE OK S603 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--por", "--duty-map"):
        ap.add_argument(k, default="")
    for k in ("--dump", "--old-dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    for k in ("fin", "db", "adb", "marg"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k)
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S603_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)) + ((os.path.abspath(a.por),) if a.por else ()):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump or not a.por or not a.duty_map:
        ap.error("--dump, --por and --duty-map are needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S603 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    secret, pw, store = portal_setup(os.path.abspath(a.por))
    app_env(a, dbp, token, secret, store)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import amir_day as AD                                     # noqa: E402
    import amir_salts as AS                                   # noqa: E402
    import padreader as PR                                    # noqa: E402
    import padwriter as PW                                    # noqa: E402
    for m in (fa, SA, SW, SF, AD, AS):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(AD, "_export_fact")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; amir_day KIT %s (%s); stock_figure %s %s"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", AD.KIT, "NEW" if NEW else "OLD", SF.VERSION, SF.KIT))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    spine_md5_0 = hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest()
    SRC = {n: read(fin, n) for n in FOUR}
    today = dt.date.today()
    TODAY = today.isoformat()
    NOW = AD._now().replace(tzinfo=None, microsecond=0)
    SIDE = "old" if a.expect_red else "new"
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    DM = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8"))
    DUTY = [x for x in DM.get("duties") or [] if x["id"] == "amir.salt_tasks"]
    DUTY = DUTY[0] if DUTY else None

    def GET(u, path, follow=False, role=None):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": role or ROLE[u]}, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def conn(path=None):
        c = sqlite3.connect(path or dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def T(minutes, base=None):
        return ((base or NOW) + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")

    def caprows(c):
        return [tuple(r) for r in c.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at, built, n_keys, detail FROM stock_start_capture ORDER BY md5")]

    def cleanup(c):
        c.execute("DELETE FROM amir_step_log WHERE by_user='w603walk'")
        c.execute("DELETE FROM mi_file WHERE md5 LIKE 'w603%'")
        c.execute("DELETE FROM purchase_export WHERE md5 LIKE 'w603%'")
        c.execute("DELETE FROM purchase_salt_task WHERE a LIKE 'W603 %'")
        c.commit()

    def tap(c, day, step, at, note=None):
        return ins(c, "amir_step_log", dict(day=day, step=step, done_at=at, by_user="w603walk", note=note))

    def receipt_mi(c, key, at, typ="PURCHASE_BILLWISE"):
        return ins(c, "mi_file", dict(md5=w603(key), type=typ, verdict="VERIFIED", received_at=at.replace(" ", "T") + "+05:30", stamp=stamp_of(at),
                                      date_from=at[:8] + "01", date_to=at[:10], drive_name="W603 " + key, reason="W603 walk"))

    def receipt_pe(c, key, at, typ="BILLWISE", pf=None, pt=None, stamp=None):
        return ins(c, "purchase_export", dict(md5=w603(key), type=typ, file="W603_" + key, period_from=pf or (at[:8] + "01"), period_to=pt or at[:10],
                                              export_stamp=stamp or stamp_of(at), received_at=at.replace(" ", "T"), n_rows=1, grand_amount_p=0))

    sw0 = SW.Spine()
    assert sw0.ok and SW.SPINE_DB == SPINE_PATH, (sw0.ok, SW.SPINE_DB)
    with conn() as c_:
        real_rows = {t: c_.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("amir_step_log", "mi_file", "purchase_export", "purchase_salt_task")}
        cleanup(c_)
    say("   today %s, now %s; the copy's rows: %s" % (TODAY, NOW, real_rows))

    # ============================================================================================ 10 (first): the pages and the APIs dumped on the quiet copy
    def s10():
        pages = [("amir", "/finance/amir", True)] + [("amir", "/finance/amir/step/%d" % n, False) for n in range(1, 8)] + [
                 ("amir", "/finance/amir/salts", False), ("manoj", "/finance/amir/day", False),
                 ("shavez", "/finance/reports/aaj", True), ("darpan", "/finance/darpan/kal", True), ("darpan", "/finance/darpan/kal/api/day", False),
                 ("reception", "/finance/porders", True), ("manoj", "/finance/stock/api/readiness", False), ("manoj", "/finance/stock/api/now", False),
                 ("manoj", "/finance/sanjeevni/api/needs-you", False)]
        changed, got = {}, {}
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "date", "yesterday_date", "ours_at", "stored_at", "stored_text", "readiness", "cache",
                                  "refresh_ms", "watch", "now", "server_time", "user", "as_of", "today"):
                            j.pop(k, None)
                        if path.endswith("/api/readiness"):
                            got["warnings"] = list(j.get("warnings") or [])
                            j["warnings"] = [w for w in j.get("warnings") or [] if not (w.startswith("Purchases are") or w.startswith("No purchase export has been taken") or w.startswith("The stock figure is for"))]
                        if path.endswith("/api/needs-you") and isinstance(j.get("lines"), list):
                            got["needs"] = [l.get("text") for l in j["lines"] if any(t in str(l.get("text")) for t in S603_TEXTS)]
                            j["lines"] = [l for l in j["lines"] if not any(t in str(l.get("text")) for t in S603_TEXTS)]
                            j.pop("count", None)                       # the count of lines moves with the masked lines
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                if old != lines:
                    os_, ns = set(old), set(lines)
                    gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                    changed[(u, path)] = (gone, new)
                    say("   CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:6]:
                        say("      - %s" % l[:240])
                    for l in new[:6]:
                        say("      + %s" % l[:240])
                else:
                    say("   unchanged on %s for %s" % (path, u))
        say("   api/readiness warnings as served: %s" % got.get("warnings"))
        say("   needs-you S603 / pending-capture lines as served: %s" % (got.get("needs") or "none"))
        DUMP["s10"] = got
        if a.old_dump:
            check("every page dump (Amir's seven steps and salts page on a quiet day, the owner's amir/day, Shavez's, Darpan's, reception's pages, stock-now) and the APIs "
                  "(api/day; api/readiness with the purchase sentences masked; needs-you with the S603 lines masked) are byte-equal to the OLD files' dumps (%d differ)" % len(changed),
                  not changed, {k: (v[0][:3], v[1][:3]) for k, v in changed.items()})
    section("10 (first) the pages and the APIs dumped on the quiet copy -- byte-equal OLD vs NEW but the masked sentences", s10)

    # ============================================================================================ 1 F-952: the band clears on the fact
    def s1():
        c = conn()
        # S605 (F-957): the walk's OWN visit day in place of the live 18-Oct -- 18-Oct's shape: bills keyed, the pair received, a bill keyed
        # after it (09:35:24), 'Dono report nikaal di' tapped (09:37:53) and no file after it
        R = (today + dt.timedelta(days=43)).isoformat()
        tap(c, R, 2, R + " 09:10:00")
        receipt_mi(c, "mi-R-first", R + " 09:20:00")
        receipt_pe(c, "pe-R-first", R + " 09:20:30")
        tap(c, R, 2, R + " 09:35:24")
        tap(c, R, 3, R + " 09:37:53", "export")
        c.commit()
        S = AD.state(c, R, "amir")
        ticks = S.ticks
        due0 = AD._reexport_due(c, R, ticks)
        say("   the walk's own visit day %s on the copy: taps %s; _reexport_due -> %s" % (R, {k: v["done_at"] for k, v in sorted(ticks.items())}, due0))
        check("C: (1) the 18-Oct replay: _reexport_due is (True, '%s 09:35:24') -- his step-3 tap of 09:37:53 clears nothing, no file came after 09:35:24" % R,
              tuple(due0) == (True, R + " 09:35:24"), due0)
        R2 = (today + dt.timedelta(days=44)).isoformat()
        receipt_mi(c, "mi-R-next", R2 + " 09:00:00")
        due1 = AD._reexport_due(c, R, ticks)
        c.execute("DELETE FROM mi_file WHERE md5=?", (w603("mi-R-next"),))
        receipt_pe(c, "pe-R-next", R2 + " 09:00:00")
        due2 = AD._reexport_due(c, R, ticks)
        c.execute("DELETE FROM purchase_export WHERE md5=?", (w603("pe-R-next"),))
        c.commit()
        say("   with a synthetic mi_file PURCHASE_BILLWISE receipt of %s 09:00 -> %s; with a synthetic purchase_export BILLWISE receipt instead -> %s" % (R2, due1, due2))
        check("C: (1) a VERIFIED mi_file receipt of ANOTHER day (%s) after T2 clears the band (True -> False): the same-day cut is gone" % R2, due0[0] is True and due1[0] is False, (due0, due1))
        check("C: (1) a purchase_export receipt after T2 clears it too (the pusher's receipt is a receipt)", due0[0] is True and due2[0] is False, (due0, due2))
        cleanup(c)
        # the morning case (R1-B1): a synthetic day far in the future
        D = (today + dt.timedelta(days=45)).isoformat()
        base = dt.datetime(int(D[:4]), int(D[5:7]), int(D[8:10]), 10, 0, 0)
        tap(c, D, 2, T(0, base))
        c.commit()
        tk = {2: dict(done_at=T(0, base))}
        m0 = AD._reexport_due(c, D, tk)
        receipt_mi(c, "mi-morning", T(4, base))
        tap(c, D, 2, T(10, base))
        tap(c, D, 3, T(12, base), "export")
        c.commit()
        tk = {2: dict(done_at=T(10, base)), 3: dict(done_at=T(12, base))}
        m1 = AD._reexport_due(c, D, tk)
        say("   the morning case (synthetic day %s): one step-2 tap at 10:00, nothing after -> %s; exports received 10:04, step 2 again 10:10, step 3 10:12 -> %s" % (D, m0, m1))
        check("(1) R1-B1: before the visit's first file nothing is expected -- (False, None)", tuple(m0) == (False, None), m0)
        check("C: (1) a bill entered after the file landed, then 'nikaal di' tapped: due (True) -- the step-3 tap is no mark", m1[0] is True and m1[1] == T(10, base), m1)
        cleanup(c)
        c.close()
        DUMP["s1"] = dict(due0=list(due0), due1=list(due1), due2=list(due2), m0=list(m0), m1=list(m1))
    section("1  F-952: the 18-Oct replay; a receipt of another day clears; the morning case", s1)

    # ============================================================================================ 2 the covering export
    def s2():
        c = conn()
        D = (today + dt.timedelta(days=47)).isoformat()
        first = D[:8] + "01"
        pm_last = (dt.date(int(D[:4]), int(D[5:7]), 1) - dt.timedelta(days=1))
        pm_first = pm_last.replace(day=1)
        for kind in ("ITEMWISE", "BILLWISE"):
            receipt_pe(c, "A-" + kind, D + " 09:00:00", kind, pf=first, pt=D, stamp=stamp_of(D + " 09:00:00"))
            receipt_pe(c, "B-" + kind, D + " 09:05:00", kind, pf=pm_first.isoformat(), pt=pm_last.isoformat(), stamp=stamp_of(D + " 09:05:00"))
        c.commit()
        ex = AD._export_state(c, D, None)
        say("   synthetic day %s: two live rows per family -- A = %s..%s (stamp 09:00), B = %s..%s (stamp 09:05, the newer) -> %s"
            % (D, first, D, pm_first, pm_last, [(e["kind"], e["state"], e.get("reason"), e.get("period")) for e in ex]))
        check("C: (2) step 4 takes the COVERING export (A) for both families -- ok, though B is the newer", all(e["state"] == "ok" for e in ex) and all(str(e.get("period", "")).startswith("01-") for e in ex),
              [(e["kind"], e["state"], e.get("reason")) for e in ex])
        c.execute("DELETE FROM purchase_export WHERE md5 IN (?,?)", (w603("A-ITEMWISE"), w603("A-BILLWISE")))
        c.commit()
        ex2 = AD._export_state(c, D, None)
        check("(2) with the non-covering export alone, both families read bad ('tareekh galat hai') -- on OLD and NEW", all(e["state"] == "bad" and "tareekh" in e.get("reason", "") for e in ex2),
              [(e["kind"], e["state"], e.get("reason")) for e in ex2])
        ex1 = AD._export_state(c, "2026-10-01", None)
        say("   the real 2026-10-01 rows as they stand (printed, not asserted; R1-C6: its 1-Oct ITEMWISE rows are superseded): %s" % [(e["kind"], e["state"], e.get("reason")) for e in ex1])
        cleanup(c)
        c.close()
        DUMP["s2"] = dict(ex=[(e["kind"], e["state"]) for e in ex], ex2=[(e["kind"], e["state"]) for e in ex2], ex1=[(e["kind"], e["state"]) for e in ex1])
    section("2  step 4 reads the covering export first, then the newest", s2)

    # ============================================================================================ 3 since when
    def s3():
        c = conn()
        D = (today + dt.timedelta(days=49)).isoformat()
        t3 = T(-10)
        tap(c, D, 2, T(-12))
        tap(c, D, 3, t3, "export")
        c.commit()
        ex = AD._export_state(c, D, t3)
        hhmm = t3[11:16]
        say("   synthetic day %s: step-3 tap at %s (10 min ago), no export -> %s" % (D, t3, [(e["kind"], e["state"], e.get("reason"), e.get("since")) for e in ex]))
        check("C: (3) the pair that did not arrive reads bad with 'hh:mm baje se nahi aayi' and since = his tap's hh:mm",
              all(e["state"] == "bad" and e.get("reason") == "%s baje se nahi aayi" % hhmm and e.get("since") == hhmm for e in ex), [(e["state"], e.get("reason"), e.get("since")) for e in ex])
        saved = AD._today
        AD._today = lambda: D
        try:
            s, h = GET("amir", "/finance/amir/step/4")
            lines = text_lines(h)
            head = [l for l in lines if "mein dikkat hai" in l]
            say("   /finance/amir/step/4 as amir (%s) on that day: head %s" % (s, head[:1]))
            check("C: (3) the step-4 head rendered as the walk's amir session carries the hh:mm ('%s baje se nahi aayi')" % hhmm, s == 200 and any("%s baje se nahi aayi" % hhmm in l for l in head), head[:2])
            # the wait state: a tap 2 minutes ago renders byte-equal OLD vs NEW
            D5 = (today + dt.timedelta(days=51)).isoformat()
            tap(c, D5, 2, T(-3))
            tap(c, D5, 3, T(-2), "export")
            c.commit()
            AD._today = lambda: D5
            s5, h5 = GET("amir", "/finance/amir/step/4")
            w = [re.sub(r"\d+ min", "N min", re.sub(r"\d{2}:\d{2}(:\d{2})?", "HH:MM", l)) for l in text_lines(h5)]
            say("   the wait state (tap 2 min ago): %s, %d lines, head %s" % (s5, len(w), [l for l in w if "aa rahi hai" in l][:1]))
            DUMP["s3"] = dict(wait=w)
            check("(3) the wait state renders 'Report aa rahi hai'", s5 == 200 and any("Report aa rahi hai" in l for l in w))
            if OLD.get("s3"):
                check("(3) the wait state's page is byte-equal OLD vs NEW (times masked)", OLD["s3"]["wait"] == w, [l for l in w if l not in OLD["s3"]["wait"]][:3])
        finally:
            AD._today = saved
        cleanup(c)
        c.close()
    section("3  since when: the bad pair's reason and the step-4 head; the wait state unchanged", s3)

    # ============================================================================================ 4 the owner's 48-hour line
    def s4():
        c = conn()
        lines0 = AD.needs_you_lines(c)
        s0 = [l["text"] for l in lines0 if any(t in l["text"] for t in S603_TEXTS)]
        say("   on the copy as it stands (clock %s): the S603 line(s): %s (the 18-Oct one appears from 09:37:53 IST 20-Oct; printed, not asserted)" % (NOW, s0 or "none"))
        newest = c.execute("SELECT MAX(x) FROM (SELECT MAX(substr(replace(received_at,'T',' '),1,19)) AS x FROM mi_file WHERE verdict='VERIFIED' AND type LIKE 'PURCHASE_%' "
                           "UNION ALL SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM purchase_export)").fetchone()[0]
        lo = (dt.datetime.strptime(newest, "%Y-%m-%d %H:%M:%S") + dt.timedelta(minutes=1))
        LO = lo.strftime("%Y-%m-%d %H:%M:%S")
        wait_h = AD._setting(c, "amir.proof_wait_hours")
        old_t3, young_t3 = T(-(wait_h + 2) * 60), T(-10 * 60)
        say("   the synthetic open days: first step-2 tap at %s (after the newest real receipt %s); step-3 taps %d h ago (%s) / 10 h ago (%s); amir.proof_wait_hours = %d"
            % (LO, newest, wait_h + 2, old_t3, young_t3, wait_h))
        days = {k: (today - dt.timedelta(days=n)).isoformat() for k, n in (("i", 3), ("ii", 4), ("iii", 6), ("iv", 7), ("v", 1))}
        for k, D in days.items():
            if c.execute("SELECT 1 FROM amir_step_log WHERE day=? AND by_user<>'w603walk'", (D,)).fetchone():
                say("   (day %s has real rows -- the walk's %s case shares it)" % (D, k))
        dd = {k: AD._dm_hm(v, time=False) for k, v in days.items()}
        # ONE fact for all days (a receipt is a receipt, whatever day's visit it answers): each case is laid and read on its own, the copy
        # cleaned between them; the moments are staggered so that no case's receipt answers another's visit when two are laid together
        def lines_for(label):
            fn = getattr(AD, "_s603_export_lines", None)
            out = [l["text"] for l in fn(c)] if fn else []
            say("   %s -> %s" % (label, out or "no line"))
            return out
        tap(c, days["i"], 2, T(20, lo))
        tap(c, days["i"], 3, old_t3, "export")
        c.commit()
        li = lines_for("(i) %s: first tap %s, step 3 %s, no receipt after the tap" % (dd["i"], T(20, lo), old_t3))
        exp_i = "Amir's purchase export of %s never reached the server — he tapped 'nikaal di' at %s; the day stays open until the pair lands (Amir)" % (dd["i"], AD._dm_hm(old_t3))
        check("C: (4 i) step-3 tap %d h ago, no receipt after the first bill-entry tap -> the 'never reached the server' line, verbatim" % (wait_h + 2), li == [exp_i], li)
        cleanup(c)
        tap(c, days["ii"], 2, LO)
        receipt_mi(c, "ii-fact", T(2, lo))
        tap(c, days["ii"], 2, T(5, lo))
        tap(c, days["ii"], 3, old_t3, "export")
        c.commit()
        lii = lines_for("(ii) %s: first tap %s, a receipt %s, a step-2 tap %s, step 3 %s" % (dd["ii"], LO, T(2, lo), T(5, lo), old_t3))
        exp_ii = "Amir entered a bill at %s on %s after that day's export and no purchase export has landed since — re-export owed (Amir)" % (T(5, lo)[11:16], dd["ii"])
        check("C: (4 ii) a receipt after lo, a step-2 tap after it, step 3 %d h ago -> the 're-export owed' line, verbatim" % (wait_h + 2), lii == [exp_ii], lii)
        cleanup(c)
        tap(c, days["iii"], 2, LO)
        receipt_mi(c, "iii-fact", T(2, lo), "PURCHASE_ITEMWISE")
        tap(c, days["iii"], 2, T(5, lo))
        receipt_pe(c, "iii-after", T(7, lo))
        tap(c, days["iii"], 3, old_t3, "export")
        c.commit()
        liii = lines_for("(iii) %s: as (ii) with a purchase_export receipt %s after the last step-2 tap" % (dd["iii"], T(7, lo)))
        check("(4 iii) a receipt after the last step-2 tap -> no line (NEW; OLD has none)", not liii, liii)
        cleanup(c)
        tap(c, days["iv"], 2, LO)
        tap(c, days["iv"], 3, young_t3, "export")
        c.commit()
        liv = lines_for("(iv) %s: as (i) with the step-3 tap only 10 h ago (%s)" % (dd["iv"], young_t3))
        check("(4 iv) the tap only 10 h ago -> no line", not liv, liv)
        cleanup(c)
        tap(c, days["v"], 2, LO)
        tap(c, days["v"], 3, old_t3, "export")
        tap(c, days["v"], 7, T(-60), "close")
        c.commit()
        lv = lines_for("(v) %s: as (i) but the day closed (a step-7 close row)" % dd["v"])
        check("(4 v) the day closed -> no line", not lv, lv)
        cleanup(c)
        lvi = lines_for("(vi) the real 2026-10-15 (closed; its pair superseded by the 16-Oct export; R1-B2) and 18-Oct as they stand")
        check("(4 vi) no line names 15-10", not any("15-10" in t for t in lvi), lvi)
        # the two lines reach the owner's list (needs_you_lines), laid together: (i)'s first tap after (ii)'s receipt, so one fact serves both
        tap(c, days["ii"], 2, LO)
        receipt_mi(c, "ii-fact", T(2, lo))
        tap(c, days["ii"], 2, T(5, lo))
        tap(c, days["ii"], 3, old_t3, "export")
        tap(c, days["i"], 2, T(20, lo))
        tap(c, days["i"], 3, old_t3, "export")
        c.commit()
        lines = AD.needs_you_lines(c)
        s603 = [l["text"] for l in lines if any(t in l["text"] for t in S603_TEXTS[:2])]
        for t in s603:
            say("   needs-you + %s" % t)
        mine = [t for t in s603 if dd["i"] in t or dd["ii"] in t]
        check("C: (4) both lines reach the owner's Needs-you list (needs_you_lines), in English, each naming Amir; no run of ten digits",
              sorted(mine) == sorted([exp_i, exp_ii]) and all(not re.search(r"\d{10}", t) for t in s603), s603)
        cleanup(c)
        c.close()
        DUMP["s4"] = dict(s0=s0, s603=s603)
    section("4  the owner's line after amir.proof_wait_hours: never reached / re-export owed; silent otherwise", s4)

    # ============================================================================================ 5 F-786: absent
    def s5():
        c = conn()
        sp = SW.Spine()
        root = SA._s446_root(c)
        ent = SA._s446_entered(c, root)
        batches = SA._s446_batches(c, root)
        win = SA._s446_window(c, root)
        at_of = {k: str(win.get(k) or v[1] or "") for k, v in ent.items()}
        first_at = min(at_of.values())[:19]
        last_at = max(at_of.values())[:19]
        T0 = SA._s524_table(c, sp, root, ent, batches, first_at, last_at, at_of)
        say("   root %s: R %s, after %s, tries %s, N %s (N_ok %s, short %r)" % (root, T0["R"] and (T0["R"]["as_on"], T0["R"]["stamp"]), [(x["as_on"], x["stamp"]) for x in T0["after"]],
                                                                             len(T0["tries"]), T0["N"] and T0["N"]["as_on"], T0["N_ok"], T0["N_short"]))
        kof = T0["kof"]
        # a batch whose every key is proven, in the window
        pick = None
        for kb in sorted(k for k in batches if k in ent):
            items = [it for it, _ch, _m in batches[kb]["lines"]]
            if items and all((T0["keys"].get(kof.get(it)) or {}).get("proven") for it in items):
                pick = kb
                break
        check("a batch of the real count whose every item is proven exists (the walk's subject)", pick is not None, len(T0["keys"]))
        X = [it for it, _ch, _m in batches[pick]["lines"]][0]
        kX = kof[X]
        tries_md5 = [x["md5"] for x in T0["after"]]
        say("   the subject: batch %s, item %s (key %s); its printed rows removed from %d capture(s) after the vouchers on a SECOND spine copy" % (SA._s446_key(pick), X, kX, len(tries_md5)))
        absent_db = os.path.join(os.path.dirname(dbp), "spine_absent_%s.db" % SIDE)
        copy_db(SPINE_PATH, absent_db)
        e = sqlite3.connect(absent_db)
        n_del = e.execute("DELETE FROM sp_close_name WHERE k20=? AND md5 IN (%s)" % ",".join("?" * len(tries_md5)), [kX] + tries_md5).rowcount
        e.commit()
        e.close()
        say("   %d sp_close_name row(s) of that key removed on the copy" % n_del)
        SW.SPINE_DB = absent_db
        try:
            sp2 = SW.Spine()
            T2 = SA._s524_table(c, sp2, root, ent, batches, first_at, last_at, at_of)
            V = SA._s524_verdict(c, sp2, T2, [pick], batches, last_at)
            kinds = [(u.get("item"), u.get("why")) for u in V.get("unseen") or []]
            ending = AD._s488_ending(V)
            say("   _s524_verdict for that batch: state %s why %s unseen %s rows %d absent %s" % (V.get("state"), V.get("why"), kinds, len(V.get("rows") or []), V.get("absent")))
            say("   _s488_ending: %r" % ending)
            check("C: (5) F-786: the proof reads state export, why 'absent', absent = [%s] -- every unseen row absent_at_try, a clean closing came, its purchase half not short" % X,
                  V.get("state") == "export" and V.get("why") == "absent" and V.get("absent") == [X] and kinds == [(X, "absent_at_try")], (V.get("state"), V.get("why"), V.get("absent"), kinds))
            check("C: (5) the owner's ending says 'not printed under their name' and names the item", "not printed under their name" in ending and X in ending, ending)
            check("C: (5) stock_app._s524_english_ending reads the same words", SA._s524_english_ending(V) == ending and "not printed" in ending, SA._s524_english_ending(V)[:120])
            # the direct rules: a mixed set and absent_before stay no_figure; the real pur_short lot stays pur_behind
            kw = dict(unseen=[dict(item=X, why="absent_at_try"), dict(item="Y", why="no_verdict")]) if NEW else {}
            mixed = SA._s488_why(c, sp2, T2["closings"], T2["R"], T2["after"], last_at, **kw).get("why")
            kw = dict(unseen=[dict(item=X, why="absent_before")]) if NEW else {}
            before = SA._s488_why(c, sp2, T2["closings"], T2["R"], T2["after"], last_at, **kw).get("why")
            say("   _s488_why with a mixed unseen set (absent_at_try + no_verdict): %s; with one absent_before: %s" % (mixed, before))
            check("(5) a mixed unseen set -> no_figure (OLD and NEW)", mixed == "no_figure", mixed)
            check("(5) one absent_before -> no_figure (OLD and NEW: R lacked the key, not this reason)", before == "no_figure", before)
        finally:
            SW.SPINE_DB = SPINE_PATH
        st = SA.amir_stage(c, root)
        pr = SA._s488_stage_proof(st) or {}
        say("   the live stage on the copy: %s; its proof why %s (closing %s %s)" % ((st or {}).get("stage"), pr.get("why"), pr.get("closing_day"), pr.get("closing_at")))
        DUMP["s5"] = dict(stage=(st or {}).get("stage"), why=pr.get("why"), X=X, mixed=mixed, before=before)
        if OLD.get("s5"):
            check("(5) the live proof's reason equals the OLD files' (%s) -- a pur_short closing stays pur_behind on both" % pr.get("why"), OLD["s5"]["why"] == pr.get("why"), (OLD["s5"]["why"], pr.get("why")))
        c.close()
    section("5  F-786: an item Marg's closing does not print -> 'absent'; mixed / absent_before / pur_short unchanged", s5)

    # ============================================================================================ 6 F-769 / F-953: readiness
    def s6():
        c = conn()
        sp = SW.Spine()
        cap = SF.capture_at(sp, None, SF.Ctx(c, sp, read_only=True) if NEW else SF.Ctx(None, sp))
        how = SF.purchase_cover_how(c, sp, cap, SF.reach(sp), SF.Ctx(c, sp, read_only=True) if NEW else SF.Ctx(None, sp)) if cap else "no capture"
        say("   the newest usable capture: printed %s taken %s -> end %s; purchase_cover_how = %r" % (cap["as_on"], cap["stamp_iso"], cap["end_day"], how))
        time.sleep(1.2)                                        # checked_at has second resolution: a judge write inside readiness() must show
        rows0 = caprows(c)
        r = SA.readiness(c)
        stk = SA._r_stock(c)
        rows1 = caprows(c)
        W = r.get("warnings") or []
        say("   readiness()['warnings']: %s" % W)
        say("   stock_start_capture rows moved by readiness() + _r_stock(): %s" % (rows0 != rows1))
        for x, y in zip(rows0, rows1):
            if x != y:
                say("      %s: checked %s -> %s, verdict %s -> %s" % (x[0][:8], x[6], y[6], x[4], y[4]))
        check("C: (6) F-769: no purchase 'days behind' sentence in readiness()['warnings']", not any(w.startswith("Purchases are") for w in W), W)
        stock_ahead = [w for w in W if w.startswith("No purchase export has been taken since") or w.startswith("The stock figure is for")]
        check("C: (6) the stock-ahead sentence follows purchase_cover_how of the newest usable capture (how %r -> %s)" % (how, "one sentence" if how is None else "no sentence"),
              NEW and (len(stock_ahead) == (1 if how is None else 0)) and all(w.startswith("No purchase export has been taken since") for w in stock_ahead), stock_ahead)
        check("C: (6) F-953: the judge did not run -- the stock_start_capture rows are byte-equal before and after readiness() and _r_stock()", rows0 == rows1,
              [(x[0][:8], x[6], y[6]) for x, y in zip(rows0, rows1) if x != y])
        check("(6) the sale 'days behind' sentence stays as it was (%s)" % any(w.startswith("The sale report is") for w in W), True)
        # the forced case: no purchase export in the spine after the capture AND no visit cover
        nopur = os.path.join(os.path.dirname(dbp), "spine_nopur_%s.db" % SIDE)
        copy_db(SPINE_PATH, nopur)
        e = sqlite3.connect(nopur)
        n = e.execute("DELETE FROM sp_export WHERE family LIKE 'PURCHASE_%'").rowcount
        e.commit()
        e.close()
        db2 = os.path.join(os.path.dirname(dbp), "f_nopur_%s.db" % SIDE)
        copy_db(dbp, db2)
        c2 = conn(db2)
        V = str(cap["stamp_iso"])[:10]
        vd = c2.execute("SELECT MAX(day) FROM amir_day WHERE day<=?", (V,)).fetchone()[0]
        n2 = c2.execute("DELETE FROM amir_step_log WHERE step=2 AND day=?", (vd,)).rowcount
        c2.commit()
        SW.SPINE_DB = nopur
        try:
            r2 = SA.readiness(c2)
        finally:
            SW.SPINE_DB = SPINE_PATH
        W2 = r2.get("warnings") or []
        say("   forced (a second spine copy without its %d purchase export rows; the copy's %d step-2 tap(s) of visit day %s removed): %s" % (n, n2, vd, W2))
        forced = [w for w in W2 if w.startswith("No purchase export has been taken since the closing stock of %s was captured" % SA._r_dmy(cap["as_on"]))]
        check("C: (6) with no purchase export after the capture and no visit cover: the one sentence 'No purchase export has been taken since the closing stock of %s was captured (...)'" % SA._r_dmy(cap["as_on"]),
              len(forced) == 1 and "none yet (bill-wise) and none yet (item-wise)" in forced[0] and "count after it, not before" in forced[0], W2)
        c2.close()
        rest = {k: v for k, v in r.items() if k not in ("warnings", "as_of", "today")}
        DUMP["s6"] = dict(rest=json.loads(json.dumps(rest, default=str)), W=W, how=str(how))
        if OLD.get("s6"):
            diff = [k for k in set(rest) | set(OLD["s6"]["rest"]) if json.loads(json.dumps(rest.get(k), default=str)) != OLD["s6"]["rest"].get(k)]
            check("(6) readiness()'s other keys equal OLD vs NEW (%s)" % sorted(rest), not diff, diff)
        c.close()
    section("6  F-769 / F-953: readiness -- no 'days behind' for purchases; the stock-ahead sentence by purchase_cover_how; the judge did not run", s6)

    # ============================================================================================ 7 start_capture_lines
    def s7():
        c = conn()
        row = c.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason FROM stock_start_capture WHERE md5=?", (PEND,)).fetchone()
        check("the 18-10 09:37 start capture (%s) is on the copy" % PEND[:8], row is not None)
        if row["verdict"] != "pending":
            c.execute("UPDATE stock_start_capture SET verdict='pending', reason='pur_short' WHERE md5=?", (PEND,))
            c.commit()
            say("   (its verdict was %s on the copy: set back to pending ON THE COPY -- stated)" % row["verdict"])
        s7db = os.path.join(os.path.dirname(dbp), "spine_s7_%s.db" % SIDE)
        copy_db(SPINE_PATH, s7db)
        e = sqlite3.connect(s7db)
        cstamp = stamp_of(row["stamp_iso"])
        n = e.execute("DELETE FROM sp_export WHERE family LIKE 'PURCHASE_%' AND stamp > ?", (cstamp,)).rowcount
        e.commit()
        nb = e.execute("SELECT MAX(stamp) FROM sp_export WHERE ok=1 AND family='PURCHASE_BILLWISE'").fetchone()[0]
        ni = e.execute("SELECT MAX(stamp) FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')").fetchone()[0]
        e.close()
        say("   a spine copy with the %d purchase export(s) stamped after the capture (%s) removed (today: none); newest bill-wise %s, item-wise %s" % (n, cstamp, nb, ni))
        SW.SPINE_DB = s7db
        try:
            rows0 = caprows(c)
            L = SW.start_capture_lines(c, SW.Spine())
            rows1 = caprows(c)
        finally:
            SW.SPINE_DB = SPINE_PATH
        texts = [l["text"] for l in L]
        say("   start_capture_lines: %s" % (texts or "none"))
        when = "%s %s" % (SW.dmy(row["as_on"])[:5], str(row["stamp_iso"])[11:16])

        def dm(st):
            s = SF.stamp_iso(st)
            return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if s else "none yet"
        exp = "Closing stock printed %s waits for a purchase export taken after it (newest: bill-wise %s, item-wise %s)" % (when, dm(nb), dm(ni))
        check("C: (7) the pending capture's line in its new words, verbatim: %r" % exp, exp in texts, texts)
        check("(7) no 'waits for Amir's purchase export' line (the day count is gone)", not any("waits for Amir's purchase export" in t for t in texts), texts)
        check("(7) the judge did not run: the stock_start_capture rows are byte-equal before and after", rows0 == rows1)
        both = os.path.join(os.path.dirname(dbp), "spine_s7b_%s.db" % SIDE)
        copy_db(s7db, both)
        e = sqlite3.connect(both)
        st = TODAY.replace("-", "") + "-080000"
        for fam, key in (("PURCHASE_BILLWISE", "exp-b"), ("PURCHASE_ITEMWISE", "exp-i")):
            e.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,1,'','W603','W603 walk')",
                      (w603(key), "W603 " + fam, fam, st, TODAY[:8] + "01", TODAY, TODAY))
        e.commit()
        e.close()
        SW.SPINE_DB = both
        try:
            L2 = SW.start_capture_lines(c, SW.Spine())
        finally:
            SW.SPINE_DB = SPINE_PATH
        t2 = [l["text"] for l in L2]
        say("   with synthetic purchase exports of BOTH families stamped %s: %s" % (st, t2 or "none"))
        check("(7) covered by clause (b): no line for the pending capture", not any("printed %s" % when in t for t in t2), t2)
        if row["verdict"] != "pending":
            c.execute("UPDATE stock_start_capture SET verdict=?, reason=? WHERE md5=?", (row["verdict"], row["reason"], PEND))
            c.commit()
        c.close()
        DUMP["s7"] = dict(texts=texts, t2=t2)
    section("7  the pending start capture's owner line reads purchase_cover_how; none once an export covers it", s7)

    # ============================================================================================ 8 the salt sheet
    SALT = {}

    def due_sql(c):
        return tuple(c.execute(DUTY["due_sql"]).fetchone()) if DUTY else None

    def grids(data):
        return PR.grids(io.BytesIO(data))

    def s8():
        c = conn()
        SALT["due0"] = due_sql(c)
        r = c.execute("SELECT id, a, answer, done, done_by, done_at FROM purchase_salt_task WHERE section='waiting' AND answer IS NOT NULL AND TRIM(answer)<>'' "
                      "AND COALESCE(done,0)=1 AND answer_at LIKE '2026-10-04%' ORDER BY id LIMIT 1").fetchone()
        check("an answered waiting row of 04-Oct, ticked by Amir on the owner's page, exists on the copy (the walk's subject)", r is not None)
        SALT["row"] = dict(r)
        say("   due_sql as the rows stand: %s; the subject: id %s (%s), answered '%s', done %s by %s at %s" % (SALT["due0"], r["id"], r["a"], r["answer"], r["done"], r["done_by"], r["done_at"]))
        c.execute("UPDATE purchase_salt_task SET done=0, done_by=NULL, done_at=NULL WHERE id=?", (r["id"],))
        c.commit()
        SALT["due1"] = due_sql(c)
        ot = AS._open_tasks(c)
        wt = AS._waiting(c)
        mine = [t for t in ot if t["id"] == r["id"]]
        say("   after done=0 on the copy: _open_tasks %d (%s), _waiting %d; due_sql %s" % (len(ot), [(t["id"], t["section"]) for t in ot][-3:], len(wt), SALT["due1"]))
        check("C: (8) _open_tasks lists the answered salt LAST with section 'waiting' and _exact = the owner's answer", bool(mine) and ot[-1]["id"] == r["id"] and mine[0]["section"] == "waiting" and AS._exact(mine[0]) == r["answer"].strip(),
              ([(t["id"], t["section"]) for t in ot], AS._exact(mine[0]) if mine else None))
        check("C: (8) _waiting (tab 2) is empty: every waiting row is answered", not wt, [(t["id"], t.get("answer")) for t in wt])
        data, n = AS._build_workbook(c)
        G = dict(grids(data))
        names = list(G)
        tab1 = G.get("SALT KAAM") or {}
        cells = [str(v) for v in tab1.values()]
        say("   the workbook: tabs %s, %d task row(s); tab 1 carries id %s: %s, 'Dr sahab ka jawab': %s, the answer: %s"
            % (names, n, r["id"], any(str(v).rstrip("0").rstrip(".") == str(r["id"]) for v in tab1.values()), any("Dr sahab ka jawab" in v for v in cells), r["answer"].strip() in cells))
        check("C: (8) tab 1 (SALT KAAM) carries the row (its id, 'Item ka salt badliye -- Dr sahab ka jawab', the answer as the exact text) and tab 2 (DR SAHAB KE LIYE) is absent",
              any(str(v).rstrip("0").rstrip(".") == str(r["id"]) for v in tab1.values()) and any("Dr sahab ka jawab" in v for v in cells) and r["answer"].strip() in cells and "DR SAHAB KE LIYE" not in names, names)
        # the upload with Y on that id, built as _read_ticks expects
        sh = PW.Sheet()
        for col, h in enumerate(["ID", "KYA KARNA HAI", "KIS PAR", "ABHI KYA HAI", "YEH EXACT NAAM COPY KIJIYE", "HO GAYA (Y)", "REMARK"]):
            sh.text(0, col, h)
        sh.num(1, 0, int(r["id"]))
        sh.text(1, 5, "Y")
        up = PW.workbook_bytes_multi([("SALT KAAM", sh)])
        resp = cl.post("/finance/amir/salts", base_url=BASE, headers={"X-Clinic-User": "amir", "X-Clinic-Role": "staff"},
                       data={"f": (io.BytesIO(up), "SALT_KAAM_W603.xlsx")}, content_type="multipart/form-data")
        r2 = c.execute("SELECT done, done_by, done_at FROM purchase_salt_task WHERE id=?", (r["id"],)).fetchone()
        say("   the upload (%s): done %s by %s at %s" % (resp.status_code, r2["done"], r2["done_by"], r2["done_at"]))
        check("(8) an upload with Y on that id ticks it: done = 1, done_by = the walk's amir", resp.status_code == 200 and r2["done"] == 1 and r2["done_by"] == "amir", dict(r2))
        # an unanswered waiting row stays on tab 2
        c.execute("UPDATE purchase_salt_task SET done=0, done_by=NULL, done_at=NULL WHERE id=?", (r["id"],))
        ins(c, "purchase_salt_task", dict(section="waiting", seq=990, a="W603 WALK ITEM", b="W603 SALT", c="", done=0, answer=None, pushed_at=T(0)))
        c.commit()
        wt2 = AS._waiting(c)
        ot2 = AS._open_tasks(c)
        data2, _n2 = AS._build_workbook(c)
        names2 = [k for k, _g in grids(data2)]
        say("   with a synthetic UNANSWERED waiting row: _waiting %d, in _open_tasks: %s, tabs %s" % (len(wt2), any(t["a"] == "W603 WALK ITEM" for t in ot2), names2))
        check("(8) an unanswered waiting row (answer NULL) stays on tab 2 and off tab 1 (NEW; on OLD every waiting row is on tab 2)",
              any(t["a"] == "W603 WALK ITEM" for t in wt2) and not any(t["a"] == "W603 WALK ITEM" for t in ot2) and "DR SAHAB KE LIYE" in names2, (len(wt2), names2))
        c.execute("DELETE FROM purchase_salt_task WHERE a='W603 WALK ITEM'")
        c.commit()
        c.close()
        DUMP["s8"] = dict(due0=list(SALT["due0"]) if SALT["due0"] else None, due1=list(SALT["due1"]) if SALT["due1"] else None, id=r["id"])
    section("8  the answered salt on Amir's sheet: tab 1, the exact text, the tick by id; the unanswered stays on tab 2", s8)

    # ============================================================================================ 9 the duty and the staff-eye walk
    def s9():
        c = conn()
        check("DUTY_MAP.json loads, is v16 of kit S603 and carries amir.salt_tasks once with the door and the marker", DM.get("version") == 16 and DM.get("kit") == KIT and DUTY is not None
              and DUTY["door"] == "/finance/amir/step/6" and DUTY["door_marker"] == MARKER and DUTY["tile"] == "Amir ka kaam" and DUTY["coded"] is None
              and sum(1 for x in DM["duties"] if x["id"] == "amir.salt_tasks") == 1, (DM.get("version"), DM.get("kit")))
        check("(9) due_sql on the copy: (0, None) as the rows stand, (1, '2026-10-04') with the answered row open (the SQL alone: the same on OLD)", tuple(SALT.get("due0") or ()) == (0, None) and tuple(SALT.get("due1") or ()) == (1, "2026-10-04"),
              (SALT.get("due0"), SALT.get("due1")))
        if hasattr(AD, "DUTY_SQL"):
            by = {x["id"]: x for x in DM["duties"]}
            same = all(by[k]["due_sql"] == v for k, v in AD.DUTY_SQL.items())
            check("S533's check re-run: the three DUTY_SQL strings are byte-equal in DUTY_MAP.json v16 (%s)" % sorted(AD.DUTY_SQL), same, [k for k, v in AD.DUTY_SQL.items() if by[k]["due_sql"] != v])
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        n_due = int(ro.execute(DUTY["due_sql"]).fetchone()[0] or 0)
        ro.close()
        # the staff-eye walk (walk_s444 118-202's pattern): the portal home as amir, then the door through the finance app
        tiles = []
        try:
            sys.path.insert(0, os.path.abspath(a.por))
            import portal as po                                # noqa: E402
            pc = po.app.test_client(use_cookies=False)
            r = pc.post("/portal/login", base_url=BASE, data={"user": "amir", "password": pw["amir"]})
            m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
            tok = m.group(1) if m else ""
            r3 = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
            tiles = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r3.get_data(as_text=True))]
            say("   the portal (the walk's own secret and user store): login %s, /portal?all=1 %s, tiles %s" % (r.status_code, r3.status_code, tiles))
            check("(9) staff-eye: Amir's portal home shows the duty's tile 'Amir ka kaam'", r3.status_code == 200 and DUTY["tile"] in tiles, tiles)
        except Exception as e:                                 # noqa: BLE001
            check("(9) staff-eye: the portal home rendered as amir", False, "%s: %s" % (type(e).__name__, str(e)[:300]))
        finally:
            if os.path.abspath(a.por) in sys.path:
                sys.path.remove(os.path.abspath(a.por))
        path = DUTY["door"]
        body, s = "", None
        for _hop in range(4):
            s, h = GET("amir", path)
            if s in (301, 302, 303):
                m = re.search(r"Location: (\S+)", h) or None
                break
            body = h
            break
        seen = MARKER in body
        say("   the door %s as amir (%s), due n = %d: the marker %s" % (path, s, n_due, "seen" if seen else "NOT seen"))
        check("C: (9) staff-eye: with the answered salt open (due n = 1) the door /finance/amir/step/6 shows the marker '%s'" % MARKER, n_due == 1 and s == 200 and seen, (n_due, s))
        s0, h0 = GET("amir", "/finance/amir/step/6")
        # the card leaves when the row is ticked (the state decides)
        rid = SALT["row"]["id"]
        c.execute("UPDATE purchase_salt_task SET done=1, done_by=?, done_at=? WHERE id=?", (SALT["row"]["done_by"], SALT["row"]["done_at"], rid))
        c.commit()
        s1_, h1 = GET("amir", "/finance/amir/step/6")
        check("(9) the row restored (done=1 as it was): the door no longer shows the marker; due_sql back to (0, None)", s1_ == 200 and MARKER not in h1 and tuple(due_sql(c)) == (0, None), due_sql(c))
        c.close()
        DUMP["s9"] = dict(tiles=tiles, n_due=n_due)
    section("9  the duty amir.salt_tasks: due_sql, the map, the staff-eye walk (tile and door)", s9)

    # ============================================================================================ 11 the greps and nothing else moved
    def s11():
        ad, sa, sw, sl = SRC["amir_day.py"], SRC["stock_app.py"], SRC["stock_watch.py"], SRC["amir_salts.py"]
        rd = fn_body(ad, "_reexport_due")
        check("C: _export_fact defined once, called twice (_reexport_due, _s603_export_lines)", ad.count("def _export_fact(") == 1 and ad.count("= _export_fact(cx, ") == 2 and "_export_fact(" in rd and "_export_fact(" in fn_body(ad, "_s603_export_lines"))
        check("C: _reexport_due has no ticks.get(3) and no same-day cut", bool(rd) and "ticks.get(3)" not in rd and "substr(replace(received_at,'T',' '),1,10)=?" not in rd)
        check("C: ORDER BY CASE WHEN once, in _export_state; 'baje se nahi aayi' once", ad.count("ORDER BY CASE WHEN") == 1 and "ORDER BY CASE WHEN" in fn_body(ad, "_export_state") and ad.count("baje se nahi aayi") == 1)
        check("C: _s603_export_lines defined once, called once (needs_you_lines)", ad.count("def _s603_export_lines(") == 1 and ad.count("_s603_export_lines(con)") == 1 and "_s603_export_lines(con)" in fn_body(ad, "needs_you_lines"))
        check("C: \"absent\" in amir_day: S488_WHYS and _s488_ending only", '"absent"' in ad[:ad.find("\ndef _today")] and ad.count('"absent"') == 3 and fn_body(ad, "_s488_ending").count('"absent"') == 2)
        why_body = fn_body(sa, "_s488_why")
        check("C: \"absent\" in stock_app: _s488_why only; _s524_verdict passes unseen", sa.count('"absent"') == 2 and why_body.count('"absent"') == 2 and "unseen=None" in why_body and "last_at, unseen=unseen)" in fn_body(sa, "_s524_verdict"))
        check("C: 'days behind today' once in stock_app.py (the sale sentence); _s488_purchase_reach zero", sa.count("days behind today") == 1 and "_s488_purchase_reach" not in sa)
        check("C: read_only=True at _r_stock and readiness's helper; purchase_cover_how once in stock_app (the helper)",
              "read_only=True" in fn_body(sa, "_r_stock") and "read_only=True" in fn_body(sa, "_s603_purchase_wait") and sa.count("read_only=True") == 2 and sa.count("purchase_cover_how(") == 1)
        check("C: read_only=True and purchase_cover_how once each in stock_watch's start_capture_lines; 'waits for Amir's purchase export' zero",
              fn_body(sw, "start_capture_lines").count("read_only=True") == 1 and sw.count("purchase_cover_how(") == 1 and "waits for Amir's purchase export" not in sw)
        check("C: '\"waiting\": (\"Item ka salt badliye' once in amir_salts.py", sl.count('"waiting": ("Item ka salt badliye') == 1)
        check("amir.salt_tasks once in the duty map (the same v16 file on both sides)", open(os.path.abspath(a.duty_map), encoding="utf-8").read().count('"amir.salt_tasks"') == 1)
        ctxs = [(i + 1, l.strip()[:90]) for i, l in enumerate(sa.splitlines()) if "_sf.Ctx(" in l]
        say("   every _sf.Ctx( in stock_app.py (the report lists which are on a GET-only path): %s" % ctxs)
        check("no run of ten digits in the four files or the walk's own output", not re.search(r"\d{10}", "".join(SRC.values()) + "\n".join(OUT)))
        check("no code of the four files writes to the spine (no INSERT / UPDATE / DELETE on an sp_ table)", not any(re.search(r"(INSERT|UPDATE|DELETE)\s+(INTO\s+|FROM\s+)?sp_", SRC[n]) for n in FOUR))
        check("stock_figure.py untouched (md5 51e1fc63)", hashlib.md5(open(os.path.join(fin, "stock_figure.py"), "rb").read()).hexdigest().startswith("51e1fc63"))
        check("the spine copy's bytes are unchanged by the walk (no write by any code under test; the synthetic spines are second copies)", hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest() == spine_md5_0)
        with conn() as c_:
            rows = {t: c_.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("amir_step_log", "mi_file", "purchase_export", "purchase_salt_task")}
            st = dict(c_.execute("SELECT id, done FROM purchase_salt_task WHERE id=?", (SALT["row"]["id"],)).fetchone()) if SALT.get("row") else {}
        check("the walk's own rows are gone from the copy and the subject salt row is as it was (%s)" % st, rows == real_rows and st.get("done") == 1, (rows, real_rows, st))
        r = cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("11 the greps (one fact, one place), the Ctx list, nothing else moved", s11)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S603: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S603: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S603: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S603: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s618.py -- kit S618_SCAN_QUALITY (22-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).

    python3 -B walk_s618.py --ar <scratch /root/assetapp (the files under test)> --fin <scratch /root/finance> --shared <scratch /root/shared>
                            --adb <COPY of assets.db> --db <COPY of finance.db> --uploads <scratch uploads (copies of the scans used)>
                            --por <scratch /root/portal copy: the walk writes its OWN secret and user store into it> --duty-map <the kit's DUTY_MAP.json>
                            --labels <the eye's labels (S335_SCAN_VISUAL_AUDIT.json)> --kit <this kit folder> --vpy <the venv python>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s618.py --facts --label before|after --adb <assets.db> --db <finance.db> --shared <folder with scan_quality.py>  (read only)

The real Scan App and the real finance app in one process: the walk's own sign-in (a random portal secret, its own user store -- never the live
ones), the Scan App's user set by the walk. Claude is called for REAL on the labelled set (section 1: the backfill on the scratch copy, under
the venv python, counted against the scratch copy's cap; the key file is read by the reader, never printed) and stubbed for the synthetic
scenes. Its own rows by key (W618 ...). No phone number is printed (ten digits masked); no bill image leaves the box.
--expect-red is the negative control: the same walk on the OLD files -- every 'C:' check must be red. Prints 'WALK OK S618 ...'."""
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

KIT = "S618_SCAN_QUALITY"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "darpan": "staff", "reception": "staff", "alisha": "staff", "shivani": "staff", "bhati": "staff", "shavez": "manager", "amir": "staff"}
UNFIT = ("B-0155", "B-0157", "B-0159", "B-0176", "B-0180", "B-0181", "B-0183", "B-0188", "B-0199")      # the eye's 'not fit for use' (brief 2)
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
        check("C: section %s ran without an exception" % title[:40], False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-1500:]))


def text_lines(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"</(div|p|li|tr|h\d|button|a|td|th|span)>|<br\s*/?>", "\n", s)
    out = []
    for l in s.split("\n"):
        t = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", l))).strip()
        if t:
            out.append(t)
    return out


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def h8(o):
    return hashlib.md5(json.dumps(o, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def eye_turn(o):
    o = str(o or "")
    return 270 if o.startswith("270") else 0 if (o.startswith("upright") or o.startswith("tilted")) else None


def pdf_pages(p):
    r = subprocess.run(["pdfinfo", p], capture_output=True, text=True, timeout=30)
    m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
    return int(m.group(1)) if m else None


def rendered_wh(p, work):
    """pdftoppm's own render of page 1 (it honours /Rotate): (width, height) of the picture."""
    root = os.path.join(work, "r618_%s" % secrets.token_hex(4))
    subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "12", "-gray", "-singlefile", p, root], capture_output=True, timeout=60)
    try:
        raw = open(root + ".pgm", "rb").read(64)
        m = re.match(rb"P5\s+(\d+)\s+(\d+)", raw)
        return (int(m.group(1)), int(m.group(2))) if m else None
    except OSError:
        return None
    finally:
        try:
            os.remove(root + ".pgm")
        except OSError:
            pass


def portal_setup(por):
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W618 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w618-walk-seed'\n" % secret)
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


# ======================================================================================================= the installer's live facts
def facts(a):
    """Read only (URI mode=ro on both databases); never a page. The scan_quality of --shared judges."""
    A = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(a.adb), uri=True, timeout=60)
    A.row_factory = sqlite3.Row
    F = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(a.db), uri=True, timeout=60)
    sys.path.insert(0, os.path.abspath(a.shared))
    try:
        import scan_quality as SQ                             # noqa: E402
    except Exception:                                          # noqa: BLE001
        SQ = None
    cols = {r[1] for r in A.execute("PRAGMA table_info(bills)")}
    tabs = {r[0] for r in A.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    now = dt.datetime.now().replace(microsecond=0)
    say("FACTS %s: clock %s IST; bills.rescan_of %s; scan_lie %s; scan_quality %s" % (a.label, now.isoformat(" "), "rescan_of" in cols, "scan_lie" in tabs,
                                                                                    getattr(SQ, "VERSION", None)))
    rows = [dict(r) for r in A.execute("SELECT id, stamp_no, kind, status, lane, page_of, doc_kind, source_stored, created_at%s FROM bills WHERE lane='pharmacy' "
                                       "AND substr(created_at,1,10)>='2026-10-08' ORDER BY id" % (", rescan_of" if "rescan_of" in cols else ""))]
    say("FACTS %s: pharmacy-lane scans since 08-Oct: %d (not set aside %d); the newest saved at %s (UTC)" % (
        a.label, len(rows), sum(1 for r in rows if r["status"] != "rejected"), max((r["created_at"] for r in rows), default="-")))
    say("FACTS %s: the labelled faults: %s" % (a.label, ", ".join("%s %s" % (r["stamp_no"], r["status"]) for r in rows if r["stamp_no"] in UNFIT)))
    ties = []
    for st in ("B-0199", "B-0180", "B-0181", "B-0155"):
        b = A.execute("SELECT id FROM bills WHERE stamp_no=?", (st,)).fetchone()
        t = F.execute("SELECT order_id, stamp, scan_at FROM order_scan_tie WHERE asset_bill_id=?", (b[0],)).fetchone() if b else None
        ties.append("%s -> %s" % (st, "order %s (stamp %s, scan_at %s)" % tuple(t) if t else "no tie"))
    say("FACTS %s: the ties: %s" % (a.label, "; ".join(ties)))
    lie = {}
    if "scan_lie" in tabs:
        for r in A.execute("SELECT * FROM scan_lie"):
            lie[(r["bill_id"], r["file"])] = dict(r)
        turned = [r for r in lie.values() if r.get("rotated_to")]
        say("FACTS %s: scan_lie rows %d (checked %d, turned %d, blur_kept %d)" % (a.label, len(lie), sum(1 for r in lie.values() if r.get("model") and not str(r["model"]).startswith("upright copy")),
                                                                               len(turned), sum(1 for r in lie.values() if r.get("blur_kept"))))
    try:
        asks = F.execute("SELECT COUNT(*), SUM(CASE WHEN done_at IS NULL AND withdrawn_at IS NULL THEN 1 ELSE 0 END) FROM scan_rescan_ask").fetchone()
        say("FACTS %s: scan_rescan_ask rows %s (open %s)" % (a.label, asks[0], asks[1] or 0))
    except sqlite3.Error:
        say("FACTS %s: scan_rescan_ask -- not there yet" % a.label)
    if SQ is not None:
        settings = {str(r[0]): r[1] for r in A.execute("SELECT key, value FROM settings WHERE key LIKE 'scan.%'")}
        reading = {}
        for r in A.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1"):
            try:
                reading[r[0]] = json.loads(r[1]) if r[1] else None
            except ValueError:
                pass
        red = []
        for r in rows:
            d = SQ.detail(r, reading.get(r["id"]), lie.get((r["id"], r["source_stored"])), settings)
            if d:
                red.append("%s %s" % (r["stamp_no"], d["code"]))
        say("FACTS %s: Scans to redo by the rule (no ask counted): %d -- %s" % (a.label, len(red), ", ".join(red) or "none"))
    A.close()
    F.close()
    say("FACTS OK S618 (%s)" % a.label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--ar", "--fin", "--shared", "--adb", "--db", "--uploads", "--por", "--duty-map", "--labels", "--kit", "--vpy", "--dump", "--old-dump", "--label"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--facts", action="store_true")
    a = ap.parse_args()
    if a.facts:
        return facts(a)
    for k in ("ar", "fin", "shared", "adb", "db", "uploads", "por", "duty_map", "labels", "kit", "vpy", "dump"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k.replace("_", "-"))
    ar, fin, shared, adb, dbp, ups, por = (os.path.abspath(getattr(a, k)) for k in ("ar", "fin", "shared", "adb", "db", "uploads", "por"))
    for p in (ar, fin, shared, adb, dbp, ups, por):
        assert p.startswith("/tmp/"), "the walk runs on scratch copies in /tmp only: %s" % p
    os.makedirs(a.dump, exist_ok=True)
    WORK = os.path.join(os.path.dirname(dbp), "w618_work_%s" % ("old" if a.expect_red else "new"))
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    say("-- S618 walk on the %s: %s . %s" % ("OLD files (negative control)" if a.expect_red else "new files", ar, fin))
    LABELS = {x["stamp"]: x for x in json.load(open(a.labels, encoding="utf-8"))}
    secret, pw, store = portal_setup(por)
    token = secrets.token_hex(16)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, ASSETS_UPLOADS=ups, SHARED_LIB_DIR=shared, CLINIC_PORTAL_DIR=por, FINANCE_ALLOW_HEADER_AUTH="1",
                      MARG_INGEST_DIR=os.path.join(os.path.dirname(dbp), "nomarg"), ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por,
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token,
                      PYTHONDONTWRITEBYTECODE="1", CLINIC_SSO_SECRET=secret, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"),
                      DUTY_MAP_JSON=os.path.abspath(a.duty_map), SCANAPP_ANTHROPIC_URL="http://127.0.0.1:9/never")      # in-process: no real call
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "SARVAM_API_KEY", "PORDERS_SOURCE"):
        os.environ.pop(k, None)
    # the original files of the scans (before the backfill turns any): the rescan scene uploads B-0199's own first bytes
    A0 = sqlite3.connect(adb)
    A0.row_factory = sqlite3.Row
    ORIG = {r["stamp_no"]: (r["id"], r["source_stored"]) for r in A0.execute("SELECT id, stamp_no, source_stored FROM bills WHERE lane='pharmacy' AND substr(created_at,1,10)>='2026-10-08'")}
    A0.close()
    sys.path.insert(0, fin)
    sys.path.insert(1, shared)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import porders_s454 as P4                                 # noqa: E402
    for m in (fa, OS, P4):
        assert m.__file__.startswith(fin), m.__file__
    sys.path.append(ar)
    import asset_register as AR                               # noqa: E402
    assert AR.__file__.startswith(ar), AR.__file__
    CL = AR.CLAUDE
    try:
        import scan_quality as SQ                             # noqa: E402
        assert SQ.__file__.startswith(shared)
    except Exception:                                          # noqa: BLE001
        SQ = None
    NEW = hasattr(CL, "lie_pass")
    say("   the real finance app (parts that did not load: %s) and the real Scan App %s loaded from the scratch folders; claude_reader %s; scan_quality %s"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", AR.APP_VERSION.split(" ")[0], "NEW (S618)" if NEW else "OLD", getattr(SQ, "VERSION", None)))
    fcl = fa.app.test_client(use_cookies=False)
    acl = AR.app.test_client()

    def GET(u, path, follow=False, headers=None):
        hd = {"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}
        hd.update(headers or {})
        r = fcl.get(path, base_url=BASE, headers=hd, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body, headers=None):
        hd = {"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}
        hd.update(headers or {})
        r = fcl.post(path, base_url=BASE, headers=hd, json=body)
        try:
            j = json.loads(r.get_data().decode("utf-8", "replace"))
        except ValueError:
            j = {}
        return r.status_code, j

    def fconn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def aconn():
        c = sqlite3.connect(adb, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    REC = {"Cookie": "clinic_who=alisha"}
    with fconn() as c_:
        OS.ensure(c_)
    # ============================================================================================ 6 (first): the pages dumped on the quiet copy
    def s_pages():
        pages = [("darpan", "/finance/darpan/kal/api/day"), ("darpan", "/finance/darpan/kal/api/order"), ("reception", "/finance/porders"),
                 ("reception", "/finance/porders/s454/order"), ("reception", "/finance/porders/s454/maal"), ("reception", "/finance/porders/s454/scan"),
                 ("reception", "/finance/porders/s454/q"), ("amir", "/finance/amir"), ("manoj", "/finance/sanjeevni/api/needs-you"),
                 ("shavez", "/finance/purchase/page/pay"), ("darpan", "/finance/porders")]
        bad = {}
        for u, path in pages:
            s, h = GET(u, path, follow=True, headers=(REC if u == "reception" else None))
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))[:120]
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "now", "server_time", "user", "as_of", "today", "purchase_upto"):
                            j.pop(k, None)
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = [re.sub(r"\b\d+ (hours?|minutes?|ghante|minute)\b", r"N \1", re.sub(r"\d{1,2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l))
                     for l in body.splitlines() if l.strip()]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                if old != lines:
                    os_, ns = set(old), set(lines)
                    bad[(u, path)] = ([l for l in old if l not in ns][:4], [l for l in lines if l not in os_][:4])
                    say("   CHANGED on %s for %s: %s" % (path, u, bad[(u, path)]))
                else:
                    say("   unchanged on %s for %s" % (path, u))
        if a.old_dump:
            check("every page dump of S613's list (reception's home, order list, maal, scan, q; Darpan's day and home; Amir's page; the approvals "
                  "Needs-you; the pay page) is byte-equal OLD vs NEW (no ask on the copy: reception's new row is absent)", not bad, bad)
    section("6 (first) the pages dumped on the quiet copy -- byte-equal OLD vs NEW", s_pages)

    # ============================================================================================ 1 upright: the real check on the labelled set
    st1 = {}

    def snap_reading():
        with aconn() as c:
            rows = [tuple(r) for r in c.execute("SELECT bill_id, at, model, ok, doc_kind, data, error FROM claude_reading ORDER BY bill_id")]
            m = c.execute("SELECT value FROM settings WHERE key='read.claude_model'").fetchone()
        return h8(rows), (m[0] if m else None), len(rows)

    def s1():
        r0 = snap_reading()
        with aconn() as c:
            cap0 = c.execute("SELECT value FROM settings WHERE key=?", ("read.calls." + dt.datetime.now().strftime("%Y-%m-%d"),)).fetchone()
        p = subprocess.run([a.vpy, "-B", os.path.join(a.kit, "backfill_s618.py"), "--assetapp", ar, "--adb", adb, "--uploads", ups],
                           capture_output=True, text=True, timeout=3600, cwd="/tmp", env=dict(os.environ, SCANAPP_ANTHROPIC_URL="https://api.anthropic.com/v1/messages"))
        for l in (p.stdout or "").splitlines():
            say("   " + l)
        if p.stderr.strip():
            say("   (stderr) " + p.stderr.strip()[-600:])
        r1 = snap_reading()
        st1["backfill_rc"] = p.returncode
        check("C: the backfill ran on the scratch copy through claude_reader.lie_pass (exit %s)" % p.returncode, p.returncode == 0 and "BACKFILL S618:" in p.stdout, p.returncode)
        check("the checks wrote no claude_reading row and left read.claude_model as it was (%s; %d readings, %s)" % (r1[1], r1[2], r1[0]), r0 == r1, (r0, r1))
        # the labelled scans the backfill does not take (set aside): checked directly, for the orientation table only
        with aconn() as c:
            lie = {(r["bill_id"]): dict(r) for r in c.execute("SELECT l.* FROM scan_lie l JOIN bills b ON b.id=l.bill_id WHERE l.model IS NOT NULL AND l.model NOT LIKE 'upright copy%'")}
            bills = {r["stamp_no"]: dict(r) for r in c.execute("SELECT id, stamp_no, status, source_stored FROM bills WHERE stamp_no IN (%s)" % ",".join("?" * len(LABELS)), list(LABELS))}
        direct = {}
        if NEW:
            os.environ["SCANAPP_ANTHROPIC_URL"] = "https://api.anthropic.com/v1/messages"
            CL.API_URL = os.environ["SCANAPP_ANTHROPIC_URL"]
            for stp, b in sorted(bills.items()):
                if b["id"] not in lie:
                    res = CL.check_scan(os.path.join(ups, ORIG[stp][1]), db_path=adb)
                    direct[stp] = res
            CL.API_URL = "http://127.0.0.1:9/never"
            os.environ["SCANAPP_ANTHROPIC_URL"] = CL.API_URL
        say("   the eye against Claude (page 1's clockwise turn; 270 = the eye's 'turn 90 deg anticlockwise'):")
        side = up = side_ok = up_bad = 0
        table = []
        for stp in sorted(LABELS):
            b = bills.get(stp) or {}
            e = eye_turn(LABELS[stp]["orientation"])
            if b.get("id") in lie:
                got = (json.loads(lie[b["id"]]["pages_json"] or "[]") or [{}])[0].get("turn")
                how = "backfill"
            else:
                got = ((direct.get(stp) or {}).get("pages") or [{}])[0].get("turn") if direct.get(stp) else None
                how = "direct (set aside)"
            if e == 270:
                side += 1
                side_ok += 1 if got == 270 else 0
            elif e == 0:
                up += 1
                up_bad += 1 if got not in (0,) else 0
            table.append((stp, e, got, how))
            say("     %-7s eye %-4s claude %-5s %s" % (stp, e, got, how))
        st1["bar"] = (side_ok, side, up_bad, up)
        check("C: the bar -- at least 20 of the %d sideways pages read exactly 270 (%d did) and no upright page reads other than 0 (%d did, of %d)"
              % (side, side_ok, up_bad, up), side >= 20 and side_ok >= 20 and up_bad == 0, st1["bar"])
        # the turned files render upright: pdftoppm honours /Rotate
        with aconn() as c:
            turned = [dict(r) for r in c.execute("SELECT b.stamp_no, l.file, l.rotated_to, l.pages_json FROM scan_lie l JOIN bills b ON b.id=l.bill_id WHERE l.rotated_to IS NOT NULL")]
            aud = c.execute("SELECT COUNT(*) FROM bill_audit WHERE action='upright'").fetchone()[0]
        good = []
        for t in turned:
            wh0, wh1 = rendered_wh(os.path.join(ups, t["file"]), WORK), rendered_wh(os.path.join(ups, t["rotated_to"]), WORK)
            e = eye_turn((LABELS.get(t["stamp_no"]) or {}).get("orientation"))
            ok_ = bool(wh0 and wh1) and wh0[1] > wh0[0] and wh1[0] > wh1[1] and e in (270, None) and os.path.exists(os.path.join(ups, t["file"]))
            good.append(ok_)
            say("     %-7s %s -> %s rendered %s -> %s (the old file kept: %s)" % (t["stamp_no"], t["file"], t["rotated_to"], wh0, wh1, os.path.exists(os.path.join(ups, t["file"]))))
        check("C: every turned scan renders sideways-to-upright (portrait page -> landscape, pdftoppm reads its /Rotate), its old file kept, one "
              "'upright' audit each (%d turned, %d audits)" % (len(turned), aud), bool(turned) and all(good) and aud == len(turned), (len(turned), good, aud))
        st1["turned"] = len(turned)
    section("1  upright: Claude checks the labelled set for real (the backfill on the scratch copy); the eye against Claude; the turned files", s1)

    # ---- 1b the join racing the turn (synthetic; the check stubbed)
    def s1b():
        if not NEW:
            check("C: the join racing the turn: the compare-and-set keeps the joined page (OLD has no turn)", False, "no lie_pass")
            return
        head_f, page_f = "bill_w618head.pdf", "bill_w618page.pdf"
        shutil.copy(os.path.join(ups, ORIG["B-0201"][1]), os.path.join(ups, head_f))
        shutil.copy(os.path.join(ups, ORIG["B-0199"][1]), os.path.join(ups, page_f))
        with aconn() as c:
            c.execute("DELETE FROM bills WHERE stamp_no IN ('W618-H','W618-P')")
            for st, f in (("W618-H", head_f), ("W618-P", page_f)):
                c.execute("INSERT INTO bills (kind, source_stored, source_orig, stamp_no, status, submitted_by, submitted_at, lane, ocr_status, created_at) "
                          "VALUES ('Pharmacy',?,?,?,'captured','w618walk',?, 'pharmacy','read', datetime('now'))", (f, f, st, dt.datetime.now().strftime("%Y-%m-%d %H:%M")))
            c.commit()
            H = dict(c.execute("SELECT * FROM bills WHERE stamp_no='W618-H'").fetchone())
            Pg = dict(c.execute("SELECT * FROM bills WHERE stamp_no='W618-P'").fetchone())
        S441 = AR.S441
        calls, real = [], CL.check_scan
        merged = {}

        def stub(path, db_path=None):
            calls.append(os.path.basename(path))
            if len(calls) == 1:                                # the join lands while Claude is answering (S441's _join_page, another thread)
                m = S441._merge_pdf(ups, H, Pg)
                merged["f"] = m
                d = sqlite3.connect(adb, timeout=60)
                d.execute("UPDATE bills SET source_stored=? WHERE id=?", (m, H["id"]))
                d.execute("UPDATE bills SET status='rejected', page_of=? WHERE id=?", (H["id"], Pg["id"]))
                d.commit()
                d.close()
                return {"pages": [{"turn": 270}], "whole_bill": True, "totals_visible": True, "legible": True, "note": "", "model": "stub"}
            return {"pages": [{"turn": 270}, {"turn": 0}], "whole_bill": True, "totals_visible": True, "legible": True, "note": "", "model": "stub"}
        CL.check_scan = stub
        try:
            w = CL.lie_pass(adb, ups, H["id"])
        finally:
            CL.check_scan = real
        with aconn() as c:
            cur = c.execute("SELECT source_stored FROM bills WHERE id=?", (H["id"],)).fetchone()[0]
            acts = [r[0] for r in c.execute("SELECT action FROM bill_audit WHERE bill_id=? ORDER BY id", (H["id"],))]
        n_cur = pdf_pages(os.path.join(ups, cur))
        say("   the head W618-H: lie_pass said %s; checked %s; the join made %s; the bill now %s (%s pages); audits %s" % (w, calls, merged.get("f"), cur, n_cur, acts))
        check("C: a join racing the turn: the compare-and-set does not apply to the pre-join file; the CURRENT (joined) file is checked and turned -- "
              "the bill keeps both pages, upright ('upright_raced' then 'upright')",
              w == "turned" and merged.get("f") and cur != merged.get("f") and cur.startswith(merged["f"][:-4]) and n_cur == 2 and "upright_raced" in acts and "upright" in acts,
              (w, cur, n_cur, acts))
        bad = CL.turn_file(ups, head_f, [270])                  # the control: what an unguarded write would have set
        n_bad = pdf_pages(os.path.join(ups, bad)) if bad else None
        check("the control: the turn of the PRE-join file alone has %s page(s) -- written without the guard it would have lost the joined page" % n_bad,
              bad is not None and n_bad == 1, (bad, n_bad))
    section("1b the join racing the turn (synthetic, the check stubbed): compare-and-set", s1b)

    # ============================================================================================ 2 the verdict on the labelled set
    def s2():
        with fconn() as c:
            x = P4.rescan_list(c) if hasattr(P4, "rescan_list") else None
        if x is None:
            check("C: the verdict -- 'Scans to redo' lists the unfit scans (OLD: no reader)", False, "no rescan_list")
            return
        red = {r["stamp"]: r for r in x["redo"]}
        with aconn() as c:
            live = {r["stamp_no"]: dict(r) for r in c.execute("SELECT b.id, b.stamp_no, b.status, b.page_of, b.source_stored FROM bills b WHERE b.lane='pharmacy' AND substr(b.created_at,1,10)>=?", (x["since"],))}
            lie = {(r["bill_id"], r["file"]): dict(r) for r in c.execute("SELECT * FROM scan_lie")}
            rd = {r[0]: json.loads(r[1]) for r in c.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1") if r[1]}
        caught_fit, missed, named = [], [], []
        say("   since %s: %d scan(s) on the list" % (x["since"], len(red)))
        for stp in sorted(live):
            b = live[stp]
            if b["status"] == "rejected" or b["page_of"]:
                continue
            lab = LABELS.get(stp)
            unfit = stp in UNFIT
            v = red.get(stp)
            l = lie.get((b["id"], b["source_stored"])) or {}
            s_, t_, na, n_ = SQ.sums(rd.get(b["id"]))
            inputs = "legible %s whole %s totals %s; lines %s of %s, %d without amount" % (l.get("legible"), l.get("whole_bill"), l.get("totals_visible"), s_, t_, na)
            if v:
                say("     CAUGHT %-7s %-10s (%s) -- %s" % (stp, v["code"], "unfit" if unfit else ("FIT" if lab else "not labelled"), inputs))
                if lab and not unfit:
                    caught_fit.append(stp)
            elif unfit:
                say("     MISSED %-7s (unfit: %s) -- %s" % (stp, (lab or {}).get("incomplete") if "cut" in str((lab or {}).get("incomplete")) else (lab or {}).get("sharpness"), inputs))
                missed.append(stp)
                if not (str(l.get("legible")) == "0" or str(l.get("whole_bill")) == "0" or str(l.get("totals_visible")) == "0"):
                    named.append(stp)
        say("   missed, and neither the reading nor the check can show it (the check said legible, whole and totals in view; the lines add up): %s" % (named or "none"))
        check("C: the verdict's bar -- no readable scan on the list (%s caught that the eye calls fit)" % (caught_fit or "none"), not caught_fit and len(red) > 0, caught_fit)
        check("C: every unfit scan not set aside is caught, except where neither the reading nor the check can show it (%s)" % (named or "none"),
              set(missed) == set(named), (missed, named))
        st1["redo"] = sorted(red)
        ch = {"lane": "pharmacy", "status": "captured", "doc_kind": "challan", "kind": "Challan"}
        check("a synthetic challan with no total and no amounts -> no verdict", SQ.verdict(ch, {"doc_kind": "challan", "total_amount": None,
                                                                                         "items": [{"name": "X", "amount": None}]}, {"whole_bill": 1, "totals_visible": 0, "legible": 1}) is None)
        check("a clinic-lane and a lab-lane scan never get a verdict", SQ.verdict({"lane": "clinic", "status": "draft"}, {"doc_kind": "other"}, {"legible": 0}) is None
              and SQ.verdict({"lane": "lab_purchase", "status": "captured"}, {"doc_kind": "other"}, {"legible": 0}) is None)
    section("2  the verdict on the labelled set: every catch and miss", s2)

    # ============================================================================================ 3 the phone, the server's half (the browser half runs on the PC)
    def s3():
        AR.current_user = lambda: {"id": None, "username": "reception", "display_name": "Reception", "role": "reception", "active": 1}
        r = acl.get("/intake?lane=pharmacy&vendor=KEDAR+PHARMACEUTICAL&bill_month=2026-10&rescan_of=199&from=%2Ffinance%2Fporders%2Fs454%2Frescan",
                    headers={"Cookie": "clinic_who=alisha"})
        h = r.get_data(as_text=True)
        open(os.path.join(a.dump, "intake_%s.html" % ("old" if a.expect_red else "new")), "w", encoding="utf-8").write(h)
        m = re.search(r"window\.SCANNER_CONFIG = (\{.*?\});</script>", h)
        cfg = json.loads(m.group(1)) if m else {}
        say("   the intake page for a pharmacy link (as reception): %s; SCANNER_CONFIG expectAspect %s, blurMin %s, uploadFields.rescan_of %s, cvScan %s"
            % (r.status_code, cfg.get("expectAspect"), cfg.get("blurMin"), (cfg.get("uploadFields") or {}).get("rescan_of"), cfg.get("cvScan")))
        check("C: a pharmacy link carries the half-A4 prior (expectAspect 0.7048) and the blur limit (blurMin) in SCANNER_CONFIG from the start, and "
              "rescan_of rides the link", r.status_code == 200 and cfg.get("expectAspect") == 0.7048 and float(cfg.get("blurMin") or 0) > 0
              and (cfg.get("uploadFields") or {}).get("rescan_of") == "199", cfg)
        check("C: the intake page clears rescan_of after the first Save (and after a PDF / file)", "delete window.SCANNER_CONFIG.uploadFields.rescan_of" in h)
        # the 33 cropped pages' aspects against arOK's 15 % band (brief 3.3)
        rows, fail = [], []
        for stp in sorted(LABELS):
            p = os.path.join(ups, ORIG[stp][1])
            q = subprocess.run(["pdfimages", "-list", "-f", "1", "-l", "1", p], capture_output=True, text=True, timeout=30).stdout.splitlines()
            wh = [(int(l.split()[3]), int(l.split()[4])) for l in q[2:3] if len(l.split()) > 5]
            if not wh or wh[0] == (1800, 2400):
                continue
            w, hh = wh[0]
            ar_, want = w / float(hh), 0.7048
            d = min(abs(ar_ - want) / want, abs(ar_ - 1 / want) * want)
            rows.append("%s %dx%d %.3f%s" % (stp, w, hh, ar_, "" if d <= 0.15 else " OUT"))
            if d > 0.15:
                fail.append(stp)
        say("   the %d cropped stored pages (not a bare 1800x2400 frame) and arOK's band (0.7048 +-15 %%): %s" % (len(rows), "; ".join(rows)))
        say("   %d of them fall outside the band: when the library's outline fails and the light finder is asked, such an outline is refused and the "
            "whole frame kept instead (Adjust still cuts it): %s" % (len(fail), ", ".join(fail)))
    section("3  the phone, the server's half: SCANNER_CONFIG on a pharmacy link; the cropped pages' aspects", s3)

    # ============================================================================================ 4 send back to reception; the staff-eye
    def portal_tiles(user):
        tiles = []
        try:
            sys.path.insert(0, por)
            import portal as po                                # noqa: E402
            pc = po.app.test_client(use_cookies=False)
            r = pc.post("/portal/login", base_url=BASE, data={"user": user, "password": pw[user]})
            m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
            r3 = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + (m.group(1) if m else "")})
            tiles = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r3.get_data(as_text=True))]
        except Exception as e:                                 # noqa: BLE001
            say("   the portal as %s could not be rendered: %s" % (user, str(e)[:200]))
        finally:
            if por in sys.path:
                sys.path.remove(por)
        return tiles

    def ids_of(*st):
        with aconn() as c:
            return [c.execute("SELECT id FROM bills WHERE stamp_no=?", (s,)).fetchone()[0] for s in st]

    def s4():
        i199, i181, i183 = ids_of("B-0199", "B-0181", "B-0183")
        s, j = POST("manoj", "/finance/porders/api/s454/rescan", {"asset_bill_id": i199, "reason": "cut"})
        check("C: the owner sends B-0199 back, reason cut off -> 200", s == 200 and j.get("ok"), (s, j))
        for u in ("reception", "alisha", "shivani"):
            sh, hh = GET(u, "/finance/porders", headers=(REC if u == "reception" else None))
            row = re.search(r'id="row_rescan"[^>]*><span class="n">(\d+)</span><span class="l">([^<]+)</span>', hh)
            sp, hp = GET(u, "/finance/porders/s454/rescan", headers=(REC if u == "reception" else None))
            t = _html.unescape(hp)
            check("C: %s's home shows 'Phir se scan karo 1' directly above 'Bill scan karna hai' (or the done line), and its page the reception words "
                  "and 'Doctor sahab ne bheja' with Scan karo (rescan_of in the link)" % u,
                  sh == 200 and row is not None and row.group(1) == "1" and row.group(2) == "Phir se scan karo" and sp == 200
                  and "Poora bill nahi aaya — poora bill frame mein laakar scan kijiye" in t and "Doctor sahab ne bheja" in t and "rescan_of=%d" % i199 in t,
                  (sh, row and row.groups(), sp))
            if u == "reception":
                pos = [hh.find('id="row_rescan"'), hh.find('id="row_scan"')]
                check("the row sits above 'Bill scan karna hai' when both are shown", pos[1] < 0 or pos[0] < pos[1], pos)
        sd, hd = GET("darpan", "/finance/porders")
        check("Darpan's home has no 'Phir se scan karo' row (not in porders.rescan_doers)", sd == 200 and 'id="row_rescan"' not in hd and "Phir se scan karo" not in hd, sd)
        s, j = POST("shavez", "/finance/porders/api/s454/rescan", {"asset_bill_id": i181, "reason": "blurred"})
        sp, hp = GET("reception", "/finance/porders/s454/rescan", headers=REC)
        check("C: Shavez sends B-0181 back (blurred) -> 200; reception's page: 'Photo dhundli hai — isi bill ki saaf photo lijiye' and 'Shavez ne bheja'",
              s == 200 and "Shavez ne bheja" in _html.unescape(hp) and "Photo dhundli hai — isi bill ki saaf photo lijiye" in _html.unescape(hp), (s, j))
        s, j = POST("darpan", "/finance/porders/api/s454/rescan", {"asset_bill_id": i199, "reason": "blurred"})
        check("C: a sender not in porders.rescan_askers (darpan) -> 403", s == 403 and j.get("error") == "not_asker", (s, j))
        s, j = POST("bhati", "/finance/porders/api/s454/rescan", {"asset_bill_id": i199, "reason": "blurred"})
        check("Bhati (no Purchase-orders role) is refused (%s)" % s, s in (401, 403, 302) and not j.get("ok"), (s, j))
        s, j = POST("manoj", "/finance/porders/api/s454/rescan", {"asset_bill_id": i183, "reason": "blurred"})
        check("C: a scan already set aside (B-0183) is refused -> 409 set_aside", s == 409 and j.get("error") == "set_aside", (s, j))
        with fconn() as c:
            n_open = c.execute("SELECT COUNT(*) FROM scan_rescan_ask WHERE done_at IS NULL AND withdrawn_at IS NULL").fetchone()[0]
        check("the asks on the copy: 2 open (B-0199 by the owner, B-0181 by Shavez); the refused ones wrote nothing", n_open == 2, n_open)
        m0 = (md5f(dbp), md5f(adb))
        so, ho = GET("manoj", "/finance/porders/s454/scans")
        ss, hs = GET("shavez", "/finance/porders/s454/scans")
        m1 = (md5f(dbp), md5f(adb))
        to, ts = _html.unescape(ho), _html.unescape(hs)
        say("   Scans to redo for the owner: %s; for Shavez: %s" % ([l for l in text_lines(ho) if l.startswith("B-")][:12], [l for l in text_lines(hs) if l.startswith("B-")][:12]))
        check("C: 'Scans to redo' -- the owner in English (Part of the bill is cut off / Get it rescanned / Open the scan, the thumbnail with ?v=), Shavez in "
              "Roman Hindi; its read leaves BOTH databases byte-equal",
              so == 200 and ss == 200 and "Scans to redo" in to and "Get it rescanned:" in to and "Open the scan" in to and "/thumb?v=" in ho
              and "Scan dobara karwane hain" in ts and "Dobara scan karwaiye:" in ts and m0 == m1, (so, ss, m0 == m1))
        sh, hh = GET("manoj", "/finance/porders")
        check("the owner's home links 'Scans to redo: N' while there is any", 'id="redo"' in hh and "Scans to redo:" in _html.unescape(hh), sh)
        # the staff-eye walk: every login the kit affects
        dm = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8"))
        d = [x for x in dm["duties"] if x["id"] == "reception.rescan"]
        with fconn() as c:
            n = c.execute(d[0]["due_sql"]).fetchone()[0] if d else None
        for who in ("reception", "alisha", "shivani"):
            tiles = portal_tiles(who)
            s_, h_ = GET(who, d[0]["door"] if d else "/finance/porders", headers=(REC if who == "reception" else None))
            check("C: staff-eye: %s -- duty reception.rescan due (n %s): the tile '%s' on the portal home and '%s' on %s"
                  % (who, n, d[0]["tile"] if d else "?", d[0]["door_marker"] if d else "?", d[0]["door"] if d else "?"),
                  bool(d) and n and d[0]["tile"] in tiles and s_ == 200 and d[0]["door_marker"] in _html.unescape(h_), (bool(d), n, tiles, s_))
        for who in ("manoj", "shavez", "darpan"):
            tiles = portal_tiles(who)
            say("   the portal as %s: tiles %s" % (who, tiles))
    section("4  send back to reception: the owner, Shavez, the refusals; Scans to redo writes nothing; the staff-eye", s4)

    # ============================================================================================ 5 the rescan replaces the old scan
    def intake_post(fields, fbytes, fname):
        import io
        data = dict(fields)
        data["client_token"] = secrets.token_hex(12)
        data["bill_scan"] = (io.BytesIO(fbytes), fname)
        AR._reader_on = lambda: False                          # no reading thread: the walk fills the reading itself (no real call)
        r = acl.post("/intake/scan_submit", data=data, content_type="multipart/form-data", headers={"Cookie": "clinic_who=alisha", "Accept": "application/json"})
        try:
            return r.status_code, r.get_json() or {}
        except Exception:                                      # noqa: BLE001
            return r.status_code, {}

    def snap_fin():
        with fconn() as c:
            out = {}
            for t, q in (("tie", "SELECT * FROM order_scan_tie ORDER BY order_id"), ("ask", "SELECT * FROM scan_rescan_ask ORDER BY id"),
                         ("ans", "SELECT * FROM s454_scan_answer ORDER BY asset_bill_id, kind"), ("state", "SELECT * FROM purchase_scan_state ORDER BY asset_bill_id"),
                         ("link", "SELECT * FROM purchase_scan_link ORDER BY bill_id"), ("orders", "SELECT id, status FROM purchase_order ORDER BY id")):
                try:
                    out[t] = [tuple(r) for r in c.execute(q)]
                except sqlite3.Error:
                    out[t] = None
        return out

    def s5():
        AR.current_user = lambda: {"id": None, "username": "reception", "display_name": "Reception", "role": "reception", "active": 1}
        i199, i176 = ids_of("B-0199", "B-0176")
        with aconn() as c:
            o199 = dict(c.execute("SELECT * FROM bills WHERE id=?", (i199,)).fetchone())
            cr = c.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1", (i199,)).fetchone()
        rd199 = json.loads(cr[0])
        with fconn() as c:
            t48 = dict(c.execute("SELECT * FROM order_scan_tie WHERE asset_bill_id=?", (i199,)).fetchone())
            ven = c.execute("SELECT vendor FROM purchase_order WHERE id=?", (t48["order_id"],)).fetchone()[0]
            c.execute("UPDATE purchase_order SET status='cancelled' WHERE created_by='w618walk'")
            oid = OS.make_order(c, "w618walk", ven, [{"item": "W618 TEST ITEM", "packs": 1}], "sent", "call",
                                created_at=(dt.datetime.now() - dt.timedelta(hours=2)).replace(microsecond=0).isoformat(), note="W618 walk: another order of the supplier waiting")
            c.execute("INSERT OR IGNORE INTO s454_scan_answer (asset_bill_id, kind, answer, value, by, at) VALUES (?,?,?,?,?,?)",
                      (i199, "w618", "yes", "a person's decision", "w618walk", OS.now_iso()))
            had_state = c.execute("SELECT 1 FROM purchase_scan_state WHERE asset_bill_id=?", (i199,)).fetchone()
            if not had_state:
                c.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at, paper_amount, chosen_vendor) VALUES (?,?,?,?,?,?)",
                          (i199, "amount_differs", "W618 walk", OS.now_iso(), 416000, ven))
            else:
                c.execute("UPDATE purchase_scan_state SET paper_amount=COALESCE(paper_amount, 416000) WHERE asset_bill_id=?", (i199,))
            c.commit()
        ntie0 = len(snap_fin()["tie"])
        raw = open(os.path.join(ups, ORIG["B-0199"][1]), "rb").read()             # the same paper: its own first bytes (same image, same triple)
        s, j = intake_post({"lane": "pharmacy", "vendor": ven, "bill_month": "2026-10", "rescan_of": str(i199)}, raw, "bill_2026-10-22_1.pdf")
        nid = j.get("id")
        with aconn() as c:
            nb = dict(c.execute("SELECT * FROM bills WHERE id=?", (nid,)).fetchone()) if nid else {}
            ob = dict(c.execute("SELECT * FROM bills WHERE id=?", (i199,)).fetchone())
        say("   the rescan of B-0199 (its own bytes, rescan_of in the fields): %s -> %s %s status %s rescan_of %s dup_of %s; B-0199 now %s '%s'"
            % (s, nb.get("stamp_no"), nid, nb.get("status"), nb.get("rescan_of"), nb.get("dup_of"), ob["status"], ob.get("reject_reason")))
        check("C: the rescan of the same paper stays captured and is the rescan of B-0199; the old scan is set aside 'rescanned as %s' (kept, its file kept)" % nb.get("stamp_no"),
              s == 200 and nb.get("status") == "captured" and nb.get("rescan_of") == i199 and ob["status"] == "rejected"
              and ob.get("reject_reason") == "rescanned as %s" % nb.get("stamp_no") and os.path.exists(os.path.join(ups, ob["source_stored"])), (s, nb.get("status"), nb.get("dup_of")))
        if not nid:
            return
        # the reading lands (the same triple) -- the stubbed check, no real call
        calls = []
        real = getattr(CL, "check_scan", None)
        if real:
            CL.check_scan = lambda p, db_path=None: calls.append(p) or {"pages": [{"turn": 0}], "whole_bill": True, "totals_visible": True, "legible": True, "note": "", "model": "stub"}
        try:
            hdr, items = CL.to_bill(rd199)
            AR._bg_extract(nid, os.path.join(ups, nb["source_stored"]), _reading=(hdr, items))
        finally:
            if real:
                CL.check_scan = real
        with aconn() as c:
            nb2 = dict(c.execute("SELECT * FROM bills WHERE id=?", (nid,)).fetchone())
        check("C: after its reading (vendor, bill no and total the same as B-0199's) the rescan is still captured -- no duplicate rule takes it (%s)" % nb2.get("dup_why"),
              nb2["status"] == "captured" and not nb2.get("dup_of"), (nb2["status"], nb2.get("dup_of"), nb2.get("dup_why")))
        with fconn() as c:
            made = OS.tie_pass(c, "w618")
        f1 = snap_fin()
        with fconn() as c:
            t = c.execute("SELECT * FROM order_scan_tie WHERE order_id=?", (t48["order_id"],)).fetchone()
            t2 = c.execute("SELECT * FROM order_scan_tie WHERE order_id=?", (oid,)).fetchone()
            ask = c.execute("SELECT * FROM scan_rescan_ask WHERE asset_bill_id=? ORDER BY id DESC", (i199,)).fetchone()
            cans = c.execute("SELECT answer FROM s454_scan_answer WHERE asset_bill_id=? AND kind='w618'", (nid,)).fetchone()
            cst = c.execute("SELECT paper_amount FROM purchase_scan_state WHERE asset_bill_id=?", (nid,)).fetchone()
            ost = c.execute("SELECT paper_amount FROM purchase_scan_state WHERE asset_bill_id=?", (i199,)).fetchone()
        say("   one tie_pass: made %s; order %s's tie -> scan %s stamp %s scan_at %s; the walk's other %s order: %s; the ask: done %s -> %s"
            % (made, t48["order_id"], t and t["asset_bill_id"], t and t["stamp"], t and t["scan_at"], ven, t2 and tuple(t2), ask and ask["done_at"], ask and ask["done_bill_id"]))
        check("C: order %d's tie now points to the rescan (its stamp), scan_at kept (%s) -- NO new tie: the other waiting order of the supplier stays untied"
              % (t48["order_id"], t48["scan_at"]), t is not None and t["asset_bill_id"] == nid and t["stamp"] == nb["stamp_no"] and t["scan_at"] == t48["scan_at"]
              and t2 is None and len(f1["tie"]) == ntie0, (t and tuple(t), t2 and tuple(t2), len(f1["tie"]), ntie0))
        check("C: the people's decisions copied to the rescan (s454_scan_answer, purchase_scan_state's paper amount), the old rows kept",
              cans is not None and cst is not None and cst[0] == 416000 and ost is not None, (cans, cst, ost))
        check("C: the ask on B-0199 closed by the rescan (done_bill_id, done_at); reception's row now counts only Shavez's ask",
              ask is not None and ask["done_bill_id"] == nid and ask["done_at"] and P4._s618_open_count(fconn()) == 1, ask and tuple(ask))
        # an ask on an UNTIED scan (B-0176, a Challan) closes on its rescan
        s, j = POST("manoj", "/finance/porders/api/s454/rescan", {"asset_bill_id": i176, "reason": "not_bill"})
        s2_, j2 = intake_post({"lane": "pharmacy", "vendor": "W618 OTHER SUPPLIER", "bill_month": "2026-10", "rescan_of": str(i176)}, CL._made_up_pdf(), "bill_2026-10-22_2.pdf")
        with fconn() as c:
            OS.tie_pass(c, "w618")
            a176 = c.execute("SELECT done_bill_id FROM scan_rescan_ask WHERE asset_bill_id=? ORDER BY id DESC", (i176,)).fetchone()
        check("C: an ask on an untied scan (B-0176, kind Challan) closes on its rescan", s == 200 and a176 is not None and a176[0] == j2.get("id"), (s, a176, j2.get("id")))
        f2a = snap_fin()
        with fconn() as c:
            OS.tie_pass(c, "w618")
        f2b = snap_fin()
        check("a second tie_pass changes nothing (the ties, the asks, the answers, the states, the links, the orders)", f2a == f2b and bool(f2a["tie"]),
              [k for k in f2a if f2a[k] != f2b[k]])
        sh, hh = GET("reception", "/finance/porders", headers=REC)
        row = re.search(r'id="row_rescan"[^>]*><span class="n">(\d+)</span>', hh)
        check("reception's row counts the one ask left (Shavez's B-0181)", row is not None and row.group(1) == "1", row and row.group(1))
        s3_, j3 = intake_post({"lane": "pharmacy", "vendor": "W618 THIRD SUPPLIER", "bill_month": "2026-10"}, CL._made_up_pdf() + b"\n% w618 next\n", "bill_2026-10-22_3.pdf")
        with aconn() as c:
            r3 = c.execute("SELECT rescan_of, status FROM bills WHERE id=?", (j3.get("id"),)).fetchone()
        check("the next, unrelated bill (no rescan_of in its fields) is a plain scan: rescan_of NULL", s3_ == 200 and r3 is not None and r3[0] is None, (s3_, r3 and tuple(r3)))
    section("5  the rescan replaces the old scan: same paper kept, the old set aside, the re-point before the loop, the asks closed", s5)

    # ============================================================================================ 6b nothing else moved; 7 DUTY_MAP
    def s6b():
        calls = []
        real = getattr(CL, "check_scan", None)
        if real:
            CL.check_scan = lambda p, db_path=None: calls.append(p) or None
        made = []
        with aconn() as c:
            for lane, kind, st in (("clinic", "Consumable", "draft"), ("lab_purchase", "Lab", "captured")):
                cur = c.execute("INSERT INTO bills (kind, source_stored, source_orig, stamp_no, status, submitted_by, submitted_at, lane, ocr_status) "
                                "VALUES (?,?,?,?,?,'w618walk',?,?, 'read')", (kind, ORIG["B-0201"][1], "w618.pdf", "W618-%s" % lane.upper()[:3], st,
                                                                               dt.datetime.now().strftime("%Y-%m-%d %H:%M"), lane))
                made.append(cur.lastrowid)
            c.commit()
        try:
            for b in made:
                if hasattr(AR, "_s618_lie"):
                    AR._s618_lie(b)
        finally:
            if real:
                CL.check_scan = real
        with aconn() as c:
            nl = c.execute("SELECT COUNT(*) FROM scan_lie WHERE bill_id IN (%d,%d)" % tuple(made)).fetchone()[0] if "scan_lie" in {r[0] for r in c.execute("SELECT name FROM sqlite_master")} else 0
        check("a clinic-lane and a lab-lane scan get no check call (%d calls) and no scan_lie row (%d)" % (len(calls), nl), not calls and nl == 0, (calls, nl))
        src = open(os.path.join(fin, "porders_s454.py"), encoding="utf-8").read()
        check("C: scan_quality is imported inside a function in porders_s454, never at its top (a failing import never takes reception's screen down)",
              "import scan_quality" in src and not re.search(r"^import scan_quality|^from scan_quality", src, re.M))
        ar_src = open(os.path.join(ar, "asset_register.py"), encoding="utf-8").read()
        check("C: one DDL of scan_lie (claude_reader.LIE_DDL is asset_register's S618_LIE_DDL, byte for byte)",
              hasattr(CL, "LIE_DDL") and getattr(AR, "S618_LIE_DDL", None) == CL.LIE_DDL and ar_src.count("CREATE TABLE IF NOT EXISTS scan_lie") == 1)
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
        r = fcl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("6b nothing else moved: the other lanes; the import; one DDL; healthz", s6b)

    def s7():
        dm = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8"))
        d = [x for x in dm["duties"] if x["id"] == "reception.rescan"]
        with fconn() as c:
            row = c.execute(d[0]["due_sql"]).fetchone() if d else None
        check("C: DUTY_MAP v18 carries reception.rescan (tile Purchase orders, door /finance/porders, marker 'Phir se scan karo'); its due_sql is ONE "
              "read-only SELECT returning (n, since) on the copy: %s" % (str(tuple(row)) if row else "none",),
              dm.get("version") == 18 and bool(d) and d[0]["door_marker"] == "Phir se scan karo" and d[0]["due_sql"].lstrip().upper().startswith("SELECT")
              and ";" not in d[0]["due_sql"].strip().rstrip(";") and row is not None and len(row) == 2, (dm.get("version"), bool(d)))
    section("7  DUTY_MAP v17 -> v18: reception.rescan", s7)

    json.dump({"bar": st1.get("bar"), "redo": st1.get("redo"), "turned": st1.get("turned")}, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in reds:
            say("  red: %s" % l[:200])
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S618: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S618: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S618: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S618: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

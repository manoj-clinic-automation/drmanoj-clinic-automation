#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s536.py -- kit S536_AMIR_BOARD_D712: the walk (the brief's section 3), on the server, on scratch copies only.

    python3 -B walk_s536.py --kit DIR --work /tmp/... --run DIR --por DIR --db finance.db --adb assets.db --spine spine.db [--map FILE]

  run       the installer's scratch layout: <run>/new/finance (the three built files), <run>/old/finance (the box as it is), each with
            marg_ingest beside it.
  por       a scratch copy of /root/portal's code; the walk writes its OWN secret and user store there (never the live ones).
  db/adb    backup-API copies of finance.db and assets.db; spine: of the LIVE spine.db.  Every probe works on its own further copies.
Probes run as fresh processes per side (NEW / OLD), signed in through the walk-only portal as amir and as the owner, with ORDER_PUSH_STUB,
a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a phone.  The walk's own rows are found by key (W536 ..., the made-up
roots 9536001..9536005), never by counting.  Every named control is the same probe on the OLD files and is printed red.
The made-up roots' orthotic proof is a stand-in that answers "done" once every orthotic batch is entered (the walk tests amir_day's line,
not the spine proof, which S524/S528 walked); the real root and the no-orthotic root run the real proof path.
No person, phone or account number is in this file."""
import argparse
import datetime as dt
import html as _html
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
import traceback

TAG = "W536JSON "
USERS = {"amir": "staff", "manoj": "doctor"}
BASE_URL = "https://followup.dr-manoj.in"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
VENDOR = "W536 VENDOR"
LINE = "live orthotic ordering can start"
ROOT_A, ROOT_B, ROOT_D, ROOT_D2, ROOT_N = 9536001, 9536002, 9536003, 9536004, 9536005
MADE_UP = 9536000
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:1500] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def red(label, cond, got=None):
    """A control: the same probe on the OLD files must show the fault (printed RED)."""
    N[0] += 1
    print(("  RED  control: " if cond else "  FAIL control did not go red: ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append("control: " + label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def vis(h):
    h = re.sub(r"(?is)<(style|script|title)[^>]*>.*?</\1>", " ", h or "")
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()


def ddmm(ts):
    t = str(ts or "").replace("T", " ")
    return "%s-%s" % (t[8:10], t[5:7]) if len(t) >= 10 else ""


def norm_json(x):
    """Drop what moves between two reads of the same copy (stamps, timings) before old and new are compared."""
    if isinstance(x, dict):
        return {k: norm_json(v) for k, v in x.items() if not re.search(r"(^|_)(at|ms|now|generated|stamp|time|took|age)($|_)", k)}
    if isinstance(x, list):
        return [norm_json(v) for v in x]
    return x


# ============================================================================================================== the probe (one per side)
def probe():
    SIDE, FIN, POR = os.environ["SIDE"], os.environ["FINDIR"], os.environ["PORDIR"]
    DB, ADB, BASE, ADB0 = os.environ["FINANCE_DB"], os.environ["ASSETS_DB"], os.environ["W536_BASE"], os.environ["W536_ADB0"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    assert AD.__file__.startswith(FIN) and SA.__file__.startswith(FIN) and SW.__file__.startswith(FIN), (AD.__file__, SA.__file__)
    R = dict(side=SIDE)
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W536J"])["pw"]
    ck = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE_URL, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
    R["signed_in"] = {w: bool(ck[w]["Cookie"][len("clinic_sso="):]) for w in USERS}
    now = dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)
    TODAY = now.date().isoformat()
    R["today"] = TODAY

    def iso(d):
        return d.strftime("%Y-%m-%dT%H:%M:%S")

    def clear_caches():
        for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE"):
            if hasattr(SA, nm):
                getattr(SA, nm).clear()

    def load():
        copydb(BASE, DB)
        copydb(ADB0, ADB)
        clear_caches()

    def C():
        c = sqlite3.connect(DB, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def cols(c, t):
        return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t).fetchall()]

    def ins(c, table, row):
        row = dict(row)
        for _cid, name, typ, notnull, dflt, pk in c.execute("PRAGMA table_info(%s)" % table).fetchall():
            if notnull and dflt is None and not pk and name not in row:
                row[name] = 0 if "INT" in (typ or "").upper() else ""
        ks = [k for k in row if k in cols(c, table)]
        return c.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(ks), ", ".join("?" * len(ks))), [row[k] for k in ks]).lastrowid

    def GET(path, who):
        t0 = time.perf_counter()
        r = fc.get(path, base_url=BASE_URL, headers=ck[who])
        ms = int((time.perf_counter() - t0) * 1000)
        return r.status_code, r.get_data(as_text=True), ms

    def block(name, fn):
        try:
            R[name] = fn()
        except Exception as e:                                          # noqa: BLE001
            R[name] = dict(error="%s: %s" % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-1500:])

    # ---- the proof stand-in, for the walk's made-up roots only (the same on both sides)
    real_proof = SA._s446_proof

    def proof(con, root, keys, ent, batches):
        if int(root) >= MADE_UP:
            keys = list(keys)
            if not keys or any(k not in ent for k in keys):
                return dict(state="wait", rows=[], text="")
            return dict(state="done", rows=[], unseen=[], as_before="", as_after="W536 stand-in", last_at=iso(now), items=len(keys),
                        proven_on={}, text="")
        return real_proof(con, root, keys, ent, batches)
    SA._s446_proof = proof

    def mkroot(c, rid, n_ortho, n_med, n_entered, a_at=None, b_at=None):
        """A made-up root (the newest count_id with voucher lines, so the one amir_stage and amir_day read): n_ortho orthotic batches,
        n_med medicine batches, the first n_entered orthotic batches entered; optional A / B 'verified' events at the given moments."""
        tot = n_ortho + n_med
        for i in range(tot):
            o = i < n_ortho
            ins(c, "stock_voucher_line", dict(count_id=rid, round_no=1, kind="ISSUE", batch_no=i + 1, batches_n=tot, line_no=1,
                                              section=("Orthotics" if o else "W536 Medicine"), family="", item="W536 %s %d" % ("ORTHO" if o else "MED", i + 1),
                                              packing="", pack=1, marg_from=5, change=-1, marg_to=4, counted=4, reason="W536", made_by="W536",
                                              made_at=iso(now - dt.timedelta(days=10))))
        for i in range(n_entered):
            ins(c, "stock_voucher_entered", dict(count_id=rid, round_no=1, kind="ISSUE", batch_no=i + 1, marg_voucher_no="W536-%d" % (i + 1),
                                                 entered_on=TODAY, by_user="amir", at=iso(now - dt.timedelta(days=2))))
        if a_at:
            ins(c, "stock_stage_event", dict(count_id=rid, stage="A", event="verified", ref="", at=a_at, detail="W536"))
        if b_at:
            ins(c, "stock_stage_event", dict(count_id=rid, stage="B", event="verified", ref="", at=b_at, detail="W536"))
        c.commit()

    def release(c, rid):
        r = c.execute("SELECT MIN(at), COUNT(*) FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release'", (rid,)).fetchone()
        return [r[0], int(r[1] or 0)]

    def ordering(c, rid):
        """The owner's Needs-you as amir_day builds it; the ordering line(s); the count line for rid; the stage read after."""
        clear_caches()
        lines = [l.get("text") or "" for l in AD.needs_you_lines(c)]
        st = SA.amir_stage(c) or {}
        return dict(hits=[t for t in lines if LINE in t], count_line=[t for t in lines if t.startswith("Count #%d:" % rid)], n=len(lines),
                    stage=st.get("stage"), root=st.get("count_id"), lines=lines)

    # ---------------------------------------------------------------------------------------------------- 1. the board, D712
    def b1():
        load()
        c = C()
        oid = ins(c, "purchase_order", dict(created_at=iso(now - dt.timedelta(days=6)), created_by="W536", vendor=VENDOR, status="sent"))
        ins(c, "purchase_order_line", dict(order_id=oid, item="W536 ITEM", packs=1, pack_size=1, units=1, supplied=1, arrived_by="W536",
                                           arrived_at=iso(now - dt.timedelta(days=5))))
        c.commit()
        root = SA._s446_root(c)
        c.close()
        out = dict(root=root)
        for who in ("amir", "manoj"):
            code, body, ms = GET("/finance/stock/api/pad/amir/%d" % root, who)
            try:
                j = json.loads(body)
            except ValueError:
                j = None
            out["board_" + who] = dict(code=code, bytes=len(body.encode("utf-8")), ms=ms, json=j)
        for who in ("amir", "manoj"):
            code, h, ms = GET("/finance/stock/page/amir", who)
            m = re.search(r"function restCard\(W\)\{.*?\n\}\n", h, flags=re.S)
            out["page_" + who] = dict(code=code, bytes=len(h.encode("utf-8")), maal=("maal aa gaya" in h), loop=("W.bill_pending" in h),
                                      rest_card=(m.group(0) if m else None), sunday=("data-sunday" in h), rest_id=('id="rest"' in h),
                                      heads=[x for x in ("Baaki kaam", "Sudhar", "closing stock", "Voucher") if x in h])
        code, body, ms = GET("/finance/sanjeevni/api/needs-you", "manoj")
        try:
            j = json.loads(body)
        except ValueError:
            j = {}
        lines = [l for l in (j.get("lines") or []) if isinstance(l, dict)]
        out["needs"] = dict(code=code, ms=ms, n=len(lines), vendor=[l.get("text") for l in lines if VENDOR in str(l.get("text"))],
                            keys=sorted({k for l in lines for k in l}), shapes_ok=all(isinstance(l.get("text"), str) and l.get("text") for l in lines))
        c = C()
        W = SW.amir_view(c)
        out["amir_view"] = dict(ok=W.get("ok"), has_key=("bill_pending" in W), vendor_rows=[x.get("text_hi") for x in (W.get("bill_pending") or []) if VENDOR in str(x.get("vendor"))])
        c.close()
        # not broken: the hub, steps 1-7 as amir
        out["hub_api"] = GET("/finance/stock/api/pad/hub/%d" % root, "manoj")[0]
        out["hub_page"] = GET("/finance/stock/page/hub?count=%d" % root, "manoj")[0]
        out["steps"] = {n: GET("/finance/amir/step/%d" % n, "amir")[0] for n in range(1, 8)}
        return out
    block("b1", b1)

    # ---------------------------------------------------------------------------------------------------- 2. the ordering line
    def b2a1():
        """(a) the install-day copy as it stands: the live root, its stage read by key."""
        load()
        c = C()
        root = SA._s446_root(c)
        st0 = SA.amir_stage(c, root) or {}
        A = st0.get("A") or {}
        bv = (st0.get("B") or {}).get("verified_at")
        out = dict(root=root, stage0=st0.get("stage"), A=dict(total=A.get("total"), entered=A.get("entered"), open=A.get("open"), pending=A.get("pending"),
                                                               proof=(A.get("proof") or {}).get("state")),
                   B=dict(verified_at=bv, total=(st0.get("B") or {}).get("total"), verified=(st0.get("B") or {}).get("verified")), moved=False)
        if bv and (AD._days_since(bv) or 0) > 2:                       # R1-9: the control needs B's moment within two days
            c.execute("UPDATE stock_stage_event SET at=? WHERE count_id=? AND stage='B' AND event='verified'", (iso(now), root))
            c.commit()
            out["moved"] = True
        o = ordering(c, root)
        out.update(hits=o["hits"], count_line=o["count_line"], stage=o["stage"], rel=release(c, root),
                   amir_lines=[t for t in o["lines"] if re.search(r"Count #|Orthotic|Goods tapped|ordering", t)])
        c.close()
        return out
    block("b2a1", b2a1)

    def b2a2():
        """(a) a made-up root at stage A (one orthotic voucher open after an 'A verified'), B verified an hour ago."""
        load()
        c = C()
        mkroot(c, ROOT_A, 2, 3, 1, a_at=iso(now - dt.timedelta(days=1)), b_at=iso(now - dt.timedelta(hours=1)))
        o = ordering(c, ROOT_A)
        out = dict(hits=o["hits"], count_line=o["count_line"], stage=o["stage"], root=o["root"], rel=release(c, ROOT_A))
        c.close()
        return out
    block("b2a2", b2a2)

    def b2bc():
        """(b) a made-up root whose orthotic batches are all entered and proven, B verified yesterday -> the first read reaches C and releases
        the first medicine lot; (c) the same copy with the earliest release three days back."""
        load()
        c = C()
        mkroot(c, ROOT_B, 2, 3, 2, b_at=iso(now - dt.timedelta(days=1)))
        out = dict(rel_before=release(c, ROOT_B))
        o = ordering(c, ROOT_B)
        out["b"] = dict(hits=o["hits"], count_line=o["count_line"], stage=o["stage"], root=o["root"], rel=release(c, ROOT_B))
        base_lines = o["lines"]
        # R1-3: the line's own try -- a fault in its query drops this one line only (NEW only; the OLD file has no such query)
        if hasattr(AD, "needs_you_lines"):
            class Faulty(object):
                def __init__(self, real):
                    self.__dict__["_r"] = real

                def __getattr__(self, k):
                    return getattr(self.__dict__["_r"], k)

                def __setattr__(self, k, v):
                    setattr(self.__dict__["_r"], k, v)

                def execute(self, sql, *a):
                    if "SELECT MIN(at) FROM stock_stage_event" in sql:
                        raise sqlite3.OperationalError("W536 fault")
                    return self.__dict__["_r"].execute(sql, *a)
            clear_caches()
            try:
                fl = [l.get("text") or "" for l in AD.needs_you_lines(Faulty(c))]
                out["fault"] = dict(hits=[t for t in fl if LINE in t], rest_same=(sorted(t for t in fl if LINE not in t) == sorted(t for t in base_lines if LINE not in t)),
                                    n=len(fl), n_base=len(base_lines))
            except Exception as e:                                      # noqa: BLE001
                out["fault"] = dict(error="%s: %s" % (type(e).__name__, str(e)[:200]))
        r = c.execute("SELECT MIN(id) FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release'", (ROOT_B,)).fetchone()
        back = iso(now - dt.timedelta(days=3))
        if r and r[0]:
            c.execute("UPDATE stock_stage_event SET at=? WHERE id=?", (back, r[0]))
            c.commit()
        o = ordering(c, ROOT_B)
        out["c"] = dict(hits=o["hits"], count_line=o["count_line"], stage=o["stage"], rel=release(c, ROOT_B), back=back)
        c.close()
        return out
    block("b2bc", b2bc)

    def b2d():
        """(d) a made-up root with no medicine batch: the orthotics proven, B verified an hour ago -> stage done, no release; and B three days
        back (the accepted edge, R1-6)."""
        out = {}
        for key, rid, bat in (("d", ROOT_D, now - dt.timedelta(hours=1)), ("d2", ROOT_D2, now - dt.timedelta(days=3))):
            load()
            c = C()
            mkroot(c, rid, 2, 0, 2, b_at=iso(bat))
            o = ordering(c, rid)
            out[key] = dict(hits=o["hits"], count_line=o["count_line"], stage=o["stage"], root=o["root"], rel=release(c, rid), b_at=iso(bat))
            c.close()
        return out
    block("b2d", b2d)

    def b2n():
        """(b, no stand-in) a made-up root with no orthotic batch at all, B verified yesterday: the real path straight to C."""
        load()
        c = C()
        mkroot(c, ROOT_N, 0, 3, 0, b_at=iso(now - dt.timedelta(days=1)))
        o = ordering(c, ROOT_N)
        out = dict(hits=o["hits"], count_line=o["count_line"], stage=o["stage"], root=o["root"], rel=release(c, ROOT_N))
        c.close()
        return out
    block("b2n", b2n)

    print(TAG + json.dumps(R, default=str))


# ============================================================================================================== the walk
def run_probe(a, side, Wd, store, secret, pw):
    fin = os.path.join(a.run, side, "finance")
    ing = os.path.join(a.run, side, "marg_ingest")
    wd = os.path.join(Wd, "probe_%s" % side)
    for sub in ("noring", "nomarg"):
        os.makedirs(os.path.join(wd, sub))
    dbp, adbp, spp = [os.path.join(wd, "w536_%s.db" % x) for x in ("app", "assets", "spine")]
    copydb(a.db, dbp)
    copydb(a.adb, adbp)
    copydb(a.spine, spp)
    env = dict(os.environ, SIDE=side, FINDIR=fin, INGDIR=ing, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp,
               W536_BASE=a.db, W536_ADB0=a.adb, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store,
               TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W536J=json.dumps(dict(pw=pw)),
               MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"),
               ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"),
               ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
               CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
    if a.map:
        env["DUTY_MAP_JSON"] = a.map
    for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE",
              "FINANCE_CRON_TOKEN", "AMIR_BILLS_FROM"):
        env.pop(k, None)
    t0 = time.time()
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True, timeout=3000)
    js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
    print("   the %s probe ran %d s (exit %s)" % (side, int(time.time() - t0), p.returncode))
    if not js:
        print("-- the %s probe did not finish; its last lines:" % side)
        for l in p.stdout.splitlines()[-40:]:
            print("   " + mask(l)[:300])
        return None
    return json.loads(js[-1][len(TAG):])


def errs(R):
    return {k: v.get("error") for k, v in R.items() if isinstance(v, dict) and v.get("error")}


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe":
        return probe()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--run", "--por", "--db", "--adb", "--spine"):
        ap.add_argument(k, required=True)
    ap.add_argument("--map", default="")
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W536 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for role in ("staff", "doctor"):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    fin_new, fin_old = os.path.join(a.run, "new", "finance"), os.path.join(a.run, "old", "finance")

    def txt(folder, fn):
        return io.open(os.path.join(folder, fn), encoding="utf-8").read()

    # ------------------------------------------------------------------------------------------------------------ 4. the greps
    print("-- 4 the greps on the NEW bytes (the OLD bytes the control)")
    hn, ho = txt(fin_new, "stock_amir.html"), txt(fin_old, "stock_amir.html")
    sn, so = txt(fin_new, "stock_app.py"), txt(fin_old, "stock_app.py")
    an = txt(fin_new, "amir_day.py")
    check("4: stock_amir.html: 'bill_pending' 0, 'bill entry baaki' 0, 'maal aa gaya' 0", hn.count("bill_pending") == 0 and hn.count("bill entry baaki") == 0
          and hn.count("maal aa gaya") == 0, (hn.count("bill_pending"), hn.count("bill entry baaki"), hn.count("maal aa gaya")))
    red("4 OLD: stock_amir.html carries them (%d / %d / %d)" % (ho.count("bill_pending"), ho.count("bill entry baaki"), ho.count("maal aa gaya")),
        ho.count("bill_pending") > 0 and ho.count("bill entry baaki") > 0)
    check("4: stock_app.py: 'bill_pending' 0", sn.count("bill_pending") == 0, sn.count("bill_pending"))
    so_lines = [l for l in so.splitlines() if "bill_pending" in l]
    red("4 OLD: stock_app.py carries 'bill_pending' on %d lines (the brief's 2: the empty rest and the two-line rest; %d occurrences)"
        % (len(so_lines), so.count("bill_pending")), len(so_lines) == 2)
    check("4: amir_day.py writes no stage event (no INSERT / UPDATE of stock_stage_event) and keeps reading the arrival for the owner's D712 line",
          not re.search(r"(INSERT\s+(OR\s+\w+\s+)?INTO|UPDATE)\s+stock_stage_event", an) and "bill_pending" in an)
    for fn in ("stock_app.py", "amir_day.py"):
        try:
            compile(txt(fin_new, fn), fn, "exec")
            ok = True
        except SyntaxError as e:
            ok = e
        check("4: the NEW %s compiles on this python (%s)" % (fn, sys.version.split()[0]), ok is True, ok)

    # ------------------------------------------------------------------------------------------------------------ the probes
    print("-- the probes (fresh processes, the walk-only portal session, each case on its own copy)")
    RN = run_probe(a, "new", Wd, store, secret, pw)
    RO = run_probe(a, "old", Wd, store, secret, pw)
    if RN is None or RO is None:
        check("both probes finished", False)
        return finish()
    check("both probes finished, no block raised", not errs(RN) and not errs(RO), dict(new=errs(RN), old=errs(RO)))
    for k, v in list(errs(RN).items()) + list(errs(RO).items()):
        print("   %s tb: %s" % (k, mask((RN.get(k) or RO.get(k) or {}).get("tb"))[-900:]))
    check("signed in as amir and the owner through the walk-only portal (both sides)", all(RN.get("signed_in", {}).values()) and all(RO.get("signed_in", {}).values()))
    TODAY = RN.get("today")

    # 1 -- the board, D712
    print("-- 1 the board, D712 (one arrival tapped 5 days ago by the walk, no spine purchase)")
    n1, o1 = RN.get("b1") or {}, RO.get("b1") or {}
    for who in ("amir", "manoj"):
        bn, bo = (n1.get("board_" + who) or {}), (o1.get("board_" + who) or {})
        rn, ro = ((bn.get("json") or {}).get("rest") or {}), ((bo.get("json") or {}).get("rest") or {})
        check("1 %s: the board answers 200; no 'bill_pending' key in rest (keys %s)" % (who, sorted(rn)), bn.get("code") == 200 and "bill_pending" not in rn
              and set(rn) == {"plan", "fixes"}, sorted(rn))
        orows = [x.get("item") for x in (ro.get("bill_pending") or [])]
        red("1 OLD %s: the payload carries the arrival rows %s" % (who, orows), "W536 ITEM" in orows)
        on, oo = norm_json(bn.get("json")), norm_json(bo.get("json"))
        if isinstance(oo, dict) and isinstance(oo.get("rest"), dict):
            oo["rest"].pop("bill_pending", None)
        check("3 %s: the light board JSON byte-equal old vs new on the same copy, the dropped key aside (stamps dropped)" % who,
              json.dumps(on, sort_keys=True) == json.dumps(oo, sort_keys=True), [k for k in set(on or {}) | set(oo or {}) if (on or {}).get(k) != (oo or {}).get(k)])
        check("4 %s: the board payload under 100 KB (NEW %s bytes, %s ms; OLD %s bytes, %s ms -- the first board read of a fresh process builds the "
              "stage's report)" % (who, bn.get("bytes"), bn.get("ms"), bo.get("bytes"), bo.get("ms")), 0 < (bn.get("bytes") or 0) < 100 * 1024)
    pn, po_ = n1.get("page_amir") or {}, o1.get("page_amir") or {}
    print("   1 section 4 as amir, NEW: the Sunday %s · fixes %d -> %s" % (
        "row" if ((n1.get("board_amir") or {}).get("json") or {}).get("rest", {}).get("plan") else "none",
        len((((n1.get("board_amir") or {}).get("json") or {}).get("rest") or {}).get("fixes") or []),
        "rows" if (((n1.get("board_amir") or {}).get("json") or {}).get("rest") or {}).get("fixes") or (((n1.get("board_amir") or {}).get("json") or {}).get("rest") or {}).get("plan")
        else "'Aaj kuch nahi — sab upar hai.'"))
    check("1: the rendered board as amir carries no 'maal aa gaya' (the page's restCard has no arrival loop; the payload has no row)",
          pn.get("code") == 200 and not pn.get("maal") and not pn.get("loop"), (pn.get("code"), pn.get("maal"), pn.get("loop")))
    red("1 OLD: the board prints 'maal aa gaya, Marg mein bill abhi nahi' (restCard loops W.bill_pending and the payload holds the W536 row)",
        po_.get("maal") and po_.get("loop") and "W536 ITEM" in [x.get("item") for x in ((((o1.get("board_amir") or {}).get("json") or {}).get("rest") or {}).get("bill_pending") or [])])
    rc_n, rc_o = pn.get("rest_card") or "", po_.get("rest_card") or ""
    rc_o_less = "\n".join(l for l in rc_o.split("\n") if "W.bill_pending" not in l)
    check("3: restCard otherwise as today (the Sunday rows, the fixes, the empty sentence) -- the old function less its one line",
          rc_n and rc_n == rc_o_less and "Aaj kuch nahi — sab upar hai." in rc_n and "data-sunday" in rc_n and "W.fixes" in rc_n)
    for who in ("amir", "manoj"):
        pg = n1.get("page_" + who) or {}
        check("3 %s: the board page renders (200, %s bytes; sections %s; #rest; the Sunday buttons' code)" % (who, pg.get("bytes"), pg.get("heads")),
              pg.get("code") == 200 and "Baaki kaam" in (pg.get("heads") or []) and pg.get("rest_id") and pg.get("sunday"))
    nn, no = n1.get("needs") or {}, o1.get("needs") or {}
    check("1: the owner's Needs-you still carries the D712 line for the walk's arrival", nn.get("code") == 200 and len(nn.get("vendor") or []) == 1
          and "Goods tapped as arrived" in (nn.get("vendor") or [""])[0], nn.get("vendor"))
    check("3: Needs-you shapes: every line has its text; the same keys old and new (%s)" % nn.get("keys"), nn.get("shapes_ok") and nn.get("keys") == no.get("keys"),
          (nn.get("keys"), no.get("keys")))
    av = n1.get("amir_view") or {}
    check("3: stock_watch.amir_view still returns bill_pending (the owner's D712 line reads it), the walk's arrival in it", av.get("ok") and av.get("has_key")
          and len(av.get("vendor_rows") or []) == 1, av)
    check("3: the hub (api, page) as the owner 200", n1.get("hub_api") == 200 and n1.get("hub_page") == 200, (n1.get("hub_api"), n1.get("hub_page")))
    check("3: Amir's steps 1-7 as amir 200", all(int(v) == 200 for v in (n1.get("steps") or {}).values()) and len(n1.get("steps") or {}) == 7, n1.get("steps"))

    # 2 -- the ordering line
    print("-- 2 the ordering line ('%s')" % LINE)
    a1n, a1o = RN.get("b2a1") or {}, RO.get("b2a1") or {}
    print("   2a the install-day copy: count #%s stage %s; A %s; B %s%s" % (a1n.get("root"), a1n.get("stage0"), a1n.get("A"), a1n.get("B"),
                                                                       " (B's moment set to now on the copy, R1-9)" if a1n.get("moved") else ""))
    for t in a1n.get("amir_lines") or []:
        print("      NEW Needs-you: %s" % mask(t)[:240])
    if a1n.get("stage0") == "A":
        check("2a: stage A on the install-day copy -> no 'ordering can start' line", a1n.get("hits") == [] and a1n.get("count_line"), a1n.get("hits"))
    else:
        exp = "Orthotics verified and renamed -- live orthotic ordering can start (count #%s, %s)" % (a1n.get("root"), ddmm((a1n.get("rel") or [None])[0] or (a1n.get("B") or {}).get("verified_at")))
        print("   2a NOTE: the install-day copy is at stage %s (voucher 29 entered and proven before the install, R1-4)" % a1n.get("stage0"))
        check("2a: stage %s on the install-day copy -> the line dated the first release (%s)" % (a1n.get("stage0"), a1n.get("rel")), a1n.get("hits") == [exp], a1n.get("hits"))
    if a1o.get("stage0") == "A":
        red("2a OLD: the old file prints the line at stage A (B verified within 2 days)", len(a1o.get("hits") or []) == 1, a1o.get("hits"))
    a2n, a2o = RN.get("b2a2") or {}, RO.get("b2a2") or {}
    check("2a': a made-up root at stage A (one orthotic voucher open, B verified an hour ago) -> no line (stage %s, root %s)" % (a2n.get("stage"), a2n.get("root")),
          a2n.get("stage") == "A" and a2n.get("root") == ROOT_A and a2n.get("count_line") and a2n.get("hits") == [] and (a2n.get("rel") or [0, 0])[1] == 0, a2n)
    red("2a' OLD: the old file prints it at stage A", len(a2o.get("hits") or []) == 1, a2o.get("hits"))
    bc_n, bc_o = RN.get("b2bc") or {}, RO.get("b2bc") or {}
    bn_, cn_ = bc_n.get("b") or {}, bc_n.get("c") or {}
    rel_b = bn_.get("rel") or [None, 0]
    exp_b = "Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (ROOT_B, ddmm(rel_b[0]))
    check("2b: the orthotics entered and proven, B verified yesterday -> no release before the read; the first read reaches C and writes the "
          "release (%s); Needs-you carries the line dated that day" % rel_b,
          (bc_n.get("rel_before") or [None, 1])[1] == 0 and bn_.get("stage") == "C" and rel_b[1] >= 1 and str(rel_b[0])[:10] == TODAY
          and bn_.get("hits") == [exp_b], bn_.get("hits"))
    ob = (bc_o.get("b") or {}).get("hits") or []
    print("   2b OLD prints %s (dated B's day, not the release)" % ob)
    f = bc_n.get("fault") or {}
    check("2b (R1-3): a fault in the line's own query drops this one line only -- every other Needs-you line stays (%s of %s)" % (f.get("n"), f.get("n_base")),
          f.get("hits") == [] and f.get("rest_same") is True, f)
    rel_c = cn_.get("rel") or [None, 0]
    check("2c: the earliest release set three days back -> no line; MIN(at) is the back-dated moment %s (releases now %d)" % (rel_c[0], rel_c[1]),
          cn_.get("hits") == [] and str(rel_c[0]) == cn_.get("back") and cn_.get("stage") in ("C", "done"), (cn_.get("hits"), rel_c, cn_.get("back")))
    red("2c OLD: the old file still prints it (B verified yesterday)", len((bc_o.get("c") or {}).get("hits") or []) == 1, (bc_o.get("c") or {}).get("hits"))
    dn = (RN.get("b2d") or {}).get("d") or {}
    d2n = (RN.get("b2d") or {}).get("d2") or {}
    exp_d = "Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (ROOT_D, ddmm(dn.get("b_at")))
    check("2d: a root with no medicine batch reaching done -> no release row; the line from B.verified_at", dn.get("stage") == "done"
          and (dn.get("rel") or [None, 1])[1] == 0 and dn.get("hits") == [exp_d], (dn.get("stage"), dn.get("rel"), dn.get("hits")))
    check("2d (R1-6, the accepted edge): the same with B verified three days back -> no line", d2n.get("stage") == "done" and d2n.get("hits") == [], (d2n.get("stage"), d2n.get("hits")))
    nn_ = RN.get("b2n") or {}
    rel_n = nn_.get("rel") or [None, 0]
    check("2b' (no stand-in): a root with no orthotic batch, B verified yesterday -> C on the first read, the release written, the line dated it",
          nn_.get("stage") == "C" and rel_n[1] >= 1 and nn_.get("hits") == ["Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (ROOT_N, ddmm(rel_n[0]))],
          (nn_.get("stage"), rel_n, nn_.get("hits")))
    return finish()


def finish():
    if FAILS:
        print("WALK_S536 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:260])
        return 1
    print("WALK_S536 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

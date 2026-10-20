#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s604.py -- kit S604_PAY_SHEET_FIXES (20-Oct-2026), the SERVER half. Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s604.py --fin <scratch /root/finance with the purchase_app.py under test> --db <COPY of finance.db> --adb <COPY of assets.db>
                            --marg <scratch marg_ingest with lib/> --por <scratch /root/portal copy -- the walk writes its OWN secret and user store>
                            --reader <the kit's marg_txt.py (S604)> --text <this morning's refused SUPPLIER/ITEM WISE text, a /tmp copy>
                            --kit <the kit folder (data_s604.py)> --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s604.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --kit ...
The real finance app in one process: the walk's own header session for the finance pages, its own machine token for /api/push, its own portal
sign-in (a random secret, its own user store -- never the live ones). Its own rows by key (md5 'w604...', 'W604 ...'), the live rows by key
(bills 542 / 579 by supplier key and bill number, the export 5307d3e5 by md5), never by counting. Every scenario starts from the quiet copy
(restored by the backup API). Section 0 dumps the pages FIRST on the quiet copy; --old-dump compares with the OLD file's dumps. --expect-red is the
negative control: the same walk on the OLD file, every 'C:' check must be red. No account or phone number is printed (ten digits masked).
Prints 'WALK OK S604 ...'."""
import argparse
import datetime as dt
import hashlib
import html as _html
import importlib.util
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

KIT = "S604_PAY_SHEET_FIXES"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "shavez": "manager", "amir": "staff"}
P = "/finance/purchase"
SEP = "2026-09"
MONTHS = ("2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10")
SW_5307 = "5307d3e5b82ec416cb70144a9efaeb6e"
KEY_LTD, KEY_PVT = "BASS PHARMA DISTRIBUTORS PVT LTD", "BASS PHARMA DISTRIBUTORS PVT"
ITEMWISE_EXPECT = {"2026-04": 38217400, "2026-05": 36804635, "2026-07": 47639296}      # R1, the read-time rule (paise)
SEP_ITEMWISE = 43101647
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
        check("C: section %s ran without an exception" % title[:40], False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-1200:]))


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


def strip_s604(h):
    """The page as the OLD file would print it where this kit changes nothing: the card, the saved rows and the cf_ keypad are removed."""
    h = re.sub(r"<!--s604card-->.*?<!--/s604card-->", "", h, flags=re.S)
    h = re.sub(r'<tr class="s604saved">.*?</tr>', "", h, flags=re.S)
    h = re.sub(r'(<input class="pin" id="cf_[^"]*" value="[^"]*") inputmode="numeric"', r"\1", h)
    return h


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def w604(s):
    return "w604" + hashlib.md5(("S604 " + s).encode()).hexdigest()[:28]


def h604(s):
    """A 32-hex md5 for the walk's own pushes (api/push takes nothing else); found again by this same key."""
    return hashlib.md5(("S604 walk " + s).encode()).hexdigest()


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst, timeout=60)
    s.backup(d)
    d.close()
    s.close()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def portal_setup(por):
    """The walk's OWN portal secret and user store in the scratch portal folder (S444's shape): never the live ones."""
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W604 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w604-walk-seed'\n" % secret)
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
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "SARVAM_API_KEY"):
        os.environ.pop(k, None)


class Ctx(object):
    """The loaded app, its client, the database path and the quiet copy."""

    def __init__(self, a, fin, dbp, token):
        self.a, self.fin, self.dbp, self.token = a, fin, dbp, token
        import finance_app as fa                              # noqa: E402
        import purchase_app as PA                             # noqa: E402
        for m in (fa, PA):
            assert m.__file__.startswith(fin), m.__file__
        self.fa, self.PA = fa, PA
        self.cl = fa.app.test_client(use_cookies=False)
        self.NEW = hasattr(PA, "_lock_gate")
        self.pristine = dbp + ".quiet"
        copy_db(dbp, self.pristine)

    def reset(self):
        copy_db(self.pristine, self.dbp)

    def conn(self):
        c = sqlite3.connect(self.dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def GET(self, u, path):
        r = self.cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(self, u, path, body):
        r = self.cl.post(path, base_url=BASE, json=body, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        try:
            j = r.get_json(silent=True)
        except Exception:                                      # noqa: BLE001
            j = None
        return r.status_code, (j if j is not None else r.get_data().decode("utf-8", "replace")[:300])

    def push(self, body):
        r = self.cl.post(P + "/api/push", base_url=BASE, json=body, headers={"X-Finance-Marg": self.token})
        return r.status_code, r.get_json(silent=True)

    # --- reads through the module under test
    def summary(self, c, m):
        return self.PA._month_summary(c, m)

    def gate(self, c, m):
        """(can, reasons) as the files under test decide the lock: _lock_gate on NEW, can_finalise on OLD."""
        s = self.PA._month_summary(c, m)
        if hasattr(self.PA, "_lock_gate"):
            return self.PA._lock_gate(c, m, s)
        return s["can_finalise"], s["reasons"]


def bass_rows(c):
    return [dict(r) for r in c.execute("SELECT id, supplier_norm, bill_no, bill_date, bw_md5, sw_md5, sw_amount_p, reason FROM purchase_bill "
                                       "WHERE bill_no='14538' ORDER BY id")]


def eff_ids(c, ids):
    q = ("SELECT b.id FROM purchase_bill b WHERE b.id IN (%s) AND EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
         "AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))" % ",".join("?" * len(ids)))
    return sorted(r[0] for r in c.execute(q, ids))


def sw_body(md5, stamp, rows, pf="2026-09-29", pt="2026-09-29"):
    return {"type": "SUPPLIERWISE", "md5": md5, "file": "W604_%s.XLS" % md5[:8], "period_from": pf, "period_to": pt,
            "export_stamp": stamp, "n_rows": len(rows), "grand_amount_p": sum(r["cash_p"] + r["credit_p"] for r in rows), "rows": rows}


def bass_row(amount_p=159700, name=KEY_PVT):
    return {"supplier": name, "bill_no": "14538", "bill_date": "2026-09-29", "cash_p": 0, "credit_p": amount_p}


def run_data_step(a, dbp):
    r = subprocess.run([sys.executable, "-B", os.path.join(os.path.abspath(a.kit), "data_s604.py"), "--db", dbp],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=120, cwd="/tmp")
    return r.returncode, r.stdout


def converted_payload(a, scratch):
    """This morning's text through the kit's reader (S604) into the .XLS, then through manojz's own road: marg_purchase.read_purchase and
    marg_purchase_rows.payload (the server's lib copies, the same bytes as manojz's: 0ae8f78d, 41d68148). None on the OLD reader's refusal."""
    rd = load(os.path.abspath(a.reader), "marg_txt_w604")
    raw = open(os.path.abspath(a.text), "rb").read()
    xls, info = rd.convert(raw)
    ri = list(getattr(rd, "RETURNS_INSIDE", []))
    md = hashlib.md5(xls).hexdigest()
    path = os.path.join(scratch, "PURCHASE_ITEMWISE_DEFAULT__2026-09-01_to_2026-09-30__20261020-080612__%s.XLS" % md[:8])
    open(path, "wb").write(xls)
    lib = os.path.join(os.path.abspath(a.marg), "lib")
    MP = load(os.path.join(lib, "marg_purchase.py"), "marg_purchase_w604")
    PR = load(os.path.join(lib, "marg_purchase_rows.py"), "marg_purchase_rows_w604")
    body = PR.payload(path, "ITEMWISE", read_purchase=MP.read_purchase)
    return body, ri, info, md


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    X = Ctx(a, fin, dbp, os.environ["FINANCE_MARG_TOKEN"])
    c = X.conn()
    say("STATE %s: files %s (purchase_app %s); clock %s IST" % (label, "NEW (S604)" if X.NEW else "OLD", hashlib.md5(open(os.path.join(fin, "purchase_app.py"), "rb").read()).hexdigest()[:8],
                                                             dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    for m in MONTHS:
        s = X.summary(c, m)
        st = s["status"]["status"]
        g = X.gate(c, m)
        say("STATE %s: %s %s: Marg %s, item-wise %s, %d bills, %d no lines, returns %d, signed %s; the lock %s%s"
            % (label, m, st.upper(), s["marg_p"], s["itemwise_p"], len(s["bills"]), len(s["no_lines"]), len(s["returns"]), s.get("signed", "-"),
               "FINAL (not asked)" if st == "final" else ("OPEN" if g[0] else "closed"), "" if (st == "final" or g[0]) else ": " + " | ".join(g[1])[:600]))
    for r in bass_rows(c):
        say("STATE %s: bill %d %s %s %s bw %s sw %s %s" % (label, r["id"], r["supplier_norm"], r["bill_no"], r["bill_date"], (r["bw_md5"] or "-")[:8],
                                                         (r["sw_md5"] or "-")[:8], r["reason"] or ""))
    for r in c.execute("SELECT month, vendor_norm, carry_fwd_p, paid_p, note, updated_by, updated_at FROM purchase_pay_line ORDER BY month, vendor_norm"):
        say("STATE %s: pay line %s" % (label, tuple(r)))
    s_, h = X.GET("manoj", P + "/page/pay/" + SEP)
    card = re.search(r"<!--s604card-->(.*?)<!--/s604card-->", h, flags=re.S)
    say("STATE %s: /page/pay/%s as manoj: %s; the card: %s" % (label, SEP, s_, "none (OLD file)" if not card else ""))
    for l in (text_lines(card.group(1)) if card else []):
        say("   %s" % l)
    c.rollback()
    c.close()
    say("STATE OK S604 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--por", "--reader", "--text", "--kit", "--dump", "--old-dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    for k in ("fin", "db", "adb", "marg", "kit"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k)
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S604_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)) + ((os.path.abspath(a.por),) if a.por else ()):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not (a.dump and a.por and a.reader and a.text):
        ap.error("--dump, --por, --reader and --text are needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S604 walk on the %s: %s . db %s" % ("OLD file (negative control)" if a.expect_red else "new file", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    secret, pw, store = portal_setup(os.path.abspath(a.por))
    app_env(a, dbp, token, secret, store)
    sys.path.insert(0, fin)
    os.chdir(fin)
    X = Ctx(a, fin, dbp, token)
    PA = X.PA
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; purchase_app %s (%s)"
        % ([n for n, _w in X.fa._MOUNT_FAILED] or "none", hashlib.md5(open(os.path.join(fin, "purchase_app.py"), "rb").read()).hexdigest()[:8],
           "NEW" if X.NEW else "OLD"))
    DUMP = {}
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    scratch = os.path.join(os.path.dirname(dbp), "w604")
    os.makedirs(scratch, exist_ok=True)
    BODY = {}

    def payload():
        if "b" not in BODY:
            BODY["b"], BODY["ri"], BODY["info"], BODY["md5"] = converted_payload(a, scratch)
        return BODY["b"]

    # ============================================================================================ 0 (first): the pages dumped on the quiet copy
    def s0():
        pages = [("manoj", P + "/page/pay/2026-08"), ("manoj", P + "/page/pay/2026-09"), ("manoj", P + "/page/pay/2026-10"),
                 ("manoj", P + "/page/month/2026-08"), ("manoj", P + "/page/pay/2026-09/letter"), ("manoj", P + "/page/pay/2026-09/pack"),
                 ("manoj", P + "/page/pay/2026-08/pack"), ("manoj", P + "/page/cheques/2026-09"), ("manoj", P + "/page/cheques/2026-08"),
                 ("amir", "/finance/amir"), ("shavez", "/finance/reports/aaj"), ("shavez", P + "/page/pay/2026-09")]
        changed = {}
        for u, path in pages:
            s, h = X.GET(u, path)
            for _ in range(3):
                if s in (301, 302, 303):
                    break
                break
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l) for l in text_lines(strip_s604(h))]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("the page %s as %s answers (%s, %d bytes)" % (path, u, s, len(h)), s in (200, 302, 303, 403), s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                if old != lines:
                    os_, ns = set(old), set(lines)
                    gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                    changed[(u, path)] = (gone, new)
                    say("   CHANGED %s for %s: %d gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:5]:
                        say("      - %s" % l[:220])
                    for l in new[:5]:
                        say("      + %s" % l[:220])
                else:
                    say("   unchanged %s for %s" % (path, u))
        # the hub, month by month: August (FINAL), September and October must not move; May, June, July carry 3.2 / 3.5's changes
        s, h = X.GET("manoj", P + "/page/hub")
        rows = {}
        for m_, body in re.findall(r'<tr><td><a href="[^"]*/page/month/(\d{4}-\d{2})">(.*?)</tr>\s*<tr><td colspan="8"[^>]*>(?:.*?)</td></tr>', h, flags=re.S):
            rows[m_] = body
        stories = dict(re.findall(r'/page/month/(\d{4}-\d{2})">.*?</tr>\s*<tr><td colspan="8"[^>]*>(.*?)</td></tr>', h, flags=re.S))
        DUMP["hub"] = {m_: [rows.get(m_), stories.get(m_)] for m_ in rows}
        say("   the hub: months %s" % sorted(rows))
        if OLD.get("hub"):
            for m_ in sorted(rows):
                o = OLD["hub"].get(m_)
                same = o == [rows.get(m_), stories.get(m_)]
                say("   hub %s: %s%s" % (m_, "unchanged" if same else "CHANGED", "" if same else " -- story OLD: %s | NEW: %s" % (_html.unescape((o or [None, ""])[1] or "")[:260], _html.unescape(stories.get(m_) or "")[:260])))
                if m_ in ("2026-08", "2026-09", "2026-10"):
                    check("the hub's %s row is byte-equal to the OLD file's (the kit changes nothing there on the quiet copy)" % m_, same)
        if a.old_dump:
            check("every page dump (the pay pages of Aug/Sep/Oct minus the card, the saved rows and the cf_ keypad; Aug's month page; Sep's letter; the packs; "
                  "the cheque registers; Amir's day; Shavez's reports and pay page) is byte-equal to the OLD file's (%d differ)" % len(changed),
                  not changed, {k: (v[0][:3], v[1][:3]) for k, v in changed.items()})
    section("0 (first) the pages dumped on the quiet copy -- byte-equal OLD vs NEW where this brief changes nothing", s0)

    # ============================================================================================ 5b: no recursion; the money readers equal OLD vs NEW (quiet copy)
    def s5b():
        X.reset()
        c = X.conn()
        got = {}
        for m in MONTHS:
            t0 = time.time()
            s = X.summary(c, m)
            _s, groups = PA._pay_rows(c, m)
            adv = PA._advice_rows_s265(c, m)
            v = PA._verify_statement(c, m)
            g = X.gate(c, m)
            got[m] = dict(marg=s["marg_p"], bills=len(s["bills"]), itemwise=s["itemwise_p"], status=s["status"]["status"],
                          pay=sorted([g_["norm"], g_["payable_p"], g_["route"], g_["total_p"]] for g_ in groups),
                          advice=sorted([r["vendor"], r["rupees"]] for r in adv[0]), advice_total=adv[1], verify_ok=v["ok"],
                          gate=bool(g[0]), reasons=list(g[1]), can_old=s["can_finalise"], secs=round(time.time() - t0, 2))
            say("   %s %s: Marg %s, item-wise %s, %d bills, verify %s; the lock %s (%.2fs)" % (m, got[m]["status"].upper(), s["marg_p"], s["itemwise_p"], len(s["bills"]),
                                                                                         v["ok"], "OPEN" if g[0] else "closed", got[m]["secs"]))
            if got[m]["status"] != "final" and not g[0]:
                for r in g[1]:
                    say("        - %s" % r[:300])
        c.close()
        DUMP["s5b"] = got
        check("C: (5) _month_summary, _pay_rows, _advice_rows_s265, _verify_statement and the gate return on every month April-October (no recursion)",
              all(m in got for m in MONTHS) and X.NEW, sorted(got))
        if OLD.get("s5b"):
            o = OLD["s5b"]
            same = all(o[m]["marg"] == got[m]["marg"] and o[m]["bills"] == got[m]["bills"] and o[m]["pay"] == got[m]["pay"]
                       and o[m]["advice"] == got[m]["advice"] and o[m]["advice_total"] == got[m]["advice_total"] for m in MONTHS)
            check("(5) every money reader equal OLD vs NEW on every month April-October: Marg total, bills, every vendor's payable and lane, the advice lines",
                  same, [m for m in MONTHS if o[m]["pay"] != got[m]["pay"] or o[m]["advice"] != got[m]["advice"]])
            iw = {m: (o[m]["itemwise"], got[m]["itemwise"]) for m in MONTHS if o[m]["itemwise"] != got[m]["itemwise"]}
            say("   item-wise OLD -> NEW where it moved: %s" % iw)
            check("(5) only April, May and July's item-wise figures move (3.2), and to R1's figures; August (FINAL) untouched",
                  sorted(iw) == ["2026-04", "2026-05", "2026-07"] and all(got[m]["itemwise"] == ITEMWISE_EXPECT[m] for m in iw), iw)
            say("   the lock, April-October, OLD -> NEW on the quiet copy:")
            for m in MONTHS:
                say("     %s: %s -> %s" % (m, "FINAL" if o[m]["status"] == "final" else ("open" if o[m]["gate"] else "closed"),
                                         "FINAL" if got[m]["status"] == "final" else ("open" if got[m]["gate"] else "closed")))
            check("(5) the gate on the quiet copy: April, May, June closed (no supplier-wise statement); July open; August FINAL untouched; September, October closed",
                  [got[m]["gate"] for m in ("2026-04", "2026-05", "2026-06", "2026-07", "2026-09", "2026-10")] == [False, False, False, True, False, False]
                  and got["2026-08"]["status"] == "final", {m: got[m]["gate"] for m in MONTHS})
        for m in ("2026-04", "2026-05", "2026-07"):
            check("C: (2) %s item-wise is R1's figure %d (its return lines counted as returns)" % (m, ITEMWISE_EXPECT[m]), got[m]["itemwise"] == ITEMWISE_EXPECT[m], got[m]["itemwise"])
    section("5b the money readers on every month (no recursion), the item-wise figures, the gate April-October", s5b)

    # ============================================================================================ 2: returns counted (3.2), the converted text pushed
    def s2():
        X.reset()
        body = payload()
        say("   this morning's text through the kit's reader: %d rows, returns inside at line(s) %s, sheet md5 %s; payload %d rows, %s..%s, grand %s"
            % (BODY["info"].get("rows", -1), BODY["ri"], BODY["md5"][:8], len(body["rows"]), body["period_from"], body["period_to"], body["grand_amount_p"]))
        check("(1) the kit's reader takes this morning's text, L.K.'s block (line 177) 'returns inside'", BODY["ri"] == [177], BODY["ri"])
        st, j = X.push(body)
        check("the converted rows are taken by /api/push (stored, new)", st == 200 and j and j.get("stored") is True, (st, j))
        c = X.conn()
        s = X.summary(c, SEP)
        neg = sorted(b["id"] for b in s["bills"] if b["marg_p"] < 0)
        lk = sorted(b["id"] for b in s["bills"] if b["marg_p"] < 0 and b["supplier_norm"].startswith("L.K."))
        say("   September after the push: item-wise %s, returns %s, signed %s, the minus bills %s (L.K.: %s), no lines %s"
            % (s["itemwise_p"], [x["bill"]["id"] for x in s["returns"]], s.get("signed"), neg, lk, [(b["id"], b["bill_no"]) for b in s["no_lines"]]))
        check("C: (2) September item-wise = 43,101,647 paise (Marg's GRAND TOTAL)", s["itemwise_p"] == SEP_ITEMWISE, s["itemwise_p"])
        check("C: (2) September's returns bucket is empty", s["returns"] == [], [x["bill"]["id"] for x in s["returns"]])
        check("C: (2) signed = the three L.K. bills with Marg's minus sign", sorted(s.get("signed") or []) == lk and len(lk) == 3, (s.get("signed"), lk))
        _s, groups = PA._pay_rows(c, SEP)
        flags = {b["id"]: b["flag"] for g in groups for b in g["bills"] if b["id"] in lk}
        check("C: (2) each L.K. return reads 'a purchase return ... counted as a return' on the sheet, and no 'needs correcting'",
              len(flags) == 3 and all("counted as a return" in f and "needs correcting" not in f for f in flags.values()), flags)
        DUMP["s2"] = dict(itemwise=s["itemwise_p"], signed=s.get("signed"), lk=lk)
        c.close()
        # April, May, July: the old flag goes
        c = X.conn()
        for m in ("2026-04", "2026-05", "2026-07"):
            _s, groups = PA._pay_rows(c, m)
            fl = [b["flag"] for g in groups for b in g["bills"] if b["flag"] and ("return" in b["flag"])]
            check("C: (2) %s: no return is flagged 'may be an entry that needs correcting'" % m, fl and not any("needs correcting" in f for f in fl), fl[:3])
        c.close()
        s_, h = X.GET("manoj", P + "/page/month/" + SEP)
        check("C: (2) September's month page: the L.K. returns read 'agrees' with the return words", s_ == 200 and h.count("counted as a return") == 3, (s_, h.count("counted as a return")))
    section("2  returns counted as returns: the converted text pushed, September 43,101,647, April / May / July", s2)

    # ============================================================================================ 3: the clipped-name twin (3.3)
    def s3():
        X.reset()
        c = X.conn()
        b0 = bass_rows(c)
        say("   the quiet copy's 14538 rows: %s" % [(r["id"], r["supplier_norm"], (r["bw_md5"] or "-")[:8], (r["sw_md5"] or "-")[:8]) for r in b0])
        real = [r for r in b0 if r["supplier_norm"] == KEY_LTD]
        twin = [r for r in b0 if r["supplier_norm"] == KEY_PVT]
        check("the copy holds the two rows the brief read (LTD with bill-wise, PVT with supplier-wise 5307d3e5)", len(real) == 1 and len(twin) == 1
              and twin[0]["sw_md5"] == SW_5307 and real[0]["sw_md5"] is None, b0)
        RID, TID = real[0]["id"], twin[0]["id"]
        # (a) a copy holding only the real row: a supplier-wise push of the clipped name joins it
        c.execute("DELETE FROM purchase_bill WHERE id=?", (TID,))
        c.commit()
        a0 = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='twin_joined'").fetchone()[0]
        st, j = X.push(sw_body(h604("sw1"), "20261020-090000", [bass_row()]))
        r1 = bass_rows(c)
        aud = [dict(r) for r in c.execute("SELECT ref, detail FROM purchase_audit WHERE action='twin_joined'")]
        say("   (a) push of '%s' 14538 onto the copy holding only %d: %s -> rows %s; twin_joined %s" % (KEY_PVT, RID, (st, j), [(r["id"], r["supplier_norm"], (r["sw_md5"] or "-")[:8]) for r in r1], aud))
        check("C: (3a) no new row; bill %d gains the supplier-wise md5; one twin_joined audit row naming both keys" % RID,
              len(r1) == 1 and r1[0]["id"] == RID and r1[0]["sw_md5"] == h604("sw1") and len(aud) == a0 + 1 and KEY_PVT in aud[-1]["detail"] and KEY_LTD in aud[-1]["detail"], (r1, aud))
        # (b) a second supplier-wise push (new md5, later stamp, same clipped row)
        st, j = X.push(sw_body(h604("sw2"), "20261020-100000", [bass_row()]))
        r2 = bass_rows(c)
        check("C: (3b) a second supplier-wise push of the clipped name after the join: still one row, the real bill takes the new md5",
              len(r2) == 1 and r2[0]["id"] == RID and r2[0]["sw_md5"] == h604("sw2"), [(r["id"], r["supplier_norm"], (r["sw_md5"] or "-")[:8]) for r in r2])
        # (e) a clipped name with a different amount stays two rows (both files)
        st, j = X.push(sw_body(h604("sw3"), "20261020-110000", [bass_row(159800)]))
        r3 = bass_rows(c)
        check("(3e) a clipped name with a different amount stays two rows (a new row, no join)", len(r3) == 2, [(r["id"], r["supplier_norm"]) for r in r3])
        c.close()
        # (c) after the data step: a supplier-wise push of the clipped name lands on the real bill, the twin stays retired
        X.reset()
        rc, out = run_data_step(a, dbp)
        say("   the data step on the copy: rc %s: %s" % (rc, out.strip().splitlines()[0] if out.strip() else ""))
        c = X.conn()
        st, j = X.push(sw_body(h604("sw4"), "20261020-120000", [bass_row()]))
        r4 = {r["id"]: r for r in bass_rows(c)}
        e4 = eff_ids(c, [RID, TID])
        say("   (c) after the data step, push of the clipped name: %s -> 542 sw %s, 579 sw %s; effective %s" % ((st, j), (r4[RID]["sw_md5"] or "-")[:8], (r4[TID]["sw_md5"] or "-")[:8], e4))
        check("C: (3c) a supplier-wise push after the data step: %d stays not effective, %d takes the md5" % (TID, RID),
              rc == 0 and r4[TID]["sw_md5"] is None and r4[RID]["sw_md5"] == h604("sw4") and e4 == [RID], (rc, e4, r4[RID]["sw_md5"], r4[TID]["sw_md5"]))
        c.close()
        # (d) MANNAT / DEEPAM 502: two true bills stay two
        X.reset()
        c = X.conn()
        pair = [dict(r) for r in c.execute("SELECT id, supplier, supplier_norm, bill_date, amount_p FROM purchase_bill WHERE bill_no='502' AND bill_date='2026-08-18'")]
        if len(pair) == 2:
            rows = [{"supplier": p["supplier"], "bill_no": "502", "bill_date": "2026-08-18", "cash_p": 0, "credit_p": p["amount_p"]} for p in pair]
            st, j = X.push(sw_body(h604("sw5"), "20261020-130000", rows, "2026-08-18", "2026-08-18"))
            after = [r[0] for r in c.execute("SELECT id FROM purchase_bill WHERE bill_no='502' AND bill_date='2026-08-18' ORDER BY id")]
            tj = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='twin_joined' AND detail LIKE '%\"502\"%'").fetchone()[0]
            check("(3d) MANNAT / DEEPAM 502 (18-Aug, both Rs 10,641): a supplier-wise push of both stays two rows, no join", after == sorted(p["id"] for p in pair) and tj == 0, (after, tj))
        else:
            check("(3d) the copy holds the MANNAT / DEEPAM 502 pair", False, pair)
        c.close()
        # (f) the data step: September 86 bills, Rs 4,31,016, verify ok, the cheque lane Rs 1,597; twice changes nothing
        X.reset()
        c = X.conn()
        s0 = X.summary(c, SEP)
        _s, g0 = PA._pay_rows(c, SEP)
        bass0 = sum(g["payable_p"] for g in g0 if g["route"] != "NEFT" and g["norm"].startswith("BASS PHARMA"))
        c.close()
        rc1, out1 = run_data_step(a, dbp)
        c = X.conn()
        s1 = X.summary(c, SEP)
        v1 = PA._verify_statement(c, SEP)
        _s, g1 = PA._pay_rows(c, SEP)
        bass1 = sum(g["payable_p"] for g in g1 if g["route"] != "NEFT" and g["norm"].startswith("BASS PHARMA"))
        neft0, neft1 = sum(g["payable_p"] for g in g0 if g["route"] == "NEFT"), sum(g["payable_p"] for g in g1 if g["route"] == "NEFT")
        snap1 = [tuple(r) for r in c.execute("SELECT * FROM purchase_bill WHERE id IN (?,?) ORDER BY id", (RID, TID))]
        c.close()
        rc2, out2 = run_data_step(a, dbp)
        c = X.conn()
        snap2 = [tuple(r) for r in c.execute("SELECT * FROM purchase_bill WHERE id IN (?,?) ORDER BY id", (RID, TID))]
        nmerge = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='twin_merge' AND ref='542<-579'").fetchone()[0]
        c.close()
        say("   (f) before the step: %d bills, Marg %s, Bass cheque %s; after: %d bills, Marg %s, verify %s %s, Bass cheque %s; NEFT %s -> %s"
            % (len(s0["bills"]), s0["marg_p"], bass0, len(s1["bills"]), s1["marg_p"], v1["ok"], v1["problems"][:2], bass1, neft0, neft1))
        say("   the second run: %s" % (out2.strip().splitlines()[0] if out2.strip() else ""))
        check("(3f) the data step: September 86 bills, Rs 4,31,016, the cross-check agrees, the cheque lane owes Rs 1,597 (was Rs 3,194); the NEFT lane unmoved",
              rc1 == 0 and len(s1["bills"]) == 86 and s1["marg_p"] == 43101600 and v1["ok"] and bass1 == 159700 and bass0 == 319400 and neft0 == neft1,
              (rc1, len(s1["bills"]), s1["marg_p"], v1["ok"], bass0, bass1))
        check("(3f) run twice: nothing changes, one twin_merge audit row", rc2 == 0 and snap1 == snap2 and nmerge == 1 and "SKIPPED" in out2, (rc2, nmerge))
    section("3  the clipped-name twin: the join, the re-export, the retired twin, the true pairs, the data step", s3)

    # ============================================================================================ 4 and 5: the card and the lock
    def card_lines(u="manoj"):
        s_, h = X.GET(u, P + "/page/pay/" + SEP)
        m = re.search(r"<!--s604card-->(.*?)<!--/s604card-->", h, flags=re.S)
        return s_, (text_lines(m.group(1)) if m else None)

    def line_of(lines, label):
        return next((l for l in (lines or []) if l.startswith(label)), "")

    def s45():
        X.reset()
        s_, L = card_lines()
        for l in L or ["(no card)"]:
            say("   [quiet copy] %s" % l)
        check("C: (4) the quiet copy: the card is at the top of September's page", s_ == 200 and L is not None and L[0] == "Month-end reports for September 2026", (s_, (L or [""])[0]))
        check("C: (4) supplier-wise received 11-Oct 10:32, 01-30 Sep, 86 bills, its total Rs 4,31,016 against the sheet",
              line_of(L, "Supplier-wise statement").startswith("Supplier-wise statement — Received 11-Oct 10:32 · 01–30 Sep · 86 bills · its total ₹4,31,016"), line_of(L, "Supplier-wise"))
        check("C: (4) bill-wise received 11-Oct 10:32, 01-30 Sep, 86 bills", line_of(L, "Bill-wise statement") == "Bill-wise statement — Received 11-Oct 10:32 · 01–30 Sep · 86 bills", line_of(L, "Bill-wise"))
        check("C: (4) item lines received, with 7 bills missing and the export to make", "but 7 bills still have no item lines" in line_of(L, "Item lines")
              and "export SUPPLIER/ITEM WISE PURCHASE STATEMENT, FROM 01-09-2026 TO 30-09-2026, as a TEXT file" in line_of(L, "Item lines"), line_of(L, "Item lines"))
        check("C: (4) this morning's refusal (08:06, line 177) is shown once under the card", sum(1 for l in L or [] if l.startswith("The medical PC refused a purchase report at 08:06")) == 1
              and any("it could not read it (line 177). Nothing for you to redo." in l for l in L or []), [l for l in L or [] if "refused" in l])
        # after 4.2's push: 1 bill missing
        st, j = X.push(payload())
        s_, L = card_lines()
        check("C: (4) after the push of this morning's lines: 1 bill still missing (Bass's twin 14538)", "but 1 bill still has no item lines (29 Sep)" in line_of(L, "Item lines"), line_of(L, "Item lines"))
        check("C: (4) the refusal line is gone once a covering item report arrived after it", L is not None and not any(l.startswith("The medical PC refused") for l in L), [l for l in L or [] if "refused" in l])
        rc, out = run_data_step(a, dbp)
        s_, L = card_lines()
        for l in L or ["(no card)"]:
            say("   [with the push and the data step] %s" % l)
        c = X.conn()
        g = X.gate(c, SEP)
        c.close()
        check("C: (4)(5) with the push and the data step: the green line, and the lock gate open", rc == 0 and "All three reports are in and agree — the month can be locked." in (L or [])
              and g[0] is True and X.NEW, (rc, g))
        say("   the gate then: %s" % (g,))
        s_, h = X.GET("manoj", P + "/page/month/" + SEP)
        check("(5) the month page then shows the FINALISE button to the doctor", "FINALISE September 2026" in h)
        # 5307d3e5 removed
        c = X.conn()
        c.execute("DELETE FROM purchase_export WHERE md5=?", (SW_5307,))
        c.commit()
        c.close()
        s_, L = card_lines()
        check("C: (4) with 5307d3e5 removed: 'Not yet -- export from Marg as a TEXT file: SUPPLIER WISE PURCHASE STATEMENT, FROM 01-09-2026 TO 30-09-2026'",
              line_of(L, "Supplier-wise statement") == "Supplier-wise statement — Not yet — export from Marg as a TEXT file: SUPPLIER WISE PURCHASE STATEMENT, FROM 01-09-2026 TO 30-09-2026",
              line_of(L, "Supplier-wise"))
        c = X.conn()
        g = X.gate(c, SEP)
        c.close()
        check("C: (5) with 5307d3e5 removed the gate is closed with the supplier-wise reason", g[0] is False and any(r.startswith("the supplier-wise statement for 01–30 Sep has not reached the server") for r in g[1]), g)
        s_, h = X.GET("manoj", P + "/page/month/" + SEP)
        check("C: (5) ... and the month page shows no FINALISE button, the reason listed", "FINALISE September 2026" not in h and "has not reached the server" in h)
        # a supplier-wise ending on the 28th
        c = X.conn()
        ins(c, "purchase_export", dict(md5=w604("sw28"), type="SUPPLIERWISE", file="W604_28.XLS", period_from="2026-09-01", period_to="2026-09-28",
                                       export_stamp="20261020-140000", received_at=dt.datetime.now().replace(microsecond=0).isoformat(), n_rows=1, grand_amount_p=0))
        c.commit()
        v = PA._verify_statement(c, SEP)
        c.close()
        s_, L = card_lines()
        check("C: (4) a supplier-wise statement ending on the 28th: 'Not yet' on the card and the cross-check says 'No supplier-wise ...' (the old -28 rule took it)",
              line_of(L, "Supplier-wise statement").startswith("Supplier-wise statement — Not yet") and v["problems"] and v["problems"][0].startswith("No supplier-wise")
              and v["export"] is None, (line_of(L, "Supplier-wise"), v["problems"][:1], (v["export"] or {}).get("md5")))
        # api_finalise refuses on the gate
        st, j = X.POST("manoj", P + "/api/finalise", {"month": SEP})
        say("   api/finalise as the doctor with the supplier-wise statement gone: %s %s" % (st, j))
        check("C: (5) api/finalise refuses September while the supplier-wise statement is missing (409, the reason named)", st == 409 and isinstance(j, dict)
              and any("supplier-wise" in r for r in j.get("reasons") or []), (st, j))
        c = X.conn()
        stt = c.execute("SELECT status FROM purchase_month WHERE month=?", (SEP,)).fetchone()
        c.close()
        check("(5) ... and September is not locked on the copy", stt is None or stt[0] != "final", stt and tuple(stt))
        # a refusal after the covering exports shows; a covering item report after it clears it
        X.reset()
        c = X.conn()
        t_ref = dt.datetime.now().replace(microsecond=0)
        ins(c, "mi_file", dict(md5=w604("ref1"), drive_name="W604 refused", type="", verdict="REFUSED", pc_verdict="REFUSED",
                               reason="the medical PC refused it: PURCHASE text -- the reader refused it (line 999)", received_at=t_ref.isoformat() + "+05:30"))
        c.commit()
        c.close()
        s_, L = card_lines()
        check("C: (4) a reader-stop refusal received after 30-Sep and after the covering exports: one plain line under the card",
              any(l.startswith("The medical PC refused a purchase report at %s" % t_ref.strftime("%H:%M")) and "(line 999). Nothing for you to redo." in l for l in L or []),
              [l for l in L or [] if "refused" in l])
        time.sleep(1.2)
        st, j = X.push(payload())
        s_, L = card_lines()
        check("C: (4) gone once a covering item report is received after it", L is not None and not any(l.startswith("The medical PC refused") for l in L) and st == 200,
              [l for l in L or [] if "refused" in l])
        # the other refusal form: its first clause only
        c = X.conn()
        t2 = dt.datetime.now().replace(microsecond=0) + dt.timedelta(seconds=5)
        ins(c, "mi_file", dict(md5=w604("ref2"), drive_name="W604 refused 2", type="", verdict="REFUSED", pc_verdict="REFUSED",
                               reason="the medical PC refused it: PURCHASE text -- a purchase statement the reader cannot take (its title or column heads are not the ones it knows)",
                               received_at=t2.isoformat() + "+05:30"))
        c.commit()
        c.close()
        s_, L = card_lines()
        check("(4) another refusal reason: 'The medical PC refused a purchase report at hh:mm: <its first clause>.'",
              any(l == "The medical PC refused a purchase report at %s: a purchase statement the reader cannot take." % t2.strftime("%H:%M") for l in L or []),
              [l for l in L or [] if "refused" in l])
        # the staff-eye: Shavez sees the same English lines; the owner's and Shavez's portal homes render (the walk's own portal)
        s_, Ls = card_lines("shavez")
        say("   shavez on /page/pay/%s: %s; card %s" % (SEP, s_, "seen" if Ls else "not seen"))
        if s_ == 200:
            check("(4) staff-eye: Shavez, opening the payment page, sees the same English card", Ls is not None and Ls[0] == "Month-end reports for September 2026", Ls and Ls[:1])
        homes = {}
        try:
            sys.path.insert(0, os.path.abspath(a.por))
            import portal as po                                # noqa: E402
            pc = po.app.test_client(use_cookies=False)
            for u in ("manoj", "shavez"):
                r = pc.post("/portal/login", base_url=BASE, data={"user": u, "password": pw[u]})
                m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
                r3 = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + (m.group(1) if m else "")})
                homes[u] = (r.status_code, r3.status_code)
        except Exception as e:                                 # noqa: BLE001
            homes["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        finally:
            if os.path.abspath(a.por) in sys.path:
                sys.path.remove(os.path.abspath(a.por))
        say("   the portal (the walk's own secret and store): %s" % homes)
        check("(4) staff-eye: the owner's and Shavez's portal homes render (no duty is added, moved or removed by this kit)", homes.get("manoj", (0, 0))[1] == 200 and homes.get("shavez", (0, 0))[1] == 200, homes)
    section("4/5 the card on September's page, the refusal line, the lock gate, api/finalise", s45)

    # ============================================================================================ 6: the two boxes (3.6)
    def s6():
        X.reset()
        c = X.conn()
        _s, groups = PA._pay_rows(c, SEP)
        ag = next((g for g in groups if g["norm"].startswith("AGARWAL SURGICALS")), None)
        nf = next((g for g in groups if g["route"] == "NEFT" and not g["norm"].startswith("AGARWAL") and g["carry_p"] is None and g["paid_p"] is None), None)
        c.close()
        check("the copy carries Agarwal's September line and a NEFT vendor with nothing typed", ag is not None and nf is not None)
        V = ag["norm"]
        tot = ag["total_p"]
        say("   Agarwal's September: total %s, carried in %s, paid %s, payable %s" % (tot, ag["carry_p"], ag["paid_p"], ag["payable_p"]))
        typed = "−%d" % (tot // 100)
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": SEP, "vendor_norm": V, "carry_fwd": typed, "paid": ""})
        c = X.conn()
        row = c.execute("SELECT carry_fwd_p, paid_p, note FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (SEP, V)).fetchone()
        adv = PA._advice_rows_s265(c, SEP)[0]
        c.close()
        say("   post carry_fwd %r: %s %s; stored %s" % (typed, st, j if not isinstance(j, dict) else {k: j.get(k) for k in ("ok", "carry_fwd_p", "payable_p", "payable", "updated_by")}, tuple(row) if row else None))
        check("C: (6) carry_fwd '%s' (U+2212) is stored -%d, payable 0 in the reply, the vendor absent from the advice" % (typed, tot), st == 200 and row and row[0] == -tot
              and isinstance(j, dict) and j.get("payable_p") == 0 and not any(r["vendor"] == ag["name"] for r in adv), (st, row and tuple(row)))
        c = X.conn()
        before = tuple(c.execute("SELECT * FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (SEP, V)).fetchone())
        c.close()
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": SEP, "vendor_norm": V, "carry_fwd": "4OO", "paid": ""})
        c = X.conn()
        after = tuple(c.execute("SELECT * FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (SEP, V)).fetchone())
        c.close()
        check("C: (6) '4OO' answers 400 malformed with words, the row unchanged", st == 400 and isinstance(j, dict) and j.get("error") == "malformed"
              and "could not be read" in (j.get("message") or "") and after == before, (st, j, before == after))
        for typed2, want in (("–400", -40000), ("-400/-", -40000), ("400/-", 40000)):
            st, j = X.POST("manoj", P + "/api/pay-line", {"month": SEP, "vendor_norm": nf["norm"], "carry_fwd": typed2, "paid": ""})
            c = X.conn()
            r_ = c.execute("SELECT carry_fwd_p FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (SEP, nf["norm"])).fetchone()
            c.close()
            check("C: (6) carry_fwd %r is read as %d" % (typed2, want), st == 200 and r_ and r_[0] == want, (st, r_ and r_[0]))
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": SEP, "vendor_norm": nf["norm"], "carry_fwd": "", "paid": "", "note": "W604 walk note"})
        st2, j2 = X.POST("manoj", P + "/api/pay-line", {"month": SEP, "vendor_norm": nf["norm"], "carry_fwd": "", "paid": ""})
        c = X.conn()
        n_ = c.execute("SELECT note FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (SEP, nf["norm"])).fetchone()
        c.close()
        check("C: (6) a stored note, then a post without the note key: the note is kept", st == 200 and st2 == 200 and n_ and n_[0] == "W604 walk note", (st, st2, n_ and n_[0]))
        s_, h = X.GET("manoj", P + "/page/pay/" + SEP)
        cf = re.search(r'<input class="pin" id="cf_%s"[^>]*>' % re.escape(_html.escape(V, quote=True)), h) or re.search(r'<input class="pin" id="cf_[^"]*"[^>]*>', h)
        saved = re.findall(r'<tr class="s604saved"><td[^>]*>(.*?)</td></tr>', h, flags=re.S)
        say("   the sheet: cf_ box %s; saved lines %s" % (cf.group(0)[:120] if cf else None, [_html.unescape(x)[:120] for x in saved][:4]))
        check("C: (6) the sheet: no inputmode=\"numeric\" on any Carried-in box; Paid keeps its keypad", s_ == 200 and not re.search(r'id="cf_[^"]*" value="[^"]*" inputmode="numeric"', h)
              and re.search(r'id="pd_[^"]*" value="[^"]*" inputmode="numeric"', h) is not None)
        check("C: (6) the sheet: 'Saved dd-Mon hh:mm by manoj -- payable now Rs 0' under Agarwal, and the note under the vendor that has one",
              any(_html.unescape(x).startswith("Saved ") and " by manoj — payable now ₹0" in _html.unescape(x) for x in saved)
              and any("note: W604 walk note" in _html.unescape(x) for x in saved), [_html.unescape(x)[:100] for x in saved][:4])
        check("C: (6) the page's script shows 'Saved -- payable now' beside the box before the reload", "Saved \\u2014 payable now " in h and "setTimeout(function(){location.reload();},1200)" in h)
        # Paid moves no money figure
        c = X.conn()
        _s, g0 = PA._pay_rows(c, SEP)
        a0 = PA._advice_rows_s265(c, SEP)
        c.close()
        bs = load(os.path.join(fin, "bank_sms.py"), "bank_sms_w604")
        c = X.conn()
        n0 = bs.neft_portion_p(c, SEP)
        c.close()
        _, hp0 = X.GET("manoj", P + "/page/pay/%s/pack" % SEP)
        _, hc0 = X.GET("manoj", P + "/page/cheques/%s" % SEP)
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": SEP, "vendor_norm": nf["norm"], "carry_fwd": "", "paid": "12345"})
        c = X.conn()
        _s, g1 = PA._pay_rows(c, SEP)
        a1 = PA._advice_rows_s265(c, SEP)
        n1 = bs.neft_portion_p(c, SEP)
        c.close()
        _, hp1 = X.GET("manoj", P + "/page/pay/%s/pack" % SEP)
        _, hc1 = X.GET("manoj", P + "/page/cheques/%s" % SEP)
        pk = lambda h: [l for l in text_lines(h) if "12,345" not in l and l != "12345"]
        check("(6) Paid typed moves no payable, advice line, NEFT portion, cheque register line (the pack differs only by the Paid figure itself)",
              st == 200 and [(g["norm"], g["payable_p"]) for g in g0] == [(g["norm"], g["payable_p"]) for g in g1]
              and [(r["vendor"], r["rupees"]) for r in a0[0]] == [(r["vendor"], r["rupees"]) for r in a1[0]] and n0 == n1 and text_lines(hc0) == text_lines(hc1),
              (st, n0, n1))
        say("   the pack's lines that differ after Paid typed: %s" % [l for l in set(pk(hp1)) ^ set(pk(hp0))][:4])
    section("6  the two boxes: a phone's minus, an unreadable figure refused, the note kept, the saved line, Paid moves nothing", s6)

    # ============================================================================================ 7: the greps
    def s7():
        src = open(os.path.join(fin, "purchase_app.py"), encoding="utf-8").read()

        def body(name):
            m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|[A-Z_]+ = )|\Z)" % re.escape(name), src, flags=re.S | re.M)
            return m.group(0) if m else ""
        ms = body("_month_summary")
        check("C: (7) one gate: _lock_gate defined once; read by api_finalise, page_hub, page_month and the card; _month_summary calls no gate, report or cross-check",
              src.count("def _lock_gate(") == 1 and "_lock_gate(" in body("api_finalise") and "_lock_gate(" in body("page_hub") and "_lock_gate(" in body("page_month")
              and "_lock_gate(" in body("_s604_reports_card") and bool(ms) and not any(x in ms for x in ("_lock_gate(", "_verify_statement(", "_month_reports(")))
        check("C: (7) one arrival reader: _month_reports defined once; the month's last day in _verify_statement, no '-28'",
              src.count("def _month_reports(") == 1 and '"-28"' not in body("_verify_statement") and "_s604_last_day(month)" in body("_verify_statement"))
        check("C: (7) the note=excluded.note of api_finalise untouched; api_pay_line writes the note only when the request carries it",
              src.count("note=excluded.note") == 3 and 'if "note" in b:' in body("api_pay_line"))
        check("no run of ten digits in purchase_app.py's S604 lines or the walk's own output", not re.search(r"\d{10}", "\n".join(l for l in src.splitlines() if "S604" in l or "s604" in l) + "\n".join(OUT)))
        r = X.cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("7  the greps (one fact, one place) and healthz", s7)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old file: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old file): %s" % l)
        if greens:
            say("WALK RED S604: %d control(s) did not go red on the old file" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old file (%d)" % len(reds))
        say("WALK OK negative control S604: %d controls red on the old file" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S604: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S604: %d checks, %d controls green on the new file" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

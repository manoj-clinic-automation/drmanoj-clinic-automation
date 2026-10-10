#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s513.py -- S513_RENEWALS_EXPIRY: a renewal counted to its REAL expiry (D689, F-775) -- walked.

  usage: walk_s513.py --apply <apply_s513.py> --finance <folder holding finance_app.py and its sibling files>

The finance app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with the kit's edits), each with an
EMPTY database made from the app's own schema and NO asset database. Each then answers the health page as a made-up
checker through the same situations -- a made-up renewals feed in the old shape (no expiryISO) and in the new one --
and takes a made-up push through its own token door. The old file's answer is the yardstick: a feed in the old shape
must mean what it meant (only the words move), and every OTHER row of the page must be the old file's. Then the
selftest's own renewals block is run, as written in each file, against its own throwaway feed: green on both.
Dates are counted from today. Nothing live is opened.  Last line: WALK_S513 GREEN|RED.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "bff362c38ec61526ea0047fd136df826"
TO = "ec5b3ab170ff37c63ac98f6f1f11ad09"
MARK = "@@S513JSON@@ "
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:700]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def child():
    import datetime
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    root = os.environ["S513_ROOT"]
    if not os.path.realpath(fa.DB_PATH).startswith(os.path.realpath(root) + os.sep) or \
            not os.path.realpath(fa.RENEWALS_STATE).startswith(os.path.realpath(root) + os.sep):
        print(MARK + json.dumps({"abort": "the finance database or the renewals feed is not the scratch one"}))
        return
    con = sqlite3.connect(fa.DB_PATH)
    con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES ('medical','wdoctor','checker',1)")
    con.commit()
    con.close()
    c = fa.app.test_client()
    H = {"X-Clinic-User": "wdoctor"}
    today = datetime.date.today()
    day = lambda n: (today + datetime.timedelta(days=n)).isoformat()
    feed = fa.RENEWALS_STATE
    tok = os.environ["FINANCE_RENEWALS_TOKEN"]

    def set_feed(items, hours_ago=0):
        if items is None:
            if os.path.exists(feed):
                os.remove(feed)
            return
        rows = []
        for it in items:
            r = {"note": ""}
            for k, v in it.items():
                r[k] = day(v) if k in ("dateISO", "expiryISO") and isinstance(v, int) else v
            rows.append(r)
        with open(feed, "w", encoding="utf-8") as fh:
            json.dump({"received_at": (datetime.datetime.now() - datetime.timedelta(hours=hours_ago)).isoformat(timespec="seconds"),
                       "window_days": 30, "items": rows}, fh)

    def look():
        r = c.get("/finance/api/health", headers=H)
        j = r.get_json() or {}
        row = [x for x in (j.get("checks") or []) if x.get("key") == "renewals"]
        rest = sorted((x["key"], x["state"], x["detail"]) for x in (j.get("checks") or []) if x.get("key") not in ("renewals", "nevfired"))
        hc = sqlite3.connect(fa.DB_PATH)
        hc.row_factory = sqlite3.Row
        try:
            head = fa._health_headline(hc)
        finally:
            hc.close()
        when = lambda t: re.sub(r"(pushed|last push) \d{4}-\d\d-\d\d \d\d:\d\d", r"\1 <when>", t or "") if t is not None else None
        for x in row:
            x["detail"] = when(x["detail"])
        return {"http": r.status_code, "row": row[0] if row else None, "n": len(row), "rest": rest, "worst": j.get("worst"),
                "culprit": "Renewals" in (j.get("culprits") or []), "head": when(head)}

    S = {}
    set_feed(None)
    S["A_no_feed"] = look()
    set_feed([{"vendor": "GoDaddy domain", "dateISO": 50}])
    S["B_old_shape_50"] = look()
    set_feed([{"vendor": "GoDaddy domain", "dateISO": 40}])
    S["B2_old_shape_40"] = look()
    set_feed([{"vendor": "GoDaddy domain", "dateISO": 12}])
    S["C_old_shape_12"] = look()
    set_feed([{"vendor": "Tailscale key", "dateISO": 3}, {"vendor": "GoDaddy domain", "dateISO": 12}])
    S["C2_old_shape_3_and_12"] = look()
    set_feed([{"vendor": "dr-manoj.in", "dateISO": -4}])
    S["D_old_shape_overdue"] = look()
    set_feed([{"vendor": "Tailscale key", "dateISO": 3}], hours_ago=100)
    S["E_stale_with_3"] = look()
    set_feed([{"vendor": "GoDaddy domain", "dateISO": 80}], hours_ago=100)
    S["E2_stale_nothing_near"] = look()
    set_feed([{"vendor": "Arms licence renewal - Manoj", "dateISO": -13, "expiryISO": 77}])
    S["F_alert_gone_expiry_77"] = look()
    set_feed([{"vendor": "Arms licence renewal - Manoj", "dateISO": -50, "expiryISO": 40}])
    S["G_expiry_40"] = look()
    set_feed([{"vendor": "Arms licence renewal - Manoj", "dateISO": -85, "expiryISO": 5}])
    S["H_expiry_5"] = look()
    set_feed([{"vendor": "Arms licence renewal - Manoj", "dateISO": -90, "expiryISO": 0}])
    S["I_expiry_today"] = look()
    set_feed([{"vendor": "Arms licence renewal - Manoj", "dateISO": -91, "expiryISO": -1}])
    S["J_expired_yesterday"] = look()
    set_feed([{"dateISO": 3}, {"vendor": "GoDaddy domain", "dateISO": 12}])
    S["K_one_row_without_a_name"] = look()

    # the push door, with a made-up token
    set_feed(None)
    P = {}
    r = c.post("/finance/api/renewals-push", headers={"X-Finance-Renewals": tok}, json={"window_days": 45, "items": [
        {"vendor": "Arms licence renewal - Manoj", "dateISO": day(-13), "expiryISO": day(77), "note": ""},
        {"vendor": "Older script row", "dateISO": day(20), "note": "kept"},
        {"vendor": "Bad expiry", "dateISO": day(21), "expiryISO": "31-12-2026"},
        {"vendor": "", "dateISO": day(5), "expiryISO": day(5)},
        {"vendor": "No date", "expiryISO": day(5)}]})
    P["http"] = r.status_code
    P["stored"] = (r.get_json() or {}).get("stored")
    P["file"] = json.load(open(feed, encoding="utf-8"))["items"] if os.path.exists(feed) else None
    P["after"] = look()
    r = c.post("/finance/api/renewals-push", headers={"X-Finance-Renewals": "wrong-" + tok}, json={"items": []})
    P["wrong_token"] = r.status_code
    P["no_login_health"] = c.get("/finance/api/health", headers={"X-Finance-Renewals": tok}).status_code
    out = {"S": S, "P": P, "days": {str(n): day(n) for n in (-13, -4, -1, 0, 3, 5, 12, 20, 21, 40, 77)}}

    # the selftest's own renewals block, exactly as this file writes it
    src = open(os.path.join(os.getcwd(), "finance_app.py"), encoding="utf-8").read()
    a = src.index("    # ---- S196 Task#8: the renewals feed (push surface + health card) -------")
    b = src.index("    # ---- S196 HLT2: the health headline finally reaches the tile -----------")
    block = "\n".join(l[4:] if l.startswith("    ") else l for l in src[a:b].splitlines())
    res = {"ok": [], "fail": []}

    def st_check(name, cond):
        res["ok" if cond else "fail"].append(name)
    os.environ.setdefault("FINANCE_DEV_USER", "")
    os.environ.setdefault("FINANCE_DEV_ROLE", "")
    made = []
    try:
        exec(compile(block, "selftest-renewals-block", "exec"), fa.__dict__,
             {"c": c, "check": st_check, "_s461_made": made, "tempfile": tempfile})
        res["ran"] = True
    except Exception as ex:                                        # noqa: BLE001
        res["ran"] = "%s: %s" % (type(ex).__name__, ex)
    for d in made:
        shutil.rmtree(d, ignore_errors=True)
    res["state_restored"] = os.path.realpath(fa.RENEWALS_STATE) == os.path.realpath(feed)
    res["assets_env"] = os.environ.get("ASSETS_DB")
    out["selftest_block"] = res
    print(MARK + json.dumps(out))


def make_app(src, dst):
    os.makedirs(dst)
    for pat in ("*.py", "*.sql", "*.html", "*.json"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024 and not f.endswith("renewals_state.json"):
                shutil.copy2(f, dst)
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))


def make_db(appdir):
    con = sqlite3.connect(os.path.join(appdir, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(appdir, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    con.commit()
    con.close()


def run(root, tag, appdir):
    base = os.path.join(root, "run_" + tag)
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    e = dict(os.environ)
    # the tokens below are made up afresh at every run -- never the box's, and no value is written in this file
    e.update({"S513_ROOT": base, "FINANCE_DB": os.path.join(base, "finance.db"), "FINANCE_SCAN_DIR": os.path.join(base, "scans"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "FINANCE_ALLOW_HEADER_AUTH": "1",
              "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "", "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "FINANCE_RENEWALS_TOKEN": "walkrn-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(base, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(base, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(base, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups_shared"),
              "ASSETS_DB": os.path.join(base, "no_such_assets.db"),
              "FINANCE_AUTOAPPLY_OFF": os.path.join(base, "AUTOAPPLY_OFF_absent"), "PYTHONDONTWRITEBYTECODE": "1"})
    shutil.move(os.path.join(appdir, "finance.db"), os.path.join(base, "finance.db"))
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--negative", action="store_true", help="walk the OLD file as if it were the new one: must go RED")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s513_walk_")
    try:
        walk(a, root)
    except Exception as ex:                                        # a walk that breaks is a RED walk, never a traceback
        check("the walk itself ran to its end", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print("  kept: %s" % root)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S513 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    make_app(fin, old)
    check("0.1 the unpatched finance_app.py is the file this kit was built from (bff362c3, the 10-Oct bundle's bytes)",
          md5(os.path.join(old, "finance_app.py")) == FROM, md5(os.path.join(old, "finance_app.py")))
    if md5(os.path.join(old, "finance_app.py")) != FROM:
        return
    shutil.copytree(old, new)
    if not a.negative:
        p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
        got = md5(os.path.join(new, "finance_app.py"))
        check("0.2 the edits apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
        p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
        check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    so = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read().splitlines()
    sn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read().splitlines()
    import difflib
    ops = [o for o in difflib.SequenceMatcher(None, so, sn, autojunk=False).get_opcodes() if o[0] != "equal"]
    ZONES = ((11925, 11935), (11750, 11870), (11965, 12005), (12378, 12436))   # 1-based, in the OLD file
    inz = lambda i: any(lo <= i + 1 <= hi for lo, hi in ZONES)
    outside = [(o[0], o[1] + 1, o[2]) for o in ops if not (inz(o[1]) and (o[2] == o[1] or inz(o[2] - 1)))]
    check("0.4 every change lies inside the renewals code: the window constant, the push door, the health row, the selftest's "
          "renewals block (%d places; nothing else in 13,538 lines moved)" % len(ops), not outside and len(ops) >= 10, outside)
    for d in (old, new):
        make_db(d)
    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag] = run(root, tag, d)
        check("0.5 the %s app answered the health page through every situation" % tag,
              bool(R[tag]) and "abort" not in R[tag] and len(R[tag].get("S", {})) == 14
              and all(v["http"] == 200 and v["n"] == 1 for v in R[tag]["S"].values()),
              (R[tag] or {}).get("abort") or p.stderr[-700:])
    if not (R.get("old") and R.get("new") and "S" in R["old"] and "S" in R["new"]):
        return
    o, n, D = R["old"]["S"], R["new"]["S"], R["new"]["days"]
    row = lambda S, k: S[k]["row"] or {}

    # ---- 1 · nothing else on the page has moved
    check("1.1 in every situation, every OTHER row of the health page is the old file's", all(n[k]["rest"] == o[k]["rest"] for k in n))
    check("1.2 no feed yet: the Renewals row, the page's colour and the tile line are the old file's", n["A_no_feed"] == o["A_no_feed"])

    # ---- 2 · a feed in the old shape (no expiryISO) means what it meant; only the words and the window move
    check("2.1 a renewal 50 days out: quiet ok on both; the new words say 'nothing expires inside 45 days'",
          row(o, "B_old_shape_50")["state"] == "ok" and row(n, "B_old_shape_50")["state"] == "ok"
          and row(n, "B_old_shape_50")["detail"] == "nothing expires inside 45 days · pushed <when>", row(n, "B_old_shape_50"))
    check("2.2 a renewal 40 days out: quiet on the old file (30-day window), info on the new one (45 days, D689) -- not a warning, not the tile",
          row(o, "B2_old_shape_40")["state"] == "ok" and row(n, "B2_old_shape_40")["state"] == "info"
          and n["B2_old_shape_40"]["worst"] == o["B2_old_shape_40"]["worst"] and n["B2_old_shape_40"]["culprit"] is False,
          (row(n, "B2_old_shape_40"), n["B2_old_shape_40"]["worst"]))
    check("2.3 a renewal 12 days out: info on both, naming it",
          row(o, "C_old_shape_12")["state"] == "info" and row(n, "C_old_shape_12")["state"] == "info"
          and row(n, "C_old_shape_12")["detail"] == "1 expiring inside 45 days · nearest: GoDaddy domain in 12 days (expires %s)" % D["12"],
          row(n, "C_old_shape_12"))
    check("2.4 one 3 days out and one 12: warn on both, nearest first; the tile line names it on the new file",
          row(o, "C2_old_shape_3_and_12")["state"] == "warn" and row(n, "C2_old_shape_3_and_12")["state"] == "warn"
          and row(n, "C2_old_shape_3_and_12")["detail"].startswith("2 expiring inside 45 days · nearest: Tailscale key in 3 days")
          and n["C2_old_shape_3_and_12"]["culprit"] is True and n["C2_old_shape_3_and_12"]["worst"] == o["C2_old_shape_3_and_12"]["worst"],
          row(n, "C2_old_shape_3_and_12"))
    check("2.5 a date 4 days gone (old shape, no expiry given): red on both, 'OVERDUE ... 4 days past expiry'",
          row(o, "D_old_shape_overdue")["state"] == "bad" and row(n, "D_old_shape_overdue")["state"] == "bad"
          and row(n, "D_old_shape_overdue")["detail"].startswith("OVERDUE: dr-manoj.in (4 days past expiry, %s)" % D["-4"])
          and n["D_old_shape_overdue"]["worst"] == o["D_old_shape_overdue"]["worst"], row(n, "D_old_shape_overdue"))
    check("2.6 a stale feed is still warn on both; the new one also names the renewal 3 days out that the old one hid",
          row(o, "E_stale_with_3")["state"] == "warn" and row(n, "E_stale_with_3")["state"] == "warn"
          and "Tailscale" not in row(o, "E_stale_with_3")["detail"]
          and row(n, "E_stale_with_3")["detail"] == "feed stale — last push <when> · nearest: Tailscale key in 3 days (expires %s)" % D["3"],
          (row(o, "E_stale_with_3"), row(n, "E_stale_with_3")))
    check("2.7 a stale feed with nothing near: exactly the old words", row(n, "E2_stale_nothing_near") == row(o, "E2_stale_nothing_near"))

    # ---- 3 · F-775: the alert day is not the deadline
    check("3.1 SHOWN on the old file: an alert day 13 days gone with the expiry 77 days off reads OVERDUE, red, and colours the page",
          row(o, "F_alert_gone_expiry_77")["state"] == "bad" and "OVERDUE" in row(o, "F_alert_gone_expiry_77")["detail"],
          row(o, "F_alert_gone_expiry_77"))
    check("3.2 the new file: the same row is quiet ok -- 77 days is outside 45 -- and the page's colour is what it is with no feed at all",
          row(n, "F_alert_gone_expiry_77")["state"] == "ok" and n["F_alert_gone_expiry_77"]["worst"] == n["A_no_feed"]["worst"]
          and n["F_alert_gone_expiry_77"]["culprit"] is False, (row(n, "F_alert_gone_expiry_77"), n["F_alert_gone_expiry_77"]["worst"]))
    check("3.3 40 days before the expiry (the alert day 50 days gone): info, counted to the expiry",
          row(n, "G_expiry_40")["state"] == "info"
          and row(n, "G_expiry_40")["detail"] == "1 expiring inside 45 days · nearest: Arms licence renewal - Manoj in 40 days (expires %s)" % D["40"],
          row(n, "G_expiry_40"))
    check("3.4 5 days before the expiry: warn (reaches the tile line)", row(n, "H_expiry_5")["state"] == "warn" and n["H_expiry_5"]["culprit"] is True,
          row(n, "H_expiry_5"))
    check("3.5 the expiry day itself: warn, not red", row(n, "I_expiry_today")["state"] == "warn", row(n, "I_expiry_today"))
    check("3.6 the day after the expiry: red, 'OVERDUE ... 1 days past expiry'",
          row(n, "J_expired_yesterday")["state"] == "bad"
          and row(n, "J_expired_yesterday")["detail"].startswith("OVERDUE: Arms licence renewal - Manoj (1 days past expiry, %s)" % D["-1"]),
          row(n, "J_expired_yesterday"))
    check("3.7 one stored row with no name: the old file loses the whole row ('could not be read'); the new one skips that row and names the other",
          "could not be read" in row(o, "K_one_row_without_a_name")["detail"]
          and row(n, "K_one_row_without_a_name")["state"] == "info" and "GoDaddy domain in 12 days" in row(n, "K_one_row_without_a_name")["detail"],
          (row(o, "K_one_row_without_a_name"), row(n, "K_one_row_without_a_name")))

    # ---- 4 · the push door
    P, Po = R["new"]["P"], R["old"]["P"]
    fl = P.get("file") or []
    check("4.1 the push keeps expiryISO; a row without a valid one keeps its alert day as its expiry; a nameless or dateless row is dropped (3 of 5)",
          P["http"] == 200 and P["stored"] == 3
          and [(x["vendor"], x["dateISO"], x["expiryISO"]) for x in fl] == [
              ("Arms licence renewal - Manoj", D["-13"], D["77"]),
              ("Older script row", D["20"], D["20"]),
              ("Bad expiry", D["21"], D["21"])], fl)
    check("4.2 SHOWN on the old file: the same push drops expiryISO", Po["http"] == 200 and all("expiryISO" not in x for x in (Po.get("file") or [])),
          Po.get("file"))
    check("4.3 after the push the row is info (the older-script row is 20 days out), not red", (P["after"]["row"] or {}).get("state") == "info",
          P["after"]["row"])
    check("4.4 a wrong token is still refused (401), and the token still opens no other route", P["wrong_token"] == 401 and P["no_login_health"] in (401, 403),
          (P["wrong_token"], P["no_login_health"]))

    # ---- 5 · the selftest's own renewals block, as each file writes it
    for tag in ("old", "new"):
        sb = R[tag]["selftest_block"]
        check("5.1 the %s file's selftest renewals block runs to its end, every check green (%d)" % (tag, len(sb["ok"])),
              sb["ran"] is True and not sb["fail"] and len(sb["ok"]) >= 11, (sb["ran"], sb["fail"]))
        check("5.2 the %s file's block puts the feed path back" % tag, sb["state_restored"] is True)
    check("5.3 the new block holds the arms-licence case and the expiry day (16 checks, the old block 11)",
          len(R["new"]["selftest_block"]["ok"]) == 16 and len(R["old"]["selftest_block"]["ok"]) == 11,
          (len(R["new"]["selftest_block"]["ok"]), len(R["old"]["selftest_block"]["ok"])))
    check("5.4 the new block keeps the asset database out of it and puts it back afterwards",
          R["new"]["selftest_block"]["assets_env"] and R["new"]["selftest_block"]["assets_env"].endswith("no_such_assets.db"),
          R["new"]["selftest_block"]["assets_env"])
    check("6.1 nothing in the finance app's own folder was written by this walk", md5(os.path.join(fin, "finance_app.py")) == FROM)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())

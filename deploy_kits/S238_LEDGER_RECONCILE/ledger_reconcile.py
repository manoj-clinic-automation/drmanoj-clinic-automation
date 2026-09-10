#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_reconcile.py  v1.0  (S238, D442)  --  the owner's stated record, made true
===============================================================================
Dr Manoj, 10-Sep-2026 (D442): "Whatever transactions I submitted to you are the
only thing which we can understand out here, and I want those to be replicated
exactly in our system."

So this tool takes HIS record as the target and the ledger as the thing that is
corrected to it. It is the instrument the staff-ledger chapter was missing: most
of the August corrections have no route through the application at all.

HOW IT BEHAVES
  * DRY RUN IS THE DEFAULT. It reads the ledger, compares it line by line to the
    stated record, prints every difference, shows what the NEXT monthly close
    would take from each person before and after the correction -- and writes
    nothing. There is no flag or setting that writes by accident.
  * --apply is a separate, deliberate run. It re-reads the ledger, refuses if a
    single byte moved since the plan was made, takes a dated backup, writes every
    row through staff_ledger.py's OWN append_ledger() (so the row shape cannot
    drift), re-checks, and files a correction note beside the ledger.
  * It NEVER edits or deletes a row, never runs a close, never touches a locked
    salary. A wrong advance is corrected the ledger's own way: a contra that
    reverses it, then the right one.
  * The stated record is DATA (a CSV-format .txt beside this file — the repository refuses .csv), not code. Next month's
    list replaces this month's without touching the logic.
  * Lines marked HELD are reported every run and never written -- they wait for
    evidence or a decision (the loan workbook, tranche B's terms).

RUN
  dry run :  /root/wa/venv/bin/python3 /root/staff_ledger_reconcile/ledger_reconcile.py
  apply   :  /root/wa/venv/bin/python3 /root/staff_ledger_reconcile/ledger_reconcile.py --apply
  proof   :  /root/wa/venv/bin/python3 /root/staff_ledger_reconcile/ledger_reconcile.py --selftest

OPTIONS  --record FILE  --module /root/staff_ledger.py  --ledger-dir DIR
         --by manoj (the checker whose authority the rows carry)
"""
import os, sys, csv, json, shutil, hashlib, tempfile, secrets, datetime, importlib.util, io, contextlib

VERSION = "1.0-S238-D442"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RECORD = os.path.join(HERE, "stated_record_2026-08.txt")
DEFAULT_MODULE = "/root/staff_ledger.py"
MAKER = "RECONCILE"
TAG = "S238"


# ----------------------------------------------------------------- helpers --
def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

def rs(n):
    n = int(n)
    return ("-" if n < 0 else "") + "Rs {:,}".format(abs(n))

def next_month(m):
    y, mm = int(m[:4]), int(m[5:7])
    return "%04d-%02d" % (y + (mm // 12), mm % 12 + 1)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_module(path, ledger_dir):
    """Import the LIVE staff_ledger.py (the file the service runs), pointed at
    ledger_dir. The module reads LEDGER_DIR at import, so set it first."""
    os.environ["LEDGER_DIR"] = ledger_dir
    spec = importlib.util.spec_from_file_location("staff_ledger_live", path)
    sm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sm)
    sm.LEDGER_DIR = ledger_dir
    for need in ("load_ledger", "append_ledger", "open_advances", "advance_schedule",
                 "parse_schedule", "advance_children", "advance_recovered",
                 "advance_capitalised", "close_month", "salary_locked", "advance_lane"):
        if not hasattr(sm, need):
            raise SystemExit("!! %s has no %s() -- this is not the staff_ledger.py this tool was "
                             "built against (v3.6-S225-LOANS-D374)" % (path, need))
    return sm


# ------------------------------------------------------------ the record ----
def load_record(path):
    """CSV columns: kind, staff, ref, month, amount, value, held, note.
    kind = recovery | schedule | balance | account | held    ('#' lines ignored)"""
    out = []
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    for i, r in enumerate(csv.DictReader(lines), 2):
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        if r["kind"] not in ("recovery", "schedule", "balance", "account", "held"):
            raise SystemExit("!! record line %d: unknown kind %r" % (i, r["kind"]))
        r["held"] = r.get("held", "").upper() in ("Y", "YES", "HELD")
        r["amount"] = int(r["amount"]) if r.get("amount") else 0
        out.append(r)
    months = {r["month"] for r in out if r["kind"] in ("recovery", "balance") and r["month"]}
    if len(months) != 1:
        raise SystemExit("!! the record must speak for exactly one month; it names %s" % sorted(months))
    return out, months.pop()


# ------------------------------------------------------------ the reading ---
def reversed_ids(rows):
    """Advances genuinely reversed -- the same test open_advances() uses."""
    out = set()
    for r in rows:
        if (r["category"] == "ADVANCE_ISSUE" and r["status"] == "APPROVED" and r.get("contra_of")):
            o = next((x for x in rows if x["id"] == r["contra_of"]), None)
            if o and r["amount"] == -o["amount"]:
                out.add(o["id"])
    return out

def recovered_in(rows, issue_id, month):
    return sum(-r["amount"] for r in rows
               if r["category"] == "ADVANCE_INSTALMENT" and r.get("contra_of") == issue_id
               and r["status"] == "APPROVED"
               and (r.get("closed_month") or r.get("date_from", "")[:7]) == month)

def account_of(issue, b_ids):
    if issue.get("interest"):
        return "A"
    return "B" if issue["id"] in b_ids else "C"

def balances_at(rows, month, b_ids):
    """{(staff, account): balance at the end of `month`} -- advances dated on or
    before the month, less what was recovered in closes up to that month."""
    rev = reversed_ids(rows)
    out = {}
    for r in rows:
        if (r["category"] != "ADVANCE_ISSUE" or r["status"] != "APPROVED" or r["amount"] <= 0
                or r["id"] in rev or r["date_from"][:7] > month):
            continue
        bal = r["amount"]
        for x in rows:
            if x.get("contra_of") != r["id"] or x["status"] != "APPROVED":
                continue
            m = x.get("closed_month") or x.get("date_from", "")[:7]
            if m > month:
                continue
            if x["category"] == "ADVANCE_INSTALMENT":
                bal += x["amount"]
            elif x["category"] == "LOAN_CAPITALISE":
                bal += x["amount"]
        k = (r["staff"], account_of(r, b_ids))
        out[k] = out.get(k, 0) + bal
    return out


# ------------------------------------------------------------- the plan -----
class Plan:
    def __init__(self):
        self.lines = []      # (status, text)   status: OK | FIX | HELD | BLOCKED
        self.rows = []       # rows to append, in order
        self.copies = []     # (src, dst) application files to copy
        self.remap = {}      # old advance id -> re-issued id

    def say(self, status, text):
        self.lines.append((status, text))


def build_plan(sm, rows, record, month, by):
    P = Plan()
    ids = {r["id"]: r for r in rows}
    rev = reversed_ids(rows)
    stamp = now()

    def live_issue(ref, staff):
        r = ids.get(ref)
        if not r:
            return None, "no row %s in the ledger" % ref
        # an advance this tool already re-issued is followed to its successor, so a
        # second run reads the corrected row instead of reporting the reversed one
        succ = [x for x in rows if x.get("reissued_from") == ref and x["status"] == "APPROVED"
                and x["category"] == "ADVANCE_ISSUE" and x["id"] not in rev]
        if r["id"] in rev and len(succ) == 1:
            r = succ[0]
        if r["category"] != "ADVANCE_ISSUE" or r["status"] != "APPROVED" or r["amount"] <= 0:
            return None, "row %s is not an approved advance" % ref
        if r["id"] in rev:
            return None, "advance %s has been reversed" % ref
        if r["staff"] != staff:
            return None, "advance %s belongs to %s, not %s" % (ref, r["staff"], staff)
        return r, ""

    # ---- 1. schedules first: a wrong one is corrected by contra + re-issue ---
    for it in [x for x in record if x["kind"] == "schedule"]:
        issue, why = live_issue(it["ref"], it["staff"])
        label = "%s · advance of %s" % (it["staff"], rs(issue["amount"]) if issue else it["ref"])
        if not issue:
            P.say("BLOCKED", "%s: %s" % (label, why)); continue
        want = sm.parse_schedule(it["value"], issue["amount"])
        have = sm.advance_schedule(issue)
        steps = ", ".join("%s %s" % (e["month"], rs(e["amount"])) for e in want)
        if have == want:
            P.say("OK", "%s %s carries its agreed schedule (%s)" % (label, issue["date_from"], steps)); continue
        if it["held"]:
            P.say("HELD", "%s: schedule should be %s — %s" % (label, steps, it["note"])); continue
        kids = sm.advance_children(issue["id"], rows)
        if kids:
            P.say("BLOCKED", "%s: schedule should be %s but the advance already has %d collection "
                  "row(s), so it cannot be reversed — needs the loan-restatement row (build item 5)"
                  % (label, steps, len(kids))); continue
        new_id = secrets.token_hex(6)
        contra = {
            "id": secrets.token_hex(6), "ts_entry": stamp, "maker": MAKER,
            "staff": issue["staff"], "category": "ADVANCE_ISSUE",
            "date_from": issue["date_from"], "date_to": issue.get("date_to", ""), "days": issue.get("days", 0),
            "amount": -issue["amount"], "instalment": None,
            "narration": ("CONTRA of %s: re-issued as %s with the agreed schedule (%s) — "
                          "reconciler %s, owner's stated record (D442)" % (issue["id"], new_id, steps, TAG)),
            "self_flag": False, "direct": True, "status": "APPROVED", "checker": by, "ts_decision": stamp,
            "contra_of": issue["id"], "closed_month": "", "interest": False,
            "against_month": issue.get("against_month", ""), "special": False, "schedule": [],
            "reconcile": TAG}
        new = dict(issue)
        new.update({"id": new_id, "ts_entry": stamp, "maker": MAKER, "checker": by,
                    "ts_decision": stamp, "direct": True, "status": "APPROVED",
                    "closed_month": "", "schedule": want, "reconcile": TAG,
                    "reissued_from": issue["id"],
                    "narration": ((issue.get("narration") or "").strip() +
                                  " [re-issued from %s with schedule %s — reconciler %s, D442]"
                                  % (issue["id"], steps, TAG)).strip()})
        P.rows += [contra, new]
        P.remap[issue["id"]] = new_id
        src = os.path.join(sm.LEDGER_DIR, "applications", "%s.pdf" % issue["id"])
        if os.path.exists(src) and os.path.getsize(src) > 0:
            P.copies.append((src, os.path.join(sm.LEDGER_DIR, "applications", "%s.pdf" % new_id)))
        P.say("FIX", "%s %s has %s; re-issue it with the agreed schedule %s (a contra and the "
              "corrected advance, 2 rows)" % (label, issue["date_from"],
                                             "no schedule" if not have else "a different schedule", steps))
        ids[new_id] = new

    # ---- 2. recoveries the closes should have made -------------------------
    for it in [x for x in record if x["kind"] == "recovery"]:
        issue, why = live_issue(it["ref"], it["staff"])
        if not issue:
            P.say("BLOCKED", "%s: %s" % (it["staff"], why)); continue
        target_id = P.remap.get(issue["id"], issue["id"])
        target = ids[target_id]
        have = recovered_in(rows, issue["id"], it["month"]) + \
               (recovered_in(rows, target_id, it["month"]) if target_id != issue["id"] else 0)
        label = "%s · %s advance of %s" % (it["staff"], issue["date_from"], rs(issue["amount"]))
        if have >= it["amount"]:
            P.say("OK", "%s: %s recovered against %s" % (label, rs(have), it["month"])); continue
        gap = it["amount"] - have
        if it["held"]:
            P.say("HELD", "%s: %s should be recovered against %s — %s" % (label, rs(gap), it["month"], it["note"])); continue
        bal = target["amount"] - sum(-x["amount"] for x in rows + P.rows
                                     if x["category"] == "ADVANCE_INSTALMENT" and x.get("contra_of") == target_id
                                     and x["status"] == "APPROVED")
        if gap > bal:
            P.say("BLOCKED", "%s: record says %s against %s but only %s is left on it" % (label, rs(gap), it["month"], rs(bal))); continue
        P.rows.append({
            "id": secrets.token_hex(6), "ts_entry": stamp, "maker": MAKER,
            "staff": issue["staff"], "category": "ADVANCE_INSTALMENT",
            "date_from": it["month"], "date_to": it["month"], "days": 0,
            "amount": -gap, "instalment": None,
            "narration": ("%s recovery recorded by the reconciler %s (owner's stated record, D442): "
                          "%s. Balance after: %d" % (it["month"], TAG, it["note"] or "not collected by the close", bal - gap)),
            "self_flag": False, "direct": True, "status": "APPROVED", "checker": by, "ts_decision": stamp,
            "contra_of": target_id, "closed_month": it["month"], "interest": False, "reconcile": TAG})
        P.say("FIX", "%s: record %s recovered against %s salary (the ledger has %s)"
              % (label, rs(gap), it["month"], rs(have)))

    # ---- 3. held lines: reported every run, never written ------------------
    for it in [x for x in record if x["kind"] == "held"]:
        P.say("HELD", "%s: %s" % (it["staff"], it["note"]))
    return P


def check_balances(rows_after, record, month, b_ids):
    got = balances_at(rows_after, month, b_ids)
    out = []
    for it in [x for x in record if x["kind"] == "balance"]:
        k = (it["staff"], it["ref"])
        have = got.get(k, 0)
        st = "OK" if have == it["amount"] else ("HELD" if it["held"] else "DIFF")
        out.append((st, it["staff"], it["ref"], it["amount"], have, it["note"]))
    return out


# ------------------------------------------------- next-close preview -------
def preview_close(sm, ledger_dir, rows, extra, month):
    """Run the module's OWN close_month() on a throw-away copy and report what it
    takes. The real ledger is never opened for writing."""
    tmp = tempfile.mkdtemp(prefix="reconcile_preview_")
    os.chmod(tmp, 0o700)
    real = sm.LEDGER_DIR
    try:
        with open(os.path.join(tmp, "ledger.jsonl"), "w", encoding="utf-8") as f:
            for r in rows + extra:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        for name in (getattr(sm, "SETTINGS_FILE", "ledger_settings.json"),):
            s = os.path.join(ledger_dir, name)
            if os.path.exists(s):
                shutil.copy2(s, os.path.join(tmp, name))
        sm.LEDGER_DIR = tmp
        n0 = len(rows) + len(extra)
        with contextlib.redirect_stdout(io.StringIO()):
            sm.close_month({"_preview": {"role": "checker"}}, "_preview", month)
        new = sm.load_ledger()[n0:]
    finally:
        sm.LEDGER_DIR = real
        shutil.rmtree(tmp, ignore_errors=True)
    per = {}
    for r in new:
        if r["category"] in ("ADVANCE_INSTALMENT", "LOAN_INTEREST"):
            per.setdefault(r["staff"], {"take": 0, "lines": [], "held": 0})
            per[r["staff"]]["take"] += -r["amount"]
            per[r["staff"]]["lines"].append((r["category"], r.get("contra_of", ""), -r["amount"]))
        elif r["category"] == "CAPACITY_HOLD":
            per.setdefault(r["staff"], {"take": 0, "lines": [], "held": 0})
            per[r["staff"]]["held"] += 1
    return per


# ------------------------------------------------------------- report -------
def describe_issue(rows, iid):
    r = next((x for x in rows if x["id"] == iid), None)
    if not r:
        return iid
    kind = "loan interest" if False else ("loan" if r.get("interest") else "advance")
    return "%s of %s, %s" % (kind, rs(r["amount"]), r["date_from"])

def report(sm, ledger_dir, rows, record, month, by, plan, out=print):
    b_ids = {x["ref"] for x in record if x["kind"] == "account" and x["value"].upper() == "B"}
    nm = next_month(month)
    out("")
    out("=" * 78)
    out("  1 · THE OWNER'S RECORD FOR %s AGAINST THE LEDGER" % month)
    out("=" * 78)
    tag = {"OK": "  ok   ", "FIX": "  FIX  ", "HELD": "  HELD ", "BLOCKED": "  !!   "}
    for st, t in plan.lines:
        out(tag[st] + t)
    out("")
    out("=" * 78)
    out("  2 · BALANCES AT THE END OF %s — the record, the ledger now, after the fix" % month)
    out("=" * 78)
    before = {(s, a): h for (_, s, a, _, h, _) in check_balances(rows, record, month, b_ids)}
    after = check_balances(rows + plan.rows, record, month, b_ids)
    names = {"A": "A · interest loan", "B": "B · interest-free", "C": "C · short-term"}
    out("  %-9s %-20s %12s %12s %12s" % ("staff", "account", "record", "ledger now", "after fix"))
    for st, s, a, want, have, note in after:
        mark = {"OK": "", "HELD": "   HELD — " + note, "DIFF": "   !! DIFFERS"}[st]
        out("  %-9s %-20s %12s %12s %12s%s" % (s, names.get(a, a), rs(want), rs(before[(s, a)]), rs(have), mark))
    out("")
    out("=" * 78)
    out("  3 · WHAT THE %s CLOSE WOULD TAKE — today, and after the fix" % nm)
    out("      (the ledger's own close, run on a throw-away copy; the real file is not touched)")
    out("=" * 78)
    pb = preview_close(sm, ledger_dir, rows, [], nm)
    pa = preview_close(sm, ledger_dir, rows, plan.rows, nm)
    allrows = rows + plan.rows
    for s in sorted(set(pb) | set(pa)):
        b, a = pb.get(s, {"take": 0, "lines": [], "held": 0}), pa.get(s, {"take": 0, "lines": [], "held": 0})
        norm = lambda p: sorted((c, describe_issue(allrows, i), m) for c, i, m in p["lines"])
        same = norm(b) == norm(a)
        out("  %-9s today %10s   after the fix %10s%s" % (s, rs(b["take"]), rs(a["take"]),
                                                          "" if same else "   <- changes"))
        for when, p in ((("", a),) if same else (("today", b), ("after", a))):
            for cat, iid, amt in p["lines"]:
                what = "interest" if cat == "LOAN_INTEREST" else describe_issue(allrows, iid)
                out("  %9s %5s %-44s %10s" % ("", when, what, rs(amt)))
        if a["held"]:
            out("  %9s   (part held back: the salary could not bear it all — collects later)" % "")
    out("")
    out("=" * 78)
    out("  4 · WHAT THE FIX TAKES OFF THE %s SALARY (not yet locked)" % month)
    out("=" * 78)
    per = {}
    for r in plan.rows:
        if r["category"] == "ADVANCE_INSTALMENT" and r.get("closed_month") == month:
            per[r["staff"]] = per.get(r["staff"], 0) - r["amount"]
    for s in sorted(per):
        out("  %-9s %10s more recovered against %s" % (s, rs(per[s]), month))
    if not per:
        out("  nothing")
    out("")
    fixes = sum(1 for st, _ in plan.lines if st == "FIX")
    held = sum(1 for st, _ in plan.lines if st == "HELD") + sum(1 for x in after if x[0] == "HELD")
    blocked = [t for st, t in plan.lines if st == "BLOCKED"] + \
              ["%s %s balance differs and no line of the record explains it" % (x[1], x[2]) for x in after if x[0] == "DIFF"]
    return fixes, held, blocked


# ------------------------------------------------------------- apply --------
def apply_plan(sm, ledger_dir, plan, md5_at_plan, record_path, month, by):
    led = os.path.join(ledger_dir, "ledger.jsonl")
    if md5_file(led) != md5_at_plan:
        raise SystemExit("!! the ledger changed while the plan was being made — nothing written. Run again.")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = led + ".bak_reconcile_" + stamp
    shutil.copy2(led, bak)
    os.chmod(bak, 0o600)
    if md5_file(bak) != md5_at_plan:
        raise SystemExit("!! the backup does not match the ledger — nothing written")
    n_before = len(sm.load_ledger())
    for src, dst in plan.copies:
        shutil.copy2(src, dst); os.chmod(dst, 0o600)
    for r in plan.rows:
        sm.append_ledger(r)          # the module's own writer: the row shape cannot drift
    rows_now = sm.load_ledger()
    if len(rows_now) != n_before + len(plan.rows):
        raise SystemExit("!! row count after writing is %d, expected %d — restore from %s"
                         % (len(rows_now), n_before + len(plan.rows), bak))
    # the file is the old file plus exactly these lines -- proven, not assumed
    with open(bak, "rb") as f:
        old = f.read()
    with open(led, "rb") as f:
        cur = f.read()
    if not cur.startswith(old):
        raise SystemExit("!! the ledger is not the old ledger plus new lines — restore from %s" % bak)
    notes = os.path.join(ledger_dir, "corrections")
    os.makedirs(notes, exist_ok=True)
    os.chmod(notes, 0o700)
    note = os.path.join(notes, "RECONCILE_%s_%s.txt" % (month, stamp))
    with open(note, "w", encoding="utf-8") as f:
        f.write("STAFF LEDGER CORRECTION — reconciler %s (%s)\n" % (TAG, VERSION))
        f.write("written      : %s (server time)\n" % now())
        f.write("authority    : the owner's stated record (D442), confirmed against his physical records 10-Sep-2026\n")
        f.write("checker      : %s\n" % by)
        f.write("stated list  : %s  md5 %s\n" % (record_path, md5_file(record_path)))
        f.write("ledger before: md5 %s  (%d rows)  backup %s\n" % (md5_at_plan, n_before, bak))
        f.write("ledger after : md5 %s  (%d rows)\n\n" % (md5_file(led), len(rows_now)))
        f.write("ROWS WRITTEN (%d):\n" % len(plan.rows))
        for r in plan.rows:
            f.write("  %s  %-9s %-18s %10s  -> %s  %s\n" % (r["id"], r["staff"], r["category"], r["amount"],
                                                       r.get("contra_of") or "-", r["narration"][:110]))
        for src, dst in plan.copies:
            f.write("  application copied: %s -> %s\n" % (os.path.basename(src), os.path.basename(dst)))
    os.chmod(note, 0o600)
    return bak, note, n_before, len(rows_now)


# ------------------------------------------------------------- main ---------
def main(argv):
    a = {"record": DEFAULT_RECORD, "module": DEFAULT_MODULE,
         "ledger": os.environ.get("LEDGER_DIR", "/root/staff_ledger"), "by": "manoj", "apply": False,
         "selftest": False}
    i = 0
    while i < len(argv):
        k = argv[i]
        if k == "--apply": a["apply"] = True
        elif k == "--selftest": a["selftest"] = True
        elif k in ("-h", "--help"): print(__doc__); return 0
        elif k in ("--record", "--module", "--ledger-dir", "--by"):
            i += 1; a[{"--ledger-dir": "ledger"}.get(k, k[2:])] = argv[i]
        else:
            print("unknown option %s — run with --help" % k); return 2
        i += 1
    if a["selftest"]:
        return selftest(a["ledger"], a["module"], a["record"])
    led = os.path.join(a["ledger"], "ledger.jsonl")
    if not os.path.exists(led):
        print("!! no ledger at %s" % led); return 2
    sm = load_module(a["module"], a["ledger"])
    record, month = load_record(a["record"])
    md5_0 = md5_file(led)
    rows = sm.load_ledger()
    print("STAFF LEDGER RECONCILER %s — %s" % (VERSION, "APPLY" if a["apply"] else "DRY RUN (writes nothing)"))
    print("  ledger : %s  %d rows  md5 %s" % (led, len(rows), md5_0))
    print("  code   : %s  md5 %s  (%s)" % (a["module"], md5_file(a["module"]), getattr(sm, "APP_VERSION", "?")))
    print("  record : %s  md5 %s  — month %s" % (a["record"], md5_file(a["record"]), month))

    # guards that hold for BOTH runs
    stop = []
    if sm.salary_locked(month, rows):
        stop.append("%s salary is already APPROVED AND LOCKED — a recovery written now would never reach it" % month)
    later = sorted({r["closed_month"] for r in rows if r.get("closed_month") and r["closed_month"] > month})
    if later:
        stop.append("the %s close has already run — it collected on the uncorrected ledger; this plan must be re-made" % ", ".join(later))

    plan = build_plan(sm, rows, record, month, a["by"])
    fixes, held, blocked = report(sm, a["ledger"], rows, record, month, a["by"], plan)

    print("=" * 78)
    print("  RESULT: %d correction(s) ready, %d row(s) to write · %d line(s) HELD · %d blocked"
          % (fixes, len(plan.rows), held, len(blocked)))
    for s in stop:
        print("  !! REFUSED: " + s)
    for b in blocked:
        print("  !! BLOCKED: " + b)
    print("=" * 78)
    if not a["apply"]:
        print("  DRY RUN — nothing was written.")
        if plan.rows and not stop and not blocked:
            print("  To write these %d rows (backup first, then a re-check):" % len(plan.rows))
            print("")
            print("  /root/wa/venv/bin/python3 %s --apply" % os.path.abspath(__file__))
        return 0
    if stop or blocked:
        print("  NOTHING WRITTEN — clear the lines above first."); return 1
    if not plan.rows:
        print("  NOTHING TO WRITE — the ledger already matches the record."); return 0
    bak, note, n0, n1 = apply_plan(sm, a["ledger"], plan, md5_0, a["record"], month, a["by"])
    print("  WRITTEN: %d rows (%d -> %d)" % (len(plan.rows), n0, n1))
    print("  backup : %s" % bak)
    print("  note   : %s" % note)
    # the re-check: a second plan on the corrected ledger must find nothing to do
    rows2 = sm.load_ledger()
    plan2 = build_plan(sm, rows2, record, month, a["by"])
    left = [t for st, t in plan2.lines if st in ("FIX", "BLOCKED")]
    bal2 = [x for x in check_balances(rows2, record, month,
            {x["ref"] for x in record if x["kind"] == "account" and x["value"].upper() == "B"}) if x[0] == "DIFF"]
    if left or bal2 or plan2.rows:
        print("  !! RE-CHECK FOUND %d open line(s) — read above; the backup is %s" % (len(left) + len(bal2), bak))
        for t in left: print("     " + t)
        return 1
    print("  RE-CHECK: the ledger now matches the record on every line that is not HELD.")
    return 0


# ============================================================ selftest ======
def selftest(ledger_dir, module, record_path):
    """The whole cycle -- plan, apply, re-check, refuse -- run on a throw-away
    COPY of the real ledger, against the real staff_ledger.py. Live shape by
    construction, and the real file is proven untouched (md5 before and after).
    No fixture of staff data is shipped: the repository is public."""
    fails, n = [], [0]
    def ck(cond, what):
        n[0] += 1
        if not cond: fails.append(what)
    real = os.path.join(ledger_dir, "ledger.jsonl")
    if not os.path.exists(real):
        print("selftest: no ledger at %s — 0 checks, 1 failures" % real); return 1
    md5_real = md5_file(real)
    tmp = tempfile.mkdtemp(prefix="reconcile_selftest_")
    os.chmod(tmp, 0o700)
    try:
        shutil.copy2(real, os.path.join(tmp, "ledger.jsonl"))
        sname = "ledger_settings.json"
        if os.path.exists(os.path.join(ledger_dir, sname)):
            shutil.copy2(os.path.join(ledger_dir, sname), os.path.join(tmp, sname))
        sm = load_module(module, tmp)
        record, month = load_record(record_path)
        b_ids = {x["ref"] for x in record if x["kind"] == "account" and x["value"].upper() == "B"}
        rows = sm.load_ledger()
        ids = {r["id"] for r in rows}
        ck(len(ids) == len(rows), "every ledger id is unique")
        plan = build_plan(sm, rows, record, month, "manoj")
        ck(not [1 for st, _ in plan.lines if st == "BLOCKED"],
           "no line is blocked: %s" % [t for st, t in plan.lines if st == "BLOCKED"])
        ck(all(r["id"] not in ids for r in plan.rows), "no planned row reuses an existing id")
        ck(all(r["maker"] == MAKER and r["reconcile"] == TAG and r["status"] == "APPROVED" for r in plan.rows),
           "every planned row says who wrote it and is approved")
        ck(all(r["closed_month"] == month for r in plan.rows if r["category"] == "ADVANCE_INSTALMENT"),
           "every recovery is stamped to the %s close" % month)
        byid = {r["id"]: r for r in rows}
        for r in plan.rows:
            if r["category"] == "ADVANCE_ISSUE" and r["amount"] < 0:
                o = byid.get(r["contra_of"])
                ck(o is not None and o["amount"] == -r["amount"] and not sm.advance_children(o["id"], rows),
                   "the contra of %s reverses exactly an advance with no collections" % r["contra_of"])
            if r.get("reissued_from"):
                o = byid[r["reissued_from"]]
                ck(all(r[k] == o[k] for k in ("staff", "amount", "date_from", "against_month")),
                   "the re-issue of %s keeps staff, amount, date and month" % o["id"])
                ck(sm.advance_lane({"issue": r, "interest": False, "instalment": r["instalment"]}) == "schedule",
                   "the re-issue of %s is recovered by its schedule" % o["id"])
        with contextlib.redirect_stdout(io.StringIO()):
            pa = preview_close(sm, tmp, rows, plan.rows, next_month(month))
        ck(isinstance(pa, dict), "the next close previews cleanly on a copy")
        led = os.path.join(tmp, "ledger.jsonl")
        md5_0 = md5_file(led)
        if plan.rows:
            with contextlib.redirect_stdout(io.StringIO()):
                bak, note, n0, n1 = apply_plan(sm, tmp, plan, md5_0, record_path, month, "manoj")
            ck(n1 == n0 + len(plan.rows), "apply wrote exactly the planned rows")
            ck(md5_file(bak) == md5_0, "the backup is the untouched ledger")
            with open(bak, "rb") as f: old = f.read()
            with open(led, "rb") as f: cur = f.read()
            ck(cur.startswith(old), "the ledger is the old file plus new lines — nothing above it was edited")
            ck(os.path.exists(note), "a correction note is filed")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    apply_plan(sm, tmp, plan, md5_0, record_path, month, "manoj")
                ck(False, "apply must refuse a ledger that moved since the plan")
            except SystemExit as e:
                ck("changed" in str(e), "apply refuses a ledger that moved since the plan")
        rows2 = sm.load_ledger()
        plan2 = build_plan(sm, rows2, record, month, "manoj")
        ck(not plan2.rows and not [1 for st, _ in plan2.lines if st in ("FIX", "BLOCKED")],
           "a second run finds nothing to do: %s" % [t for st, t in plan2.lines if st in ("FIX", "BLOCKED")])
        diffs = [x for x in check_balances(rows2, record, month, b_ids) if x[0] == "DIFF"]
        ck(not diffs, "after the fix every balance matches the record, except HELD: %s" % diffs)
    except Exception as e:
        import traceback; traceback.print_exc()
        fails.append("exception: %r" % e)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ck(md5_file(real) == md5_real, "the REAL ledger was not touched by the selftest")
    for f in fails:
        print("  FAIL: " + f)
    print("selftest %s: %d checks, %d failures" % (VERSION, n[0], len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

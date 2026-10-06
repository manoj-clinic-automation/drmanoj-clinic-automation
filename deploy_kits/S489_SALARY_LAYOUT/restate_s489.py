#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
restate_s489.py -- kit S489_SALARY_LAYOUT (session 297, 06-Oct-2026) -- ONE ROW in the staff ledger.

THE OWNER'S RULING (06-Oct-2026, D682), asked "Does the Rs 1,000 for April stay on the loan, or
should it come off?" -- "Come off."

  April 2026 was a skipped month on Darpan's loan with interest, and the loan workbook added the
  flat Rs 1,000 interest to the loan for it. May and June were paid, and the ledger took the loan
  over on 07-Aug-2026 -- with that Rs 1,000 inside the migrated amount. This has been "the loan's
  Rs 1,000", HELD since S238 (stated_record_2026-08.txt: held = Y, "waits for the loan
  workbook"). The workbook has now been read; the owner has ruled.

WHAT THIS WRITES: exactly ONE row, through staff_ledger.py's OWN append_ledger() (so the row's
shape cannot drift) --

    category   LOAN_CAPITALISE          the ledger's own "interest added on a skip" row, the only
    amount     -1000                    row type its balance arithmetic already carries everywhere
    contra_of  the loan's id            (amount + capitalised - recovered); a NEGATIVE one takes the
    date_from  2026-04                  workbook's addition off again. staff_ledger.py is not edited.
    closed_month 2026-07                the same stamp the April skip row itself carries (the
                                        migration's month) -- so no new "closed month" appears.

  It is outside salary money (SALARY_EXCLUDED): no salary, no instalment, no interest charge and
  no locked month changes. The loan's balance falls by exactly Rs 1,000 from that row on.

HOW: dry run by default -- it reads the ledger, checks every precondition, says what it would
write, and writes NOTHING. --apply refuses if a byte moved since the plan, takes a dated backup
beside the ledger, appends the row, re-reads and proves -- on the rows themselves -- that the
loan's balance moved by exactly the ruled amount and no other advance moved, and files a
correction note in <ledger>/corrections/. IT NEVER WRITES THE BACKUP OVER THE LEDGER: the ledger
app may add a row of its own at any moment, and that row is not this tool's to lose. If its
re-check fails it takes back ONLY its own row, and only while that row is still the last line.
Run twice, the second run says ALREADY APPLIED and writes nothing.

    dry run :  /root/wa/venv/bin/python3 restate_s489.py
    apply   :  /root/wa/venv/bin/python3 restate_s489.py --apply
    options :  --ledger DIR (default $LEDGER_DIR or /root/staff_ledger) --module PATH --by NAME

Console prints NO balance and NO salary figure (F-31) -- only the ruled Rs 1,000 and row counts.
"""
import os, sys, json, shutil, hashlib, secrets, datetime, importlib.util

TAG = "S489"
STAFF = "Darpan"
LOAN_ID = "b1eb7a8e419e"                 # the interest-bearing tranche migrated on 07-Aug-2026
MONTH = "2026-04"                        # the skipped month the workbook's Rs 1,000 belongs to
STAMP_MONTH = "2026-07"                  # the close stamp the April skip row carries
AMOUNT = -1000                           # the ledger's own flat interest (INTEREST_RS), taken off again
MAKER = "RESTATE"
NARRATION = ("April 2026 was a skipped month and the loan workbook added the flat Rs 1,000 interest to this "
             "loan for it; that Rs 1,000 came into the ledger inside the migrated amount. THE OWNER'S RULING "
             "of 06-Oct-2026 (D682): it comes off. This row takes it off -- outside salary money; no "
             "instalment, interest charge or locked month changes. "
             "Written by kit S489_SALARY_LAYOUT (restate_s489.py).")


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_module(path, ledger_dir):
    """The box's own staff_ledger.py, pointed at ledger_dir (it reads LEDGER_DIR at import)."""
    os.environ["LEDGER_DIR"] = ledger_dir
    spec = importlib.util.spec_from_file_location("staff_ledger_s489", path)
    sm = importlib.util.module_from_spec(spec)
    sys.modules["staff_ledger_s489"] = sm
    spec.loader.exec_module(sm)
    sm.LEDGER_DIR = ledger_dir
    for need in ("load_ledger", "append_ledger", "open_advances", "advance_capitalised", "advance_recovered"):
        if not hasattr(sm, need):
            raise SystemExit("!! %s has no %s() -- not the ledger module this kit was built on" % (path, need))
    return sm


def balance(sm, rows, issue_id=LOAN_ID):
    issue = next(r for r in rows if r["id"] == issue_id)
    return issue["amount"] + sm.advance_capitalised(issue_id, rows) - sm.advance_recovered(issue_id, rows)


def all_balances(sm, rows):
    """Every approved advance's balance, by the ledger's own arithmetic on THESE rows (not on the file)."""
    return {r["id"]: balance(sm, rows, r["id"]) for r in rows
            if r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED" and (r.get("amount") or 0) > 0}


def plan(sm, rows, by):
    """(state, row_or_None, why). state: 'plan' | 'done' | 'refuse'."""
    issue = next((r for r in rows if r.get("id") == LOAN_ID), None)
    if not issue:
        return "refuse", None, "the loan %s is not in this ledger" % LOAN_ID
    if (issue.get("category") != "ADVANCE_ISSUE" or issue.get("status") != "APPROVED"
            or issue.get("staff") != STAFF or not issue.get("interest")):
        return "refuse", None, "row %s is not %s's approved loan with interest" % (LOAN_ID, STAFF)
    if not str(issue.get("narration", "")).startswith("opening balance migrated"):
        return "refuse", None, "the loan is not the migrated opening balance this ruling was made on"
    if any(r.get("contra_of") == LOAN_ID and r.get("category") == "ADVANCE_ISSUE"
           and r.get("status") == "APPROVED" and r.get("amount") == -issue["amount"] for r in rows):
        return "refuse", None, "the loan has been reversed"
    if not any(r.get("category") == "LOAN_SKIP" and r.get("contra_of") == LOAN_ID
               and str(r.get("date_from", ""))[:7] == MONTH and r.get("status") == "APPROVED" for r in rows):
        return "refuse", None, "the ledger has no skip recorded for %s on this loan" % MONTH
    mine = [r for r in rows if r.get("restate") == TAG]
    if mine:
        ok = (len(mine) == 1 and mine[0].get("contra_of") == LOAN_ID and mine[0].get("amount") == AMOUNT
              and mine[0].get("category") == "LOAN_CAPITALISE" and mine[0].get("status") == "APPROVED")
        return ("done", None, "the row is already in the ledger (id %s)" % mine[0].get("id")) if ok else \
               ("refuse", None, "a row tagged %s exists but is not the row this kit writes" % TAG)
    caps = [r for r in rows if r.get("category") == "LOAN_CAPITALISE" and r.get("contra_of") == LOAN_ID
            and r.get("status") == "APPROVED" and str(r.get("date_from", ""))[:7] == MONTH]
    if caps:
        return "refuse", None, "the ledger already carries a capitalisation row for %s on this loan" % MONTH
    if not any(r.get("closed_month") == STAMP_MONTH for r in rows):
        return "refuse", None, "%s is not a closed month in this ledger -- the row's stamp would open one" % STAMP_MONTH
    if balance(sm, rows) + AMOUNT <= 0:
        return "refuse", None, "the loan's balance is not above the ruled amount"
    stamp = now()
    row = {"id": secrets.token_hex(6), "ts_entry": stamp, "maker": MAKER, "staff": STAFF,
           "category": "LOAN_CAPITALISE", "date_from": MONTH, "date_to": MONTH, "days": 0,
           "amount": AMOUNT, "instalment": None, "narration": NARRATION,
           "self_flag": False, "direct": True, "status": "APPROVED", "checker": by, "ts_decision": stamp,
           "contra_of": LOAN_ID, "closed_month": STAMP_MONTH, "interest": False, "restate": TAG}
    while any(r.get("id") == row["id"] for r in rows):
        row["id"] = secrets.token_hex(6)
    return "plan", row, ""


def take_back(led, row_id):
    """Remove this tool's OWN row, and only if it is still the LAST line of the ledger. True if removed.
    Nothing else is ever rewritten: a row the ledger app added meanwhile is not ours to touch."""
    with open(led, "rb+") as f:
        data = f.read()
        body = data.rstrip(b"\n")
        cut = body.rfind(b"\n") + 1                     # 0 when the file is one line
        try:
            last = json.loads(body[cut:].decode("utf-8"))
        except Exception:
            return False
        if not isinstance(last, dict) or last.get("id") != row_id or last.get("restate") != TAG:
            return False
        f.seek(0, 2)
        if f.tell() != len(data):                       # the file grew while we looked
            return False
        f.truncate(cut)
    return True


def apply_row(sm, ledger_dir, row, md5_at_plan, by):
    led = os.path.join(ledger_dir, "ledger.jsonl")
    if md5_file(led) != md5_at_plan:
        raise SystemExit("!! the ledger changed between the plan and the write -- nothing written; run again")
    rows0 = sm.load_ledger()
    bal0 = balance(sm, rows0)
    all0 = all_balances(sm, rows0)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = os.path.join(ledger_dir, "ledger.jsonl.bak_restate_%s_%s" % (TAG, stamp))
    shutil.copy2(led, bak)
    if md5_file(bak) != md5_at_plan:
        raise SystemExit("!! the backup does not match the ledger -- nothing written")
    sm.append_ledger(row)                       # the module's own writer: the row shape cannot drift
    rows1 = sm.load_ledger()
    mine = [r for r in rows1 if r.get("restate") == TAG]
    others = [r for r in rows1[len(rows0):] if r.get("restate") != TAG]     # rows the ledger app added meanwhile
    problems = []
    if rows1[:len(rows0)] != rows0:
        problems.append("an earlier row changed")
    if len(mine) != 1 or mine[0] != row:
        problems.append("the row in the ledger is not the row that was planned")
    # the proof is worked on the rows themselves -- the ledger as it was plus this one row -- so a row
    # the ledger app adds at the same moment can neither hide a fault nor raise a false one
    proof = rows0 + [row]
    all1 = all_balances(sm, proof)
    if all1.get(LOAN_ID) != bal0 + AMOUNT:
        problems.append("the loan's balance did not move by exactly the ruled amount")
    moved = [k for k in set(all0) | set(all1) if k != LOAN_ID and all0.get(k) != all1.get(k)]
    if moved:
        problems.append("another advance's balance moved: %s" % ", ".join(sorted(moved)))
    if hasattr(sm, "closed_months") and sm.closed_months(proof) != sm.closed_months(rows0):
        problems.append("a new closed month appeared")
    if problems:
        gone = take_back(led, row["id"])
        raise SystemExit("!! RE-CHECK FAILED (%s) -- %s. Backup of the ledger as it was: %s"
                         % ("; ".join(problems),
                            "this tool's own row was taken out again; no other row was touched" if gone else
                            "this tool's row is STILL IN the ledger (another row was written after it) -- "
                            "read the ledger before anything else", bak))
    note = os.path.join(ledger_dir, "corrections", "RESTATE_%s_%s.txt" % (TAG, stamp))
    try:                                        # the ROW is the ruling; the note is a courtesy and must not
        os.makedirs(os.path.dirname(note), exist_ok=True)      # turn a written row into a red run
        with open(note, "w", encoding="utf-8") as f:
            f.write("STAFF LEDGER CORRECTION -- kit S489_SALARY_LAYOUT (restate_s489.py)\n")
            f.write("when   : %s (server clock)\nby     : %s\n" % (now(), by))
            f.write("ruling : the owner, 06-Oct-2026 (D682) -- April 2026's Rs 1,000 comes off Darpan's loan with interest\n")
            f.write("ledger before: md5 %s  (%d rows)  backup %s\n" % (md5_at_plan, len(rows0), bak))
            f.write("ledger after : md5 %s  (%d rows%s)\n"
                    % (md5_file(led), len(rows1),
                       ("; %d of them written by the ledger app during the write" % len(others)) if others else ""))
            f.write("row    : %s\n" % json.dumps(row, ensure_ascii=False))
            f.write("loan %s balance before %s -> after %s\n" % (LOAN_ID, bal0, bal0 + AMOUNT))
        os.chmod(note, 0o600)
    except OSError as e:
        note = "(the correction note could not be written: %s -- the row IS in the ledger; the backup is above)" % type(e).__name__
    return bak, note


def main(argv):
    a = {"ledger": os.environ.get("LEDGER_DIR", "/root/staff_ledger"), "module": "/root/staff_ledger.py",
         "by": "manoj", "apply": False}
    it = iter(argv[1:])
    for k in it:
        if k == "--apply":
            a["apply"] = True
        elif k in ("--ledger", "--module", "--by"):
            a[k[2:]] = next(it, "")
        else:
            print(__doc__)
            return 2
    led = os.path.join(a["ledger"], "ledger.jsonl")
    if not os.path.isfile(led):
        print("!! no ledger at %s" % led)
        return 1
    md5_at_plan = md5_file(led)
    sm = load_module(a["module"], a["ledger"])
    rows = sm.load_ledger()
    state, row, why = plan(sm, rows, a["by"])
    print("RESTATE %s -- %s -- ledger %s (%d rows)" % (TAG, "APPLY" if a["apply"] else "DRY RUN, nothing is written",
                                                     a["ledger"], len(rows)))
    if state == "refuse":
        print("!! REFUSED: %s -- nothing written" % why)
        return 1
    if state == "done":
        print("-- ALREADY APPLIED: %s -- nothing written" % why)
        return 0
    print("   1 row to write: %s / LOAN_CAPITALISE / %s / Rs %d on loan %s (April's Rs 1,000 comes off)"
          % (STAFF, MONTH, AMOUNT, LOAN_ID))
    if not a["apply"]:
        print("   every precondition holds. To write it (backup first, then a re-check):")
        print("   /root/wa/venv/bin/python3 %s --apply" % os.path.abspath(__file__))
        print("RESTATE PLAN OK")
        return 0
    bak, note = apply_row(sm, a["ledger"], row, md5_at_plan, a["by"])
    print("   written: row %s · the loan's balance moved by exactly Rs %d · no other advance moved" % (row["id"], AMOUNT))
    print("   backup : %s" % bak)
    print("   note   : %s" % note)
    print("RESTATE APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

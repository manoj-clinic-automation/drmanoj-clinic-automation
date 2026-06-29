"""
send_followups.py — the batch driver that connects the tracker to WABA.

It reads the ledgers the tracker already produces, maps each patient's
Followup_Status (and same-day visits) to the correct approved template, and
sends — with hard safety rails:

  • DRY-RUN by default (prints what it would send; sends nothing).
  • Test allowlist: if WABA_TEST_ALLOWLIST is set, ONLY those numbers are sent.
  • De-dupe: a given obligation (Followup_ID) or visit (Visit_ID) receives each
    template at most once, ever (recorded in data/messages_log.csv).
  • Opt-out: numbers in data/opt_outs.csv are never sent.
  • Daily ceiling: if eligible recipients exceed --cap (default 100), it PAUSES
    and refuses to send unless --force is given.

Usage (run from the tracker folder, after a normal daily run):
    python send_followups.py                 # dry run, shows the plan
    python send_followups.py --send          # actually send (respects allowlist)
    python send_followups.py --send --force   # send even if over the cap
    python send_followups.py --kinds B3,B4    # restrict to certain templates

Nothing here changes the tracker's own files; it only appends to messages_log.csv.
"""

from __future__ import annotations
import os
import csv
import sys
import uuid
import argparse
from pathlib import Path
from datetime import date, datetime, timedelta

import waba

DATA_DIR      = Path(__file__).parent / "data"
FOLLOWUP_FILE = DATA_DIR / "followup_ledger.csv"
VISIT_FILE    = DATA_DIR / "visit_ledger.csv"
LOG_FILE      = DATA_DIR / "messages_log.csv"
OPTOUT_FILE   = DATA_DIR / "opt_outs.csv"

LOG_COLS = ["Timestamp", "Kind", "Ref_ID", "Patient_UID", "Mobile", "Template",
            "Var1", "Var2", "Var3", "Myop_Ref_Id", "Message_ID",
            "Conversation_ID", "Status", "Error"]

# Tracker status  →  (template name, kind tag)
STATUS_TEMPLATE = {
    "Due Today":                   ("drmanoj_followup_due",      "B3"),
    "Grace Period":                ("drmanoj_followup_due",      "B3"),
    "Actionable Missed Follow-Up": ("drmanoj_followup_missed",   "B4"),
    "Probable Dropout":            ("drmanoj_followup_dropout",  "B5"),
    # B2 (tomorrow) is derived from "Not Due" + due==tomorrow, handled in code.
}
TOMORROW_TEMPLATE = ("drmanoj_followup_tomorrow", "B2")
POSTVISIT_TEMPLATE = ("drmanoj_post_visit", "B1")


# ── small CSV helpers ─────────────────────────────────────────────────────────
def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fmt_date(iso: str) -> str:
    """'2026-06-14' -> '14 Jun 2026'. Falls back to the raw string."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(iso.strip(), fmt).strftime("%d %b %Y")
        except (ValueError, AttributeError):
            continue
    return iso


def parse_iso(iso: str):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(iso.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def load_optouts() -> set[str]:
    out = set()
    for r in read_csv(OPTOUT_FILE):
        m = waba.normalize_mobile(r.get("Mobile", ""))
        if m:
            out.add(m)
    return out


def load_already_sent() -> set[tuple]:
    """Set of (Ref_ID, Template) already sent successfully — for de-dupe."""
    done = set()
    for r in read_csv(LOG_FILE):
        if str(r.get("Status", "")).upper() in ("SENT", "SUCCESS", "OK"):
            done.add((r.get("Ref_ID", ""), r.get("Template", "")))
    return done


def append_log(rows: list[dict]) -> None:
    new = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LOG_COLS})


# ── build the send plan ───────────────────────────────────────────────────────
def build_plan(today: date, kinds: set[str] | None) -> list[dict]:
    plan: list[dict] = []
    tomorrow = today + timedelta(days=1)

    # Follow-up ladder (B2/B3/B4/B5) from the follow-up ledger
    for r in read_csv(FOLLOWUP_FILE):
        status = r.get("Followup_Status", "")
        name = (r.get("Standard_Name") or r.get("FU_Name_Raw") or "").strip()
        mobile = waba.normalize_mobile(r.get("FU_Mobile_Clean", ""))
        due = parse_iso(r.get("Due_Date", ""))
        ref = r.get("Followup_ID", "")
        uid = r.get("Patient_UID_Resolved", "")
        if status in STATUS_TEMPLATE:
            tmpl, kind = STATUS_TEMPLATE[status]
            variables = [name, fmt_date(r.get("Due_Date", ""))]
            if kind == "B5":
                variables.append(str(r.get("Days_Overdue", "")).strip() or "0")
        elif status == "Not Due" and due == tomorrow:
            tmpl, kind = TOMORROW_TEMPLATE
            variables = [name, fmt_date(r.get("Due_Date", ""))]
        else:
            continue
        if kinds and kind not in kinds:
            continue
        plan.append({"Kind": kind, "Template": tmpl, "Ref_ID": ref,
                     "Patient_UID": uid, "name": name, "mobile": mobile,
                     "variables": variables})

    # Post-visit (B1) from the visit ledger — patients seen today
    if not kinds or "B1" in kinds:
        for r in read_csv(VISIT_FILE):
            if parse_iso(r.get("Visit_Date", "")) != today:
                continue
            name = (r.get("Patient_Name") or "").strip()
            mobile = waba.normalize_mobile(r.get("Mobile_Clean", ""))
            tmpl, kind = POSTVISIT_TEMPLATE
            plan.append({"Kind": kind, "Template": tmpl,
                         "Ref_ID": r.get("Visit_ID", ""),
                         "Patient_UID": r.get("Patient_UID", ""),
                         "name": name, "mobile": mobile, "variables": [name]})
    return plan


def filter_plan(plan, optouts, already, allowlist):
    """Return (eligible, skipped[reason])."""
    eligible, skipped = [], []
    for p in plan:
        if not p["mobile"]:
            skipped.append((p, "invalid/missing mobile")); continue
        if not p["name"]:
            skipped.append((p, "missing name")); continue
        if (p["Ref_ID"], p["Template"]) in already:
            skipped.append((p, "already sent")); continue
        if p["mobile"] in optouts:
            skipped.append((p, "opted out")); continue
        if allowlist is not None and p["mobile"] not in allowlist:
            skipped.append((p, "not in test allowlist")); continue
        eligible.append(p)
    return eligible, skipped


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="actually send (default is dry-run)")
    ap.add_argument("--force", action="store_true", help="send even if over the daily cap")
    ap.add_argument("--cap", type=int, default=int(os.environ.get("WABA_DAILY_CAP", "100")))
    ap.add_argument("--kinds", default="", help="comma list e.g. B1,B3,B4 (default all)")
    ap.add_argument("--date", default="", help="run date YYYY-MM-DD (default today)")
    args = ap.parse_args()

    today = parse_iso(args.date) or date.today()
    kinds = {k.strip().upper() for k in args.kinds.split(",") if k.strip()} or None

    allowlist_env = os.environ.get("WABA_TEST_ALLOWLIST", "").strip()
    allowlist = None
    if allowlist_env:
        allowlist = {m for m in (waba.normalize_mobile(x) for x in allowlist_env.split(",")) if m}

    plan = build_plan(today, kinds)
    optouts = load_optouts()
    already = load_already_sent()
    eligible, skipped = filter_plan(plan, optouts, already, allowlist)

    # Report
    print(f"\n=== WABA send plan for {today} ===")
    by_kind = {}
    for p in eligible:
        by_kind[p["Kind"]] = by_kind.get(p["Kind"], 0) + 1
    print("Eligible by template:", by_kind or "none")
    print(f"Eligible total: {len(eligible)}   Skipped: {len(skipped)}")
    if allowlist is not None:
        print(f"** TEST ALLOWLIST ACTIVE — only {len(allowlist)} numbers can receive **")
    for p in eligible[:20]:
        print(f"  [{p['Kind']}] {p['Template']:<26} {p['mobile']}  {p['name']}  vars={p['variables']}")
    if len(eligible) > 20:
        print(f"  … and {len(eligible) - 20} more")

    # Cap guard
    if len(eligible) > args.cap and not args.force:
        print(f"\n!! PAUSED: {len(eligible)} eligible exceeds cap {args.cap}.")
        print("   Review the plan above. Re-run with --force to send anyway.")
        return

    if not args.send:
        print("\nDRY RUN — nothing sent. Add --send to send for real.")
        return

    # Send
    waba.check_config()
    print("\nSending…")
    log_rows, sent, failed = [], 0, 0
    try:
        for p in eligible:
            ref_id = f"{p['Kind']}-{p['Ref_ID']}-{uuid.uuid4().hex[:8]}"
            res = waba.send_template(p["mobile"], p["Template"], p["variables"],
                                     myop_ref_id=ref_id)
            v = (p["variables"] + ["", "", ""])[:3]
            log_rows.append({
                "Timestamp": datetime.now().isoformat(timespec="seconds"),
                "Kind": p["Kind"], "Ref_ID": p["Ref_ID"], "Patient_UID": p["Patient_UID"],
                "Mobile": p["mobile"], "Template": p["Template"],
                "Var1": v[0], "Var2": v[1], "Var3": v[2], "Myop_Ref_Id": ref_id,
                "Message_ID": res.get("message_id", ""),
                "Conversation_ID": res.get("conversation_id", ""),
                "Status": "SENT" if res.get("ok") else "FAILED",
                "Error": "" if res.get("ok") else f"{res.get('code')} {res.get('message')}",
            })
            if res.get("ok"):
                sent += 1
                print(f"  ✓ {p['mobile']} {p['Template']}  id={res.get('message_id','')[:12]}")
            else:
                failed += 1
                print(f"  ✗ {p['mobile']} {p['Template']}  {res.get('code')} {res.get('message')}")
    except waba.WabaFatalError as e:
        print(f"\n!! HALTED — {e}. No further messages sent this run.")
    finally:
        if log_rows:
            append_log(log_rows)
    print(f"\nDone. Sent: {sent}  Failed: {failed}  Logged to {LOG_FILE.name}")


if __name__ == "__main__":
    main()

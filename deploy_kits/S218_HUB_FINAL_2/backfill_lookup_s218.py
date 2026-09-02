#!/usr/bin/env python3
"""
backfill_lookup_s218.py -- S218: empty the review queue by BOOKING every open
row (owner rulings: "apply all money effects, just show me" · a bill never
sits in a silent queue; an unresolved one books openly).

For each OPEN sale_item_review row (raw_text carries the bill's own JSON:
bill_no, name, phone_last4, mode, amount):
  identity, per D355 (mobile > id > name; name alone only corroborates):
    1. a clinic-id stuck to the name (RAJAT7919) -> patient by that id
    2. phone_last4 + first-name-prefix agreeing on exactly ONE patient -> that patient
    3. otherwise resolve_patient(None, name) -- the ingest's own stub path:
       the money books, the bill's name shows, master-match stays open honestly
  money: amount>=0 -> service 'pharmacy'; amount<0 -> 'pharmacy_return' stored
  positive (the S180 rule). One synthetic ingest_batch per day (adapter
  's218_lookup') so every booked row is traceable and reversible per batch.
  The review row is marked resolved ('booked: s218_lookup'), NEVER deleted.

Prints and writes the per-day money-effect table (the owner shows it to
Darpan): /root/finance/s218_backfill_effects.csv
DRY-RUN by default; --apply to write. Idempotent (only status='open' rows).
"""
import csv
import datetime as dt
import json
import os
import re
import sqlite3
import sys

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(FIN_DIR, "finance.db"))
OUT_CSV = os.environ.get("S218_EFFECTS_CSV",
                         os.path.join(FIN_DIR, "s218_backfill_effects.csv"))
sys.path.insert(0, FIN_DIR)
UNIT = "medical"


def pick_patient(con, name, last4):
    """Returns (patient_ref_id or None, how)."""
    m = re.search(r"^(.*?)(\d{3,5})$", (name or "").strip())
    if m:
        cid = m.group(2)
        p = con.execute("SELECT id, name FROM patient_ref WHERE clinic_id=?",
                        (cid,)).fetchone()
        if p:
            return p["id"], "clinic id %s in the name" % cid
    if last4:
        first = (name or "").strip().split()[0][:4].lower() if (name or "").strip() else ""
        rows = con.execute("SELECT id, name FROM patient_ref WHERE phone_last4=?",
                           (last4,)).fetchall()
        hits = [r for r in rows
                if first and (r["name"] or "").strip().lower().startswith(first)]
        if len(hits) == 1:
            return hits[0]["id"], "phone last4 + name agree (unique)"
    return None, "name only -- booked to the bill's own name (stub)"


def main():
    apply_ = "--apply" in sys.argv
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    import finance_ingest                                    # noqa: PLC0415
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    rows = [dict(r) for r in con.execute(
        "SELECT r.id, r.day_entry_id, r.raw_text, r.guess_name, r.guess_clinic_id, "
        "r.amount_p, r.confidence, d.business_date bd FROM sale_item_review r "
        "JOIN day_entry d ON d.id=r.day_entry_id "
        "WHERE r.status='open' ORDER BY d.business_date")]
    print("open review rows: %d" % len(rows))
    per_day = {}
    batches = {}
    booked = master = stub = 0
    for r in rows:
        try:
            raw = json.loads(r["raw_text"] or "{}")
        except ValueError:
            raw = {}
        name = (raw.get("patient_name") or r["guess_name"] or "").strip()
        bill = (raw.get("bill_no") or "").strip() or None
        last4 = (raw.get("phone_last4") or "").strip() or None
        mode = (raw.get("mode") or "").strip() or None
        amt = int(r["amount_p"] or 0)
        kind_return = amt < 0
        service = "pharmacy_return" if kind_return else "pharmacy"
        clean_name = re.sub(r"\d{3,5}$", "", name).strip()
        pid, how = pick_patient(con, name, last4)
        d = per_day.setdefault(r["bd"], dict(sales_n=0, sales_p=0, ret_n=0, ret_p=0,
                                             master=0, stub=0))
        if kind_return:
            d["ret_n"] += 1; d["ret_p"] += -amt
        else:
            d["sales_n"] += 1; d["sales_p"] += amt
        if pid: d["master"] += 1
        else: d["stub"] += 1
        booked += 1
        if not apply_:
            continue
        if pid is None:
            pid = finance_ingest.resolve_patient(con, None, clean_name or name or None)
            stub += 1
        else:
            master += 1
        b = batches.get(r["day_entry_id"])
        if b is None:
            cur = con.execute(
                "INSERT INTO ingest_batch (day_entry_id, unit, adapter, source_ref, "
                "rows_read, status, run_by, run_at) VALUES (?,?,?,?,?, 'ok', ?, ?)",
                (r["day_entry_id"], UNIT, "s218_lookup",
                 "review-queue backfill (owner OK 02-Sep)", 0, "manoj", now))
            b = batches[r["day_entry_id"]] = cur.lastrowid
        con.execute(
            "INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, "
            "service, description, amount_p, mode, source, source_ref, confidence) "
            "VALUES (?,?,?,?,?,?,?,?, 'manual', ?, ?)",
            (r["day_entry_id"], b, UNIT, pid, service, r["raw_text"],
             abs(amt), mode, bill, r["confidence"]))
        con.execute("UPDATE sale_item_review SET status='resolved', resolved_by=?, "
                    "resolved_at=? WHERE id=?",
                    ("s218_lookup: booked (%s)" % how, now, r["id"]))
    if apply_:
        con.commit()
    hdr = ["day", "bills booked", "sales Rs", "returns booked", "returns Rs",
           "master-matched", "named (stub)"]
    table = [[d, v["sales_n"], "%.2f" % (v["sales_p"] / 100.0), v["ret_n"],
              "%.2f" % (v["ret_p"] / 100.0), v["master"], v["stub"]]
             for d, v in sorted(per_day.items())]
    w = [max(len(str(x)) for x in [h] + [row[i] for row in table])
         for i, h in enumerate(hdr)]
    print("  ".join(h.ljust(w[i]) for i, h in enumerate(hdr)))
    for row in table:
        print("  ".join(str(x).ljust(w[i]) for i, x in enumerate(row)))
    if apply_:
        with open(OUT_CSV, "w", newline="") as f:
            cw = csv.writer(f); cw.writerow(hdr); cw.writerows(table)
        print("effects table written: %s  (share/export to Darpan)" % OUT_CSV)
        print("booked %d rows (%d master-matched, %d named-stub)" % (booked, master, stub))
        left = con.execute("SELECT COUNT(*) c FROM sale_item_review WHERE status='open'").fetchone()["c"]
        print("review rows still open: %d" % left)
    else:
        print("DRY RUN -- nothing written. %d rows would book." % booked)
    return 0


if __name__ == "__main__":
    sys.exit(main())

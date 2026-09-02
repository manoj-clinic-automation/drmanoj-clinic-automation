#!/usr/bin/env python3
"""
correct_days_s218.py -- S218: the owner's OK of 02-Sep ("OK") -- post the
bank-truth corrections for the two relic days of the old model.

  2026-08-28: entered cash 14,398.00 / UPI 999.00 -> cash 8,710.00 / UPI 6,687.00
  2026-08-31: entered cash 40,172.00 / UPI 0.00   -> cash 32,809.00 / UPI 7,363.00

Day totals unchanged; only the SPLIT moves to the bank's settled figure (the
arbiter, owner ruling S208). The old lines are preserved verbatim in
day_revision. reconcile_upi re-runs afterwards so both flags close themselves.
DRY-RUN by default; --apply to write. Idempotent: refuses a day whose UPI
already equals the bank figure.
"""
import datetime as dt
import json
import os
import sqlite3
import sys

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
UNIT = "medical"
DAYS = ["2026-08-28", "2026-08-31"]


def main():
    apply_ = "--apply" in sys.argv
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    import finance_upi                                       # noqa: PLC0415
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for day in DAYS:
        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, day)).fetchone()
        if not e:
            print("%s: no day entry -- skipped" % day)
            continue
        st = con.execute("SELECT parsed_total_p FROM upi_statement WHERE unit=? "
                         "AND statement_date=?", (UNIT, day)).fetchone()
        if not st or not st["parsed_total_p"]:
            print("%s: no bank statement -- REFUSED (bank is the arbiter)" % day)
            continue
        bank = int(st["parsed_total_p"])
        lines = [dict(r) for r in con.execute(
            "SELECT id, service, mode, amount_p, line_kind FROM day_line "
            "WHERE day_entry_id=? AND mode IN ('cash','upi')", (e["id"],))]
        cash = sum(l["amount_p"] for l in lines if l["mode"] == "cash")
        upi = sum(l["amount_p"] for l in lines if l["mode"] == "upi")
        total = cash + upi
        if upi == bank:
            print("%s: UPI already equals the bank (%.2f) -- nothing to do"
                  % (day, bank / 100.0))
            continue
        new_cash = total - bank
        if new_cash < 0:
            print("%s: bank %.2f exceeds the day's cash+UPI %.2f -- REFUSED, "
                  "needs a person" % (day, bank / 100.0, total / 100.0))
            continue
        print("%s: cash %.2f -> %.2f | UPI %.2f -> %.2f (bank-truth)"
              % (day, cash / 100.0, new_cash / 100.0, upi / 100.0, bank / 100.0))
        if not apply_:
            continue
        rev = con.execute("SELECT COALESCE(MAX(revision),0)+1 r FROM day_revision "
                          "WHERE day_entry_id=?", (e["id"],)).fetchone()["r"]
        con.execute("INSERT INTO day_revision (day_entry_id, revision, submitted_at, "
                    "payload_json) VALUES (?,?,?,?)",
                    (e["id"], rev, now, json.dumps(dict(
                        reason="S218 bank-truth correction (owner OK, 02-Sep-2026)",
                        old_lines=lines, bank_p=bank))))
        cash_line = next(l for l in lines if l["mode"] == "cash")
        con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (new_cash, cash_line["id"]))
        upi_lines = [l for l in lines if l["mode"] == "upi"]
        if upi_lines:
            con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (bank, upi_lines[0]["id"]))
            for extra in upi_lines[1:]:
                con.execute("UPDATE day_line SET amount_p=0 WHERE id=?", (extra["id"],))
        else:
            con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p, "
                        "line_kind) VALUES (?, 'pharmacy_sale', 'upi', ?, ?)",
                        (e["id"], bank, cash_line["line_kind"]))
        con.commit()
        r = finance_upi.reconcile_upi(con, UNIT, day)
        print("   reconcile after: match=%s (bank %.2f, entered %.2f)"
              % (r["match"], r["bank_p"] / 100.0, r["entered_p"] / 100.0))
    row = con.execute("SELECT business_date, closing_p FROM v_cash_ledger "
                      "WHERE unit=? ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()
    if row:
        print("running closing after: %s -> Rs %.2f" % (row["business_date"], row["closing_p"] / 100.0))
    if not apply_:
        print("DRY RUN -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

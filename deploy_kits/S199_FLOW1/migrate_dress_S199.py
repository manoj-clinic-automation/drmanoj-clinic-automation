#!/usr/bin/env python3
"""migrate_dress_S199.py — owner ruling S199: the pre-dropdown dress/I-card
ticks of August 2026 meant YES (proper) — the checkbox had no stated polarity
(the inversion finding). Under the new Yes/No dropdown, stored 1 = WITHOUT.
This one-shot sets August's stored flags to 0 so no phantom fine can ever
arise from the old ticks. Backs the DB up first; idempotent."""
import os, shutil, sqlite3, datetime
DB = os.environ.get("SR_DB_PATH", "/root/staff_register/staff_register.db")
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = DB + ".bak_S199_dress_" + ts
shutil.copy2(DB, bak)
con = sqlite3.connect(DB)
before = con.execute("SELECT SUM(dress_improper), SUM(icard_missing) FROM daily_register "
                     "WHERE reg_date LIKE '2026-08-%'").fetchone()
con.execute("UPDATE daily_register SET dress_improper=0, icard_missing=0 "
            "WHERE reg_date LIKE '2026-08-%'")
con.commit()
after = con.execute("SELECT SUM(dress_improper), SUM(icard_missing) FROM daily_register "
                    "WHERE reg_date LIKE '2026-08-%'").fetchone()
con.close()
print("August dress/icard flags: before=%s after=%s (backup: %s)" % (before, after, bak))
print("DONE — the old ticks can no longer read as fines.")

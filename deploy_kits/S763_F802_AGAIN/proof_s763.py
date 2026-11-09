#!/usr/bin/env python3
"""proof_s763.py -- kit S763_F802_AGAIN's proof on a COPY of this box's finance.db (read only; counts and times only, no names, no numbers).

usage: proof_s763.py <code_dir> <root> <finance.db> <scratch> <DUTY_MAP.json> <label>
  code_dir holds amir_day.py and reports_tile.py (the kit's rebuilt files, or the live ones); root/finance and root/marg_ingest give the rest.
It copies finance.db into scratch (sqlite backup), and reads:
  the salt duty by amir_day (n, since, the last list) · the reports tile's salt row · every duty of the map by its own due_sql;
then, IN THE COPY ONLY, sets a made-up salt re-receipt at this minute (the setting the door writes) and reads the salt duty again.
The last line: 'PROOF S763 <label>: salt duty n=N since=S last=L · salt row R · duties D read E err H=<hash> · after a re-receipt now: n=M'.
"""
import hashlib
import importlib.util
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone

CODE, ROOT, DB, SCR, MAP, LABEL = sys.argv[1:7]
IST = timezone(timedelta(hours=5, minutes=30))
sys.path.insert(0, os.path.join(ROOT, "marg_ingest"))
sys.path.insert(1, os.path.join(ROOT, "finance"))
sys.path.insert(0, CODE)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


os.makedirs(SCR, exist_ok=True)
copy = os.path.join(SCR, "proof.db")
if os.path.exists(copy):
    os.remove(copy)
src = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=30)
dst = sqlite3.connect(copy)
src.backup(dst)
dst.close()
src.close()
cx = sqlite3.connect(copy)
cx.row_factory = sqlite3.Row
had = bool(cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='mi_receipt'").fetchone())
n_again = cx.execute("SELECT COUNT(*) FROM mi_receipt").fetchone()[0] if had else 0
hs = bool(cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='setting'").fetchone())
key = cx.execute("SELECT value FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST'").fetchone() if hs else None
KEY = ("present %s" % str(key[0])[:16]) if key and key[0] else "absent"
t0 = time.time()
amir = load("amir_day", os.path.join(CODE, "amir_day.py"))
tile = load("reports_tile", os.path.join(CODE, "reports_tile.py"))
today = datetime.now(IST).date().isoformat()
s = amir._s444_salt(cx)
r = cx.execute(amir.DUTY_SQL["amir.salt_list"]).fetchone()
row = tile._salt_row(cx, today)
rstate = "none" if row is None else str(row.get("state") or "shown")
import json                                                                 # noqa: E402
dmap = json.load(open(MAP, encoding="utf-8"))
res, err = [], 0
for du in dmap.get("duties", []):
    sql = str(du.get("due_sql") or "").strip().rstrip(";").strip()
    if not sql:
        continue
    try:
        got = cx.execute(sql).fetchone()
        res.append("%s=%s" % (du["id"], tuple(got) if got is not None else None))
    except sqlite3.Error as e:
        err += 1
        res.append("%s=ERR %s" % (du["id"], str(e)[:40]))
H = hashlib.md5("\n".join(res).encode("utf-8")).hexdigest()[:12]
verified = cx.execute("SELECT COUNT(*), MAX(received_at) FROM mi_file WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'").fetchone()
newest = cx.execute("SELECT md5 FROM mi_file WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED' ORDER BY received_at DESC LIMIT 1").fetchone()
after = "no verified salt list on this box"
if newest:
    cx.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    cx.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('mi_again:SALT_WISE_ITEM_LIST', ?)",
               (datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),))
    a = cx.execute(amir.DUTY_SQL["amir.salt_list"]).fetchone()
    after = "n=%s" % a[0]
cx.rollback()
cx.close()
os.remove(copy)
el = time.time() - t0
print("  the copy: mi_receipt %s (%d row(s)); the salt re-receipt setting %s; verified salt lists %d, the newest received %s" % (
    "present" if had else "absent", n_again, KEY, verified[0] or 0, str(verified[1] or "-")[:16]))
print("  amir_day: pending %s, ticks %s, oldest tick %s, last list %s" % (s.get("pending"), s.get("ticks"), str(s.get("oldest_tick"))[:16],
                                                                         str(s.get("last_list"))[:16]))
print("  the map: %d duties read by their own due_sql, %d error(s); fingerprint %s; %.1f s" % (len(res), err, H, el))
for line in res:
    if "ERR" in line:
        print("  WARN %s" % line)
print("AGAIN-KEY %s" % KEY)
print("PROOF S763 %s: salt duty n=%s since=%s last=%s · salt row %s · duties %d read %d err H=%s · after a re-receipt now: %s" % (
    LABEL, r[0], str(r[1])[:16], str(s.get("last_list"))[:16], rstate, len(res), err, H, after))

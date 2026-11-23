#!/usr/bin/env python3
"""s939_on.py -- kit S939's switch on the live database. argv: <kit dir> <finance.db> [on|off]
on : setting order.d1053 = 1, and Marg's sheet that is newest at the install marked final by 'install' (its orders are already made:
     tonight's screens are not locked; the first sheet after the install is the first one Darpan makes final).
off: setting order.d1053 = 0 (every screen and door as before the kit; the kit's own tables stay, unused)."""
import datetime as dt, sqlite3, sys
KDIR, DB = sys.argv[1], sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "on"
sys.path.insert(0, KDIR)
import order_d1053 as D
con = sqlite3.connect(DB, timeout=30)
now = dt.datetime.now().replace(microsecond=0).isoformat()
if MODE == "off":
    con.execute("INSERT INTO setting (key, value, note) VALUES ('order.d1053','0','S939: the purchase order flow (D1053) -- 1 on, 0 off') "
                "ON CONFLICT(key) DO UPDATE SET value='0'")
    con.commit()
    print("S939 switch: order.d1053 = 0 (off)")
    sys.exit(0)
D.ensure(con)
r = con.execute("SELECT id FROM order_sheet ORDER BY COALESCE(NULLIF(stamp,''),'0') DESC, taken_at DESC, id DESC LIMIT 1").fetchone()
if r:
    n = con.execute("INSERT OR IGNORE INTO order_d1053_final (sheet_key, day, at, by, counts) VALUES (?,?,?,?,?)",
                    ("sheet:%d" % r[0], dt.date.today().isoformat(), now, "install", '{"install": 1}')).rowcount
    print("S939 switch: Marg's newest sheet %d marked final by the install (%s)" % (r[0], "new" if n else "already"))
con.execute("INSERT INTO setting (key, value, note) VALUES ('order.d1053','1','S939: the purchase order flow (D1053) -- 1 on, 0 off') "
            "ON CONFLICT(key) DO UPDATE SET value='1'")
con.commit()
print("S939 switch: order.d1053 = 1 (on)")

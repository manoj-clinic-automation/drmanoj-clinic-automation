"""make_s645.py -- kit S645_RECEPTION_ORDER_FLOOR (session S349, the parent, 25-Oct-2026; F-1024).
Builds the new /root/finance/aaj_seed.py from the LIVE bytes (2f9ab396, the 25-Oct bundle) with ONE counted edit: the
REWRITE table refitted to the Sanjeevni chat's S619 SQL in DUTY_MAP.json v20 (78b5f07e). Every piece is cut from the map's
own bytes, never retyped.
  reception.order_arrival, shavez.order_followup -- the piece runs from the CTE o's WHERE to the CTE L's FROM: the floor goes on
      o beside its own order.track_since, and L reads main.purchase_order_line.
  reception.bill_scan -- the piece runs from its first to its fourth 'FROM purchase_order_line l': all four read the main table;
      no floor is added (the duty carries its own: purchase.register_from and arrival_scan_days).
WHY main.: the staff connection's floored view of purchase_order_line keeps only lines whose goods ARRIVED on or after the floor
(aaj_seed.FLOOR), so a line where nothing came -- the very line these duties look for -- was hidden from them.
Usage: python make_s645.py <live aaj_seed.py> <DUTY_MAP.json> <out aaj_seed.py>"""
import hashlib, json, sys
FROM, MAP = "2f9ab3964769fa67f709f661db7e067f", "78b5f07ef7cdd48b1a76d78db52107fc"
OLD = ('    "reception.order_arrival": ("WHERE o.status = \'sent\' AND", '
       '"WHERE o.status = \'sent\' AND substr(o.created_at, 1, 10) >= \'{floor}\' AND"),\n')
A0 = "FROM purchase_order WHERE status IN ('sent','received') AND"
A1 = "FROM purchase_order_line l"
src, mp, out = sys.argv[1], sys.argv[2], sys.argv[3]
b = open(src, "rb").read(); mb = open(mp, "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "the live aaj_seed.py is not 2f9ab396"
assert hashlib.md5(mb).hexdigest() == MAP, "DUTY_MAP.json is not v20 78b5f07e"
duties = {d["id"]: d.get("due_sql") or "" for d in json.loads(mb)["duties"]}

def o_to_l(i):
    sql = duties[i]
    assert sql.count(A0) == 1 and sql.count(A1) == 1 and sql.index(A0) < sql.index(A1), i + ": the S619 SQL is not as read"
    piece = sql[sql.index(A0): sql.index(A1) + len(A1)]
    assert sql.count(piece) == 1
    return piece, piece.replace(A0, A0 + " substr(created_at,1,10) >= '{floor}' AND", 1).replace(A1, "FROM main." + A1[5:], 1)

def lines_only(i):
    sql = duties[i]
    assert sql.count(A1) == 4 and "{floor}" not in sql, i + ": the SQL is not as read"
    a = sql.index(A1); z = sql.rindex(A1) + len(A1)
    piece = sql[a:z]
    assert sql.count(piece) == 1 and piece.count(A1) == 4
    return piece, piece.replace(A1, "FROM main." + A1[5:])

ent = [("reception.order_arrival", o_to_l("reception.order_arrival")),
       ("shavez.order_followup", o_to_l("shavez.order_followup")),
       ("reception.bill_scan", lines_only("reception.bill_scan"))]
NEW = ("    # S645 (F-1024): S619_ORDER_TRACKER (22-Oct) rewrote the order duties' SQL. The staff floor's view of purchase_order_line\n"
       "    # keeps only lines whose goods ARRIVED on or after the floor, and these three duties look for lines where nothing came:\n"
       "    # each reads main.purchase_order_line. The two that list orders also take the floor on the CTE o, beside its own\n"
       "    # order.track_since. If the map moves again a piece stops fitting and that line is UNREAD -- never shown unfloored.\n")
for k, (p, n) in ent:
    NEW += "    %s: (%s,\n        %s),\n" % (json.dumps(k), json.dumps(p), json.dumps(n))
s = b.decode("utf-8")
assert s.count(OLD) == 1, "anchor not found exactly once"
s = s.replace(OLD, NEW, 1)
open(out, "wb").write(s.encode("utf-8"))
print("1 counted edit (the REWRITE table: 1 entry refitted, 2 added) ->", hashlib.md5(s.encode("utf-8")).hexdigest())

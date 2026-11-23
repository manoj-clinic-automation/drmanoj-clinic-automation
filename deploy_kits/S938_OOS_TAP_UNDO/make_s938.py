#!/usr/bin/env python3
"""make_s938.py -- kit S938_OOS_TAP_UNDO (23-Nov-2026, Sanjeevni session 508; the owner 18:01 IST). argv: <dir with the FROM files> <out dir>
  order_s778.py 0b94825f -> TO : na_undo() (a staff 'Out of stock' not yet answered by the doctor taken back: the sheet hold, the dropped
      carry, the cleared Dobara row given back, the row removed, the whole row kept in purchase_audit 's778_na_undo'); taps_today();
      the red box carries 'Tapped Out of stock today -- Undo' (two taps); ok_html's 'undone' line.
  order_flow.py e912fc1d -> TO : v2.2 -- his row of a staff tap not yet answered: 'Tapped by mistake -- put back'; act's do=undo_tap.
  porders_s454.py 5ee6b346 -> TO : the door POST /finance/porders/api/s778/na_undo (staff: today's taps; the doctor: any)."""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"order_s778.py": "0b94825fee5036d6246627095fd8ab84", "order_flow.py": "e912fc1db7381d1de8ef5de56c1850dd",
        "porders_s454.py": "5ee6b346c193bcd8e806bc7afef565ab"}


def rd(n):
    b = open(os.path.join(SRC, n), "rb").read()
    if hashlib.md5(b).hexdigest() != FROM[n]:
        sys.exit("%s not at FROM" % n)
    return b.decode("utf-8")


def rep(s, old, new, what):
    if s.count(old) != 1:
        sys.exit("anchor %s: %d" % (what, s.count(old)))
    return s.replace(old, new)


# ---------------------------------------------------------------- order_s778.py
s = rd("order_s778.py")
BLOCK = r'''

# ---- S938_OOS_TAP_UNDO (23-Nov-2026, Sanjeevni session 508; the owner 18:01 IST: "a way back for such accidental taps needed") ----------
#  na_undo(): an 'Out of stock' tap the doctor has not answered (status asked, not cleared, no word of his on it) taken back -- exactly
#  what na() did, reversed: the Marg sheet line's hold (s778_na) removed, a carry it dropped opened again, a Dobara row it cleared given
#  back; the row itself removed (the table admits no 'undone' status and every reader takes an uncleared 'asked' row as the tap) and
#  kept whole in purchase_audit 's778_na_undo'. Staff: a tap of today only. The doctor (and Shavez on his page): any unanswered tap.
#  The red box (reception's order screen) lists today's taps with Undo (two taps, no dialog).
W.update({"tap_hd": ("Aaj 'Out of stock' dabaya — galti se dabaya ho to wapas lijiye", "Tapped 'Out of stock' today — by mistake? Take it back"),
          "tap_undo": ("Wapas lo", "Undo"), "tap_again": ("Dobara dabaiye — wapas", "Tap again to undo"),
          "tap_by": ("%s · %s, %s baje", "%s · %s, %s"),
          "undone": ("%s — wapas order list par", "%s — back on the order list")})


def taps_today(con, day=None):
    """Today's 'Out of stock' taps still waiting for the doctor (status asked, not cleared), oldest first."""
    ensure(con)
    d = str(day or today().isoformat())[:10]
    return [dict(r) for r in con.execute("SELECT id, item, vendor, by, at FROM order_s778_na WHERE status='asked' AND cleared_at IS NULL "
                                         "AND substr(at,1,10)=? ORDER BY id", (d,))]


def _s938_his_word(con, nid):
    """True when the doctor has already said something on this tap (a wait / other / sub mark, or a word of his page)."""
    for sql in ("SELECT 1 FROM order_flow_mark WHERE na_id=? AND undone_at IS NULL LIMIT 1",
                "SELECT 1 FROM order_flow_word WHERE na_id=? AND undone_at IS NULL LIMIT 1"):
        try:
            if con.execute(sql, (int(nid),)).fetchone():
                return True
        except sqlite3.Error:
            pass
    return False


def na_undo(con, who, nid, owner=False):
    """Take back an 'Out of stock' tap made by mistake. (dict, status)."""
    ensure(con)
    r = con.execute("SELECT * FROM order_s778_na WHERE id=?", (int(nid or 0),)).fetchone()
    if not r:
        return dict(ok=False, error="gone", message="Yeh tap ab nahi hai." if not owner else "This tap is no longer there."), 404
    r = dict(r)
    if r["status"] != "asked" or r.get("cleared_at") or _s938_his_word(con, r["id"]):
        return dict(ok=False, error="answered", message=("Doctor sahab ne iska faisla de diya hai — wahi badlenge." if not owner
                                                          else "Your word is already on it — change it from your page.")), 409
    if not owner and str(r["at"])[:10] != today().isoformat():
        return dict(ok=False, error="old_tap", message="Sirf aaj ka tap yahan se wapas hota hai — doctor sahab ko bataiye."), 409
    t = now_iso()
    _unhold_sheet(con, r)
    if r.get("kind") == "carry" and str(r.get("ref") or "").isdigit():
        con.execute("UPDATE order_carry SET dropped_at=NULL, dropped_by=NULL WHERE id=? AND dropped_by='s778_na' AND done_at IS NULL", (int(r["ref"]),))
    if r.get("kind") == "s778" and str(r.get("ref") or "").isdigit():
        con.execute("UPDATE order_s778_again SET cleared_at=NULL, cleared_by=NULL WHERE id=? AND cleared_by LIKE 'na:%' AND done_at IS NULL", (int(r["ref"]),))
    con.execute("DELETE FROM order_s778_na WHERE id=?", (r["id"],))
    _os().audit(con, who, "s778_na_undo", r["id"], dict(r, undone_at=t, kit="S938_OOS_TAP_UNDO"))
    con.commit()
    return dict(ok=True, item=r["item"], vendor=r.get("vendor") or ""), 200


def taps_html(con, en):
    ts = taps_today(con)
    if not ts:
        return ""
    h = ['<div class="s778box" id="s938taps" style="border-color:#8a5a00;background:#fff6e0;margin-top:10px"><div class="hd" style="color:#6b4500">%s</div>'
         % esc(T(en, "tap_hd"))]
    for r in ts:
        hm = str(r["at"])[11:16]
        armed = "if(!this.dataset.a){this.dataset.a='1';this.textContent=%s;return false;}" % esc(__import__("json").dumps(T(en, "tap_again"), ensure_ascii=False))
        h.append('<div class="s778l" data-na="%d"><div></div><div><div class="it">%s</div><div class="dl">%s</div></div><div class="s778btn">'
                 '<button class="gh" onclick="%s%s">%s</button></div></div>'
                 % (int(r["id"]), esc(r["item"]), esc(T(en, "tap_by", short(r.get("vendor") or ""), who_name(r.get("by") or ""), hm)),
                    armed, js_call(P + "/api/s778/na_undo", dict(id=int(r["id"])), _done_then("undone", en)), esc(T(en, "tap_undo"))))
    h.append("</div>")
    return "".join(h)


_s938_red_box_before = red_box


def red_box(con, en, cards=None):                              # noqa: F811 -- S938: today's taps, with Undo, under the box
    h = _s938_red_box_before(con, en, cards)
    try:
        h += taps_html(con, en)
    except Exception as e:                                     # noqa: BLE001 -- the box stands as it was
        print("S938 taps_html failed: %r" % (e,), file=__import__("sys").stderr)
    return h


_s938_ok_before = ok_html


def ok_html(en, args):                                         # noqa: F811 -- S938: the 'back on the order list' line
    if str(args.get("s778") or "") == "undone":
        return '<div class="s778ok" id="s778ok">%s</div>' % esc(T(en, "undone", str(args.get("i") or "")[:80]))
    return _s938_ok_before(en, args)
# ---- S938 end ---------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":'''
s = rep(s, '\n\nif __name__ == "__main__":', BLOCK, "s778 main")
open(os.path.join(OUT, "order_s778.py"), "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- order_flow.py
f = rd("order_flow.py")
f = rep(f, 'VERSION = "2.1"   # S937', 'VERSION = "2.2"   # S938: a staff tap taken back from his row. S937', "flow version")
f = rep(f, '''    if do not in ("same", "two", "sub_by", "other2", "again_sh", "wait2", "not_now", "stop", "came", "sub_by_ok", "sub_by_return"):
        return None
''', '''    if do == "undo_tap":                                          # S938: a staff 'Out of stock' tapped by mistake -- put back
        return _s7().na_undo(con, who, int(b.get("na") or 0), owner=True)
    if do not in ("same", "two", "sub_by", "other2", "again_sh", "wait2", "not_now", "stop", "came", "sub_by_ok", "sub_by_return"):
        return None
''', "act_s926")
f = rep(f, '''    h += '<button onclick="ofCame(this,%s)">It came / we have it…</button>' % esc(__import__("json").dumps(b))
    h += '</div><div class="pick" style="display:none"></div>'
''', '''    h += '<button onclick="ofCame(this,%s)">It came / we have it…</button>' % esc(__import__("json").dumps(b))
    n = s.get("na") or {}
    if n.get("id") and n.get("status") == "asked" and not n.get("cleared_at"):    # S938: the staff's tap, not yet answered
        h += _b926("Tapped by mistake — put back on the order list", dict(b, do="undo_tap", na=int(n["id"])))
    h += '</div><div class="pick" style="display:none"></div>'
''', "sh_buttons")
open(os.path.join(OUT, "order_flow.py"), "w", encoding="utf-8").write(f)

# ---------------------------------------------------------------- porders_s454.py
p = rd("porders_s454.py")
p = rep(p, '''            elif name == "dealer_ok":
                body, code = S.dealer_ok(con, who(u), str(b.get("sn") or ""), str(b.get("item") or ""))
''', '''            elif name == "dealer_ok":
                body, code = S.dealer_ok(con, who(u), str(b.get("sn") or ""), str(b.get("item") or ""))
            elif name == "na_undo":                           # S938: an 'Out of stock' tapped by mistake (staff: today's; the doctor: any)
                body, code = S.na_undo(con, who(u), int(b.get("id") or 0), owner=(kind == "owner"))
''', "door")
p = rep(p, '''for _n778 in ("again", "na", "na_answer", "dealer_ok", "move"):''', '''for _n778 in ("again", "na", "na_answer", "dealer_ok", "move", "na_undo"):''', "routes")
open(os.path.join(OUT, "porders_s454.py"), "w", encoding="utf-8").write(p)
for n in FROM:
    print(hashlib.md5(open(os.path.join(OUT, n), "rb").read()).hexdigest(), n)

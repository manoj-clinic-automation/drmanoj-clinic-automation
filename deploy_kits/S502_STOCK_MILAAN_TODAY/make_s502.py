#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s502.py -- the builder of kit S502_STOCK_MILAAN_TODAY (10-Oct-2026, D699; F-812, F-813, F-814, F-815).

    python3 -B make_s502.py --finance /root/finance --out DIR

Reads THREE live files, refuses anything but their FROM pins, makes anchored edits (every anchor must occur exactly
once -- else NOTHING is written), compiles each python result and refuses anything but its TO pin (all three build,
or nothing is written):

    stock_watch.py    ensure(): void_at / void_why on stock_watch_loss_line (PRAGMA table_info, then ALTER TABLE, on every
                      call); write_point(expected=, expected_as_on=, commit=); correct_roster() -- 'Galat likha? Badlo';
                      superseded points skipped where points are picked or summed (last_point, month_leak, the watch list's
                      three points and its trend); answer_roster's second-entry message; roster_view can_fix / by;
                      darpan_view: the loss lines of the last 7 days that are not voided, in plain words
    stockmatch.py     POST /finance/stockmatch/api/spot/fix; /api/recount refuses a non-owner (the 06-Sep count is sealed)
    stockmatch.html   Darpan's page shows only today's work (D699): Aaj ki ginti with 'Galat likha? Badlo', the Sunday card,
                      the unanswered swap pairs, the open lines, the unanswered claims, Stock batao, Kuchh gadbad hai?,
                      'Pichhle 7 din mein kam nikla'. Gone: the 06-Sep block and its note box, the progress bar, the heading
                      '06-Sep ki ginti · round 1', Dobara ginna hai, System ne dekha.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import os
import sys

PINS = {   # file: (FROM md5, TO md5)
    "stock_watch.py": ("d78c902e0d3258fd0c615cd9715346b6", "c960f6c890e3e83c58b88d8a7f219752"),
    "stockmatch.py": ("f09d9516a9df73941033591af8878c3e", "fc1caf4496c4fd072e909b4d3e6784aa"),
    "stockmatch.html": ("0dc4d303434d6f87d9e470bccb79f54c", "02826136d9cbb015dfb44c63ef5263d1"),
}


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise Stop("anchor '%s' occurs %d times (must be exactly 1)" % (what, n))
    return text.replace(old, new)


def after(text, anchor, add, what):
    return one(text, anchor, anchor + add, what)


def before(text, anchor, add, what):
    return one(text, anchor, add + anchor, what)


def span(text, start, end, new, what):
    """Replace everything from `start` up to (not including) `end`; each must occur exactly once, start before end."""
    if text.count(start) != 1 or text.count(end) != 1:
        raise Stop("span '%s': start occurs %d times, end %d times (each must be exactly 1)" % (what, text.count(start), text.count(end)))
    i, j = text.index(start), text.index(end)
    if not i < j:
        raise Stop("span '%s': its end is not after its start" % what)
    return text[:i] + new + text[j:]


# =====================================================================================================================
# stock_watch.py
# =====================================================================================================================
SW_COLS = r'''_UNSET = object()                                          # S502: 'not given' for write_point(expected=) -- None already means "work it out fresh"


def _s502_columns(con):
    """S502 (F-814): void_at / void_why on stock_watch_loss_line -- added on EVERY call to a database whose tables already exist
    (ensure()'s own branch runs only when a table is missing). A voided line is one the system no longer believes; it is never deleted."""
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_watch_loss_line)").fetchall()}
        for c in ("void_at", "void_why"):
            if cols and c not in cols:
                con.execute("ALTER TABLE stock_watch_loss_line ADD COLUMN %s TEXT" % c)
    except sqlite3.Error:
        pass


'''

SW_WRITE_POINT_OLD = "def write_point(con, item, qty_units, source, who, roster_id=None, note=None, sp=None, count_id=None, silent=False):\n"
SW_WRITE_POINT_NEW = ("def write_point(con, item, qty_units, source, who, roster_id=None, note=None, sp=None, count_id=None, silent=False,\n"
                      "                expected=_UNSET, expected_as_on=None, commit=True):\n")
SW_EXPECTED_OLD = "    E = _s454_expected(con, sp, item)                          # S454 P3 (9.2, D667): the shelf figure, else the records' expectation\n"
SW_EXPECTED_NEW = ("    if expected is _UNSET:\n"
                   "        E = _s454_expected(con, sp, item)                      # S454 P3 (9.2, D667): the shelf figure, else the records' expectation\n"
                   "    else:                                                      # S502 (F-812): a correction is judged against the figure the old point was judged on\n"
                   "        E = dict(expected=(None if expected is None else float(expected)), provisional=0.0,\n"
                   "                 as_on=(str(expected_as_on)[:10] if expected_as_on else None))\n")
SW_COMMIT_OLD = ("    _audit(con, \"point\", dict(item=item, qty=float(qty_units), source=source, expected=E[\"expected\"], gap=gap, status=status, "
                 "text=\"%s: %s counted (%s), %s\" % (item, P[\"qty_text\"], source, P[\"verdict\"])), who, pid)\n    con.commit()\n    return P\n")
SW_COMMIT_NEW = ("    _audit(con, \"point\", dict(item=item, qty=float(qty_units), source=source, expected=E[\"expected\"], gap=gap, status=status, "
                 "text=\"%s: %s counted (%s), %s\" % (item, P[\"qty_text\"], source, P[\"verdict\"])), who, pid)\n"
                 "    if commit:                                                 # S502: correct_roster commits its one transaction itself\n"
                 "        con.commit()\n    return P\n")

SW_CORRECT = r'''

def correct_roster(con, roster_id, qty_units, who, is_owner=False, sp=None):
    """S502 (D699, F-812) -- 'Galat likha? Badlo': a morning-list count corrected THE SAME DAY by the one who wrote it (or the owner).
    A count is never lost, only replaced: the old point is marked superseded (its note names the replacement) and a NEW point takes
    its place, judged against the figure the OLD point was judged on (its own expected_units -- never a fresh shelf figure, which
    would take the wrong old point itself as the base and book a false loss). The old point's loss line is voided, its open trace
    closed BY ITS OWN ID. Every path returns four values (ok, msg, code, P), the shape of answer_roster; refusals carry P=None."""
    r = con.execute("SELECT id, item, day, answered_at, qty_units, point_id FROM stock_spot_roster WHERE id=?", (int(roster_id),)).fetchone()
    if not r or not r[3] or not r[5]:
        return False, "Yeh ginti abhi likhi nahi gayi.", 404, None
    if str(r[2])[:10] != today().isoformat():
        return False, "Sirf aaj ki ginti badal sakte hain.", 409, None
    old = con.execute("SELECT id, item, qty_units, expected_units, at, by, note FROM stock_point WHERE id=?", (int(r[5]),)).fetchone()
    if not old:
        return False, "Yeh ginti abhi likhi nahi gayi.", 404, None
    if (old[5] or "") != (who or "") and not is_owner:
        return False, "Yeh ginti kisi aur ne likhi thi — doctor sahab se kahiye.", 403, None
    q = float(qty_units)
    if q == float(r[4] if r[4] is not None else old[2]):
        return True, "Wahi ginti pehle se likhi hai.", 200, None
    sp = sp or Spine()
    info = item_info(con, sp, old[1])
    old_words = qw(old[2], info["pack"], info["packing"], old[1], "hi")
    ts = now_iso()
    try:
        con.execute("UPDATE stock_point SET status='superseded' WHERE id=?", (old[0],))
        P = write_point(con, old[1], q, "spot", who, roster_id=r[0], note="badla: pehle %s likha tha (point %d)" % (old_words, old[0]), sp=sp,
                        expected=old[3], expected_as_on=str(old[4] or "")[:10], commit=False, silent=True)
        con.execute("UPDATE stock_point SET note=? WHERE id=?", (((old[6] + " · ") if old[6] else "") + "S502: badla, ab point %d" % P["id"], old[0]))
        con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why='ginti badli' WHERE point_id=? AND void_at IS NULL", (ts, old[0]))
        con.execute("UPDATE stock_trace SET status='seen', seen_by='S502', seen_at=? WHERE status='open' AND json_extract(findings_json,'$.point_id')=?", (ts, old[0]))
        con.execute("UPDATE stock_spot_roster SET qty_units=?, point_id=?, answered_at=? WHERE id=?", (q, P["id"], ts, r[0]))
        _audit(con, "spot_fix", dict(item=old[1], old_qty=float(old[2]), new_qty=q, old_point=old[0], new_point=P["id"]), who, P["id"])
        con.commit()
    except Exception:                                         # noqa: BLE001 -- nothing half-written
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return False, "Nahi hua, dobara koshish kijiye.", 500, None
    if P.get("loss_line"):                                    # still short beyond the allowance against the old expected figure: its trace, as write_point would have
        try:
            P["trace"] = open_trace(con, old[1], "point", P["gap"], who, sp=sp, point_id=P["id"])["id"]
        except Exception:                                     # noqa: BLE001 -- the correction stands; the trace is a courtesy
            P["trace"] = None
    return True, "Badal diya: %s — %s. %s" % (old[1], P["qty_hi"], P["verdict_hi"]), 200, P
'''

SW_ROSTER_VIEW_OLD = ("    for x in rows:\n        if x[\"point_id\"]:\n"
                      "            p = con.execute(\"SELECT gap_units, status, note FROM stock_point WHERE id=?\", (x[\"point_id\"],)).fetchone()\n"
                      "            x[\"gap\"] = p[0] if p else None\n")
SW_ROSTER_VIEW_NEW = ("    for x in rows:\n"
                      "        x[\"can_fix\"] = bool(x[\"answered_at\"]) and str(x[\"day\"])[:10] == today().isoformat()     # S502 (D699): 'Galat likha? Badlo' the same day\n"
                      "        x[\"by\"] = \"\"\n"
                      "        if x[\"point_id\"]:\n"
                      "            p = con.execute(\"SELECT gap_units, status, note, by FROM stock_point WHERE id=?\", (x[\"point_id\"],)).fetchone()\n"
                      "            x[\"gap\"] = p[0] if p else None\n"
                      "            x[\"by\"] = (p[3] or \"\") if p else \"\"\n")

SW_LOSSES_OLD = ("        losses = [dict(id=r[0], at=r[1], at_text=dmy(r[1][:10]), item=r[2], text_hi=\"%s: %s %s kam\" % (\"Aaj\" if r[1][:10] == today().isoformat() else dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or \"\", r[2], \"hi\")),\n"
                 "                       text=\"%s: %s %s short\" % (dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or \"\", r[2])))\n"
                 "                  for r in con.execute(\"SELECT id, at, item, gap_units, pack, packing FROM stock_watch_loss_line ORDER BY id DESC LIMIT 12\")]\n")
SW_LOSSES_NEW = ("        # S502 (D699, F-814): the last 7 days' lines that the system still believes (a voided line shows nowhere), in plain words\n"
                 "        losses = [dict(id=r[0], at=r[1], at_text=dmy(r[1][:10]), item=r[2],\n"
                 "                       text_hi=\"%s: %s — %s kam. Doctor sahab dekh rahe hain.\" % (\"Aaj\" if r[1][:10] == today().isoformat() else dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or \"\", r[2], \"hi\")),\n"
                 "                       text=\"%s: %s %s short\" % (dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or \"\", r[2])))\n"
                 "                  for r in con.execute(\"SELECT id, at, item, gap_units, pack, packing FROM stock_watch_loss_line WHERE void_at IS NULL AND at >= ? ORDER BY id DESC LIMIT 12\",\n"
                 "                                       ((today() - dt.timedelta(days=7)).isoformat(),))]\n")


def build_stock_watch(t):
    t = one(t, "  at TEXT NOT NULL, item TEXT NOT NULL, gap_units REAL NOT NULL, pack INTEGER, packing TEXT, mrp_p INTEGER, point_id INTEGER\n);\n",
            "  at TEXT NOT NULL, item TEXT NOT NULL, gap_units REAL NOT NULL, pack INTEGER, packing TEXT, mrp_p INTEGER, point_id INTEGER,\n"
            "  void_at TEXT, void_why TEXT                -- S502 (F-814): a line the system no longer believes -- voided, never deleted\n);\n", "SCHEMA: the loss line")
    t = before(t, "def ensure(con):\n", SW_COLS, "def ensure")
    t = after(t, "    if len(have) < len(_TABLES):\n        con.executescript(SCHEMA)\n", "    _s502_columns(con)\n", "ensure: the missing-table branch")
    t = one(t, "    r = con.execute(q + \" ORDER BY at DESC, id DESC LIMIT 1\", (item_norm,)).fetchone()\n",
            "    q += \" AND status<>'superseded'\"                          # S502: a replaced count is never picked\n"
            "    r = con.execute(q + \" ORDER BY at DESC, id DESC LIMIT 1\", (item_norm,)).fetchone()\n", "last_point")
    t = one(t, SW_WRITE_POINT_OLD, SW_WRITE_POINT_NEW, "write_point: the signature")
    t = one(t, SW_EXPECTED_OLD, SW_EXPECTED_NEW, "write_point: the expectation")
    t = one(t, SW_COMMIT_OLD, SW_COMMIT_NEW, "write_point: the commit")
    t = one(t, "        return True, \"Pehle hi likha hai.\", 200, None\n",
            "        return True, \"Pehle hi likha hai — badalna ho to 'Galat likha? Badlo' dabaiye.\", 200, None     # S502\n", "answer_roster: already answered")
    t = after(t, "    return True, \"Likh liya: %s — %s. %s\" % (r[1], P[\"qty_hi\"], P[\"verdict_hi\"]), 200, P\n", SW_CORRECT, "answer_roster: its last line")
    t = one(t, SW_ROSTER_VIEW_OLD, SW_ROSTER_VIEW_NEW, "roster_view: the point lookup")
    t = one(t, "        for r in con.execute(\"SELECT id, item, gap_units, at FROM stock_point WHERE substr(at,1,7)=? AND gap_units<0 AND source<>'full_count'\", (ym,)):\n",
            "        for r in con.execute(\"SELECT id, item, gap_units, at FROM stock_point WHERE substr(at,1,7)=? AND gap_units<0 AND source<>'full_count' AND status<>'superseded'\", (ym,)):   # S502\n",
            "month_leak: the month's points")
    t = one(t, "               for p in con.execute(\"SELECT at, qty_units, gap_units, source FROM stock_point WHERE item_norm=? ORDER BY at DESC LIMIT 3\", (norm_name(name),))]\n",
            "               for p in con.execute(\"SELECT at, qty_units, gap_units, source FROM stock_point WHERE item_norm=? AND status<>'superseded' ORDER BY at DESC LIMIT 3\", (norm_name(name),))]   # S502\n",
            "watch_list: the three points")
    t = one(t, "            g = con.execute(\"SELECT COALESCE(SUM(CASE WHEN gap_units<0 THEN -gap_units ELSE 0 END),0) FROM stock_point WHERE item_norm=? AND at>=? AND at<?\", (norm_name(name), m0.isoformat(), m1.isoformat())).fetchone()[0]\n",
            "            g = con.execute(\"SELECT COALESCE(SUM(CASE WHEN gap_units<0 THEN -gap_units ELSE 0 END),0) FROM stock_point WHERE item_norm=? AND at>=? AND at<? AND status<>'superseded'\", (norm_name(name), m0.isoformat(), m1.isoformat())).fetchone()[0]   # S502\n",
            "watch_list: the trend")
    t = one(t, SW_LOSSES_OLD, SW_LOSSES_NEW, "darpan_view: the loss lines")
    t = one(t, "VERSION = \"1.3\"\nKIT = \"S436_STAFF_PAGES_CLEAN\"                                 # v1.2 was S432_DESK_GROUP_FLOW\n",
            "VERSION = \"1.4\"\nKIT = \"S502_STOCK_MILAAN_TODAY\"                               # v1.3 was S436_STAFF_PAGES_CLEAN\n"
            "# v1.4 (S502, D699, 10-Oct-2026; F-812, F-813, F-814, F-815): a morning-list count can be corrected the same day (correct_roster -- the old\n"
            "# point superseded, never deleted; the new one judged on the OLD expected figure); a loss line can be VOIDED (void_at / void_why, F-814) and a\n"
            "# voided line shows nowhere; superseded points are skipped where points are picked or summed; Darpan's page shows the last 7 days' loss lines\n"
            "# in plain words. The 06-Sep count is sealed for staff (stockmatch.api_recount). THE LAST PATCH on this layer under the S303 build charter.\n",
            "the version line")
    return t


# =====================================================================================================================
# stockmatch.py
# =====================================================================================================================
SM_FIX = r'''@bp.route("/finance/stockmatch/api/spot/fix", methods=["POST"])
def api_spot_fix():
    """S502 (D699, F-812) -- 'Galat likha? Badlo': {roster_id, strips, loose} or {roster_id, pcs}, parsed as api_spot; the same day, by
    the one who wrote the count (or the owner); the old point is superseded, never deleted (stock_watch.correct_roster)."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        rid = int(b.get("roster_id") or 0)
    except (TypeError, ValueError):
        rid = 0
    r = con.execute("SELECT pack FROM stock_spot_roster WHERE id=?", (rid,)).fetchone() if rid else None
    if not r:
        return jsonify(ok=False, error="not_found", message="Yeh item aaj ki list mein nahi hai."), 404
    try:
        q = _qty_from(b, r[0])
    except (TypeError, ValueError):
        q = None
    if q is None or q < 0 or q > 100000:
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code, P = _sw().correct_roster(con, rid, q, (u or {}).get("user") or "", is_owner=(kind == "owner"))
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="spot_fix", message=msg, point=P))


'''


def build_stockmatch_py(t):
    t = after(t, "    \"\"\"Phir se gino: {item, strips, loose} or {item, units}. His figure replaces the shelf; the owner's desk re-piles.\"\"\"\n"
                 "    u, con, kind, err = _auth()\n    if err:\n        return err\n",
              "    if kind != \"owner\":                                       # S502 (D699, F-813): the 06-Sep count is SEALED for staff -- today's count goes to Stock batao\n"
              "        return jsonify(ok=False, error=\"moved\", message=\"Aaj ki ginti 'Stock batao' mein likhiye.\"), 403\n", "api_recount: after the auth")
    t = before(t, "@bp.route(\"/finance/stockmatch/api/watch-items\")\n", SM_FIX, "the watch-items route")
    t = one(t, "VERSION = \"1.1\"\nKIT = \"S436_STAFF_PAGES_CLEAN\"                                 # v1.0 was S404_ORTHO_STOCK_CLOSE\n",
            "VERSION = \"1.2\"\nKIT = \"S502_STOCK_MILAAN_TODAY\"                               # v1.1 was S436_STAFF_PAGES_CLEAN\n"
            "# v1.2 (S502, D699, 10-Oct-2026; F-812, F-813): POST /api/spot/fix -- 'Galat likha? Badlo' (stock_watch.correct_roster); /api/recount refuses\n"
            "# a non-owner (the 06-Sep count is sealed; today's count goes to Stock batao). The section verdict, the block and the claims are still computed.\n",
            "the version line")
    return t


# =====================================================================================================================
# stockmatch.html -- Darpan's page, D699
# =====================================================================================================================
HTML_COMMENT_OLD = "The verdict tail and the four status lines are gone. -->"
HTML_COMMENT_NEW = ("The verdict tail and the four status lines are gone.\n"
                    "     S502_STOCK_MILAAN_TODAY (10-Oct-2026, D699; F-812 .. F-815) -- the owner: \"this should only show to Darpan what he needs to do and not\n"
                    "     what has already been done on the 6th September work.\" So the page shows ONLY today's work: Aaj ki ginti (an answered row can be\n"
                    "     corrected the same day -- 'Galat likha? Badlo' -> /api/spot/fix), the Sunday card, the swap pairs only while one is unanswered, the\n"
                    "     open lines he has not answered, Bina bill? only for claims without an answer, Stock batao, Kuchh gadbad hai?, and the last 7 days'\n"
                    "     shortages in plain words ('Pichhle 7 din mein kam nikla' -- information only). GONE from his page: the 06-Sep block and its note\n"
                    "     box, the progress bar, the heading '06-Sep ki ginti · round 1', Dobara ginna hai (it wrote into the sealed 06-Sep count, F-813),\n"
                    "     System ne dekha. Those stay on the owner's Loss desk. Every figure still comes from /api/state; nothing is computed here. -->")

HTML_RENDER = r'''function render(){
 const s=S; let h=msgHtml();
 h+=s428Top(s);                                              // S428 / S502: Aaj ki ginti (an answered row: 'Galat likha? Badlo' the same day), the count's Sunday
 h+=pairsCard(s);                                            // S502 (D699): only while a pair is unanswered, and only those pairs
 h+=linesCard(s);                                            // S502: only the open lines he has not answered (a defaulted line is finished work)
 h+=workCards(s);                                            // S502: Bina bill? (unanswered claims), Stock batao, Kuchh gadbad hai?, the last 7 days' shortages
 const R=(s.watch&&s.watch.roster)||null;
 el("sub").textContent="Aaj: "+((R&&R.day_text)?R.day_text:todayText());   // S502: the day only -- no '06-Sep ki ginti', no round
 el("body").innerHTML=h;
}
function todayText(){const d=new Date();const p=n=>String(n).padStart(2,"0");return p(d.getDate())+"-"+p(d.getMonth()+1)+"-"+d.getFullYear();}
'''

HTML_PAIRS = r'''function pairsCard(s){
 const P=(s.pairs||[]).filter(p=>!p.answer&&!p.by_words);    // S502 (D699): an answered pair is finished work -- it leaves the page
 if(!P.length) return '';
 let h='<div class="card"><h2>Adla-badli? <span class="tag">'+P.length+'</span></h2><div class="muted">Ek size kam, doosra zyada &mdash; kya doosre size ka bill bana tha? Haan = adla-badli.</div>';
 P.forEach(p=>{
  h+='<div class="pair"><div class="row"><span class="k">Kam:</span><span class="nm">'+esc(p.short)+'</span></div>'+
     '<div class="row"><span class="k">Zyada:</span><span class="nm">'+esc(p.over)+'</span></div>'+
     '<div class="muted">'+esc(p.qty_text)+' &middot; '+esc(p.close)+(p.family?' &middot; '+esc(p.family):'')+'</div>'+
     '<div><span class="btn ok" onclick="pair(\''+esc(p.short).replace(/'/g,"\\'")+'\',\''+esc(p.over).replace(/'/g,"\\'")+'\',\'YES\')">Haan</span><span class="btn bad" onclick="pair(\''+esc(p.short).replace(/'/g,"\\'")+'\',\''+esc(p.over).replace(/'/g,"\\'")+'\',\'NO\')">Nahi</span></div></div>';
 });
 return h+'</div>';
}
'''

HTML_LINES = r'''function linesCard(s){
 const L=(s.lines||[]).filter(l=>l.open&&!l.defaulted);       // S502 (D699): the defaulted 06-Sep lines are finished work -- only what is still open
 if(!L.length) return '';
 const open2=L.filter(l=>!l.answered).length;
 let h='<div class="card"><h2>Kam kyun? <span class="tag">'+open2+'</span></h2><div class="muted">Adla-badli ke baad jo kam ya zyada bacha &mdash; ek tap: kam = bina bill bik gaya, zyada = bill bana par diya nahi.</div>';
 L.forEach(l=>{
  const own=l.reasoned&&l.cause_by&&l.cause_by!==s.user;
  h+='<div class="line'+(l.answered?(own||l.word?' owner':' done'):'')+'"><div class="nm">'+esc(l.item)+'</div>'+
     '<div class="muted">Marg '+l.marg+' &middot; gina '+l.counted+' &middot; <b>'+esc(l.rem_text)+'</b>'+(l.swapped?' &middot; adla-badli '+l.swapped+' ('+esc(l.swap_with.join(", "))+')':'')+'</div>';
  if(l.word) h+='<div class="ans owner">Doctor sahab: '+esc(l.word)+'</div>';
  if(l.reasoned) h+='<div class="ans'+(own?' owner':'')+'">'+(own?'Doctor sahab':'Aapne')+': '+esc(l.cause_hi)+(l.cause_at_text?' <span class="muted">('+esc(l.cause_at_text)+')</span>':'')+'</div>';
  if(!l.locked&&!l.word) h+='<div>'+l.reasons.map(r=>'<span class="btn chip'+(l.cause===r.key?' on':'')+'" onclick="reason('+l.diff_id+',\''+r.key+'\')">'+esc(r.hi)+'</span>').join("")+'</div>';
  h+='</div>';
 });
 return h+'</div>';
}
'''

HTML_WORK = r'''/* ---- S418 (D631) / S502 (D699): Bina bill? -- only the claims without an answer; then the S428 cards. (Dobara ginna hai and the
   06-Sep block are gone from this page: the count is sealed, F-813 / F-815; they stay on the owner's Loss desk.) ---- */
function workCards(s){
 let h='';
 const C=(s.claims||[]).filter(c=>!c.answer), A=s.claim_answers||[];
 if(C.length){
  h+='<div class="card"><h2>Bina bill? <span class="tag">'+C.length+'</span></h2><div class="muted">Doctor sahab in lines ka pata kar rahe hain &mdash; ek jawab chuniye.</div>';
  C.forEach(c=>{
   h+='<div class="line"><div class="nm">'+esc(c.item)+'</div>'+(c.short_qty?'<div class="muted">'+c.short_qty+' kam</div>':'');
   h+='<div>'+A.map(a=>'<span class="btn chip" onclick="claim('+c.id+',\''+a.key+'\')">'+esc(a.hi)+'</span>').join("")+'</div></div>';
  });
  h+='</div>';
 }
 h+=s428Cards(s);
 return h;
}
'''

HTML_TOP = r'''function s428Top(s){
 const W=s.watch; if(!W||!W.ok) return '';
 let h='';
 const R=W.roster||{items:[]};
 if(R.items.length){
  h+='<div class="card"><h2>Aaj ki ginti <span class="tag">'+R.open+'</span></h2><div class="muted">'+esc(R.day_text)+' &middot; yeh '+R.items.length+' item aaj subah gin kar likhiye. Shelf par jitna hai utna.</div>';
  R.items.forEach(r=>{
   h+='<div class="line'+(r.answered_at?' done':'')+'"><div class="nm">'+esc(r.item)+'</div><div class="muted">'+esc(r.packing||'')+(r.pack>1?' &middot; ek patte mein '+r.pack:'')+(r.reason_hi?' &middot; '+esc(r.reason_hi):'')+'</div>';
   if(r.answered_at){
    h+='<div class="ans">Aapne gina: <b>'+esc(r.qty_hi)+'</b></div>';
    if(r.can_fix){                                             // S502 (D699, F-812): the same day, the one who wrote it may correct it
     if(FIX===r.id) h+='<div class="muted">Sahi ginti likhiye:</div><div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(r.pack,r.whole_hi,"f"+r.id)+'<span class="btn ok" onclick="spotFix('+r.id+','+r.pack+')">Badal do</span><span class="btn" onclick="FIX=null;render()">Rehne do</span></div>';
     else h+='<div><span class="btn chip" onclick="FIX='+r.id+';render()">Galat likha? Badlo</span></div>';
    }
   }
   else h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(r.pack,r.whole_hi,"r"+r.id)+'<span class="btn ok" onclick="spot('+r.id+','+r.pack+')">Bhej do</span></div>';
   h+='</div>';
  });
  h+='</div>';
 }
 if(W.plan){
  h+='<div class="card"><h2>Poori ginti ka Sunday</h2><div class="muted">'+esc(W.plan.text_hi)+'</div>';
  if(!W.plan.confirmed) h+='<div><span class="btn ok" onclick="plan(\'ok\')">Theek hai</span><span class="btn bad" onclick="plan(\'no\')">Nahi ho payega</span></div>';
  h+='</div>';
 }
 return h;
}
let FIX=null;                                                   // S502: which answered row has its 'Badal do' boxes open (a page variable, no storage)
'''

HTML_CARDS = r'''function s428Cards(s){
 const W=s.watch; if(!W||!W.ok) return '';
 let h='';
 h+='<div class="card"><h2>Stock batao</h2><div class="muted">Kisi bhi din, koi bhi item: naam likhiye, phir shelf par jitna hai utna likhiye.</div>';
 h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="sq" placeholder="Item ka naam" oninput="wsearch(\'sq\',\'ssugg\',\'spick\')" autocomplete="off" style="flex:1;min-width:12em;font-size:17px;padding:8px"></div><div id="ssugg" class="sugg"></div>';
 if(SSEL){ h+='<div class="line"><div class="nm">'+esc(SSEL.item)+'</div><div class="muted">'+esc(SSEL.packing||'')+(SSEL.pack>1?' &middot; ek patte mein '+SSEL.pack:'')+'</div><div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(SSEL.pack,SSEL.whole,"s")+'<span class="btn ok" onclick="stockBatao()">Likh do</span></div></div>'; }
 h+='</div>';
 h+='<div class="card"><h2>Kuchh gadbad hai?</h2><div class="muted">Koi item kam lag raha hai, ek-do dabbe nahi mil rahe? Item chuniye, kya dikh raha hai likhiye. System bikri aur kharid dekh kar batayega.</div>';
 h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="gq" placeholder="Item ka naam" oninput="wsearch(\'gq\',\'gsugg\',\'gpick\')" autocomplete="off" style="flex:1;min-width:12em;font-size:17px;padding:8px"></div><div id="gsugg" class="sugg"></div>';
 if(GSEL){ h+='<div class="line"><div class="nm">'+esc(GSEL.item)+'</div><div class="muted">'+esc(GSEL.packing||'')+(GSEL.pack>1?' &middot; ek patte mein '+GSEL.pack:'')+'</div>'
   +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="gt" placeholder="Kya gadbad hai?" maxlength="500" style="flex:1;min-width:12em;font-size:16px;padding:8px"></div>'
   +'<div class="muted">Abhi shelf par kitna hai (likh sakein to):</div><div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(GSEL.pack,GSEL.whole,"g")+'<span class="btn ok" onclick="gadbad()">Bhej do</span></div></div>'; }
 h+='</div>';
 if((W.losses||[]).length){                                   // S502 (D699): the last 7 days' shortages, information only -- the server's lines (voided ones never come)
  h+='<div class="card"><h2>Pichhle 7 din mein kam nikla</h2><div class="muted">Sirf jaankari ke liye &mdash; aapko kuchh nahi karna.</div>'+W.losses.map(l=>'<div class="line"><div class="nm">'+esc(l.text_hi)+'</div></div>').join("")+'</div>';
 }
 return h;
}
'''

HTML_SPOTFIX = r'''async function spotFix(rid, pack){
 if(BUSY)return; const body={roster_id:rid};                  // S502 (D699, F-812): 'Badal do' -> /api/spot/fix, the same boxes as an unanswered row
 if(!readBoxes(pack,"f"+rid,body)){MSG={kind:"err",title:"Sahi ginti likhiye",lines:[]};render();return;}
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/spot/fix"+Q,body); FIX=null; after(j,"\u2713 Badal diya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
'''


def build_stockmatch_html(t):
    t = one(t, HTML_COMMENT_OLD, HTML_COMMENT_NEW, "the head comment")
    t = one(t, '<div class="sub" id="sub">06-Sep ki ginti &middot; sirf orthotics</div>', '<div class="sub" id="sub"></div>', "the static sub-heading")
    t = span(t, "function render(){\n", "/* ---- card 1 -- the pairs:", HTML_RENDER, "render()")
    t = span(t, "function pairsCard(s){\n", "/* ---- card 2 -- the lines:", HTML_PAIRS, "pairsCard()")
    t = span(t, "function linesCard(s){\n", "/* ---- S427 (D632): THE STAFF BLOCK", HTML_LINES, "linesCard()")
    t = span(t, "/* ---- S427 (D632): THE STAFF BLOCK", "/* ---- S428 (D633): Darpan's side of the watch.", HTML_WORK, "the block, Dobara ginna hai and the note box")
    t = span(t, "function s428Top(s){\n", "function s428Cards(s){\n", HTML_TOP, "s428Top()")
    t = span(t, "function s428Cards(s){\n", "let SSEL=null, GSEL=null, WSUGG={}, WT=null;\n", HTML_CARDS, "s428Cards()")
    t = before(t, "async function stockBatao(){\n", HTML_SPOTFIX, "stockBatao()")
    js = t.split("<script>", 1)[1]                             # the ACTIVE code only: the head comment and the CSS keep the old words on purpose
    for word in ("blockCard(", "function tbl(", "function recount(", "function rsearch(", "function rpick(", "function note(", "RSEL", "System ne dekha",
                 "Dobara ginna hai</h2>", "class=\"prog\"", "Badi kami", "ki ginti · "):
        if word in js:
            raise Stop("the built page's script still carries '%s'" % word)
    return t


BUILD = {"stock_watch.py": build_stock_watch, "stockmatch.py": build_stockmatch_py, "stockmatch.html": build_stockmatch_html}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True, help="the folder holding the three live files")
    ap.add_argument("--out", required=True, help="where the built files are written (created)")
    ap.add_argument("--print-to", action="store_true", help="print the built md5s and accept them (packing the kit)")
    a = ap.parse_args(argv)
    built = {}
    try:
        for name, fn in BUILD.items():
            raw = open(os.path.join(a.finance, name), "rb").read()
            frm, to = PINS[name]
            if md5(raw) != frm:
                raise Stop("%s is %s, not the FROM pin %s -- someone changed it since the brief" % (name, md5(raw), frm))
            if b"\r" in raw:
                raise Stop("%s carries carriage returns" % name)
            new = fn(raw.decode("utf-8")).encode("utf-8")
            if name.endswith(".py"):
                compile(new, name, "exec")
            if md5(new) != to and not a.print_to:
                raise Stop("%s built to %s, not the TO pin %s" % (name, md5(new), to))
            built[name] = new
    except Stop as e:
        print("STOP: %s" % e)
        return 2
    os.makedirs(a.out, exist_ok=True)
    for name, new in built.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(new)
        print("%s  %s -> %s  (%+d lines)" % (name, PINS[name][0][:8], md5(new)[:8] if a.print_to else PINS[name][1][:8],
                                             new.count(b"\n") - open(os.path.join(a.finance, name), "rb").read().count(b"\n")))
        if a.print_to:
            print("   TO %s = %s" % (name, md5(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

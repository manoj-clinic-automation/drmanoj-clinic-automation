#!/usr/bin/env python3
# make_s950.py -- kit S950_WRONG_BILL_FIXES (Sanjeevni session 518, 25-Nov-2026): reproduces the three TO files from the FROM bytes.
#   python make_s950.py <from_dir> <out_dir>      (FROM pins checked first; every anchor must occur exactly once)
import hashlib, os, sys

FROM = {"order_d1053_msg.py": "d652f1538ded88541f704317ae25d224", "order_d1053.py": "056a31cf93036d5b8c928e15070289d3",
        "darpan_kal.html": "13f0810b25c0bce338ac73b602e6ae83"}


def rep(s, old, new, name):
    n = s.count(old)
    if n != 1:
        sys.exit("ANCHOR %s occurs %d times in %s" % (old[:60].replace("\n", "|"), n, name))
    return s.replace(old, new, 1)


# ------------------------------------------------------------------ order_d1053_msg.py v1.1 -> v1.2
M_HEAD_OLD = """#   numbers as reception's screen); a sheet made final by the install counts today's orders as sent.
# ============================================================================="""
M_HEAD_NEW = """#   numbers as reception's screen); a sheet made final by the install counts today's orders as sent.
#
#  v1.2 · kit S950_WRONG_BILL_FIXES · Sanjeevni session 518 · 25-Nov-2026 · the two repairs he asked for at the S509 close ("fresh chat"):
#   F-1657 THE NAME MATCH -> a bill line is on the order when it carries the ordered Marg item (as before), or when every word of an
#                     ordered line's name (this order, or the same dealer's orders of the last 30 days) is in the bill's name --
#                     "UPRISE D3 6L INJ" carries "UPRISE 6L INJ". Three words at least, two of them not a form word (TAB, INJ ...),
#                     the same first word; never when the bill adds a variant word (PLUS, FORTE, XT, D, MR, SR ...), and for an
#                     orthotic never with a size clash -- a doubt stays his line. Only an ordered line the bill's other lines have not
#                     already taken; one of THIS order goes through the quantity check as before. An open line that the rule, judged
#                     again on its whole bill, no longer finds is cleared by the tick (status 'cleared', by S950) and leaves every list.
#   F-1658 WRONG BILLS WAITING -> on his flow page, each open line (dealer · bill no. · medicine) opening /finance/porders/d1053/bill/<scan>;
#                     the same lines on Darpan's tab (darpan_payload 'wrong', drawn by darpan_kal.html).
#   MESSAGES TODAY  -> on his flow page, read only and folded: each message of the flow made today -- time, what, to whom, sent / failed /
#                     waiting -- from order_d1053_msg (no server line is ever needed to see it).
# ============================================================================="""

M_VER_OLD = 'VERSION = "1.1"\nKIT = "S941_ORDER_ADDINS"'
M_VER_NEW = 'VERSION = "1.2"\nKIT = "S950_WRONG_BILL_FIXES"'

M_TOK_OLD = '''def judge_bill(con, oid, scan, stamp=""):'''
M_TOK_NEW = '''# S950 (F-1657): the words of a name -- letters and digits, upper case ("UPRISE-D3 6L INJ." -> UPRISE D3 6L INJ)
def _toks(s):
    import re                                                  # noqa: PLC0415
    return re.findall(r"[A-Z0-9]+", str(s or "").upper())


_FORM = {"TAB", "TABS", "TABLET", "TABLETS", "CAP", "CAPS", "CAPSULE", "INJ", "INJECTION", "SYP", "SYRUP", "SUSP", "GEL", "CREAM", "OINT",
         "OINTMENT", "DROP", "DROPS", "SOL", "LOTION", "SPRAY", "POWDER", "SACHET", "VIAL", "AMP", "KIT", "LIQ", "LIQUID"}
_VARIANT = {"TH4", "TH8", "K27", "K2"}          # variant words with a digit; any added word of letters only (PLUS, FORTE, XT, D, TH ...) refuses too


def _added_refuses(added):
    """S950: a word the bill adds that makes it another medicine -- letters only and not a form word, a strength or size starting with a
    digit (60K, 10ML, 500), or a known variant with a digit. A letter-first digit word (D3) may be added."""
    return any((w.isalpha() and w not in _FORM) or w[:1].isdigit() or w in _VARIANT for w in added)


def token_on_order(con, bill_name, ordered):
    """S950 (F-1657): the ordered item whose every word is in the bill's name, else None -- three words at least and two of them not a
    form word, the same first word, no word of letters or digit-first word added by the bill (a letter-first word like D3 may be added), and an orthotic never
    with a size clash. The first wins."""
    bt = _toks(bill_name)
    if not bt:
        return None
    bs = set(bt)
    ortho = None
    for it in ordered:
        ot = _toks(it)
        os_ = set(ot)
        if len(ot) < 3 or len(os_ - _FORM) < 2 or ot[0] != bt[0] or not os_ <= bs or _added_refuses(bs - os_):
            continue
        try:
            if ortho is None:
                ortho = _ot()._s825_ortho(con)
            if _os()._pa().norm(it) in ortho and _ot().size_clash(it, bill_name, True):
                continue
        except Exception as e:                                 # noqa: BLE001 -- no orthotic test: the words decide
            log("S950 ortho", e)
        return it
    return None


def rejudge_open(con):
    """S950: each open 'not on the order' line's bill is judged again (judge_bill, with the word rule); a line it no longer names is
    cleared (by S950) -- it leaves his page, Darpan's tab and the bill page's buttons. Returns how many were cleared."""
    ensure(con)
    k = 0
    t = _os().now_iso()
    rows = [dict(x) for x in con.execute("SELECT id, item, order_id, scan, stamp, made_at FROM order_d1053_billq WHERE status='open' AND kind='extra'")]
    seen = {}
    for r in rows:
        if not r.get("order_id") or not con.execute("SELECT 1 FROM purchase_order WHERE id=?", (int(r["order_id"]),)).fetchone():
            continue                                           # no order to judge against: stays his line
        key = (int(r["scan"]), int(r["order_id"]))
        if key not in seen:
            reads = _reading(r["scan"])
            if not reads:
                seen[key] = None                               # not read now, or read with no lines: stays his line
            else:
                tie = con.execute("SELECT MIN(tied_at) FROM order_scan_tie WHERE asset_bill_id=? AND order_id=?", (int(r["scan"]), int(r["order_id"]))).fetchone()
                until = (tie[0] if tie and tie[0] else "") or r.get("made_at") or ""
                seen[key] = judge_bill(con, r["order_id"], r["scan"], r.get("stamp") or "", until=until)   # the whole bill, orders up to the tie
        got = seen[key]
        if got is None or any(g[0] == r["item"] for g in got):
            continue                                           # still not on the order: stays his line
        if any(g[1] == "more" for g in got):
            continue                                           # the bill came more than ordered somewhere: every line of it stays his
        con.execute("UPDATE order_d1053_billq SET status='cleared', by='S950', at=? WHERE id=? AND status='open'", (t, r["id"]))
        _os().audit(con, "S950", "d1053_bill_cleared", r["id"], dict(item=r["item"], scan=r["scan"], kit=KIT))
        k += 1
    return k


def judge_bill(con, oid, scan, stamp=""):'''

M_JB_OLD = '''    out = []
    for n, q in reads:
        it = used.get(n)'''
M_JB_NEW = '''    # S950 (F-1657): a bill name that carries every word of an ordered line's name is on the order too -- never 'extra'. Only an
    # ordered line the bill's other lines have not taken; one of THIS order then goes through the quantity check below.
    mine = [l["item"] for l in lines]
    for n, _q in reads:
        if n in used or n in known:
            continue
        taken = set(used.values())
        it = token_on_order(con, n, [x for x in mine if x not in taken])
        if it is not None:
            used[n] = it
            continue
        if token_on_order(con, n, [x for x in other if x not in mine]) is not None:
            known.add(n)

    out = []
    for n, q in reads:
        it = used.get(n)'''

M_H_OLD = '''    OS, D = _os(), _d()
    since = _since(con)
    k = 0
    rows = [dict(r) for r in con.execute("SELECT t.order_id, t.asset_bill_id'''
M_H_NEW = '''    OS, D = _os(), _d()
    since = _since(con)
    k = 0
    try:
        rejudge_open(con)                                      # S950: an open line the word rule now matches leaves the lists
    except Exception as e:                                     # noqa: BLE001 -- judged again next tick
        log("S950 rejudge", e)
    rows = [dict(r) for r in con.execute("SELECT t.order_id, t.asset_bill_id'''

M_OC_OLD = '''        log("owner na", e)
    h.append("</div></div>")
    return "".join(h)'''
M_OC_NEW = '''        log("owner na", e)
    for part in (wrong_bills_html, messages_today_html):      # S950: wrong bills waiting · messages today
        try:
            h.append(part(con))
        except Exception as e:                                 # noqa: BLE001 -- the card as before
            log("S950 " + part.__name__, e)
    h.append("</div></div>")
    return "".join(h)


# ------------------------------------------------------------------ S950: wrong bills waiting · messages today (his page, read only)
def open_wrong(con):
    """The open wrong-bill lines, oldest first."""
    ensure(con)
    return [dict(r) for r in con.execute("SELECT * FROM order_d1053_billq WHERE status='open' ORDER BY made_at, id")]


def _what(r, en):
    if r.get("kind") == "extra":
        return "not on the order" if en else "ऑर्डर में नहीं थी"
    return ("%s %s came, %s ordered" % (r.get("read_qty"), _uw(r.get("unit"), True), r.get("ordered"))) if en else \\
        ("%s %s आए, %s मंगाए" % (r.get("read_qty"), _uw(r.get("unit"), False), r.get("ordered")))


def wrong_bills_html(con):
    """F-1658: each open line on his page, grouped by bill, opening the bill's page (Keep / Send back there). '' when none."""
    rows = open_wrong(con)
    back = con.execute("SELECT COUNT(*) FROM order_d1053_billq WHERE status='back'").fetchone()[0]
    if not rows and not back:
        return ""
    by = {}
    for r in rows:
        by.setdefault(int(r["scan"]), []).append(r)
    h = ['<div id="d950wrong" style="margin-top:8px;background:#fff6e0;border:2px solid #8a5a00;border-radius:12px;padding:8px 12px;font-size:14px">']
    if rows:
        h.append('<div style="font-weight:700;color:#6b4500;font-size:15px">Wrong bills waiting (%d) — open a bill to Keep or Send back</div>' % len(rows))
        for scan, rs in by.items():
            h.append('<div style="padding:4px 0;border-top:1px solid #eadfc6"><a href="/finance/porders/d1053/bill/%d"><b>%s · bill %s</b></a> — %s</div>'
                     % (scan, esc(short(rs[0].get("vendor") or "")), esc(rs[0].get("stamp") or ""),
                        esc(", ".join("%s (%s)" % (r["item"], _what(r, True)) for r in rs))))
    if back:
        h.append('<div style="padding:4px 0;color:#4a5563">%d line%s with reception to send back to the dealer</div>' % (back, "" if back == 1 else "s"))
    h.append("</div>")
    return "".join(h)


_KIND = {"A": "Sheet in", "B": "Final", "C": "WhatsApps gone", "D": "Delivery", "E": "Late", "F1": "Reminder · not final",
         "F1o": "Reminder to you · not final", "F2": "Reminder · not sent", "F2o": "Reminder to you · not sent", "G": "20:00 summary",
         "H": "Wrong bill"}


def _state(r):
    if not r.get("sent_at"):
        return "waiting", "#8a5a00"
    try:
        j = json.loads(r.get("result") or "{}")
    except (TypeError, ValueError):
        j = {}
    s, f = int(j.get("sent") or 0), int(j.get("failed") or 0)
    if s > 0:
        return ("sent" + (" · %d failed" % f if f else "")), "#2f6b45"
    return "not delivered (that phone needs notifications allowed)", "#a3271f"


def messages_today_html(con):
    """Every message of the flow made today -- time, what, to whom, sent / failed / waiting; folded."""
    ensure(con)
    today = _os().today().isoformat()
    rows = [dict(r) for r in con.execute("SELECT kind, to_user, title, body, made_at, sent_at, result FROM order_d1053_msg WHERE substr(made_at,1,10)=? "
                                          "ORDER BY made_at, id", (today,))]
    if not rows:
        return '<div id="d950msgs" style="margin-top:8px;font-size:13px;color:#4a5563">Messages today: none yet</div>'
    st = [_state(r)[0] for r in rows]
    ns = sum(1 for x in st if x.startswith("sent"))
    nw = sum(1 for x in st if x == "waiting")
    nf = len(rows) - ns - nw
    h = ['<details id="d950msgs" style="margin-top:8px;font-size:14px"><summary style="cursor:pointer"><b>Messages today (%d)</b> · sent %d%s%s</summary>'
         % (len(rows), ns, (" · <b style=\\"color:#a3271f\\">not delivered %d</b>" % nf) if nf else "", (" · waiting %d" % nw) if nw else ""),
         '<table style="border-collapse:collapse;margin-top:4px;font-size:13px">']
    for r in rows:
        s, col = _state(r)
        h.append('<tr><td style="padding:3px 10px 3px 0">%s</td><td style="padding:3px 10px 3px 0">%s</td><td style="padding:3px 10px 3px 0">%s</td>'
                 '<td style="padding:3px 0;color:%s">%s</td></tr>'
                 % (esc(_d().hm(r.get("sent_at") or r.get("made_at"))), esc(_KIND.get(r["kind"], r["kind"])), esc(_d().who_name(r["to_user"])), col, esc(s)))
    h.append("</table></details>")
    return "".join(h)


def darpan_wrong(con):
    """S950 (F-1658): the open wrong-bill lines for Darpan's tab -- [dict(item, vendor, stamp, what, url)]."""
    return [dict(item=r["item"], vendor=short(r.get("vendor") or ""), stamp=r.get("stamp") or "", what=_what(r, False),
                 url="/finance/porders/d1053/bill/%d" % int(r["scan"])) for r in open_wrong(con)]'''

M_BP_OLD = '''              "returned": ("Sent back" if en else "वापस गई")}.get(r["status"], "")'''
M_BP_NEW = '''              "returned": ("Sent back" if en else "वापस गई"),
              "cleared": ("On the order — matched by name" if en else "ऑर्डर में थी — नाम से मिली")}.get(r["status"], "")'''

M_SIG_OLD = '''def judge_bill(con, oid, scan, stamp=""):
    """The lines of a scan'''
M_SIG_NEW = '''def judge_bill(con, oid, scan, stamp="", until=None):
    """S950: `until` (an ISO time) keeps the dealer's other orders to those made by then (a later order never excuses an old bill).
    The lines of a scan'''
M_OTH_OLD = '''                                               "AND o.id<>? AND o.created_at>=?", (sn, int(oid), t0))})'''
M_OTH_NEW = '''                                               "AND o.id<>? AND o.created_at>=? AND o.created_at<=?", (sn, int(oid), t0, until or "9999"))})'''

# ------------------------------------------------------------------ order_d1053.py: Darpan's payload carries the open wrong-bill lines
D_OLD = '''                final=(dict(at=hm(fr["at"]), by=("पहले से" if fr["by"] == "install" else who_name(fr["by"]))) if fr else None), cards=lst, sent=sent)'''
D_NEW = '''                final=(dict(at=hm(fr["at"]), by=("पहले से" if fr["by"] == "install" else who_name(fr["by"]))) if fr else None), cards=lst, sent=sent,
                wrong=_s950_wrong(con))


def _s950_wrong(con):
    """S950 (F-1658): the open wrong-bill lines for Darpan's tab (order_d1053_msg beside this file); [] on any fault."""
    try:
        import order_d1053_msg                                 # noqa: PLC0415
        return order_d1053_msg.darpan_wrong(con)
    except Exception as e:                                     # noqa: BLE001
        log("S950 wrong", e)
        return []'''

# ------------------------------------------------------------------ darpan_kal.html: the line on his tab
H_OLD = '''  h+='<div class="d53box" id="d53q">'+s+'</div>';
 }'''
H_NEW = '''  h+='<div class="d53box" id="d53q">'+s+'</div>';
 }
 if(d.wrong&&d.wrong.length) h+='<div class="d53box" id="d950wrong"><div class="d53t">गलत बिल — आपका फ़ैसला ('+d.wrong.length+')</div>'+   /* S950 (F-1658) */
   d.wrong.map(w=>'<a class="d53q" style="display:block;color:inherit;text-decoration:none" href="'+esc(w.url)+'"><div class="d53i">'+esc(w.item)+'</div>'+
    '<div class="muted">'+esc(w.vendor)+' · बिल '+esc(w.stamp)+' · '+esc(w.what)+'</div><div><b>खोलें → रख लो / वापस भेजो</b></div></a>').join("")+'</div>';'''


def main():
    src, out = sys.argv[1], sys.argv[2]
    for n, pin in FROM.items():
        b = open(os.path.join(src, n), "rb").read()
        if hashlib.md5(b).hexdigest() != pin:
            sys.exit("FROM %s is not at its pin %s" % (n, pin[:8]))
    os.makedirs(out, exist_ok=True)
    s = open(os.path.join(src, "order_d1053_msg.py"), encoding="utf-8").read()
    for o, n in ((M_HEAD_OLD, M_HEAD_NEW), (M_VER_OLD, M_VER_NEW), (M_TOK_OLD, M_TOK_NEW), (M_JB_OLD, M_JB_NEW), (M_H_OLD, M_H_NEW),
                 (M_OC_OLD, M_OC_NEW), (M_BP_OLD, M_BP_NEW), (M_SIG_OLD, M_SIG_NEW), (M_OTH_OLD, M_OTH_NEW)):
        s = rep(s, o, n, "order_d1053_msg.py")
    open(os.path.join(out, "order_d1053_msg.py"), "w", encoding="utf-8", newline="\n").write(s)
    s = open(os.path.join(src, "order_d1053.py"), encoding="utf-8").read()
    s = rep(s, D_OLD, D_NEW, "order_d1053.py")
    open(os.path.join(out, "order_d1053.py"), "w", encoding="utf-8", newline="\n").write(s)
    s = open(os.path.join(src, "darpan_kal.html"), encoding="utf-8").read()
    s = rep(s, H_OLD, H_NEW, "darpan_kal.html")
    open(os.path.join(out, "darpan_kal.html"), "w", encoding="utf-8", newline="\n").write(s)
    for n in FROM:
        print(hashlib.md5(open(os.path.join(out, n), "rb").read()).hexdigest() + "  finance/" + n)


if __name__ == "__main__":
    main()

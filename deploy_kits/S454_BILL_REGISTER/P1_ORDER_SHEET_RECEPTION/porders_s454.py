#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  porders_s454.py  ·  v1.0  ·  kit S454_BILL_REGISTER (part 1)  ·  Session 283 (Sanjeevni)  ·  D666 / D668 / D669 / D640 / D643 / D648
#
#  THE RECEPTION SCREEN, ONE TASK AT A TIME (/finance/porders). The owner, 03-Oct-2026: "They should only see what they need to do ...
#  in very simple terms." Two habits: send the order, and scan the bill when goods come. Everything else is done by the system or is
#  optional. Server-rendered pages (phone width first, buttons 44 px and more), Roman Hindi for the staff, English for the owner; the
#  words, the order and the buttons are the S454 mock's (claude_code_briefs/S454_BILL_REGISTER_MOCK.html, screens 1-15).
#
#    GET  /finance/porders                            Aaj ka kaam (porders.page hands over while porders.simple = 1; ?old=1 = today's page)
#    GET  /finance/porders/s454/order                 Order karna hai -- a card per supplier, Sab ko WhatsApp bhejo, Order sheet print karo
#    GET  /finance/porders/s454/order/<supplier>      one supplier: the medicines, Call karo (tel:, the number under it), Order ho gaya,
#                                                     Quantity badalni hai?, its old pending block (Dobara order karo)
#    GET  /finance/porders/s454/old                   Purane pending -- all of them, by supplier
#    GET  /finance/porders/s454/sheet.pdf             the printed order sheet (order_sheet_pdf)
#    GET  /finance/porders/s454/maal                  Maal aaya? -- a card per order awaited: Bill scan karo · Bill nahi hai, ya kam aaya?
#    GET  /finance/porders/s454/maal/<order>          the arrival screen (not a required step); then "Bill abhi scan karna hai?"
#    GET  /finance/porders/s454/scan[?month=]         Bill scan karna hai -- by supplier, five at a time; Koi paper nahi mil raha?
#    GET  /finance/porders/s454/q[?month=]            Photo dekh kar bataiye -- one question on the screen
#    GET  /finance/porders/s454/purana/<yyyy-mm>      a parked month: optional, the same two rows for that month only
#    POST /finance/porders/api/s454/<action>          ordered · whatsapp · call · qty · reorder · arrive · later · pharmacy · vendor ·
#                                                     confirm · amount · paper_missing · setting (owner)
#    GET  /finance/porders/api/s454/state             the counts (the walk and the duty map read them)
#  The owner's cards (who decides, the agreement line, the old pending orders, the sheet's state) and the settings card sit on the old
#  page (?old=1), for the owner only. No phone number is written anywhere but on a sender's own call screen and the reception phone's message.
# =============================================================================
import datetime as dt
import html as _html
import json
import os
import re
import sqlite3
import sys
from urllib.parse import quote, urlencode

from flask import Blueprint, jsonify, redirect, request

import order_sheet as OS

VERSION = "1.0"
KIT = "S454_BILL_REGISTER"
bp = Blueprint("porders_s454", __name__)
HERE = os.path.dirname(os.path.abspath(__file__))
P = "/finance/porders"
QKINDS = ("bill", "amount", "vendor", "pharmacy", "s441")
PURANA_USERS = ("manoj", "shavez")


def init(app):
    app.register_blueprint(bp)
    return bp


def _po():
    import porders                                            # noqa: PLC0415 -- the screen's own module, mounted first
    return porders


def _pa():
    return OS._pa()


def esc(s):
    return _html.escape("" if s is None else str(s), quote=True)


# ------------------------------------------------------------------ words (staff Roman Hindi | owner English)
T = {
    "home": ("Aaj ka kaam", "Today's work"), "scan_new": ("Naya bill scan karo", "Scan a new bill"),
    "r_order": ("Order karna hai", "To order"), "r_maal": ("Maal aaya?", "Goods arrived?"), "r_scan": ("Bill scan karna hai", "Bills to scan"),
    "r_q": ("Photo dekh kar bataiye", "Look at the photo and answer"),
    "done": ("Sab kaam ho gaya", "All work is done"), "done2": ("Naya bill aate hi yahan dikhega.", "A new bill shows here as soon as it comes."),
    "purana": ("Purana kaam: %s", "Earlier work: %s"), "oldpage": ("Purana page", "Old page"), "signed": ("Signed in: %s", "Signed in: %s"),
    "po": ("Purchase orders", "Purchase orders"),
    "whose": ("%s ka order · %s · %d supplier, %d dawa", "%s's order · %s · %d suppliers, %d medicines"),
    "darpan": ("Darpan", "Darpan"), "system": ("System", "The system"),
    "wa_all": ("Sab ko WhatsApp bhejo", "WhatsApp all"), "print": ("Order sheet print karo", "Print the order sheet"),
    "callnote": ("Call se order kiya? Us supplier par “Order ho gaya” dabaiye.", "Ordered by phone? Tap “Order done” on that supplier."),
    "open": ("Kholiye", "Open"), "ordered": ("Order ho gaya", "Order done"), "dawa": ("%d dawa", "%d medicines"),
    "called": ("call kiya tha, order baaki", "called, not yet ordered"), "inline": ("WhatsApp line mein hai", "WhatsApp is in the line"),
    "wa_no": ("WhatsApp nahi gaya — call kijiye", "WhatsApp did not go — please call"), "nophone": ("phone number yahan nahi hai", "no phone number here"),
    "more": ("Baaki %d supplier dikhaiye", "Show the other %d suppliers"), "more2": ("Baaki %d dikhaiye", "Show the other %d"),
    "oldlink": ("Purane pending: %d", "Old pending: %d"),
    "wa_went": ("WhatsApp chala gaya: %d supplier", "WhatsApp went: %d suppliers"), "wa_who": ("%s · %s · %s ne bheja", "%s · %s · sent by %s"),
    "still": ("Abhi baaki: %d", "Still to order: %d"), "doneN": ("Ho chuke: %d. Chahein to call bhi kar sakte hain.", "Done: %d. You may call as well."),
    "wa_gaya": ("WhatsApp gaya", "WhatsApp went"), "wa_call": ("WhatsApp + call ho gaya", "WhatsApp + call done"), "call_done": ("Call se order ho gaya", "Ordered by call"),
    "scan_done": ("Bill scan se order ho gaya", "Ordered by the bill's scan"), "call": ("Call", "Call"),
    "wa_off": ("Reception phone set nahi hai — call se order kijiye", "The reception phone is not set up — order by call"),
    "inline_n": ("WhatsApp line mein: %d", "In the WhatsApp line: %d"),
    "order": ("Order", "Order"), "likhwaiye": ("Phone par yeh order likhwaiye:", "Give this order on the phone:"),
    "callkaro": ("Call karo", "Call"), "baat": ("Baat ho gayi? Tab yeh dabaiye. Phone nahi laga to BACK, order yahin baaki rahega.",
                                             "Spoke to them? Then tap this. If the call did not go through, BACK — the order stays here."),
    "nophone_l": ("Is supplier ka phone number yahan nahi hai", "This supplier has no phone number here"),
    "qtychange": ("Quantity badalni hai?", "Change a quantity?"), "remove": ("hatao", "remove"),
    "oldblk": ("Purane pending — dobara order tabhi, jab zaroorat ho", "Old pending — order again only when needed"),
    "orderdate": ("Order %s · ", "Ordered %s · "), "reorder": ("Dobara order karo", "Order again"),
    "oldall": ("Purane pending", "Old pending"), "onlyold": ("Sirf purane pending", "Only old pending"),
    "maal_top": ("Maal aaya? Bill scan kijiye, bas. Maal apne aap darj ho jayega.", "Goods arrived? Just scan the bill. The goods are recorded by themselves."),
    "orderN": ("Order %s · %d dawa", "Order %s · %d medicines"), "billscan": ("Bill scan karo", "Scan the bill"),
    "nobill": ("Bill nahi hai, ya kam aaya?", "No bill, or something came short?"),
    "tapshort": ("Jo kam aaya ya nahi mila, us par tap kijiye.", "Tap what came short or did not come."),
    "kam": ("Kam aaya", "Came short"), "nahimila": ("Nahi mila", "Did not come"), "aagaya": ("Aa gaya", "Arrived"),
    "kitna": ("Kitna aaya?", "How many came?"), "maal_ok": ("Maal aa gaya", "Goods arrived"), "abhinahi": ("Abhi nahi aaya", "Not yet arrived"),
    "darj": ("Maal darj ho gaya", "Goods recorded"), "abhiscan": ("Bill abhi scan karna hai?", "Scan the bill now?"), "baadmein": ("Baad mein", "Later"),
    "baadnote": ("Baad mein karenge to yeh “Bill scan karna hai” mein milega.", "If later, it will be under “Bills to scan”."),
    "scan_top": ("In bill ka paper nikaaliye aur scan kijiye.", "Take out the paper of these bills and scan it."),
    "nbill": ("%s · %d bill", "%s · %d bills"), "kamaal": ("%s ka maal", "goods of %s"), "billno": ("Bill %s", "Bill %s"),
    "k_recv": ("Maal aa gaya, bill scan baaki", "Goods arrived, bill scan due"), "k_marg": ("Marg mein hai, scan nahi", "In Marg, not scanned"),
    "scankaro": ("Scan karo", "Scan"), "agle": ("Agle 5 dikhaiye", "Show the next 5"), "nopaper": ("Koi paper nahi mil raha?", "A paper cannot be found?"),
    "papernotfound": ("Paper nahi mila", "Paper not found"), "tickpaper": ("Jis bill ka paper nahi mil raha, us par tick kijiye.", "Tick each bill whose paper cannot be found."),
    "sawaal": ("Sawaal %d / %d", "Question %d / %d"), "photo": ("Bill ki photo", "The bill's photo"), "kagaz": ("Kagaz ki photo", "The paper's photo"),
    "badi": ("Badi karne ke liye tap kijiye", "Tap to enlarge"),
    "q_bill": ("Kya yeh %s ka bill %s hai?", "Is this %s's bill %s?"), "q_dup": ("Kya yeh %s ke bill %s ka doosra scan hai?", "Is this a second scan of %s's bill %s?"),
    "haan": ("Haan", "Yes"), "nahi": ("Nahi", "No"), "q_amount": ("Bill par total amount kya likha hai?", "What total amount is written on the bill?"),
    "koiaur_amt": ("Koi aur amount", "Another amount"), "q_vendor": ("Yeh bill kis supplier ka hai?", "Whose bill is this?"),
    "koiaur": ("Koi aur", "Someone else"), "pick": ("— supplier chuniye —", "— choose the supplier —"), "notlisted": ("List mein nahi hai", "Not on the list"),
    "q_ph": ("Kya yeh dawa (pharmacy) ka bill hai?", "Is this a medicine (pharmacy) bill?"), "ph_yes": ("Haan, pharmacy ka bill", "Yes, a pharmacy bill"),
    "ph_no": ("Nahi, pharmacy ka nahi", "No, not pharmacy"), "q_twin": ("Kya yeh dono ek hi kaagaz hain?", "Are these two the same paper?"),
    "same": ("Haan, wahi kaagaz", "Yes, the same paper"), "diff": ("Nahi, alag bill", "No, a different bill"),
    "q_lane": ("Yeh supplier pharmacy (Marg) ka lagta hai — clinic lane mein scan hua", "This supplier looks like a pharmacy (Marg) one — scanned in the clinic lane"),
    "tophar": ("Haan, pharmacy ka hai", "Yes, it is pharmacy"), "stay": ("Nahi, clinic ka hi", "No, it is clinic"),
    "scan_of": ("scan %s", "scan %s"), "go": ("Theek hai", "OK"),
    "park_top": ("Yeh zaroori nahi hai. Jab samay ho, tab kijiye.", "This is optional. Do it when there is time."),
    "frozen": ("Medicine ordering band hai", "Medicine ordering is frozen"),
    "who_first": ("Pehle apna naam chuniye (Kaun kaam kar raha hai?).", "Choose your name first."),
    "saved": ("Ho gaya", "Done"), "err": ("Nahi hua", "Not done"),
    "back": ("← BACK", "← BACK"),
}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def L(en, k, *a):
    s = T[k][1 if en else 0]
    return (s % a) if a else s


def month_name(ym):
    try:
        return MONTHS[int(ym[5:7]) - 1]
    except (ValueError, IndexError):
        return ym


# ------------------------------------------------------------------ the page frame (the mock's colours and sizes)
CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f6f4f1;color:#1c1c1c;font:16px/1.45 system-ui,sans-serif}
.wrap{max-width:480px;margin:0 auto;padding:0 12px 28px;display:flex;flex-direction:column;gap:12px}
.bar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:10px;background:#1f3864;color:#fff;margin:0 -12px;padding:6px 10px}
.bar a.bk{display:flex;align-items:center;justify-content:center;min-height:44px;width:150px;background:#fff;color:#1f3864;border-radius:9px;font-size:18px;font-weight:800;text-decoration:none}
.bar .tt{font-weight:600}
h1{margin:4px 0 0;font-size:22px}
.mut{font-size:15px;color:#5b5b5b}
.sig{font-size:14px;color:#5b5b5b}
a.big,button.big{display:flex;align-items:center;justify-content:center;gap:10px;min-height:60px;width:100%;background:#2e6b34;border:1px solid #2e6b34;border-radius:12px;padding:12px;color:#fff;font:700 20px system-ui,sans-serif;text-align:center;text-decoration:none;cursor:pointer}
a.big.out,button.big.out{background:#fff;color:#1f3864;border-color:#1f3864}
a.big.blue,button.big.blue{background:#1f3864;border-color:#1f3864}
button.big[disabled]{background:#b8b8b8;border-color:#b8b8b8;color:#fff;cursor:default}
a.row{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:14px 16px;color:#1c1c1c;text-decoration:none;min-height:60px}
a.row .n{flex:0 0 52px;height:52px;border-radius:26px;background:#1f3864;color:#fff;display:flex;align-items:center;justify-content:center;font-size:21px;font-weight:800}
a.row .l{flex:1 1 auto;font-size:19px;font-weight:700}
.card{background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:8px}
.card .nm{font-size:17px;font-weight:700}
.card .sb{font-size:14.5px;color:#5b5b5b}
.card .sb.am{color:#8a5300;font-weight:600}
.two{display:flex;gap:8px}
.two>*{flex:1 1 0;display:flex;align-items:center;justify-content:center;min-height:48px;border-radius:10px;padding:8px;font:700 16px system-ui,sans-serif;text-decoration:none;cursor:pointer}
.b{background:#fff;color:#1f3864;border:1px solid #1f3864}
.g{background:#2e6b34;color:#fff;border:1px solid #2e6b34}
.ok{background:#e4f2e6;border:2px solid #2e6b34;border-radius:12px;padding:14px 16px}
.ok .t{font-size:19px;font-weight:800;color:#1f4d25}
.err{background:#fbe7e5;border:2px solid #b3261e;border-radius:12px;padding:12px 14px;color:#8c1d18;font-weight:700}
.lnk{text-align:center}
.lnk a,.lnk button{display:inline-block;min-height:44px;padding:10px 8px;color:#5b5b5b;font:15px system-ui,sans-serif;text-decoration:underline;background:none;border:0;cursor:pointer}
.more{display:block;min-height:52px;border:1px solid #1f3864;border-radius:10px;padding:12px;background:#fff;color:#1f3864;font-weight:700;font-size:17px;text-align:center;text-decoration:none}
.list{background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:4px 14px;display:flex;flex-direction:column}
.li{display:flex;align-items:baseline;gap:10px;padding:11px 0;border-top:1px solid #eee}
.li:first-child{border-top:0}
.li .i{flex:1 1 auto;font-size:18px;font-weight:600}
.li .q{font-size:18px;font-weight:800;white-space:nowrap}
.num{text-align:center;font-size:17px;font-weight:600;padding-top:6px;letter-spacing:.04em}
.oldb{background:#fdf1dc;border:2px solid #8a5300;border-radius:12px;padding:10px 14px}
.oldb .h{font-size:15.5px;font-weight:800;color:#5c3700}
.ol{padding:10px 0;border-top:1px solid #f0d9b0;display:flex;flex-direction:column;gap:6px}
.ol:first-of-type{border-top:0}
.ol .r1{display:flex;align-items:baseline;gap:10px}.ol .r1 .i{flex:1 1 auto;font-size:17px;font-weight:600}.ol .r1 .q{font-size:16px;font-weight:700}
.ol .r2{display:flex;align-items:center;gap:10px}.ol .r2 .w{flex:1 1 auto;font-size:14.5px}
.red{color:#8c1d18;font-weight:700}.grn{color:#1f4d25;font-weight:700}
.sm{border:1px solid #1f3864;border-radius:9px;padding:8px 10px;color:#1f3864;background:#fff;font:600 14.5px system-ui,sans-serif;min-height:44px;cursor:pointer;white-space:nowrap}
.qbox{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.qbox b{min-width:34px;text-align:center;font-size:20px}
.pm{min-width:48px;min-height:44px;font-size:20px;border:1px solid #bbb;border-radius:9px;background:#fafafa;cursor:pointer}
.ar{display:flex;align-items:center;gap:10px;min-height:52px;padding:8px 0;border-top:1px solid #eee;cursor:pointer}
.ar:first-child{border-top:0}.ar .i{flex:1 1 auto;font-size:18px;font-weight:600}.ar .q{font-size:17px;font-weight:700;white-space:nowrap}
.chips{display:flex;gap:8px;flex-wrap:wrap}.chips button{min-height:44px;border:1px solid #bbb;border-radius:9px;padding:9px 12px;background:#fafafa;font:600 16px system-ui,sans-serif;cursor:pointer}
.chips button.on{border-color:#8a5300;background:#fdf1dc;color:#5c3700}
input.amt,input.kq{min-height:44px;font-size:18px;border:1px solid #999;border-radius:9px;padding:9px 10px;width:110px}
select.kv{min-height:44px;font-size:16px;padding:8px;max-width:100%;width:100%}
.prog{height:6px;background:#e4e0da;border-radius:3px;overflow:hidden}.prog i{display:block;height:6px;background:#1f3864}
.pic{display:block;background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:8px;text-align:center;text-decoration:none;color:#5b5b5b}
.pic img{max-width:100%;max-height:360px;border-radius:6px}
.grp{font-size:17px;font-weight:800;margin-top:4px}
.ln{background:#fff;border:1px solid #e4e0da;border-radius:12px;padding:12px 14px;display:flex;align-items:center;gap:10px}
.ln .t{flex:1 1 auto;min-width:0}.ln .t .a{font-size:17px;font-weight:700}.ln .t .s{font-size:14.5px;color:#5b5b5b}
.ln a.sk{display:inline-flex;align-items:center;justify-content:center;min-height:48px;border-radius:10px;padding:10px 14px;background:#2e6b34;color:#fff;font-weight:700;text-decoration:none;white-space:nowrap}
label.tk{display:flex;align-items:center;gap:12px;min-height:48px}label.tk input{width:24px;height:24px}
"""
JS = """
async function s454(url, body, then){
 try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
  const j=await r.json().catch(()=>({}));
  if(!r.ok||!j.ok){const m=document.getElementById('msg');if(m){m.className='err';m.textContent=j.message||j.error||('HTTP '+r.status);m.style.display='block';window.scrollTo(0,0);}return null;}
  if(typeof then==='string'){location.href=then;}else if(typeof then==='function'){then(j);}else{location.reload();}
  return j;}catch(e){const m=document.getElementById('msg');if(m){m.className='err';m.textContent=String(e);m.style.display='block';}return null;}
}
"""


def shell(con, u, title, body, back="/portal", login=""):
    page = ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s</title><style>%s</style><script>%s</script></head><body><div class="wrap">'
            '<div class="bar"><a class="bk" href="%s">← BACK</a><span class="tt">%s</span></div>'
            '<div id="msg" class="err" style="display:none"></div>%s</div></body></html>'
            % ("en" if u.get("_en") else "hi", esc(title), CSS, JS, esc(back), esc(title), body))
    try:
        S441 = _po().S441
        if S441 is not None and S441.is_shared_login(login):
            page = page.replace("</body>", S441.who_script(login) + "</body>", 1)
    except Exception:                                         # noqa: BLE001
        pass
    return page, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


def _auth_page():
    """(u, con, kind, login, err) for a page: a viewer keeps the old page."""
    po = _po()
    u, con, kind, err = po._auth()
    if err:
        return None, None, None, "", err
    login = str(u.get("login") or u.get("user") or "").lower()
    if kind not in ("owner", "sender"):
        return None, None, None, login, redirect(P + "?old=1")
    u = dict(u, _en=(kind == "owner"))
    OS.ensure(con)
    return u, con, kind, login, None


def _auth_api(order=False):
    """(u, con, kind, err) for a POST; order=True: an ordering route, refused while medicine ordering is frozen (S410's freeze)."""
    po = _po()
    u, con, kind, err = po._auth()
    if err:
        return None, None, None, err
    if kind not in ("owner", "sender"):
        return None, None, None, (jsonify(ok=False, error="view_only", message="Aap sirf dekh sakte hain."), 403)
    OS.ensure(con)
    if order:
        import order_rules                                    # noqa: PLC0415
        fr = order_rules._frozen(con)
        if fr:
            return None, None, None, (jsonify(ok=False, error="frozen", message="Medicine ordering band hai: %s" % (fr.get("reason") or "")), 423)
    return u, con, kind, None


def who(u):
    return str(u.get("user") or "")


def _safe_from():
    f = str(request.args.get("from") or "")
    return f if (f.startswith("/") and not f.startswith("//") and len(f) < 300 and not re.search(r"[\\\r\n\"'<>]", f)) else "/portal"


def intake(vendor="", bill_no=None, bill_date=None, amount_p=None, back=P):
    q = dict(lane="pharmacy")
    if vendor:
        q["vendor"] = str(vendor)[:120]
    if bill_no:
        q["bill_no"] = str(bill_no)[:40]
    if bill_date:
        q["bill_date"] = str(bill_date)[:10]
    if amount_p:
        q["amount"] = "%.2f" % (int(amount_p) / 100.0)
    q["from"] = back
    return "/scanapp/intake?" + urlencode(q)


def rs(p):
    try:
        return _po()._s440_rs(p)
    except Exception:                                         # noqa: BLE001
        return "₹%d" % (int(p or 0) // 100)


# ------------------------------------------------------------------ months: counted, parked
def counted_from(con):
    v = OS.setting(con, "purchase.register_from")
    return v[:7] if re.match(r"^\d{4}-\d\d", v) else "2026-10"


def parked(con):
    return [m.strip() for m in OS.setting(con, "purchase.parked_months").split(",") if re.match(r"^\d{4}-\d\d$", m.strip())]


def month_class(con, ym):
    """counted | parked | hidden"""
    if not ym:
        return "counted"
    if ym >= counted_from(con):
        return "counted"
    return "parked" if ym in parked(con) else "hidden"


# ------------------------------------------------------------------ the work: maal aaya, bills to scan, questions
def maal_orders(con):
    """Orders made and not yet received: status sent, no bill scan tied."""
    tied = OS.ties(con)
    out = []
    for o in con.execute("SELECT * FROM purchase_order WHERE status='sent' ORDER BY created_at, id"):
        o = dict(o)
        if o["id"] in tied:
            continue
        o["n"] = con.execute("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=?", (o["id"],)).fetchone()[0]
        out.append(o)
    return out


def scan_lines(con, cls_want="counted", month=None):
    """'Bill scan karna hai': orders received with no bill scan (still asking), and Marg bills with no scan and no likely scan -- of the
    month class wanted ('counted', or 'parked' with a month). Paper-not-found bills are gone from it."""
    pa = _pa()
    out = []
    asking = OS.awaiting_scan(con)
    for sn, orders in asking.items():
        for o in orders:
            if o["status"] != "received":
                continue
            ym = str(o["received_at"] or o["created_at"])[:7]
            if not _want(con, ym, cls_want, month):
                continue
            out.append(dict(kind="recv", vendor=o["vendor"], sn=sn, order_id=o["id"], date=str(o["created_at"])[:10], ym=ym, sort=str(o["created_at"])[:10],
                            intake=intake(o["vendor"], back=P + "/s454/scan" + ("?month=" + month if month else ""))))
    try:
        work = _po().scan_work(con)
    except Exception:                                         # noqa: BLE001
        work = dict(scan=[])
    missing = {r[0] for r in con.execute("SELECT bill_id FROM s454_paper_missing")}
    for b in work.get("scan") or []:
        if b["bill_id"] in missing:
            continue
        ym = str(b.get("month") or b.get("bill_date") or "")[:7]
        if not _want(con, ym, cls_want, month):
            continue
        out.append(dict(kind="marg", vendor=b["vendor"], sn=b.get("vendor_norm") or pa.supplier_key(b["vendor"]), bill_id=b["bill_id"], bill_no=b["bill_no"],
                        date=b["bill_date"], amount_p=b["amount_p"], ym=ym, sort=b["bill_date"],
                        intake=intake(b["vendor"], b["bill_no"], b["bill_date"], b["amount_p"], back=P + "/s454/scan" + ("?month=" + month if month else ""))))
    out.sort(key=lambda x: (x["sort"], x["vendor"]))
    return out


def _want(con, ym, cls_want, month):
    c = month_class(con, ym)
    if cls_want == "counted":
        return c == "counted"
    return c == "parked" and (month is None or ym == month)


def _scan_meta(ids):
    """{scan id: dict(month, at, stamp, vendor, bill_no, amount_p, bill_date)} -- the asset app's rows (READ ONLY)."""
    if not ids:
        return {}
    acon = OS._assets()
    if acon is None:
        return {}
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "total_amount", "submitted_at", "created_at", "bill_month", "ocr_status",
                           "lane", "kind", "status", "dup_of") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE id IN (%s)" % (", ".join(sel), ",".join("?" * len(ids))), list(ids))]
    finally:
        acon.close()
    out = {}
    for r in rows:
        at = OS.scan_moment(r)
        r["at"] = at
        bm = str(r.get("bill_month") or "")
        r["month"] = bm if re.match(r"^\d{4}-\d\d$", bm) else (str(r.get("bill_date") or "")[:7] if re.match(r"^\d{4}-\d\d", str(r.get("bill_date") or "")) else
                                                             (at.strftime("%Y-%m") if at else ""))
        out[int(r["id"])] = r
    return out


def questions(con, cls_want="counted", month=None):
    """The queue of 'Photo dekh kar bataiye', oldest scan first ('Baad mein' sends a card to the end). Each: dict(kind, scan, ...)."""
    pa = _pa()
    po = _po()
    try:
        work = po.scan_work(con)
    except Exception:                                         # noqa: BLE001
        work = dict(confirm=[], amount=[], vendor=[], twin=[], suppliers=[])
    ans = OS.answers(con)
    qs = []
    for x in work.get("confirm") or []:
        qs.append(dict(kind="bill", scan=x["scan"], bill=x["bill_id"], vendor=x["vendor"], bill_no=x["bill_no"], date_text=x["date_text"], amount=x["amount"],
                       taken=bool(x.get("taken_by")), ym=None, bill_month=None, thumb=x["thumb"], pdf=x["pdf"], stamp=x["stamp"]))
    for x in work.get("amount") or []:
        if (ans.get(x["scan"]) or {}).get("amount"):
            continue                                          # a parked month's answer is on the register only; asked once
        qs.append(dict(kind="amount", scan=x["scan"], bill=x["bill_id"], vendor=x["vendor"], bill_no=x["bill_no"], date_text=x["date_text"],
                       marg_p=x["amount_p"], scan_p=x.get("scan_amount_p"), thumb=x["thumb"], pdf=x["pdf"], stamp=x["stamp"]))
    for x in work.get("vendor") or []:
        qs.append(dict(kind="vendor", scan=x["scan"], read=x.get("scan_vendor") or "", thumb=x["thumb"], pdf=x["pdf"], stamp=x["stamp"], s440=True))
    for x in work.get("twin") or []:
        qs.append(dict(kind="s441", scan=x["scan"], q=x["q"], qkind=x["kind"], cand=x.get("cand"), stamp=x["stamp"], thumb=x["thumb"], pdf=x["pdf"],
                       read="%s · %s · %s" % (x.get("scan_vendor") or "—", x.get("scan_no") or "—", x.get("scan_amount") or "—")))
    # S454 4.7: a paper with no bill number and no amount (or headed Estimate / Challan / Quotation) -- is it a pharmacy bill?
    scans = OS.pharmacy_scans(days=120) or []
    linked = set()
    try:
        linked = {r[0] for r in con.execute("SELECT asset_bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        pass
    tied = {v["scan"] for v in OS.ties(con).values()}
    sup_of = OS._resolver(con)
    seen = {q["scan"] for q in qs}
    bills = None
    for s in scans:
        sid = int(s["id"])
        if sid in linked or sid in seen or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or not OS.unread(s):
            continue
        a = ans.get(sid) or {}
        ph = (a.get("pharmacy") or {}).get("answer")
        pic = dict(thumb="/scanapp/bills/%d/thumb" % sid, pdf="/scanapp/bills/%d/file" % sid, stamp=s.get("stamp_no") or "#%d" % sid)
        if not ph:
            qs.append(dict(kind="pharmacy", scan=sid, read=s.get("vendor") or "", at=s["at"], **pic))
            continue
        if ph != "yes":
            continue
        sn = sup_of(s)
        if not sn:
            qs.append(dict(kind="vendor", scan=sid, read=s.get("vendor") or "", s440=False, **pic))
            continue
        if sid in tied or (a.get("pair") or {}).get("answer") == "no":
            continue
        if bills is None:
            bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL +
                                                  " AND NOT EXISTS (SELECT 1 FROM purchase_scan_link k WHERE k.bill_id=b.id)")]
        day = s["at"].date() if s.get("at") else None
        win = OS.int_setting(con, "purchase.unread_pair_days")
        near = [b for b in bills if b["supplier_norm"] == sn and day and OS._date(b["bill_date"]) and abs((OS._date(b["bill_date"]) - day).days) <= win]
        if len(near) == 1:
            b = near[0]
            qs.append(dict(kind="bill", scan=sid, bill=b["id"], vendor=pa.supplier_key(b["supplier"]), bill_no=str(b["bill_no"]), date_text=OS.dmy(b["bill_date"]),
                           amount=rs(b["amount_p"]), taken=False, unread=True, **pic))
    meta = _scan_meta({q["scan"] for q in qs})
    later = {(r[0], r[1]): r[2] for r in con.execute("SELECT asset_bill_id, kind, at FROM s454_later")}
    out = []
    for q in qs:
        m = meta.get(q["scan"]) or {}
        ym = None
        if q.get("bill"):
            r = con.execute("SELECT month, bill_date FROM purchase_bill WHERE id=?", (q["bill"],)).fetchone()
            ym = (r[0] or str(r[1] or "")[:7]) if r else None
        ym = ym or m.get("month") or ""
        if not _want(con, ym, cls_want, month):
            continue
        q["ym"] = ym
        q["later"] = later.get((q["scan"], q["kind"]), "")
        q["sat"] = m.get("at").isoformat() if m.get("at") else ""
        q["scan_day"] = OS.ddmm(q["sat"]) if q["sat"] else ""
        out.append(q)
    out.sort(key=lambda q: (1 if q["later"] else 0, q["later"], q["scan"]))
    return out


def counts(con, month=None):
    """The home's four rows (counted months) -- or, with a parked month, its two."""
    if month:
        return dict(scan=len(scan_lines(con, "parked", month)), q=len(questions(con, "parked", month)))
    import order_rules                                        # noqa: PLC0415
    es = OS.entries(con)
    return dict(order=(0 if order_rules._frozen(con) else len([e for e in es if e["state"] != "in_line"])), maal=len(maal_orders(con)),
                scan=len(scan_lines(con)), q=len(questions(con)))


def parked_with_work(con):
    out = []
    for m in parked(con):
        c = counts(con, m)
        if c["scan"] or c["q"]:
            out.append((m, c))
    return out


def _every_read(con):
    """Every page read: the sheets the door took, the WhatsApp line, Marg's clearing, the tie (fail-soft each)."""
    try:
        OS.cron_pass(con, "page")
    except Exception:                                         # noqa: BLE001
        pass


# ------------------------------------------------------------------ the home (screens 1, 14)
def home():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    c = counts(con)
    nm = ""
    try:
        S441 = _po().S441
        if S441 is not None and S441.is_shared_login(login):
            nm = S441.who_name(request.cookies) or ""
    except Exception:                                         # noqa: BLE001
        pass
    h = ['<div class="sig">%s</div>' % esc(L(en, "signed", login + ((" · " + nm) if nm else ""))), "<h1>%s</h1>" % L(en, "home"),
         '<a class="big" id="scannew" href="%s">📷 %s</a>' % (esc(intake(back=P)), L(en, "scan_new"))]
    rows = (("order", P + "/s454/order", "r_order"), ("maal", P + "/s454/maal", "r_maal"), ("scan", P + "/s454/scan", "r_scan"), ("q", P + "/s454/q", "r_q"))
    any_ = False
    for k, href, lab in rows:
        if c[k] > 0:
            any_ = True
            h.append('<a class="row" id="row_%s" href="%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (k, href, c[k], L(en, lab)))
    if not any_:
        h.append('<div class="ok" id="alldone"><div class="t">%s</div><div>%s</div></div>' % (L(en, "done"), L(en, "done2")))
    for m, _c in parked_with_work(con):
        h.append('<div class="lnk"><a id="park_%s" href="%s/s454/purana/%s">%s</a></div>' % (m, P, m, L(en, "purana", month_name(m))))
    if kind == "owner" or str(login) in PURANA_USERS or str(u.get("user") or "").lower() in PURANA_USERS:
        h.append('<div class="lnk"><a id="oldpage" href="%s?old=1">%s</a></div>' % (P, L(en, "oldpage")))
    return shell(con, u, L(en, "po"), "".join(h), back=_safe_from(), login=login)


# ------------------------------------------------------------------ Order karna hai (screens 2, 3)
def _card(en, e, sent=False):
    sub = L(en, "dawa", len(e["lines"]))
    am = False
    if e["state"] == "withdrawn":
        sub, am = sub + " · " + L(en, "wa_no"), True
    elif e["state"] == "in_line":
        sub, am = sub + " · " + L(en, "inline"), True
    elif not e["has_phone"]:
        sub, am = sub + " · " + L(en, "nophone"), True
    elif e.get("called"):
        sub, am = sub + " · " + L(en, "called"), True
    q = quote(e["sn"], safe="")
    btn = ('<button class="g" onclick="s454(\'%s/api/s454/ordered\',{sn:%s})">%s</button>' % (P, esc(json.dumps(e["sn"])), L(en, "ordered")))
    return ('<div class="card" data-sn="%s"><div><div class="nm">%s</div><div class="sb%s">%s</div></div><div class="two"><a class="b" href="%s/s454/order/%s">%s</a>%s</div></div>'
            % (esc(e["sn"]), esc(e["vendor"]), " am" if am else "", esc(sub), P, q, L(en, "open"), btn))


def order_list():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return shell(con, u, L(en, "r_order"), '<div class="err">%s</div>' % L(en, "frozen"), back=P, login=login)
    es = OS.entries(con)
    pend = [e for e in es if e["state"] != "in_line"]
    line = [e for e in es if e["state"] == "in_line"]
    src = OS.source(con)
    h = []
    ns = OS.newest_sheet(con)
    if src == "marg_sheet" and ns:
        n = OS.day_order(con, ns["id"])
        h.append('<div class="mut" id="whose">%s</div>' % esc(L(en, "whose", L(en, "darpan"), OS.ddmm(ns["newest_date"]), n[1], n[0])))
    elif src == "system":
        h.append('<div class="mut" id="whose">%s</div>' % esc(L(en, "whose", L(en, "system"), OS.today().strftime("%d-%m"), len(es), sum(len(e["lines"]) for e in es))))
    done = _done_today(con)
    wa = [d for d in done if d["via"] in ("whatsapp", "whatsapp+call")]
    if wa:
        last = max(wa, key=lambda d: d["sent_at"] or "")
        h.append('<div class="ok" id="wagone"><div class="t">%s</div><div>%s</div></div>'
                 % (L(en, "wa_went", len(wa)), esc(L(en, "wa_who", OS.ddmm(last["sent_at"]), _hm(last["sent_at"]), last["by"] or ""))))
    alive, _why = OS.phone_state(con)
    if pend:
        h.append('<button class="big" id="waall" %s onclick="s454(\'%s/api/s454/whatsapp\',{})">%s</button>' % ("" if alive else "disabled", P, L(en, "wa_all")))
        if not alive:
            h.append('<div class="mut" id="waoff">%s</div>' % L(en, "wa_off"))
            con.execute("INSERT INTO setting (key, value, note) VALUES ('s454.phone_off_met', ?, 'S454: when someone last met the disabled WhatsApp button') "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("%s %s" % (OS.now_iso(), who(u)),))   # the owner hears of it once met
            con.commit()
        h.append('<a class="big out" id="print" href="%s/s454/sheet.pdf" target="_blank">%s</a>' % (P, L(en, "print")))
        h.append('<div class="mut">%s</div>' % L(en, "callnote"))
    if done or line:
        h.append('<div class="mut" id="still">%s</div>' % L(en, "still", len(pend)))
    show = int(request.args.get("all") or 0)
    for i, e in enumerate(pend):
        if i >= 4 and not show:
            h.append('<a class="more" href="?all=1">%s</a>' % L(en, "more", len(pend) - 4))
            break
        h.append(_card(en, e))
    if line:
        h.append('<div class="mut" id="inlinehead">%s</div>' % L(en, "inline_n", len(line)))
        for e in line:
            h.append(_card(en, e))
    if done:
        h.append('<div class="mut" id="donehead">%s</div>' % L(en, "doneN", len(done)))
        for i, d in enumerate(done):
            if i >= 3 and not show:
                h.append('<a class="more" href="?all=1">%s</a>' % L(en, "more2", len(done) - 3))
                break
            word = {"whatsapp": "wa_gaya", "whatsapp+call": "wa_call", "call": "call_done", "scan": "scan_done"}.get(d["via"], "call_done")
            p1 = d["phone"]
            callb = ('<a class="sm" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">%s</a>' % (esc(_tel(p1)), P, esc(json.dumps(d["sn"])), L(en, "call"))
                     if p1 else "")
            h.append('<div class="ln"><div class="t"><div class="a">%s</div><div class="s grn">✓ %s</div></div>%s</div>' % (esc(d["vendor"]), L(en, word), callb))
    if not pend and not line and not done:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "done"))
    nold = len(OS.old_lines(con))
    if nold:
        h.append('<div class="lnk"><a id="oldlink" href="%s/s454/old">%s</a></div>' % (P, L(en, "oldlink", nold)))
    return shell(con, u, L(en, "r_order"), "".join(h), back=P, login=login)


def _hm(iso):
    d = OS._dtm(iso)
    return d.strftime("%I:%M %p").lstrip("0").lower() if d else ""


def _tel(p):
    d = re.sub(r"[^0-9+]", "", str(p or ""))
    return d


def _done_today(con):
    """Orders of the new flow made today (or from the newest sheet): how each went."""
    ns = OS.newest_sheet(con)
    since = min([OS.today().isoformat()] + ([str(ns["taken_at"])[:10]] if ns else []))
    out = []
    for o in con.execute("SELECT * FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') AND order_via<>'paper' AND created_at>=? "
                         "ORDER BY created_at, id", (since,)):
        o = dict(o)
        sent_at = o["created_at"]
        try:
            m = con.execute("SELECT sent_at FROM supplier_msg WHERE kind='order' AND ref=? AND status='sent'", (o["id"],)).fetchone()
            if m and m[0]:
                sent_at = m[0]
        except sqlite3.Error:
            pass
        out.append(dict(id=o["id"], vendor=o["vendor"], sn=o.get("supplier_norm") or _pa().supplier_key(o["vendor"]), via=o.get("order_via") or "",
                        sent_at=sent_at, by=o.get("created_by") or "", phone=OS._phones(con, o["vendor"])[0]))
    return out


# ------------------------------------------------------------------ one supplier (screens 4, 5)
def supplier_page(sn):
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return shell(con, u, L(en, "order"), '<div class="err">%s</div>' % L(en, "frozen"), back=P + "/s454/order", login=login)
    e = OS.entry_of(con, sn)
    olds = OS.old_lines(con, sn)
    vendor = e["vendor"] if e else (olds[0]["supplier"] if olds else sn)
    h = ['<h1>%s</h1>' % esc(vendor)]
    edit = request.args.get("edit") == "1"
    if e:
        h.append('<div class="mut">%s</div>' % L(en, "likhwaiye"))
        items = []
        for l in e["lines"]:
            q = OS.line_qty_text(l)
            if edit and l["src"] != "draft":
                b = esc(json.dumps(dict(src=l["src"], ref=l["ref"], item=l["item"])))
                ctl = ('<span class="qbox"><button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:-1}))">−</button><b>%d</b>'
                       '<button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:1}))">+</button>'
                       '<button class="sm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{remove:1}))">%s</button></span>'
                       % (P, b, int(l["qty"]), P, b, P, b, L(en, "remove")))
                items.append('<div class="li"><span class="i">%s</span>%s</div>' % (esc(l["item"]), ctl))
            else:
                items.append('<div class="li"><span class="i">%s</span><span class="q">%s</span></div>' % (esc(l["item"]), esc(q)))
        h.append('<div class="list" id="lines">%s</div>' % "".join(items))
        if e["has_phone"]:
            nums = "".join('<div class="num">%s</div>' % esc(x) for x in (e["phone"], e["phone2"]) if x)
            h.append('<div><a class="big blue" id="callkaro" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">📞 %s</a>%s</div>'
                     % (esc(_tel(e["phone"])), P, esc(json.dumps(e["sn"])), L(en, "callkaro"), nums))
            h.append('<div class="mut" style="text-align:center">%s</div>' % L(en, "baat"))
        else:
            h.append('<div class="mut" id="nophone">%s</div>' % L(en, "nophone_l"))
        if e["state"] == "in_line":
            h.append('<div class="mut">%s</div>' % L(en, "inline"))
        elif e["state"] == "withdrawn":
            h.append('<div class="mut am">%s</div>' % L(en, "wa_no"))
        h.append('<button class="big" id="ordered" onclick="s454(\'%s/api/s454/ordered\',{sn:%s},\'%s/s454/order\')">%s</button>'
                 % (P, esc(json.dumps(e["sn"])), P, L(en, "ordered")))
        if not e.get("draft"):
            h.append('<div class="lnk"><a id="qtylink" href="?edit=%d">%s</a></div>' % (0 if edit else 1, L(en, "qtychange")))
    if olds:
        h.append(_old_block(en, olds))
    return shell(con, u, L(en, "order"), "".join(h), back=P + "/s454/order", login=login)


def _old_block(en, olds, title=True):
    rows = []
    for l in olds:
        w = OS.old_word(l, en)
        rows.append('<div class="ol" data-line="%d"><div class="r1"><span class="i">%s</span><span class="q">%s</span></div><div class="r2"><span class="w">'
                    '<span class="mut">%s</span><span class="%s">%s</span></span><button class="sm" onclick="s454(\'%s/api/s454/reorder\',{line:%d})">%s</button></div></div>'
                    % (l["id"], esc(l["item"]), esc(OS.qty_text(l["qty_raw"])), L(en, "orderdate", OS.ddmm(l["line_date"])),
                       "grn" if l.get("marg_date") else "red", esc(w), P, l["id"], L(en, "reorder")))
    return '<div class="oldb">%s%s</div>' % (('<div class="h">%s</div>' % L(en, "oldblk")) if title else "", "".join(rows))


def old_page():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    olds = OS.old_lines(con)
    by = {}
    for l in olds:
        by.setdefault(l["supplier_norm"], []).append(l)
    h = ['<h1>%s</h1>' % L(en, "oldall"), '<div class="mut">%s</div>' % L(en, "oldblk")]
    for sn, ls in sorted(by.items(), key=lambda kv: kv[1][0]["supplier"]):
        h.append('<div class="grp"><a href="%s/s454/order/%s" style="color:#1c1c1c">%s</a></div>' % (P, quote(sn, safe=""), esc(ls[0]["supplier"])))
        h.append(_old_block(en, ls, title=False))
    if not olds:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "done"))
    return shell(con, u, L(en, "oldall"), "".join(h), back=P + "/s454/order", login=login)


# ------------------------------------------------------------------ Maal aaya? (screens 7, 8, 9)
def maal_list():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    os_ = maal_orders(con)
    h = ['<div style="font-size:16px">%s</div>' % L(en, "maal_top")]
    for o in os_:
        h.append('<div class="card" data-order="%d"><div><div class="nm">%s</div><div class="sb">%s</div></div>'
                 '<a class="big" style="min-height:52px;font-size:18px" href="%s">📷 %s</a>'
                 '<div class="lnk"><a href="%s/s454/maal/%d">%s</a></div></div>'
                 % (o["id"], esc(o["vendor"]), esc(L(en, "orderN", OS.ddmm(o["created_at"]), o["n"])),
                    esc(intake(o["vendor"], back=P + "/s454/maal")), L(en, "billscan"), P, o["id"], L(en, "nobill")))
    if not os_:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "done"))
    return shell(con, u, L(en, "r_maal"), "".join(h), back=P, login=login)


def arrive_page(oid):
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    o = con.execute("SELECT * FROM purchase_order WHERE id=?", (oid,)).fetchone()
    if not o:
        return shell(con, u, L(en, "r_maal"), '<div class="err">no such order</div>', back=P + "/s454/maal", login=login)
    o = dict(o)
    if request.args.get("done") == "1" or o["status"] != "sent":
        n = con.execute("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=?", (oid,)).fetchone()[0]
        h = ['<div class="ok" id="darj"><div class="t">%s</div><div>%s · %s</div></div>' % (L(en, "darj"), esc(o["vendor"]), esc(L(en, "dawa", n))),
             '<div style="font-size:18px;font-weight:700">%s</div>' % L(en, "abhiscan"),
             '<div class="two"><a class="g" id="scannow" href="%s">%s</a><a class="b" id="later" href="%s">%s</a></div>'
             % (esc(intake(o["vendor"], back=P)), L(en, "billscan"), P, L(en, "baadmein")),
             '<div class="mut">%s</div>' % L(en, "baadnote")]
        return shell(con, u, L(en, "r_maal"), "".join(h), back=P, login=login)
    lines = [dict(l) for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id=? ORDER BY id", (oid,))]
    h = ['<h1>%s</h1>' % esc(o["vendor"]), '<div class="mut">%s · %s</div>' % (L(en, "orderdate", OS.ddmm(o["created_at"]))[:-3], L(en, "tapshort"))]
    rows = []
    for l in lines:
        qt = ("%d strip" % l["packs"]) if int(l["pack_size"] or 1) > 1 else "%d" % l["packs"]
        rows.append('<div class="ar" data-line="%d" onclick="arTap(%d)"><span id="ic%d">✓</span><span class="i">%s</span><span class="q">%s</span></div>'
                    '<div id="ch%d" style="display:none;padding:0 0 10px"><div class="chips"><button onclick="arHow(%d,\'short\')" id="b_short_%d">%s</button>'
                    '<button onclick="arHow(%d,\'missing\')" id="b_missing_%d">%s</button><button onclick="arHow(%d,\'ok\')" id="b_ok_%d">%s</button></div>'
                    '<div class="qbox" id="kq%d" style="display:none;margin-top:8px"><span>%s</span><input class="kq" type="number" min="0" max="%d" id="kv%d"> <span>%s</span></div></div>'
                    % (l["id"], l["id"], l["id"], esc(l["item"]), esc(qt), l["id"], l["id"], l["id"], L(en, "kam"), l["id"], l["id"], L(en, "nahimila"),
                       l["id"], l["id"], L(en, "aagaya"), l["id"], L(en, "kitna"), max(0, int(l["packs"]) - 1), l["id"],
                       "strip" if int(l["pack_size"] or 1) > 1 else ""))
    h.append('<div class="list">%s</div>' % "".join(rows))
    h.append('<button class="big" id="maalok" onclick="arSave()">%s</button>' % L(en, "maal_ok"))
    h.append('<div class="lnk"><a id="abhinahi" href="%s/s454/maal">%s</a></div>' % (P, L(en, "abhinahi")))
    h.append("""<script>
var HOW={};
function arTap(id){var c=document.getElementById('ch'+id);c.style.display=(c.style.display==='none'?'block':'none');}
function arHow(id,how){HOW[id]=how;['short','missing','ok'].forEach(function(k){document.getElementById('b_'+k+'_'+id).className=(k===how?'on':'');});
 document.getElementById('kq'+id).style.display=(how==='short'?'flex':'none');document.getElementById('ic'+id).textContent=(how==='ok'?'✓':'!');}
function arSave(){var lines=[];for(var id in HOW){var l={id:parseInt(id),how:HOW[id]};if(HOW[id]==='short'){var v=parseInt((document.getElementById('kv'+id)||{}).value);
 if(isNaN(v)){var m=document.getElementById('msg');m.textContent='%s';m.style.display='block';window.scrollTo(0,0);return;}l.supplied=v;}lines.push(l);}
 s454('%s/api/s454/arrive',{order_id:%d,lines:lines},'%s/s454/maal/%d?done=1');}
</script>""" % (L(en, "kitna"), P, oid, P, oid))
    return shell(con, u, L(en, "r_maal"), "".join(h), back=P + "/s454/maal", login=login)


# ------------------------------------------------------------------ Bill scan karna hai (screen 10)
def scan_page():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    month = request.args.get("month") if re.match(r"^\d{4}-\d\d$", str(request.args.get("month") or "")) else None
    if month and month_class(con, month) != "parked":
        month = None
    lines = scan_lines(con, "parked" if month else "counted", month)
    back = (P + "/s454/purana/" + month) if month else P
    if request.args.get("missing") == "1":
        marg = [x for x in lines if x["kind"] == "marg"]
        h = ['<div class="mut">%s</div>' % L(en, "tickpaper")]
        for x in marg:
            h.append('<label class="tk card"><input type="checkbox" value="%d" class="pm_"><span><b>%s</b> · %s · %s · %s</span></label>'
                     % (x["bill_id"], esc(x["vendor"]), esc(L(en, "billno", x["bill_no"])), esc(OS.ddmm(x["date"])), esc(rs(x["amount_p"]))))
        h.append('<button class="big" id="pmsave" onclick="var ids=[].slice.call(document.querySelectorAll(\'.pm_:checked\')).map(function(e){return parseInt(e.value)});'
                 's454(\'%s/api/s454/paper_missing\',{bills:ids},\'%s/s454/scan%s\')">%s</button>' % (P, P, ("?month=" + month) if month else "", L(en, "papernotfound")))
        return shell(con, u, L(en, "nopaper"), "".join(h), back=P + "/s454/scan" + (("?month=" + month) if month else ""), login=login)
    shown = 5 * max(1, int(request.args.get("n") or 1))
    h = ['<div class="mut">%s</div>' % L(en, "scan_top")]
    vis = lines[:shown]
    by = []
    for x in vis:
        if not by or by[-1][0] != x["sn"]:
            by.append((x["sn"], x["vendor"], []))
        by[-1][2].append(x)
    for sn, vendor, xs in by:
        h.append('<div class="grp">%s</div>' % esc(L(en, "nbill", vendor, len([y for y in lines if y["sn"] == sn]))))
        for x in xs:
            if x["kind"] == "recv":
                a, s = L(en, "kamaal", OS.ddmm(x["date"])), L(en, "k_recv")
            else:
                a, s = L(en, "billno", x["bill_no"]), "%s · %s · %s" % (OS.ddmm(x["date"]), rs(x["amount_p"]), L(en, "k_marg"))
            h.append('<div class="ln" data-kind="%s"><div class="t"><div class="a">%s</div><div class="s">%s</div></div><a class="sk" href="%s">%s</a></div>'
                     % (x["kind"], esc(a), esc(s), esc(x["intake"]), L(en, "scankaro")))
    if len(lines) > shown:
        h.append('<a class="more" id="agle" href="?n=%d%s">%s</a>' % (shown // 5 + 1, ("&month=" + month) if month else "", L(en, "agle")))
    if any(x["kind"] == "marg" for x in lines):
        h.append('<div class="lnk"><a id="nopaper" href="?missing=1%s">%s</a></div>' % (("&month=" + month) if month else "", L(en, "nopaper")))
    if not lines:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "done"))
    return shell(con, u, L(en, "r_scan"), "".join(h), back=back, login=login)


# ------------------------------------------------------------------ Photo dekh kar bataiye (screens 11, 12, 13)
def _likely_suppliers(con, read):
    pa = _pa()
    sups = sorted({pa.supplier_key(r[0]) for r in con.execute("SELECT DISTINCT supplier FROM purchase_bill") if r[0]})
    toks = pa._vendor_tokens_s439(read)
    scored = []
    if toks:
        for s in sups:
            try:
                sc = pa._vendor_sim_s439(toks, pa._vendor_tokens_s439(s))
            except Exception:                                 # noqa: BLE001
                sc = 0
            if sc > 0:
                scored.append((-sc, s))
    top = [s for _sc, s in sorted(scored)[:3]]
    if len(top) < 3:
        for sn, _os in OS.awaiting_scan(con).items():
            if sn not in top and sn in sups:
                top.append(sn)
            if len(top) >= 3:
                break
    return top[:3], sups


def q_page():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    month = request.args.get("month") if re.match(r"^\d{4}-\d\d$", str(request.args.get("month") or "")) else None
    if month and month_class(con, month) != "parked":
        month = None
    qs = questions(con, "parked" if month else "counted", month)
    back = (P + "/s454/purana/" + month) if month else P
    if not qs:
        return shell(con, u, L(en, "r_q"), '<div class="ok" id="alldone"><div class="t">%s</div></div><a class="more" href="%s">%s</a>'
                     % (L(en, "done"), back, "OK"), back=back, login=login)
    q = qs[0]
    n = len(qs)
    mq = ("&month=" + month) if month else ""
    h = ['<div class="mut" id="sawaal">%s</div><div class="prog"><i style="width:%d%%"></i></div>' % (L(en, "sawaal", 1, n), int(100.0 / n)),
         '<a class="pic" href="%s" target="_blank"><img src="%s" alt="scan" onerror="this.style.display=\'none\'"><div>%s · %s</div></a>'
         % (esc(q["pdf"]), esc(q["thumb"]), L(en, "kagaz" if q["kind"] == "pharmacy" else "photo"), L(en, "badi"))]
    body = dict(scan=q["scan"])
    if q["kind"] == "bill":
        h.append('<div class="nm" style="font-size:18px;font-weight:700" data-q="bill">%s</div><div class="mut">%s · %s</div>'
                 % (esc(L(en, "q_dup" if q.get("taken") else "q_bill", q["vendor"], q["bill_no"])), esc(OS.ddmm(OS._iso_dmy(q["date_text"]) or q["date_text"])), esc(q["amount"])))
        b = esc(json.dumps(dict(scan=q["scan"], bill=q["bill"])))
        h.append('<button class="big" onclick="s454(\'%s/api/s454/confirm\',Object.assign(%s,{yes:true}))">%s</button>'
                 '<button class="big out" onclick="s454(\'%s/api/s454/confirm\',Object.assign(%s,{yes:false}))">%s</button>'
                 % (P, b, L(en, "haan"), P, b, L(en, "nahi")))
    elif q["kind"] == "amount":
        a1, a2 = sorted([int(q["marg_p"] or 0), int(q["scan_p"] or 0)])
        h.append('<div class="mut">%s · %s · %s</div><div style="font-size:18px;font-weight:700" data-q="amount">%s</div>'
                 % (esc(q["vendor"]), esc(L(en, "billno", q["bill_no"])), esc(OS.ddmm(OS._iso_dmy(q["date_text"]) or q["date_text"])), L(en, "q_amount")))
        for a in (a1, a2):
            h.append('<button class="big out" onclick="s454(\'%s/api/s454/amount\',{scan:%d,paper:\'%s\'})">%s</button>' % (P, q["scan"], "%.2f" % (a / 100.0), esc(rs(a))))
        h.append('<div class="qbox"><span>%s</span><input class="amt" inputmode="decimal" id="koiaur"><button class="sm" onclick="s454(\'%s/api/s454/amount\','
                 '{scan:%d,paper:(document.getElementById(\'koiaur\').value||\'\').trim()})">%s</button></div>' % (L(en, "koiaur_amt"), P, q["scan"], L(en, "go")))
    elif q["kind"] == "vendor":
        top, sups = _likely_suppliers(con, q.get("read") or "")
        h.append('<div class="mut">%s</div><div style="font-size:18px;font-weight:700" data-q="vendor">%s</div>' % (esc(L(en, "scan_of", q["stamp"])), L(en, "q_vendor")))
        for s in top:
            h.append('<button class="big out" onclick="s454(\'%s/api/s454/vendor\',{scan:%d,vendor:%s})">%s</button>' % (P, q["scan"], esc(json.dumps(s)), esc(s)))
        h.append('<details class="card"><summary style="min-height:44px;cursor:pointer;font-weight:700">%s</summary><select class="kv" id="kv"><option value="">%s</option>%s'
                 '<option value="-">%s</option></select><button class="big" onclick="var v=document.getElementById(\'kv\').value;if(v)s454(\'%s/api/s454/vendor\',{scan:%d,vendor:v})">%s</button></details>'
                 % (L(en, "koiaur"), L(en, "pick"), "".join('<option>%s</option>' % esc(s) for s in sups), L(en, "notlisted"), P, q["scan"], L(en, "go")))
    elif q["kind"] == "pharmacy":
        h.append('<div class="mut">%s · %s</div><div style="font-size:18px;font-weight:700" data-q="pharmacy">%s</div>'
                 % (esc(q.get("read") or "—"), esc(L(en, "scan_of", q["scan_day"] or q["stamp"])), L(en, "q_ph")))
        h.append('<button class="big" onclick="s454(\'%s/api/s454/pharmacy\',{scan:%d,yes:true})">%s</button>' % (P, q["scan"], L(en, "ph_yes")))
        h.append('<form method="post" action="/scanapp/bills/%d/lane" onsubmit="return s454nope(this)"><input type="hidden" name="lane" value="clinic">'
                 '<input type="hidden" name="back" value="%s/s454/q%s"><button class="big out" style="width:100%%">%s</button></form>'
                 % (q["scan"], P, ("?month=" + month) if month else "", L(en, "ph_no")))
        h.append('<script>function s454nope(f){fetch("%s/api/s454/pharmacy",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scan:%d,yes:false})})'
                 '.then(function(){f.submit();}).catch(function(){f.submit();});return false;}</script>' % (P, q["scan"]))
    elif q["kind"] == "s441":
        lane = q.get("qkind") == "lane"
        c = q.get("cand")
        h.append('<div class="mut">%s · %s</div><div style="font-size:18px;font-weight:700" data-q="s441">%s</div>' % (esc(q["stamp"]), esc(q.get("read") or ""),
                                                                                                                 L(en, "q_lane" if lane else "q_twin")))
        if c:
            h.append('<a class="pic" href="%s" target="_blank"><img src="%s" alt="scan"><div>%s · %s</div></a>' % (esc(c["pdf"]), esc(c["thumb"]), esc(c["stamp"]), esc(c.get("amount") or "")))
        a1, a2 = ("pharmacy", "stay") if lane else ("same", "different")
        h.append('<button class="big" onclick="s454(\'/scanapp/bills/%d/s441\',{q:%s,answer:\'%s\'})">%s</button>'
                 '<button class="big out" onclick="s454(\'/scanapp/bills/%d/s441\',{q:%s,answer:\'%s\'})">%s</button>'
                 % (q["scan"], esc(json.dumps(q["q"])), a1, L(en, "tophar" if lane else "same"), q["scan"], esc(json.dumps(q["q"])), a2, L(en, "stay" if lane else "diff")))
    h.append('<div class="lnk"><button id="later" onclick="s454(\'%s/api/s454/later\',{scan:%d,kind:\'%s\'})">%s</button></div>' % (P, q["scan"], q["kind"], L(en, "baadmein")))
    _ = body, mq
    return shell(con, u, L(en, "sawaal", 1, n), "".join(h), back=back, login=login)


# ------------------------------------------------------------------ a parked month (screen 15)
def purana_page(month):
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    if month_class(con, month) != "parked":
        return redirect(P)
    c = counts(con, month)
    h = ['<h1>%s</h1>' % esc(month_name(month)), '<div class="mut">%s</div>' % L(en, "park_top")]
    if c["scan"]:
        h.append('<a class="row" id="prow_scan" href="%s/s454/scan?month=%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (P, month, c["scan"], L(en, "r_scan")))
    if c["q"]:
        h.append('<a class="row" id="prow_q" href="%s/s454/q?month=%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (P, month, c["q"], L(en, "r_q")))
    if not (c["scan"] or c["q"]):
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "done"))
    return shell(con, u, L(en, "purana", month_name(month)), "".join(h), back=P, login=login)


# ------------------------------------------------------------------ routes
@bp.route(P + "/s454/order")
def r_order():
    return order_list()


@bp.route(P + "/s454/order/<path:sn>")
def r_supplier(sn):
    return supplier_page(sn)


@bp.route(P + "/s454/old")
def r_old():
    return old_page()


@bp.route(P + "/s454/maal")
def r_maal():
    return maal_list()


@bp.route(P + "/s454/maal/<int:oid>")
def r_arrive(oid):
    return arrive_page(oid)


@bp.route(P + "/s454/scan")
def r_scan():
    return scan_page()


@bp.route(P + "/s454/q")
def r_q():
    return q_page()


@bp.route(P + "/s454/purana/<month>")
def r_purana(month):
    return purana_page(month)


@bp.route(P + "/s454/sheet.pdf")
def r_sheet_pdf():
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import order_sheet_pdf                                    # noqa: PLC0415
    data = order_sheet_pdf.build(con)
    OS.audit(con, who(u), "s454_sheet_printed", "", dict(bytes=len(data)))
    con.commit()
    return data, 200, {"Content-Type": "application/pdf", "Cache-Control": "no-store",
                       "Content-Disposition": 'inline; filename="order_sheet_%s.pdf"' % OS.today().isoformat()}


@bp.route(P + "/api/s454/state")
def api_state():
    u, con, kind, err = _auth_api()
    if err:
        return err
    _every_read(con)
    c = counts(con)
    es = OS.entries(con)
    return jsonify(ok=True, counts=c, source=OS.source(con), parked=[m for m, _c in parked_with_work(con)],
                   suppliers=[dict(sn=e["sn"], vendor=e["vendor"], state=e["state"], lines=len(e["lines"]), has_phone=e["has_phone"]) for e in es],
                   phone_alive=OS.phone_state(con)[0])


def _body():
    return request.get_json(silent=True) or {}


@bp.route(P + "/api/s454/ordered", methods=["POST"])
def api_ordered():
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    b, code = OS.order_supplier(con, who(u), str(_body().get("sn") or ""), "call")
    return jsonify(**b), code


@bp.route(P + "/api/s454/whatsapp", methods=["POST"])
def api_whatsapp():
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    b, code = OS.whatsapp_all(con, who(u))
    return jsonify(**b), code


@bp.route(P + "/api/s454/call", methods=["POST"])
def api_call():
    u, con, kind, err = _auth_api()
    if err:
        return err
    sn = str(_body().get("sn") or "")[:120]
    OS.audit(con, who(u), "s454_call", sn, dict(supplier=sn))
    con.commit()
    return jsonify(ok=True)


@bp.route(P + "/api/s454/qty", methods=["POST"])
def api_qty():
    """Quantity badalni hai? -- S410's plus, minus, remove on one line before it is ordered. A re-ordered old line removed goes back
    among the old pending."""
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    b = _body()
    src, ref, item = str(b.get("src") or ""), str(b.get("ref") or ""), str(b.get("item") or "")
    if src not in ("sheet", "proposal", "ortho"):
        return jsonify(ok=False, error="bad_line"), 400
    e = next((x for x in OS.entries(con) for l in x["lines"] if l["src"] == src and l["ref"] == ref and l["item"] == item), None)
    if not e:
        return jsonify(ok=False, error="gone", message="Yeh line ab order mein nahi hai."), 409
    l = next(l for l in e["lines"] if l["src"] == src and l["ref"] == ref and l["item"] == item)
    if b.get("remove"):
        if src == "sheet":
            r = con.execute("SELECT reorder_day, kind FROM order_sheet_line WHERE id=?", (int(ref),)).fetchone()
            if r and r[0]:
                con.execute("UPDATE order_sheet_line SET state='old', reorder_day=NULL, updated_at=? WHERE id=?", (OS.now_iso(), int(ref)))
                OS.audit(con, who(u), "s454_reorder_undone", ref, dict(item=item))
                con.commit()
                return jsonify(ok=True, back_to_old=True)
        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES (?,?,?,?,1,?,?) ON CONFLICT(src, ref, item) DO UPDATE SET removed=1, by=excluded.by, at=excluded.at",
                    (src, ref, item, None, who(u), OS.now_iso()))
        OS.audit(con, who(u), "s454_line_removed", ref, dict(src=src, item=item))
    else:
        try:
            d = int(b.get("delta") or 0)
        except (TypeError, ValueError):
            d = 0
        q = max(1, int(l["qty"]) + d)
        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES (?,?,?,?,0,?,?) ON CONFLICT(src, ref, item) DO UPDATE SET qty=excluded.qty, by=excluded.by, at=excluded.at",
                    (src, ref, item, q, who(u), OS.now_iso()))
        OS.audit(con, who(u), "s454_qty", ref, dict(src=src, item=item, before=int(l["qty"]), after=q))
    con.commit()
    return jsonify(ok=True)


@bp.route(P + "/api/s454/reorder", methods=["POST"])
def api_reorder():
    """Dobara order karo -- an old pending line becomes a new line of today's order (counted from today)."""
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    try:
        lid = int(_body().get("line") or 0)
    except (TypeError, ValueError):
        lid = 0
    r = con.execute("SELECT id, state, item FROM order_sheet_line WHERE id=?", (lid,)).fetchone()
    if not r or r[1] not in ("old", "lapsed"):
        return jsonify(ok=False, error="not_old", message="Yeh line purane pending mein nahi hai."), 409
    con.execute("UPDATE order_sheet_line SET state='to_order', reorder_day=?, marg_date=NULL, marg_bill=NULL, marg_seen_at=NULL, updated_at=? WHERE id=?",
                (OS.today().isoformat(), OS.now_iso(), lid))
    OS.audit(con, who(u), "s454_reorder", lid, dict(item=r[2]))
    con.commit()
    return jsonify(ok=True)


@bp.route(P + "/api/s454/arrive", methods=["POST"])
def api_arrive():
    """The arrival screen: every line received unless tapped -- 'Kam aaya' with how many, 'Nahi mila'; saved by today's rules
    (porders' per-line answers, then the order RECEIVED by S225's own door)."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        oid = int(b.get("order_id") or 0)
    except (TypeError, ValueError):
        oid = 0
    o = con.execute("SELECT id, status FROM purchase_order WHERE id=?", (oid,)).fetchone()
    if not o:
        return jsonify(ok=False, error="no_such_order"), 404
    if o[1] != "sent":
        return jsonify(ok=True, already=True, message="Yeh order pehle hi aa chuka hai.")
    tapped = {}
    for x in b.get("lines") or []:
        try:
            tapped[int(x.get("id"))] = x
        except (TypeError, ValueError, AttributeError):
            continue
    w = who(u)
    t = OS.now_iso()
    for l in con.execute("SELECT id, item, packs, supplied, missing FROM purchase_order_line WHERE order_id=?", (oid,)).fetchall():
        if l[3] is not None or l[4]:
            continue
        x = tapped.get(l[0]) or {}
        how = x.get("how") or "ok"
        packs = int(l[2] or 0)
        if how == "short":
            try:
                sup = int(x.get("supplied"))
            except (TypeError, ValueError):
                return jsonify(ok=False, error="bad_qty", message="Kitna aaya?"), 400
            if sup < 0 or sup >= packs:
                return jsonify(ok=False, error="bad_qty", message="Kam aaya = %d se kam." % packs), 400
            vals = (sup, 1, 0)
        elif how == "missing":
            vals = (0, 1, 1)
        else:
            vals = (packs, 0, 0)
        con.execute("UPDATE purchase_order_line SET supplied=?, short=?, missing=?, arrived_by=?, arrived_at=? WHERE id=?", vals + (w, t, l[0]))
        if how != "ok":
            OS.audit(con, w, "porders_line_" + how, l[0], dict(order=oid, item=l[1], ordered=packs, supplied=vals[0], missing=vals[2], kit="S454"))
    con.commit()
    _po()._close_complete_orders(con, w)
    OS.audit(con, w, "s454_arrived", oid, dict(tapped=len(tapped)))
    con.commit()
    return jsonify(ok=True, order_id=oid)


@bp.route(P + "/api/s454/later", methods=["POST"])
def api_later():
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        sid = int(b.get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    k = str(b.get("kind") or "")
    if not sid or k not in QKINDS:
        return jsonify(ok=False, error="bad_request"), 400
    con.execute("INSERT INTO s454_later (asset_bill_id, kind, at) VALUES (?,?,?) ON CONFLICT(asset_bill_id, kind) DO UPDATE SET at=excluded.at", (sid, k, OS.now_iso()))
    con.commit()
    return jsonify(ok=True)


def _answer(con, sid, kindq, answer, value, w):
    con.execute("INSERT INTO s454_scan_answer (asset_bill_id, kind, answer, value, by, at) VALUES (?,?,?,?,?,?) ON CONFLICT(asset_bill_id, kind) DO UPDATE SET "
                "answer=excluded.answer, value=excluded.value, by=excluded.by, at=excluded.at", (sid, kindq, answer, value, w, OS.now_iso()))
    OS.audit(con, w, "s454_scan_answer", sid, dict(kind=kindq, answer=answer, value=value))
    con.commit()


@bp.route(P + "/api/s454/pharmacy", methods=["POST"])
def api_pharmacy():
    """Kya yeh dawa (pharmacy) ka bill hai? -- Haan keeps it in the pharmacy lane (an unread pharmacy paper); Nahi is recorded here and the
    page then moves it to the clinic lane through the asset app's own re-lane route."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        sid = int(b.get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    if not sid:
        return jsonify(ok=False, error="bad_request"), 400
    _answer(con, sid, "pharmacy", "yes" if b.get("yes") else "no", None, who(u))
    return jsonify(ok=True)


@bp.route(P + "/api/s454/vendor", methods=["POST"])
def api_vendor():
    """Yeh bill kis supplier ka hai? -- S440's own route when the matcher asks (it learns the spelling); for an unread pharmacy paper the
    choice is kept here."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        sid = int(b.get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    row = con.execute("SELECT why FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone() if sid else None
    if row and row[0] == "vendor_unknown":
        return _po().api_scan_vendor()
    v = str(b.get("vendor") or "").strip()
    pa = _pa()
    sups = {pa.supplier_key(r[0]) for r in con.execute("SELECT DISTINCT supplier FROM purchase_bill") if r[0]}
    if v != "-" and v not in sups:
        return jsonify(ok=False, error="bad_vendor", message="List mein se supplier chuniye."), 400
    _answer(con, sid, "vendor", "chosen", v, who(u))
    return jsonify(ok=True)


@bp.route(P + "/api/s454/confirm", methods=["POST"])
def api_confirm():
    """Kya yeh <SUPPLIER> ka bill <number> hai? -- S440's own route for the matcher's likely bill; for an unread pharmacy paper reception's
    'Haan' pairs it (grade CONFIRMED, 'paired by reception; nothing was read on the paper')."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        sid, bid = int(b.get("scan") or 0), int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    s = (OS.answers(con).get(sid) or {}).get("pharmacy")
    if not s or s.get("answer") != "yes":
        return _po().api_scan_confirm()                       # the matcher's likely bill: S440's own meaning
    w = who(u)
    if not b.get("yes"):
        _answer(con, sid, "pair", "no", str(bid), w)
        return jsonify(ok=True, linked=False)
    if con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=? OR asset_bill_id=?", (bid, sid)).fetchone():
        return jsonify(ok=False, error="taken", message="Yeh bill ab kisi aur scan se juda hai."), 409
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (bid, sid, "CONFIRMED", "paired by reception; nothing was read on the paper", OS.now_iso()))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, bid))
    _answer(con, sid, "pair", "yes", str(bid), w)
    OS.audit(con, w, "scan_link", bid, dict(scan=sid, grade="CONFIRMED", rule="paired by reception; nothing was read on the paper", kit="S454"))
    con.commit()
    return jsonify(ok=True, linked=True)


@bp.route(P + "/api/s454/amount", methods=["POST"])
def api_amount():
    """Bill par total amount kya likha hai? -- a counted month: S440's own consequences; a parked month: the answer is recorded on the
    register only (nothing reaches Amir)."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        sid = int(b.get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    raw = str(b.get("paper") or "").replace(",", "").replace("₹", "").strip()
    if not re.fullmatch(r"\d{1,9}(\.\d{1,2})?", raw):
        return jsonify(ok=False, error="bad_amount", message="Sirf ank likhiye — jaise 14442"), 400
    lk = con.execute("SELECT l.bill_id, b.month, b.bill_date FROM purchase_scan_link l JOIN purchase_bill b ON b.id=l.bill_id WHERE l.asset_bill_id=?", (sid,)).fetchone()
    if not lk:
        return jsonify(ok=False, error="no_such_line"), 409
    ym = lk[1] or str(lk[2] or "")[:7]
    if month_class(con, ym) == "counted":
        return _po().api_scan_amount()
    _answer(con, sid, "amount", "paper", str(int(round(float(raw) * 100))), who(u))
    return jsonify(ok=True, parked=True)


@bp.route(P + "/api/s454/paper_missing", methods=["POST"])
def api_paper_missing():
    u, con, kind, err = _auth_api()
    if err:
        return err
    ids = []
    for x in _body().get("bills") or []:
        try:
            ids.append(int(x))
        except (TypeError, ValueError):
            continue
    w = who(u)
    for bid in ids:
        if con.execute("SELECT 1 FROM purchase_bill WHERE id=?", (bid,)).fetchone():
            con.execute("INSERT OR IGNORE INTO s454_paper_missing (bill_id, by, at) VALUES (?,?,?)", (bid, w, OS.now_iso()))
            OS.audit(con, w, "s454_paper_missing", bid, dict(kit="S454"))
    con.commit()
    return jsonify(ok=True, n=len(ids))


# ------------------------------------------------------------------ the owner's settings card and ordering cards (the old page, owner only)
def _valid(key, v):
    v = str(v or "").strip()
    if key == "porders.simple" or key == "order.sheet_print_old":
        return v in ("0", "1"), v
    if key == "order.source":
        return v in ("marg_sheet", "system"), v
    if key == "order.remind_times":
        m = re.match(r"^(\d\d):(\d\d)$", v)
        ok = bool(m) and "05:00" <= v <= "21:50" and int(m.group(2)) % 10 == 0
        return ok, v
    if key == "purchase.register_from":
        ok = bool(re.match(r"^\d{4}-\d\d-01$", v))
        return ok, v
    if key == "purchase.parked_months":
        ms = [x.strip() for x in v.split(",") if x.strip()]
        return all(re.match(r"^\d{4}-\d\d$", x) for x in ms), ",".join(ms)
    lim = {"order.sheet_max_age_days": (1, 60), "order.old_done_days": (0, 90), "order.old_show_days": (1, 365), "order.whatsapp_wait_min": (5, 600),
           "order.phone_alive_min": (5, 600), "supplier_msg.handout_gap_min": (1, 120), "purchase.arrival_scan_days": (1, 60),
           "purchase.unread_pair_days": (1, 60)}.get(key)
    if lim:
        try:
            n = int(v)
        except ValueError:
            return False, v
        return lim[0] <= n <= lim[1], str(n)
    return False, v


@bp.route(P + "/api/s454/setting", methods=["POST"])
def api_setting():
    """The owner's settings card: one key at a time, validated, audited (purchase_audit 's454_setting'). The owner only."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = _body()
    key = str(b.get("key") or "")
    if key not in OS.SETTINGS:
        return jsonify(ok=False, error="bad_key"), 400
    ok, v = _valid(key, b.get("value"))
    if not ok:
        return jsonify(ok=False, error="bad_value", message="%s: not a valid value" % key), 400
    old = OS.setting(con, key)
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, v, OS.SETTINGS[key][1]))
    OS.audit(con, who(u), "s454_setting", key, dict(before=old, after=v))
    con.commit()
    return jsonify(ok=True, key=key, value=v, before=old)


def owner_cards(con):
    """The owner's ordering cards (S454 7.5, without the gap card) and the settings card -- HTML for the old page, English."""
    OS.ensure(con)
    try:
        OS.load_pending(con)
    except Exception:                                         # noqa: BLE001
        pass
    src = OS.source(con)
    st = 'style="background:#fff;border:1px solid #e4e0da;border-radius:10px;margin:10px 0;padding:12px 14px"'
    h = ['<div id="s454owner">']
    h.append('<div %s id="s454src"><b>Who decides the order</b> · %s <button onclick="s454set(\'order.source\',\'%s\')" style="min-height:40px">%s</button>'
             '<div style="color:#666;font-size:13px">%s</div></div>'
             % (st, "Darpan's Marg order sheet" if src == "marg_sheet" else "The system's own list", "system" if src == "marg_sheet" else "marg_sheet",
                "Change to the system's own list" if src == "marg_sheet" else "Change to Darpan's sheet",
                "The system's own list is worked out every order day but is shown to no staff." if src == "marg_sheet" else
                "Darpan's sheet, when one arrives, is compared and shown to you only."))
    ns = OS.newest_sheet(con)
    if ns and ns.get("cmp"):
        c = json.loads(ns["cmp"])
        if "x" in c:
            rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(r["item"]), esc(r["sheet"]), esc(r["system"])) for r in c["both"])
            h.append('<div %s id="s454cmp"><b>Orders of %s: the system agreed on %d of %d items with Darpan\'s sheet</b>'
                     '<details><summary>the three lists</summary><table style="width:100%%;font-size:14px"><tr><th>On both</th><th>Darpan ordered</th><th>System\'s list</th></tr>%s</table>'
                     '<p>Only on Darpan\'s sheet (%d): %s</p><p>Only on the system\'s list (%d): %s</p></details></div>'
                     % (st, esc(OS.dmy(ns["newest_date"])), c["x"], c["y"], rows, len(c["only_sheet"]), esc(", ".join(r["item"] for r in c["only_sheet"])),
                        len(c["only_system"]), esc(", ".join("%s %s" % (r["item"], r["system"]) for r in c["only_system"]))))
    allold = OS.old_lines(con, staff=False)
    if allold:
        sup = sum(1 for l in allold if l.get("marg_date"))
        by = {}
        for l in allold:
            by.setdefault(l["supplier"], []).append(l)
        oldest = min(l["line_date"] for l in allold)
        lst = "".join("<li><b>%s</b>: %s</li>" % (esc(k), esc("; ".join("%s %s (%s)" % (l["item"], OS.dmy(l["line_date"]), OS.old_word(l, True)) for l in v)))
                      for k, v in sorted(by.items()))
        h.append('<div %s id="s454old"><b>Marg shows %d old pending orders: %d already supplied since, %d never came</b><div style="color:#666;font-size:13px">'
                 'The oldest is of %s. Staff see them marked apart and are not asked to close them in Marg.</div><details><summary>by supplier</summary><ul>%s</ul></details></div>'
                 % (st, len(allold), sup, len(allold) - sup, esc(OS.dmy(oldest)), lst))
    if ns:
        rf = OS.refused_sheet(con)
        un = json.loads(ns.get("unresolved") or "[]")
        phn = json.loads(ns.get("phones_new") or "{}")
        extra = ""
        if un:
            extra += "<div>Names not found in Marg's stock list: %s</div>" % esc(", ".join(x["item"] for x in un))
        for v in phn.values():
            extra += "<div>%s prints %s; the phone book has none — <a href=\"/finance/purchase/page/book\">add it in the phone book</a></div>" % (esc(v["supplier"]), esc(", ".join(v["phones"])))
        h.append('<div %s id="s454sheet"><b>Order sheet of %s: taken %s, %d new lines</b> (%d old, %d known)%s%s</div>'
                 % (st, esc(OS.dmy(ns["newest_date"])), esc(str(ns["taken_at"])[:16].replace("T", " ")), int(ns["n_new"] or 0), int(ns["n_old"] or 0), int(ns["n_known"] or 0),
                    ("<div style=\"color:#8c1d18\">A newer file was refused %s: %s</div>" % (esc(rf["at"]), esc(rf["reason"][:200]))) if rf else "", extra))
    else:
        h.append('<div %s id="s454sheet"><b>No order sheet taken yet.</b> A file that is incomplete is refused and shown here.</div>' % st)
    rows = []
    for k, (dv, meaning) in OS.SETTINGS.items():
        v = OS.setting(con, k)
        rows.append('<tr><td><code>%s</code><div style="color:#666;font-size:12.5px">%s</div></td><td><input id="s454k_%s" value="%s" style="width:120px;min-height:36px">'
                    ' <button onclick="s454set(\'%s\',document.getElementById(\'s454k_%s\').value)" style="min-height:36px">Save</button></td></tr>'
                    % (esc(k), esc(meaning), esc(k.replace(".", "_")), esc(v), esc(k), esc(k.replace(".", "_"))))
    h.append('<details %s id="s454settings"><summary><b>Settings (S454)</b></summary><table style="width:100%%;font-size:14px">%s</table></details>' % (st, "".join(rows)))
    h.append("""<script>function s454set(k,v){fetch('/finance/porders/api/s454/setting',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k,value:v})})
.then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error);return;}location.reload();});}</script>""")
    h.append('<div style="margin:6px 0"><a href="/finance/porders">← the new screen</a></div></div>')
    return "".join(h)

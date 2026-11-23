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
#    GET  /finance/porders/s454/marg.pdf              S543: Marg's own PENDING ORDERS export, printed as Marg printed it (marg_order_pdf)
#    S561 (15-Oct-2026): both PDF buttons open a new address at every tap (?s=<the export's stamp>&t=<the moment>, the moment set
#    again by the click script); the two routes name the file by the export's time (the order sheet also by the print's) and send
#    Cache-Control no-store, max-age=0 / Pragma no-cache / Expires 0 -- a phone has no old copy of either paper it could reopen.
#    GET  /finance/porders/s454/maal                  Maal aaya? -- a card per order awaited: Bill scan karo · Bill nahi hai, ya kam aaya?
#    GET  /finance/porders/s454/maal/<order>          the arrival screen (not a required step); then "Bill abhi scan karna hai?"
#    GET  /finance/porders/s454/scan[?month=]         Bill scan karna hai -- by supplier, five at a time; Koi paper nahi mil raha?
#    GET  /finance/porders/s454/q[?month=]            Photo dekh kar bataiye -- one question on the screen
#    GET  /finance/porders/s454/purana/<yyyy-mm>      a parked month: optional, the same two rows for that month only
#    POST /finance/porders/api/s454/<action>          ordered · whatsapp · call · qty · reorder · arrive · later · pharmacy · vendor ·
#                                                     confirm · amount · paper_missing · setting (owner)
#    GET  /finance/porders/api/s454/state             the counts (the walk and the duty map read them)
#  S605_ORDER_FIXES (20-Oct-2026; F-961, F-962, the owner's numbers of 15:28 / 15:54 IST):
#    GET  /finance/porders/s454/order/whatsapp        WhatsApp bhejna hai? -- the suppliers order_sheet.wa_plan queues now, each with its
#                                                     numbers, those with no number; "Haan, WhatsApp bhejo" posts the list it showed (409
#                                                     when the list moved); its read writes nothing. "Sab ko WhatsApp bhejo" is a link to it.
#    The home keeps "Aaj ke order — call karo" (the Ho chuke rule) once nothing is left to order. Every dealer line of the order screens
#    carries "Call: <call> · WhatsApp: <wa>" (nums_text: the one builder of these words, for the screens and both PDFs).
#  S619_ORDER_TRACKER (22-Oct-2026): one order, five steps (order_track):
#    GET  /finance/porders/s454/late                  Order ka maal nahi aaya -- call karo: the late orders (and part orders), Call and Maal aaya
#    GET  /finance/porders/s454/track                 the order list -- the owner (English), porders.rescan_askers (Roman Hindi); writes nothing
#    The home's call row (late, order_track) replaces S605's 'Aaj ke order -- call karo'; Maal aaya lists the orders not arrived and not yet
#    late; the owner's / Shavez's home carries the order list's card instead of S618's separate 'Scans to redo' link; the remove asks a reason.
#  The owner's cards (who decides, the agreement line, the old pending orders, the sheet's state) and the settings card sit on the old
#  page (?old=1), for the owner only. No phone number is written anywhere but on a sender's own call screen and the reception phone's message.
#  S638_EXPIRY_WATCH (24-Oct-2026, F-1015): a late card of an order where NOTHING came names every awaited medicine with its quantity
#    (Shivani, 23-Oct: "SHIVAAZ 12-10 1 medicine" told her nothing); a part order's card is as it was. Nothing else on the page moves.
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


def _s937_js(v):
    """S937 (F-1619): a value written INSIDE a <script> element -- JSON, with & < > and the two JS line breaks as \\u escapes (the browser
    decodes no entity there; html.escape turned RADHA MEDICAL & SCIENTIFIC into '&amp;' and the WhatsApp-all list never matched)."""
    return (json.dumps(v, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


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
    "nonum": ("Number nahi hai — Dr sahab ko dijiye", "No number — give it to Dr Manoj"),     # S574 (switch ON): for nophone / nophone_l
    "num_call": ("Call: %s", "Call: %s"), "num_wa": ("WhatsApp: %s", "WhatsApp: %s"),            # S574 (switch ON): under the name
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
    "onebill": ("Ek scan mein ek hi bill.", "One bill per scan."), "save": ("Save kijiye", "Save"),     # S454 P3B (18.1, 18.2)
    "margopen": ("Marg mein khula order (%s) · %d supplier, %d dawa", "Marg's open order (%s) · %d suppliers, %d medicines"),   # S543 (D716)
    "margpdf": ("Marg ka order (PDF)", "Marg's order (PDF)"),
    "margband": ("Yeh order Marg mein band ho chuka hai.", "Marg has closed this order."),
    "margoff": ("Yeh line ab Marg ke order mein nahi hai.", "This line is no longer on Marg's order."),
    "r_call": ("Aaj ke order — call karo", "Today's orders — call"),                                    # S605 (F-962)
    "wa_q": ("WhatsApp bhejna hai?", "Send the WhatsApp?"), "wa_n": ("In %d supplier ko WhatsApp jayega", "These %d suppliers get a WhatsApp"),   # S605 (F-961)
    "wa_yes": ("Haan, WhatsApp bhejo", "Yes, send the WhatsApp"), "wa_back": ("Nahi, wapas", "No, back"),
    "wa_none": ("Abhi kisi supplier ko WhatsApp nahi jayega.", "No supplier gets a WhatsApp now."),
    "wa_nonum2": ("%s — number nahi hai, call kijiye.", "%s — no number, please call."),
    "darpan_haan": ("Darpan ki haan", "Darpan's yes"),
    "wa_unlock": ("WhatsApp khud khulega, har minute ek supplier (%d minute). Phone chalu aur mobile data on rakhiye.",      # S914
                  "WhatsApp opens by itself, one supplier a minute (%d minutes). Keep the phone on and its mobile data on."),
}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def L(en, k, *a):
    s = T[k][1 if en else 0]
    s = (s % a) if a else s
    if en:                                                    # S454 P1C (17.5): "1 medicine", "1 supplier", "1 bill" -- never "1 medicines"
        s = re.sub(r"(?<![\d,])1 (medicine|supplier|bill)s\b", r"1 \1", s)
    return s


def nums_text(call, wa, en=False, missing=None):
    """S605 (the owner, 20-Oct 15:28 / 15:54 IST): 'Call: <call> · WhatsApp: <wa>' from book_card's two numbers -- the ONE builder of these
    words for the screens and both PDFs. missing=None (the screens): a number that is not there is left out ('' when neither is); missing=
    <sentence> (the PDFs): a missing number prints its own label with that sentence, both missing print the sentence alone."""
    if missing is not None and not call and not wa:
        return missing
    parts = []
    for k, v in (("num_call", call), ("num_wa", wa)):
        if v:
            parts.append(L(en, k, v))
        elif missing is not None:
            parts.append(L(en, k, missing))
    return " · ".join(parts)


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
.red{color:#8c1d18;font-weight:700}.grn{color:#1f4d25;font-weight:700}.amb{color:#8a5300;font-weight:700}
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
FRESH_JS = ("<script>document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-fresh]');"
            "if(a){var u=new URL(a.href);u.searchParams.set('t',Date.now());a.href=u.href;}},true);</script>")   # S561: the tap's own moment


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
    """S619: the orders not arrived and not yet late (order_track's light half) -- the late ones are on the call row ('Order ka maal nahi aaya')."""
    out = []
    for s in _s619_ot().awaited(con, OS.now()):
        o = dict(con.execute("SELECT * FROM purchase_order WHERE id=?", (s["id"],)).fetchone())
        o["n"] = s["n"]
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
                        intake=intake(b["vendor"], back=P + "/s454/scan" + ("?month=" + month if month else ""))))   # S454 (5): the line's supplier only
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
                scan=len(scan_lines(con)), q=len(questions(con)), rescan=_s618_open_count(con) + _s708_papers(con),      # S618 + S708
                late=_s619_late_n(con))                         # S619: Order ka maal nahi aaya -- call karo


def _s708_papers(con):
    """S708: the papers never scanned that the owner or Shavez sent to reception (still needed) -- on reception's row with the rescans."""
    try:
        import order_track_page as OTP                        # noqa: PLC0415
        return OTP.open_paper_count(con)
    except Exception:                                         # noqa: BLE001
        return 0


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
    if _s618_doer(con, str(login).lower()):                   # S736 (D847): the server asks reception for a rescan by itself -- on reception's home
        _s736_raise_soft(con)
    c = counts(con)
    nm = ""
    try:
        S441 = _po().S441
        if S441 is not None and S441.is_shared_login(login):
            nm = S441.who_name(request.cookies) or ""
    except Exception:                                         # noqa: BLE001
        pass
    h = ['<div class="sig">%s</div>' % esc(L(en, "signed", login + ((" · " + nm) if nm else ""))), "<h1>%s</h1>" % L(en, "home"),
         '<a class="big" id="scannew" href="%s">📷 %s</a>' % (esc(intake(back=P)), L(en, "scan_new")),
         '<div class="mut onebill" style="text-align:center;margin-top:-4px">%s</div>' % L(en, "onebill")]      # S454 P3B (18.1, F-712)
    rows = (("order", P + "/s454/order", "r_order"), ("late", P + "/s454/late", "r_late"), ("maal", P + "/s454/maal", "r_maal"),   # S619: the call row
            ("scan", P + "/s454/scan", "r_scan"), ("q", P + "/s454/q", "r_q"))
    s736_ok = False
    if _s618_doer(con, str(login).lower()):                   # S736 (D847): the reception logins -- ONE row, Aaj ka bill kaam (rescans, papers,
        c, s736_ok = _s736_home(con, c)                       # bills to scan, bill questions); Photo dekh kar bataiye keeps the other questions
        if s736_ok:
            rows = rows[:3] + (("billkaam", P + "/s454/billkaam", "r_billkaam"), ("q", P + "/s454/q?nobill=1", "r_q"))
    if not s736_ok and c.get("rescan") and _s618_doer(con, str(login).lower()):   # S618: Phir se scan karo, directly above Bill scan karna hai -- the reception logins only
        rows = rows[:3] + (("rescan", P + "/s454/rescan", "r_rescan"),) + rows[3:]
    any_ = False
    for k, href, lab in rows:
        if c.get(k, 0) > 0:                                   # S619: the call row stands on its own (S605's 'Aaj ke order -- call karo' retired)
            any_ = True
            h.append('<a class="row" id="row_%s" href="%s"><span class="n">%d</span><span class="l">%s</span><span>›</span></a>' % (k, href, c[k], L(en, lab)))
    if not any_:
        h.append('<div class="ok" id="alldone"><div class="t">%s</div><div>%s</div></div>' % (L(en, "done"), L(en, "done2")))
    for m, _c in parked_with_work(con):
        h.append('<div class="lnk"><a id="park_%s" href="%s/s454/purana/%s">%s</a></div>' % (m, P, m, L(en, "purana", month_name(m))))
    if _s618_asker(con, kind, _s618_login(u, login)):          # S619: the order list's card -- the one way in (Scans to redo is a section of it)
        h.append(_s619_track_card(con, en))
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
        sub, am = sub + " · " + L(en, "nonum" if e.get("book_on") else "nophone"), True      # S574
    elif e.get("called"):
        sub, am = sub + " · " + L(en, "called"), True
    q = quote(e["sn"], safe="")
    btn = ('<button class="g" onclick="s454(\'%s/api/s454/ordered\',{sn:%s})">%s</button>' % (P, esc(json.dumps(e["sn"])), L(en, "ordered")))
    nt = nums_text(e.get("phone"), e.get("wa"), en)            # S605: the phone book's two numbers, named (a sender's / the owner's page)
    nums = ('<div class="sb nums">%s</div>' % esc(nt)) if nt else ""
    return ('<div class="card" data-sn="%s"><div><div class="nm">%s</div>%s<div class="sb%s">%s</div></div><div class="two"><a class="b" href="%s/s454/order/%s">%s</a>%s</div></div>'
            % (esc(e["sn"]), esc(e["vendor"]), nums, " am" if am else "", esc(sub), P, q, L(en, "open"), btn))


def _s593_counts(es):
    """S593 (F-739, charter 8 / 13): the heading counts the cards' own list LESS a card that is only S403's orthotic shortage, and the
    medicine lines only (a mixed card -- a supplier with both -- counts once, with its medicine lines). entries() hands sources as a list."""
    med = [e for e in es if set(e.get("sources") or []) != {"ortho"}]
    return len(med), sum(1 for e in med for l in e["lines"] if l.get("src") != "ortho")


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
    oo = OS.open_order(con)                                   # S543 (D716): Marg's open order heads the page, on every source
    margopen = ('<div class="mut" id="margopen">%s</div>' % esc(L(en, "margopen", oo["stamp_text"], oo["suppliers"], oo["count"]))) if oo["count"] else ""
    if src == "marg_sheet":
        h.append(margopen)
    elif src == "system":
        nsup, nmed = _s593_counts(es)                         # S593 (F-739): the medicine cards, less the orthotic-only card
        h.append('<div class="mut" id="whose">%s</div>' % esc(L(en, "whose", L(en, "system"), OS.today().strftime("%d-%m"), nsup, nmed)))
    elif src == "darpan":                                     # S485 (D677): the system's list, as Darpan made it pakka on his page
        nsup, nmed = _s593_counts(es)                         # S593 (F-739)
        h.append('<div class="mut" id="whose">%s</div>' % esc(re.sub(r"(?<![\d,])1 (medicine|supplier)s\b", r"1 \1",
                 ("Darpan's confirmed list · %s · %d suppliers, %d medicines" if en else "Darpan ki pakki list · %s · %d supplier, %d dawa")
                 % (OS.today().strftime("%d-%m"), nsup, nmed))))
    if src != "marg_sheet":
        h.append(margopen)
    done_all = _done_today(con)                               # S593 (F-916, D743): the page's CONDITIONS read every done order; the block below filters
    wa = [d for d in done_all if d["via"] in ("whatsapp", "whatsapp+call")]
    if wa:
        last = max(wa, key=lambda d: d["sent_at"] or "")
        h.append('<div class="ok" id="wagone"><div class="t">%s</div><div>%s</div></div>'
                 % (L(en, "wa_went", len(wa)), esc(L(en, "wa_who", OS.ddmm(last["sent_at"]), _hm(last["sent_at"]), last["by"] or ""))))
    nwait = _s605_waiting(con)
    if nwait:                                                 # S605 (F-961): while the day's order messages wait for the phone
        h.append('<div class="ok" id="waunlock"><div class="t">%s</div></div>' % esc(L(en, "wa_unlock", nwait)))
    alive, _why = OS.phone_state(con)
    if pend:
        if alive:                                             # S605 (F-961): the confirm screen first -- no POST from here
            h.append('<a class="big" id="waall" href="%s/s454/order/whatsapp">%s</a>' % (P, L(en, "wa_all")))
        else:
            h.append('<button class="big" id="waall" disabled>%s</button>' % L(en, "wa_all"))
        if not alive:
            h.append('<div class="mut" id="waoff">%s</div>' % esc(_s702_waoff(con, en, _why)))   # S702 (F-1089): why, in words
            con.execute("INSERT INTO setting (key, value, note) VALUES ('s454.phone_off_met', ?, 'S454: when someone last met the disabled WhatsApp button') "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("%s %s" % (OS.now_iso(), who(u)),))   # the owner hears of it once met
            con.commit()
    if pend or oo["count"]:                                   # S543 (R2-11): both papers whenever Marg's open order has a line
        fq = _fresh_q(con)                                    # S561: a new address at every tap -- the export's stamp, the moment
        h.append('<a class="big out" id="print" href="%s" data-fresh="1" target="_blank">%s</a>' % (esc(P + "/s454/sheet.pdf?" + fq), L(en, "print")))
        h.append('<a class="big out" id="margpdf" href="%s" data-fresh="1" target="_blank">%s</a>' % (esc(P + "/s454/marg.pdf?" + fq), L(en, "margpdf")))
        h.append(FRESH_JS)
    if pend:
        h.append('<div class="mut">%s</div>' % L(en, "callnote"))
    if done_all or line:
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
    pend_sn = {e["sn"] for e in pend}                         # S593 (F-916, D743): a supplier with a card above is not repeated under 'Ho chuke'
    done = [d for d in done_all if d["sn"] not in pend_sn]
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
            mark = L(en, word)
            if OS.ddmm(d["sent_at"]) != OS.ddmm(OS.now_iso()):   # S593 (F-916): a done line of an earlier day says its own date
                mark = "%s · %s" % (esc(OS.ddmm(d["sent_at"])), mark)
            nt = nums_text(d["phone"], d.get("wa"), en)          # S605: the phone book's two numbers, named
            h.append('<div class="ln"><div class="t"><div class="a">%s</div><div class="s grn">✓ %s</div>%s</div>%s</div>'
                     % (esc(d["vendor"]), mark, ('<div class="s nums">%s</div>' % esc(nt)) if nt else "", callb))
    if not pend and not line and not done_all:
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
        call, wa, _shown, _on = OS.book_card(con, o["vendor"])  # S613: the phone book's one reader (S574) -- the Calls and the Order WhatsApp number
        out.append(dict(id=o["id"], vendor=o["vendor"], sn=o.get("supplier_norm") or _pa().supplier_key(o["vendor"]), via=o.get("order_via") or "",
                        sent_at=sent_at, by=o.get("created_by") or "", phone=call, wa=wa))
    return out


def _s702_waoff(con, en, why):
    """S702 (F-1089): the disabled WhatsApp button says WHY -- since when the reception phone has been silent (or refused); with no key,
    the old words.  The phone's last ask is supplier_msg.phone_last ('<when> <code>'), written by the queue door."""
    if why != "silent":
        return L(en, "wa_off")
    raw = str(OS.setting(con, "supplier_msg.phone_last", "") or "")
    at, _sp, code = raw.partition(" ")
    d = OS._dtm(at)
    if d is None:
        return L(en, "wa_off")
    when = d.strftime("%d-%m %H:%M")
    if code and code != "200":
        return ("The reception phone asked at %s and was refused (%s) \u2014 tell the doctor; order by call meanwhile" % (when, code) if en else
                "Reception phone ne %s par poocha par mana ho gaya (%s) \u2014 Doctor sahab ko bataiye; tab tak call se order kijiye" % (when, code))
    return ("The reception phone has been silent since %s \u2014 keep it on with its mobile data on, and MacroDroid not force-stopped; order by call meanwhile" % when
            if en else
            "Reception phone %s se chup hai \u2014 phone chalu aur mobile data on rakhiye, MacroDroid band mat kijiye; tab tak call se order kijiye" % when)


def _s605_waiting(con):
    """S605 (F-961): today's order messages still waiting for the reception phone (queued -- handed or not -- with a number)."""
    try:
        return int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status='queued' AND to_number IS NOT NULL AND substr(queued_at,1,10)=?",
                               (OS.now().date().isoformat(),)).fetchone()[0])
    except sqlite3.Error:
        return 0


def wa_confirm_page():
    """S605 (F-961): 'WhatsApp bhejna hai?' -- the suppliers order_sheet.wa_plan would queue now (each with its line count and numbers), those
    with no number, those to call; 'Haan, WhatsApp bhejo' posts the list it showed. Its read writes nothing (no _every_read)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    back = P + "/s454/order"
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return shell(con, u, L(en, "wa_q"), '<div class="err">%s</div>' % L(en, "frozen"), back=back, login=login)
    alive, _why = OS.phone_state(con)
    if not alive:
        return shell(con, u, L(en, "wa_q"), '<div class="mut" id="waoff">%s</div><a class="more" id="waback" href="%s">%s</a>' % (esc(_s702_waoff(con, en, _why)), back, L(en, "wa_back")),
                     back=back, login=login)
    q, nonum, call = OS.wa_plan(con)
    h = []
    if q:
        h.append('<h1 id="wan">%s</h1>' % esc(L(en, "wa_n", len(q))))
        for e in q:
            n = len(e["lines"])
            sub = L(en, "dawa", n) + ((" (%s)" % L(en, "darpan_haan")) if "ortho" in (e.get("sources") or []) else "")
            nt = nums_text(e.get("phone"), e.get("wa"), en) if kind in ("owner", "sender") else ""
            h.append('<div class="card" data-sn="%s"><div class="nm">%s</div><div class="sb">%s</div>%s</div>'
                     % (esc(e["sn"]), esc(e["vendor"]), esc(sub), ('<div class="sb nums">%s</div>' % esc(nt)) if nt else ""))
    else:
        h.append('<div class="ok" id="wanone"><div class="t">%s</div></div>' % L(en, "wa_none"))
    for e in nonum:
        h.append('<div class="mut am" data-nonum="%s">%s</div>' % (esc(e["sn"]), esc(L(en, "wa_nonum2", e["vendor"]))))
    for e in call:
        h.append('<div class="mut am" data-call="%s">%s — %s</div>' % (esc(e["sn"]), esc(e["vendor"]), L(en, "wa_no")))
    if q:
        h.append('<button class="big" id="wayes" onclick="s605wa()">%s</button>' % L(en, "wa_yes"))
        h.append("<script>function s605wa(){fetch('%s/api/s454/whatsapp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sns:%s})})"
                 ".then(function(r){return r.json().then(function(j){return [r,j];});}).then(function(x){var r=x[0],j=x[1];"
                 "if(r.ok&&j.ok){location.href='%s';return;}var m=document.getElementById('msg');m.textContent=j.message||j.error||('HTTP '+r.status);m.style.display='block';"
                 "if(j.error==='list_changed'){setTimeout(function(){location.reload();},1500);}}).catch(function(e){var m=document.getElementById('msg');"
                 "m.textContent=String(e);m.style.display='block';});}</script>" % (P, _s937_js([e["sn"] for e in q]), back))          # S937: JSON for a <script>, never html.escape
    h.append('<a class="more" id="waback" href="%s">%s</a>' % (back, L(en, "wa_back")))
    return shell(con, u, L(en, "wa_q"), "".join(h), back=back, login=login)


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
            q = OS.qty_of(l, en, con=con)                     # S543: qty_words, the shop's one nomenclature
            if edit and l["src"] != "draft":
                b = esc(json.dumps(dict(src=l["src"], ref=l["ref"], item=l["item"])))
                ctl = ('<span class="qbox"><button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:-1}))">−</button><b>%d</b>'
                       '<button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:1}))">+</button></span>'
                       % (P, b, int(l["qty"]), P, b)) + _s619_remove_chips(en, b)           # S619: the one remove door asks a reason
                items.append('<div class="li" style="flex-wrap:wrap"><span class="i">%s%s</span>%s</div>' % (esc(l["item"]), _s619_carry_tag(en, l), ctl))
            else:
                items.append('<div class="li"><span class="i">%s%s</span><span class="q">%s</span></div>' % (esc(l["item"]), _s619_carry_tag(en, l), esc(q)))
        h.append('<div class="list" id="lines">%s</div>' % "".join(items))
        if e["has_phone"]:
            if e.get("book_on"):                              # S574: the Calls number and the Order WhatsApp number, to read only
                nums = ('<div class="num" id="numcall">%s</div><div class="num" id="numwa">%s</div>'
                        % (esc(L(en, "num_call", e["phone"])), esc(L(en, "num_wa", e["wa"]))))
            else:
                nums = "".join('<div class="num">%s</div>' % esc(x) for x in e["shown"])
            h.append('<div><a class="big blue" id="callkaro" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">📞 %s</a>%s</div>'
                     % (esc(_tel(e["phone"])), P, esc(json.dumps(e["sn"])), L(en, "callkaro"), nums))
            h.append('<div class="mut" style="text-align:center">%s</div>' % L(en, "baat"))
        else:
            h.append('<div class="mut" id="nophone">%s</div>' % L(en, "nonum" if e.get("book_on") else "nophone_l"))   # S574
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
    """S543: the old group's lines -- Marg's pending quantity, the day (an order made here: its day), the one word in one colour, and
    'Dobara order karo' only where its door accepts the line (OS.can_reorder)."""
    rows = []
    for l in olds:
        w = OS.old_word(l, en)
        btn = ('<button class="sm" onclick="s454(\'%s/api/s454/reorder\',{line:%d})">%s</button>' % (P, l["id"], L(en, "reorder"))) if OS.can_reorder(l) else ""
        rows.append('<div class="ol" data-line="%d"><div class="r1"><span class="i">%s</span><span class="q">%s</span></div><div class="r2"><span class="w">'
                    '<span class="mut">%s</span><span class="amb">%s</span></span>%s</div></div>'
                    % (l["id"], esc(l["item"]), esc(OS.qty_of(l, en, pend=True)), L(en, "orderdate", OS.ddmm(OS.old_day(l))), esc(w), btn))
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
                 '<div class="mut onebill" style="text-align:center">%s</div>'                     # S454 P3B (18.1, F-712)
                 '<div class="lnk"><a href="%s/s454/maal/%d">%s</a></div></div>'
                 % (o["id"], esc(o["vendor"]), esc(L(en, "orderN", OS.ddmm(o["created_at"]), o["n"])),
                    esc(intake(o["vendor"], back=P + "/s454/maal")), L(en, "billscan"), L(en, "onebill"), P, o["id"], L(en, "nobill")))
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
    if OS.marg_closed_order(con, o):                          # S543 (R1-17, R3-16): an awaited order Marg has closed is not arrived here
        return shell(con, u, L(en, "r_maal"), '<div class="err" id="margband">%s</div><a class="more" href="%s/s454/maal">%s</a>'
                     % (L(en, "margband"), P, L(en, "back")), back=P + "/s454/maal", login=login)
    lines = [dict(l) for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id=? ORDER BY id", (oid,))]
    h = ['<h1>%s</h1>' % esc(o["vendor"]), '<div class="mut">%s · %s</div>' % (L(en, "orderdate", OS.ddmm(o["created_at"]))[:-3], L(en, "tapshort"))]
    rows = []
    sheet = OS.sheet_lines_of_order(con, oid)                 # S543: the sheet line's packing, for qty_words
    for l in lines:
        ql = dict(item=l["item"], qty=int(l["packs"] or 0), loose=0, strip=1 if int(l["pack_size"] or 1) > 1 else 0, pack_size=int(l["pack_size"] or 1),
                  packing=((sheet.get(l["item"]) or {}).get("packing") or ""))
        qt = OS.qty_of(ql, en, con=con)
        rows.append('<div class="ar" data-line="%d" onclick="arTap(%d)"><span id="ic%d">✓</span><span class="i">%s</span><span class="q">%s</span></div>'
                    '<div id="ch%d" style="display:none;padding:0 0 10px"><div class="chips"><button onclick="arHow(%d,\'short\')" id="b_short_%d">%s</button>'
                    '<button onclick="arHow(%d,\'missing\')" id="b_missing_%d">%s</button><button onclick="arHow(%d,\'ok\')" id="b_ok_%d">%s</button></div>'
                    '<div class="qbox" id="kq%d" style="display:none;margin-top:8px"><span>%s</span><input class="kq" type="number" min="0" max="%d" id="kv%d"> <span>%s</span></div></div>'
                    % (l["id"], l["id"], l["id"], esc(l["item"]), esc(qt), l["id"], l["id"], l["id"], L(en, "kam"), l["id"], l["id"], L(en, "nahimila"),
                       l["id"], l["id"], L(en, "aagaya"), l["id"], L(en, "kitna"), max(0, int(l["packs"]) - 1), l["id"],
                       esc(OS.unit_word(ql, en, con=con))))
    h.append('<div class="list">%s</div>' % "".join(rows))
    h.append('<button class="big" id="maalok" data-ok="%s" data-save="%s" onclick="arSave()">%s</button>'      # S454 P3B (18.2): "Save kijiye" while
             % (esc(L(en, "maal_ok")), esc(L(en, "save")), L(en, "maal_ok")))                         # a line is short or missing
    h.append('<div class="lnk"><a id="abhinahi" href="%s/s454/maal">%s</a></div>' % (P, L(en, "abhinahi")))
    h.append("""<script>
var HOW={};
function arTap(id){var c=document.getElementById('ch'+id);c.style.display=(c.style.display==='none'?'block':'none');}
function arHow(id,how){HOW[id]=how;['short','missing','ok'].forEach(function(k){document.getElementById('b_'+k+'_'+id).className=(k===how?'on':'');});
 document.getElementById('kq'+id).style.display=(how==='short'?'flex':'none');document.getElementById('ic'+id).textContent=(how==='ok'?'✓':'!');arLabel();}
function arLabel(){var b=document.getElementById('maalok'),s=false;for(var k in HOW){if(HOW[k]==='short'||HOW[k]==='missing'){s=true;}}b.textContent=b.getAttribute(s?'data-save':'data-ok');}
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
    if request.args.get("nobill") == "1" and not month:      # S736: reception's home row -- the bill questions are on Aaj ka bill kaam
        qs = [q for q in qs if q["kind"] != "bill"]
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


@bp.route(P + "/s454/order/whatsapp")
def r_wa_confirm():
    return wa_confirm_page()                                  # S605 (F-961): a static rule, matched before the supplier's


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


# ------------------------------------------------------------------ S561: the two papers, fresh at every tap
STAMP_RE = re.compile(r"^(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)")         # the export's capture stamp, as order_sheet._stamp_text reads it


def _export(con):
    """(newest sheet, its stamp) -- the stamp ('20261015-141250', written by marg_watch / marg_router) only when it has that shape, else ''."""
    ns = OS.newest_sheet(con)
    st = str((ns or {}).get("stamp") or "")
    return ns, (st if STAMP_RE.match(st) else "")


def _fresh_q(con):
    """The query both PDF buttons carry: s = the newest export's stamp ('' when it has none), t = the server's moment (YYYYMMDDHHMMSS)."""
    return "s=%s&t=%s" % (quote(_export(con)[1]), OS.now().strftime("%Y%m%d%H%M%S"))


def _pdf_name(kind, st, n):
    """The file name: the export's dd-mm_HHMM from its stamp (no stamp: the print's), and for the order sheet the print's HHMMSS too."""
    m = STAMP_RE.match(st or "")
    base = ("%s-%s_%s%s" % (m.group(3), m.group(2), m.group(4), m.group(5))) if m else n.strftime("%d-%m_%H%M")
    return ("order_sheet_%s_%s.pdf" % (base, n.strftime("%H%M%S"))) if kind == "sheet" else ("marg_order_%s.pdf" % base)


def _pdf_headers(name):
    return {"Content-Type": "application/pdf", "Cache-Control": "no-store, max-age=0", "Pragma": "no-cache", "Expires": "0",
            "Content-Disposition": 'inline; filename="%s"' % name}


@bp.route(P + "/s454/sheet.pdf")
def r_sheet_pdf():
    """The printed order sheet -- always the newest sheet; s and t only make the address new (S561)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import order_sheet_pdf                                    # noqa: PLC0415
    n = OS.now()                                              # S561: one clock, the print's moment (never OS.today(), which follows ORDER_TODAY)
    name = _pdf_name("sheet", _export(con)[1], n)
    data = order_sheet_pdf.build(con, now=n)
    OS.audit(con, who(u), "s454_sheet_printed", "", dict(bytes=len(data), file=name))
    con.commit()
    return data, 200, _pdf_headers(name)


@bp.route(P + "/s454/marg.pdf")
def r_marg_pdf():
    """S543 (D716): Marg's own PENDING ORDERS export, printed as Marg printed it -- beside the system's sheet, to compare. S561: named by
    the export's time; s and t only make the address new."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    import marg_order_pdf                                     # noqa: PLC0415
    n = OS.now()
    ns, st = _export(con)
    name = _pdf_name("marg", st, n)
    data = marg_order_pdf.build(con)
    OS.audit(con, who(u), "s454_marg_pdf_printed", (ns or {}).get("id", ""), dict(bytes=len(data), sheet=(ns or {}).get("id"), file=name))
    con.commit()
    return data, 200, _pdf_headers(name)


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
    b, code = OS.whatsapp_all(con, who(u), expect=[str(x) for x in (_body().get("sns") or [])])   # S605 (F-961): 409 when the list moved
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
    if src not in ("sheet", "proposal", "ortho", "carry", "s778"):     # S619: + a carried line; S778: + a line put on a card by S778
        return jsonify(ok=False, error="bad_line"), 400
    e = next((x for x in OS.entries(con) for l in x["lines"] if l["src"] == src and l["ref"] == ref and l["item"] == item), None)
    if not e:
        return jsonify(ok=False, error="gone", message="Yeh line ab order mein nahi hai."), 409
    l = next(l for l in e["lines"] if l["src"] == src and l["ref"] == ref and l["item"] == item)
    reason = str(b.get("reason") or "")
    if b.get("remove"):                                       # S619: a reason on the one remove door -- only on a card with no draft yet
        if e.get("draft") or e.get("state") != "pending":
            return jsonify(ok=False, error="has_draft", message="Is supplier ka order ban chuka hai — ab line nahi hat sakti."), 409
        if reason not in ("dealer_no", "not_now"):
            return jsonify(ok=False, error="reason_needed", message="Wajah chuniye: Dealer ke paas nahi hai / Abhi nahi chahiye."), 400
    if b.get("remove"):
        if src == "sheet":
            r = con.execute("SELECT reorder_day, kind FROM order_sheet_line WHERE id=?", (int(ref),)).fetchone()
            if r and r[0]:
                con.execute("UPDATE order_sheet_line SET state='old', reorder_day=NULL, updated_at=? WHERE id=?", (OS.now_iso(), int(ref)))
                OS.audit(con, who(u), "s454_reorder_undone", ref, dict(item=item))
                con.commit()
                return jsonify(ok=True, back_to_old=True)
        con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at, reason) VALUES (?,?,?,?,1,?,?,?) ON CONFLICT(src, ref, item) DO UPDATE SET "
                    "removed=1, by=excluded.by, at=excluded.at, reason=excluded.reason", (src, ref, item, None, who(u), OS.now_iso(), reason))
        if src == "carry":                                    # S619: a carried line removed (either reason) is dropped
            con.execute("UPDATE order_carry SET dropped_at=?, dropped_by=? WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (OS.now_iso(), who(u), int(ref)))
        OS.audit(con, who(u), "s454_line_removed", ref, dict(src=src, item=item, reason=reason))
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
    """Dobara order karo -- an old pending line becomes a new line of today's order (counted from today). S543 (charter 13): only a line
    on Marg's open order, and only where the old block shows the button (OS.can_reorder) -- never a line ordered here."""
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    try:
        lid = int(_body().get("line") or 0)
    except (TypeError, ValueError):
        lid = 0
    l = next((x for x in OS.open_order(con)["lines"] if x["id"] == lid), None)
    if l is None:
        return jsonify(ok=False, error="not_on_marg", message=L(False, "margoff")), 409
    if not OS.can_reorder(l):
        return jsonify(ok=False, error="not_old", message="Yeh line purane pending mein nahi hai."), 409
    r = (l["id"], l["state"], l["item"])
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
    if OS.marg_closed_order(con, dict(con.execute("SELECT * FROM purchase_order WHERE id=?", (oid,)).fetchone())):   # S543 (R1-17)
        return jsonify(ok=False, error="marg_closed", message=L(False, "margband")), 409
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
    if key in ("porders.simple", "order.sheet_print_old", "order.carry_on_card"):   # S820: + the carry switch
        return v in ("0", "1"), v
    if key == "order.source":
        return v in ("marg_sheet", "system", "darpan"), v       # S485 (D677)
    if key == "purchase.entry_mode":                          # S454 P2 (6): paper, or both; digital is not built
        return v in ("paper", "both"), v
    if key == "order.stock_basis":                            # S454 P3 (9.2)
        return v in ("count", "marg"), v
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
    if key == "order.deliver_skip":                           # S619: the five settings of the order list
        ds = [x.strip().upper() for x in v.split(",") if x.strip()]
        return all(x in ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN") for x in ds), ",".join(ds)
    if key == "order.deliver_window":
        parts = [x.strip() for x in v.split(",") if x.strip()]
        return bool(parts) and all(re.match(r"^(\d{1,2}:\d\d)?-(\d{1,2}:\d\d)?$", x) for x in parts), ",".join(parts)
    if key == "order.wa_delivery_line":
        return 0 < len(v) <= 200 and not re.search(r"\d{7,}", v), v
    if key == "order.track_since":
        return bool(re.match(r"^\d{4}-\d\d-\d\d$", v)), v
    lim = {"order.sheet_max_age_days": (1, 60), "order.whatsapp_wait_min": (5, 600),
           "order.phone_alive_min": (5, 1440), "supplier_msg.handout_gap_min": (1, 120), "purchase.arrival_scan_days": (1, 60),
           "purchase.unread_pair_days": (1, 60), "purchase.total_noise_rs": (0, 100), "purchase.scan_wait_days": (1, 30),
           "purchase.entry_wait_days": (1, 60), "stock.gap_min_packs": (0, 100), "order.deliver_days": (0, 7)}.get(key)
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
    if key in _s470_keys():                                   # S470 (B.8): the engine's six settings
        return _s470_set(con, u, key, b.get("value"))
    if key not in OS.SETTINGS:
        return jsonify(ok=False, error="bad_key"), 400
    ok, v = _valid(key, b.get("value"))
    if not ok:
        if key == "purchase.entry_mode" and str(b.get("value") or "").strip() == "digital":
            return jsonify(ok=False, error="not_built", message="purchase.entry_mode: 'digital' is not built yet -- scans go into Marg's digital "
                                                                "entry without Amir only in a later kit. Choose paper or both."), 400
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
    s485 = {"marg_sheet": ("Darpan's Marg order sheet", "Change to Darpan's sheet",
                           "The system's own list is worked out every order day but is shown to no staff."),
            "system": ("The system's own list", "Change to the system's own list",
                       "Darpan's sheet, when one arrives, is compared and shown to you only."),
            "darpan": ("The system's list, confirmed by Darpan on his page", "Change to Darpan confirming the system's list",
                       "Darpan sees the system's list on his own page from the list time and taps Pakka; reception orders what he confirmed. "
                       "His Marg sheet, when one arrives, is compared and shown to you only.")}   # S485 (D677): three values, one tap to any other
    h.append('<div %s id="s454src"><b>Who decides the order</b> · %s %s<div style="color:#666;font-size:13px">%s</div></div>'
             % (st, s485[src][0], "".join('<button onclick="s454set(\'order.source\',\'%s\')" style="min-height:40px">%s</button> ' % (k, s485[k][1])
                                          for k in ("marg_sheet", "system", "darpan") if k != src), s485[src][2]))
    h.append(_s470_card(con, st))                              # S470 (D): the weekly line; no-supplier; a family; the source
    ns = OS.newest_sheet(con)
    if ns and ns.get("cmp"):
        c = json.loads(ns["cmp"])
        if "x" in c:
            rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(r["item"]), esc(r["sheet"]), esc(r["system"])) for r in c["both"])
            h.append('<div %s id="s454cmp"><b>Orders of %s: the system agreed on %d of %d items with Darpan\'s sheet</b> <span id="s454basis">%s</span>'
                     '<details><summary>the three lists</summary><table style="width:100%%;font-size:14px"><tr><th>On both</th><th>Darpan ordered</th><th>System\'s list</th></tr>%s</table>'
                     '<p>Only on Darpan\'s sheet (%d): %s</p><p>Only on the system\'s list (%d): %s</p></details></div>'
                     % (st, esc(OS.dmy(ns["newest_date"])), c["x"], c["y"], esc(_s454_basis_words(c)), rows, len(c["only_sheet"]), esc(", ".join(r["item"] for r in c["only_sheet"])),
                        len(c["only_system"]), esc(", ".join("%s %s" % (r["item"], r["system"]) for r in c["only_system"]))))
    allold = OS.old_lines(con)                                 # S543: Marg's open order, its old group -- what the staff see
    if allold:
        by = {}
        for l in allold:
            by.setdefault(l["supplier"], []).append(l)
        oldest = min(OS.old_day(l) for l in allold)
        lst = "".join("<li><b>%s</b>: %s</li>" % (esc(k), esc("; ".join("%s %s · %s" % (l["item"], OS.dmy(OS.old_day(l)), OS.old_word(l, True)) for l in v)))
                      for k, v in sorted(by.items()))
        h.append('<div %s id="s454old"><b>Older lines still open in Marg\'s order: %d</b><div style="color:#666;font-size:13px">'
                 'The oldest is of %s. A line leaves when Marg stops printing it.</div><details><summary>by supplier</summary><ul>%s</ul></details></div>'
                 % (st, len(allold), esc(OS.dmy(oldest)), lst))
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
    rows.extend(_s470_setting_rows(con))                       # S470 (B.8): the engine's six settings on the same card
    h.append(_s454_gap_card(con, st))                          # S454 P3 (7.5): Marg and the shelf figure
    h.append(phone_card(con, st))                              # S454 P1C (17.7): the reception phone's state and a test message
    h.append('<details %s id="s454settings"><summary><b>Settings (S454)</b></summary><table style="width:100%%;font-size:14px">%s</table></details>' % (st, "".join(rows)))
    h.append("""<script>function s454set(k,v){fetch('/finance/porders/api/s454/setting',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k,value:v})})
.then(function(r){return r.json();}).then(function(j){if(!j.ok){var d=document.getElementById('s454settings'),e=document.createElement('div');
e.style.color='#a61b1b';e.textContent='Not saved \u2014 '+(j.message||j.error);if(d)d.appendChild(e);return;}location.reload();});}</script>""")   # S921 (F-1464): no dialog on his page
    h.append('<div style="margin:6px 0"><a href="/finance/porders">← the new screen</a></div></div>')
    return "".join(h)


# ==========================================================================================================================================
# S454 part 1C (17.7): THE OWNER'S "RECEPTION PHONE" CARD on the old page -- when the phone last asked, the messages waiting (orders,
# payments), the test number (masked), "Send a test message", the last test's state in IST. The key is never on it.
#    POST /finance/porders/api/s454/test_number {number}     the owner only; the number never reaches a log or the audit
#    POST /finance/porders/api/s454/test_send                the owner only; one message of kind 'test'
# ==========================================================================================================================================
def _when(iso):
    d = OS._dtm(iso)
    return d.strftime("%d-%m %H:%M") if d else ""


def phone_card(con, st):
    """S898: the S454 card, with the phone's last 'sent' report and the messages it took and never reported. Fail-soft."""
    h = _s454_phone_card(con, st)
    try:
        h = h[:h.rindex("</div>")] + _s898_block(con) + "</div>"
    except Exception:                                         # noqa: BLE001 -- the card never waits on its new part
        pass
    return h


def _s898_block(con):
    import supplier_msg as SM                                 # noqa: PLC0415
    done = SM.s898_last_done(con)
    rows = SM.s898_stuck(con)
    h = ['<div id="s898" style="margin-top:10px;border-top:1px solid #ccc;padding-top:8px">',
         '<div>Last "sent" report from the phone: <b>%s</b></div>' % esc(SM._s898_ddmm(done) if done else "never")]
    if rows:
        ids = [r["id"] for r in rows]
        h.append('<div style="margin-top:6px"><b>Taken by the phone, never reported: %d</b> '
                 '<span style="color:#666;font-size:13px">-- they may have gone. Send again, or remove from every list (kept on record).</span></div>' % len(rows))
        h.append('<div style="margin:6px 0"><button style="min-height:36px" onclick="s898t(this,\'resend\',%s)">Send all %d again</button> '
                 '<button style="min-height:36px" onclick="s898t(this,\'remove\',%s)">Remove all %d</button></div>'
                 % (json.dumps(ids), len(rows), json.dumps(ids), len(rows)))
        h.append('<table style="border-collapse:collapse;font-size:14px"><tr><th align="left">Dealer</th><th align="left">What</th>'
                 '<th align="left">Taken by the phone</th><th></th></tr>')
        for r in rows:
            h.append('<tr><td style="padding:3px 8px 3px 0">%s</td><td style="padding:3px 8px">%s%s</td><td style="padding:3px 8px">%s</td>'
                     '<td><button onclick="s898t(this,\'resend\',[%d])">Send again</button> <button onclick="s898t(this,\'remove\',[%d])">Remove</button></td></tr>'
                     % (esc(r["vendor"]), esc(r["what"]), (" (%s)" % esc(r["month"])) if r["month"] else "", esc(r["handed"]), r["id"], r["id"]))
        h.append('</table>')
    else:
        h.append('<div style="color:#2f6b45">Nothing taken by the phone is left unreported.</div>')
    h.append('<script>function s898t(b,a,ids){if(!b.dataset.armed){b.dataset.armed="1";b.dataset.t=b.textContent;b.textContent="Tap again to confirm";'
             'setTimeout(function(){if(b.dataset.armed){delete b.dataset.armed;b.textContent=b.dataset.t;}},5000);return;}b.disabled=true;'
             'fetch("/finance/porders/api/s898/"+a,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids:ids})})'
             '.then(function(r){return r.json();}).then(function(j){if(!j.ok){b.textContent=j.message||j.error||"Not done";return;}location.reload();})'
             '.catch(function(){b.textContent="Not done (network)";});}</script></div>')
    return "".join(h)


def _s454_phone_card(con, st):
    import supplier_msg as SM                                 # noqa: PLC0415
    f = SM.s454_card_facts(con)
    if f["last_ask"]:
        ask = "%s IST%s" % (_when(f["last_ask"]), "" if f["code"] == "200" else " — answered %s (wrong key)" % esc(f["code"]))
    else:
        ask = "never"
    lt = f["last_test"]
    if lt:
        steps = ["queued %s" % _when(lt["queued_at"])]
        if lt["handed_at"]:
            steps.append("handed to the phone %s" % _when(lt["handed_at"]))
        if lt["status"] == "sent":
            steps.append("sent %s" % _when(lt["sent_at"]))
        elif lt["status"] == "failed":
            steps.append("failed %s: %s" % (_when(lt["tried_at"]), lt["error"] or "the phone said no"))
        test_line = "Last test: " + " · ".join(steps)
    else:
        test_line = "No test sent yet."
    has = bool(f["test_to"])
    return ('<div %s id="s454phone"><b>Reception phone</b>'
            '<div>Last asked the server: <b>%s</b></div>'
            '<div>Waiting for the phone: <b>%d</b> order message%s · <b>%d</b> payment message%s</div>'
            '<div style="color:#666;font-size:13px">The phone asks every minute, with its screen dark too (no screen lock; the macro wakes the screen to send). The 10:00 daily check proves it.</div>'
            '<div style="margin-top:6px">Test number: <b id="s454testto">%s</b> <input id="s454testnum" inputmode="tel" placeholder="your number" style="width:150px;min-height:36px"> '
            '<button style="min-height:36px" onclick="s454t(\'test_number\',{number:document.getElementById(\'s454testnum\').value})">Save</button></div>'
            '<div style="margin-top:6px"><button id="s454testsend" style="min-height:40px" %s onclick="s454t(\'test_send\',{})">Send a test message</button>%s</div>'
            '<div id="s454testlast" style="margin-top:4px">%s</div>'
            '<script>function s454t(a,b){fetch(\'/finance/porders/api/s454/\'+a,{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},'
            'body:JSON.stringify(b)}).then(function(r){return r.json();}).then(function(j){if(!j.ok){var e=document.getElementById(\'s454testlast\');'
            'if(e){e.style.color=\'#a61b1b\';e.textContent=\'Not saved \u2014 \'+(j.message||j.error);}return;}location.reload();});}</script></div>'   # S921 (F-1552)
            % (st, ask, f["orders_wait"], "" if f["orders_wait"] == 1 else "s", f["pay_wait"], "" if f["pay_wait"] == 1 else "s",
               esc(f["test_to"]) if has else "none saved", "" if has else "disabled",
               "" if has else ' <span style="color:#8c1d18">Save a test number first.</span>', esc(test_line)))


def _owner_api():
    u, con, kind, err = _auth_api()
    if err:
        return None, None, err
    if kind != "owner":
        return None, None, (jsonify(ok=False, error="owner_only"), 403)
    return u, con, None


@bp.route(P + "/api/s454/test_number", methods=["POST"])
def api_test_number():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    ok, msg = SM.s454_save_test_to(con, who(u), str(_body().get("number") or "")[:30])
    return jsonify(ok=ok, message=msg), (200 if ok else 400)


@bp.route(P + "/api/s898/resend", methods=["POST"])
def api_s898_resend():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    n = SM.s898_resend(con, who(u), (_body().get("ids") or [])[:200])
    return (jsonify(ok=True, done=n), 200) if n else (jsonify(ok=False, message="Nothing to send again -- the list moved; reload."), 409)


@bp.route(P + "/api/s898/remove", methods=["POST"])
def api_s898_remove():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    n = SM.s898_remove(con, who(u), (_body().get("ids") or [])[:200])
    return (jsonify(ok=True, done=n), 200) if n else (jsonify(ok=False, message="Nothing to remove -- the list moved; reload."), 409)


@bp.route(P + "/api/s454/test_send", methods=["POST"])
def api_test_send():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    ok, v = SM.s454_queue_test(con, who(u))
    return (jsonify(ok=True, message_id=v), 200) if ok else (jsonify(ok=False, error="no_test_number", message=v), 409)
# ---- S454 part 1C end -------------------------------------------------------------------------------------------------------------------



# ---- S454 part 3 (7.5 / 9.3): the owner's card "Marg and the shelf figure moved apart on N items" -----------------------------------------
def _s454_gap_card(con, st):
    try:
        import shelf_figure                                   # noqa: PLC0415
        as_on, fl = shelf_figure.gap_flags(con)
        basis = OS.setting(con, "order.stock_basis")
        lst = "".join("<li>%s: %s</li>" % (esc(x["item"]), esc(x["why"] or "")) for x in fl)
        cnt = con.execute("SELECT c.id, c.marg_as_on, COUNT(i.shelf_qty) FROM stock_count c JOIN stock_count_item i ON i.count_id=c.id "
                          "WHERE i.shelf_qty IS NOT NULL GROUP BY c.id ORDER BY c.id DESC LIMIT 1").fetchone() if _s454_has_shelf_col(con) else None
        return ('<div %s id="s454gap"><b>Marg and the shelf figure moved apart on %d item%s</b>%s'
                '<div style="color:#666;font-size:13px">The shelf figure is the 6 September count carried forward by sales and purchases, plus what arrived and '
                'is not yet in Marg. The system\'s own list works from %s. A gap that moves with no voucher sends the item up Darpan\'s spot-count list.%s</div>'
                '%s</div>' % (st, len(fl), "" if len(fl) == 1 else "s", (" (closing of %s)" % esc(OS.dmy(as_on))) if as_on else " (no closing recorded yet)",
                              "the shelf figure" if basis == "count" else "Marg's closing stock",
                              (" At the count of %s the shelf figure was stored beside Marg's on %d rows." % (esc(cnt[1]), cnt[2])) if cnt else "",
                              ("<details><summary>the items</summary><ul>%s</ul></details>" % lst) if lst else ""))
    except Exception:                                         # noqa: BLE001
        return ""


def _s454_has_shelf_col(con):
    try:
        return "shelf_qty" in {r[1] for r in con.execute("PRAGMA table_info(stock_count_item)")}
    except sqlite3.Error:
        return False
# ---- S454 part 3 end ---------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S454_BILL_REGISTER P3B (03-Oct-2026, S454 18.6): the agreement card says on what stock the figure was taken. The figure is the record kept
# at the sheet's load and is not recomputed. A comparison stored before part 3 (placed 03-Oct 18:17:11 IST) was taken on Marg's stock;
# from P3B each one carries its own basis (order_sheet.compare).
# ==========================================================================================================================================
S454_P3_PLACED = "2026-10-03T18:17:11"


def _s454_basis_words(c):
    b = c.get("basis")
    if b not in ("count", "marg"):
        b = "count" if str(c.get("at") or "") >= S454_P3_PLACED else "marg"
    return "on the shelf figure" if b == "count" else "on Marg's stock"
# ---- S454 P3B end -------------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S470_ORDER_ON_SPINE (04-Oct-2026, D672 / D673): the owner's card on the old page -- ONE LINE A WEEK from the nightly trial
# (spine/orders/order_score_latest.json, written by spine/order_rehearsal.py), the medicines with no supplier on record (order_rules.plan's
# no_supplier), a family member in the plan said as such, and the six engine settings on the settings card. English; the owner only (the
# old page's owner cards). Nothing here is on a staff screen.
# ==========================================================================================================================================
S470_LIMITS = {"order.pace_days": (7, 90), "order.dead_after_days": (1, 365), "order.on_order_days": (1, 30), "order.in_transit_days": (1, 60),
               "order.lot_history_days": (30, 730),
               # S644 (the levels model's numbers; order.model and order.relist_until are word / clock settings, validated below)
               "order.rate_short_days": (3, 14), "order.rate_short_cap_pct": (100, 400), "order.rate_short_min_sell_days": (1, 7), "order.big_day_days": (0, 90),
               "order.interim_margin_days": (0, 7), "order.new_item_days": (7, 90), "order.review_min_days": (1, 7), "order.review_max_days": (3, 45),
               "order.review_default_days": (2, 30)}
S644_CHOICE = {"order.model": ("fixed", "levels")}


def _s470_or():
    import order_rules                                        # noqa: PLC0415 -- beside this file
    return order_rules


def _s470_keys():
    return tuple(getattr(_s470_or(), "S470_KEYS", ()))


def _s470_valid(key, v):
    v = str(v or "").strip()
    if key == "order.engine_source":
        return v in ("spine", "tables"), v
    if key in S644_CHOICE:                                     # S644: a word setting
        return v in S644_CHOICE[key], v
    if key == "order.relist_until":                            # S644: a clock, HH:MM
        m = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v)
        return bool(m), v
    lim = S470_LIMITS.get(key)
    if not lim:
        return False, v
    try:
        n = int(v)
    except ValueError:
        return False, v
    return lim[0] <= n <= lim[1], str(n)


def _s470_set(con, u, key, value):
    """One of S470's six settings, from the same card and the same route as the others: validated, audited (s454_setting), the owner only."""
    ok, v = _s470_valid(key, value)
    if not ok:
        lim = S470_LIMITS.get(key)
        hint = ("%d to %d" % lim) if lim else (" or ".join(S644_CHOICE[key]) if key in S644_CHOICE else ("HH:MM" if key == "order.relist_until" else "spine or tables"))
        return jsonify(ok=False, error="bad_value", message="%s: not a valid value (%s)" % (key, hint)), 400
    if key in ("order.review_min_days", "order.review_max_days"):   # S644: the two clamps must stay in order
        other = "order.review_max_days" if key == "order.review_min_days" else "order.review_min_days"
        ov = int(_s470_or()._setting(con, other) or 0)
        if (key == "order.review_min_days" and int(v) > ov) or (key == "order.review_max_days" and int(v) < ov):
            return jsonify(ok=False, error="bad_value", message="%s: review_min_days must stay at or below review_max_days (now %d)" % (key, ov)), 400
    old = _s470_or()._setting(con, key)
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, v, "S410 D626 -- " + _s470_or().SETTINGS[key][1]))
    OS.audit(con, who(u), "s454_setting", key, dict(before=old, after=v, kit="S470"))
    con.commit()
    return jsonify(ok=True, key=key, value=v, before=old)


def _s470_setting_rows(con):
    rows = []
    for k in _s470_keys():
        v = _s470_or()._setting(con, k)
        rows.append('<tr><td><code>%s</code><div style="color:#666;font-size:12.5px">%s</div></td><td><input id="s454k_%s" value="%s" style="width:120px;min-height:36px">'
                    ' <button onclick="s454set(\'%s\',document.getElementById(\'s454k_%s\').value)" style="min-height:36px">Save</button></td></tr>'
                    % (esc(k), esc(_s470_or().SETTINGS[k][1]), esc(k.replace(".", "_")), esc(v), esc(k), esc(k.replace(".", "_"))))
    return rows


def _s470_score_file():
    return os.environ.get("ORDER_SCORE_FILE") or os.path.join(os.path.dirname(os.path.abspath(_s470_or().__file__)), "spine", "orders", "order_score_latest.json")


def _s470_score_line():
    """The owner's one line a week, or 'not ready yet' when the file is missing, older than two days, or has no scored day."""
    not_ready = "The weekly score is not ready yet."
    try:
        with open(_s470_score_file(), encoding="utf-8") as fh:
            j = json.load(fh)
        day = dt.date.fromisoformat(str(j.get("date") or "")[:10])
    except (OSError, ValueError, TypeError):
        return not_ready
    if (dt.date.today() - day).days > 2 or not int(j.get("days_scored_7") or 0):
        if j.get("first_score_on") and (dt.date.today() - day).days <= 2:
            return not_ready + " The first week is scored on the night of %s." % OS.dmy(j["first_score_on"])
        return not_ready
    pct = lambda x, late: ("%d%%" % int(round(float(x)))) if x is not None else late       # noqa: E731
    m, k = int(j.get("stockouts") or 0), int(j.get("stockouts_listed_in_time") or 0)
    s = ("Last week: of what was bought, %s was on the list beforehand · of what was listed, %s was bought within 14 days · "
         "%d medicine%s ran out, %d of them listed in time."
         % (pct(j.get("bought_on_list_pct"), "nothing yet"), pct(j.get("listed_bought_pct"), "not known yet (14 days are needed)"),
            m, "" if m == 1 else "s", k))
    bm = j.get("by_model") or {}                               # S644 (B.8): the same figures per model, when a week carried more than one
    if bm:
        s += " " + " · ".join("%s list: %s of the list bought within 14 days (%d day%s)" % (("new" if mk == "levels" else "old"), pct(v.get("listed_bought_pct"), "n/a"),
                                                                                             int(v.get("days") or 0), "" if int(v.get("days") or 0) == 1 else "s")
                              for mk, v in sorted(bm.items()))
    return s


def _s644_model_line(con):
    """S644 (B.0): How the list is made -- one line and one button for the other value, on the owner's old page (the approvals fold draws its own)."""
    cur = _s470_or()._setting(con, "order.model", "fixed")
    words = {"levels": "Levels -- each supplier's own rhythm, the shop's lots, yesterday's sales", "fixed": "Fixed days -- as before"}
    other = "fixed" if cur == "levels" else "levels"
    return ('<div id="s644model"><b>How the list is made</b> · %s <button onclick="s454set(\'order.model\',\'%s\')" style="min-height:40px">Change to %s</button>'
            '<div style="color:#666;font-size:13px">The list is made and scored in the background; no staff screen changes with this setting.</div></div>'
            % (esc(words.get(cur, cur)), other, esc(words[other])))


def _s470_card(con, st):
    h = ['<div %s id="s470">%s<div id="s470score">%s</div>' % (st, _s644_model_line(con), esc(_s470_score_line()))]
    try:
        p = _s470_or().plan(con)
        ns = p.get("no_supplier") or []
        if ns:
            h.append('<div id="s470nosup">%d medicine%s no supplier on record<details><summary>the list</summary>%s<div style="color:#666;font-size:13px">'
                     'Sold, and never bought on any purchase bill Marg has given: the system\'s list orders them from nobody.</div></details></div>'
                     % (len(ns), " has" if len(ns) == 1 else "s have", esc(", ".join(x["item"] for x in ns))))
        fam = [(l["item"], l["family"]) for v in (p.get("vendors") or {}).values() for l in v["lines"] if int(l.get("family") or 0) > 1]
        if fam:
            h.append('<div id="s470family">On the system\'s list: %s</div>' % esc("; ".join("%s (1 of %d under this name)" % (i, n) for i, n in sorted(fam))))
        nc = p.get("no_closing") or []
        if nc:
            h.append('<div id="s470noclose" style="color:#8c1d18">%d item%s of Marg\'s stock list %s not in the spine\'s latest closing and %s left out of the system\'s list: %s</div>'
                     % (len(nc), "" if len(nc) == 1 else "s", "is" if len(nc) == 1 else "are", "is" if len(nc) == 1 else "are", esc(", ".join(nc[:12]))))
        eng = str(p.get("engine") or "")
        if eng and eng != "spine":
            h.append('<div id="s470engine" style="color:#8c1d18">The system\'s list is made from %s.</div>'
                     % esc("the old tables (order.engine_source = tables)" if eng == "tables" else eng))
    except Exception:                                         # noqa: BLE001 -- the card never breaks the page
        pass
    h.append("</div>")
    return "".join(h)
# ---- S470 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S618 (22-Oct-2026, kit S618_SCAN_QUALITY): send a scan back, rescan it ---------------------------------------------------------------
#    GET  /finance/porders/s454/scans              Scans to redo -- the owner (English) and the logins in porders.rescan_askers (Roman Hindi):
#                                                  (a) the open asks, (b) every pharmacy-lane scan since scan.redo_since with a scan_quality
#                                                  verdict and no open or done ask; Get it rescanned (blurred / cut off / not a bill), Open the
#                                                  scan. Its read writes nothing (no _every_read).
#    GET  /finance/porders/s454/rescan             Phir se scan karo -- reception's list of the open asks, each with Scan karo (the intake link
#                                                  carries rescan_of and the old bill's month)
#    POST /finance/porders/api/s454/rescan         {asset_bill_id, reason} -- the owner or an asker; refused for a scan set aside or a joined page
#    POST /finance/porders/api/s454/rescan/withdraw  {id} -- the same people
#  The words: scan_quality.WORDS only (imported inside the functions, fail-soft -- never at the top of this module). The ask: scan_rescan_ask
#  (order_sheet.DDL); only done_* / withdrawn_* are ever set; never deleted. An ask is closed by order_sheet.tie_pass from bills.rescan_of.
S618_ASKERS = "shavez"                                        # setting porders.rescan_askers (the owner asks by his role, always)
S618_DOERS = "reception,alisha,shivani"                       # setting porders.rescan_doers (not Darpan)
T.update({"r_rescan": ("Phir se scan karo", "Scans sent back for a rescan"),
          "r_redo": ("Scan dobara karwane hain", "Scans to redo"),
          "redo_link": ("Scan dobara karwane hain: %d", "Scans to redo: %d"),
          "redo_top": ("In scan ko reception se dobara karwaiye. Wajah chuniye.", "Send any of these back to reception for a rescan. Choose the reason."),
          "redo_asked": ("Reception ko bheje gaye", "Sent to reception"), "redo_none": ("Koi scan dobara nahi karwana.", "No scan needs redoing."),
          "redo_get": ("Dobara scan karwaiye:", "Get it rescanned:"), "redo_open": ("Scan dekhiye", "Open the scan"),
          "redo_withdraw": ("Wapas lijiye", "Withdraw"), "redo_by": ("%s · %s ne bheja", "%s · sent by %s"),
          "rescan_top": ("In bill ka paper dobara scan kijiye.", "Scan the paper of these bills again."),
          "rescan_none": ("Koi bill dobara scan nahi karna.", "No bill to rescan.")})


def _sq():
    try:
        import scan_quality                                   # noqa: PLC0415 -- /root/shared (porders.py puts it on sys.path); fail-soft
        return scan_quality
    except Exception:                                         # noqa: BLE001
        return None


def _s618_names(con, key, default):
    try:
        v = _po()._setting(con, key, default)
    except Exception:                                         # noqa: BLE001
        v = default
    return [p.strip().lower() for p in re.split(r"[,;\s]+", str(v or "")) if p.strip()]


def _s618_login(u, login=""):
    return str(login or (u or {}).get("login") or (u or {}).get("user") or "").lower()


def _s618_asker(con, kind, login):
    return kind == "owner" or login in _s618_names(con, "porders.rescan_askers", S618_ASKERS)


def _s618_doer(con, login):
    return login in _s618_names(con, "porders.rescan_doers", S618_DOERS)


def _s618_open_count(con):
    """The rescan asks neither done nor withdrawn -- DUTY_MAP reception.rescan's due_sql. S708: reception's home row adds the paper asks
    (order_track_page.open_paper_count); the duty map does not count those yet (named to the parent, F-1024)."""
    try:
        return int(con.execute("SELECT COUNT(*) FROM scan_rescan_ask WHERE done_at IS NULL AND withdrawn_at IS NULL").fetchone()[0])
    except sqlite3.Error:
        return 0


def _s618_owner_logins(con):
    try:
        return {str(r[0]).lower() for r in con.execute("SELECT username FROM unit_role WHERE unit='porders' AND role='checker' AND active=1")}
    except sqlite3.Error:
        return {"manoj"}


def _s618_month(r):
    bm = str(r.get("bill_month") or "")
    if re.match(r"^\d{4}-\d\d$", bm):
        return bm
    bd = str(r.get("bill_date") or "")
    if re.match(r"^\d{4}-\d\d", bd):
        return bd[:7]
    at = r.get("at")
    return at.strftime("%Y-%m") if at else ""


def rescan_list(con):
    """S618: 'Scans to redo' -- the ONE reader (S619 embeds it). dict(asks=[the open asks], redo=[the scans with a verdict and no open or
    done ask], since=..., ok=bool). assets.db READ ONLY (scan_lie of each bill's CURRENT file, its good reading, the scan.* settings);
    finance.db read only. Writes nothing."""
    sq = _sq()
    out = dict(asks=[], redo=[], since="", ok=sq is not None)
    try:
        asks = [dict(r) for r in con.execute("SELECT * FROM scan_rescan_ask ORDER BY id")]
    except sqlite3.Error:
        asks = []
    open_ = [a for a in asks if not a.get("done_at") and not a.get("withdrawn_at")]
    taken = {int(a["asset_bill_id"]) for a in asks if not a.get("withdrawn_at")}       # an open or a done ask: never listed again
    owners = _s618_owner_logins(con)
    acon = OS._assets()
    if acon is None:                                          # S711 (F-1123): the same shape as below, so every list can draw it
        for a in open_:
            login = str(a.get("asked_by") or "").lower()
            out["asks"].append(dict(id=a["id"], scan=int(a["asset_bill_id"]), stamp=a.get("stamp") or "", vendor="", date="", reason=a.get("reason") or "",
                                    asked_by=login, by_owner=login in owners, asked_at=a.get("asked_at") or "", month="", v=""))
        return out
    try:
        settings = {}
        try:
            settings = {str(r[0]): r[1] for r in acon.execute("SELECT key, value FROM settings WHERE key LIKE 'scan.%'")}
        except sqlite3.Error:
            pass
        since = str((sq.setting(settings, "scan.redo_since") if sq else "") or "2026-10-08")[:10]
        out["since"] = since
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        want = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "bill_month", "total_amount", "submitted_at", "created_at", "lane", "kind",
                            "status", "page_of", "doc_kind", "source_stored") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE lane='pharmacy' AND substr(created_at,1,10)>=? ORDER BY id" % ", ".join(want), (since,))]
        ids = {int(a["asset_bill_id"]) for a in open_} - {int(r["id"]) for r in rows}
        if ids:
            rows += [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE id IN (%s)" % (", ".join(want), ",".join("?" * len(ids))), sorted(ids))]
        reading, lie = {}, {}
        try:
            for r in acon.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1"):
                try:
                    reading[int(r[0])] = json.loads(r[1]) if r[1] else None
                except ValueError:
                    pass
        except sqlite3.Error:
            pass
        try:
            for r in acon.execute("SELECT * FROM scan_lie"):
                lie[(int(r["bill_id"]), r["file"])] = dict(r)
        except sqlite3.Error:
            pass
    finally:
        acon.close()
    by = {}
    for r in rows:
        r["at"] = OS.scan_moment(r)
        r["lie"] = lie.get((int(r["id"]), r.get("source_stored")))
        r["v"] = str((r["lie"] or {}).get("at") or "").replace(" ", "T")
        by[int(r["id"])] = r
    for a in open_:
        r = by.get(int(a["asset_bill_id"])) or {}
        login = str(a.get("asked_by") or "").lower()
        out["asks"].append(dict(id=a["id"], scan=int(a["asset_bill_id"]), stamp=a.get("stamp") or r.get("stamp_no") or "", vendor=r.get("vendor") or "",
                                date=str(r.get("bill_date") or "")[:10] or (r["at"].date().isoformat() if r.get("at") else ""), reason=a["reason"],
                                asked_by=login, by_owner=login in owners, asked_at=a.get("asked_at") or "", month=_s618_month(r), v=r.get("v", "")))
    if sq is None:
        return out
    for r in rows:
        sid = int(r["id"])
        if sid in taken or str(r.get("status") or "") == "rejected" or r.get("page_of") or str(r.get("created_at") or "")[:10] < since:
            continue
        d = sq.detail(r, reading.get(sid), r["lie"], settings)
        if d:
            out["redo"].append(dict(scan=sid, stamp=r.get("stamp_no") or "#%d" % sid, vendor=r.get("vendor") or "", code=d["code"], sum=d["sum"], total=d["total"],
                                    date=str(r.get("bill_date") or "")[:10] or (r["at"].date().isoformat() if r.get("at") else ""), v=r["v"]))
    return out


def _s618_count(con):
    """The home's link: the open asks and the scans to redo."""
    try:
        x = rescan_list(con)
        return len(x["asks"]) + len(x["redo"])
    except Exception:                                         # noqa: BLE001
        return 0


def _s618_intake(vendor, ym, rid, back):
    q = dict(lane="pharmacy")
    if vendor:
        q["vendor"] = str(vendor)[:120]
    if ym:
        q["bill_month"] = str(ym)[:7]
    q["rescan_of"] = str(int(rid))
    q["from"] = back
    return "/scanapp/intake?" + urlencode(q)


def _s618_thumb(x):
    return "/scanapp/bills/%d/thumb" % x["scan"] + (("?v=" + quote(x["v"])) if x.get("v") else "")


def scans_page():
    """Scans to redo (the owner, English; the askers, Roman Hindi). S736: the server's asking runs first (scan_rescan_ask rows, audited)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    login = _s618_login(u, login)
    if not _s618_asker(con, kind, login):
        return redirect(P)
    sq = _sq()
    who = "owner" if en else "shavez"
    _s736_raise_soft(con)                                      # S736 (D847): the bad scans of a counted month are already with reception
    x = rescan_list(con)
    h = ['<div class="mut">%s</div>' % L(en, "redo_top")]
    h.append(_s736_escalated_html(con, en))                    # S736: rescanned twice and still in trouble -- his and the owner's
    if not x["ok"]:
        h.append('<div class="err">scan_quality is not available -- only the open asks are shown.</div>')
    if x["asks"]:
        h.append('<div class="grp" id="redo_asks">%s · %d</div>' % (L(en, "redo_asked"), len(x["asks"])))
        for a in x["asks"]:
            if en:                                            # S628 (F-995): the owner's page in English
                by = L(en, "sent_by_you") if a["by_owner"] else L(en, "sent_by_x", str(a["asked_by"] or "").split(" ")[0].title())
            else:
                by = (sq.sent_by("owner" if a["by_owner"] else "", a["asked_by"]) if sq else a["asked_by"])
            h.append('<div class="card" data-ask="%d" data-scan="%d"><div class="nm">%s · %s</div><div class="sb">%s</div>'
                     '<div class="sb am">%s</div><div class="sb">%s</div>'
                     '<div class="lnk"><button onclick="s454(\'%s/api/s454/rescan/withdraw\',{id:%d})">%s</button></div></div>'
                     % (a["id"], a["scan"], esc(a["stamp"]), esc(a["vendor"]), esc(OS.ddmm(a["date"])),
                        esc(sq.words(a["reason"], who) if sq else a["reason"]), esc(by + " · " + OS.ddmm(a["asked_at"])), P, a["id"], L(en, "redo_withdraw")))
    if x["redo"]:
        h.append('<div class="grp" id="redo_list">%s · %d</div>' % (L(en, "r_redo"), len(x["redo"])))
        for r in x["redo"]:
            chips = "".join('<button data-reason="%s" onclick="s454(\'%s/api/s454/rescan\',{asset_bill_id:%d,reason:\'%s\'})">%s</button>'
                            % (c, P, r["scan"], c, esc(sq.CHIP_WORDS[c][0 if en else 1])) for c in sq.CHIPS)
            h.append('<div class="card" data-scan="%d" data-code="%s"><div style="display:flex;gap:10px;align-items:center">'
                     '<a href="/scanapp/bills/%d/file" target="_blank"><img src="%s" alt="scan" style="width:64px;height:84px;object-fit:cover;border:1px solid #ccc;border-radius:4px"></a>'
                     '<div><div class="nm">%s · %s</div><div class="sb">%s</div><div class="red">%s</div></div></div>'
                     '<div class="mut">%s</div><div class="chips">%s</div>'
                     '<a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div>'
                     % (r["scan"], r["code"], r["scan"], esc(_s618_thumb(r)), esc(r["stamp"]), esc(r["vendor"]), esc(OS.ddmm(r["date"])),
                        esc(sq.words(r["code"], who, r["sum"], r["total"])), L(en, "redo_get"), chips, r["scan"], L(en, "redo_open")))
    if not x["asks"] and not x["redo"]:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "redo_none"))
    taken = {int(a["scan"]) for a in x["asks"]} | {int(r["scan"]) for r in x["redo"]}
    ev = [r for r in _s628_recent(14) if int(r["id"]) not in taken]      # S628 (F-993): any pharmacy scan can be sent back
    if ev:
        h.append('<details class="card" id="sec_every"><summary style="min-height:44px;cursor:pointer;font-weight:700">%s · %d</summary>%s</details>'
                 % (L(en, "every_scan"), len(ev), "".join(
                     '<div class="sb" data-every="%d" style="padding:6px 0;border-top:1px solid #eee">%s · %s · %s <a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a>'
                     '<div class="chips">%s</div></div>' % (int(r["id"]), esc(r.get("stamp_no") or "#%d" % int(r["id"])), esc(r.get("vendor") or ""),
                                                           esc(OS.ddmm(str(r.get("bill_date") or r.get("created_at") or "")[:10])), int(r["id"]),
                                                           L(en, "redo_open"), _s628_chips(en, int(r["id"]))) for r in ev)))
    return shell(con, u, L(en, "r_redo"), "".join(h), back=P, login=login)


def _s628_recent(days):
    """S628: the pharmacy scans of the last `days` days, not set aside, first pages only (assets.db READ ONLY), newest first."""
    acon = OS._assets()
    if acon is None:
        return []
    try:
        since = (dt.date.today() - dt.timedelta(days=int(days))).isoformat()
        return [dict(r) for r in acon.execute("SELECT id, stamp_no, vendor, bill_date, created_at FROM bills WHERE lane='pharmacy' AND COALESCE(status,'')<>'rejected' "
                                              "AND page_of IS NULL AND substr(created_at,1,10)>=? ORDER BY id DESC", (since,))]
    except sqlite3.Error:
        return []
    finally:
        acon.close()


def rescan_page():
    """Phir se scan karo -- reception's list of the open asks (the reception words and who sent it), each with Scan karo."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    login = _s618_login(u, login)
    if request.args.get("old") != "1":                        # S708 (D830): reception's scan work rebuilt; ?old=1 keeps this list
        try:
            import order_track_page as OTP                    # noqa: PLC0415
            return OTP.reception(con, u, kind, login, en)
        except Exception as ex:                               # noqa: BLE001
            print("S708 reception page failed, the S618 list drawn: %r" % (ex,), file=sys.stderr)
    sq = _sq()
    x = rescan_list(con)
    h = ['<div class="mut">%s</div>' % L(en, "rescan_top")]
    for a in x["asks"]:
        by = sq.sent_by("owner" if a["by_owner"] else "", a["asked_by"]) if sq else a["asked_by"]
        h.append('<div class="ln" data-ask="%d" data-scan="%d"><div class="t"><div class="a">%s · %s</div><div class="s red">%s</div><div class="s">%s · %s</div></div>'
                 '<a class="sk" href="%s">%s</a></div>'
                 % (a["id"], a["scan"], esc(a["vendor"]), esc(a["stamp"]), esc(sq.words(a["reason"], "owner" if en else "reception") if sq else a["reason"]),
                    esc(by), esc(OS.ddmm(a["asked_at"])), esc(_s618_intake(a["vendor"], a["month"], a["scan"], P + "/s454/rescan")), L(en, "scankaro")))
    if not x["asks"]:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "rescan_none"))
    return shell(con, u, L(en, "r_rescan"), "".join(h), back=P, login=login)


@bp.route(P + "/s454/scans")
def r_scans():
    return scans_page()


@bp.route(P + "/s454/rescan")
def r_rescan():
    return rescan_page()


@bp.route(P + "/api/s454/rescan", methods=["POST"])
def api_rescan():
    u, con, kind, err = _auth_api()
    if err:
        return err
    login = _s618_login(u)
    if not _s618_asker(con, kind, login):
        return jsonify(ok=False, error="not_asker", message="Only the owner and %s send a scan back." % ", ".join(_s618_names(con, "porders.rescan_askers", S618_ASKERS))), 403
    b = _body()
    try:
        sid = int(b.get("asset_bill_id") or 0)
    except (TypeError, ValueError):
        sid = 0
    reason = str(b.get("reason") or "")
    sq = _sq()
    if not sid or reason not in (sq.CHIPS if sq else ("blurred", "cut", "not_bill")):
        return jsonify(ok=False, error="bad_request"), 400
    acon = OS._assets()
    r = None
    if acon is not None:
        try:
            r = acon.execute("SELECT id, stamp_no, lane, status, page_of FROM bills WHERE id=?", (sid,)).fetchone()
        finally:
            acon.close()
    if r is None:
        return jsonify(ok=False, error="no_such_scan"), 404
    if str(r["lane"] or "") != "pharmacy":
        return jsonify(ok=False, error="not_pharmacy", message="Only a pharmacy scan is sent back here."), 409
    if str(r["status"] or "") == "rejected" or r["page_of"]:
        return jsonify(ok=False, error="set_aside", message="This scan is already set aside -- nothing to rescan."), 409
    if con.execute("SELECT 1 FROM scan_rescan_ask WHERE asset_bill_id=? AND done_at IS NULL AND withdrawn_at IS NULL", (sid,)).fetchone():
        return jsonify(ok=False, error="already_asked", message="It is already with reception."), 409
    cur = con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at) VALUES (?,?,?,?,?)",
                      (sid, r["stamp_no"] or "", reason, login, OS.now_iso()))
    OS.audit(con, who(u), "s618_rescan_ask", sid, dict(ask=cur.lastrowid, stamp=r["stamp_no"], reason=reason, kit="S618"))
    con.commit()
    return jsonify(ok=True, id=cur.lastrowid)


@bp.route(P + "/api/s454/rescan/withdraw", methods=["POST"])
def api_rescan_withdraw():
    u, con, kind, err = _auth_api()
    if err:
        return err
    login = _s618_login(u)
    if not _s618_asker(con, kind, login):
        return jsonify(ok=False, error="not_asker"), 403
    try:
        aid = int(_body().get("id") or 0)
    except (TypeError, ValueError):
        aid = 0
    cur = con.execute("UPDATE scan_rescan_ask SET withdrawn_at=?, withdrawn_by=? WHERE id=? AND done_at IS NULL AND withdrawn_at IS NULL",
                      (OS.now_iso(), login, aid))
    if not cur.rowcount:
        return jsonify(ok=False, error="not_open"), 409
    OS.audit(con, who(u), "s618_rescan_withdrawn", aid, dict(kit="S618"))
    con.commit()
    return jsonify(ok=True)
# ---- S618 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S619 (22-Oct-2026, kit S619_ORDER_TRACKER): one order, five steps -------------------------------------------------------------------
#    GET  /finance/porders/s454/late     Order ka maal nahi aaya -- call karo: the late orders (nothing came, or medicines still awaited), each with
#                                        Call (book_card's Calls number) and Maal aaya / Baaki maal aaya (the existing arrive page)
#    S708 (05-Nov-2026, D830): /s454/track and /s454/rescan are drawn by order_track_page.py (beside this file); ?old=1 = the pages below.
#    GET  /finance/porders/s454/track    the order list: the owner (English) and the logins in porders.rescan_askers (Roman Hindi); every other sender
#                                        refused (403); Bhati redirected as today. Its read writes nothing (no _every_read).
#  Every count here is order_track's light half (finance.db only); the track page adds the scan half (assets.db READ ONLY) for its notes only.
T.update({"r_late": ("Order ka maal nahi aaya — call karo", "Goods not arrived — call"),
          "late_top": ("In order ka maal do din mein nahi aaya. Dealer ko call kijiye. Maal aa jaye to “Maal aaya” dabaiye.",
                       "These orders did not arrive within two days. Call the dealer. When the goods come, tap “Goods arrived”."),
          "late_none": ("Koi order der se nahi hai.", "No order is late."),
          "late_sub": ("Order %s · %s · %d dawa · aaj tak nahi aaya", "Ordered %s · %s · %d medicines · not arrived yet"),
          "part_sub": ("Order %s · %s · %d mein se %d dawa aayi · %s baaki", "Ordered %s · %s · %d of %d came · %s awaited"),
          "maal_aaya": ("Maal aaya", "Goods arrived"), "baaki_aaya": ("Baaki maal aaya", "The rest arrived"),
          "rm_dealer_no": ("Dealer ke paas nahi hai", "Dealer does not have it"), "rm_not_now": ("Abhi nahi chahiye", "Not needed now"),
          "carry_tag": ("pichhle order se baaki (%s)", "back from the order of %s"),
          "track": ("Purchase orders ka haal", "Purchase orders — the order list"),
          "track_link": ("Orders ka haal: %d der se · %d mein dawa kam aayi · %d scan dobara", "The order list: %d late · %d came short · %d scans to redo"),
          "t_orders": ("order %s se", "orders since %s"), "t_na": ("nahi aaye", "not arrived"), "t_short": ("kam aaye", "came short"),
          "t_marg": ("Marg mein baaki", "not in Marg yet"), "t_redo": ("scan dobara", "scans to redo"),
          "s_na": ("Nahi aaye", "Not arrived"), "s_marg": ("Bill scan hua, Marg mein abhi nahi", "Bill scanned, not in Marg yet"),
          "s_short": ("Kam aaye", "Came short"), "s_redo": ("Scan dobara karwane hain", "Scans to redo"),
          "s_wrong": ("Kisi aur dealer ke naam se save hue", "Saved under another dealer"), "s_done": ("Poore aa gaye", "Complete"),
          "refused": ("Yeh list Doctor sahab aur Shavez ke liye hai.", "This list is for the owner and Shavez only."),
          "late_w": ("der se", "late"), "due_w": ("%s shaam tak aana hai", "due %s evening"), "came_w": ("aaya %s", "came %s"),
          "outside_w": ("aaya %s — maal ke samay ke bahar", "came %s — outside the delivery hours"),
          "of_came": ("%d mein se %d aayi", "%d of %d came"), "awaited_w": ("baaki", "awaited"),
          "nm_short": ("nahi aaya: %s (%s)", "did not come: %s (%s)"), "sent_ph": ("WhatsApp gaya %s", "WhatsApp sent %s"),
          "open_scan": ("Scan dekhiye", "Open the scan")})
# ---- S628 (D761, 22-Oct-2026, kit S628_ONE_NAME_LIST): the words of the order list's corrections (F-993, F-995) -----------------------------
T.update({"none_came": ("maal aaya — is order ki koi dawa nahi aayi", "arrived — nothing on it came"),
          "send_back": ("Dobara scan ke liye bhejiye:", "Send back for rescan:"), "sent_back": ("dobara scan ke liye bheja ✓", "sent back for rescan ✓"),
          "withdraw": ("Wapas lijiye", "Withdraw"), "fix_dealer": ("Dealer badliye: %s", "Change dealer to %s"),
          "fix_none": ("Kaagaz ka dealer pakka nahi padha gaya — scan kholkar dekhiye.", "The paper's dealer is not read for sure — open the scan."),
          "s_same": ("Ek hi kaagaz ke do scan", "The same paper scanned twice"), "s_names": ("Naam milaiye", "Names to confirm"),
          "q_yes": ("Haan", "Yes"), "q_no": ("Nahi", "No"),
          "every_scan": ("Har pharmacy scan · pichhle 14 din", "Every pharmacy scan · last 14 days"),
          "sent_by_you": ("aapne bheja", "sent back by you"), "sent_by_x": ("%s ne bheja", "sent back by %s"),
          "part_sub": ("Order %s · %s · %d mein se %d dawa aayi · %s baaki", "Ordered %s · %s · of %d medicines %d came · %s awaited")})
S619_VIA = {"whatsapp": ("WhatsApp", "WhatsApp"), "call": ("Call", "Call"), "whatsapp+call": ("WhatsApp + call", "WhatsApp + call"), "scan": ("Bill scan", "bill scan"),
            "paper": ("Paper", "paper")}
S619_STEP_HI = {"Ordered": "Order", "Arrived": "Maal aaya", "Bill scanned": "Bill scan", "In Marg": "Marg mein", "All lines came": "Saari dawa aayi"}
S619_DOT = {"done": "#2e6b34", "wait": "#c9c4bc", "late": "#b3261e", "short": "#b3261e", "conflict": "#8a5300"}


def _s619_ot():
    import order_track                                        # noqa: PLC0415 -- S619, beside this file
    return order_track


def _s619_rows(con):
    return _s619_ot().light_all(con, OS.now())


def _s619_late_n(con):
    try:
        return len(_s619_ot().late_orders(con, OS.now()))
    except Exception:                                         # noqa: BLE001 -- the home never waits on this
        return 0


def _s619_via(en, v):
    return S619_VIA.get(str(v or ""), (str(v or "—"), str(v or "—")))[1 if en else 0]


def _s619_carry_tag(en, l):
    if l.get("src") != "carry":
        return ""
    return ' <span class="sb am s619carry">%s</span>' % esc(L(en, "carry_tag", OS.ddmm(l.get("carry_from"))))


def _s619_remove_chips(en, b):
    """The one remove door (api_qty remove) asks one reason chip: Dealer ke paas nahi hai / Abhi nahi chahiye."""
    return ('<span class="chips s619rm">' + "".join('<button data-reason="%s" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{remove:1,reason:\'%s\'}))">%s</button>'
                                                   % (r, P, b, r, L(en, "rm_" + r)) for r in ("dealer_no", "not_now")) + '</span>')


def _s619_track_card(con, en):
    """The owner's and Shavez's one way in (replaces S618's separate 'Scans to redo' link): the order list, with its three counts."""
    try:
        rows = _s619_rows(con)
        n_late = sum(1 for s in rows if s["late"])
        n_short = sum(1 for s in rows if s["short"])
    except Exception:                                         # noqa: BLE001
        n_late = n_short = 0
    return '<a class="row" id="track" href="%s/s454/track"><span class="l" style="font-size:16px">%s</span><span>›</span></a>' % (
        P, esc(L(en, "track_link", n_late, n_short, _s618_count(con))))


def _s619_late_card(con, en, s):
    call, _wa, _shown, _on = OS.book_card(con, s["vendor"])
    if s["part"]:
        baaki = ", ".join(x["item"] for x in s["lines"] if x["state"] in ("open", "part"))
        sub = L(en, "part_sub", OS.ddmm(s["created_at"]), _s619_via(en, s["via"]), s["n"], s["came"], baaki)
    else:
        sub = L(en, "late_sub", OS.ddmm(s["created_at"]), _s619_via(en, s["via"]), s["n"])
    names = "" if s["part"] else _s638_awaited(con, en, s)             # S638 (F-1015): what is awaited, by name and quantity
    callb = ('<a class="b" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">📞 %s</a>' % (esc(_tel(call)), P, esc(json.dumps(s["sn"])), L(en, "call"))
             if call else '<span class="b" style="color:#8a5300">%s</span>' % L(en, "nonum"))
    return ('<div class="card" data-order="%d" data-late="1"><div><div class="nm">%s</div><div class="sb am">%s</div>%s</div>'
            '<div class="two">%s<a class="g" href="%s/s454/maal/%d">%s</a></div></div>'
            % (s["id"], esc(s["vendor"]), esc(sub), names, callb, P, s["id"], L(en, "baaki_aaya" if s["part"] else "maal_aaya")))


def _s638_awaited(con, en, s):
    """S638 (F-1015): every line of the order still awaited (open / part), each with what is awaited -- the strips, pieces or bottles
    ordered less what came, in the shop's own words (qty_words with the whole-unit list loaded, OS.whole_units; fail-soft to the bare
    figure)."""
    out = []
    for x in s.get("lines") or []:
        if x.get("state") not in ("open", "part"):
            continue
        n = max(int(x.get("packs") or 0) - int(x.get("came") or 0), 0)
        ps = int(x.get("pack_size") or 1)
        try:
            qw = OS.whole_units(con)
            q = qw.words(n * ps, pack=ps, name=x.get("item"), lang="en" if en else "hi") if qw is not None else str(n)
        except Exception:                                              # noqa: BLE001
            q = str(n)
        out.append("%s · %s" % (x.get("item") or "", q))
    return ('<div class="sb s638aw">%s</div>' % "<br>".join(esc(o) for o in out)) if out else ""


def late_page():
    """Order ka maal nahi aaya -- call karo: the late orders, oldest first (part orders too)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    late = [s for s in _s619_rows(con) if s["late"]]
    h = ['<div class="mut">%s</div>' % L(en, "late_top")]
    for s in late:
        h.append(_s619_late_card(con, en, s))
    if not late:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "late_none"))
    return shell(con, u, L(en, "r_late"), "".join(h), back=P, login=login)


def _s619_dots(en, s):
    out = []
    for name, st in _s619_ot().dots(s):
        out.append('<span class="s619d" data-step="%s" data-state="%s" title="%s" style="display:inline-flex;align-items:center;gap:4px;margin-right:8px;font-size:12.5px">'
                   '<i style="display:inline-block;width:11px;height:11px;border-radius:6px;background:%s"></i>%s</span>'
                   % (esc(name), st, esc(name), S619_DOT.get(st, "#c9c4bc"), esc(name if en else S619_STEP_HI.get(name, name))))
    return '<div class="s619dots">%s</div>' % "".join(out)


def _s619_order_card(con, en, s, show_lines=True, marg=None, asked=None):
    OT = _s619_ot()
    when = s["created"].strftime("%d-%m %H:%M") if s.get("created") else OS.ddmm(s["created_at"])
    sub = [_s619_via(en, s["via"])]
    if s.get("sent_at"):
        sub.append(L(en, "sent_ph", OS._dtm(s["sent_at"]).strftime("%H:%M") if OS._dtm(s["sent_at"]) else ""))
    sub.append(L(en, "dawa", s["n"]))
    if s["part"] or (s["arrived"] and s["came"] and s["came"] < s["n"]):
        sub.append(L(en, "of_came", *((s["came"], s["n"]) if en else (s["n"], s["came"]))))   # S628 (F-995): "came 1 of 2" -- never "2 of 1"
    if s["arrived"] and s["n"] and not s["came"] and s["short"] == s["n"]:
        sub.append(L(en, "none_came"))                        # S628 (F-995): an arrival with none of its lines
    if s["late"]:
        sub.append(L(en, "late_w"))
    elif not s["arrived"] and s.get("due_at"):
        sub.append(L(en, "due_w", s["due_at"].strftime("%d-%m")))
    times = []
    if s.get("arrived_at"):
        t = s["arrived_at"].strftime("%d-%m %H:%M")
        times.append(L(en, "came_w", t) + (" (%s)" % {"tap": "tap", "scan": "scan", "marg": "Marg"}.get(s["arrived_how"], s["arrived_how"])))
    if s.get("outside"):
        times.append(L(en, "outside_w", s["outside"]))
    for x in s.get("scans") or []:
        times.append("%s%s" % (x.get("stamp") or "#%s" % x["scan"], (" " + OS._dtm(x["scan_at"]).strftime("%d-%m %H:%M")) if OS._dtm(x.get("scan_at")) else ""))
    if s.get("bills"):
        times.append("Marg: " + ", ".join(s["bills"]))
    li = []
    if show_lines or any(x.get("how") == "other" or x.get("notes") for x in s["lines"]):   # S628: a complete card still says 'came from Janta'
        for x in (s["lines"] if show_lines else [y for y in s["lines"] if y.get("how") == "other" or y.get("notes")]):
            st = x["state"]
            if st == "short":
                w = "%s · %s" % (L(en, "nm_short", x["item"], x["short_text"]), OT.short_words(con, s, x, en, marg))
                cls = "red"
            elif st in ("open", "part"):
                w = "%s · %s%s" % (x["item"], L(en, "awaited_w"), (" (%s)" % x["short_text"]) if st == "part" else "")
                cls = "amb"
            elif st == "awaiting":
                w = x["item"]
                cls = ""
            else:
                w = "%s ✓" % x["item"]
                cls = "grn"
            soft = (s.get("soft") or {}).get(x["id"])
            notes = [OT.W(k, en, *a) for k, a in x.get("notes") or []]
            li.append('<div class="sb" data-line="%d" data-state="%s"><span class="%s">%s</span>%s%s</div>'
                      % (x["id"], st, cls, esc(w), (' <span class="amb s619soft" data-soft="%s">· %s</span>' % (soft[0], esc(soft[1]))) if soft else "",
                         "".join(' <span class="amb s619note">· %s</span>' % esc(n) for n in notes)))
    thumb = ('<a href="%s" target="_blank"><img src="%s" alt="scan" style="width:56px;height:74px;object-fit:cover;border:1px solid #ccc;border-radius:4px"></a>'
             % (esc(s["file"]), esc(s["thumb"]))) if s.get("thumb") else ""
    notes = "".join('<div class="sb am s619note">%s</div>' % esc(n) for n in s.get("notes") or [])
    sb = _s628_send_back(en, s, asked) if asked is not None else ""
    return ('<div class="card s619o" data-order="%d" data-key="%s"><div style="display:flex;gap:10px;align-items:flex-start"><div style="flex:1 1 auto">'
            '<div class="nm">%s · %s</div><div class="sb">%s</div>%s<div class="sb">%s</div>%s%s%s</div>%s</div></div>'
            % (s["id"], s["key"], esc(s["vendor"]), esc(when), esc(" · ".join(sub)), _s619_dots(en, s), esc(" · ".join(times)), notes, "".join(li), sb, thumb))


def _s628_chips(en, sid):
    sq = _sq()
    chips = sq.CHIPS if sq else ("blurred", "cut", "not_bill")
    words = sq.CHIP_WORDS if sq else {"blurred": ("blurred", "dhundli"), "cut": ("cut off", "kata hua"), "not_bill": ("not a bill", "bill nahi")}
    return "".join('<button data-reason="%s" data-scan="%d" onclick="s454(\'%s/api/s454/rescan\',{asset_bill_id:%d,reason:\'%s\'})">%s</button>'
                   % (c, sid, P, sid, c, esc(words[c][0 if en else 1])) for c in chips)


def _s628_send_back(en, s, asked):
    """S628 (F-993): every scan an order card names -- the clearer scan of its paper -- carries Send back (the three chips), or 'sent back ✓'
    with Withdraw when an ask is open. asked = {scan id: ask id} of the open asks."""
    out, seen = [], set()
    for x in s.get("scans") or []:
        sid = int(x.get("head") or x["scan"])
        if x.get("head_set_aside"):                           # S630: the clearer copy is set aside -- offer the tied scan itself, if it is not
            sid = int(x["scan"])
            if x.get("set_aside"):
                continue                                      # both set aside: nothing to send back (the scan app refuses it)
        if sid in seen or x.get("other"):
            continue
        seen.add(sid)
        st = x.get("stamp") if int(x["scan"]) == sid else (x.get("head_stamp") or "#%d" % sid)   # S630: never a set-aside scan here
        if sid in asked:
            out.append('<div class="sb s628sb" data-sbscan="%d">%s · <span class="am">%s</span> <button onclick="s454(\'%s/api/s454/rescan/withdraw\',{id:%d})">%s</button></div>'
                       % (sid, esc(st), L(en, "sent_back"), P, asked[sid], L(en, "withdraw")))
        else:
            out.append('<div class="sb s628sb" data-sbscan="%d">%s · %s <span class="chips">%s</span></div>' % (sid, esc(st), L(en, "send_back"), _s628_chips(en, sid)))
    return "".join(out)


def track_page():
    """The order list -- the owner (English) and porders.rescan_askers (Roman Hindi). Sections: Not arrived (late first; part orders too),
    Bill scanned not in Marg yet (the soft notes), Came short (Marg-confirmed / tapped), Scans to redo (S618's rescan_list), Saved under another
    dealer (Open the scan only), Complete (folded). Its read writes nothing."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    login = _s618_login(u, login)
    if not _s618_asker(con, kind, login):
        pg, _c, hd = shell(con, u, L(en, "track"), '<div class="err" id="refused">%s</div>' % L(en, "refused"), back=P, login=login)
        return pg, 403, hd
    if request.args.get("old") != "1":                        # S708 (D830): the order list rebuilt; ?old=1 keeps this page
        try:
            import order_track_page as OTP                    # noqa: PLC0415
            return OTP.page(con, u, kind, login, en)
        except Exception as ex:                               # noqa: BLE001
            print("S708 track page failed, the S619 page drawn: %r" % (ex,), file=sys.stderr)
    OT = _s619_ot()
    now = OS.now()
    rows = OT.light_all(con, now)
    ctx = OT.Ctx(con)
    OT.full_all(con, now, en=en, ctx=ctx, rows=rows)
    redo = getattr(ctx, "redo", None) or dict(asks=[], redo=[])
    redo = dict(redo, redo=[r for r in redo.get("redo") or [] if ctx.head(r["scan"]) == int(r["scan"])])   # S628 (F-992): a copy whose clearer scan
    tl = OT.tiles(rows, len(redo.get("asks") or []) + len(redo.get("redo") or []))                         # exists is not asked to be redone
    marg = OT._marg_items(con)
    asked = {int(a["scan"]): int(a["id"]) for a in redo.get("asks") or []}     # S628: the open asks, for Send back / Withdraw on the cards
    h = ['<h1 id="trackh">%s</h1>' % L(en, "track")]
    if kind == "owner":                                       # S628 (D761): the one name list's questions -- the owner's, one line each
        try:
            import med_names                                  # noqa: PLC0415
            qs = med_names.questions(con)
        except Exception:                                     # noqa: BLE001
            qs = []
        if qs:
            h.append('<div class="grp" id="sec_names">%s · %d</div>' % (L(en, "s_names"), len(qs)))
            for q in qs:
                h.append('<div class="card" data-nameq="%d"><div class="nm">%s</div><div class="two">'
                         '<button class="g" onclick="s454(\'%s/api/s454/name_answer\',{id:%d,yes:1})">%s</button>'
                         '<button onclick="s454(\'%s/api/s454/name_answer\',{id:%d,yes:0})">%s</button></div></div>'
                         % (q["id"], esc(med_names.question_text(q, True)), P, q["id"], L(en, "q_yes"), P, q["id"], L(en, "q_no")))
    h.append('<div class="two" id="tiles" style="flex-wrap:wrap">%s</div>' % "".join(
        '<div class="card" data-tile="%s" style="flex:1 1 30%%;min-width:90px;padding:8px"><div class="nm" style="font-size:22px">%d</div><div class="sb">%s</div></div>'
        % (k, n, esc(lab)) for k, n, lab in (("orders", tl["orders"], L(en, "t_orders", OS.ddmm(OT.since(con)))), ("not_arrived", tl["not_arrived"], L(en, "t_na")),
                                             ("short", tl["short"], L(en, "t_short")), ("not_in_marg", tl["not_in_marg"], L(en, "t_marg")),
                                             ("redo", tl["redo"], L(en, "t_redo")))))
    na = sorted([s for s in rows if s["key"] in ("not_arrived", "part")], key=lambda s: (0 if s["late"] else 1, s["created_at"]))
    nm = [s for s in rows if s["key"] == "awaiting"]
    sh = [s for s in rows if s["short"]]
    done = [s for s in rows if s["complete"]]
    for sid, title, lst in (("sec_na", "s_na", na), ("sec_marg", "s_marg", nm), ("sec_short", "s_short", sh)):
        h.append('<div class="grp" id="%s">%s · %d</div>' % (sid, L(en, title), len(lst)))
        for s in lst:
            h.append(_s619_order_card(con, en, s, True, marg, asked))
    h.append('<div class="grp" id="sec_redo">%s · %d</div>' % (L(en, "s_redo"), tl["redo"]))
    sq = _sq()
    for a in redo.get("asks") or []:
        h.append('<div class="card" data-ask="%d" data-scan="%d"><div class="nm">%s · %s</div><div class="sb am">%s</div>'
                 '<div class="lnk"><button onclick="s454(\'%s/api/s454/rescan/withdraw\',{id:%d})">%s</button></div></div>'
                 % (a["id"], a["scan"], esc(a["stamp"]), esc(a["vendor"]), esc(sq.words(a["reason"], "owner" if en else "shavez") if sq else a["reason"]),
                    P, a["id"], L(en, "withdraw")))
    for r in redo.get("redo") or []:
        chips = "".join('<button data-reason="%s" onclick="s454(\'%s/api/s454/rescan\',{asset_bill_id:%d,reason:\'%s\'})">%s</button>'
                        % (c, P, r["scan"], c, esc(sq.CHIP_WORDS[c][0 if en else 1])) for c in sq.CHIPS) if sq else ""
        h.append('<div class="card" data-scan="%d" data-code="%s"><div style="display:flex;gap:10px;align-items:center">'
                 '<a href="/scanapp/bills/%d/file" target="_blank"><img src="%s" alt="scan" style="width:56px;height:74px;object-fit:cover;border:1px solid #ccc;border-radius:4px"></a>'
                 '<div><div class="nm">%s · %s</div><div class="red">%s</div></div></div><div class="mut">%s</div><div class="chips">%s</div>'
                 '<a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div>'
                 % (r["scan"], r["code"], r["scan"], esc(_s618_thumb(r)), esc(r["stamp"]), esc(r["vendor"]),
                    esc(sq.words(r["code"], "owner" if en else "shavez", r["sum"], r["total"]) if sq else r["code"]), L(en, "redo_get"), chips, r["scan"], L(en, "redo_open")))
    wd = OT.wrong_dealer(con, ctx)
    h.append('<div class="grp" id="sec_wrong">%s · %d</div>' % (L(en, "s_wrong"), len(wd)))
    for w in wd:
        pk = OT.paper_dealer(con, ctx, w["scan"])            # S628: the server's own reading of the paper's dealer -- the one-tap door
        fix = ('<div class="lnk"><button class="g" data-fix="%d" onclick="s454(\'%s/api/s454/dealer_fix\',{scan:%d})">%s</button></div>'
               % (w["scan"], P, w["scan"], esc(L(en, "fix_dealer", pk))) if pk else '<div class="sb am">%s</div>' % L(en, "fix_none"))
        h.append('<div class="card" data-wrong="%d"><div class="nm">%s · %s</div><div class="sb">%s</div>%s<a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div>'
                 % (w["scan"], esc(w["stamp"]), esc(OS.ddmm(w["date"])), esc(("saved as %s; the paper says %s" if en else "%s ke naam se save; kaagaz par %s") % (w["saved"], w["paper"])),
                    fix, w["scan"], L(en, "open_scan")))
    sp2 = OT.same_paper(con, ctx)                             # S628 (F-992): the same paper scanned twice, neither set aside
    if sp2:
        h.append('<div class="grp" id="sec_same">%s · %d</div>' % (L(en, "s_same"), len(sp2)))
        for p in sp2:
            h.append('<div class="card" data-same="%d-%d"><div class="nm">%s</div><div class="lnk"><a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a> '
                     '<a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div><div class="chips">%s</div></div>'
                     % (p["a"], p["b"], esc(OT.W("same_paper", en, p["sa"], p["sb"], p["bill"])), p["a"], esc(p["sa"]), p["b"], esc(p["sb"]),
                        L(en, "send_back") + " " + esc(p["sa"]) + " " + _s628_chips(en, p["a"]) + " · " + esc(p["sb"]) + " " + _s628_chips(en, p["b"])))
    h.append('<details class="card" id="sec_done"><summary style="min-height:44px;cursor:pointer;font-weight:700">%s · %d</summary>%s</details>'
             % (L(en, "s_done"), len(done), "".join(_s619_order_card(con, en, s, False, marg, asked) for s in done)))
    return shell(con, u, L(en, "track"), "".join(h), back=P, login=login)


@bp.route(P + "/s454/late")
def r_late():
    return late_page()


@bp.route(P + "/api/s454/name_answer", methods=["POST"])
def api_name_answer():
    """S628 (D761): the owner's Yes / No on one name question of the one name list (med_names). The owner only."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only", message="Only the owner answers the name questions."), 403
    b = _body()
    try:
        qid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        qid = 0
    import med_names                                          # noqa: PLC0415
    ok, st = med_names.answer(con, qid, bool(b.get("yes")), who(u))
    if not ok:
        return jsonify(ok=False, error="not_open", message="Already answered."), 409
    OS.audit(con, who(u), "s628_name_answer", qid, dict(state=st, kit="S628"))
    con.commit()
    return jsonify(ok=True, state=st)


S711_CHANGE = ("CREATE TABLE IF NOT EXISTS s711_dealer_change (id INTEGER PRIMARY KEY AUTOINCREMENT, scan INTEGER NOT NULL, stamp TEXT, saved TEXT, "
               "dealer TEXT NOT NULL, before TEXT, tie_to INTEGER, by TEXT, at TEXT, undone_at TEXT, undone_by TEXT)")


def _s711_state(con, sid):
    """What a dealer change touches, as it is now: the s454 vendor answer, the matcher's chosen_vendor, the scan's tie (+ its order's arrival)."""
    a = con.execute("SELECT answer, value, by, at FROM s454_scan_answer WHERE asset_bill_id=? AND kind='vendor'", (sid,)).fetchone()
    try:
        c = con.execute("SELECT chosen_vendor FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone()
    except sqlite3.Error:
        c = None
    t = con.execute("SELECT order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    o = con.execute("SELECT status, received_at, received_by FROM purchase_order WHERE id=?", (t[0],)).fetchone() if t else None
    return dict(answer=list(a) if a else None, chosen=(c[0] if c else None), state_row=c is not None,
                tie=list(t) if t else None, order=list(o) if o else None)


def _s711_untie(con, sid, stamp, w, why):
    """Remove the scan's tie; when that tie alone made its order 'arrived' (the S454 tie's own mark: received_by 'bill scan <stamp>'), the order
    waits again. -> the removed tie's order id or None."""
    t = con.execute("SELECT order_id, arrived FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if not t:
        return None
    con.execute("DELETE FROM order_scan_tie WHERE asset_bill_id=?", (sid,))
    if t[1]:
        con.execute("UPDATE purchase_order SET status='sent', received_at=NULL, received_by=NULL WHERE id=? AND status='received' AND received_by IN (?,?)",
                    (t[0], "bill scan %s" % (stamp or sid), "bill scan %s" % sid))
    OS.audit(con, w, "s711_untie", sid, dict(order=t[0], arrived=t[1], why=why, kit="S711"))
    return t[0]


def _s708_put_dealer(con, u, sid, pk, ctx, s, action="s628_dealer_fix"):
    """S628's dealer door, made callable (S708): the scan's dealer becomes pk (a supplier key the SERVER chose -- the paper's reading for
    Change dealer, the server's own list for S708's pick), s454_scan_answer + the S440 matcher's door, the links re-matched.
    S711 (F-1121): no tie is made here any more -- a tie to another dealer's order is removed (with the arrival that tie alone made) and the S454
    tie (order_sheet.tie_pass, its own rules, reading this answer first) ties the scan; the change is kept in s711_dealer_change with what it
    replaced, so _s711_dealer_undo can put it back. -> dict(ok, dealer, tie, linked, change)."""
    w = who(u)
    kit = "S708" if action.startswith("s708") else "S628"
    con.execute(S711_CHANGE)
    before = _s711_state(con, sid)
    _answer(con, sid, "vendor", "chosen", pk, w)              # commits; audited s454_scan_answer
    try:                                                      # the S440 matcher's own door too (purchase_scan_state.chosen_vendor) -- no alias learnt:
        _po()._s440_put(con, sid, w, chosen_vendor=pk)        # the saved text names the WRONG dealer
        con.commit()
    except Exception:                                         # noqa: BLE001
        pass
    pa = _pa()
    moved = None
    t = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t:
        o = con.execute("SELECT vendor FROM purchase_order WHERE id=?", (t[0],)).fetchone()
        if o and pa.supplier_key(o[0]) != pk:
            _s711_untie(con, sid, s.get("stamp_no") or "", w, "dealer changed to %s" % pk)
    OS.audit(con, w, action, sid, dict(stamp=s.get("stamp_no"), saved=s.get("vendor"), paper=pk, kit=kit))
    con.commit()
    try:                                                      # S711 (F-1121): the S454 tie, by its own rules, now -- not a tie of this door's
        OS.tie_pass(con, "%s dealer" % w)
    except Exception as ex:                                   # noqa: BLE001
        con.rollback()                                        # a half-done pass is not kept (the cron runs it again)
        print("S711 tie_pass after a dealer change failed: %r" % (ex,), file=sys.stderr)
    t2 = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t2 and (not t or t2[0] != t[0]):
        moved = t2[0]
    cur = con.execute("INSERT INTO s711_dealer_change (scan, stamp, saved, dealer, before, tie_to, by, at) VALUES (?,?,?,?,?,?,?,?)",
                      (sid, s.get("stamp_no") or "", s.get("vendor") or "", pk, json.dumps(before), t2[0] if t2 else None, w, OS.now_iso()))
    change = cur.lastrowid
    OS.audit(con, w, "s711_dealer_change", sid, dict(id=change, dealer=pk, tie_to=t2[0] if t2 else None, kit="S711"))
    con.commit()
    try:
        _pa()._rematch(con, w)                                # the scan links follow at once (as S440's Supplier chuno does)
    except Exception:                                         # noqa: BLE001
        pass
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return dict(ok=True, dealer=pk, tie=moved, linked=bool(lk), change=change)


def _s711_dealer_undo(con, u, cid):
    """S711: undo one dealer change, while nothing newer has happened to the scan (no later change; its tie is the one the change left):
    the s454 vendor answer and the matcher's choice back as they were, the tie made after it removed (and the arrival it alone made), the
    tie it removed put back (with its order's arrival) when that order is still free. -> (ok, error)."""
    w = who(u)
    try:
        r = con.execute("SELECT id, scan, stamp, dealer, before, tie_to, undone_at, at FROM s711_dealer_change WHERE id=?", (cid,)).fetchone()
    except sqlite3.Error:
        r = None
    if not r or r[6]:
        return False, "not_open"
    sid = int(r[1])
    if con.execute("SELECT 1 FROM s711_dealer_change WHERE scan=? AND id>? AND undone_at IS NULL", (sid, cid)).fetchone():
        return False, "moved_on"
    t = con.execute("SELECT order_id, tied_at, how FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t and t[0] != r[5] and (str(t[2] or "") != "scan" or str(t[1] or "") < str(r[7] or "")):
        return False, "moved_on"                              # a person's tie, or a tie older than the change: not ours to undo
    if t and str(t[2] or "") == "scan_made_order":
        return False, "made_order"                            # the S454 tie made an order from this bill: undo would leave it paperless
    a_now = con.execute("SELECT answer, value, at FROM s454_scan_answer WHERE asset_bill_id=? AND kind='vendor'", (sid,)).fetchone()
    if not a_now or a_now[0] != "chosen" or a_now[1] != r[3] or str(a_now[2] or "") > str(r[7] or ""):
        return False, "moved_on"                              # the dealer was answered another way since (S440's door): not ours to undo
    if not con.execute("UPDATE s711_dealer_change SET undone_at=?, undone_by=? WHERE id=? AND undone_at IS NULL", (OS.now_iso(), w, cid)).rowcount:
        return False, "not_open"                              # a second tap at the same moment
    t2 = con.execute("SELECT order_id, tied_at, how FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if (tuple(t2) if t2 else None) != (tuple(t) if t else None):
        con.rollback()
        return False, "moved_on"                              # the S454 tie ran between the read and the claim: read again
    try:
        b = json.loads(r[4] or "{}")
    except ValueError:
        b = {}
    if t:                                                     # the tie the change left, or the S454 tie made after it under the new dealer
        _s711_untie(con, sid, r[2] or "", w, "undo of dealer change %d" % cid)
    a = b.get("answer")
    if a:
        con.execute("UPDATE s454_scan_answer SET answer=?, value=?, by=?, at=? WHERE asset_bill_id=? AND kind='vendor'", (a[0], a[1], a[2], a[3], sid))
    else:
        con.execute("DELETE FROM s454_scan_answer WHERE asset_bill_id=? AND kind='vendor'", (sid,))
    try:
        con.execute("UPDATE purchase_scan_state SET chosen_vendor=? WHERE asset_bill_id=?", (b.get("chosen"), sid))
    except sqlite3.Error:
        pass
    old = b.get("tie")
    part = ""
    if old and not con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=? OR asset_bill_id=?", (old[0], sid)).fetchone():
        con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,?)", tuple(old))
        o = b.get("order")
        if o and o[0] == "received":
            con.execute("UPDATE purchase_order SET status='received', received_at=?, received_by=? WHERE id=? AND status='sent'", (o[1], o[2], old[0]))
    elif old:
        part = "old_tie_taken"                                # its old order has another scan now: this scan waits for its order again
    OS.audit(con, w, "s711_dealer_undo", sid, dict(id=cid, part=part, kit="S711"))
    con.commit()
    try:
        _pa()._rematch(con, w)
    except Exception:                                         # noqa: BLE001
        pass
    return True, part


@bp.route(P + "/api/s454/dealer_fix", methods=["POST"])
def api_dealer_fix():
    """S628 (F-993, D761): a pharmacy scan saved under the wrong dealer -> the dealer its paper names, read by the SERVER (order_track.paper_dealer,
    never the browser): s454_scan_answer(vendor, chosen) -- which order_sheet._resolver already reads first -- and the scan's tie to an order of
    the other dealer moves to the paper dealer's newest untied order made before the scan within 7 days (else it is only removed). The owner
    and porders.rescan_askers (Shavez) only. The scan app's own record keeps its text (its Edit changes that)."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    login = _s618_login(u)
    if not _s618_asker(con, kind, login):
        return jsonify(ok=False, error="not_asker", message="Only the owner and Shavez correct a scan's dealer."), 403
    try:
        sid = int(_body().get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    OT = _s619_ot()
    ctx = OT.Ctx(con)
    s = ctx.scans.get(sid)
    if not sid or not s or str(s.get("lane") or "") != "pharmacy" or str(s.get("status") or "") == "rejected":
        return jsonify(ok=False, error="no_such_scan"), 404
    if sid not in {w["scan"] for w in OT.wrong_dealer(con, ctx)}:
        return jsonify(ok=False, error="not_wrong", message="This scan is not saved under another dealer."), 409
    pk = OT.paper_dealer(con, ctx, sid)
    if not pk:
        return jsonify(ok=False, error="paper_unread", message="The paper's dealer is not read for sure."), 409
    return jsonify(**_s708_put_dealer(con, u, sid, pk, ctx, s))


@bp.route(P + "/s454/track")
def r_track():
    return track_page()


# ---- S708 (05-Nov-2026, D830): the doors of the rebuilt order list and reception's scan work (order_track_page.py) -------------------------
def _s708_door(fn):
    u, con, kind, err = _auth_api()
    if err:
        return err
    import order_track_page as OTP                            # noqa: PLC0415
    b = _body()
    if not isinstance(b, dict):
        return jsonify(ok=False, error="bad_request"), 400
    d, code = getattr(OTP, fn)(con, u, kind, _s618_login(u), b)
    return jsonify(**d), code


@bp.route(P + "/api/s454/s708/pick", methods=["POST"])
def api_s708_pick():
    return _s708_door("api_pick")


@bp.route(P + "/api/s454/s708/pick/undo", methods=["POST"])
def api_s708_pick_undo():
    return _s708_door("api_pick_undo")


@bp.route(P + "/api/s454/s708/dealer", methods=["POST"])
def api_s708_dealer():
    return _s708_door("api_dealer")


@bp.route(P + "/api/s454/s711/dealer/undo", methods=["POST"])
def api_s711_dealer_undo():
    return _s708_door("api_dealer_undo")                      # S711


@bp.route(P + "/api/s454/s708/paper", methods=["POST"])
def api_s708_paper():
    return _s708_door("api_paper")


@bp.route(P + "/api/s454/s708/paper/withdraw", methods=["POST"])
def api_s708_paper_withdraw():
    return _s708_door("api_paper_withdraw")


@bp.route(P + "/api/s454/s708/paper/scanned", methods=["POST"])
def api_s708_paper_scanned():
    return _s708_door("api_paper_scanned")


@bp.route(P + "/api/s454/s708/paper/tie", methods=["POST"])
def api_s708_paper_tie():
    return _s708_door("api_paper_tie")


@bp.route(P + "/api/s454/s708/paper/reask", methods=["POST"])
def api_s708_paper_reask():
    return _s708_door("api_paper_reask")


@bp.route(P + "/api/s454/s708/lost", methods=["POST"])
def api_s708_lost():
    return _s708_door("api_lost")


@bp.route(P + "/api/s454/s708/lost/clear", methods=["POST"])
def api_s708_lost_clear():
    return _s708_door("api_lost_clear")
# ---- S619 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S736 (06-Nov-2026, Sanjeevni session 396, kit S736_RECEPTION_BILL_LIST; D847, D839, D840, D848) --------------------------------------
#  RECEPTION'S ONE LIST -- "Aaj ka bill kaam" (the owner's approved mock https://claude.ai/artifact/Mwe48BGnJcu6vb5ZPMH4tV):
#    GET  /finance/porders/s454/billkaam   four groups, each card one job: Dobara scan karo (every open rescan ask -- a person's or the
#                                          server's -- with its try), Order ka bill dhoondo (S708's paper asks, opened on their own page),
#                                          Scan karo (a Marg bill with no scan: days waited, Bill nahi mil raha), Ek sawaal (Kya yeh wahi
#                                          bill hai? -- the field that differs and what the scan read against Marg); then today's scans.
#  THE SERVER ASKS BY ITSELF (D847: a bad scan goes straight to reception, never through Shavez). s736_raise(), on reception's home, on
#  this page and on Shavez's Scans to redo (never on a GET of the owner's step view): a pharmacy scan of a COUNTED month (September raises
#  nothing, D848) with a scan_quality verdict (rescan_list's own rule) or a paired scan that read neither a total nor a bill number
#  (S726's "Paired, nothing read") gets ONE scan_rescan_ask row asked_by='server', reason = the verdict code or 'unread' -- when the scan
#  has never had an ask (open, done or withdrawn: a person's decision stands), is not set aside, not rescanned, not a picked-away copy
#  (S708), not a second scan (why 'dup'), is at least S736_SETTLE_MIN minutes old, and the owner has not accepted it. The try is the
#  rescan chain (assets.db bills.rescan_of): a scan with S736_TRIES rescans behind it is NOT asked again -- it goes to the owner and
#  Shavez (his step view row 5 and Shavez's Scans to redo). An open server ask whose scan is now fine (a good reading present, no
#  verdict, not unread) is withdrawn by the server. assets.db READ ONLY; writes only scan_rescan_ask rows and audit rows.
#  Reception's home: the reception logins (porders.rescan_doers) see ONE row "Aaj ka bill kaam" in place of Phir se scan karo and Bill
#  scan karna hai; their Photo dekh kar bataiye row counts (and opens) the other questions only. Every old page stays at its address.
S736_KIT = "S736_RECEPTION_BILL_LIST"
S736_SERVER = "server"
S736_TRIES = 2                                                # two tries at reception, then the owner and Shavez (D847)
S736_SETTLE_MIN = 30                                          # a scan is judged only once its check and reading have had time to land
S736_SHOW = 8                                                 # cards shown per group before "Aur dikhaiye"
S736_WORDS = {"unread": ("Nothing was read on the scan — rescan it straight, in good light", "Kuch padha nahi gaya",
                         "Kuch padha nahi gaya — bill seedha rakh kar, roshni mein, saaf scan kijiye")}
S736_REASON_EN = {"unread": "nothing read", "blurred": "blurred", "cut": "cut off", "no_total": "no total", "not_adding": "lines do not add up",
                  "not_bill": "not a bill"}
T.update({"r_billkaam": ("Aaj ka bill kaam", "Today's bill work"),
          "bk_top": ("Har line ek kaam hai. Kaam hote hi line khud hat jaati hai.", "Each line is one job. A line goes by itself once its job is done."),
          "bk_redo": ("Dobara scan karo · %d", "Rescan · %d"), "bk_paper": ("Order ka bill dhoondo · %d", "Find the order's bill · %d"),
          "bk_scan": ("Scan karo — Marg mein hai, scan nahi · %d", "Scan — in Marg, not scanned · %d"), "bk_q": ("Ek sawaal · %d", "A question · %d"),
          "bk_try1": ("Pehli baar", "First try"), "bk_try2": ("Doosri baar (aakhri) · iske baad Doctor sahab aur Shavez dekhenge",
                                                           "Second try (the last) · then you and Shavez look"),
          "bk_tryn": ("%d-vi baar", "Try %d"), "bk_by_server": ("server ne %s ko bheja", "sent by the server on %s"),
          "bk_by_owner": ("Doctor sahab ne %s ko bheja", "sent by you on %s"), "bk_by_x": ("%s ne %s ko bheja", "sent by %s on %s"),
          "bk_scan_no": ("scan %s", "scan %s"), "bk_days": ("%d din se baaki", "%d days waiting"), "bk_today": ("aaj ka bill", "today's bill"),
          "bk_recv": ("%s · maal aaya %s", "%s · goods came %s"), "bk_recv_s": ("Is order ka bill scan karna hai", "This order's bill is to be scanned"),
          "bk_missing": ("Bill nahi mil raha", "Bill not found"), "bk_paper_s": ("Order %s · bill ka kaagaz abhi scan nahi hua", "Ordered %s · its bill paper is not scanned yet"),
          "bk_open": ("Kholo", "Open"), "bk_q_h": ("Kya yeh wahi bill hai?", "Is this the same bill?"), "bk_marg": ("Marg mein:", "In Marg:"),
          "bk_q_dup": ("Is bill ka ek scan pehle se hai — kya yeh usi bill ka doosra scan hai?", "This bill already has a scan — is this a second scan of it?"),
          "bk_yes": ("Haan, yahi hai", "Yes, it is"), "bk_no": ("Nahi", "No"), "bk_photo": ("scan %s ki photo", "photo of scan %s"),
          "bk_f_no": ("Scan par <b>bill number</b> nahi padha gaya.", "The <b>bill number</b> was not read on the scan."),
          "bk_f_nod": ("Scan par bill number “%s” padha gaya — Marg mein %s.", "The scan reads bill number “%s” — Marg has %s."),
          "bk_f_amt": ("Scan par <b>amount</b> nahi padha gaya.", "The <b>amount</b> was not read on the scan."),
          "bk_f_amtd": ("Scan par amount %s padha gaya — Marg mein %s.", "The scan reads the amount %s — Marg has %s."),
          "bk_f_date": ("Scan par date %s padhi gayi — Marg mein %s.", "The scan reads the date %s — Marg has %s."),
          "bk_f_none": ("Scan par kuch padha nahi gaya — supplier aur din mil rahe hain.", "Nothing was read on the scan — the supplier and the day match."),
          "bk_f_same": ("%s mil rahe hain.", "%s match."), "bk_f_check": ("Photo aur Marg ko milaakar dekhiye.", "Compare the photo with Marg."),
          "bk_w_sup": ("Supplier", "The supplier"), "bk_w_amt": ("amount", "the amount"), "bk_w_date": ("date", "the date"), "bk_w_no": ("bill number", "the bill number"),
          "bk_and": (" aur ", " and "), "bk_more": ("Aur dikhaiye (%d)", "Show more (%d)"),
          "bk_aaj0": ("Aaj abhi koi bill scan nahi hua.", "No bill scanned yet today."),
          "bk_aaj_ok": ("Aaj ke scan: %d bill scan hue, sab padhe gaye ✓", "Today's scans: %d bills scanned, all read ✓"),
          "bk_aaj_n": ("Aaj ke scan: %d bill scan hue · %d padhe gaye", "Today's scans: %d bills scanned · %d read"),
          "bk_none": ("Aaj ka bill kaam poora ✓", "Today's bill work is done ✓"),
          "bk_esc": ("Reception do baar scan kar chuki — Doctor sahab aur aap dekhiye · %d", "Rescanned twice by reception — for you and Shavez · %d"),
          "bk_esc_s": ("%s · %s · abhi bhi: %s", "%s · %s · still: %s")})


def _s736_sr():
    import scan_register                                      # noqa: PLC0415 -- beside this file
    return scan_register


def _s736_depth(parent, sid):
    """How many rescans stand behind this scan (bills.rescan_of followed back): 0 for a first scan."""
    n, seen, cur = 0, set(), int(sid)
    while cur in parent and cur not in seen and n < 50:
        seen.add(cur)
        cur = parent[cur]
        n += 1
    return n


def _s736_facts(con):
    """READ ONLY: everything the server's asking needs, in one read of each database. ok=False when assets.db or scan_quality is missing
    (then nothing is asked or withdrawn)."""
    sq = _sq()
    out = dict(ok=False, rows={}, reading={}, settings={}, parent={}, kids=set(), asks=[], link={}, dec={}, picked=set(), dup=set(), since="", final=set())
    try:                                                      # a finalised month is never changed (S726's rule): nothing is asked in it
        out["final"] = {str(r[0]) for r in con.execute("SELECT month FROM purchase_month WHERE status='final'")}
    except sqlite3.Error:
        pass
    try:
        out["asks"] = [dict(r) for r in con.execute("SELECT * FROM scan_rescan_ask ORDER BY id")]
    except sqlite3.Error:
        out["asks"] = []
    try:
        for r in con.execute("SELECT l.asset_bill_id, l.bill_id, b.month, b.bill_date, b.bill_no, b.supplier, b.amount_p FROM purchase_scan_link l "
                             "JOIN purchase_bill b ON b.id=l.bill_id"):
            out["link"][int(r[0])] = dict(bill=int(r[1]), month=r[2], bill_date=r[3], bill_no=r[4], supplier=r[5], amount_p=r[6])
    except sqlite3.Error:
        pass
    try:
        out["dec"] = {int(r[0]): dict(decision=r[1], raw_p=r[2], at=r[3], by=r[4]) for r in
                      con.execute("SELECT asset_bill_id, decision, raw_p, at, by FROM s736_decision")}
    except sqlite3.Error:
        out["dec"] = {}
    try:
        out["picked"] = {int(r[0]) for r in con.execute("SELECT drop_id FROM s708_scan_pick WHERE undone_at IS NULL")}
    except sqlite3.Error:
        pass
    try:
        out["dup"] = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_state WHERE why='dup'")}
    except sqlite3.Error:
        pass
    if sq is None:
        return out
    acon = OS._assets()
    if acon is None:
        return out
    try:
        try:
            out["settings"] = {str(r[0]): r[1] for r in acon.execute("SELECT key, value FROM settings WHERE key LIKE 'scan.%'")}
        except sqlite3.Error:
            pass
        since = str(sq.setting(out["settings"], "scan.redo_since") or "2026-10-08")[:10]
        out["since"] = since
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        want = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "bill_month", "total_amount", "submitted_at", "created_at", "lane", "kind",
                            "status", "page_of", "doc_kind", "source_stored", "rescan_of", "dup_of", "ocr_status") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE lane='pharmacy' AND substr(created_at,1,10)>=? ORDER BY id" % ", ".join(want), (since,))]
        have = {int(r["id"]) for r in rows}
        extra = ({int(a["asset_bill_id"]) for a in out["asks"]} | set(out["link"])) - have
        if extra:
            ids = sorted(extra)
            for i in range(0, len(ids), 500):
                part = ids[i:i + 500]
                rows += [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE id IN (%s)" % (", ".join(want), ",".join("?" * len(part))), part)]
        if "rescan_of" in cols:
            for r in acon.execute("SELECT id, rescan_of FROM bills WHERE rescan_of IS NOT NULL"):
                out["parent"][int(r[0])] = int(r[1])
                out["kids"].add(int(r[1]))
        lie = {}
        try:
            for r in acon.execute("SELECT * FROM scan_lie"):
                lie[(int(r["bill_id"]), r["file"])] = dict(r)
        except sqlite3.Error:
            pass
        ids = {int(r["id"]) for r in rows}
        try:
            for r in acon.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1"):
                if int(r[0]) in ids:
                    try:
                        out["reading"][int(r[0])] = json.loads(r[1]) if r[1] else None
                    except ValueError:
                        pass
        except sqlite3.Error:
            pass
        for r in rows:
            r["at"] = OS.scan_moment(r)
            r["lie"] = lie.get((int(r["id"]), r.get("source_stored")))
            out["rows"][int(r["id"])] = r
    finally:
        acon.close()
    out["ok"] = True
    return out


def _s736_month(f, sid, r):
    lk = f["link"].get(sid)
    if lk:
        return str(lk.get("month") or str(lk.get("bill_date") or "")[:7])
    return _s618_month(r)


def _s736_reason(f, sid, r, sq):
    """The scan's trouble as a reason code -- the scan_quality verdict, else 'unread' for a paired scan that read neither a total nor a
    bill number (scan_register.s726_state's own test) -- or None."""
    if str(r.get("created_at") or "")[:10] >= f["since"]:
        d = sq.detail(r, f["reading"].get(sid), r.get("lie"), f["settings"])
        if d:
            return d["code"]
    lk = f["link"].get(sid)
    ocr = str(r.get("ocr_status") or "")
    settled = ocr in ("", "read", "empty", "failed", "done") or (r.get("at") is not None and (OS.now() - r["at"]).total_seconds() > 6 * 3600)
    if lk is not None and settled and str(r.get("kind") or "") == "Pharmacy" and str(r.get("status") or "") == "captured":
        SR = _s736_sr()
        raw = SR._amount_p(r.get("total_amount"))
        if raw in (None, 0) and SR.billno(r.get("bill_no"), lk.get("bill_no")) == "not_read":
            return "unread"
    return None


def _s736_accepted(f, sid, r):
    d = f["dec"].get(sid)
    if not d or d.get("decision") != "accept":
        return False
    raw = _s736_sr()._amount_p(r.get("total_amount"))
    return (None if d.get("raw_p") is None else int(d["raw_p"])) == (None if raw is None else int(raw))


def s736_plan(con, now=None, facts=None):
    """READ ONLY: dict(ok, ask=[scans the server asks for now], withdraw=[ask ids it withdraws], escalated=[scans after two tries],
    facts). Each scan item: dict(scan, stamp, vendor, reason, month, tries, bill)."""
    f = facts if facts is not None else _s736_facts(con)
    out = dict(ok=f["ok"], ask=[], withdraw=[], escalated=[], facts=f)
    if not f["ok"]:
        return out
    sq = _sq()
    now = now or OS.now()
    by = {}
    for a in f["asks"]:
        by.setdefault(int(a["asset_bill_id"]), []).append(a)
    for sid in sorted(f["rows"]):
        r = f["rows"][sid]
        srv_open = [a for a in by.get(sid, []) if str(a.get("asked_by") or "") == S736_SERVER and not a.get("done_at") and not a.get("withdrawn_at")]
        gone = (str(r.get("status") or "") == "rejected" or r.get("page_of") or str(r.get("lane") or "") != "pharmacy" or sid in f["kids"]
                or sid in f["picked"] or sid in f["dup"] or r.get("dup_of")
                or str(r.get("kind") or "") == "Summary")             # S765: a dealer's summary (its filed kind) is no bill
        if gone:
            if srv_open and sid not in f["kids"]:             # set aside, moved off the pharmacy lane, a copy: the server's ask has no work left
                out["withdraw"] += [int(a["id"]) for a in srv_open]
            continue                                          # a rescanned scan: its open ask is closed by tie_pass (bills.rescan_of)
        reason = _s736_reason(f, sid, r, sq)
        month = _s736_month(f, sid, r)
        held = month_class(con, month) != "counted" or month in f["final"] or _s736_accepted(f, sid, r)
        if reason is None or held:
            if srv_open and (held or sid in f["reading"] or r.get("lie")):
                out["withdraw"] += [int(a["id"]) for a in srv_open]
            continue
        if by.get(sid):
            continue                                          # asked before (open, done or withdrawn): never asked twice by the server
        if r.get("at") is None or (now - r["at"]).total_seconds() < S736_SETTLE_MIN * 60:
            continue
        lk = f["link"].get(sid) or {}
        item = dict(scan=sid, stamp=r.get("stamp_no") or "#%d" % sid, vendor=(_pa().supplier_key(lk["supplier"]) if lk.get("supplier") else (r.get("vendor") or "")),
                    bill_no=str(lk.get("bill_no") or r.get("bill_no") or ""), reason=reason, month=month, tries=_s736_depth(f["parent"], sid),
                    bill=lk.get("bill"))
        (out["escalated"] if item["tries"] >= S736_TRIES else out["ask"]).append(item)
    for a in f["asks"]:                                       # S766: the scan was DELETED in the Scan App (assets.db no longer holds it,
        sid = int(a["asset_bill_id"])                         # _s736_facts fetched every asked id) -- the server's own open ask has no
        if (sid not in f["rows"] and sid not in f["kids"] and str(a.get("asked_by") or "") == S736_SERVER   # work left; a rescanned one
                and not a.get("done_at") and not a.get("withdrawn_at") and int(a["id"]) not in out["withdraw"]):   # is closed as done
            out["withdraw"].append(int(a["id"]))
    return out


def s736_raise(con, now=None):
    """The server's asking (the header above): writes the plan's asks and withdrawals, each audited; commits. -> dict(asked, withdrawn,
    plan). A fault is said on stderr and nothing is written."""
    try:
        p = s736_plan(con, now)
    except Exception as e:                                    # noqa: BLE001 -- the page never fails for it
        print("S736 plan failed: %r" % (e,), file=sys.stderr)
        return dict(asked=0, withdrawn=0, plan=None)
    n = w = 0
    if not p["ok"]:
        return dict(asked=0, withdrawn=0, plan=p)
    at = OS.now_iso()
    try:
        for x in p["ask"]:
            cur = con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at) SELECT ?,?,?,?,? "
                              "WHERE NOT EXISTS (SELECT 1 FROM scan_rescan_ask WHERE asset_bill_id=?)", (x["scan"], x["stamp"], x["reason"], S736_SERVER, at, x["scan"]))
            if cur.rowcount:
                n += 1
                OS.audit(con, S736_SERVER, "s736_server_ask", x["scan"], dict(ask=cur.lastrowid, stamp=x["stamp"], reason=x["reason"], try_n=x["tries"] + 1,
                                                                          month=x["month"], kit=S736_KIT))
        for aid in p["withdraw"]:
            cur = con.execute("UPDATE scan_rescan_ask SET withdrawn_at=?, withdrawn_by=? WHERE id=? AND asked_by=? AND done_at IS NULL AND withdrawn_at IS NULL",
                              (at, "server (S736: the scan is fine now)", aid, S736_SERVER))
            if cur.rowcount:
                w += 1
                OS.audit(con, S736_SERVER, "s736_server_ask_withdrawn", aid, dict(kit=S736_KIT))
        if n or w:
            con.commit()
    except sqlite3.Error as e:
        con.rollback()
        print("S736 raise failed: %r" % (e,), file=sys.stderr)
        return dict(asked=0, withdrawn=0, plan=p)
    return dict(asked=n, withdrawn=w, plan=p)


def _s736_raise_soft(con):
    try:
        return s736_raise(con)
    except Exception as e:                                    # noqa: BLE001
        print("S736 raise failed: %r" % (e,), file=sys.stderr)
        return dict(asked=0, withdrawn=0, plan=None)


def s736_view(con):
    """READ ONLY, for the owner's step view: dict(ok, asks=[open asks with month, try, who], escalated=[...], decided=[...])."""
    p = s736_plan(con)
    f = p["facts"]
    out = dict(ok=f["ok"], asks=[], escalated=p["escalated"], decided=[])
    for a in f["asks"]:
        if a.get("done_at") or a.get("withdrawn_at"):
            continue
        sid = int(a["asset_bill_id"])
        r = f["rows"].get(sid) or {}
        lk = f["link"].get(sid) or {}
        out["asks"].append(dict(id=int(a["id"]), scan=sid, stamp=a.get("stamp") or r.get("stamp_no") or "#%d" % sid, reason=a.get("reason") or "",
                                by=str(a.get("asked_by") or ""), try_n=_s736_depth(f["parent"], sid) + 1,
                                month=(_s736_month(f, sid, r) if r else str(lk.get("month") or "")), bill=lk.get("bill")))
    for sid, d in sorted(f["dec"].items()):
        r = f["rows"].get(sid) or {}
        lk = f["link"].get(sid) or {}
        out["decided"].append(dict(scan=sid, decision=d.get("decision"), at=d.get("at"), by=d.get("by"), stamp=r.get("stamp_no") or "#%d" % sid,
                                   vendor=(_pa().supplier_key(lk["supplier"]) if lk.get("supplier") else (r.get("vendor") or "")),
                                   bill_no=str(lk.get("bill_no") or ""), month=(_s736_month(f, sid, r) if r else str(lk.get("month") or ""))))
    return out


# ------------------------------------------------------------------ the page
def _s736_try(en, n):
    if n <= 1:
        return L(en, "bk_try1")
    if n == 2:
        return L(en, "bk_try2")
    return L(en, "bk_tryn", n)


def _s736_by(en, con, a):
    login = str(a.get("asked_by") or "").lower()
    day = OS.ddmm(a.get("asked_at") or "")
    if login == S736_SERVER:
        return L(en, "bk_by_server", day)
    if a.get("by_owner") or login in _s618_owner_logins(con):
        return L(en, "bk_by_owner", day)
    return L(en, "bk_by_x", login.split(" ")[0].title() or "?", day)


def _s736_fields(en, q, meta, bill):
    """The question's lines: each field that differs or was not read, with what the scan read against Marg, then what matches."""
    if q.get("unread"):
        return [L(en, "bk_f_none")]
    SR = _s736_sr()
    lines, same = [], []
    sno = str(meta.get("bill_no") or "")
    bn = SR.billno_compat(sno, bill.get("bill_no"))
    if bn == "not_read":
        lines.append(L(en, "bk_f_no"))
    elif bn in ("differ", "close"):
        lines.append(L(en, "bk_f_nod", esc(sno), esc(bill.get("bill_no") or "")))
    else:
        same.append(L(en, "bk_w_no"))
    sp = SR._amount_p(meta.get("total_amount"))
    if sp in (None, 0):
        lines.append(L(en, "bk_f_amt"))
    elif abs(int(sp) - int(bill.get("amount_p") or 0)) > 100:
        lines.append(L(en, "bk_f_amtd", esc(SR.rs2(sp)), esc(SR.rs2(bill.get("amount_p")))))
    else:
        same.append(L(en, "bk_w_amt"))
    dm = SR.date_md(meta.get("bill_date"), bill.get("bill_date"))
    if dm == "differ":
        lines.append(L(en, "bk_f_date", esc(OS.ddmm(meta.get("bill_date"))), esc(OS.ddmm(bill.get("bill_date")))))
    elif dm == "agree":
        same.append(L(en, "bk_w_date"))
    if lines:
        w = [L(en, "bk_w_sup")] + same                        # the question is this supplier's bill: the supplier always matches
        lines.append(L(en, "bk_f_same", w[0] if len(w) == 1 else ", ".join(w[:-1]) + L(en, "bk_and") + w[-1]))
    return lines or [L(en, "bk_f_check")]


def s736_model(con, now=None, raised=None):
    """The page's four groups as plain rows (read only; the server's asking is done by the caller). -> dict(redo, paper, scan, q, today, n)."""
    now = now or OS.now()
    f = ((raised or {}).get("plan") or {}).get("facts") or _s736_facts(con)
    x = rescan_list(con)
    owners = _s618_owner_logins(con)
    redo = []
    for a in sorted(x.get("asks") or [], key=lambda z: (str(z.get("asked_at") or ""), z["id"])):
        sid = int(a["scan"])
        lk = f["link"].get(sid) or {}
        r = f["rows"].get(sid) or {}
        redo.append(dict(a, by_owner=a.get("by_owner") or str(a.get("asked_by") or "").lower() in owners, try_n=_s736_depth(f["parent"], sid) + 1,
                         head_vendor=(_pa().supplier_key(lk["supplier"]) if lk.get("supplier") else (a.get("vendor") or r.get("vendor") or "")),
                         head_no=str(lk.get("bill_no") or r.get("bill_no") or "")))
    paper = []
    try:
        import order_track_page as OTP                        # noqa: PLC0415
        for oid, ask in sorted(OTP.paper_asks(con, reception_only=True).items(), key=lambda z: z[1]["id"]):
            o = con.execute("SELECT id, vendor, created_at FROM purchase_order WHERE id=?", (oid,)).fetchone()
            if o is not None:
                paper.append(dict(order=int(o["id"]), vendor=o["vendor"] or "", created_at=o["created_at"] or "", ask=int(ask["id"])))
    except Exception:                                         # noqa: BLE001 -- its own page still lists them
        paper = []
    scan = scan_lines(con)
    qs = [q for q in questions(con) if q["kind"] == "bill"]
    meta = _scan_meta({q["scan"] for q in qs})
    for q in qs:
        b = con.execute("SELECT id, supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (q["bill"],)).fetchone()
        q["_bill"] = dict(b) if b else {}
        q["_meta"] = meta.get(q["scan"]) or {}
    today = now.date()
    todays = [r for r in f["rows"].values() if r.get("at") and r["at"].date() == today and str(r.get("status") or "") != "rejected" and not r.get("page_of")
              and str(r.get("lane") or "") == "pharmacy"]
    nread = sum(1 for r in todays if int(r["id"]) in f["reading"])
    return dict(redo=redo, paper=paper, scan=scan, q=qs, today=(len(todays), nread), n=len(redo) + len(paper) + len(scan) + len(qs), ok=f["ok"])


def _s736_home(con, c):
    """Reception's home row: (counts, ok). The Photo dekh kar bataiye row keeps the questions that are not on this page."""
    try:
        m = s736_model(con)
    except Exception as e:                                    # noqa: BLE001 -- the old rows stand
        print("S736 home model failed: %r" % (e,), file=sys.stderr)
        return c, False
    c = dict(c, billkaam=m["n"], q=max(0, int(c.get("q") or 0) - len(m["q"])))
    return c, True


def _s736_more(en, key, n, shown, total):
    if total <= shown:
        return ""
    return '<a class="more" id="more_%s" href="?all=%s">%s</a>' % (key, key, L(en, "bk_more", total - shown))


def billkaam_page():
    """Aaj ka bill kaam -- reception's ONE list (the header above). The server's asking runs first."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    _every_read(con)
    raised = _s736_raise_soft(con)
    m = s736_model(con, raised=raised)
    sq = _sq()
    allk = str(request.args.get("all") or "")
    back = P + "/s454/billkaam"
    h = ['<div class="mut" id="bktop">%s</div>' % L(en, "bk_top")]
    if m["redo"]:
        h.append('<div class="grp red" id="g_redo">%s</div>' % L(en, "bk_redo", len(m["redo"])))
        lim = len(m["redo"]) if allk == "redo" else S736_SHOW
        for a in m["redo"][:lim]:
            what = sq.words(a.get("reason"), "owner" if en else "reception") if sq else (a.get("reason") or "")
            head = " · ".join(z for z in (a["head_vendor"], (L(en, "billno", a["head_no"]) if a["head_no"] else ""), L(en, "bk_scan_no", a.get("stamp") or "#%d" % a["scan"])) if z)
            h.append('<div class="card" data-redo="%d" data-scan="%d" data-try="%d" data-by="%s"><div class="nm">%s</div><div class="red">%s</div>'
                     '<div class="sb">%s · %s</div><div><a class="sk" style="display:inline-flex;align-items:center;min-height:48px;padding:0 22px;border-radius:10px;'
                     'background:#1f3864;color:#fff;font-weight:700;text-decoration:none" href="%s">%s</a></div></div>'
                     % (a["id"], a["scan"], a["try_n"], esc(str(a.get("asked_by") or "")), esc(head), esc(what), esc(_s736_try(en, a["try_n"])),
                        esc(_s736_by(en, con, a)), esc(_s618_intake(a["head_vendor"] or a.get("vendor") or "", a.get("month") or "", a["scan"], back)), L(en, "scankaro")))
        h.append(_s736_more(en, "redo", lim, lim, len(m["redo"])))
    if m["paper"]:
        h.append('<div class="grp amb" id="g_paper">%s</div>' % L(en, "bk_paper", len(m["paper"])))
        for p_ in m["paper"]:
            h.append('<div class="ln" data-paper="%d"><div class="t"><div class="a">%s</div><div class="s">%s</div></div><a class="sk" href="%s/s454/rescan">%s</a></div>'
                     % (p_["ask"], esc(p_["vendor"]), esc(L(en, "bk_paper_s", OS.ddmm(p_["created_at"]))), P, L(en, "bk_open")))
    if m["scan"]:
        h.append('<div class="grp" id="g_scan" style="color:#1f3864">%s</div>' % L(en, "bk_scan", len(m["scan"])))
        lim = len(m["scan"]) if allk == "scan" else S736_SHOW
        t = OS.today()
        for x in m["scan"][:lim]:
            if x["kind"] == "recv":
                h.append('<div class="card" data-scanline="recv" data-order="%d"><div class="nm">%s</div><div class="sb">%s</div>'
                         '<div class="two"><a class="g" href="%s">%s</a></div></div>'
                         % (int(x.get("order_id") or 0), esc(L(en, "bk_recv", x["vendor"], OS.ddmm(x["date"]))), L(en, "bk_recv_s"),
                            esc(_s736_back(x["intake"], back)), L(en, "scankaro")))
                continue
            bd = OS._date(x.get("date"))
            days = (t - bd).days if bd else 0
            wait = L(en, "bk_days", days) if days > 0 else L(en, "bk_today")
            h.append('<div class="card" data-scanline="marg" data-bill="%d"><div class="nm">%s · %s · %s · %s</div><div class="sb">%s</div>'
                     '<div class="two"><a class="g" href="%s">%s</a><button class="b" onclick="s454(\'%s/api/s454/paper_missing\',{bills:[%d]})">%s</button></div></div>'
                     % (x["bill_id"], esc(x["vendor"]), esc(L(en, "billno", x["bill_no"])), esc(OS.ddmm(x["date"])), esc(rs(x["amount_p"])), esc(wait),
                        esc(_s736_back(x["intake"], back)), L(en, "scankaro"), P, x["bill_id"], L(en, "bk_missing")))
        h.append(_s736_more(en, "scan", lim, lim, len(m["scan"])))
    if m["q"]:
        h.append('<div class="grp amb" id="g_q">%s</div>' % L(en, "bk_q", len(m["q"])))
        lim = len(m["q"]) if allk == "q" else S736_SHOW
        for q in m["q"][:lim]:
            b = q["_bill"]
            lines = _s736_fields(en, q, q["_meta"], b)
            body = esc(json.dumps(dict(scan=q["scan"], bill=q["bill"])))
            h.append('<div class="card" data-q="%d" data-bill="%d"><div class="nm">%s</div><div style="display:flex;gap:10px">'
                     '<a href="%s" target="_blank" rel="noopener" style="flex:1 1 0;min-width:0;min-height:120px;display:flex;align-items:center;justify-content:center;'
                     'background:#eef0f4;border-radius:8px;color:#555;font-size:13px;text-align:center;text-decoration:none;padding:4px">'
                     '<img src="%s" alt="%s" style="width:100%%;max-height:200px;object-fit:contain;border-radius:8px" '
                     'onerror="this.replaceWith(document.createTextNode(this.alt))"></a>'
                     '<div style="flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:3px;font-size:14.5px"><b>%s</b><div>%s · %s</div><div>%s · %s</div>%s</div></div>'
                     '<div class="two"><button class="g" onclick="s454(\'%s/api/s454/confirm\',Object.assign(%s,{yes:true}))">%s</button>'
                     '<button class="b" style="color:#8c1d18;border-color:#8c1d18" onclick="s454(\'%s/api/s454/confirm\',Object.assign(%s,{yes:false}))">%s</button></div></div>'
                     % (q["scan"], q["bill"], L(en, "bk_q_dup") if q.get("taken") else L(en, "bk_q_h"), esc(q["pdf"]), esc(q["thumb"]), esc(L(en, "bk_photo", q.get("stamp") or "")),
                        L(en, "bk_marg"), esc(q["vendor"]), esc(b.get("bill_no") or q.get("bill_no") or ""), esc(OS.ddmm(b.get("bill_date") or "")),
                        esc(rs(b.get("amount_p"))) if b.get("amount_p") is not None else esc(q.get("amount") or ""),
                        "".join('<div style="color:#8a5300">%s</div>' % ln for ln in lines), P, body, L(en, "bk_yes"), P, body, L(en, "bk_no")))
        h.append(_s736_more(en, "q", lim, lim, len(m["q"])))
    if not m["n"]:
        h.append('<div class="ok" id="alldone"><div class="t">%s</div></div>' % L(en, "bk_none"))
    nt, nr = m["today"]
    h.append('<div class="mut" id="bkaaj" style="background:#e9f2ea;border-radius:10px;padding:10px 12px;color:#1f4d25">%s</div>'
             % (L(en, "bk_aaj0") if not nt else (L(en, "bk_aaj_ok", nt) if nr >= nt else L(en, "bk_aaj_n", nt, nr))))
    return shell(con, u, L(en, "r_billkaam"), "".join(h), back=P, login=login)


def _s736_back(href, back):
    """The intake link with its 'from' set to this page (so the Back of the scan screen returns here)."""
    try:
        from urllib.parse import parse_qsl, urlsplit         # noqa: PLC0415
        sp = urlsplit(href)
        q = [(k, v) for k, v in parse_qsl(sp.query, keep_blank_values=True) if k != "from"] + [("from", back)]
        return sp.path + "?" + urlencode(q)
    except Exception:                                         # noqa: BLE001
        return href


def _s736_escalated_html(con, en):
    """Shavez's Scans to redo: the scans reception has rescanned twice and that are still in trouble (READ ONLY)."""
    try:
        p = s736_plan(con)
    except Exception:                                         # noqa: BLE001
        return ""
    if not p["escalated"]:
        return ""
    sq = _sq()
    h = ['<div class="grp red" id="redo_esc">%s</div>' % L(en, "bk_esc", len(p["escalated"]))]
    for x in p["escalated"]:
        what = S736_REASON_EN.get(x["reason"], x["reason"]) if en else (sq.words(x["reason"], "shavez") if sq else x["reason"])
        h.append('<div class="card" data-esc="%d"><div class="nm">%s</div><a class="more" href="/scanapp/bills/%d/file" target="_blank" rel="noopener">%s</a></div>'
                 % (x["scan"], esc(L(en, "bk_esc_s", x["stamp"], " ".join(z for z in (x["vendor"], x["bill_no"]) if z), what)), x["scan"], L(en, "redo_open")))
    return "".join(h)


@bp.route(P + "/s454/billkaam")
def r_billkaam():
    return billkaam_page()


_sq_before_s736 = _sq


class _S736Words(object):
    """scan_quality with the server's own reason ('unread') and the server as the sender -- every screen that reads the asks (this file's,
    order_track_page's) says them in words, never the bare code."""

    def __init__(self, m):
        self._m = m

    def __getattr__(self, k):
        return getattr(self._m, k)

    def words(self, code, who="owner", a=None, b=None):
        w = S736_WORDS.get(code)
        if w:
            return w[self._m.AUDIENCE.get(who, 0)]
        return self._m.words(code, who, a, b)

    def sent_by(self, kind, login=""):
        if str(login or "").lower() == S736_SERVER:
            return "Server ne khud bheja"
        return self._m.sent_by(kind, login)


def _sq():                                                    # noqa: F811 -- S736: the words above, over scan_quality's own
    m = _sq_before_s736()
    return _S736Words(m) if m is not None else None
# ---- S736 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S740 (07-Nov-2026, Sanjeevni session 399, kit S740_PURCHASE_RETURNS; D839 kit 3 as the owner refined it 06:02 - 06:28 IST) -------------
#  RECEPTION'S ONE QUESTION ON A RETURN: on "Aaj ka bill kaam", a group "Ek sawaal · wapsi" -- for every bill whose paper reads MORE than Marg
#  (scan_register.s740_model's questions): "Bill par ya parchi par wapsi (return) likhi hai?" with the scan's photo, Haan / Nahi. One tap; the
#  line leaves. POST /finance/porders/api/s740/wapsi {bill, yes}. A Marg purchase return with no paper reads on the Scan karo card as
#  "Wapsi ka kaagaz (credit note)" with its size (never a minus figure), and porders' amount question is never raised for a purchase return.
#  The list keeps the returns' tracker in step (scan_register.s740_sync) when it is read.
S740_KIT = "S740_PURCHASE_RETURNS"
T.update({"bk_q740": ("Ek sawaal · wapsi · %d", "A question · a return · %d"),
          "bk_q740_h": ("Bill par ya parchi par wapsi (return) likhi hai?", "Is a return written on the bill or on a slip?"),
          "bk_q740_s": ("Kaagaz par %s · Marg mein %s", "The paper %s · Marg %s"),
          "bk_q740_y": ("Haan, wapsi likhi hai", "Yes, a return is written"), "bk_q740_n": ("Nahi", "No"),
          "bk_q740_p": ("Scan %s ki photo kholo", "Open the photo of scan %s"),
          "bk_ret": ("Wapsi ka kaagaz (credit note)", "The return's paper (credit note)")})


def _s740_sr():
    import scan_register as SR                                # noqa: PLC0415
    return SR


_s736_model_before_s740 = s736_model


def s736_model(con, now=None, raised=None):                   # noqa: F811 -- S740: + the return question; a purchase return's card by its size
    m = _s736_model_before_s740(con, now, raised)
    q740 = []
    try:
        q740 = _s740_sr().s740_model(con)["questions"]
    except Exception as e:                                    # noqa: BLE001 -- the page stands without it
        print("S740 questions failed: %r" % (e,), file=sys.stderr)
    for x in m.get("scan") or []:
        if x.get("kind") == "marg" and int(x.get("amount_p") or 0) < 0:
            x["amount_p"] = -int(x["amount_p"])
            x["s740_ret"] = True
    m["q740"] = q740
    m["n"] = int(m.get("n") or 0) + len(q740)
    return m


_billkaam_page_before_s740 = billkaam_page


def billkaam_page():                                          # noqa: F811
    out = _billkaam_page_before_s740()
    if not (isinstance(out, tuple) and len(out) == 3 and isinstance(out[0], str)):
        return out
    page, code, hdr = out
    try:
        u, con, kind, login, err = _auth_page()
        if err:
            return out
        en = u["_en"]
        try:
            _s740_sr().s740_sync(con)
        except Exception as e:                                # noqa: BLE001
            con.rollback()
            print("S740 sync on billkaam failed: %r" % (e,), file=sys.stderr)
        m = _s740_sr().s740_model(con)
        h = []
        if m["questions"]:
            h.append('<div class="grp amb" id="g_q740">%s</div>' % L(en, "bk_q740", len(m["questions"])))
            for q in m["questions"]:
                photo = ('<a class="more" href="/scanapp/bills/%d/file" target="_blank" rel="noopener">%s</a>'
                         % (int(q["scan"]), esc(L(en, "bk_q740_p", q.get("stamp") or "")))) if q.get("scan") is not None else ""
                h.append('<div class="card" data-q740="%d"><div class="nm">%s · %s · %s</div><div class="sb">%s</div><div style="font-size:16px;font-weight:700;margin-top:4px;color:#8a5300">%s</div>%s'
                         '<div class="two"><button class="g" onclick="s454(\'%s/api/s740/wapsi\',{bill:%d,yes:true})">%s</button>'
                         '<button class="b" onclick="s454(\'%s/api/s740/wapsi\',{bill:%d,yes:false})">%s</button></div></div>'
                         % (int(q["bill_id"]), esc(q["supplier"]), esc(L(en, "billno", q["bill_no"])), esc(OS.ddmm(q["date"])),
                            esc(L(en, "bk_q740_s", rs(q["paper_p"]), rs(q["marg_p"]))), L(en, "bk_q740_h"), photo, P, int(q["bill_id"]),
                            L(en, "bk_q740_y"), P, int(q["bill_id"]), L(en, "bk_q740_n")))
        add = "".join(h)
        if add:
            if '<div class="ok" id="alldone">' in page:
                page = re.sub(r'<div class="ok" id="alldone">.*?</div></div>', "", page, count=1, flags=re.S)
            page = page.replace('<div class="mut" id="bkaaj"', add + '<div class="mut" id="bkaaj"', 1)
        page = re.sub(r'(<div class="card" data-scanline="marg" data-bill="(\d+)"><div class="nm">)',
                      lambda mm: mm.group(1) + (esc(L(en, "bk_ret")) + " · " if int(mm.group(2)) in _s740_neg(con) else ""), page)
    except Exception as e:                                    # noqa: BLE001 -- the page stands as S736 drew it
        print("S740 billkaam failed: %r" % (e,), file=sys.stderr)
    return page, code, hdr


def _s740_neg(con):
    try:
        return {int(r[0]) for r in con.execute("SELECT id FROM purchase_bill WHERE amount_p<0")}
    except Exception:                                         # noqa: BLE001
        return set()


@bp.route(P + "/api/s740/wapsi", methods=["POST"])
def api_s740_wapsi():
    """Reception's answer: is a return written on the bill or on a slip? (scan_register.s740_answer_put)"""
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s740_sr().s740_answer_put(con, who(u), bid, bool(b.get("yes")))
    if not ok:
        return jsonify(ok=False, error="gone", message=msg), 409
    return jsonify(ok=True)


try:                                                          # porders' amount question: a purchase return is compared by its size
    _s440_differs_before_s740 = _po()._s440_differs

    def _s740_differs(scan_p, marg_p, ym=None):
        try:
            mp = int(marg_p or 0)
        except (TypeError, ValueError):
            mp = 0
        if mp < 0:                                            # a purchase return: never reception's amount question (S440 would mark it WRONG
            return False                                      # at a plus figure); S740 puts a differing credit note on Amir's card, paper beside him
        try:                                                  # a dealer's later bill that took a return off, held in Marg at the goods as S740
            sp = int(scan_p or 0)                             # requires: its paper is right and so is Marg -- never a question (S440 would mark
            for pp, cm in _s740_sr().s740_model(_po()._db()).get("later_ok") or ():   # it WRONG at the net figure: the return counted twice)
                if abs(sp - pp) <= 100 and abs(mp - cm) <= 100:   # that very bill: its paper and its current Marg figure
                    return False
        except Exception:                                     # noqa: BLE001 -- the question as before
            pass
        return _s440_differs_before_s740(scan_p, marg_p, ym)

    _po()._s440_differs = _s740_differs
except Exception as _e_s740:                                  # noqa: BLE001
    print("S740: porders._s440_differs not wrapped: %r" % (_e_s740,), file=sys.stderr)
# ---- S740 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S750 (08-Nov-2026, Sanjeevni session 406, kit S750_MONTH_END; D849): the dealer's summary on Aaj ka bill kaam ---------------------------
#  When the owner taps 'Ask reception to scan it' on a dealer's line of row 7 (or 'Ask reception to rescan' on one that could not be read),
#  reception's one list gets a card: "<Dealer> ka <month> ka hisaab (summary) scan karo" with the scan screen's link (lane Pharmacy, the
#  dealer filled in) and the one instruction -- press the 'Dealer ka mahine ka hisaab (summary) hai' button when scanning. The card leaves
#  by itself when the summary's scan has come (scan_register.s750_reception_asks). Reads only; the home row's count carries it.
KIT_S750 = "S750_MONTH_END"
_s736_model_before_s750 = s736_model
_billkaam_page_before_s750 = billkaam_page
T.update({"bk_s750": ("Dealer ka hisaab (summary) scan karo · %d", "Scan the dealer's month summary · %d"),
          "bk_s750_h": ("%s ka %s ka hisaab (summary) scan karo", "Scan %s's %s summary"),
          "bk_s750_r": ("%s ke hisaab (summary) ko dobara scan karo — pehla padha nahi gaya", "Rescan %s's summary — the first could not be read"),
          "bk_s750_s": ("Scan karte waqt 'Dealer ka mahine ka hisaab (summary) hai' button dabaiye.", "When scanning, press the 'Dealer ka mahine ka hisaab (summary) hai' button."),
          "bk_s750_since": ("Doctor sahab ne %s ko kaha", "Asked by the doctor %s"),
          "bk_s750_auto": ("%s khatam — dealer ka hisaab (summary) abhi tak nahi aaya", "%s has ended — the dealer's summary has not come yet")})   # S755


def _s750_sr():
    import scan_register                                      # noqa: PLC0415
    return scan_register


def _s750_asks(con):
    try:
        return _s750_sr().s750_reception_asks(con)
    except Exception as e:                                    # noqa: BLE001 -- the list stands as it was
        print("porders_s454 S750: the summary asks could not be read: %r" % (e,), file=sys.stderr)
        return []


def s736_model(con, now=None, raised=None):                   # noqa: F811 -- S750: + the owner's summary asks
    m = _s736_model_before_s750(con, now=now, raised=raised)
    asks = _s750_asks(con)
    m["s750"] = asks
    m["n"] = int(m.get("n") or 0) + len(asks)
    return m


def _s750_month_hi(ym, en):
    try:
        return "%s %s" % (month_name(ym), ym[:4])
    except (TypeError, IndexError):
        return str(ym or "")


def billkaam_page():                                          # noqa: F811 -- S750
    out = _billkaam_page_before_s750()
    if not (isinstance(out, tuple) and len(out) == 3 and isinstance(out[0], str)):
        return out
    page, code, hdr = out
    try:
        u, con, kind, login, err = _auth_page()
        if err:
            return out
        en = u["_en"]
        asks = _s750_asks(con)
        if not asks:
            return out
        back = P + "/s454/billkaam"
        h = ['<div class="grp" id="g_s750" style="color:#1f3864">%s</div>' % L(en, "bk_s750", len(asks))]
        for a in asks:
            head = L(en, "bk_s750_r", a["name"].title()) if a["kind"] == "rescan" else L(en, "bk_s750_h", a["name"].title(), _s750_month_hi(a["month"], en))
            h.append('<div class="card" data-s750="%s|%s"><div class="nm">%s</div><div class="sb">%s · %s</div>'
                     '<div class="two"><a class="g" href="%s">%s</a>%s</div></div>'
                     % (esc(a["dealer"]), esc(a["month"]), esc(head), esc(L(en, "bk_s750_s")),
                        esc(L(en, "bk_s750_auto", _s750_month_hi(a["month"], en)) if a.get("auto") else L(en, "bk_s750_since", OS.ddmm(str(a.get("at") or "")[:10]))),   # S755
                        esc(_s736_back(intake(a["name"], back=back), back)), L(en, "scankaro"),
                        ('<a class="more" href="/scanapp/bills/%d/file" target="_blank" rel="noopener">%s</a>' % (int(a["scan"]), esc(L(en, "bk_scan_no", a.get("stamp") or "")))) if a.get("scan") else ""))
        add = "".join(h)
        if '<div class="ok" id="alldone">' in page:
            page = re.sub(r'<div class="ok" id="alldone">.*?</div></div>', "", page, count=1, flags=re.S)
        page = page.replace('<div class="mut" id="bkaaj"', add + '<div class="mut" id="bkaaj"', 1)
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was
        print("S750 billkaam failed: %r" % (e,), file=sys.stderr)
    return page, code, hdr
# ---- S750 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S778 (10-Nov-2026, Sanjeevni session 425, kit S778_ORDER_SCREEN; D890, the owner's mock approved 15:08 IST) ------------------------
#  The order screen (order_s778.py beside this file holds the logic):
#   (a) Order karna hai opens with the OLD ORDERS in a red box -- ordered, not come 3 days after (Sundays not counted), the age big,
#       'Dobara order karo' / 'Ab nahi milta'; the dealer's card names its old lines 'PURANA · N din'.
#   (b) 'Ab nahi milta' on a card line or a red-box line: off today's list at once; the doctor's Needs-you line opens
#       /finance/porders/s454/abnahi (Stop it everywhere / Keep ordering / Undo).
#   (c) the wrong-dealer check on the cards and in the red box ('<X> ke card par bhejo' / '<dealer> hi sahi', remembered).
#  order_sheet.entries / order_supplier / cron_pass and order_rules.needs_you_lines are wrapped here, fail-soft: an error in S778 leaves
#  every screen as it was before it. POST /finance/porders/api/s778/{again, na, na_answer (owner), dealer_ok, move}.
def _s778():
    import order_s778                                         # noqa: PLC0415 -- beside this file
    return order_s778


def _s778_log(where, e):
    print("S778 %s failed: %r" % (where, e), file=sys.stderr)


def _s778_g():
    from flask import g                                       # noqa: PLC0415
    return g


_s778_entries_before = OS.entries
_s778_order_supplier_before = OS.order_supplier
_s778_cron_before = OS.cron_pass


def _s778_entries(con, *a, **k):
    out = _s778_entries_before(con, *a, **k)
    try:
        return _s778().adjust_entries(con, [dict(e, lines=list(e["lines"])) for e in out])
    except Exception as e:                                    # noqa: BLE001 -- the cards as order_sheet made them
        _s778_log("entries", e)
        return out


def _s778_order_supplier(con, who_, sn, via):
    body, code = _s778_order_supplier_before(con, who_, sn, via)
    try:
        if code == 200 and body.get("ok") and body.get("order_id") and not body.get("already"):
            _s778().mark_done(con, sn, body["order_id"])
    except Exception as ex:                                   # noqa: BLE001
        _s778_log("order_supplier mark", ex)
    return body, code


def _s778_cron(con, who_="cron"):
    out = _s778_cron_before(con, who_)
    try:
        out["s778"] = _s778().clear_by_bills(con)
    except Exception as e:                                    # noqa: BLE001
        out["s778"] = "error: %s" % str(e)[:80]
    return out


OS.entries = _s778_entries
OS.order_supplier = _s778_order_supplier
OS.cron_pass = _s778_cron
try:
    import order_rules as _s778_OR                            # noqa: E402
    _s778_nyl_before = _s778_OR.needs_you_lines

    def _s778_nyl(con):
        out = _s778_nyl_before(con)
        try:
            return list(out) + _s778().owner_lines(con)
        except Exception as e:                                # noqa: BLE001
            _s778_log("needs_you", e)
            return out
    _s778_OR.needs_you_lines = _s778_nyl
except Exception as _e778:                                    # noqa: BLE001
    _s778_log("needs_you wrap", _e778)

_s778_order_list_before = order_list
_s778_card_before = _card
_s778_supplier_page_before = supplier_page
S778_MARK = '<div id="msg" class="err" style="display:none"></div>'


def order_list():                                             # noqa: F811 -- S778: the red box at the top, the cards' tags and warnings
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    g = None
    try:
        g = _s778_g()
        g.s778_con = con
    except Exception as e:                                    # noqa: BLE001
        _s778_log("order_list g", e)
    r = _s778_order_list_before()
    try:
        import order_rules                                    # noqa: PLC0415
        if isinstance(r, tuple) and r[1] == 200 and not order_rules._frozen(con) and S778_MARK in r[0]:
            S, en = _s778(), u["_en"]
            add = '<style>%s</style>%s%s' % (S.CSS, S.ok_html(en, request.args), S.red_box(con, en))
            n = S.wrong_count(con, OS.entries(con))
            if n:
                add += '<div class="s778wd" id="s778wdtop">%s</div>' % esc(S.T(en, "wd_top", n, "" if n == 1 else "s") if en else S.T(en, "wd_top", n))
            page = r[0].replace(S778_MARK, S778_MARK + add, 1)
            if 'id="s778box"' in add:                         # the old lines are in the box at the top: S543's link to them is not repeated
                page = re.sub(r'<div class="lnk"><a id="oldlink" [^>]*>[^<]*</a></div>', "", page, count=1)
            r = (page,) + tuple(r[1:])
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was
        _s778_log("order_list", e)
    finally:
        if g is not None:
            g.s778_con = None
    return r


def _card(en, e, sent=False):                                 # noqa: F811 -- S778: the old lines named, the wrong-dealer warnings
    h = _s778_card_before(en, e, sent)
    try:
        con = getattr(_s778_g(), "s778_con", None)
        if con is not None:
            x = _s778().card_extra(con, en, e)
            if x and '</div><div class="two">' in h:
                h = h.replace('</div><div class="two">', x + '</div><div class="two">', 1)
    except Exception as ex:                                   # noqa: BLE001
        _s778_log("card", ex)
    return h


def supplier_page(sn):                                        # noqa: F811 -- S778: S543's screen, each line with its age, Ab nahi milta, the warning
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    try:
        return _s778_supplier_page(u, con, kind, login, sn)
    except Exception as e:                                    # noqa: BLE001 -- the screen as it was before S778
        _s778_log("supplier_page", e)
        return _s778_supplier_page_before(sn)


def _s778_supplier_page(u, con, kind, login, sn):
    S = _s778()
    en = u["_en"]
    import order_rules                                        # noqa: PLC0415
    if order_rules._frozen(con):
        return shell(con, u, L(en, "order"), '<div class="err">%s</div>' % L(en, "frozen"), back=P + "/s454/order", login=login)
    e = OS.entry_of(con, sn)
    olds = OS.old_lines(con, sn)
    vendor = e["vendor"] if e else (olds[0]["supplier"] if olds else sn)
    h = ['<style>%s</style>' % S.CSS, S.ok_html(en, request.args), '<h1>%s</h1>' % esc(vendor)]
    edit = request.args.get("edit") == "1"
    if e:
        ages = S.old_of(con, e["sn"])
        h.append('<div class="mut">%s</div>' % L(en, "likhwaiye"))
        items = []
        for l in e["lines"]:
            age = next((ages[f] for f in S.forms(con, l["item"], e["sn"]) if f in ages), 0)
            tag = _s619_carry_tag(en, l) + S.tag_html(en, age)
            q = OS.qty_of(l, en, con=con)                     # S543: qty_words, the shop's one nomenclature
            if edit and l["src"] != "draft":
                b = esc(json.dumps(dict(src=l["src"], ref=l["ref"], item=l["item"])))
                ctl = ('<span class="qbox"><button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:-1}))">−</button><b>%d</b>'
                       '<button class="pm" onclick="s454(\'%s/api/s454/qty\',Object.assign(%s,{delta:1}))">+</button></span>'
                       % (P, b, int(l["qty"]), P, b)) + _s619_remove_chips(en, b)           # S619: the one remove door asks a reason
                items.append('<div class="li" style="flex-wrap:wrap"><span class="i">%s%s</span>%s</div>' % (esc(l["item"]), tag, ctl))
            else:
                items.append('<div class="li" style="flex-wrap:wrap"><span class="i">%s%s</span><span class="q">%s</span>%s</div>'
                             % (esc(l["item"]), tag, esc(q), S.na_button(en, e, l)))
            items.append(S.line_wrong_html(con, en, e, l))
        h.append('<div class="list" id="lines">%s</div>' % "".join(items))
        if e["has_phone"]:
            if e.get("book_on"):                              # S574: the Calls number and the Order WhatsApp number, to read only
                nums = ('<div class="num" id="numcall">%s</div><div class="num" id="numwa">%s</div>'
                        % (esc(L(en, "num_call", e["phone"])), esc(L(en, "num_wa", e["wa"]))))
            else:
                nums = "".join('<div class="num">%s</div>' % esc(x) for x in e["shown"])
            h.append('<div><a class="big blue" id="callkaro" href="tel:%s" onclick="s454(\'%s/api/s454/call\',{sn:%s},function(){})">📞 %s</a>%s</div>'
                     % (esc(_tel(e["phone"])), P, esc(json.dumps(e["sn"])), L(en, "callkaro"), nums))
            h.append('<div class="mut" style="text-align:center">%s</div>' % L(en, "baat"))
        else:
            h.append('<div class="mut" id="nophone">%s</div>' % L(en, "nonum" if e.get("book_on") else "nophone_l"))   # S574
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


def s778_abnahi_page():
    """The doctor's answers to 'Ab nahi milta' and the week's wrong-dealer catches (owner only, English)."""
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    if kind != "owner":
        return redirect(P + "/s454/order")
    S = _s778()
    return shell(con, u, "Out of stock", '<style>%s</style>%s%s' % (S.CSS, S.owner_ok_html(request.args), S.owner_page_body(con)),
                 back="/finance/approvals", login=login)


def _s778_door(name):
    def view():
        owner = name == "na_answer"
        u, con, kind, err = _auth_api(order=not owner)
        if err:
            return err
        if owner and kind != "owner":
            return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
        b = _body()
        S = _s778()
        try:
            if name == "again":
                body, code = S.again(con, who(u), str(b.get("kind") or ""), str(b.get("ref") or ""), str(b.get("to") or ""))
            elif name == "na":
                body, code = S.na(con, who(u), b)
            elif name == "na_answer":
                body, code = S.na_answer(con, who(u), int(b.get("id") or 0), str(b.get("answer") or ""))
            elif name == "dealer_ok":
                body, code = S.dealer_ok(con, who(u), str(b.get("sn") or ""), str(b.get("item") or ""))
            elif name == "na_undo":                           # S938: an 'Out of stock' tapped by mistake (staff: today's; the doctor: any)
                body, code = S.na_undo(con, who(u), int(b.get("id") or 0), owner=(kind == "owner"))
            else:
                body, code = S.move(con, who(u), b)
        except (TypeError, ValueError) as e:
            return jsonify(ok=False, error="bad_request", message=str(e)[:120]), 400
        return jsonify(body), code
    view.__name__ = "api_s778_" + name
    return view


bp.add_url_rule(P + "/s454/abnahi", "s778_abnahi", s778_abnahi_page)
for _n778 in ("again", "na", "na_answer", "dealer_ok", "move", "na_undo"):
    bp.add_url_rule(P + "/api/s778/" + _n778, "api_s778_" + _n778, _s778_door(_n778), methods=["POST"])
# ---- S778 end ---------------------------------------------------------------------------------------------------------------------------



# ==========================================================================================================================================
# S909_PHONE_DAILY_CHECK (20-Nov-2026, Sanjeevni session 494; D1026): the owner's Reception phone card shows the daily delivery check --
# its last result, the clinic's WhatsApp number (masked), Save, Check now. No dialog. Two owner-only doors:
#    POST /finance/porders/api/s909/clinic_number {number}     the number never reaches a log or the audit
#    POST /finance/porders/api/s909/check_now                  one check now (none running)
# ==========================================================================================================================================
_phone_card_before_s909 = phone_card


def phone_card(con, st):                                       # noqa: F811 -- S909: + the daily check (fail-soft)
    h = _phone_card_before_s909(con, st)
    try:
        import phone_check                                     # noqa: PLC0415
        h = h[:h.rindex("</div>")] + phone_check.card_block(con) + "</div>"
    except Exception:                                          # noqa: BLE001 -- the card never waits on its new part
        pass
    return h


@bp.route(P + "/api/s909/clinic_number", methods=["POST"])
def api_s909_clinic_number():
    u, con, err = _owner_api()
    if err:
        return err
    import phone_check                                         # noqa: PLC0415
    ok, msg = phone_check.save_to(con, who(u), str(_body().get("number") or "")[:30])
    return jsonify(ok=ok, message=msg), (200 if ok else 400)


@bp.route(P + "/api/s909/check_now", methods=["POST"])
def api_s909_check_now():
    u, con, err = _owner_api()
    if err:
        return err
    import phone_check                                         # noqa: PLC0415
    ok, v = phone_check.start_run(con, manual=True, who=who(u))
    return (jsonify(ok=True, run=v), 200) if ok else (jsonify(ok=False, message=v), 409)
# ---- S909 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S921 (21-Nov-2026, Sanjeevni session 500, kit S921_PURCHASE_FLOW_2; D1030 / D1034, mock-up v4 FINAL tab "Reception") ---------------
#  Reception's home (the logins in porders.rescan_doers): the purchase flow's grouped strip (order_flow.rec_body -- the one reader's
#  groups(), never a second grouping) stands under "Naya bill scan karo"; the two rows it replaces ("Order ka maal nahi aaya -- call karo",
#  "Maal aaya?") go. Every sender but the owner and PURANA_USERS: the September (parked month) link goes (F-1548).
#  Switch: setting order_flow.rec_on = 0 gives reception's home its two old rows back (the September link stays off). Any fault: the home as before.
_s921_home_before = home


def _s921_on(con):
    return str(OS.setting(con, "order_flow.rec_on", "1")).strip() != "0"


def home():                                                   # noqa: F811 -- S921
    r = _s921_home_before()
    if not (isinstance(r, tuple) and len(r) > 1 and r[1] == 200):
        return r
    try:
        u, con, kind, login, err = _auth_page()
        if err:
            return r
        page = r[0]
        if kind != "owner" and str(login) not in PURANA_USERS and str(u.get("user") or "").lower() not in PURANA_USERS:
            page = re.sub(r'<div class="lnk"><a id="park_[^"]*" [^>]*>[^<]*</a></div>', "", page)     # F-1548: the September backlog
        if kind != "owner" and _s618_doer(con, str(login).lower()) and _s921_on(con):
            import order_flow                                 # noqa: PLC0415
            rf = con.row_factory
            con.row_factory = sqlite3.Row
            try:
                strip = order_flow.rec_body(con, OS.now())
            finally:
                con.row_factory = rf
            if strip:
                page = re.sub(r'<a class="row" id="row_(?:late|maal)" [^>]*>.*?</a>', "", page, flags=re.S)
                page = re.sub(r'<div class="ok" id="alldone">.*?</div></div>', "", page, count=1, flags=re.S)
                mark = L(False, "onebill") + "</div>"
                if mark in page:
                    page = page.replace(mark, mark + strip, 1)
                else:
                    page = page.replace("</div></body>", strip + "</div></body>", 1)
        return (page,) + tuple(r[1:])
    except Exception as e:                                    # noqa: BLE001 -- the home as before
        print("S921 home failed: %r" % (e,), file=sys.stderr)
        return r
# ---- S921 end ---------------------------------------------------------------------------------------------------------------------------



# ==========================================================================================================================================
# S939_ORDER_FINAL (23-Nov-2026, Sanjeevni session 509; D1053, the owner's "Mockup okay" 18:52 IST) -- order_d1053.py beside this file
#  holds the logic. With setting order.d1053 = 1 and the order made from Marg's sheet:
#   * the old lines are Darpan's (his tab): reception's red box gives way to one line and the waiting / final banner; the lines that
#     came leave by themselves (F-1623, order_s778.red_lines wrapped);
#   * reception only raises: a card line's Out of stock and the remove chips become "Dealer ke paas nahi → Darpan ko"
#     (POST /finance/porders/api/d1053/raise); her strip's Dobara / Out of stock become the same raise; the doctor keeps his buttons;
#   * WhatsApp all, its confirm screen and its door are LOCKED until Darpan's सूची पक्की करो; Call and Order done stay open;
#   * the day's "Ho chuke" becomes the SENT record -- each dealer with its WhatsApp / call time and the day its goods are due, until
#     they come.
#  Any other value of order.d1053, or any fault here: every screen and door exactly as before this kit.
# ==========================================================================================================================================
def _d53():
    import order_d1053                                        # noqa: PLC0415 -- beside this file
    return order_d1053


def _d53_log(where, e):
    print("S939 %s failed: %r" % (where, e), file=sys.stderr)


def _d53_con():
    try:
        return getattr(_s778_g(), "d1053_con", None)
    except Exception:                                         # noqa: BLE001
        return None


try:
    import order_s778 as _d53_S7                              # noqa: E402
    _d53_red_lines_before = _d53_S7.red_lines

    def _d53_red_lines(con, en=False, cards=None):
        g, key = None, "d1053_red_%d" % (1 if en else 0)
        try:
            g = _s778_g()
            hit = getattr(g, key, None)
            if hit is not None:
                return hit                                    # one reading per request, as order_s778's own (cleared after a write)
        except Exception:                                     # noqa: BLE001 -- outside a request
            g = None
        out = _d53_red_lines_before(con, en, cards)
        try:
            out = _d53().red_lines_filter(con, out)
        except Exception as e:                                # noqa: BLE001 -- the lines as order_s778 made them
            _d53_log("red_lines", e)
            return out
        if g is not None:
            try:
                setattr(g, key, out)
            except Exception:                                 # noqa: BLE001
                pass
        return out
    _d53_S7.red_lines = _d53_red_lines

    _d53_red_box_before = _d53_S7.red_box

    def _d53_red_box(con, en, cards=None):
        try:
            D = _d53()
            if D.live(con):
                q = D.questions(con, cards)
                n = len(q["old"])
                line = ""
                if n:
                    line = ('<div class="mut" id="d1053old">%s</div>' % esc(("%d old medicine%s wait for Darpan's decision on his tab" % (n, "" if n == 1 else "s"))
                                                                         if en else ("%d purani dawa — Darpan apne page par faisla karenge" % n)))
                return '<div id="s778box" data-d1053="1">%s%s</div>' % (D.banner_html(con, en), line)
        except Exception as e:                                # noqa: BLE001 -- the box as before
            _d53_log("red_box", e)
        return _d53_red_box_before(con, en, cards)
    _d53_S7.red_box = _d53_red_box

    _d53_na_button_before = _d53_S7.na_button

    def _d53_na_button(en, e, l):
        try:
            con = _d53_con()
            if con is not None and _d53().live(con):
                note = _d53().raised_on_card(con, e["sn"]).get((l.get("src"), str(l.get("ref")), l.get("item")))
                if note:
                    return _d53().raised_note(note, "", en)
                if not en:
                    return _d53().raise_button(e, l)
        except Exception as ex:                               # noqa: BLE001
            _d53_log("na_button", ex)
        return _d53_na_button_before(en, e, l)
    _d53_S7.na_button = _d53_na_button

    _d53_card_extra_before = _d53_S7.card_extra

    def _d53_card_extra(con, en, e):
        h = _d53_card_extra_before(con, en, e)
        try:
            D = _d53()
            if D.live(con):
                for (src, ref, item), ba in D.raised_on_card(con, e["sn"]).items():
                    h += D.raised_note(ba, item, en)
        except Exception as ex:                               # noqa: BLE001
            _d53_log("card_extra", ex)
        return h
    _d53_S7.card_extra = _d53_card_extra
except Exception as _e939:                                    # noqa: BLE001
    _d53_log("order_s778 wraps", _e939)

_d53_whatsapp_all_before = OS.whatsapp_all


def _d53_whatsapp_all(con, who_, expect=None):
    try:
        if _d53().locked(con):
            return dict(ok=False, error="not_final", message="Darpan ne list abhi pakki nahi ki — tab tak WhatsApp band hai. Call se order kar sakte hain."), 409
    except Exception as e:                                    # noqa: BLE001 -- the door as before
        _d53_log("whatsapp lock", e)
    return _d53_whatsapp_all_before(con, who_, expect=expect)


OS.whatsapp_all = _d53_whatsapp_all

_d53_wa_confirm_before = wa_confirm_page


def wa_confirm_page():                                         # noqa: F811 -- S939: locked until Darpan's final
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    try:
        D = _d53()
        if D.locked(con):
            en = u["_en"]
            back = P + "/s454/order"
            return shell(con, u, L(en, "wa_q"), '%s<a class="more" id="waback" href="%s">%s</a>' % (D.banner_html(con, en), back, L(en, "wa_back")),
                         back=back, login=login)
    except Exception as e:                                    # noqa: BLE001
        _d53_log("wa_confirm", e)
    return _d53_wa_confirm_before()


_d53_order_list_before = order_list
_D53_DONE_END = ('<div class="lnk"><a id="oldlink"', '<div class="ok"><div class="t">')


def _d53_body_end(page):
    """Where shell()'s body ends: the last </div> before </body> (a shared login's who-script may sit between them)."""
    e = page.find("</body>")
    return page.rfind("</div>", 0, e) if e >= 0 else -1


def order_list():                                             # noqa: F811 -- S939: the lock on WhatsApp all, the sent record
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    g = None
    try:
        g = _s778_g()
        g.d1053_con = con
    except Exception as e:                                    # noqa: BLE001
        _d53_log("order_list g", e)
    r = _d53_order_list_before()
    try:
        D = _d53()
        if isinstance(r, tuple) and r[1] == 200 and D.live(con):
            en = u["_en"]
            page = r[0]
            if D.locked(con):
                page = re.sub(r'<a class="big" id="waall" href="[^"]*">([^<]*)</a>',
                              lambda m: '<button class="big" id="waall" disabled>%s</button>' % (m.group(1) + (" (locked)" if en else " (band)")), page, count=1)
            a = page.find('<div class="mut" id="donehead">')
            sent = D.sent_html(con, en)
            be = _d53_body_end(page)
            if a >= 0:
                ends = [page.find(x, a) for x in _D53_DONE_END] + [be]
                b = min([x for x in ends if x > a] or [-1])
                if b > a:
                    page = page[:a] + sent + page[b:]
            elif sent:
                ends = [page.find(x) for x in _D53_DONE_END] + [be]
                b = min([x for x in ends if x >= 0] or [-1])
                if b >= 0:
                    page = page[:b] + sent + page[b:]
            r = (page,) + tuple(r[1:])
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was
        _d53_log("order_list", e)
    finally:
        if g is not None:
            g.d1053_con = None
    return r


_d53_supplier_page_before = supplier_page


def supplier_page(sn):                                        # noqa: F811 -- S939: the line's button is the raise
    g = None
    try:
        po = _po()
        u, con, kind, err = po._auth()
        if not err:
            g = _s778_g()
            g.d1053_con = con
    except Exception as e:                                    # noqa: BLE001
        _d53_log("supplier g", e)
    try:
        return _d53_supplier_page_before(sn)
    finally:
        if g is not None:
            g.d1053_con = None


_d53_remove_chips_before = _s619_remove_chips


def _s619_remove_chips(en, b):                                # noqa: F811 -- S939: reception raises to Darpan instead of removing
    try:
        con = _d53_con()
        if con is not None and not en and _d53().live(con):
            return ""
    except Exception as e:                                    # noqa: BLE001
        _d53_log("remove chips", e)
    return _d53_remove_chips_before(en, b)


_D53_DECIDE = (P + "/api/s778/na", P + "/api/s778/again", P + "/api/s454/reorder")


@bp.before_request
def _d53_gate():
    """Every request of this screen: the request knows its connection and who asks (the line buttons read it). With the flow on, the
    decisions on a line are the doctor's and Darpan's: a staff POST to Out of stock, Dobara / again, or the remove is refused -- she
    raises to Darpan."""
    try:
        po = _po()
        u, con, kind, err = po._auth()
        if err:
            return None
        g = _s778_g()
        g.d1053_con, g.d1053_kind = con, kind
        if request.method != "POST" or kind == "owner":
            return None
        path = request.path
        if path == P + "/api/s454/qty":
            if not (request.get_json(silent=True) or {}).get("remove"):
                return None
        elif path not in _D53_DECIDE:
            return None
        if _d53().live(con):
            return jsonify(ok=False, error="raise_only", message="Iska faisla Darpan karenge — 'Dealer ke paas nahi → Darpan ko' dabaiye."), 409
    except Exception as e:                                    # noqa: BLE001 -- the door as before
        _d53_log("gate", e)
    return None


_d53_old_block_before = _old_block


def _old_block(en, olds, title=True):                         # noqa: F811 -- S939: no Dobara button for staff (Darpan decides)
    h = _d53_old_block_before(en, olds, title)
    try:
        con = _d53_con()
        if con is not None and not en and _d53().live(con):
            h = re.sub(r'<button class="sm" onclick="s454\(\'[^\']*/api/s454/reorder\',\{line:\d+\}\)">[^<]*</button>', "", h)
    except Exception as e:                                    # noqa: BLE001
        _d53_log("old block", e)
    return h


@bp.route(P + "/api/d1053/raise", methods=["POST"])
def api_d1053_raise():
    u, con, kind, err = _auth_api(order=True)
    if err:
        return err
    try:
        D = _d53()
        if not D.live(con):
            return jsonify(ok=False, error="off", message="Yeh button abhi band hai."), 409
        body, code = D.raise_line(con, who(u), _body())
    except Exception as e:                                    # noqa: BLE001
        _d53_log("raise door", e)
        return jsonify(ok=False, error="unavailable"), 503
    return jsonify(**body), code


try:                                                          # reception's strip (order_flow): Dobara / Out of stock become the raise
    import order_flow as _d53_OF                              # noqa: E402
    _d53_rline_before = _d53_OF._rline_btns
    _d53_rrow_before = _d53_OF._rrow_acts
    _d53_rec_act_before = _d53_OF.rec_act

    def _d53_flow_live():
        """Once per request (cached on g): is the flow live? Outside a request: no (the strip as before)."""
        try:
            from flask import g, has_app_context              # noqa: PLC0415
            if not has_app_context():
                return False
            v = getattr(g, "d1053_flowlive", None)
            if v is None:
                v = bool(_d53().live(_po()._db()))
                g.d1053_flowlive = v
            return v
        except Exception:                                     # noqa: BLE001
            return False

    def _d53_rline(r, l):
        if l.get("state") in ("short", "part") and r.get("id") and l.get("id") and not r.get("orderless") and _d53_flow_live():
            return (_d53_OF._rbtn("Substitute aaya", dict(oid=r["id"], lid=l["id"], do="sub")) +
                    '<span class="small">Baaki dawa ka faisla Darpan karenge</span>')
        return _d53_rline_before(r, l)

    def _d53_rrow(r):
        if r.get("group") == "late" and r.get("id") and not r.get("orderless") and _d53_flow_live():
            return (_d53_OF._rbtn("Call kiya — aa raha hai", dict(do="called", oid=r["id"]), "p") +
                    _d53_OF._rbtn("Dealer ke paas nahi → Darpan ko", dict(do="raise", oid=r["id"])) +
                    _d53_OF._rbtn("Nahi bhejenge", dict(do="refused", oid=r["id"]), "w"))
        return _d53_rrow_before(r)

    def _d53_rec_act(con, who_, b):
        try:
            D = _d53()
            if isinstance(b, dict) and D.live(con):
                do = str(b.get("do") or "")
                if do == "raise":
                    return D.raise_line(con, who_, dict(oid=b.get("oid")))
                if do in ("again", "oos", "oosrow"):
                    return dict(ok=False, error="raise_only", message="Iska faisla Darpan karenge — 'Dealer ke paas nahi → Darpan ko' dabaiye."), 409
        except Exception as e:                                # noqa: BLE001
            _d53_log("rec_act", e)
        return _d53_rec_act_before(con, who_, b)

    _d53_OF._rline_btns = _d53_rline
    _d53_OF._rrow_acts = _d53_rrow
    _d53_OF.rec_act = _d53_rec_act
except Exception as _e939b:                                   # noqa: BLE001
    _d53_log("order_flow wraps", _e939b)
# ---- S939 end ---------------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S940_ORDER_MESSAGES (23-Nov-2026, Sanjeevni session 509; D1053) -- order_d1053_msg.py beside this file: his Purchase orders page opens
#  with the day in four steps (sheet in · final · sent · arriving) while the flow is on; the old sheet notice gives way to message A.
#  The messages themselves are made and sent by order_rules' tick (its S940 block). Any fault: the page as before.
# ==========================================================================================================================================
try:
    import order_d1053_msg as _d540                           # noqa: E402
    _d540.install(OS)
    import order_flow as _d540_OF                             # noqa: E402
    _d540_owner_body_before = _d540_OF.owner_body

    def _d540_owner_body(con, now=None, G=None):
        body = _d540_owner_body_before(con, now, G)
        try:
            return _d540.owner_card(con) + body
        except Exception as e:                                # noqa: BLE001 -- the page as before
            print("S940 owner card failed: %r" % (e,), file=sys.stderr)
            return body
    _d540_OF.owner_body = _d540_owner_body
except Exception as _e940:                                    # noqa: BLE001
    print("S940 wraps failed: %r" % (_e940,), file=sys.stderr)
# ---- S940 end ---------------------------------------------------------------------------------------------------------------------------

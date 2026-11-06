# -*- coding: utf-8 -*-
"""
marg_flows.py -- S714_MARG_FLOWS (S388, Sanjeevni, 06-Nov-2026; D827, D830): one phone-first page per Marg report, shareable.

THE OWNER, 05-Nov-2026 (D827): one flow per recurring Marg report, phone-first -- screenshots cropped to the box, the field to change
ringed; Roman Hindi; collected in one place for the staff assigned; EACH FLOW SHAREABLE ON ITS OWN WITH ANYONE AT ANY TIME (Ram Singh,
to add the reports to the reports login; any staff; himself); Shivani trained as the backup for Marg reports.  D830: Shivani's Marg
reports work in her own app login, with the server's confirmation.

  GET /finance/flows               the index: every flow, one link each (no login)
  GET /finance/flows/<id>          one flow: its steps with Marg's own screens, the legend, "WhatsApp par bhejiye" (no login)
  GET /finance/flows/pic/<n>.jpg   one picture (no login)
  GET /finance/reports/flows       inside the app (any medical role): every flow with the server's word on its last report
(the routes are declared in reports_tile.py; finance_app's gate lets GET /finance/flows and /finance/flows/* through, S714.)

The public pages carry ONLY fixed text and the pictures below: no database read, no name, no figure.  Every public answer says
noindex (header and meta).  The steps are the owner's settings as fixed at the S384 session (D827); the two morning reports are
reports_guide.py's own steps (S500, D694), shown here so that they too can be shared.  The pictures: marg_flows_pics.py (F-185
re-checked at S388) and reports_guide_pics.py.
"""
import html
from urllib.parse import quote

KIT = "S714_MARG_FLOWS"
PUBLIC = "/finance/flows"
APP = "/finance/reports/flows"
SITE = "https://followup.dr-manoj.in"

# id -> the mi_file types the server files that report under (the confirmation inside the app)
TYPES = {"valuation": ("STOCK_VALUATION",), "batch": ("BATCH_STOCK",), "salt": ("SALT_WISE_ITEM_LIST",), "items": ("ITEM_MASTER",),
         "purchase-bill": ("PURCHASE_BILLWISE",), "purchase-item": ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE"),
         "order-sheet": ("ORDER_PENDING",), "category": ("CATEGORY_WISE_ITEM_LIST",), "sale": ("SALE_BILLWISE",), "stock": ("STOCK_CLOSING",)}

SAVE = "Bas. File apne aap clinic server par chali jaati hai."
SAVE_STEP = "Upar <b>%s</b> dikhe. Ab <b>Save wala icon</b> dabaiye, ya keyboard par <b>F3</b>."

FLOWS = [
    dict(id="valuation", name="Stock Valuation", when="Har mahine, 1 se 7 tareekh tak", who="Shavez (reports login)",
         file="WHOLE STORES STOCK VALUATION AS ON <mahine ki aakhri tareekh>",
         steps=[
             ("Menu <b>Stocks</b> → <b>Stock Valuation</b>.", "", ["v1"]),
             ("<b>WHOLE</b> chuniye → <b>Enter</b>.", "<span class=no>DTH, MAIN STORE ya SCRAP STORE nahi.</span>", ["v2"]),
             ("Sirf <b>ek cheez badalni hai</b>: Valuation On → <b>Pur. Rate</b>. Baaki sab jaisa bhara hai, waisa hi rehne dijiye. Phir <b>Accept</b>.",
              "<span class=ck>Check:</span> Stock as on = <b>pichhle mahine ki aakhri tareekh</b> (jaise 31-10-2026). Alag ho to theek kijiye.", ["v3"]),
             ("List khulegi. Upar <b>WHOLE STORES : STOCK VALUATION : 31-10-2026</b> dikhe. Ab <b>Alt + P</b> → <b>A Stock Statement</b> → <b>Enter</b>.", "", ["v4", "v5"]),
             ("<b>B Alphabatic</b> → <b>Enter</b>.", "", ["v6"]),
             ("Kuch nahi badalna (1 No pehle se bhara hai). Bas <b>Enter 3 baar</b>.", "", ["v7"]),
             ("<b>View</b> dabaiye.", "<span class=no>Print ya Excel nahi.</span>", ["v8"]),
             (SAVE_STEP % "WHOLE STORES STOCK VALUATION AS ON 31-10-2026", SAVE, ["v9a", "v9b"]),
         ]),
    dict(id="batch", name="Batch Stock", when="Har mahine, Amir ki pehli visit par", who="Amir · Shavez backup",
         file="WHOLE STORES CLOSING STOCK AS ON <kal ki tareekh>",
         steps=[
             ("Menu <b>Stocks</b> → <b>Batch Stock</b>.", "", ["b1"]),
             ("<b>WHOLE</b> chuniye → <b>Enter</b>.", "<span class=no>DTH, MAIN STORE ya SCRAP STORE nahi.</span>", ["b2"]),
             ("Kuch nahi badalna. <b>Accept</b>.", "<span class=ck>Check:</span> Stock as on = <b>kal ki tareekh</b>.", ["b3"]),
             ("List khulegi. <b>Alt + P</b> → <b>A Stock Statement</b> → <b>Enter</b>.", "", ["b4"]),
             ("<b>B Alphabatic</b> → <b>Enter</b>.", "", ["b5"]),
             ("Kuch nahi badalna (1 No pehle se bhara hai). Bas <b>Enter 3 baar</b>.", "", ["b6"]),
             ("<b>View</b> dabaiye.", "<span class=no>Print ya Excel nahi.</span>", ["b7"]),
             (SAVE_STEP % "WHOLE STORES CLOSING STOCK", SAVE, ["b8a", "b8b"]),
         ]),
    dict(id="salt", name="Salt-wise item list", when="Har hafte", who="Amir · Shavez backup", file="SALT WISE ITEM LIST",
         steps=[
             ("Menu <b>Daily Reports</b> → <b>Inventory Reports</b> → <b>Various Types of Items List</b>.", "", ["s1"]),
             ("<b>D Salt Wise List</b> → <b>Enter</b>.", "", ["s3"]),
             ("<b>*</b> dabaiye (sab salt par tick lag jaayega) → <b>Enter</b>.", "", ["s4"]),
             ("Kuch nahi badalna. <b>View</b>.", "", ["s5"]),
             (SAVE_STEP % "SALT WISE ITEM LIST", SAVE, ["s6a", "s6b"]),
         ]),
    dict(id="items", name="List of items", when="Har mahine", who="Amir · Shavez backup", file="LIST OF ITEMS",
         steps=[
             ("Menu <b>Daily Reports</b> → <b>Inventory Reports</b> → <b>Various Types of Items List</b>.", "", ["s1"]),
             ("<b>B Alphabatic List</b> → <b>Enter</b>.", "", ["s7"]),
             ("Kuch nahi badalna. <b>View</b>.", "", ["s8"]),
             (SAVE_STEP % "LIST OF ITEMS", SAVE, ["s9a", "s9b"]),
         ]),
    dict(id="purchase-bill", name="Purchase bill-wise", when="Amir ki har visit par", who="Amir · Shavez backup",
         file="BILL WISE PURCHASE STATEMENT FROM <is mahine ki 1 tareekh> TO <kal ki tareekh>",
         steps=[
             ("Menu <b>Daily Reports</b> → <b>Purchase Report</b> → <b>Bill Wise Summary</b>.", "", ["p1"]),
             ("Report For mein <b>2 Purc-P/R-Brk</b> chuniye. Baaki jaisa hai. Phir <b>View</b>.",
              "<span class=ck>Check:</span> From = <b>is mahine ki 1 tareekh</b>, To = <b>kal ki tareekh</b>.", ["p2"]),
             ("Chaaron store par tick pehle se laga hai. Bas <b>Enter</b>.", "", ["p3"]),
             (SAVE_STEP % "BILL WISE PURCHASE STATEMENT", SAVE, ["p4a", "p4b"]),
         ]),
    dict(id="purchase-item", name="Purchase item-wise", when="Amir ki har visit par", who="Amir · Shavez backup",
         file="SUPPLIER/ITEM WISE PURCHASE STATEMENT FROM <is mahine ki 1 tareekh> TO <kal ki tareekh>",
         steps=[
             ("Menu <b>Daily Reports</b> → <b>Purchase Report</b> → <b>Supplier/Item Wise Statement</b>.", "", ["i1"]),
             ("Report For mein <b>2 Purc-P/R-Brk</b> chuniye.", "<span class=no>1 Purchase nahi.</span>", ["i2"]),
             ("<b>M.R.P./Rate</b> mein <b>Purc. Rate</b> chuniye (list ke sabse neeche). Baaki jaisa hai. Phir <b>View</b>.",
              "<span class=no>M.R.P. nahi</span>, M.R.P. ke saath file wapas aa jaati hai. <span class=ck>Check:</span> From = <b>is mahine ki 1 tareekh</b>, "
              "To = <b>kal ki tareekh</b>.", ["i3b", "i3"]),
             ("Chaaron store par tick pehle se laga hai. Bas <b>Enter</b>.", "", ["i4"]),
             ("<b>Shift</b> aur <b>*</b> ek saath dabaiye: sab supplier par tick lag jaayega. Phir <b>Enter</b>.", "", ["i5"]),
             (SAVE_STEP % "SUPPLIER/ITEM WISE PURCHASE STATEMENT", SAVE, ["i6a", "i6b"]),
         ]),
    dict(id="order-sheet", name="Order sheet (pending orders)", when="Roz dopahar, order banane ke baad", who="Darpan",
         file="PENDING ORDERS (PURCHASE)",
         steps=[
             ("Menu <b>Transactions</b> → <b>Purchase Order</b> → <b>Item Pending</b>.", "", ["o1"]),
             ("Kuch nahi badalna. <b>Enter</b> dabaate jaiye jab tak agla page na aaye, ya ek baar <b>Page Down</b>.", "", ["o2"]),
             ("<b>A ALL ITEMS</b> pehle se chuna hai. Bas <b>Enter</b>.", "", ["o3"]),
             ("Pending orders ki list khulegi. Ab <b>Alt + P</b>.", "", ["o4"]),
             ("<b>A Order Detailed</b> pehle se chuna hai. Bas <b>Enter</b>.", "", ["o5"]),
             ("<b>View</b> pehle se chuna hai. Bas <b>Enter</b>.", "<span class=no>Print ya Excel nahi.</span>", ["o6"]),
             (SAVE_STEP % "PENDING ORDERS (PURCHASE)", SAVE, ["o7a", "o7b"]),
         ]),
    dict(id="category", name="Category-wise item list", when="Har mahine", who="Amir · Shavez backup", file="CATEGORY WISE ITEM LIST",
         steps=[
             ("Menu <b>Daily Reports</b> → <b>Inventory Reports</b> → <b>Various Types of Items List</b>.", "", ["c1"]),
             ("<b>E Category Wise</b> → <b>Enter</b>.", "", ["c2"]),
             ("Chaaron category par tick pehle se laga hai. Bas <b>Enter</b>.",
              "<span class=ck>Check:</span> COMMON, NEW SEPT 2025, ORTHOTICS, OTHERS, sab par tick. Tick na ho to <b>*</b> dabaiye.", ["c3"]),
             ("Kuch nahi badalna. <b>View</b>.", "", ["c4"]),
             (SAVE_STEP % "CATEGORY WISE ITEM LIST", SAVE, ["c5a", "c5b"]),
         ]),
    dict(id="sale", name="Bikri report (Bill-wise sale)", when="Roz subah", who="Shavez · Shivani backup",
         file="BILL WISE SALES STATEMENT AS ON <kal ki tareekh>", guide="sale",
         start="Marg mein <b>REPORT</b> wali ID se login kijiye. <b>My Menu</b> mein sirf do hi cheezein milengi."),
    dict(id="stock", name="Closing stock (Stock Status)", when="Roz subah", who="Shavez · Shivani backup",
         file="WHOLE STORES CLOSING STOCK AS ON <kal ki tareekh>", guide="stock",
         start="Marg mein <b>REPORT</b> wali ID se login kijiye. <b>My Menu</b> mein sirf do hi cheezein milengi."),
]
BY_ID = {f["id"]: f for f in FLOWS}

CSS = """
:root{--bg:#f3f5f1;--paper:#fff;--ink:#1d2621;--muted:#5b6a61;--line:#d5ddd6;--marg:#2e6a4f;--marg-ink:#fff;--code-bg:#e6efe8;
 --no:#b3261e;--ok:#2e6a4f;--wa:#1b7f4a;--ring-ch:#e85d00;--ring-ck:#1e78e6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:20px 16px 48px}
.wrap{max-width:640px;margin:0 auto;display:grid;gap:20px}
h1{font-size:1.6rem;line-height:1.2;margin:0}
.lead{margin:6px 0 0;color:var(--muted)}
.rules{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:14px 16px;display:grid;gap:6px}
.rules h3{margin:0;font-size:1rem}.rules ul{margin:0;padding-left:20px;display:grid;gap:4px}
.idx{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.idx a{display:grid;gap:2px;padding:12px 14px;background:var(--paper);border:1px solid var(--line);border-radius:8px;color:inherit;text-decoration:none;min-height:56px}
.idx a:focus-visible,.idx a:hover{border-color:var(--marg);outline:none}
.nm{font-weight:700}.meta{color:var(--muted);font-size:.92rem}
.flow{background:var(--paper);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.bar{background:var(--marg);color:var(--marg-ink);padding:12px 16px;display:grid;gap:4px}
.bar h2{margin:0;font-size:1.2rem;letter-spacing:.02em}
.bar dl{margin:0;display:flex;flex-wrap:wrap;gap:4px 18px;font-size:.92rem}.bar dl div{display:flex;gap:6px}.bar dt{opacity:.85}.bar dd{margin:0;font-weight:700}
.check{margin:14px 16px 0;font-size:.95rem;color:var(--muted)}
.start{margin:14px 16px 0;padding:10px 12px;background:var(--code-bg);border-radius:6px;font-size:.95rem}
code{font-family:ui-monospace,Consolas,monospace;font-size:.85rem;background:var(--code-bg);padding:2px 6px;border-radius:3px;word-break:break-word}
.steps{list-style:none;margin:0;padding:8px 16px 16px}
.step{display:grid;gap:12px;padding:18px 0;border-top:1px solid var(--line)}.step:first-child{border-top:0}
.txt{display:flex;gap:12px;min-width:0}
.n{flex:none;width:30px;height:30px;border-radius:50%;background:var(--marg);color:var(--marg-ink);font-weight:700;display:grid;place-items:center;font-size:.95rem}
.txt p{margin:0}.note{margin-top:6px!important;color:var(--muted);font-size:.93rem}
.no{color:var(--no);font-weight:700}.ck{color:var(--ring-ck);font-weight:700}
.pics{display:grid;gap:10px;min-width:0}figure{margin:0}figure img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:4px;background:#fff}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.95rem}.legend span{display:inline-flex;align-items:center;gap:8px}
.legend i{width:26px;height:16px;border-radius:5px;border:3px solid}.legend .c i{border-color:var(--ring-ch)}.legend .k i{border-color:var(--ring-ck)}
.wa{display:flex;align-items:center;justify-content:center;gap:8px;min-height:52px;padding:0 18px;border-radius:10px;background:var(--wa);color:#fff;
 font-weight:700;text-decoration:none;font-size:17px}
.top{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.back{color:var(--marg);font-weight:700;text-decoration:none;min-height:44px;display:inline-flex;align-items:center}
.foot{color:var(--muted);font-size:.88rem}
.st{font-size:.9rem;font-weight:700}.st.ok{color:var(--ok)}.st.bad{color:var(--no)}.st.none{color:var(--muted)}
"""

RULES = ("<div class=rules role=note><h3>Har report mein yaad rakhiye</h3><ul>"
         "<li>Store: jahan <b>ek</b> chunna ho, wahan <b>WHOLE</b>. <span class=no>DTH, MAIN STORE ya SCRAP STORE nahi.</span> "
         "Jahan chaaron par tick pehle se ho, wahan bas Enter.</li>"
         "<li>Aakhir mein <b>View</b>, phir <b>Save wala icon</b>. <span class=no>Print ya Excel nahi.</span></li>"
         "<li>Save ke baad kuch bhejna nahi hai. Medical PC file khud clinic server ko bhej deta hai.</li></ul>"
         "<div class=legend><span class=c><i></i>Narangi ghera: yahan chuniye / dabaiye</span>"
         "<span class=k><i></i>Neela ghera: sirf check kijiye</span></div></div>")


def _e(v):
    return html.escape("" if v is None else str(v), quote=True)


def url(fid):
    return SITE + PUBLIC + "/" + fid


def wa_link(f):
    """A wa.me link carrying this flow's name and its address only -- the phone asks whom to send it to."""
    return "https://wa.me/?text=" + quote("%s -- Marg mein kaise banayein: %s" % (f["name"], url(f["id"])), safe="")


def shown():
    """The names of every picture a flow's steps show -- the only pictures the public address serves."""
    out = set()
    for f in FLOWS:
        for _t, _n, pics in _steps(f):
            out.update(pics)
    return out


def pic(name):
    """One picture's bytes (JPEG), or None: this module's pictures, else reports_guide's (the two morning reports).
    Only a picture some flow's steps show (reports_guide's stock_view, a report result, is not one)."""
    name = str(name or "")
    if name not in shown():
        return None
    try:
        import marg_flows_pics                                  # noqa: PLC0415
        h = marg_flows_pics.HEX.get(name)
        if h:
            return bytes.fromhex("".join(h) if isinstance(h, (tuple, list)) else h)
    except Exception:                                           # noqa: BLE001 -- a page never fails for a picture
        pass
    try:
        import reports_guide                                    # noqa: PLC0415
        return reports_guide.pic(name)
    except Exception:                                           # noqa: BLE001
        return None


def _steps(f):
    """[(html, note, [picture names])] -- the morning two from reports_guide.steps (its own words), the rest from FLOWS."""
    if f.get("guide"):
        try:
            import reports_guide                                # noqa: PLC0415
            return [(t, n, [p for p, _w in pics]) for t, n, pics in reports_guide.steps(f["guide"], "kal ki tareekh")]
        except Exception:                                       # noqa: BLE001
            return []
    return f["steps"]


def _flow_html(f):
    rows = []
    for i, (t, note, pics) in enumerate(_steps(f), 1):
        p = "".join('<figure><img loading=lazy src="%s/pic/%s.jpg" alt="%s"></figure>' % (PUBLIC, _e(n), _e("%s, step %d" % (f["name"], i))) for n in pics)
        rows.append('<li class=step><div class=txt><span class=n>%d</span><div><p>%s</p>%s</div></div><div class=pics>%s</div></li>'
                    % (i, t, ('<p class=note>%s</p>' % note) if note else "", p))
    start = ('<p class=start>%s</p>' % f["start"]) if f.get("start") else ""
    return ('<section class=flow id="%s"><header class=bar><h2>%s</h2><dl><div><dt>Kab</dt><dd>%s</dd></div><div><dt>Kaun</dt><dd>%s</dd></div></dl>'
            '</header>%s<p class=check>Sahi file ke upar likha hota hai: <code>%s</code></p><ol class=steps>%s</ol></section>'
            % (_e(f["id"]), _e(f["name"]), _e(f["when"]), _e(f["who"]), start, _e(f["file"]), "".join(rows)))


def _shell(title, body):
    return ("<!doctype html><html lang=hi><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<meta name=robots content='noindex,nofollow'><meta name=referrer content=no-referrer>"
            "<title>%s</title><style>%s</style></head><body><div class=wrap>%s</div></body></html>" % (_e(title), CSS, body))


def flow_page(fid):
    """One flow's public page (str), or None for an unknown id."""
    f = BY_ID.get(str(fid or ""))
    if f is None:
        return None
    body = ('<div class=top><a class=back href="%s">&lsaquo; Saari reports</a></div>'
            '<header><h1>%s</h1><p class=lead>Sanjeevni Medicos &middot; Marg mein yeh report kaise banayein. Steps upar se neeche, ek-ek karke.</p></header>'
            '<a class=wa href="%s" rel="noopener">WhatsApp par bhejiye</a>%s%s'
            '<a class=wa href="%s" rel="noopener">WhatsApp par bhejiye</a>'
            '<p class=foot>Screenshots: Sanjeevni ka medical PC, Marg ERP. Is page par koi naam, number ya hisaab nahi hai.</p>'
            % (PUBLIC, _e(f["name"]), _e(wa_link(f)), RULES, _flow_html(f), _e(wa_link(f))))
    return _shell("%s -- Marg report" % f["name"], body)


def index_page():
    """The public index (str): every flow, one link each."""
    li = "".join('<li><a href="%s/%s"><span class=nm>%s</span><span class=meta>%s &middot; %s</span></a></li>'
                 % (PUBLIC, _e(f["id"]), _e(f["name"]), _e(f["when"]), _e(f["who"])) for f in FLOWS)
    body = ('<header><h1>Marg report kaise banayein</h1><p class=lead>Sanjeevni ki har report ka sahi tareeka, Marg ki asli screen ke saath. '
            'Apni report kholiye; har page akela bhi WhatsApp par bheja ja sakta hai.</p></header>%s<nav aria-label="Reports"><ul class=idx>%s</ul></nav>'
            % (RULES, li))
    return _shell("Marg report kaise banayein", body)


def app_page(con, en, last_of, ddmm):
    """Inside the app: every flow with the server's word on its last report, its page and its WhatsApp share.
    last_of(con, types) -> dict(at, verdict, reason_hi) or None  (reports_tile's own reading of mi_file); ddmm(iso) -> 'dd-mm hh:mm'."""
    rows = []
    for f in FLOWS:
        r = None
        try:
            r = last_of(con, TYPES.get(f["id"], ()))
        except Exception:                                       # noqa: BLE001 -- a row never fails the page
            r = None
        if not r:
            st = '<span class="st none">%s</span>' % ("No report received yet" if en else "Abhi tak koi report nahi aayi")
        elif r.get("verdict") == "VERIFIED":
            st = '<span class="st ok">&#10003; %s %s</span>' % ("Last report received" if en else "Pichhli report aa gayi", _e(ddmm(r.get("at"))))
        else:
            st = '<span class="st bad">&#10007; %s %s%s</span>' % ("Last report refused" if en else "Pichhli report manzoor nahi hui", _e(ddmm(r.get("at"))),
                                                                 (" &middot; " + _e(r.get("reason_hi"))) if r.get("reason_hi") and not en else "")
        rows.append('<li><a href="%s/%s"><span class=nm>%s</span><span class=meta>%s &middot; %s</span>%s</a>'
                    '<a class=wa style="min-height:44px;font-size:15px;margin-top:6px" href="%s" rel="noopener">WhatsApp par bhejiye</a></li>'
                    % (PUBLIC, _e(f["id"]), _e(f["name"]), _e(f["when"]), _e(f["who"]), st, _e(wa_link(f))))
    head = ("<h1>Marg reports</h1><p class=lead>Every Marg report's steps, one page each. Each page opens without a login, so it can be sent to anyone "
            "(Ram Singh, any staff). Beside each: the server's word on the last report it received.</p>") if en else \
           ("<h1>Marg reports</h1><p class=lead>Har Marg report ke steps, ek page har report ka. Page bina login ke khulta hai, kisi ko bhi WhatsApp par "
            "bheja ja sakta hai. Har report ke neeche: server ne pichhli report li ya nahi.</p>")
    body = ('<div class=top><a class=back href="/finance/reports/aaj">&lsaquo; %s</a></div><header>%s</header><ul class=idx>%s</ul>'
            '<p class=foot>%s <a href="%s">%s</a></p>' % ("Aaj ki reports", head, "".join(rows),
                                                        "All flows at one address:" if en else "Saari flows ek address par:", PUBLIC, _e(SITE + PUBLIC)))
    return _shell("Marg reports", body)

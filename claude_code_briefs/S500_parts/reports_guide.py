# -*- coding: utf-8 -*-
"""
reports_guide.py -- S500_REPORT_CHECK (08-Oct-2026, D694): how the two morning Marg reports are made.

THE OWNER, 08-Oct-2026: "I have created a dedicated user ID in Marg where only two reports can be
generated ... make an intuitive staff friendly short flow so that they do error free exports and whenever
Shavez is not on duty other morning staff such as Shivani are also able to do this."

This file is the STEPS, in the words and the order he approved on the counter card (Roman Hindi), with
Marg's own screens beside them.  reports_tile.py shows them at
    /finance/reports/aaj/kaise/sale     /finance/reports/aaj/kaise/stock
and shows ONE step again (redo) under a report its check found wrong.  The pictures are his own
screenshots of 08-Oct, cut to the box or button each step names; they are kept as text in
reports_guide_pics.py so that they ride every copy of the code.  No picture shows a person, a phone
number or an account.

Nothing here reads or writes the database.  No Flask import: reports_tile does the routing.
"""
import html

KIT = "S500_REPORT_CHECK"
VERSION = "S500 1.0"
BASE = "/finance/reports/aaj"

# name -> (width, height, what it shows) -- the sizes of the files in reports_guide_pics.py
PICS = {
    "menu_sales": (193, 75, "My Menu: DAILY SALES"),
    "sale_dates": (520, 75, "Report From aur To"),
    "sale_full": (560, 720, "Poora BILL WISE STATEMENT menu: Report Type aur With Item Deta. par ghera"),
    "sale_two": (560, 157, "Report Type Detail, With Item Deta. Yes"),
    "sale_view": (480, 69, "View button"),
    "store_ticks": (440, 169, "Select Store: teeno par tick"),
    "save_bar": (520, 59, "Hari patti mein Save wala icon"),
    "menu_stock": (193, 77, "My Menu: Stock Status"),
    "store_whole": (420, 195, "Select Store: WHOLE"),
    "report_menu": (400, 297, "Report list: A Stock Statement"),
    "only_total": (340, 141, "ONLY TOTAL STOCK"),
    "view_btn": (520, 88, "View button"),
    "stock_view": (640, 175, "Whole Stores Closing Stock: khali stock wale item bhi"),
}

CSS = """
.kb{display:inline-block;margin-top:8px;padding:8px 14px;border:1px solid var(--accent);border-radius:9px;
    color:var(--accent);background:#fff;font-weight:600;font-size:15px;text-decoration:none}
.try{display:inline-block;margin:8px 0 0 10px;font-size:13px;font-weight:600;color:var(--warn)}
.redo{display:block;margin-top:8px;font-weight:700;color:var(--accent)}
.stop{display:block;margin-top:6px;padding:10px;background:#fdecea;border:1px solid #f1b9b3;border-radius:8px;color:var(--bad)}
.pic{display:block;max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px;margin-top:6px}
.no{color:var(--bad);font-weight:600}
ol.gs{list-style:none;margin:0;padding:0;counter-reset:gs}
ol.gs li{counter-increment:gs;position:relative;padding:12px 0 12px 40px;border-bottom:1px solid var(--line)}
ol.gs li:last-child{border-bottom:0}
ol.gs li:before{content:counter(gs);position:absolute;left:0;top:12px;width:28px;height:28px;border-radius:50%;
    background:var(--accent);color:#fff;font-weight:700;text-align:center;line-height:28px}
ol.mini{margin:4px 0 0;padding-left:22px}
.chk{background:#e7f3e9;border-color:#bfe0c6}
.chk ul{margin:4px 0 0;padding-left:20px}
"""


def _e(v):
    return html.escape("" if v is None else str(v), quote=True)


def pic(name):
    """The picture's bytes (JPEG), or None."""
    if name not in PICS:
        return None
    try:
        import reports_guide_pics                               # noqa: PLC0415
        h = reports_guide_pics.HEX.get(name)
        return bytes.fromhex("".join(h.split())) if h else None
    except Exception:                                           # noqa: BLE001 -- a page never fails for a picture
        return None


def img(name, show):
    w, h, alt = PICS[name]
    return ("<img class=pic src='%s/pic/%s.jpg' width=%d height=%d style='width:%dpx' alt='%s' loading=lazy>"
            % (BASE, name, w, h, min(show, w), _e(alt)))


def steps(kind, due):
    """[(html, small, [pictures])] -- `due` is the day the report is for, dd-mm-yyyy."""
    d = _e(due)
    if kind == "sale":
        return [
            ("My Menu mein <b>DAILY SALES</b> par click.", "", [("menu_sales", 170)]),
            ("<b>Tareekh dekhiye.</b> Report From aur To, dono mein <b>%s</b> honi chahiye." % d,
             "Tasveer ki tareekh sirf namoona hai.", [("sale_dates", 300)]),
            ("<b>Sirf do cheezein badaliye:</b><br>Report Type &rarr; <b>Detail</b><br>With Item Deta. &rarr; <b>Yes</b>",
             "<span class=no>Baaki kuch mat chhediye.</span> Poore menu mein sirf yahi do lines.",
             [("sale_full", 320), ("sale_two", 320)]),
            ("<b>View</b> dabaiye.", "", [("sale_view", 280)]),
            ("SELECT STORE khulega. Teeno par &#10003; pehle se laga hai. Seedha <b>Enter</b>.", "", [("store_ticks", 260)]),
            ("Report khul gayi. Neeche hari patti mein <b>Save wala icon</b> dabaiye.",
             "Tasveer mein narangi ghere wala.", [("save_bar", 320)]),
        ]
    return [
        ("My Menu mein <b>Stock Status</b> par click.", "", [("menu_stock", 170)]),
        ("Sabse neeche <b>WHOLE</b> chuniye, phir <b>Enter</b>.",
         "<span class=no>DTH, MAIN STORE ya SCRAP STORE nahi.</span>", [("store_whole", 260)]),
        ("Poori list khulegi. Ab <b>Alt + P</b> dabaiye.<br>Pehla wala, <b>A Stock Statement</b>, phir <b>Enter</b>.", "",
         [("report_menu", 260)]),
        ("<b>ONLY TOTAL STOCK</b>, phir <b>Enter</b>.", "", [("only_total", 230)]),
        ("<b>View</b> dabaiye.", "<span class=no>Print ya Excel nahi.</span>", [("view_btn", 320)]),
        ("Report khul gayi. Wahi <b>Save wala icon</b> dabaiye.", "Tasveer mein narangi ghere wala.", [("save_bar", 320)]),
    ]


def page(kind, due):
    """The guide page's body for one report."""
    back = "<p><a class=btn href='%s'>&lsaquo; Wapas &mdash; jaanch dekhiye</a></p>" % BASE
    if kind == "sale":
        head = "Report 1 &middot; Bikri report"
        marg = "DAILY SALES"
        checks = ["Upar likha ho <b>BILL WISE SALES STATEMENT AS ON</b> aur %s." % _e(due),
                  "Har bill ke neeche <b>dawaiyon ki lines</b> dikhen. Sirf bill aur rakam dikhe to step 3 chhoot gaya &mdash; dobara banaiye."]
        tail = ""
    else:
        head = "Report 2 &middot; Closing stock"
        marg = "Stock Status"
        checks = ["Upar likha ho <b>WHOLE STORES CLOSING STOCK AS ON</b>.",
                  "<b>Khali stock wale item bhi dikhen.</b> Unke aage - likha hota hai, jaise neeche ACROVIN 500. "
                  "Sirf stock wale item dikhen to report adhoori hai &mdash; dobara banaiye."]
        tail = img("stock_view", 340)
    li = ""
    for text, small, pics in steps(kind, due):
        li += "<li>%s%s%s</li>" % (text, ("<br><span class=small>%s</span>" % small) if small else "",
                                   "".join(img(n, w) for n, w in pics))
    return ("<h1>%s</h1><p class=sub>Marg mein: %s &middot; %s ki report</p>%s"
            "<div class=how>Marg mein <b>REPORT</b> wali ID se login kijiye. <b>My Menu</b> mein sirf do hi cheezein milengi.<br>"
            "<span class=small>Galat jagah pahunch gaye? Esc dabakar wapas aaiye aur phir se shuru kijiye.</span></div>"
            "<div class=card><ol class=gs>%s</ol></div>"
            "<div class='card chk'><b>Sahi report ki pehchaan</b><ul>%s</ul>%s</div>"
            "<p class=small>Save ke baad file yahan khud aa jaati hai &mdash; kuch bhejna nahi hai. Wapas jaakar &#10003; dekhiye.</p>%s"
            % (head, marg, _e(due), back, li, "".join("<li>%s</li>" % c for c in checks), tail, back))


def redo(fix, due):
    """The one step to do again, under a report found wrong.  '' -> the whole report again."""
    d = _e(due)
    if fix == "sale3":
        return ("<span class=redo>Step 3 dobara kijiye:</span>Report Type &rarr; <b>Detail</b> &middot; With Item Deta. &rarr; <b>Yes</b>"
                + img("sale_two", 300))
    if fix == "sale2":
        return "<span class=redo>Step 2 dekhiye:</span>Report From aur To, dono mein <b>%s</b> honi chahiye." % d
    if fix == "stock4":
        return "<span class=redo>Step 4 dobara kijiye:</span><b>ONLY TOTAL STOCK</b> chuniye, phir Enter." + img("only_total", 220)
    if fix == "stock25":
        return ("<span class=redo>Poori report dobara, step 2 se 5 dhyan se:</span>"
                "<ol class=mini start=2><li><b>WHOLE</b>, phir Enter</li><li><b>Alt + P</b>, phir A Stock Statement</li>"
                "<li><b>ONLY TOTAL STOCK</b></li><li><b>View</b></li></ol>")
    return "<span class=redo>Wahi report ek baar phir banaiye.</span>"

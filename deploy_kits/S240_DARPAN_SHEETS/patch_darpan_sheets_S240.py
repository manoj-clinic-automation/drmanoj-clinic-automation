#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_darpan_sheets_S240.py -- the two sheets for a person kept off the common salary sheet.

THE OWNER, 12-Sep-2026: Darpan comes off the shared sheet (done, D475) and gets two of his own --
"one for myself and one for him. My one will include all his running advances, extra, everything.
And Darpan's includes what he actually needs, nothing historical, so that he understands in one
line what is his number of leaves, what is the deduction of the leaves, what are the late minutes,
what are the marks given, what are the deductions for late minutes." His own sheet SHOWS the
advance deducted this month (the owner, 12-Sep).

WHAT THIS ADDS -- two printed pages at the end of the same document, one per such person:

  SHEET 5  the owner's full working: every deduction with the numbers behind it, and the advance
           story for the month -- opening, taken, recovered, interest, closing -- read from the
           ledger the month close already computes. No invented figures.
  SHEET 6  his own slip, in his words: salary, each deduction with its working, the advance cut
           this month, what he is paid, and a signature line. No balances, no history.

Each starts on a new page, so SHEET 6 can be torn off and handed over on its own.

NOTHING IS COMPUTED HERE. Every figure comes from the month's own computation, which is unchanged.

It refuses rather than guesses: each anchor must occur EXACTLY ONCE, and it must compile after the
edit or the backup is restored.

    /root/wa/venv/bin/python3 -B patch_darpan_sheets_S240.py            (on the box)
    SP_PATH=./copy.py python3 -B patch_darpan_sheets_S240.py            (offline)
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("SP_PATH", "/root/staff_register/salary_policy.py")
MARK = "def own_sheet_html("

A_OLD = '''    _own = own_sheet_names(res.get("settings") or {})   # S240: off the common sheet
    if _own:
        res = dict(res)
        res["staff"] = [_s for _s in res["staff"]
                        if str(_s["name"]).strip().lower() not in _own]
'''
A_NEW = '''    _own = own_sheet_names(res.get("settings") or {})   # S240: off the common sheet
    _own_staff = []
    if _own:
        res = dict(res)
        _own_staff = [_s for _s in res["staff"]
                      if str(_s["name"]).strip().lower() in _own]
        res["staff"] = [_s for _s in res["staff"]
                        if str(_s["name"]).strip().lower() not in _own]
'''

B_OLD = "    out.append(_S34_PRINT_CSS)"
B_NEW = '''    for _s in _own_staff:                               # S240: his own two pages
        out.append(own_sheet_html(_s, res, cap))
    out.append(_S34_PRINT_CSS)'''

C_ANCHOR = "def sheets34_html(res, back=None, approved=None, prefix=\"/register\", status_html=\"\"):"
C_INSERT = '''def own_sheet_html(st, res, cap):
    """Two printed pages for one person: the owner's full working, then the person's own slip.

    Reads only what the month already computed. It invents nothing and decides nothing."""
    e = html.escape
    ym = res["ym"]
    nm = str(st["name"])
    lm = st.get("ledger_money") or {}
    di = round(float(st.get("dress_rs", 0)) + float(st.get("icard_rs", 0)), 2)
    fines = round(float(st.get("fine_uninf", 0)) + float(st.get("fine_exc", 0)), 2)
    leaves = st.get("leaves_total", 0)
    wtd = st.get("leaves_weighted", leaves)
    offs = st.get("offs", 0)
    charged = round(float(wtd) - float(offs), 2)

    def row(label, work, amount, cls=""):
        return ("<tr%s><td>%s%s</td><td class='n'>%s</td></tr>"
                % ((" class='%s'" % cls) if cls else "", e(label),
                   ("<br><span class='wk'>%s</span>" % e(work)) if work else "",
                   money(amount)))

    o = ['<div class="s4pg" style="page-break-before:always">',
         _clinic_hdr("SHEET 5 · %s — FULL WORKING — %s" % (nm.upper(), month_words(ym)), cap),
         "<div class='tw'><table class='ownt'>",
         "<tr><th>Item</th><th>Amount (Rs.)</th></tr>",
         row("Salary", "", st["base"])]
    o.append("<tr class='sec'><td colspan='2'>Deductions</td></tr>")
    o.append(row("Leaves", "%s taken · %s weighted · %s allowed · %s charged"
                 % (money(leaves), money(wtd), money(offs), money(charged)), st["leave_amt"]))
    o.append(row("Late — collected this month",
                 "%s min · %s marks · charge %s · held %s"
                 % (money(st["late_min"]), money(st["marks"]), money(st["late_charge"]),
                    money(st["held"])), st["collect"]))
    if st.get("prior_collect"):
        o.append(row("Last month's held late charge", "", st["prior_collect"]))
    if st.get("release"):
        o.append(row("Last month's held charge written off", "improved", st["release"]))
    if di:
        o.append(row("Dress and I-card", "%s + %s days"
                     % (money(st.get("dress_days", 0)), money(st.get("icard_days", 0))), di))
    if fines:
        o.append(row("Other fines", "", fines))
    o.append(row("Advance adjusted this month", "", st.get("adv_ded", 0)))
    if st.get("duty_credits") or st.get("ot_paid"):
        o.append("<tr class='sec'><td colspan='2'>Added</td></tr>")
        if st.get("duty_credits"):
            o.append(row("Duty credits", "night + extra duty + outstation", st["duty_credits"]))
        if st.get("ot_paid"):
            o.append(row("Overtime paid", "", st["ot_paid"]))
    o.append("<tr class='sec'><td colspan='2'>Advances — the running story</td></tr>")
    o.append(row("Opening balance", "", lm.get("start", 0)))
    o.append(row("Taken this month", "", lm.get("taken", 0)))
    o.append(row("Recovered this month", "", lm.get("recovered", 0)))
    if lm.get("interest"):
        o.append(row("Interest charged", "", lm["interest"]))
    o.append(row("Closing balance", "", lm.get("end", 0)))
    o.append("<tr class='net'><td><b>NET PAYABLE</b></td><td class='n'><b>%s</b></td></tr>"
             % money(st["net"]))
    o.append("</table></div>")
    o.append('<div class="sub">Every entry behind the advance figures is on his own money page '
             '(SHEET 2). Nothing on this page is computed here — it is the month\\'s own working.</div>')
    o.append("</div>")

    o.append('<div class="s4pg" style="page-break-before:always">')
    o.append(_clinic_hdr("SALARY SLIP — %s — %s" % (nm.upper(), month_words(ym)), cap))
    o.append("<div class='tw'><table class='ownt'>")
    o.append("<tr><th>Vivran</th><th>Rs.</th></tr>")
    o.append(row("Salary", "", st["base"]))
    o.append("<tr class='sec'><td colspan='2'>Kaate gaye</td></tr>")
    o.append(row("Chhutti — %s din" % money(leaves),
                 "%s din free · %s din ka paisa kata" % (money(offs), money(charged)),
                 st["leave_amt"]))
    o.append(row("Late — %s minute, %s mark" % (money(st["late_min"]), money(st["marks"])),
                 "is mahine ka", st["collect"]))
    if st.get("prior_collect"):
        o.append(row("Pichhle mahine ka late", "jo roka gaya tha", st["prior_collect"]))
    if di:
        o.append(row("Dress aur I-card — %s + %s din"
                     % (money(st.get("dress_days", 0)), money(st.get("icard_days", 0))), "", di))
    if fines:
        o.append(row("Anya jurmana", "", fines))
    o.append(row("Advance kata", "is mahine", st.get("adv_ded", 0)))
    if st.get("duty_credits") or st.get("ot_paid"):
        o.append("<tr class='sec'><td colspan='2'>Joda gaya</td></tr>")
        if st.get("duty_credits"):
            o.append(row("Duty credit", "", st["duty_credits"]))
        if st.get("ot_paid"):
            o.append(row("Overtime", "", st["ot_paid"]))
    o.append("<tr class='net'><td><b>Is mahine mila</b></td><td class='n'><b>%s</b></td></tr>"
             % money(st["net"]))
    o.append("</table></div>")
    if float(st["net"]) < 0:
        o.append('<div class="ownwarn">Is mahine advance, salary se Rs. %s zyada kata hai. '
                 'Matlab is mahine kuch nahi milega, aur Rs. %s agle mahine se adjust hoga.</div>'
                 % (money(abs(float(st["net"]))), money(abs(float(st["net"])))))
    o.append('<div class="sub">Mila / Received — hastakshar</div>'
             '<div style="height:44px;border-bottom:1px solid #444;max-width:320px"></div>')
    o.append("</div>")
    return "".join(o)


'''

CSS_OLD = "_S34_PRINT_CSS = "
CSS_ADD = ('\n_OWN_SHEET_CSS = ("<style>.ownt td,.ownt th{padding:6px 9px}"\n'
           '                  ".ownt .wk{color:#666;font-size:11px}"\n'
           '                  ".ownt tr.sec td{background:#f2f2f2;font-weight:600;font-size:12px;'
           'text-transform:uppercase;letter-spacing:.06em}"\n'
           '                  ".ownt tr.net td{border-top:2px solid #222;font-size:15px}"\n'
           '                  ".ownwarn{border:1px solid #a33;background:#fdecea;color:#a33;'
           'padding:9px 12px;margin:10px 0;font-size:13px;max-width:520px}</style>")\n')


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if MARK in src:
        print("ALREADY DONE; pin %s -- nothing to do" % cur)
        return 0
    if b"\r\n" in raw:
        sys.exit("REFUSING: CRLF line endings (F-294)")
    for name, anchor in (("the own-sheet filter", A_OLD), ("the print CSS line", B_OLD),
                         ("sheets34_html()", C_ANCHOR), ("the print CSS block", CSS_OLD)):
        n = src.count(anchor)
        if n != 1:
            sys.exit("REFUSING: %s occurs %d times, expected exactly 1. Nothing was changed."
                     % (name, n))

    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    new = new.replace(C_ANCHOR, C_INSERT + C_ANCHOR, 1)
    new = new.replace(CSS_OLD, CSS_ADD.lstrip("\n") + "\n" + CSS_OLD, 1)
    # the two new pages need their style in the document
    new = new.replace("    out.append(_S34_PRINT_CSS)",
                      "    out.append(_OWN_SHEET_CSS)\n    out.append(_S34_PRINT_CSS)", 1)

    bak = TARGET + ".bak_S240sheets_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after the edit (%s); %s restored" % (ex, TARGET))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("   added : SHEET 5 (full working) and the SALARY SLIP, one pair per own-sheet person")
    print("   %s : %s -> %s" % (os.path.basename(TARGET), cur[:8], got[:8]))
    print("   backup    : %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())

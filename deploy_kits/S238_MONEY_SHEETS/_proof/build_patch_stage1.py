#!/usr/bin/env python3
"""build_patch.py -- salary_policy.py v1.7 (7c0cfb94...) -> v1.8 (S238): Sheet 1 prints
as exactly two A4 pages -- page 1 the machine-data grid (all days), page 2 the month
summary. Anchored, exactly-once edits; anything else aborts."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
PIN = "7c0cfb940df2b542d1c4eb849ee3f924"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not the pinned v1.7")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

rep('''"""
salary_policy.py — v1.7 (S200/R10)''', '''"""
salary_policy.py — v1.8 (S238) — Sheet 1 PRINTS AS TWO A4 PAGES: page 1 the
machine-data grid with every day of the month (it was cut off at 100%: the grid
sat in a scrolling box, which a printer clips), page 2 the month summary with the
staff-remark column (the owner, 10-Sep-2026). Screen view unchanged.
v1.7 (S200/R10)''', "doc")

rep('''    for half in halves:
        days = [d for d in half]
        out.append('<div class="tw"><table><tr><th>Staff</th>')''', '''    out.append('<div class="s1grid">')
    for half in halves:
        days = [d for d in half]
        out.append('<div class="tw"><table><tr><th>Staff</th>')''', "grid_open")

rep('''            out.append("</tr>")
        out.append("</table></div>")

    out.append("<h2>Month summary</h2><div class='tw'><table>"''', '''            out.append("</tr>")
        out.append("</table></div>")
    out.append('<div class="sub">Cell = arrival time (amber 11–59 min late, red '
               '&ge;60). Hover for the out-punch. L sanctioned leave · A absent · '
               '&#42; approved present-request. Sundays carry the purple SUN column. '
               'The running day is excluded until '
               'it ends. Money appears on no staff copy.</div>')
    out.append('</div><div class="s1sum">')
    out.append('<div class="printonly">%s</div>'
               % _clinic_hdr("SHEET 1 · MONTH SUMMARY — %s" % month_words(ym)))
    out.append("<h2>Month summary</h2><div class='tw'><table>"''', "grid_close")

rep('''    else:
        out.append("</table></div>")
    out.append('<div class="sub">Cell = arrival time (amber 11–59 min late, red '
               '&ge;60). Hover for the out-punch. L sanctioned leave · A absent · '
               '&#42; approved present-request. Sundays carry the purple SUN column. '
               'The running day is excluded until '
               'it ends. Money appears on no staff copy.</div>')
    out.append("</body></html>")
    return "".join(out)''', '''    else:
        out.append("</table></div>")
    out.append("</div>")
    out.append(_S1_PRINT_CSS)
    out.append("</body></html>")
    return "".join(out)


# S238: A4, two pages. Page 1 = the grid (every day, never clipped), page 2 = the
# summary. The screen view is untouched; these rules act only when printing.
_S1_PRINT_CSS = """<style>
 .printonly{display:none}
 @page{size:A4 portrait;margin:8mm}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .printonly{display:block}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:12px;margin:0 0 4px}
  .hdr .cap{font-size:10px;margin-top:2px}
  .banner,.note{font-size:10.5px;padding:4px 8px;margin:6px 0}
  .sub{font-size:10.5px}
  .s1grid table{width:100%;table-layout:fixed;margin:4px 0}
  .s1grid th,.s1grid td{font-size:11.5px;padding:6px 0;line-height:1.25;text-align:center;white-space:nowrap;overflow:hidden}
  .s1grid th:first-child,.s1grid td:first-child{width:22mm;text-align:left;padding-left:3px;font-size:12px}
  .s1grid .gcell{font-size:11.5px}
  .s1grid .sub{font-size:12px;color:#333}
  .s1grid th.sun small{font-size:6px;letter-spacing:0}
  .s1grid td.sun,.s1grid th.sun{border-left:2px solid #7c5cff}
  .s1grid{break-after:page;page-break-after:always}
  .s1grid .tw{break-inside:avoid;page-break-inside:avoid}
  .s1sum table{width:100%}
  .s1sum th,.s1sum td{font-size:11px;padding:4px 6px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""''', "tail")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())

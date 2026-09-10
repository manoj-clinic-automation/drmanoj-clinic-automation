#!/usr/bin/env python3
"""build_patch_stage4.py -- salary_policy.py v1.9 (e848c81f..., LIVE since 10-Sep 22:07)
-> v1.10 (S238, the owner's third review, 10-Sep-2026 late night).
Anchored, exactly-once edits; anything else aborts."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
PIN = "e848c81f14d3a01b5311d218e2a1ee35"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not the live v1.9")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

rep('''salary_policy.py — v1.9 (S238, the owner's second Sheet-2 review)''',
    '''salary_policy.py — v1.10 (S238, the owner's third review) — last month's hold is shown
where it bites: 'deducted now' and 'written off' columns in the fines table and on the
salary sheet; Sheet 1's month summary carries the days not punched (with their dates,
Sundays marked) for the physical-register check, the late fine in total (no hold split),
and overtime minutes with OT payable (2 x own minute-rate, real out-punch only, D256);
OT enters the net only when the setting ot_pay = 1.
v1.9 (S238, the owner's second Sheet-2 review)''', "doc")

# ---- 1. OT: computed from the report's own OT-candidate minutes (D256) ----------------
rep('''    "hold_enabled": 1,''', '''    "hold_enabled": 1,
    "ot_pay": 0,                # S238: 1 = OT payable enters the net; 0 = shown only (owner to rule)''', "ot_setting")
rep('''        duty_credits = round(night_rs + extra_rs + outst_rs, 2)''',
    '''        duty_credits = round(night_rs + extra_rs + outst_rs, 2)
        # S238 v1.10: overtime -- the attendance report's minutes beyond shift end on days
        # with a REAL out-punch (F-47), paid at 2 x the person's own minute-rate (D256).
        ot_min = 0 if exempt else int(a.get("ot_min", 0) or 0)
        ot_rs = round(ot_min * rate * 2, 2) if (base and ot_min) else 0.0
        ot_paid = ot_rs if s.get("ot_pay") else 0.0''', "ot_calc")
rep('''        net = round(base - deductions - adv_ded + duty_credits, 2) if base else 0.0''',
    '''        net = round(base - deductions - adv_ded + duty_credits + ot_paid, 2) if base else 0.0''', "ot_net")
rep('''            "outst_days": outst,''', '''            "outst_days": outst, "ot_min": ot_min, "ot_rs": ot_rs, "ot_paid": ot_paid,''', "ot_out")

# ---- 2. Sheet 1 month summary: days not punched + dates, late fine, OT -------------------
a = s.index('''    out.append("<h2>Month summary</h2><div class='tw'><table>"''')
b = s.index('''    out.append("</div>")
    out.append(_S1_PRINT_CSS)''')
s = s[:a] + '''    money_ok = only_uid is None            # money never appears on a staff copy
    out.append("<h2>Month summary</h2><div class='tw'><table class='s1t'>"
               "<tr><th rowspan='2'>Staff</th><th rowspan='2'>Present</th>"
               "<th colspan='4'>DAYS NOT PUNCHED on the machine</th>"
               "<th rowspan='2' class='dcol'>Dates not punched<br><small>(check against the "
               "physical register · <span class='sunk'>Sun</span> · L = sanctioned leave)</small></th>"
               "<th rowspan='2'>Late marks</th><th rowspan='2'>Late min</th>"
               + ("<th rowspan='2'>Late fine<br><small>(total)</small></th>" if money_ok else "")
               + "<th rowspan='2'>OT min</th>"
               + ("<th rowspan='2'>OT payable<br><small>%s</small></th>"
                  % ("in the net" if res["settings"].get("ot_pay") else "shown, not paid")
                  if money_ok else "")
               + ("<th rowspan='2' class='rcol'>Remark</th>" if print_ else "")
               + "</tr><tr><th>total</th><th>sanctioned leave</th><th>outstation</th>"
               "<th>absent, no leave</th></tr>")
    for st in rows:
        lv = st.get("leave_dates") or set()
        ds = []
        for d in sorted(st.get("absent_dates") or []):
            try:
                dd = datetime.date.fromisoformat(d)
            except (ValueError, TypeError):
                continue
            t = "%d" % dd.day + ("L" if d in lv else "")
            ds.append("<span class='sunk'>%s</span>" % t if dd.weekday() == 6 else t)
        absent = st.get("absent", 0)
        lia = st.get("leave_in_absent", 0)
        outst = min(st.get("outst_days", 0), max(0, absent - lia))
        out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                   "<td class='n'>%d</td><td class='n'>%d</td><td class='n'>%d</td>"
                   "<td class='dcol'>%s</td><td class='n'>%d</td><td class='n'>%d</td>%s"
                   "<td class='n'>%d</td>%s%s</tr>"
                   % (e(st["name"]), st["present"], absent, lia, outst,
                      max(0, absent - lia - outst), ", ".join(ds) or "—",
                      st["marks"], st["late_min"],
                      ("<td class='n'>%s</td>" % money(st["late_charge"])) if money_ok else "",
                      st.get("ot_min", 0),
                      ("<td class='n'>%s</td>" % money(st.get("ot_rs", 0))) if money_ok else "",
                      "<td class='rcol'></td>" if print_ else ""))
    out.append("</table></div>")
    out.append('<div class="sub">Days not punched = sanctioned leave + outstation + absent '
               'without leave (one set of days). OT = minutes beyond shift end on days with a '
               'real out-punch.%s%s</div>'
               % (' Late fine = the whole month\\'s late charge before any hold; OT payable at '
                  '2 &times; own minute-rate.' if money_ok else '',
                  ' The blank last column is the staff-remark space.' if print_ else ''))
''' + s[b:]

rep(''' @page{size:A4 portrait;margin:8mm}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .printonly{display:block}''', ''' @page{size:A4 portrait;margin:8mm}
 @page s1sum{size:A4 landscape;margin:8mm}
 .sunk{color:#4c1d95;font-weight:800;background:#ece6ff;padding:0 2px;border-radius:3px}
 .s1t td.dcol{white-space:normal;min-width:180px;max-width:320px;font-size:13px}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .printonly{display:block}
  .s1sum{page:s1sum}
  .s1t td.dcol{font-size:10.5px;max-width:none}
  .s1t .rcol{width:26mm}''', "s1_css")

# ---- 3. Sheet 2 fines table: last month's hold, deducted / written off ------------------
rep('''                   "<th rowspan='2'>Late charge</th><th rowspan='2'>Collect now</th><th rowspan='2'>Hold</th>"
                   "<th rowspan='2'>Leave amt<br><small>(+ded / −credit)</small></th>"''',
    '''                   "<th rowspan='2'>Late charge</th><th rowspan='2'>Collect now</th><th rowspan='2'>Hold</th>"
                   "<th colspan='2'>%s hold</th>"
                   "<th rowspan='2'>Leave amt<br><small>(+ded / −credit)</small></th>"''', "fines_head1")
rep('''                   "<tr><th>total</th><th>sanctioned leave</th><th>outstation</th>"
                   "<th>absent, no leave</th></tr>")
        for st in res["staff"]:''', '''                   "<tr><th>total</th><th>sanctioned leave</th><th>outstation</th>"
                   "<th>absent, no leave</th><th>deducted now</th><th>written off</th></tr>"
                   % month_words(prev_ym(ym))[:3])
        for st in res["staff"]:''', "fines_head2")
rep('''                           st["late_charge"], st["collect"], st["held"], st["leave_amt"],
                           st["fine_uninf"], st["fine_exc"], st["dress_rs"],''',
    '''                           st["late_charge"], st["collect"], st["held"],
                           st.get("prior_collect", 0), st.get("release", 0), st["leave_amt"],
                           st["fine_uninf"], st["fine_exc"], st["dress_rs"],''', "fines_vals")
rep('''                   "Outstation days are duty, not leave.</div></section>")''',
    '''                   "Outstation days are duty, not leave. Last month's hold: 'deducted now' "
                   "comes off this salary (improvement under the bar); 'written off' is never "
                   "recovered (improvement at or over the bar).</div></section>")''', "fines_note")

# ---- 4. Sheet 3: last month's hold visible, OT column --------------------------------------
rep('''            "Marks", "Late charge", "Collect now", "Hold", "Hold released",
            "Dress", "I-card", "D+I fine", "Fines", "Duty credits", "Incentive→pot",
            "NET PAYABLE"]''', '''            "Marks", "Late charge", "Collect now", "Hold",
            "Prev hold deducted", "Prev hold written off",
            "Dress", "I-card", "D+I fine", "Fines", "Duty credits", "OT paid",
            "Incentive (to pot)", "NET PAYABLE"]''', "s3_cols")
rep('''                st["collect"], st["held"], st["release"], st["dress_days"],
                st["icard_days"], di, fines, st["duty_credits"], st["incentive"],
                st["net"]]''', '''                st["collect"], st["held"], st.get("prior_collect", 0), st["release"],
                st["dress_days"], st["icard_days"], di, fines, st["duty_credits"],
                st.get("ot_paid", 0), st["incentive"], st["net"]]''', "s3_vals")
# ---- 5. Sheet 3 prints A4 LANDSCAPE, every column inside the page; Sheet 4 portrait -------
rep("""    out.append("<div class='tw'><table><tr>" +
               "".join("<th>%s</th>" % c for c in cols) + "</tr>")
    tot = dict.fromkeys(range(len(cols)), 0.0)""", """    out.append("<div class='tw'><table class='s3t'><tr>" +
               "".join("<th>%s</th>" % c for c in cols) + "</tr>")
    tot = dict.fromkeys(range(len(cols)), 0.0)""", "s3_table")
rep("""    out.append('<div style="page-break-before:always"></div>')
    out.append(_clinic_hdr("SHEET 4 · SALARY PAYMENT &amp; SIGNATURE — %s" % month_words(ym), cap))""",
    """    out.append('<div class="s4pg" style="page-break-before:always">')
    out.append(_clinic_hdr("SHEET 4 · SALARY PAYMENT & SIGNATURE — %s" % month_words(ym), cap))""", "s4_open")
rep("""    out.append('<div class="sub">Received the above amount in full. / '
               'उपरोक्त राशि पूरी प्राप्त की।</div>')
    out.append("</body></html>")""", """    out.append('<div class="sub">Received the above amount in full. / '
               'उपरोक्त राशि पूरी प्राप्त की।</div></div>')
    out.append(_S34_PRINT_CSS)
    out.append("</body></html>")""", "s4_close")
rep("""# S238: Sheet 2 on A4 — every section whole on one sheet""", """# S238 v1.10: Sheet 3 on A4 LANDSCAPE with every column inside the page (it had
# grown past portrait width); Sheet 4, the signature sheet, stays portrait.
_S34_PRINT_CSS = \"\"\"<style>
 @page{size:A4 landscape;margin:7mm}
 @page s4{size:A4 portrait;margin:10mm}
 @media print{
  body{margin:0;font-size:10px;line-height:1.25}
  .tw{overflow:visible}
  .hdr h1{font-size:16px} .hdr .sub{font-size:11.5px;margin:0 0 3px}
  table.s3t{width:100%;table-layout:auto}
  table.s3t th{font-size:9px;padding:3px 2px;white-space:normal;line-height:1.15;vertical-align:bottom}
  table.s3t td{font-size:10px;padding:4px 2px}
  .s4pg{page:s4}
  .s4pg table{width:100%}
  .s4pg th,.s4pg td{font-size:12px;padding:6px 8px}
  .sub{font-size:9.5px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>\"\"\"


# S238: Sheet 2 on A4 — every section whole on one sheet""", "s34_css")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())

#!/usr/bin/env python3
"""build_patch_register2.py -- staff_register.py v0.13 (d217f3f0..., LIVE since
10-Sep 20:55) -> v0.14 (S238): STEP 0 of the month-end flow -- the machine-absent
days, staff-wise, printed for checking against the PHYSICAL attendance register,
with the FIX ABSENTS desk one click away (the owner, 10-Sep-2026: "that should be a
step before the computation of the final salary"). Anchored, exactly-once edits."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
PIN = "d217f3f0091a570e2b8da41e6c937785"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not the live v0.13")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

rep('''v0.13(S238) — the Lock refuses''', '''v0.14(S238) — STEP 0 of the month-end flow: the machine-absent days, staff-wise,
              printable for checking against the physical attendance register
              (/salary/flow/verify), then corrected on the FIX ABSENTS desk --
              before Sheet 1 is approved and the salary is worked out.
v0.13(S238) — the Lock refuses''', "doc")

rep('''@app.route(APP_PREFIX + "/salary/flow")
@require("salary")
def salary_flow():''', '''VERIFY_HTML = """<!doctype html><meta charset="utf-8">
<title>Step 0 - absent days to check - {{ ym }}</title>
<style>
 body{font-family:Segoe UI,Arial,sans-serif;margin:14px;color:#111;background:#fff;font-size:13px}
 h1{font-size:18px;margin:0 0 2px} .sub{color:#444;font-size:12.5px;margin:0 0 8px}
 .how{border:1px solid #999;border-radius:6px;padding:6px 10px;margin:6px 0 10px;font-size:12.5px;background:#f6f6f6}
 .bar a{margin-right:14px;color:#05c;font-weight:bold}
 .grid{columns:2;column-gap:14px}
 .blk{break-inside:avoid;page-break-inside:avoid;border:1px solid #888;border-radius:6px;padding:4px 8px 6px;margin:0 0 10px;display:inline-block;width:100%;box-sizing:border-box}
 .blk h2{font-size:14px;margin:2px 0 4px} .blk h2 small{font-weight:400;color:#444}
 table{border-collapse:collapse;width:100%;table-layout:fixed} th,td{border:1px solid #bbb;padding:3px 5px;text-align:left;font-size:12.5px}
 th.c1{width:30%} th.c2{width:52%} th.c3{width:18%}
 th{background:#eee;font-size:11.5px} td.box{width:26%} tr.done td{color:#555}
 .sun{font-weight:bold} .err{border:2px solid #b00;padding:8px;border-radius:6px}
 @page{size:A4 portrait;margin:9mm}
 @media print{.noprint{display:none!important} body{margin:0}}
</style>
<div class="bar noprint"><a href="{{ prefix }}/salary/flow?ym={{ ym }}">&larr; Month-end flow</a>
 <a href="{{ prefix }}/fixabsents?ym={{ ym }}">Fix absents desk &rarr;</a>
 <a href="#" onclick="window.print();return false">Print</a></div>
<h1>STEP 0 &middot; Absent days to check against the PHYSICAL register &mdash; {{ month }}</h1>
<div class="sub">Machine data as on {{ today }} &middot; {{ nstaff }} staff &middot;
 {{ nopen }} day(s) still marked absent &middot; {{ ndone }} already corrected</div>
<div class="how">For every date below the biometric machine has <b>no punch</b> although the person
 was on the roster. Look each date up in the physical attendance register and write in the box:
 <b>P</b> = present (the machine missed the punch) &middot; <b>L</b> = on leave &middot; <b>A</b> = absent.
 Then mark every <b>P</b> present on the <b>Fix absents</b> desk (with the in-time from the register),
 and tick &ldquo;done&rdquo;. What is left is the final attendance &mdash; approve Sheet 1 only after this.</div>
{% if not feed_ok %}<div class="err">The punch feed is unavailable, so absences cannot be listed.
 This page will not guess &mdash; try again later.</div>
{% elif not blocks %}<div class="how">No machine-absent days in {{ month }}.</div>
{% else %}<div class="grid">
{% for b in blocks %}<div class="blk"><h2>{{ b.name }} <small>&mdash; {{ b.absent }} day(s) without a punch
 {% if b.corrected %}&middot; {{ b.corrected }} already corrected{% endif %}</small></h2>
<table><tr><th class="c1">Date</th><th class="c2">Register says (P / L / A)</th><th class="c3">done</th></tr>
{% for r in b["items"] %}<tr{% if r.done %} class="done"{% endif %}>
 <td>{{ r.d[8:10] }}-{{ r.d[5:7] }} {% if r.sun %}<span class="sun">Sun</span>{% else %}{{ r.dow }}{% endif %}</td>
 {% if r.done %}<td colspan="2">&#10003; already marked present{% if r["in"] %} (in {{ r["in"] }}){% endif %}</td>
 {% else %}<td class="box"></td><td></td>{% endif %}</tr>
{% endfor %}</table></div>
{% endfor %}</div>{% endif %}
<div class="sub">Days a staff member has already asked to be marked present (awaiting a decision) are in the
 requests queue, not on this list. Holidays and rostered-off days are never listed.</div>
<div class="sub" style="margin-top:14px">Checked by: ____________________ &nbsp; Date: ____________</div>
"""


def _verify_blocks(ym):
    """STEP 0 data: absent_worklist, each staff's open and corrected days in one
    date-ordered list. Returns (blocks, feed_ok)."""
    con = get_db()
    try:
        blocks, feed_ok = absent_worklist(con, ym)
    finally:
        con.close()
    for b in blocks:
        items = [dict(r, done=False) for r in b["rows"]] + [dict(r, done=True) for r in b["done"]]
        b["items"] = sorted(items, key=lambda r: r["d"])
    return blocks, feed_ok


@app.route(APP_PREFIX + "/salary/flow/verify")
@require("salary")
def salary_flow_verify():
    ym = _flow_ym()
    blocks, feed_ok = _verify_blocks(ym)
    try:
        month = datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except Exception:
        month = ym
    return render_template_string(
        VERIFY_HTML, prefix=APP_PREFIX, ym=ym, month=month, blocks=blocks, feed_ok=feed_ok,
        today=_today(), nstaff=len(blocks),
        nopen=sum(len(b["rows"]) for b in blocks), ndone=sum(len(b["done"]) for b in blocks))


@app.route(APP_PREFIX + "/salary/flow")
@require("salary")
def salary_flow():''', "verify_route")

rep('''    con.close()
    return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym,
                                  s1=st.get("sheet1"), s2=st.get("sheet2"), remarks=remarks,
                                  msg=request.args.get("msg", ""), err="")''', '''    con.close()
    try:                                   # STEP 0 counts; the flow page never dies on them
        _vb, _vok = _verify_blocks(ym)
        v0 = {"ok": _vok, "open": sum(len(b["rows"]) for b in _vb),
              "done": sum(len(b["done"]) for b in _vb), "staff": len(_vb)}
    except Exception:
        v0 = {"ok": False, "open": 0, "done": 0, "staff": 0}
    return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym, v0=v0,
                                  s1=st.get("sheet1"), s2=st.get("sheet2"), remarks=remarks,
                                  msg=request.args.get("msg", ""), err="")''', "flow_v0")

rep('''<ol style="line-height:2">
  <li><a href="{{ prefix }}/salary/flow/sheet1?ym={{ ym }}" style="color:#5fd">SHEET 1 — attendance grid</a>''',
    '''<ol start="0" style="line-height:2">
  <li><a href="{{ prefix }}/salary/flow/verify?ym={{ ym }}" style="color:#5fd">STEP 0 — absent days to check against the physical register</a>
      (print it) · <a href="{{ prefix }}/fixabsents?ym={{ ym }}" style="color:#fd5">Fix absents desk</a>
      {% if v0 %}{% if v0.ok %} &mdash; {{ v0.open }} day(s) still absent{% if v0.done %}, {{ v0.done }} corrected{% endif %}{% else %} &mdash; <i>punch feed unavailable</i>{% endif %}{% endif %}
      <br><small style="color:#9ab">Do this first: what is left after the corrections is the final attendance.</small></li>
  <li><a href="{{ prefix }}/salary/flow/sheet1?ym={{ ym }}" style="color:#5fd">SHEET 1 — attendance grid</a>''', "flow_li")

rep('''    rF = c.get(APP_PREFIX + "/fixabsents?ym=2026-08")
    assert rF.status_code == 200 and b"Fix absents" in rF.data
    assert b'name="pick" value="2026-08-04|6"' not in rF.data, \\''', '''    rF = c.get(APP_PREFIX + "/fixabsents?ym=2026-08")
    assert rF.status_code == 200 and b"Fix absents" in rF.data
    # S238 v0.14: STEP 0 -- the printable check list carries the same days
    rV = c.get(APP_PREFIX + "/salary/flow/verify?ym=2026-08")
    assert rV.status_code == 200 and b"PHYSICAL register" in rV.data, "step 0 page"
    assert b"04-08" in rV.data and b"already marked present" in rV.data, \\
        "step 0 must list the open absence and show the corrected one as done"
    rV = c.get(APP_PREFIX + "/salary/flow?ym=2026-08")
    assert rV.status_code == 200 and b"STEP 0" in rV.data and b"still absent" in rV.data
    assert c2.get(APP_PREFIX + "/salary/flow/verify?ym=2026-08").status_code != 200, \\
        "a maker must not reach the salary flow's step 0"
    assert b'name="pick" value="2026-08-04|6"' not in rF.data, \\''', "selftest")

open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())

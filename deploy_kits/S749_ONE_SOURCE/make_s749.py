#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s749.py -- S749_ONE_SOURCE: the appended sections and the anchored changes of the six live files (four of this project, two of the parent's).
    python3 -B make_s749.py <finance dir> <portal dir> <out dir> [<dir holding the S749 sections>]
Each FROM file must carry its pinned md5 (the 08-Nov bundle, 03:15 IST); every anchor must stand EXACTLY ONCE; the TO md5s are printed.
The sections are read from sec_sr749.txt, sec_amir749.txt, sec_porders749.txt, sec_pa749.txt and sec_mread749.txt beside this script."""
import hashlib
import os
import sys

FROM = {"finance/scan_register.py": "12e3c7cb057b678084de7c82e414e1bf",     # S740's TO (live 07-Nov 10:0x; the 08-Nov bundle)
        "finance/purchase_app.py": "600c96d733da7885f98ab6272ac6e8ad",      # S740's TO
        "finance/amir_day.py": "42a8430be4a9df19701326d8efb6159a",          # S740's TO
        "finance/porders.py": "eda0a4c6d31a011611b6c786f6d49512",           # S726's TO (confirmed by the 08-Nov bundle)
        "finance/month_read.py": "d5d6f676e15f15583229243093a4b2f4",        # the parent's, the 08-Nov bundle (PLANNED, D646)
        "portal/portal.py": "d52261a25791fb00bfdc6cbfcb44a124"}             # the parent's, the 08-Nov bundle (PLANNED, D646)
APPEND = {"finance/scan_register.py": "sec_sr749.txt", "finance/amir_day.py": "sec_amir749.txt", "finance/porders.py": "sec_porders749.txt",
          "finance/month_read.py": "sec_mread749.txt", "finance/purchase_app.py": "sec_pa749.txt"}

# purchase_app.py -- the anchored changes (each anchor exactly once)
PA_EDITS = [
    # the audit page: the register's states read once
    ('''    s = _month_summary(con, month)
    final = s["status"]["status"] == "final"
    doctor, viewer = _is_doctor(u), _is_viewer_only(u)
    gate = (False, []) if final else _lock_gate(con, month, s)          # S604: the one gate
''',
     '''    s = _month_summary(con, month)
    final = s["status"]["status"] == "final"
    doctor, viewer = _is_doctor(u), _is_viewer_only(u)
    gate = (False, []) if final else _lock_gate(con, month, s)          # S604: the one gate
    s749 = _s749_states(con, month)                                       # S749: the register's word and whose/next per bill
'''),
    # the audit page: Correct / Wrong off the doctor's view (one place to decide: his step view)
    ('''            if not final and not viewer and b["id"] in s["needs_verdict"]:''',
     '''            if not final and not viewer and not doctor and b["id"] in s["needs_verdict"]:      # S749: not on the doctor's view'''),
    # the audit page: the two new cells
    ('''            out.append('<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                       '<td class="n">%d</td><td>%s</td><td>%s%s</td></tr>'
                       % (_human(b["bill_date"]), _esc(b["bill_no"]), _r(b["marg_p"]), _r(tot) if n else "\\u2014",
                          n, scan, vh, btn))''',
     '''            sw_, sn_, _sk = s749.get(b["id"]) or ("\\u2014", "", "")            # S749
            out.append('<tr><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                       '<td class="n">%d</td><td>%s</td><td><b>%s</b></td><td class="muted">%s</td><td>%s%s</td></tr>'
                       % (_human(b["bill_date"]), _esc(b["bill_no"]), _r(b["marg_p"]), _r(tot) if n else "\\u2014",
                          n, scan, _esc(sw_), _esc(sn_), vh, btn))'''),
    ('''            '<th class="n">Lines</th><th>Scan</th><th>Check</th></tr>%s</table></div>%s</div>\'''',
     '''            '<th class="n">Lines</th><th>Scan</th><th>Purchase check</th><th>Next \\u00b7 whose</th><th>Check</th></tr>%s</table></div>%s</div>\''''),
    ('''        out.append('<tr><th colspan="7" style="text-transform:none;font-size:14px;color:var(--ink);\'''',
     '''        out.append('<tr><th colspan="9" style="text-transform:none;font-size:14px;color:var(--ink);\''''),
    ('''               '<tr><td colspan="7" class="muted">No bills for this month.</td></tr>', und))''',
     '''               '<tr><td colspan="9" class="muted">No bills for this month.</td></tr>', und))'''),
    ('''    body = ('<h1>%s \\u2014 purchases</h1><div class="muted">This is the purchase audit''',
     '''    body = (_s749_strip(con, month, "month") + '<h1>%s \\u2014 purchases</h1><div class="muted">This is the purchase audit'''),
    # the hub: the register's words per month; the scan card for counted months only
    ('''        rows.append('<tr><td><a href="%s/page/month/%s">%s</a></td><td class="n"><b>%s</b>%s</td>'
                    '<td class="n">%s</td><td class="n">%d</td><td class="n">%d</td>'
                    '<td class="n %s">%d</td><td class="n %s">%d</td>'
                    '<td><span class="chip %s">%s</span></td></tr>'
                    '<tr><td colspan="8" class="muted" style="padding-top:2px;padding-bottom:12px">%s</td></tr>'
                    % (prefix, m, _esc(_month_name(m)), _r(s["marg_p"]),
                       "" if s["basis"] == "supplier-wise" else '<div class="muted">bill-wise</div>',
                       _r(s["itemwise_p"]), len(s["bills"]), len(s["returns"]),
                       "warn" if s["no_lines"] else "", len(s["no_lines"]),
                       "bad" if s["wrong"] else "", s["wrong"],
                       "ok" if st == "FINAL" else "warn", st, _esc(story)))''',
     '''        try:                                                   # S749: the register's words for the month
            pc = _s749_hub_words(con, m)
        except Exception as _e749:                             # noqa: BLE001
            pc = '<span class="warn">not read (%s)</span>' % _esc(str(_e749)[:60])
        rows.append('<tr><td><a href="%s/page/month/%s">%s</a></td><td class="n"><b>%s</b>%s</td>'
                    '<td class="n">%s</td><td class="n">%d</td><td class="n">%d</td>'
                    '<td class="n %s">%d</td><td class="n %s">%d</td><td>%s</td>'
                    '<td><span class="chip %s">%s</span></td></tr>'
                    '<tr><td colspan="9" class="muted" style="padding-top:2px;padding-bottom:12px">%s</td></tr>'
                    % (prefix, m, _esc(_month_name(m)), _r(s["marg_p"]),
                       "" if s["basis"] == "supplier-wise" else '<div class="muted">bill-wise</div>',
                       _r(s["itemwise_p"]), len(s["bills"]), len(s["returns"]),
                       "warn" if s["no_lines"] else "", len(s["no_lines"]),
                       "bad" if s["wrong"] else "", s["wrong"], pc,
                       "ok" if st == "FINAL" else "warn", st, _esc(story)))'''),
    ('''              '<th class="n">Wrong</th><th>Status</th></tr>%s</table></div>%s</div>\'''',
     '''              '<th class="n">Wrong</th><th>Purchase check</th><th>Status</th></tr>%s</table></div>%s</div>\''''),
    ('''    sc = _scan_state(con)
    if sc is None:
        scan = ('<div class="card"><h2>Scan links</h2><div class="warn">asset app not reachable</div></div>')
    else:
        scan = ('<div class="card"><h2>Scan links</h2><div class="grid"><div class="kv"><b>%d</b>'
                '<span>pharmacy scans with no Marg bill</span></div><div class="kv"><b>%d</b>'
                '<span>Marg bills with no scan</span></div></div>'
                '<div><a href="%s/page/scans">Open the scan-link page</a></div></div>'
                % (sc["unmatched_scans"], sc["unscanned_bills"], prefix))
''',
     '''    try:                                                       # S749: counted months only, the register's words, the step view the way in
        scan = _s749_hub_scan_card(con, prefix)
    except Exception as _e749:                                 # noqa: BLE001
        scan = '<div class="card"><h2>Purchase check</h2><div class="warn">not read (%s)</div></div>' % _esc(str(_e749)[:80])
'''),
    # the payment sheet: Step 2 by the server; the one lock gate in Step 3; the month strip
    ('''    nextcard = (
        '<div class="card"><h2>3 &middot; Lock it</h2><div class="muted">%s The NEFT total is what '
        'goes into the bank advice file and its covering letter, and they are built from this sheet '
        'and from nothing else.</div></div>'
        % ('This month is <b>final</b>: the figures are locked until it is reopened.' if final
           else 'Finalise the month on its own page once the check above agrees, and these figures lock.'))
''',
     '''    nextcard = _s749_lock_card(con, month, s, final, (False, []) if final else _lock_gate(con, month, s))      # S749: the one gate
'''),
    ('''    body = ('<h1>Vendor payments — %s</h1><div class="muted">Sanjeevni Medicos &middot; the sheet ''',
     '''    body = (_s749_strip(con, month, "pay") + '<h1>Vendor payments — %s</h1><div class="muted">Sanjeevni Medicos &middot; the sheet '''),
]
PA_VERIFY_START = '''    # ----------------------------------------------------- 2 · the verification
    last = _pay_last_check(con, month)
'''
PA_VERIFY_END = '''        '<div id="vout"></div></div>' % (verdict, notes, when, month))
'''
PA_VERIFY_NEW = '''    # ----------------------------------------------------- 2 · the verification -- S749: run by the server, no tap
    verify_card = _s749_verify_card(con, month, s)
'''

# portal.py -- the tile opens the step view (F-1182); the hub stays reachable from it
PORTAL_EDITS = [
    ('''     "desc": "Purchases \\u00b7 scans \\u00b7 orders \\u00b7 stock check",
     "live": True,
     "url": "/finance/purchase/page/hub",''',
     '''     "desc": "Purchase check \\u00b7 the full list \\u00b7 orders",
     "live": True,
     "url": "/finance/purchase/page/check",'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, pairs, name):
    for old, new in pairs:
        n = text.count(old)
        if n != 1:
            sys.exit("REFUSED: %s anchor found %d times (must be once): %s" % (name, n, old.strip().splitlines()[0][:90]))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    fd, pd, od = sys.argv[1], sys.argv[2], sys.argv[3]
    secd = sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(os.path.abspath(__file__))
    src = {}
    for n, pin in FROM.items():
        path = os.path.join(fd if n.startswith("finance/") else pd, os.path.basename(n))
        b = open(path, "rb").read()
        if md5(b) != pin:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (n, md5(b)[:8], pin[:8]))
        src[n] = b.decode("utf-8")
    out = {}
    pa = src["finance/purchase_app.py"]
    pa = edit(pa, PA_EDITS, "purchase_app.py")
    i, j = pa.find(PA_VERIFY_START), pa.find(PA_VERIFY_END)
    if pa.count(PA_VERIFY_START) != 1 or pa.count(PA_VERIFY_END) != 1 or j < i:
        sys.exit("REFUSED: purchase_app.py verification block anchors not found once")
    pa = pa[:i] + PA_VERIFY_NEW + pa[j + len(PA_VERIFY_END):]
    src["finance/purchase_app.py"] = pa
    src["portal/portal.py"] = edit(src["portal/portal.py"], PORTAL_EDITS, "portal.py")
    for n, sec in APPEND.items():
        if not src[n].endswith("\n"):
            sys.exit("REFUSED: %s does not end in a newline" % n)
        out[n] = src[n] + open(os.path.join(secd, sec), encoding="utf-8").read()
    out["portal/portal.py"] = src["portal/portal.py"]
    for n in FROM:
        os.makedirs(os.path.join(od, os.path.dirname(n)), exist_ok=True)
        b = out[n].encode("utf-8")
        open(os.path.join(od, n), "wb").write(b)
        print("%s  %s -> %s" % (n, FROM[n][:8], md5(b)))


if __name__ == "__main__":
    main()

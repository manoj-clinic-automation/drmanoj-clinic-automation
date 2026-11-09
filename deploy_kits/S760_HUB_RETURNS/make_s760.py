#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s760.py -- S760_HUB_RETURNS: the anchored changes and the appended sections of four live files (this project's only).
    python3 -B make_s760.py <finance dir> <out dir> [<dir holding the sec_*760.txt files>]
Each FROM file must carry its pinned md5 (the live bytes of 09-Nov: the 09-Nov bundle); every anchor must stand EXACTLY the number of
times named; the TO md5s are printed. finance_app.py is not touched."""
import hashlib
import os
import sys

FROM = {"finance/returns_kinds.py": "9dd7175de142cbf3c8f6e6b415580822",                 # S677's TO (the 09-Nov bundle)
        "finance/darpan_app.py": "a55ecbed4bbe1230b24565b4185b8755",                    # S488's TO (the 09-Nov bundle)
        "finance/finance_ui/finance_approvals.html": "037af6261a636273a71db99625da4abf",  # S657's TO (the 09-Nov bundle)
        "finance/sanjeevni_approvals.py": "d063e939bbe14d21a3741b8629fceef7"}           # the 09-Nov bundle (CONFIRMED)
APPEND = {"finance/returns_kinds.py": "sec_rk760.txt", "finance/darpan_app.py": "sec_da760.txt",
          "finance/sanjeevni_approvals.py": "sec_sa760.txt"}

RK_EDITS = [
    # S760 (no new GET writes): kind_of and enrich gain save=True; the hub reads with save=False and writes nothing.
    # cn-detail, flip, month_fields and pending_count keep save=True -- byte-for-byte the old behaviour.
    ('''def kind_of(con, unit, date, bill, recompute):
    """The stored kind (the owner's word always; the auto word when the month is closed), else classified and stored."""
    ensure(con)
    b = str(bill or "").strip().upper()
''',
     '''def kind_of(con, unit, date, bill, recompute, save=True):
    """The stored kind (the owner's word always; the auto word when the month is closed), else classified and stored.
    S760: save=False gives the same answer and writes nothing (the hub's GETs)."""
    b = str(bill or "").strip().upper()
    if save:
        ensure(con)
    elif not _has(con, "cn_kind"):
        kind, why = classify(con, unit, date, b)
        return dict(kind=kind, why=why, source="auto", by=None, at=_now())
''', 1),
    ('''    kind, why = classify(con, unit, date, b)
    if not r or r[0] != kind or r[1] != why:
''',
     '''    kind, why = classify(con, unit, date, b)
    if save and (not r or r[0] != kind or r[1] != why):                          # S760: never on the hub's GETs
''', 1),
    ('''def enrich(con, unit, month, notes, with_prev=True):
    """Adds to every cn-detail note: kind, kind_why, kind_source, kind_by, status, diff_p, noise, needs_ok, pending_ok,
    patient_text. Returns the section's summary."""
    ensure(con)
''',
     '''def enrich(con, unit, month, notes, with_prev=True, save=True):
    """Adds to every cn-detail note: kind, kind_why, kind_source, kind_by, status, diff_p, noise, needs_ok, pending_ok,
    patient_text. Returns the section's summary. S760: save=False reads the kinds without storing them (the hub)."""
    if save:
        ensure(con)
''', 1),
    ('''        k = kind_of(con, unit, n["date"], n["bill"], recompute)
''',
     '''        k = kind_of(con, unit, n["date"], n["bill"], recompute, save=save)
''', 1),
    # F-1200: the shortfall carries the rounding line too (the S406 rule had reached only diff_p)
    ('''        n["noise"] = bool(noise)
''',
     '''        n["noise"] = bool(noise)
        n["short_noise"] = bool(n.get("refund_shortfall_p")) and is_noise(st, int(n.get("refund_shortfall_p") or 0), amt)   # S760 F-1200
''', 1),
]

DA_EDITS = [
    # S760: a return only the spine holds (an orphan credit note) can be decided -- its date read from the spine, read only
    ('''        if not d0:
            return jsonify(ok=False, error="not_found",
                           message="no return bill %s on this server" % bill), 404
''',
     '''        if not d0:
            d0 = _s760_spine_cn_date(bill)                         # S760: the spine's credit note, read only
        if not d0:
            return jsonify(ok=False, error="not_found",
                           message="no return bill %s on this server" % bill), 404
''', 1),
]

SA_EDITS = [
    # the Needs-you returns line: the card's own read (returns_kinds.hub, light), the S446 line its fail-soft
    ('''    rl = _s446_returns_line(con, today)
''',
     '''    rl = _s760_returns_line(con, today)                     # S760: one source with the hub's Returns card; S446's line its fail-soft
''', 1),
]

HTML_HEADER = ('<!doctype html>\n<!-- S410_MEDICINE_ORDERING',
               '<!doctype html>\n<!-- KIT_S760 S760_HUB_RETURNS (Sanjeevni session 414, 09-Nov-2026, D873 / F-1200): the Returns card as approved -- every\n'
               '     month on one card (the month picker goes), the returns waiting for the owner\'s OK from every month together at the top,\n'
               '     newest first, each naming only the medicine in question with Approve / Reject, the batch check a count, can\'t-be-checked\n'
               '     beneath, the months folded with June - August as history, petty refund differences not shown (F-1200). One read:\n'
               '     /finance/darpan/api/cn-hub. The S406 month view (loadCN406) and the first view (loadCNOld) one link away.\n'
               '  -- kit S410 header below --\n<!-- S410_MEDICINE_ORDERING', 1)

HTML_CARD = ('''<div class="card" id="returnsCard"><h2><span class="kick">Credit notes, each to its medicines</span>Returns</h2>
  <div class="row"><span class="mut">month</span><input type="month" id="cnMonth" onchange="loadCN()">
  <button class="ghost" onclick="loadCN()">show</button></div>
  <div id="cnBox" class="note" style="margin-top:8px">loading&hellip;</div>
</div>''',
             '''<div class="card" id="returnsCard"><h2><span class="kick">Credit notes · every month on one card</span>Returns</h2>
  <input type="hidden" id="cnMonth" value="">
  <div id="cnMsg" style="font-size:13px"></div>
  <div id="cnBox" style="margin-top:6px">loading&hellip;</div>
</div>''', 1)

HTML_LOADCN = ('''function loadCN(){
  if(window.CN_OLD){loadCNOld();return}
  var box=$("cnBox"); if(!box) return;
''', None, 1)            # new text = the S760 block + the S406 renderer renamed loadCN406

HTML_F1200 = ('''     (n.refund_shortfall_p?' · <span class="badge b-warn">₹'+(n.refund_shortfall_p/100).toFixed(2)+' withheld on the refund</span>':'')+
     (n.diff_p!=null?''',
              '''     (n.refund_shortfall_p&&!n.short_noise?' · <span class="badge b-warn">₹'+(n.refund_shortfall_p/100).toFixed(2)+' withheld on the refund</span>':'')+
     (n.diff_p!=null?''', 1)

HTML_SPOT = ('''  var spot=$("spotBox"); if(spot)spot.innerHTML=h||'<span class="mut">nothing on the spot-count list</span>';
}
function loadCNOld(){''',
             '''  var spot=$("spotBox"); if(spot)spot.innerHTML=h||'<span class="mut">nothing on the spot-count list</span>';
  var cs=$("cnSpot"); if(cs){ cs.innerHTML=h||'<span class="mut">nothing on the spot-count list</span>'; var sf=$("cnSpotFold"); if(sf&&/to count</.test(h)) sf.open=true; }   /* S760 */
}
function loadCNOld(){''', 1)

HTML_CSS = ('</style></head><body>', None, 1)


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text, edits, name):
    for old, new, n in edits:
        c = text.count(old)
        if c != n:
            sys.exit("!! %s: anchor stands %d time(s), expected %d:\n%s" % (name, c, n, old[:200]))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fin, out = sys.argv[1], sys.argv[2]
    here = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    sec = lambda f: open(os.path.join(here, f), "rb").read().decode("utf-8")   # noqa: E731
    for rel, want in FROM.items():
        src = os.path.join(fin, rel[len("finance/"):])
        b = open(src, "rb").read()
        if md5(b) != want:
            sys.exit("!! %s is %s, expected %s -- not the live bytes this kit was built on; STOP" % (src, md5(b)[:8], want[:8]))
        if b"\r\n" in b:
            sys.exit("!! %s carries CRLF; STOP" % src)
        t = b.decode("utf-8")
        if "KIT_S760" in t:
            sys.exit("!! %s already carries S760; STOP" % src)
        if rel.endswith("returns_kinds.py"):
            t = apply(t, RK_EDITS, rel)
        elif rel.endswith("darpan_app.py"):
            t = apply(t, DA_EDITS, rel)
        elif rel.endswith("sanjeevni_approvals.py"):
            t = apply(t, SA_EDITS, rel)
        else:
            js, css = sec("sec_js760.txt"), sec("sec_css760.txt")
            t = apply(t, [HTML_HEADER, HTML_CARD, HTML_F1200, HTML_SPOT,
                          (HTML_LOADCN[0], js.rstrip("\n") + "\n" + HTML_LOADCN[0].replace("function loadCN(){", "function loadCN406(){"), 1),
                          (HTML_CSS[0], css.rstrip("\n") + "\n" + HTML_CSS[0], 1)], rel)
            if t.count("function loadCN(){") != 1 or t.count("function loadCN406(){") != 1:
                sys.exit("!! finance_approvals.html: loadCN must stand once, loadCN406 once; STOP")
        if rel in APPEND:
            t = t.rstrip("\n") + "\n" + sec(APPEND[rel])
        nb = t.encode("utf-8")
        os.makedirs(os.path.join(out, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(out, rel), "wb").write(nb)
        print("%s  %s -> %s" % (rel, want[:8], md5(nb)))


if __name__ == "__main__":
    main()

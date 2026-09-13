#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_s254.py -- S254_SHEET_PHONE: the counter sheet on a regular Android phone.

THE OWNER, 13-Sep-2026, after checking it on his phone: "The entry boxes appear so small that the typed
amount is not visible in total. And secondly, it is a long scroll including all the optional sections.
Make extra sections collapsible so that on a regular day it is less scroll and easy submit, expandable
once opened as required, with their text written on the expandable boxes."

TWO FILES, each anchor asserted EXACTLY ONCE:

    clinic_register.py   (live 92136a97929d86b8458e62e1a9c8878f, S251)
      E1  the entry table: each head gets its OWN full-width label row, and the three boxes get a
          row of their own -- so each box has a third of the screen instead of a fifth.
      E2  the physiotherapy row the same way.
      E3  the "End of day -- cash handed over" count is a folded box; its line says what to hand over.
      E4  the "three records" table is a folded box; its line carries the verdict.
      E5  CSS: the folded boxes; the boxes' text at phone width.
    clinic_money.py      (live da9122e0f8b48a1a0aa3d86d02adc109, S253)
      M1  the other-UPI box folded, its line saying what is recorded today; open when there is a row.
      M2  the float box folded, its line carrying the keep-aside / hand-over instruction; open only
          when the day is short or a change was asked.

    python3 -B patch_s254.py --build <src_dir> <out_dir>
    python3 -B patch_s254.py --selftest <src_dir> <kit_dir>
"""
import hashlib
import io
import os
import sys

FROM = {"clinic_register.py": "92136a97929d86b8458e62e1a9c8878f",
        "clinic_money.py": "da9122e0f8b48a1a0aa3d86d02adc109"}
MARKS = {"clinic_register.py": "S254 phone layout", "clinic_money.py": "S254-CLINIC-MONEY-1.3"}

CR = [
("E1 each head: its own label row, then a row of three boxes",
 '''        extra = " <span class='hint'>(counts with Procedures)</span>" if sec == "dress" else ""
        rows.append("<tr><th class='sec'>%s%s</th>%s</tr>" % (label, extra, cells))
''',
 '''        extra = " <span class='hint'>(counts with Procedures)</span>" if sec == "dress" else ""
        # S254 phone layout: the label on a row of its own, the three boxes on the next -- each box a
        # third of the screen, so a typed amount is readable in full on a regular Android phone.
        rows.append("<tr class='head'><th colspan='3'>%s%s</th></tr><tr class='boxes'>%s</tr>" % (label, extra, cells))
'''),
("E2 the physiotherapy row the same way",
 '''    phys = ("<tr><th class='sec'>Physiotherapy</th>%s%s<td><select name='physio_handed_to' class='note'>%s</select></td></tr>"
''',
 '''    phys = ("<tr class='head'><th colspan='3'>Physiotherapy <span class='hint'>cash · UPI · handed to</span></th></tr>"
            "<tr class='boxes'>%s%s<td><select name='physio_handed_to' class='note' style='font-size:15px;padding:6px 2px;min-height:56px'>%s</select></td></tr>"
'''),
("E3 the column headings once, no empty first column; the separator spans three",
 '''        <table class="grid entry"><thead><tr><th></th><th>Cash</th><th>UPI</th><th>Card</th>
          </tr></thead><tbody>%s
          <tr class="sep"><td colspan="4">kept separately at reception</td></tr>
''',
 '''        <table class="grid entry"><thead><tr><th>Cash</th><th>UPI</th><th>Card</th>
          </tr></thead><tbody>%s
          <tr class="sep"><td colspan="3">kept separately at reception</td></tr>
'''),
("E4 the hand-over count, folded; its line says what to hand over",
 '''    return """
      <div class="card"><h2>End of day — cash handed over</h2>
        <p class="mut">Count the notes into piles and type how many of each. The total is worked
        out for you. Coins are at the bottom — leave them empty on a day with none.</p>
        <form method="post">
''',
 '''    # S254: folded. The line on the fold says what to hand over, or what was counted.
    if counted is not None:
        fold_line = "End of day — cash handed over · counted &#8377; %s%s" % (
            _r(counted), " ✓ confirmed" if (row is not None and row["status"] == "confirmed") else "")
    elif exp is not None:
        fold_line = "End of day — cash handed over · &#8377; %s to hand over" % _r(exp)
    else:
        fold_line = "End of day — cash handed over"
    fold_open = " open" if (row is not None and row["status"] != "confirmed") else ""
    return """
      <details class="card"%s><summary>%s</summary>
        <p class="mut">Count the notes into piles and type how many of each. The total is worked
        out for you. Coins are at the bottom — leave them empty on a day with none.</p>
        <form method="post">
'''),
("E5 ... and it closes as a fold",
 '''        %s%s%s
      </div>
<script>
(function(){
  var f=document.querySelectorAll('.qty');
''',
 '''        %s%s%s
      </details>
<script>
(function(){
  var f=document.querySelectorAll('.qty');
'''),
("E6 ... with the two new values in its format tuple",
 '''</script>""" % (band("Notes", NOTES), band("Coins", COINS),
                 _esc("" if row is None else (row["note"] or "")), summary, status, confirm)
''',
 '''</script>""" % (fold_open, fold_line, band("Notes", NOTES), band("Coins", COINS),
                 _esc("" if row is None else (row["note"] or "")), summary, status, confirm)
'''),
("E7 the three records, folded; its line carries the verdict",
 '''    return """
      <div class="card"><h2>The three records, side by side</h2>
        <table class="grid"><thead><tr><th></th><th class="r">Register</th>
          <th class="r">Docterz</th><th class="r">Bank</th><th></th></tr></thead>
          <tbody>%s%s</tbody></table>
        <p class="verdict %s">%s</p>%s
        <p class="mut">This screen states what the three records say. It does not decide who is
        right, and it never accuses anyone. Where two agree and one differs, that is the one to
        look at first.</p>
      </div>""" % ("".join(body), extra, t["verdict"].replace(" ", "_"), _esc(t["why"]), closer)
''',
 '''    return """
      <details class="card"><summary>The three records, side by side · <span class="pill %s">%s</span></summary>
        <div style="overflow-x:auto"><table class="grid"><thead><tr><th></th><th class="r">Register</th>
          <th class="r">Docterz</th><th class="r">Bank</th><th></th></tr></thead>
          <tbody>%s%s</tbody></table></div>
        <p class="verdict %s">%s</p>%s
        <p class="mut">This screen states what the three records say. It does not decide who is
        right, and it never accuses anyone. Where two agree and one differs, that is the one to
        look at first.</p>
      </details>""" % (t["verdict"].replace(" ", "_"), _esc(t["verdict"] or "—"),
                       "".join(body), extra, t["verdict"].replace(" ", "_"), _esc(t["why"]), closer)
'''),
("E8 CSS: the folds, the label rows, the boxes at phone width",
 '''@media (max-width:620px){
 body{padding:10px;font-size:19px}
 .card{padding:12px}
 .grid th,.grid td{padding:8px 6px}
 .sec{width:30%%;font-size:17px}
 .entry input.amt{font-size:23px;min-height:58px}
 a.btn{display:block;text-align:center;margin:10px 0 0}
}
''',
 '''/* S254 phone layout: every head on its own row, three equal boxes beneath; the extras folded */
tr.head th{text-align:left;background:#eef2f5;font-size:18px;padding:8px 10px}
tr.boxes td{width:33.3%%;padding:6px 4px}
.entry input.amt{padding:8px 6px}
.entry thead th{font-size:16px;padding:6px}
details.card>summary{cursor:pointer;font-size:19px;font-weight:700;color:var(--accent);list-style-position:inside}
details.card[open]>summary{margin-bottom:10px}
@media (max-width:620px){
 body{padding:10px;font-size:19px}
 .card{padding:12px}
 .grid th,.grid td{padding:8px 6px}
 .sec{width:30%%;font-size:17px}
 tr.boxes td{padding:5px 3px}
 .entry input.amt{font-size:22px;min-height:56px;padding:6px 6px;letter-spacing:.3px}
 details.card>summary{font-size:18px}
 a.btn{display:block;text-align:center;margin:10px 0 0}
}
'''),
]

CM = [
("M1 version",
 '''APP_VERSION = "S253-CLINIC-MONEY-1.2-PLAIN-CARD"''',
 '''APP_VERSION = "S254-CLINIC-MONEY-1.3-SHEET-FOLDS"'''),
("M2 the other-UPI box folded; open when something is recorded today",
 '''    return """
      <div class="card" id="otherupi"><h2>ICICI UPI not working? &rarr; Paid to another UPI</h2>
''',
 '''    return """
      <details class="card" id="otherupi"%s><summary>ICICI UPI not working? &rarr; Paid to another UPI%s</summary>
'''),
("M3 ... its close and the two new values",
 '''        <button type="submit" class="save">%s</button>
        </form>
      </div>""" % (table, d, _esc(apps[0]) if apps else "",''',
 '''        <button type="submit" class="save">%s</button>
        </form>
      </details>""" % (" open" if rows else "", (" · &#8377; %s recorded" % _r(total)) if rows else "", table, d, _esc(apps[0]) if apps else "",'''),
("M4 the float box folded; the instruction rides on the fold; open only when short or change asked",
 '''    return """
      <div class="card" id="float"><h2>The float — reception ka chutta</h2>
        %s%s%s
''',
 '''    fold_open = " open" if (expand or (row is not None and (standing - row["kept_p"] > 0 or (row["need"] and not row["need_done"])))) else ""
    fold_line = "Float — alag rakho %s%s" % (words, (" · hand over &#8377; %s" % _r(hand)) if hand is not None and hand >= 0 else "")
    return """
      <details class="card" id="float"%s><summary>%s</summary>
        %s%s%s
'''),
("M5 ... its close and the two new values",
 '''        <p class="hint">Yeh ₹ %s din ki kamai ka hissa nahi hai — sirf chutta. Kuch nahi karna agar poora rakha.</p>
      </div>""" % (line, status, form, chg, _r(standing))''',
 '''        <p class="hint">Yeh ₹ %s din ki kamai ka hissa nahi hai — sirf chutta. Kuch nahi karna agar poora rakha.</p>
      </details>""" % (fold_open, fold_line, line, status, form, chg, _r(standing))'''),
]
EDITS = {"clinic_register.py": CR, "clinic_money.py": CM}


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_text(name, src):
    if MARKS[name] in src:
        return src, "already"
    for label, old, _new in EDITS[name]:
        n = src.count(old)
        if n != 1:
            return src, "refused: %s -- anchor matched %d times, expected exactly 1" % (label, n)
    new = src
    for _label, old, rep in EDITS[name]:
        new = new.replace(old, rep, 1)
    return new, "patched"


def build(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rc = 0
    for name in FROM:
        raw = io.open(os.path.join(src_dir, name), "rb").read()
        if md5(raw) != FROM[name]:
            print("REFUSED %s: source is %s, expected %s" % (name, md5(raw), FROM[name]))
            rc = 1
            continue
        new, st = patch_text(name, raw.decode("utf-8"))
        if st != "patched":
            print("REFUSED %s: %s" % (name, st))
            rc = 1
            continue
        b = new.encode("utf-8")
        io.open(os.path.join(out_dir, name), "wb").write(b)
        print("%-20s %s -> %s  (%d edits)" % (name, md5(raw)[:8], md5(b), len(EDITS[name])))
    return rc


def selftest(src_dir, kit_dir):
    rc = 0
    for name in FROM:
        raw = io.open(os.path.join(src_dir, name), "rb").read()
        new, st = patch_text(name, raw.decode("utf-8"))
        kit = io.open(os.path.join(kit_dir, name), "rb").read()
        again, st2 = patch_text(name, new)
        ok = md5(raw) == FROM[name] and st == "patched" and new.encode("utf-8") == kit and st2 == "already"
        print("%s %s: patch(live) == kit %s; second pass %s" % ("ok  " if ok else "FAIL", name, new.encode("utf-8") == kit, st2))
        rc |= (0 if ok else 1)
    print("selftest", "GREEN" if rc == 0 else "RED")
    return rc


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--build"] and len(a) == 3:
        sys.exit(build(a[1], a[2]))
    if a[:1] == ["--selftest"] and len(a) == 3:
        sys.exit(selftest(a[1], a[2]))
    print(__doc__)
    sys.exit(2)

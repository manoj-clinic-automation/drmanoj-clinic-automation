#!/usr/bin/env python3
"""make_s747.py -- S747_CALLS_REVIEW_CARDS (the parent, S400, 07-Nov-2026): builds the three TO files from their LIVE bytes
by counted edits, each anchor found exactly once (F-472: no anchor inferred -- every one was read in the live file).

usage: make_s747.py <calls_console.py> <aaj_kaam.html> <clinic_state_backup.py> <out_dir> [--expect]
  calls_console.py       40200409... (S745, live)        -> the review buttons, the staff card API, the reception credit
  aaj_kaam.html          9f8fb9df... (S493 lineage, live) -> 'Mere calls', each person's own card in Hindi
  clinic_state_backup.py 37ed5524... (S719, live)        -> one line: /root/portal/call_review.db in the encrypted nightly
--expect: refuse unless each FROM file hashes as above and each TO file hashes as TO_MD5 says (the installer's way)."""
import hashlib
import os
import sys

FROM_MD5 = {"calls_console.py": "4020040980d1557255b5c3b3527e3e6c",
            "aaj_kaam.html": "9f8fb9df13e66773f6645dda321dedcb",
            "clinic_state_backup.py": "37ed5524ca4dffa96a19346bf6d3a012"}
TO_MD5 = {}          # filled at the build (TO_MD5.txt beside this file) -- --expect reads it from there

HERE = os.path.dirname(os.path.abspath(__file__))


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("STOP: anchor %s found %d times (must be 1)" % (label, n))
    return text.replace(old, new, 1)


def span(text, start, end, new, label):
    """Replace from `start` (kept out) up to `end` (kept) -- both found exactly once."""
    if text.count(start) != 1 or text.count(end) != 1:
        sys.exit("STOP: span %s anchors found %d / %d times" % (label, text.count(start), text.count(end)))
    a, b = text.index(start), text.index(end)
    if b <= a:
        sys.exit("STOP: span %s ends before it starts" % label)
    return text[:a] + new + text[b:]


def blk(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    expect = "--expect" in sys.argv
    if len(a) != 4:
        sys.exit(__doc__)
    src = {"calls_console.py": a[0], "aaj_kaam.html": a[1], "clinic_state_backup.py": a[2]}
    out = a[3]
    os.makedirs(out, exist_ok=True)
    raw = {}
    for k, p in src.items():
        with open(p, "rb") as fh:
            raw[k] = fh.read()
        if md5(raw[k]) != FROM_MD5[k]:
            sys.exit("STOP: %s is %s, not the FROM %s" % (k, md5(raw[k])[:8], FROM_MD5[k][:8]))

    # ------------------------------------------------------------------ calls_console.py (11 counted edits)
    t = raw["calls_console.py"].decode("utf-8")
    t = edit(t, "Nothing here writes anything. The Staff performance section is the next kit.\n",
             "Nothing here writes anything. The Staff performance section is the next kit.\n" + blk("cc_doc.txt"), "E1 doc")
    t = edit(t, 'KIT = "S745_STAFF_CARDS_FIX"\nVERSION = "S745 1.0"\n', 'KIT = "S747_CALLS_REVIEW_CARDS"\nVERSION = "S747 1.0"\n', "E2 kit")
    t = edit(t, "import re\nimport sqlite3\n", "import re\nimport sqlite3\nimport sys\n", "E3 import sys")
    t = edit(t, 'OWNER_FIRST = ("manoj",)                             # S745: the owner\'s own agent is never a card\n',
             'OWNER_FIRST = ("manoj",)                             # S745: the owner\'s own agent is never a card\n' + blk("cc_store.txt"),
             "E4 store")
    t = span(t, "def staff_cards(people, d_from, d_to, now, master_path=None, punch_path=None, agents=None, phone_staff=None):\n",
             "\n\ndef _agent_firsts(conn, now=None):\n", blk("cc_cards.txt"), "E5 staff_cards")
    t = span(t, "def _safe_cards(conn, people, d_from, d_to, now, master_path, punch_path):\n",
             "\n\ndef _calls_min(conn, d_from, d_to):\n", blk("cc_safe.txt"), "E6 _safe_cards")
    t = edit(t, "@media (max-width:900px){.cols{grid-template-columns:minmax(0,1fr)}h2{flex-wrap:wrap}}\n",
             blk("cc_css.txt") + "@media (max-width:900px){.cols{grid-template-columns:minmax(0,1fr)}h2{flex-wrap:wrap}}\n", "E7 css")
    t = edit(t, '{% macro furow(r) %}', blk("cc_macro.txt") + '{% macro furow(r) %}', "E8 macro")
    t = span(t, '  <section id="staff">\n', "  {% set k = d.ckb %}\n", blk("cc_section.txt"), "E9 section")
    t = edit(t, "function toast(t){", blk("cc_js.txt") + "function toast(t){", "E10 js")
    t = edit(t, "    return render_template_string(PAGE, d=d, m=m, I=ICONS, words=item_words, vocab=REVIEW_VOCAB,\n",
             "    return render_template_string(PAGE, d=d, m=m, I=ICONS, words=item_words, vocab=REVIEW_VOCAB, rw=REVIEW_WORDS, figshort=FIG_SHORT, figw=FIG_WORDS,\n",
             "E11 render")
    t = edit(t, '        return jsonify({"ok": ok, "msg": msg}), code\n\n    return True\n',
             '        return jsonify({"ok": ok, "msg": msg}), code\n\n' + blk("cc_routes.txt") + "    return True\n", "E12 routes")
    new_cc = t.encode("utf-8")

    # ------------------------------------------------------------------ aaj_kaam.html (3 counted edits)
    h = raw["aaj_kaam.html"].decode("utf-8")
    h = edit(h, "[hidden]{display:none!important}\n</style></head>", "[hidden]{display:none!important}\n" + blk("ak_css.txt") + "</style></head>", "H1 css")
    h = edit(h, '<div id="list"></div>\n', '<div id="list"></div>\n<div id="calls"></div>\n', "H2 slot")
    h = edit(h, "</script>\n</body></html>", "</script>\n" + blk("ak_js.txt") + "</body></html>", "H3 js")
    new_ak = h.encode("utf-8")

    # ------------------------------------------------------------------ clinic_state_backup.py (1 counted edit)
    s = raw["clinic_state_backup.py"].decode("utf-8")
    s = edit(s, '    "/root/portal/gmb_store.db",\n]\n', '    "/root/portal/gmb_store.db",\n' + blk("sb_line.txt") + ']\n', "B1 line")
    new_sb = s.encode("utf-8")

    res = {"calls_console.py": new_cc, "aaj_kaam.html": new_ak, "clinic_state_backup.py": new_sb}
    want = {}
    if expect:
        with open(os.path.join(HERE, "TO_MD5.txt"), encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    h5, name = line.split()
                    want[name] = h5
    for k, b in res.items():
        if expect and want.get(k) != md5(b):
            sys.exit("STOP: the made %s is %s, not the TO %s" % (k, md5(b)[:8], (want.get(k) or "?")[:8]))
        with open(os.path.join(out, k), "wb") as fh:
            fh.write(b)
        print("made %s %s -> %s" % (k, FROM_MD5[k][:8], md5(b)[:8]))


if __name__ == "__main__":
    main()

#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s821.py -- kit S821 (session S453, the parent, 14-Nov-2026): exact, counted edits turning the live
/root/finance/pc_kits.py (9c2b3615) into the S821 file.
    python3 edits_s821.py LIVE OUT [KIT]   (exit 0 only if every anchor occurs once and, when KIT is given, OUT = KIT)

The owner's word, 14-Nov-2026 05:57 IST: the Medical PC's card must say how that PC is set up now, and that its kit
keeps itself current.  On https://followup.dr-manoj.in/finance/pcs :
  * an entry of PCS may carry `setup_now` {"noted", "items"}: its card then shows a block 'How this PC is set up now'
    -- below the 'Only a person can do these' list, above the 'Kit on the server' line -- and its small CSS (class
    .setnow, its own) goes into the page only then.  The Medical PC carries one: the cable and the Wi-Fi dongle, which
    USB port holds what, and to put them back the same way.
  * an entry may carry `kit_keeps`: one sentence after 'Kit on the server: <version>, packed <date>.' saying how that
    kit is kept current (pc_kits_current.py, S723, nightly on Dr Manoj's PC).  Medical and Reception carry one.
Every string is plain text through html.escape.  A PC without the keys renders exactly the bytes it rendered before.
Display only: no route, no door, no logic changed; nothing written.  Never a password, key, token or number.
"""
import hashlib
import sys

EDITS = [
    # 1 -- the module's own note
    ('''place on the page. No new door, nothing written, the same owner-only gate.
"""
''', '''place on the page. No new door, nothing written, the same owner-only gate.

S821 (14-Nov-2026): a PC's card can say how that PC is set up NOW, and how its kit is kept current -- the owner's word,
14-Nov-2026 05:57 IST: the Medical PC's card must say how that PC is set up now, and that its kit keeps itself current.
Two optional keys on an entry of PCS, both plain text and both escaped: `setup_now` (a dated list, shown below the 'Only
a person can do these' list) and `kit_keeps` (one sentence after 'Kit on the server: ...', saying what the nightly
pc_kits_current.py does for that kit). A PC without them renders exactly the bytes it did before. Display only: no new
door, nothing written, the same owner-only gate.
"""
'''),
    # 2 -- the comment above PCS names the two keys
    ('''# One entry per clinic PC. `health` is the key of the row /finance/health already computes for that machine.
''', '''# One entry per clinic PC. `health` is the key of the row /finance/health already computes for that machine.
# S821, both optional and both plain text (escaped on the page): `setup_now` {"noted": date words, "items": [lines]} is
# how that PC is physically set up today; `kit_keeps` is one sentence on how its kit is kept current. A kit that changes
# a PC's set-up changes these lines in the same kit.
'''),
    # 3 -- the Reception PC: how its kit is kept current
    ('''                          "type its password when it asks")]},
''', '''                          "type its password when it asks")],
     "kit_keeps": "Checked every night against this PC's recorded programs; a difference is reported. "
                  "This kit is not repacked by itself."},
'''),
    # 4 -- the Medical PC: how it is set up now, and how its kit is kept current
    ('''                ("user", "The staff account: double-click ENABLE_AGENT_THIS_ACCOUNT.bat once")]},
''', '''                ("user", "The staff account: double-click ENABLE_AGENT_THIS_ACCOUNT.bat once")],
     "setup_now": {"noted": "14-Nov-2026", "items": [
         "Network: the cable (Ethernet) and, since 13-Nov-2026, a Wi-Fi dongle beside it. Either one keeps this PC online.",
         "USB: the Wi-Fi dongle is in a FRONT USB port — the working one of the two front ports. "
         "The pen drive (the agent's backup stick) is in a REAR USB port.",
         "After a reinstall, a repair or a move: put the cable, the dongle and the pen drive back the same way."]},
     "kit_keeps": "Checked every night against the programs this PC actually runs; a changed program is repacked "
                  "into the kit by itself, or the night's report says why not. The new kit shows here after your "
                  "next publish and the next server line."},
'''),
    # 5 -- the block's own CSS (given to the page only when a card shows the block) and the block itself
    ('''a{color:#93c5fd}
"""
''', '''a{color:#93c5fd}
"""
# S821: the 'How this PC is set up now' block has its OWN class (.now belongs to setup_notes.py on this same page). This
# CSS is added to the page only when a card shows the block, so a page without one is the page it was.
_CSS_SETNOW = (".setnow{margin:12px 0 0;padding:10px 12px;border-radius:10px;background:#10293d;border:1px solid var(--line);"
               "font-size:12.5px;color:#c9d8e6}.setnow b{color:#fff}.setnow ul{margin:6px 0 0;padding-left:18px}"
               ".setnow li{margin:4px 0;overflow-wrap:anywhere}"
               ".setnow small{display:block;margin:6px 0 0;font-size:11.5px;color:var(--muted)}\\n")


def _setup_now_html(pc):
    """S821: the card's 'How this PC is set up now' block, or "" when the PC has no `setup_now`. Plain text only: every
    string goes through html.escape."""
    try:
        sn = pc.get("setup_now")
        if not sn:
            return ""
        items = [str(x) for x in sn["items"] if str(x).strip()]
        if not items:
            return ""
        return ("<div class=setnow><b>How this PC is set up now</b><ul>%s</ul><small>Noted %s.</small></div>"
                % ("".join("<li>%s</li>" % html.escape(x) for x in items), html.escape(str(sn["noted"]))))
    except Exception:                                          # noqa: BLE001 -- the page never dies of a note
        return ""
'''),
    # 6, 7 -- _page can be handed that extra CSS
    ('''def _page(title, body, refresh=False):
''', '''def _page(title, body, refresh=False, css=""):
'''),
    ('''html.escape(title), _CSS, body))''', '''html.escape(title), _CSS + css, body))'''),
    # 8 -- the page remembers whether any card showed the block
    ('''    planned = []
    for pc in PCS:
''', '''    planned = []
    now_css = ""                                               # S821: the block's CSS, only when a card shows the block
    for pc in PCS:
'''),
    # 9 -- the block is made once per card
    ('''        info = kit_info(pc["id"]) if pc["id"] in SETUPS else None
        if info:
''', '''        info = kit_info(pc["id"]) if pc["id"] in SETUPS else None
        setnow = _setup_now_html(pc)                           # S821: "" for a PC without `setup_now`
        if setnow:
            now_css = _CSS_SETNOW
        if info:
'''),
    # 10 -- with a kit: the block above the kit line, the kit_keeps sentence inside it before any ' Last: ...'
    ('''            last = _log_tail(pc["id"])
            card.append("<p class=kit>Kit on the server: %s, packed %s.%s</p>" % (
                html.escape(info["version"]), html.escape(info["packed"]),
''', '''            if setnow:
                card.append(setnow)
            last = _log_tail(pc["id"])
            card.append("<p class=kit>Kit on the server: %s, packed %s.%s%s</p>" % (
                html.escape(info["version"]), html.escape(info["packed"]),
                (" " + html.escape(str(pc["kit_keeps"]))) if pc.get("kit_keeps") else "",                # S821
'''),
    # 11 -- without a kit: the block still shows (how the PC is set up does not depend on its kit)
    ('''        else:
            card.append("<p class=kit>Its setup kit is not on the server yet — it is being packed and rehearsed. "
''', '''        else:
            if setnow:
                card.append(setnow)
            card.append("<p class=kit>Its setup kit is not on the server yet — it is being packed and rehearsed. "
'''),
    # 12 -- the page
    ('''    return _page("Clinic PCs & phones", "".join(out), refresh=True)
''', '''    return _page("Clinic PCs & phones", "".join(out), refresh=True, css=now_css)
'''),
]


def main():
    if len(sys.argv) < 3:
        print("  usage: python3 edits_s821.py LIVE OUT [KIT]")
        return 2
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    with open(live, encoding="utf-8", newline="") as fh:
        s = fh.read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1) -- nothing written" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    with open(out, "rb") as fh:
        a = hashlib.md5(fh.read()).hexdigest()
    print("  %d edits applied, rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        with open(kit, "rb") as fh:
            b = hashlib.md5(fh.read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""make_s527.py -- kit S527_SETUP_CARDS: builds /root/finance/setup_notes.py from its pinned FROM bytes by exact,
counted edits (every anchor exactly once), in memory first; nothing is written unless every edit applies.
The five cards' text is cards_block.txt beside this file, inserted whole.
  python3 make_s527.py <dir with setup_notes.py> <out dir>"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = "61348f425820d28f3e2a53435ca64acd"


def edits():
    block = open(os.path.join(HERE, "cards_block.txt"), encoding="utf-8").read()
    return [
        ("E1 the header names S527",
         '"""setup_notes.py -- kit S492_SETUP_NOTES (session 298, 07-Oct-2026). PARENT.',
         '"""setup_notes.py -- kit S492_SETUP_NOTES (session 298, 07-Oct-2026). PARENT. S527 (session 305, 11-Oct-2026):\n'
         'the five set-up cards that were "to be built" -- Hostinger, CyberPanel, the SSH login, the websites, Bitwarden --\n'
         'are built (CARDS, below the biometric machine), from the server\'s own files and the records; see CARDS\' note.'),
        ("E2 the to-be-built list becomes the five cards",
         "# ---------------------------------------------------------------------------------------------------------------------\n"
         "# asked for by the owner, not built yet -- one line each on what the card will hold (each line is trusted HTML of this file)\n"
         "# ---------------------------------------------------------------------------------------------------------------------\n"
         "TO_BUILD = [\n"
         "    (\"Hostinger \\u2014 the server\", \"The plan and its renewal date, where to sign in, and what to do if the server is down.\"),\n"
         "    (\"CyberPanel\", \"The websites' control panel on the server: its link and what it is used for.\"),\n"
         "    (\"SSH login\", \"How your PC reaches the server, where its key is kept, and what to do on a new PC.\"),\n"
         "    (\"Websites\", \"<span class=nw>drmanojagarwal.com</span>, the clinic's internal pages on <span class=nw>dr-manoj.in</span> and \"\n"
         "                 \"<span class=nw>nkpathology.com</span>: where each is hosted, how each is changed, and the domain renewals.\"),\n"
         "    (\"Bitwarden\", \"Every login kept in one place, brought in by stages, so that nothing lives only in memory.\"),\n"
         "]\n",
         block),
        ("E3 a card's HTML",
         "def section(now_ts=None):\n",
         "def card_html(c):\n"
         "    \"\"\"S527: one set-up card. Every string is this file's own trusted text; titles and gaps are escaped.\"\"\"\n"
         "    out = [\"<div class=pc><div class=row><div class=pcn>%s</div><span class='st info'>%s</span></div><p class=what>%s</p>\"\n"
         "           % (html.escape(c[\"label\"]), html.escape(c[\"chip\"]), c[\"what\"])]\n"
         "    for title, items in c[\"blocks\"]:\n"
         "        out.append(\"<details class=sn><summary>%s</summary><ul>%s</ul></details>\"\n"
         "                   % (html.escape(title), \"\".join(\"<li>%s</li>\" % i for i in items)))\n"
         "    if c.get(\"steps\"):\n"
         "        title, items = c[\"steps\"]\n"
         "        out.append(\"<details class=sn><summary>%s</summary><ol>%s</ol></details>\"\n"
         "                   % (html.escape(title), \"\".join(\"<li>%s</li>\" % i for i in items)))\n"
         "    if c.get(\"gaps\"):\n"
         "        out.append(\"<div class=todo><b>Not written down yet:</b><ul>%s</ul></div>\"\n"
         "                   % \"\".join(\"<li>%s</li>\" % html.escape(g) for g in c[\"gaps\"]))\n"
         "    out.append(\"</div>\")\n"
         "    return \"\".join(out)\n"
         "\n"
         "\n"
         "def section(now_ts=None):\n"),
        ("E4 the cards on the page; the to-be-built part only while it has rows",
         "    out.append(\"<div class=pc><div class=pcn>To be built</div><p class=what>Asked for and on the list. Each gets a card \"\n",
         "    out.extend(card_html(c) for c in CARDS)                       # S527: the five set-up cards\n"
         "    if TO_BUILD:\n"
         "      out.append(\"<div class=pc><div class=pcn>To be built</div><p class=what>Asked for and on the list. Each gets a card \"\n"),
    ]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, out):
    b = open(os.path.join(src, "setup_notes.py"), "rb").read()
    if md5(b) != FROM:
        raise SystemExit("REFUSED: setup_notes.py is %s, not the FROM pin %s" % (md5(b), FROM))
    t = b.decode("utf-8")
    for label, old, new in edits():
        n = t.count(old)
        if n != 1:
            raise SystemExit("REFUSED: %s: the anchor occurs %d times" % (label, n))
        t = t.replace(old, new)
    nb = t.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "setup_notes.py"), "wb") as fh:
        fh.write(nb)
    print("setup_notes.py  4 edits  %s -> %s" % (FROM[:8], md5(nb)[:8]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])

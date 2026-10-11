#!/usr/bin/env python3
"""walk_s527.py -- kit S527_SETUP_CARDS, walked before anything is placed. Read-only.
The old and the new setup_notes.py each render the 'Other set-ups' section, with this box's own punch file and staff list
(the module's two live reads) at one fixed moment: the biometric card is byte for byte the same; after it come the five
new cards, each well formed, every link on this site or https, no 'To be built' part left; nothing that looks like a
secret, a login file or a PC path to one is in the new text; and the page the finance app builds (pc_kits.py) still
imports it and carries the five cards.
  walk_s527.py <kit dir> [--live /root/finance/setup_notes.py]"""
import argparse, html.parser, importlib.util, os, re, sys, time

N = [0]


def check(name, ok, detail=""):
    if not ok:
        print("FAIL %d: %s %s" % (N[0] + 1, name, detail)); sys.exit(1)
    N[0] += 1


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


class Tags(html.parser.HTMLParser):
    VOID = {"br", "img", "input", "meta", "link", "hr"}

    def __init__(self):
        super().__init__(); self.stack = []; self.bad = []; self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs).get("href", ""))
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.bad.append((tag, list(self.stack[-3:])))
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("kit"); ap.add_argument("--live", default="/root/finance/setup_notes.py")
    a = ap.parse_args()
    old = load(a.live, "sn_old"); new = load(os.path.join(a.kit, "setup_notes.py"), "sn_new")
    now = time.time()
    ho, hn = old.section(now), new.section(now)
    cut = ho.find("<div class=pc><div class=pcn>To be built</div>")
    check("the old section has its 'To be built' part", cut > 0)
    check("everything before it -- the biometric card and its two live reads -- is byte for byte the same", hn[:cut] == ho[:cut])
    rest = hn[cut:]
    check("no 'To be built' part is left", "To be built" not in hn)
    check("five cards follow, in order", [m for m in re.findall(r"<div class=pcn>([^<]+)</div><span class='st info'>", rest)]
          == ["Hostinger \u2014 the server", "CyberPanel", "SSH login", "Websites", "Bitwarden"])
    p = Tags(); p.feed(hn); p.close()
    check("the whole section's HTML is well formed (every tag closed in order)", not p.bad and not p.stack, str(p.bad[:3]) + str(p.stack[-3:]))
    check("every link is on this site or https", all(h.startswith("/") or h.startswith("https://") for h in p.hrefs), str(p.hrefs))
    check("the new cards carry links (hPanel, CyberPanel, the sites)", sum(1 for h in p.hrefs if h.startswith("https://")) >= 8)
    low = rest.lower()
    for bad in ("password:", "passwd", "pwd=", "token=", "secret=", "begin openssh", "private key-----", "\\credentials",
                "credentials\\", ".ppk", "id_ed25519", "c:\\users\\", "@gmail.com", "apple notes:"):
        check("no '%s' in the new cards" % bad, bad not in low)
    check("no long run of digits that could be a number or a code", not re.search(r"\d{8,}", re.sub(r"<[^>]+>", " ", rest)))
    for c in new.CARDS:
        check("%s: every block has lines" % c["label"], c["blocks"] and all(items for _t, items in c["blocks"]))
    check("the module's two live reads are unchanged", new.last_punch.__code__.co_code == old.last_punch.__code__.co_code
          and new.staff_codes.__code__.co_code == old.staff_codes.__code__.co_code)
    pk = os.path.join(os.path.dirname(a.live), "pc_kits.py")
    if os.path.isfile(pk):
        src = open(pk, encoding="utf-8").read()
        check("pc_kits.py imports setup_notes and calls section() under its guard",
              "import setup_notes as _setup_notes" in src and "_setup_notes.section()" in src)
    print("   %d characters of new cards; %d links; the biometric card unchanged" % (len(rest), len(p.hrefs)))
    print("WALK OK -- %d checks" % N[0])


if __name__ == "__main__":
    main()

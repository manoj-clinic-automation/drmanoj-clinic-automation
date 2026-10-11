#!/usr/bin/env python3
"""walk_s529.py -- kit S529_SAVE_CARD_AND_SEND_SAYS, walked on the box before anything is placed. Read-only.
  packs.html     the kit's file renders as a Jinja template exactly where the live one does (the same values), carries the
                 send button's name and answer line, and differs from the live file only in the three edits.
  setup_notes.py the section renders; everything but the Websites card's save lines is byte for byte the live one's.
  save/index.php holds no number and no secret; reads its card from clinic.vcf beside it.
  walk_s529.py <kit dir> [--fin /root/finance]"""
import argparse, importlib.util, os, re, sys

N = [0]


def check(name, ok, detail=""):
    if not ok:
        print("FAIL %d: %s %s" % (N[0] + 1, name, detail)); sys.exit(1)
    N[0] += 1


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("kit"); ap.add_argument("--fin", default="/root/finance")
    a = ap.parse_args()
    lp = open(os.path.join(a.fin, "packs.html"), encoding="utf-8").read()
    kp = open(os.path.join(a.kit, "packs.html"), encoding="utf-8").read()
    try:
        import jinja2
        env = jinja2.Environment()
        vals = {"month": "2026-09"}
        rl, rk = env.from_string(lp).render(**vals), env.from_string(kp).render(**vals)
        check("both packs pages render as templates", bool(rl) and bool(rk))
        check("the kit's page renders the button's name and its answer line",
              'id="sendbtn"' in rk and 'id="sendres"' in rk and "function sendPack()" in rk and "Sending" in rk)
    except ImportError:
        print("   (jinja2 not importable here -- template render not walked; the text checks below still run)")
    check("the live page carries the three anchors the kit changed", lp.count('onclick="sendPack()"') == 1 and lp.count("function sendPack()") == 1)
    strip = lambda t: re.sub(r"function sendRes.*?\n|function sendPack\(\)\{.*?\n|// S529.*?\n|// cannot be pressed twice.*?\n|    \$\(\"sendbtn\"\).*?\n", "", t)
    check("outside the send button the two pages are identical",
          strip(kp).replace(' id="sendbtn"', "").replace('<div id="sendres" style="margin-top:8px"></div>', "") == strip(lp))
    check("the kit's page asks before a second send", "already sent. Send it AGAIN" in kp)

    old = load(os.path.join(a.fin, "setup_notes.py"), "sn_old"); new = load(os.path.join(a.kit, "setup_notes.py"), "sn_new")
    ho, hn = old.section(0), new.section(0)
    cut = ho.find("<div class=pc><div class=row><div class=pcn>Websites")
    check("the live notes carry the Websites card", cut > 0)
    check("everything before the Websites card is byte for byte the same", hn[:cut] == ho[:cut])
    tail_o = ho[ho.find("<div class=pc><div class=row><div class=pcn>Bitwarden"):]
    tail_n = hn[hn.find("<div class=pc><div class=row><div class=pcn>Bitwarden"):]
    check("the Bitwarden card after it is byte for byte the same", tail_o == tail_n and tail_n)
    check("the Websites card names the save page and no longer says the link is broken",
          "drmanojagarwal.com/save/" in hn and "did not open on 11-Oct" not in hn)

    php = open(os.path.join(a.kit, "save", "index.php"), encoding="utf-8").read()
    body = re.sub(r"/\*.*?\*/", "", php, flags=re.S)
    check("the save page holds no number", not re.search(r"\d{6,}", body))
    check("the save page reads its card from clinic.vcf beside it and falls back to the contact page",
          "__DIR__ . '/clinic.vcf'" in php and "https://contact.dr-manoj.in" in php)
    check("the save page escapes what it prints", php.count("$h(") >= 5)
    check("Android gets the phone's own new-contact form; iPhone gets the card", "android.intent.action.INSERT" in php and "?card=1" in php)
    print("WALK OK -- %d checks" % N[0])


if __name__ == "__main__":
    main()

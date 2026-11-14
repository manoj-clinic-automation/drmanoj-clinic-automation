#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s821.py -- kit S821 (session S453, the parent, 14-Nov-2026): the proof for the Clinic PCs page's two new notes.

    python3 -B walk_s821.py --code DIR --old DIR --scratch DIR [--control]

--code DIR   the folder holding the pc_kits.py under test (the kit's folder)
--old DIR    the folder holding the pc_kits.py it replaces, and that page's setup_notes.py beside it
--scratch    a folder this walk may write in; it makes one sub-folder there and removes it at the end

Everything is made up: a made-up PC_KITS_ROOT (a KIT_INFO.txt and a tiny zip for reception / medical / manojz, so the
three cards have kits), made-up health rows, a `require` that returns the owner, made-up files for the notes module.
Nothing of the live system is read except the two code files named above; nothing outside --scratch is written.

  (a) the NEW page shows 'How this PC is set up now', its three lines and 'Noted 14-Nov-2026.' on the Medical card only
  (b) each kit_keeps sentence is on the right card, and none on Dr Manoj's PC
  (c) with the two new keys taken off the NEW module's PCS at run time, the page is the OLD page byte for byte
  (d) every string is escaped
  (e) the routes and their methods are the same; the gate and the POST doors answer as before
  (f) the 'Other set-ups' section is the same byte for byte
  (g) THE CONTROL: with --code = --old, the checks of (a), (b) and (d) go RED.

Plain run: PASS/FAIL per check, a total, exit 0 only when nothing failed (last line 'WALK S821 GREEN ...').
--control: exit 0 only when exactly the checks that must tell old from new are red and every other one is green
(last line 'CONTROL S821 RED as it must be ...'). Exit 2 = the walk itself could not run.
"""
import argparse
import hashlib
import html
import importlib.util
import io
import os
import re
import shutil
import sys
import warnings
import zipfile

sys.dont_write_bytecode = True
warnings.simplefilter("ignore")

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--old", required=True)
ap.add_argument("--scratch", required=True)
ap.add_argument("--control", action="store_true")
A = ap.parse_args()
CODE_PY = os.path.join(os.path.abspath(A.code), "pc_kits.py")
OLD_DIR = os.path.abspath(A.old)
OLD_PY = os.path.join(OLD_DIR, "pc_kits.py")
for p in (CODE_PY, OLD_PY):
    if not os.path.isfile(p):
        print("WALK S821 COULD NOT RUN: %s is not there" % p)
        sys.exit(2)
try:
    from flask import Flask
except Exception as ex:                                        # noqa: BLE001
    print("WALK S821 COULD NOT RUN: this python has no Flask (%s)" % str(ex)[:80])
    sys.exit(2)

# the owner's words, exactly as the kit was asked to show them -------------------------------------------------------
TITLE = "How this PC is set up now"
NOTED = "14-Nov-2026"
ITEMS = [
    "Network: the cable (Ethernet) and, since 13-Nov-2026, a Wi-Fi dongle beside it. Either one keeps this PC online.",
    "USB: the Wi-Fi dongle is in a FRONT USB port — the working one of the two front ports. The pen drive (the agent's "
    "backup stick) is in a REAR USB port.",
    "After a reinstall, a repair or a move: put the cable, the dongle and the pen drive back the same way.",
]
KEEPS_MED = ("Checked every night against the programs this PC actually runs; a changed program is repacked into the kit "
             "by itself, or the night's report says why not. The new kit shows here after your next publish and the next "
             "server line.")
KEEPS_REC = ("Checked every night against this PC's recorded programs; a difference is reported. This kit is "
             "not repacked by itself.")
L_REC, L_MED, L_MAN = "Reception PC", "Medical PC (Sanjeevni)", "Dr Manoj’s PC"
NEW_KEYS = ("setup_now", "kit_keeps")

results = []          # (id, ok, must_be_red_on_the_old_file, label)


def check(cid, ok, label, tells=False):
    results.append((cid, bool(ok), tells, label))
    print(("  ok   " if ok else "  FAIL ") + "[%s] %s" % (cid, label))
    return ok


# the made-up root ---------------------------------------------------------------------------------------------------
os.makedirs(A.scratch, exist_ok=True)
T = os.path.join(os.path.abspath(A.scratch), "walk_s821_%d" % os.getpid())
shutil.rmtree(T, ignore_errors=True)
os.makedirs(T)


def md5b(b):
    return hashlib.md5(b).hexdigest()


def tiny_zip(name, text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo(name, (2099, 1, 1, 0, 0, 0)), text)
    return buf.getvalue()


def make_root(root, pcs):
    os.makedirs(os.path.join(root, "_shared"))
    py = tiny_zip("pyportable/README.txt", "walk: not a real Python")
    with open(os.path.join(root, "_shared", "pyportable_walk.zip"), "wb") as fh:
        fh.write(py)
    for pc in pcs:
        os.makedirs(os.path.join(root, pc))
        kit = tiny_zip("README.txt", "walk: a made-up kit for %s" % pc)
        with open(os.path.join(root, pc, "kit.zip"), "wb") as fh:
            fh.write(kit)
        with open(os.path.join(root, pc, "KIT_INFO.txt"), "w", encoding="utf-8") as fh:
            fh.write("# made up by walk_s821.py\nversion=WALK-%s-v1\npacked=01-Jan-2099\nkit_md5=%s\n"
                     "python_file=pyportable_walk.zip\npython_md5=%s\n" % (pc, md5b(kit), md5b(py)))


ROOT3 = os.path.join(T, "PC_KITS")                 # reception, medical and manojz all have a kit
ROOT2 = os.path.join(T, "PC_KITS_no_medical")      # the Medical PC's kit is not on the server
make_root(ROOT3, ["reception", "medical", "manojz"])
make_root(ROOT2, ["reception", "manojz"])
os.makedirs(os.path.join(T, "phones"))
with open(os.path.join(T, "staff_master.csv"), "w") as fh:
    fh.write("user_id,name\n9001,Walk Staff\n")
with open(os.path.join(T, "punches.csv"), "w") as fh:
    fh.write("x\n")
os.environ.update({
    "PC_KITS_ROOT": ROOT3, "PHONE_KITS_ROOT": os.path.join(T, "phones"),
    "PC_KIT_CODES": os.path.join(T, "pc_kit_codes.json"), "PC_KIT_LOG": os.path.join(T, "pc_kit_log.txt"),
    "PC_KIT_SERVER_URL": "https://walk.invalid",
    # the notes module ('Other set-ups'): made-up or absent files only, so it says the same thing at every render
    "ATT_PUNCH_CSV": os.path.join(T, "punches.csv"), "ATT_STAFF_MASTER": os.path.join(T, "staff_master.csv"),
    "FRESHNESS_STATE_FILE": os.path.join(T, "no-such-freshness.json"), "CERTWATCH_LOG_FILE": os.path.join(T, "no-such-cert.log"),
    "SETUP_NOTES_ROOT_FS": os.path.join(T, "no-such-folder"), "SETUP_NOTES_PROC_UPTIME": os.path.join(T, "no-such-uptime"),
})

# the notes module, the one both pages import -- from beside the OLD file, with the clock held still
sys.path.insert(0, OLD_DIR)
SN = None
try:
    import setup_notes as SN                                   # noqa: E402
    _section = SN.section
    FIXED = 4070910600.0                                       # one fixed moment (01-Jan-2099), so the notes never differ by the clock
    SN.section = lambda now_ts=None: _section(FIXED)
except Exception as ex:                                        # noqa: BLE001
    print("  note: setup_notes.py beside the old file did not load (%s)" % str(ex)[:100])
    SN = None

GATE = {"open": True}
HEALTH = {"checks": [
    {"key": "reception", "state": "ok", "detail": "walk: the reception PC reported 2 minutes ago"},
    {"key": "watcher", "state": "warn", "detail": "walk: the medical PC's last export is 5 hours old"},
    {"key": "pipeline", "state": "ok", "detail": "walk: the nightly ran"},
]}


def fake_require(_role):
    return ({"user": "walk-owner"}, None) if GATE["open"] else (None, "not permitted")


def load(path, tag):
    s = importlib.util.spec_from_file_location("pc_kits_walk_" + tag, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    app = Flask("walk_" + tag)
    m.init(app, lambda: None, fake_require, lambda _db: HEALTH)
    return m, app, app.test_client()


def page(c):
    r = c.get("/finance/pcs")
    return r.status_code, r.get_data(as_text=True)


def card(pg, label):
    s = pg.find("<div class=pc><div class=row><div class=pcn>%s</div>" % html.escape(label))
    if s < 0:
        return ""
    ends = [e for e in (pg.find("<div class=pc>", s + 10), pg.find("<h1 style=", s + 10)) if e >= 0]
    return pg[s:min(ends)] if ends else pg[s:]


def routes(app):
    return sorted((r.rule, tuple(sorted(r.methods - {"HEAD", "OPTIONS"})), r.endpoint.split(".")[-1])
                  for r in app.url_map.iter_rules() if r.endpoint != "static")


def strip_keys(m):
    for p in m.PCS:
        for k in NEW_KEYS:
            p.pop(k, None)


try:
    O, Oapp, Oc = load(OLD_PY, "old")
    N, Napp, Nc = load(CODE_PY, "new")
    S, Sapp, Sc = load(CODE_PY, "stripped")
    strip_keys(S)
    X, Xapp, Xc = load(CODE_PY, "inject")
    e = html.escape

    so, po = page(Oc)
    sn, pn = page(Nc)
    ss, ps = page(Sc)
    med, rec, man = card(pn, L_MED), card(pn, L_REC), card(pn, L_MAN)
    _b = re.search(r"<div class=setnow>.*?</div>", med, re.S)
    block = _b.group(0) if _b else ""
    check("0", so == sn == ss == 200 and all(card(po, x) and card(pn, x) for x in (L_REC, L_MED, L_MAN))
          and po.count("Kit on the server:") == 3,
          "both pages open for the owner, with the three PC cards and a kit on each")

    # (a) the block, on the Medical card only
    check("a1", pn.count("<b>%s</b>" % TITLE) == 1 and ("<b>%s</b>" % TITLE) in block,
          "the Medical card is titled '%s', once on the page" % TITLE, tells=True)
    check("a2", block.count("<li>") == 3 and "<ul>%s</ul>" % "".join("<li>%s</li>" % e(x) for x in ITEMS) in block,
          "its three lines, word for word and in order (the cable and the dongle; the USB ports; put them back the same way)", tells=True)
    check("a3", block.endswith("<small>Noted %s.</small></div>" % NOTED), "its last small line says 'Noted %s.'" % NOTED, tells=True)
    i_todo, i_blk, i_kit = med.find("A tick is what this PC itself last reported.</div>"), med.find("<div class=setnow>"), med.find("<p class=kit>Kit on the server:")
    check("a4", 0 <= i_todo < i_blk < i_kit, "it sits below the 'Only a person can do these' list and above the 'Kit on the server' line", tells=True)
    check("a5", pn.count("<div class=setnow>") == 1 and "setnow" not in rec and "setnow" not in man
          and pn.count(".setnow{") == 1 and pn.find(".setnow{") < pn.find("</style>") and "class=now" not in med,
          "one block on the whole page -- none on Reception or Dr Manoj's PC -- with its own class in the page's style", tells=True)

    # (b) how each kit is kept current
    check("b1", "<p class=kit>Kit on the server: WALK-medical-v1, packed 01-Jan-2099. %s</p>" % e(KEEPS_MED) in med and pn.count(e(KEEPS_MED)) == 1,
          "the Medical card: '... a changed program is repacked by itself, or the report says why not; shows here after the next publish and server line', right after the kit line", tells=True)
    check("b2", "<p class=kit>Kit on the server: WALK-reception-v1, packed 01-Jan-2099. %s</p>" % e(KEEPS_REC) in rec and pn.count(e(KEEPS_REC)) == 1,
          "the Reception card: '... a difference is reported. This kit is not repacked by itself'", tells=True)
    check("b3", pn.count("Checked every night") == 2 and "Checked every night" not in man
          and "<p class=kit>Kit on the server: WALK-manojz-v1, packed 01-Jan-2099.</p>" in man,
          "two such sentences on the page and none on Dr Manoj's PC, whose kit line is as it was", tells=True)

    # (c) without the two keys, the old page
    check("c1", ps == po, "with the two new keys taken off at run time, the page is the old page byte for byte (%d bytes)" % len(po.encode("utf-8")))
    check("c2", card(pn, L_MAN) == card(po, L_MAN) and pn[pn.find("<h1 style="):] == po[po.find("<h1 style="):]
          and pn[:pn.find("<style>")] == po[:po.find("<style>")],
          "on the full new page, Dr Manoj's PC card (no keys) and everything from the phones down are the old bytes")

    # (e) the doors -- pressed on every copy, so the shared trail then gives each page the same ' Last: ...' words
    check("e1", routes(Oapp) == routes(Napp) and len(routes(Napp)) == 5,
          "the routes and their methods are the same, old and new (%d)" % len(routes(Napp)))
    r_o, r_n = Oc.post("/finance/pcs/setup/shavez"), Nc.post("/finance/pcs/setup/shavez")
    check("e2", r_o.status_code == r_n.status_code == 404 and r_o.get_data() == r_n.get_data() and b"No kit" in r_n.get_data(),
          "the setup button for a PC without a kit answers 404 'No kit', the same bytes old and new")
    f_o, f_n = Oc.post("/finance/pcs/setup/medical"), Nc.post("/finance/pcs/setup/medical")
    mask = lambda b: re.sub(rb'set "CODE=[A-Za-z0-9_-]+"', b'set "CODE=*"', b)
    info = N.kit_info("medical")
    check("e3", f_o.status_code == f_n.status_code == 200 and mask(f_o.get_data()) == mask(f_n.get_data())
          and f_n.headers.get("Content-Disposition") == f_o.headers.get("Content-Disposition") == 'attachment; filename="ClinicSetup_Medical.cmd"'
          and O.setup_file("medical", "C" * 32, info) == N.setup_file("medical", "C" * 32, info)
          and b"dongle" not in f_n.get_data() and b"Checked every night" not in f_n.get_data(),
          "the Medical PC's setup file is the same file (its one-time code apart); the new words are not in it")
    x_o = Oc.post("/finance/pcs/setup/medical", headers={"Sec-Fetch-Site": "cross-site"})
    x_n = Nc.post("/finance/pcs/setup/medical", headers={"Sec-Fetch-Site": "cross-site"})
    check("e4", x_o.status_code == x_n.status_code == 403 and x_o.get_data() == x_n.get_data(),
          "a press from another site is refused 403, the same bytes old and new")
    GATE["open"] = False
    g_o, g_n = Oc.get("/finance/pcs"), Nc.get("/finance/pcs")
    GATE["open"] = True
    check("e5", g_o.status_code == g_n.status_code == 403 and g_o.get_data() == g_n.get_data() and b"setnow" not in g_n.get_data(),
          "anyone but the owner gets 'Not permitted' (403), the same bytes old and new")

    # (b) and (c) again, now that the trail has lines
    _, po2 = page(Oc)
    _, pn2 = page(Nc)
    _, ps2 = page(Sc)
    med2 = card(pn2, L_MED)
    check("b4", "packed 01-Jan-2099. %s Last: " % e(KEEPS_MED) in med2 and " Last: " in card(po2, L_MED),
          "with a trail, the sentence comes before the ' Last: ...' words", tells=True)
    check("c3", ps2 == po2 and po2 != po, "with a trail (' Last: ...'), the page without the keys is still the old page byte for byte")

    # the Medical PC's kit not on the server: the note does not depend on the kit
    for m in (O, N, S):
        m.KIT_ROOT = ROOT2
    _, po3 = page(Oc)
    _, pn3 = page(Nc)
    _, ps3 = page(Sc)
    for m in (O, N, S):
        m.KIT_ROOT = ROOT3
    med3 = card(pn3, L_MED)
    check("a6", 0 <= med3.find("<div class=setnow>") < med3.find("<p class=kit>Its setup kit is not on the server yet")
          and "Checked every night" not in med3 and "<form" not in med3,
          "with the Medical PC's kit not on the server: the block still shows, above 'not on the server yet'; no kit sentence, no button", tells=True)
    check("c4", ps3 == po3 and "Its setup kit is not on the server yet" in card(po3, L_MED),
          "... and without the keys that page too is the old page byte for byte")

    # (d) escaping, and a note that is not in shape
    xm = X.PC_BY_ID["medical"]
    xm["setup_now"] = {"noted": "<i>d</i>", "items": list(ITEMS) + ["<b>x</b> & \"more\""]}
    X.PC_BY_ID["manojz"]["kit_keeps"] = "<u>k</u>"
    sx, px = page(Xc)
    check("d1", sx == 200 and "<li>&lt;b&gt;x&lt;/b&gt; &amp; &quot;more&quot;</li>" in px and "<b>x</b>" not in px
          and "Noted &lt;i&gt;d&lt;/i&gt;." in px and "<i>d</i>" not in px
          and "packed 01-Jan-2099. &lt;u&gt;k&lt;/u&gt;" in card(px, L_MAN) and "<u>k</u>" not in px,
          "a line, a date and a kit sentence holding <b>, <i>, <u>, & and quotes are shown as text, never as markup", tells=True)
    xm["setup_now"] = "not in shape"
    X.PC_BY_ID["manojz"].pop("kit_keeps")
    sx2, px2 = page(Xc)
    xm["setup_now"] = {"noted": NOTED, "items": []}
    sx3, px3 = page(Xc)
    check("d2", sx2 == sx3 == 200 and "setnow" not in px2 and "setnow" not in px3 and card(px2, L_MAN) == card(po2, L_MAN),
          "a note that is not in shape, or has no lines, shows no block and the page still opens")

    # (f) the 'Other set-ups' section
    def other(pg):
        h = pg.find("<h1 style='margin-top:18px'>Other set-ups</h1>")
        return pg[pg.rfind("<style>", 0, h):pg.find("<p class=how>")] if h >= 0 else ""
    check("f1", SN is not None and len(other(po)) > 500 and other(po) == other(pn) == other(pn2) == SN.section(),
          "the 'Other set-ups' section is on both pages and is the same byte for byte (%d bytes)" % len(other(po).encode("utf-8")))
    added = block + " ".join(str(N.PC_BY_ID[k].get("kit_keeps", "")) for k in ("reception", "medical", "manojz"))
    check("f2", not re.search(r"\d{5,}|(?i:password|passwd|token|secret)\s*[:=]", added),
          "the new words hold no number-, password- or token-shaped text")
finally:
    shutil.rmtree(T, ignore_errors=True)

red = [r for r in results if not r[1]]
print("")
if A.control:
    wrong = [r[0] for r in results if r[1] == r[2]]            # a telling check that passed, or another that failed
    if not wrong and red:
        print("CONTROL S821 RED as it must be: %d checks red on the old file (%s), the other %d green"
              % (len(red), " ".join(r[0] for r in red), len(results) - len(red)))
        sys.exit(0)
    print("CONTROL S821 WRONG: these checks did not behave as they must on the old file: %s" % (" ".join(wrong) or "none red"))
    sys.exit(1)
print(("WALK S821 GREEN" if not red else "WALK S821 RED") + ": %d passed, %d failed, of %d" % (len(results) - len(red), len(red), len(results)))
sys.exit(0 if not red else 1)

#!/usr/bin/python3
# make_s793.py -- kit S793_WA_OPEN_IN_MYOP (S431, 11-Nov-2026, the parent; the owner 17:46 IST: an interim while the clinic's own
# WhatsApp sends fail -- F-1031, MyOperator ticket 691386). Each chat in his WhatsApp inbox (/portal/inbox) gets an
# "Open in MyOperator" button in its header: it opens that patient's chat in MyOperator's panel in a new tab, so he replies there.
# The panel's own address for a chat by number, read from its app at S431: /chat/<the clinic number's id>/91/<10 digits>;
# the clinic number's id is that of the LIVE account (Dr. Manoj Agrawal Clinic) on https://in.app.myoperator.com/whatsapp.
# Usage: make_s793.py <live portal_inbox.py> <out dir>. Exact replacements on portal_inbox.py f89ad282 (S701); nothing else changes.
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("f89ad282"), "not the live portal_inbox.py (f89ad282)"
C = b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:80]
    return t.replace(a, b)
# 1. the health answer names this kit (the installer's proof the new file is the one running)
C = rp(C, 'return jsonify({"inbox": "ok", "kit": "S701"})', 'return jsonify({"inbox": "ok", "kit": "S793"})')
# 2. the button's look: white outline on the green header; on a narrow phone the word hides and the icon stays
C = rp(C, ".callbtn{height:44px;",
       ".myopbtn{height:44px;border:1px solid #CFE5DF;border-radius:22px;background:transparent;color:#fff;font-weight:600;font-size:15px;"
       "padding:0 14px;display:flex;align-items:center;gap:8px;text-decoration:none;flex-shrink:0;white-space:nowrap}\n"
       ".myopbtn:focus-visible,.callbtn:focus-visible{outline:2px solid #fff;outline-offset:2px}\n"
       "@media (max-width:440px){.myopbtn .lbl{display:none}.myopbtn{padding:0 11px}}\n"
       ".callbtn{height:44px;")
# 3. the icon (a box with an arrow leaving it)
C = rp(C, "var IC={back:'<path d=\"M15 18l-6-6 6-6\"></path>',",
       "var IC={ext:'<path d=\"M14 3h7v7\"></path><path d=\"M10 14L21 3\"></path><path d=\"M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5\"></path>',"
       "back:'<path d=\"M15 18l-6-6 6-6\"></path>',")
# 4. the address of a patient's chat in MyOperator (the last 10 digits; nothing when the number is shorter)
C = rp(C, "function fmtNum(p){",
       "var MYOP_CHAT=\"https://in.app.myoperator.com/chat/dfb2da39-0d45-4383-ad58-d63f29c09920/91/\";   // S793: the clinic number's chat page in MyOperator\n"
       "function myopUrl(p){var d=String(p==null?\"\":p).replace(/\\D/g,\"\");return d.length>=10?MYOP_CHAT+d.slice(-10):\"\";}\n"
       "function fmtNum(p){")
# 5. the button in each chat's header, before Call
C = rp(C, """    el("button",{cls:"callbtn",type:"button","aria-label":"Call from the clinic number",onclick:doCall},[svg(IC.call),el("span",{cls:"lbl",text:"Call"})]));""",
       """    (myopUrl(j.phone)?el("a",{cls:"myopbtn",href:myopUrl(j.phone),target:"_blank",rel:"noopener","aria-label":"Open this chat in MyOperator (new tab)",title:"Reply to this patient in MyOperator"},[svg(IC.ext,"#fff"),el("span",{cls:"lbl",text:"MyOperator"})]):document.createTextNode("")),   // replaceChildren would print a null
    el("button",{cls:"callbtn",type:"button","aria-label":"Call from the clinic number",onclick:doCall},[svg(IC.call),el("span",{cls:"lbl",text:"Call"})]));""")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "portal_inbox.py"), "wb").write(C.encode("utf-8"))
print("written portal_inbox.py", hashlib.md5(C.encode("utf-8")).hexdigest()[:8])

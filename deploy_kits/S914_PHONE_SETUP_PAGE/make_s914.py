"""make_s914.py -- kit S914_PHONE_SETUP_PAGE (Sanjeevni session 497, 21-Nov-2026).

The reception phone's set-up, written as the phone now stands (D1029, the owner's own steps 19:58-20:43 IST 20-Nov):
screen lock None; the macro 'Sanjeevni Whatsapp' with NO constraints; Screen On + Wait 2 s after JSON Parse; the 'sent'
POST with no constraint (F-1516); the 10:00 daily check (S909) proves it every day.

  python make_s914.py page  <supplier_msg.py in> <porders_s454.py in> <out dir>
      supplier_msg.py : page_phone_setup's steps rewritten (Hindi, staff); nothing else in the file changes.
      porders_s454.py : three wordings that still said "keep the phone unlocked / a dark phone does not ask".
  python make_s914.py macro <macros.template.mdr in> <out dir>
      the repository's reference macro brought to the same: the macro's two constraints and the POST's constraint
      removed; Screen On + Wait 2 s put after JSON Parse. Only key names are touched -- no value is printed.

Exact anchors only: each must occur exactly once in the input, or the script stops and writes nothing.
"""
import hashlib
import json
import os
import sys

NEW_BLOCK = """<div class="card"><h2>Har din apne aap jaanch</h2>
<p>Har subah <b>10:00 baje</b> server is phone se clinic ke apne WhatsApp par ek jaanch message bhejwata hai. Message clinic inbox mein pahunch gaya to setup sahi hai. Na pahunche to server khud dhoondta hai ki kahan ruka, aur Doctor sahab ko batata hai. Aapko kuch nahi karna.</p></div>
<div class="card"><h2>Phone ki settings (ek baar)</h2>
<ul>
<li><b>Screen lock: None</b> (Settings &rarr; Lock screen &rarr; Screen lock type &rarr; None). Pattern, PIN ya password nahi &mdash; warna andhere phone par WhatsApp nahi khulta.</li>
<li><b>Phone par sirf ek WhatsApp:</b> <b>WhatsApp Business</b>. Uske saath doosra (bina register kiya) WhatsApp Messenger pada ho to link ek box par ruk jaata hai aur kuch nahi jaata &mdash; use hata dijiye. Phone WhatsApp mein login rahe.</li>
<li>MacroDroid &rarr; Battery &rarr; <b>Unrestricted</b>; Accessibility &rarr; MacroDroid <b>on</b>; <i>Display over other apps</i> <b>on</b>.</li>
</ul></div>
<div class="card"><h2>Macro: <i>Sanjeevni Whatsapp</i> (MacroDroid)</h2>
<p><b>Trigger:</b> <i>Regular Interval</i> &middot; har <b>1 minute</b>. Koi loop nahi.</p>
<p><b>Constraints: koi nahi</b> &mdash; na macro par, na kisi action par (na <i>Device Unlocked</i>, na <i>Screen On</i>, na <i>App foreground</i>). Phone andhera ho tab bhi har minute poochta hai; screen macro khud jagata hai.</p>
<p><b>Actions, isi kram mein:</b></p>
<ol>
<li><b>HTTP Request</b> &middot; GET &middot; URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/next</code> &middot; Header ka naam bilkul <code>X-Phone-Token</code> &mdash; beech mein ya aakhir mein koi space nahi (keyboard khud ek space jod deta hai, tab request phone se nikalti hi nahi) &middot; value = neeche wala token &middot; Response ko variable <code>resp</code> mein save karein.</li>
<li><b>If</b> <code>resp</code> contains <code>text</code>:</li>
<li>&nbsp;&nbsp;<b>JSON Parse</b>: <code>resp</code> ko dictionary <code>msg</code> mein.</li>
<li>&nbsp;&nbsp;<b>Screen On/Off</b> &rarr; <b>Screen On</b>.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 2 second.</li>
<li>&nbsp;&nbsp;<b>Open Website</b>: address haath se type kijiye, chat se kabhi paste nahi: <code>https://wa.me/{lv=msg[to]}?text={lv=msg[text]}</code> (<code>lv</code> mein chhota <b>L</b> hai, ank 1 nahi) &middot; <i>URL encode parameters</i> par tick.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 6 second.</li>
<li>&nbsp;&nbsp;<b>UI Interaction</b> &rarr; <i>Click</i> &rarr; text <code>Send</code>.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 3 second.</li>
<li>&nbsp;&nbsp;<b>HTTP Request</b> &middot; POST &middot; URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/done</code> &middot; content type <code>application/json</code> &middot; Body: <code>{"id": {lv=msg[id]}, "ok": true}</code>. Yeh request <b>pehli request ko copy karke</b> banaiye &mdash; tab key uske saath aa jaati hai. <b>Is action par koi constraint nahi.</b></li>
<li><b>End If</b>.</li>
</ol>
<p><b>Pehli baar:</b> macro ko ek baar <i>Test actions</i> se chalaiye aur phone ki screen dekhte rahiye. Bina dekhe dobara mat chalaiye.</p>
<p class="mut">Ek message server ek hi baar deta hai. Agar Send nahi dab paaya: POST body <code>{"id": {lv=msg[id]}, "ok": false, "error": "send not clicked"}</code> bhejein &mdash; server 30 minute baad phir se dega, aur 30 minute baad Vendor payments page par <b>Bhejo</b> button dikhne lagega.</p>
<p class="mut">Poora macro, key ke saath, ek file mein Doctor sahab ke <i>Clinic PCs</i> page par hai (sirf unke liye).</p></div>"""

INTRO_OLD = 'Reception ka phone har minute server se poochta hai "koi message hai?"'
INTRO_NEW = 'Reception ka phone har minute (screen band ho tab bhi) server se poochta hai "koi message hai?"'
BLOCK_START = '<div class="card"><h2>Ek baar ka kaam'
BLOCK_END = 'upar likhe steps hi record hain.</p></div>'
ROUTE = '@bp.route("/finance/purchase/page/phone-setup")\n'
ROUTE_NOTE = ('# S914_PHONE_SETUP_PAGE (21-Nov-2026, D1029): the steps as the phone now stands -- screen lock None, the macro with NO\n'
              '#   constraints, Screen On + Wait 2 s after JSON Parse, the POST unconstrained (F-1516); the 10:00 daily check (S909) proves it.\n')

PORDERS = [
    ('"wa_unlock": ("Reception phone unlocked rakhiye. WhatsApp khud khulega, har minute ek supplier (%d minute).",\n'
     '                  "Keep the reception phone unlocked. WhatsApp opens by itself, one supplier a minute (%d minutes)."),',
     '"wa_unlock": ("WhatsApp khud khulega, har minute ek supplier (%d minute). Phone chalu aur mobile data on rakhiye.",      # S914\n'
     '                  "WhatsApp opens by itself, one supplier a minute (%d minutes). Keep the phone on and its mobile data on."),'),
    ('"The reception phone has been silent since %s \\u2014 unlock it, keep the screen on and mobile data on; order by call meanwhile"',
     '"The reception phone has been silent since %s \\u2014 keep it on with its mobile data on, and MacroDroid not force-stopped; order by call meanwhile"'),
    ('"Reception phone %s se chup hai \\u2014 phone unlock kijiye, screen on aur mobile data on rakhiye; tab tak call se order kijiye"',
     '"Reception phone %s se chup hai \\u2014 phone chalu aur mobile data on rakhiye, MacroDroid band mat kijiye; tab tak call se order kijiye"'),
    ("The phone sends only while it is awake and unlocked; a dark phone does not ask, and that is normal.",
     "The phone asks every minute, with its screen dark too (no screen lock; the macro wakes the screen to send). The 10:00 daily check proves it."),
]


def once(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("make_s914: anchor %s found %d times (must be 1) -- nothing written" % (what, n))
    return s.replace(old, new)


def md5(b):
    return hashlib.md5(b).hexdigest()


def page(sm_in, po_in, out):
    s = open(sm_in, encoding="utf-8").read()
    if s.count(BLOCK_START) != 1 or s.count(BLOCK_END) != 1:
        sys.exit("make_s914: the set-up block's anchors are not each found once -- nothing written")
    a = s.index(BLOCK_START)
    b = s.index(BLOCK_END) + len(BLOCK_END)
    if a > b:
        sys.exit("make_s914: the block's anchors are out of order -- nothing written")
    s = s[:a] + NEW_BLOCK + s[b:]
    s = once(s, INTRO_OLD, INTRO_NEW, "intro")
    s = once(s, ROUTE, ROUTE_NOTE + ROUTE, "route")
    p = open(po_in, encoding="utf-8").read()
    for i, (o, n) in enumerate(PORDERS):
        p = once(p, o, n, "porders #%d" % (i + 1))
    os.makedirs(out, exist_ok=True)
    for name, text in (("supplier_msg.py", s), ("porders_s454.py", p)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("%s %s" % (md5(text.encode("utf-8")), name))


def _siguid(seed):
    return int(hashlib.md5(seed.encode()).hexdigest()[:15], 16)      # a positive long, fixed for this kit


def macro(tpl_in, out):
    raw = open(tpl_in, "rb").read()
    d = json.loads(raw.decode("utf-8"))
    same = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8") == raw
    ms = d.get("macroList") or []
    if len(ms) != 1 or ms[0].get("m_name") != "Sanjeevni Whatsapp":
        sys.exit("make_s914: the template does not hold the one macro 'Sanjeevni Whatsapp' -- nothing written")
    m = ms[0]
    A = m["m_actionList"]
    kinds = [a.get("m_classType") for a in A]
    want = ["HttpRequestAction", "IfConditionAction", "JsonParseAction", "OpenWebPageAction", "PauseAction",
            "UIInteractionAction", "PauseAction", "HttpRequestAction", "EndIfAction"]
    if kinds != want:
        sys.exit("make_s914: the template's actions are not the 04-Oct shape -- nothing written: %s" % kinds)
    if [c.get("m_classType") for c in m["m_constraintList"]] != ["DeviceLockedConstraint", "ScreenOnOffConstraint"]:
        sys.exit("make_s914: the macro's constraints are not the 04-Oct pair -- nothing written")
    if [c.get("m_classType") for c in A[7]["m_constraintList"]] != ["ActiveApplicationConstraint"]:
        sys.exit("make_s914: the POST's constraint is not the App-foreground one -- nothing written")
    m["m_constraintList"] = []
    A[7]["m_constraintList"] = []
    screen = {"m_pieLockScreen": False, "m_screenOff": False, "m_screenOffNoLock": False, "m_screenOnAlternative": False,
              "disableLogging": False, "m_SIGUID": _siguid("S914 screen on"), "m_classType": "ScreenOnAction",
              "m_constraintList": [], "m_isDisabled": False, "m_isOrCondition": False}
    wait = dict(A[4])                                   # the template's own Wait action, as MacroDroid wrote it
    wait["m_constraintList"] = []
    wait["m_delayInSeconds"] = 2
    wait["m_delayInMilliSeconds"] = 0
    wait["m_SIGUID"] = _siguid("S914 wait 2 s")
    m["m_actionList"] = A[:3] + [screen, wait] + A[3:]
    ids = [a["m_SIGUID"] for a in m["m_actionList"]] + [t["m_SIGUID"] for t in m["m_triggerList"]]
    if len(set(ids)) != len(ids):
        sys.exit("make_s914: a SIGUID would repeat -- nothing written")
    outb = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "macros.template.mdr"), "wb") as fh:
        fh.write(outb)
    print("%s macros.template.mdr (the input re-dumped byte-identical: %s; actions %d -> %d; constraints 2 -> 0; POST's 1 -> 0)"
          % (md5(outb), same, len(A), len(m["m_actionList"])))


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "page":
        page(sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 4 and sys.argv[1] == "macro":
        macro(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)

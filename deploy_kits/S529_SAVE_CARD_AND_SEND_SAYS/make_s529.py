#!/usr/bin/env python3
"""make_s529.py -- kit S529_SAVE_CARD_AND_SEND_SAYS: builds packs.html and setup_notes.py from their pinned FROM bytes by
exact, counted edits (every anchor exactly once), in memory first; nothing is written unless every edit applies.
save/index.php is written whole (it is new) and holds no number.
  python3 make_s529.py <dir with the FROM files> <out dir>"""
import hashlib, os, sys

FROM = {"packs.html": "633ddba801a80e2aaaf1102d8ef7d1a2",
        "setup_notes.py": "63477bc0781f6554b57a7868ea6161dc"}

PACKS = [
    ("K1 the button has a name and an answer line under it",
     '<button class="big" onclick="sendPack()">Send to accountants</button> <span class="mut" id="to"></span>'
     '<div id="sends" class="mut" style="margin-top:4px"></div></div>',
     '<button class="big" id="sendbtn" onclick="sendPack()">Send to accountants</button> <span class="mut" id="to"></span>'
     '<div id="sendres" style="margin-top:8px"></div>'
     '<div id="sends" class="mut" style="margin-top:4px"></div></div>'),
    ("K2 once sent, the button reads 'Send again'",
     "    $(\"sends\").innerHTML=(j.sends||[]).length?'Sent: '",
     "    $(\"sendbtn\").textContent=(j.sends||[]).length?\"Send again to accountants\":\"Send to accountants\";   // S529 (F-855)\n"
     "    $(\"sends\").innerHTML=(j.sends||[]).length?'Sent: '"),
    ("K3 the send says Sending, then Sent / NOT sent right under the button",
     'function sendPack(){if(!confirm("Send the "+$("mn").textContent+" pack to the accountants now?"))return; '
     'post("/finance/packs/api/send",{month:$("m").value}).then(function(j){if(!j.ok){alert(j.message||j.error);return} '
     'flash(j.already?j.message:("Sent — "+j.parts+" mail(s), "+j.attachments+" attachment(s)"+(j.resend?" (a re-send, recorded)":"")+".")); load()})}',
     '// S529 (F-855): the answer appears right under the button -- Sending..., then Sent at HH:MM or NOT sent -- and the button\n'
     '// cannot be pressed twice while a send is on its way. The owner pressed twice on 11-Oct because no answer showed where he looked.\n'
     'function sendRes(html){$("sendres").innerHTML=html}\n'
     'function sendPack(){var b=$("sendbtn");var again=(b.textContent.indexOf("again")>=0);'
     'if(!confirm((again?"This pack was already sent. Send it AGAIN":"Send the "+$("mn").textContent+" pack")+" to the accountants now?"))return;'
     'var old=b.textContent;b.disabled=true;b.textContent="Sending… (up to a minute)";'
     'sendRes(\'<div class="mut">Sending the pack now — please keep this page open.</div>\');'
     'post("/finance/packs/api/send",{month:$("m").value}).then(function(j){b.disabled=false;b.textContent=old;'
     'if(!j.ok){sendRes(\'<div class="green" style="background:#fbeaea;border-left-color:#a33">NOT sent — \'+esc(j.message||j.error)+\'</div>\');return}'
     'var hm=new Date().toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit"});'
     'var t=j.already?j.message:("Sent at "+hm+" — "+j.parts+" mail(s), "+j.attachments+" attachment(s)"+(j.resend?" (a re-send, recorded)":"")+".");'
     'sendRes(\'<div class="green">✓ \'+esc(t)+\'</div>\');flash(t);load()})'
     '.catch(function(){b.disabled=false;b.textContent=old;'
     'sendRes(\'<div class="green" style="background:#fff6e0;border-left-color:#b27a00">The page lost the answer. Wait a minute, then look at the Sent line below before pressing again.</div>\')})}'),
]

NOTES = [
    ("N1 the Websites card: the save page",
     "                \"<b>At GoDaddy, as forwarding links</b> (they never touch this server): save, contact, map, web, ios, \"\n",
     "                \"<b>save</b> opens the clinic's <a href='https://drmanojagarwal.com/save/' target=_blank rel=noopener>save contact</a> \"\n"
     "                \"page on this server (S529): one tap opens the phone's own new-contact form, filled in. Its card is \"\n"
     "                \"<span class=nw>clinic.vcf</span> beside the page \\u2014 change the card there, never the page.\",\n"
     "                \"<b>At GoDaddy, as forwarding links</b> (they never touch this server): save (to that page), contact, map, web, ios, \"\n"),
    ("N2 the save gap is closed",
     "            \"save.dr-manoj.in (the contact card patients save) did not open on 11-Oct from Claude's browser; on 08-Sep it \"\n"
     "            \"forwarded through GoDaddy. Worth one tap on your phone.\",\n",
     ""),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, out):
    res = {}
    for name, edits in (("packs.html", PACKS), ("setup_notes.py", NOTES)):
        b = open(os.path.join(src, name), "rb").read()
        if md5(b) != FROM[name]:
            raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (name, md5(b), FROM[name]))
        t = b.decode("utf-8")
        for label, old, new in edits:
            n = t.count(old)
            if n != 1:
                raise SystemExit("REFUSED: %s / %s: the anchor occurs %d times" % (name, label, n))
            t = t.replace(old, new)
        res[name] = t.encode("utf-8")
        print("%-15s %d edits  %s -> %s" % (name, len(edits), FROM[name][:8], md5(res[name])[:8]))
    os.makedirs(out, exist_ok=True)
    for name, b in res.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(b)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])

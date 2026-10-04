#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s473.py -- S473_PHONE_KITS (session 293, 04-Oct-2026). Exact-anchor edits on /root/finance/pc_kits.py 83f318d7 (S460).

The owner, 04-Oct: "there are two mobiles on MacroDroid, so a full setup of that MacroDroid part for the reception mobile and
for my mobile should also be there in case it is required again". Built as he agreed:
  * two PHONE cards on the Clinic PCs page (now 'Clinic PCs & phones'): Dr Manoj's phone (Fold) -- the two bank-SMS macros --
    and the reception mobile -- the Sanjeevni WhatsApp order macro. Each card says what the server last heard from that phone
    (the last bank SMS received; when the queue door was last asked), the macros it carries, the things only a person can do
    on a fresh phone (install MacroDroid, grant SMS / notification / accessibility / battery, import the file, switch the
    macros on), and what else lives on that phone.
  * ONE button per phone: 'Set up this phone again' -> the browser downloads MacroDroid_<phone>_<date>.mdr, made at that
    moment from a TEMPLATE in the repository (deploy_kits/PC_KITS/macrodroid/<phone>/macros.template.mdr: the owner's own
    exports of 04-Oct with every key replaced by a placeholder and the retired 'SMS to Google Sheet' macro dropped) with the
    LIVE key put in -- the bank-SMS door's key (bank_sms.key on this box) and the reception phone's token (the setting
    supplier_msg.phone_token). Nothing secret is in the repository; the file carries the key only while it is downloaded by
    the owner, signed in, from this page (the same cross-site check as the PC buttons; the press is logged).
    On the phone: open the downloaded file -> MacroDroid imports it. The person-list on the card is the rest.
Every anchor must be found exactly once.
   usage: apply_s473.py <pc_kits.py>
"""
import hashlib
import sys

FROM = "83f318d70abbaa2058aca97c0cbc2784"

EDITS = [
    ('''PC_BY_ID = {p["id"]: p for p in PCS}
''',
     '''PC_BY_ID = {p["id"]: p for p in PCS}

# S473: the two phones that run MacroDroid. The template (the owner's own export, keys replaced by placeholders) lives in
# the repository under PC_KITS/macrodroid/<id>/; the key goes in at download time, from this box, for the owner only.
PHONES = [
    {"id": "foldphone", "label": "Dr Manoj’s phone (Fold)", "what": "The bank's settlement SMS to the clinic server · 2 macros",
     "file": "MacroDroid_DrManojPhone", "macros": ["Bank SMS to Clinic Server", "Bank SMS 2 (Yes Bank) to Clinic Server"],
     "keys": [("{{BANK_SMS_KEY}}", "bank_sms")],
     "person": [("macrodroid", "Install MacroDroid from the Play Store; open it once"),
                ("perms", "Allow it to read SMS and to run in the background (battery: unrestricted)"),
                ("import", "Open the downloaded file — MacroDroid imports both macros; switch each on"),
                ("test", "Tap ‘Test’ on ‘Bank SMS to Clinic Server’ once — the server answers 200 on the bank-SMS page")],
     "also": ["Tailscale (signed in)", "CX File Explorer (the SMB user for this PC)", "The Clinic app (your login)"]},
    {"id": "receptionmobile", "label": "Reception mobile", "what": "Sanjeevni WhatsApp orders to the suppliers · 1 macro",
     "file": "MacroDroid_ReceptionMobile", "macros": ["Sanjeevni Whatsapp"],
     "keys": [("{{PHONE_TOKEN}}", "supplier_msg.phone_token")],
     "person": [("macrodroid", "Install MacroDroid from the Play Store; open it once"),
                ("perms", "Allow it to run in the background (battery: unrestricted), to draw over other apps, and its accessibility service"),
                ("import", "Open the downloaded file — MacroDroid imports the macro; switch it on"),
                ("whatsapp", "WhatsApp signed in on this phone (the orders go from its own WhatsApp)")],
     "also": ["WhatsApp (the reception number, internal use)", "The Clinic app (the shared reception login)", "Callback Tracker (backup)"]},
]
PHONE_BY_ID = {p["id"]: p for p in PHONES}
PHONES_ROOT = os.environ.get("PHONE_KITS_ROOT", os.path.join(KIT_ROOT, "macrodroid"))
'''),
    ('''@bp.route("/finance/pcs/setup/<pc_id>", methods=["POST"])
def pcs_setup(pc_id):
''',
     '''def phone_template(ph_id):
    """S473: the phone's template file, when it is there and KIT_INFO.txt says it is whole. None otherwise."""
    try:
        d = os.path.join(PHONES_ROOT, ph_id)
        info = {}
        with open(os.path.join(d, "KIT_INFO.txt"), "r", encoding="utf-8") as fh:
            for line in fh:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip()
        tpl = os.path.join(d, "macros.template.mdr")
        if _md5(tpl) != info.get("template_md5"):
            return None
        return {"path": tpl, "template_md5": info["template_md5"], "version": info.get("version", ""), "packed": info.get("packed", "")}
    except (OSError, KeyError):
        return None


def _phone_key(which):
    """S473: the live value a placeholder stands for -- read on this box at download time, never stored in the kit."""
    if which == "bank_sms":
        bs = sys.modules.get("bank_sms")
        try:
            return (bs._key() if bs is not None else "") or ""
        except Exception:                                      # noqa: BLE001
            return ""
    try:
        r = _db().execute("SELECT value FROM setting WHERE key=?", (which,)).fetchone()
        return (r[0] if r else "") or ""
    except Exception:                                          # noqa: BLE001
        return ""


def phone_file(ph, info):
    """S473: the template with the live keys put in. Returns (bytes, missing) -- missing names a key this box could not read."""
    with open(info["path"], "r", encoding="utf-8") as fh:
        text = fh.read()
    missing = []
    for placeholder, which in ph["keys"]:
        val = _phone_key(which)
        if not val:
            missing.append(which)
            continue
        text = text.replace(placeholder, json.dumps(val)[1:-1])
    return text.encode("utf-8"), missing


def _phone_heard(ph_id):
    """S473: what this box last heard from the phone, in the owner's words (its own records; never a number)."""
    try:
        con = _db()
        if ph_id == "foldphone":
            r = con.execute("SELECT MAX(received_at) FROM bank_sms_settlement").fetchone()
            y = con.execute("SELECT MAX(received_at) FROM bank_sms_yes").fetchone()
            a, b = (r[0] if r else None), (y[0] if y else None)
            return ("last bank SMS received %s%s" % (_when(a), (" · last Yes Bank SMS %s" % _when(b)) if b else "")) if a else "no bank SMS has reached the server yet"
        if ph_id == "receptionmobile":
            r = con.execute("SELECT value FROM setting WHERE key='supplier_msg.phone_last'").fetchone()
            if r and r[0]:
                at, _sp, code = str(r[0]).partition(" ")
                return "last asked the order queue %s (%s)" % (_when(at.replace("T", " ")), "answered" if code == "200" else "refused: wrong token")
            return "the phone has not asked the order queue yet"
    except Exception:                                          # noqa: BLE001
        pass
    return "its record could not be read"


@bp.route("/finance/pcs/phone/<ph_id>", methods=["POST"])
def pcs_phone(ph_id):
    """S473: the owner's press -> MacroDroid_<phone>_<date>.mdr with the live key in. Same gate and same cross-site check as a PC."""
    u, err = _require("checker")
    if err:
        return _page("Clinic PCs & phones", _denied()), 403
    why = _cross_site()
    if why:
        _log("phone:" + (ph_id if ph_id in PHONE_BY_ID else "?"), "a press was REFUSED: %s [origin=%s host=%s]" % (
            why, _seen(request.headers.get("Origin")), _seen(request.host)), u.get("user") or "")
        return _page("Clinic PCs & phones", "<h1>Clinic PCs & phones</h1><div class=pc><div class=pcn>Not taken</div><p class=what>The "
                     "press did not come from this page (%s). Open the Clinic PCs tile from your portal and press "
                     "the button there.</p></div>" % html.escape(why)), 403
    ph = PHONE_BY_ID.get(ph_id)
    info = phone_template(ph_id) if ph else None
    if not info:
        return _page("Clinic PCs & phones", "<div class=pc><div class=pcn>No kit</div><p class=what>This phone's macros are not on the "
                     "server yet, so there is nothing to set it up with.</p></div>"), 404
    body, missing = phone_file(ph, info)
    if missing:
        _log("phone:" + ph_id, "the file was NOT made: this box could not read %s" % ", ".join(missing), u.get("user") or "")
        return _page("Clinic PCs & phones", "<div class=pc><div class=pcn>Not made</div><p class=what>This box could not read the key "
                     "the macros need (%s), so no file was made. Tell the assistant.</p></div>" % html.escape(", ".join(missing))), 503
    _log("phone:" + ph_id, "the MacroDroid file was made (template %s)" % info["template_md5"][:8], u.get("user") or "")
    r = Response(body, mimetype="application/octet-stream")
    r.headers["Content-Disposition"] = 'attachment; filename="%s_%s.mdr"' % (ph["file"], _ist_now().strftime("%Y%m%d"))
    r.headers["Cache-Control"] = "no-store"
    return r


@bp.route("/finance/pcs/setup/<pc_id>", methods=["POST"])
def pcs_setup(pc_id):
'''),
    ('''    if planned:
        out.append("<div class=pc>%s</div>" % "".join(
            "<div class=row%s><div class=pcn>%s</div><span class='st info'>Not set up yet</span></div>"
            % (" style='margin-top:8px'" if i else "", html.escape(p["label"])) for i, p in enumerate(planned)))
''',
     '''    if planned:
        out.append("<div class=pc>%s</div>" % "".join(
            "<div class=row%s><div class=pcn>%s</div><span class='st info'>Not set up yet</span></div>"
            % (" style='margin-top:8px'" if i else "", html.escape(p["label"])) for i, p in enumerate(planned)))
    # S473: the two phones
    out.append("<h1 style='margin-top:18px'>Phones</h1><p class=sub>The MacroDroid macros on the two phones. After a reset or a new phone: "
               "sign in to the portal on that phone, open this page, press its button, open the downloaded file.</p>")
    for ph in PHONES:
        info = phone_template(ph["id"])
        card = ["<div class=pc><div class=row><div class=pcn>%s</div><span class='st %s'>%s</span></div><p class=what>%s</p><p class=said>%s</p>"
                % (html.escape(ph["label"]), "ok" if info else "info", "Macros on the server" if info else "No kit yet",
                   html.escape(ph["what"]), html.escape(_phone_heard(ph["id"])))]
        card.append("<p class=said>Macros: %s</p>" % html.escape(" · ".join(ph["macros"])))
        if info:
            card.append("<form method=post action='/finance/pcs/phone/%s'><button type=submit>Set up this phone again</button></form>" % ph["id"])
            card.append("<div class=todo><b>Only a person can do these, on the phone:</b><ul>%s</ul></div>" % "".join(
                "<li>%s</li>" % html.escape(words) for _k, words in ph["person"]))
            card.append("<p class=said>Also on this phone, not in the file: %s</p>" % html.escape(" · ".join(ph["also"])))
            last = _log_tail("phone:" + ph["id"])
            card.append("<p class=kit>Macros on the server: %s, packed %s. The key goes in when you press the button; it is not in the kit.%s</p>" % (
                html.escape(info["version"]), html.escape(info["packed"]),
                (" Last: " + html.escape(" · ".join("%s %s" % (_when(r[0]), r[2]) for r in last if len(r) > 2))) if last else ""))
        else:
            card.append("<p class=kit>Its macros are not on the server yet.</p>")
        card.append("</div>")
        out.append("".join(card))
'''),
    ('''    return _page("Clinic PCs", "".join(out), refresh=True)
''',
     '''    return _page("Clinic PCs & phones", "".join(out), refresh=True)
'''),
    ('''    out = ["<h1>Clinic PCs</h1><p class=sub>After a Windows reinstall: sign in to the portal on that PC, open this "
           "page, press that PC’s button.</p>"]
''',
     '''    out = ["<h1>Clinic PCs &amp; phones</h1><p class=sub>After a Windows reinstall: sign in to the portal on that PC, open this "
           "page, press that PC’s button. The phones are below.</p>"]
'''),
]


def apply(src):
    for n, (old, new) in enumerate(EDITS, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor %d was found %d time(s), expected 1 - nothing written" % (n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s473.py <pc_kits.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("pc_kits.py %s -> %s (%d edits; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()

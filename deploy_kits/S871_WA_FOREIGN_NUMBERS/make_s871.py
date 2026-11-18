#!/usr/bin/env python3
"""make_s871.py -- kit S871_WA_FOREIGN_NUMBERS (the parent, S480, 18-Nov-2026).

A WhatsApp sender with a number abroad (e.g. the USA, +1 and 10 digits) was stored under its LAST 10 digits and
treated as Indian: Reply went to +91 and the cut number (MyOperator: "Recipient phone number is invalid"), the screens
showed "+91 ...", and Call rang an invalid Indian number. This patcher, from the exact FROM bytes:

  /root/portal/portal_inbox.py   chat key keeps a number abroad whole; sends split code + number; templates and calls
                                  refused for a number abroad in plain words; shown as "+1 20171 6xxxx · abroad"; the
                                  MyOperator link uses its own code; once, the chats already cut are moved to the whole
                                  number from the raw pushes; health carries one count (no numbers).
  /root/portal/calls_console.py  the WhatsApp items keep the whole number; shown with its code; no Call button for it;
                                  the click-to-call refuses it.

Usage: python make_s871.py SRC_DIR OUT_DIR    (SRC_DIR holds the two FROM files; OUT_DIR gets the two TO files)
Every anchor must occur exactly once; any miss stops with nothing written.
"""
import hashlib
import os
import sys

FROM = {"portal_inbox.py": "ff0f02a89d66863b228de0a22e888367",
        "calls_console.py": "36f6221cca5a2bb2edef4229f1724ece"}

# ------------------------------------------------------------------------------------------------ portal_inbox.py
PI = []

PI.append(('''def last10(s):
    d = re.sub(r"\\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else ""
''', '''def last10(s):
    """The chat key. S871: an Indian number -> its 10 digits (as before); a number from another country -> all its
    digits, the country code first (MyOperator sends 1 + 10 digits for the USA), so a reply reaches it. Idempotent:
    a key passed back by the page comes out unchanged."""
    d = re.sub(r"\\D", "", str(s or ""))
    if d.startswith("00"):
        d = d[2:]
    if len(d) < 10:
        return ""
    if len(d) == 10 or (len(d) == 12 and d.startswith("91")) or (len(d) == 11 and d.startswith("0")):
        return d[-10:]
    if len(d) <= 15 and d[0] != "0":
        return d
    return d[-10:]


def ten(s):
    """The old rule (the last 10 digits): kept for the patient list, whose numbers are Indian."""
    d = re.sub(r"\\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else ""


# S871: country codes by length (ITU E.164) -- a number abroad is split into its code and number for MyOperator.
_CC1 = ("1", "7")
_CC2 = ("20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "41", "43", "44", "45", "46", "47", "48", "49",
        "51", "52", "53", "54", "55", "56", "57", "58", "60", "61", "62", "63", "64", "65", "66", "81", "82", "84",
        "86", "90", "91", "92", "93", "94", "95", "98")


def abroad(key):
    """True for a chat key longer than 10 digits: a number from another country."""
    return len(str(key or "")) > 10


def split_cc(key):
    """'98765xxxxx' -> ('91', the 10 digits); '1' + 10 digits -> ('1', the 10). Pure."""
    k = str(key or "")
    if not abroad(k):
        return "91", k
    n = 1 if k[:1] in _CC1 else (2 if k[:2] in _CC2 else 3)
    return k[:n], k[n:]


def full_number(key):
    """Country code + number, digits only (the send log's customer_number column)."""
    cc, nat = split_cc(key)
    return (cc + nat) if nat else ""


_S871 = {"done": False}                 # the once-only move's mark, once seen, is not looked for again in this process


def s871_rekey(c, names, raw_dir=None):
    """S871, once: a chat from abroad was stored under its last 10 digits. Read the raw pushes again; where a
    message's sender had a number abroad, move that chat to the whole number. A cut key that two different numbers
    share is left alone. When the cut key could also be an Indian mobile (6-9 first), only the messages that number
    sent are moved, never the rest. Returns {cut key: whole number}."""
    return s871_apply(c, s871_plan(names, raw_dir))


def s871_plan(names, raw_dir=None):
    """S871: read the raw pushes (no database, no lock) -> {cut key: (set of whole numbers, set of message ids)}."""
    raw_dir = raw_dir or RAW_DIR
    seen, mids = {}, {}
    for n in names:
        try:
            with open(os.path.join(raw_dir, n), "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        for line in data.split(b"\\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line.decode("utf-8", "replace"))
                body = rec.get("body") if isinstance(rec, dict) else None
                if not isinstance(body, dict):
                    continue
                p = read_push(body)
            except Exception:                                           # noqa: BLE001
                continue
            new, old = last10(p["phone"]), ten(p["phone"])
            mid = str(p["id"] or "").strip()
            if not new or not old or new == old or not mid:
                continue
            seen.setdefault(old, set()).add(new)
            mids.setdefault(old, set()).add(mid)
    return {old: (seen[old], mids.get(old, set())) for old in seen}


def s871_apply(c, plan):
    """S871: move the cut chats of a plan (inside the caller's transaction). Returns {cut key: whole number}."""
    moved = {}
    for old, (news, idset) in sorted((plan or {}).items()):
        if len(news) != 1:
            continue
        new = next(iter(news))
        if old[:1] in "6789":
            ids = sorted(idset or ())
            for mid in ids:
                c.execute("UPDATE msgs SET phone=? WHERE phone=? AND mid=?", (new, old, mid))
            moved[old] = new
            continue
        if not c.execute("SELECT 1 FROM msgs WHERE phone=? LIMIT 1", (old,)).fetchone():
            continue
        c.execute("UPDATE msgs SET phone=? WHERE phone=?", (new, old))
        c.execute("UPDATE retry_q SET phone=? WHERE phone=?", (new, old))
        r = c.execute("SELECT ts FROM reads WHERE phone=?", (old,)).fetchone()
        if r:
            c.execute("INSERT OR REPLACE INTO reads(phone,ts) VALUES(?,?)", (new, r[0]))
            c.execute("DELETE FROM reads WHERE phone=?", (old,))
        moved[old] = new
    return moved


def abroad_count():
    """S871: how many chats are from numbers abroad (a count only -- no number). -1 when the store cannot be read."""
    try:
        c = db()
        try:
            return int(c.execute("SELECT COUNT(DISTINCT phone) FROM msgs WHERE length(phone) > 10").fetchone()[0])
        finally:
            c.close()
    except Exception:                                                   # noqa: BLE001
        return -1
'''))

PI.append(('''                k = last10(r[0])
                if k and k not in m:''', '''                k = ten(r[0])                                    # S871: the patient list keeps the old rule
                if k and k not in m:'''))

PI.append(('''        except OSError:
            return
        c = db()
        try:
            c.execute("BEGIN IMMEDIATE")
            for n in names:
                fp = os.path.join(RAW_DIR, n)''', '''        except OSError:
            return
        plan = None                                                     # S871, once: chats from abroad get their whole number
        if not _S871["done"]:
            try:
                c0 = db()
                try:
                    need = c0.execute("SELECT 1 FROM offsets WHERE fname='s871:rekey'").fetchone() is None
                finally:
                    c0.close()
            except Exception:                                           # noqa: BLE001
                need = None                                             # the store busy for a moment: try again next time
            if need is False:
                _S871["done"] = True                                    # seen once: never looked for again in this process
            elif need:
                try:
                    plan = s871_plan(names)                             # the raw files read OUTSIDE the write lock
                except Exception:                                       # noqa: BLE001
                    plan = {}                                           # never a loop: the mark is written, nothing moved
        c = db()
        try:
            c.execute("BEGIN IMMEDIATE")
            if plan is not None and not c.execute("SELECT 1 FROM offsets WHERE fname='s871:rekey'").fetchone():
                c.execute("SAVEPOINT s871")
                try:
                    s871_apply(c, plan)
                    c.execute("RELEASE SAVEPOINT s871")
                except Exception:                                       # noqa: BLE001 -- the move fails alone; the ingest goes on
                    c.execute("ROLLBACK TO SAVEPOINT s871")
                    c.execute("RELEASE SAVEPOINT s871")
                c.execute("INSERT OR REPLACE INTO offsets(fname,pos) VALUES('s871:rekey',1)")
            for n in names:
                fp = os.path.join(RAW_DIR, n)'''))

PI.append(('''    payload = {"phone_number_id": PHONE_NUMBER_ID, "customer_country_code": "91", "customer_number": phone,''',
           '''    cc, nat = split_cc(phone)                                           # S871: a number abroad keeps its own code
    payload = {"phone_number_id": PHONE_NUMBER_ID, "customer_country_code": cc, "customer_number": nat,'''))

PI.append(('''("91" + e["customer"]) if e.get("customer") else "",''',
           '''full_number(e["customer"]) if e.get("customer") else "",'''))

PI.append(('''Customer: +91 %s\\n''', '''Customer: +%s\\n'''))

PI.append(('''% (e.get("ts", ""), e.get("by", ""), e.get("customer", ""), e.get("kind", ""),''',
           '''% (e.get("ts", ""), e.get("by", ""), full_number(e.get("customer", "")), e.get("kind", ""),'''))

PI.append(('''        ph = last10(b.get("phone"))
        if not ph:
            return fail("no number for this chat")
        try:
            import portal_wa''', '''        ph = last10(b.get("phone"))
        if not ph:
            return fail("no number for this chat")
        if abroad(ph):                                                  # S871
            return fail("This number is from abroad. Templates go only to Indian numbers -- reply while the "
                        "24-hour window is open.")
        try:
            import portal_wa'''))

PI.append(('''        ph = last10((request.get_json(silent=True) or {}).get("phone"))
        if not ph:
            return fail("no number for this chat")
        key = read_env().get("CALL_API_SECRET", "")''', '''        ph = last10((request.get_json(silent=True) or {}).get("phone"))
        if not ph:
            return fail("no number for this chat")
        if abroad(ph):                                                  # S871
            return fail("This number is from abroad -- the clinic line cannot call it. Reply on WhatsApp instead.")
        key = read_env().get("CALL_API_SECRET", "")'''))

PI.append(('''   var who=(e.name?e.name+" · ":"")+(e.customer?"+91 "+e.customer:"");''',
           '''   var who=(e.name?e.name+" · ":"")+(e.customer?(String(e.customer).length>10?"+"+e.customer+" (abroad)":"+91 "+e.customer):"");'''))

PI.append(('''function myopUrl(p){var d=String(p==null?"":p).replace(/\\D/g,"");return d.length>=10?MYOP_CHAT+d.slice(-10):"";}
function fmtNum(p){return "+91 "+p.slice(0,5)+" "+p.slice(5);}''',
           '''var CC2=["20","27","30","31","32","33","34","36","39","40","41","43","44","45","46","47","48","49","51","52","53","54","55","56","57","58","60","61","62","63","64","65","66","81","82","84","86","90","91","92","93","94","95","98"];   // S871: two-digit country codes
function ccLen(d){return /^[17]/.test(d)?1:(CC2.indexOf(d.slice(0,2))>=0?2:3);}
function myopUrl(p){var d=String(p==null?"":p).replace(/\\D/g,"");if(d.length>10){var n=ccLen(d);return MYOP_CHAT.replace(/91\\/$/,"")+d.slice(0,n)+"/"+d.slice(n);}return d.length>=10?MYOP_CHAT+d.slice(-10):"";}
function fmtNum(p){p=String(p==null?"":p);if(p.length<=10)return "+91 "+p.slice(0,5)+" "+p.slice(5);var n=ccLen(p),r=p.slice(n);return "+"+p.slice(0,n)+" "+r.slice(0,5)+" "+r.slice(5)+" · abroad";}'''))

PI.append(('''el("button",{cls:"callbtn",type:"button","aria-label":"Call from the clinic number",onclick:doCall},[svg(IC.call),el("span",{cls:"lbl",text:"Call"})])''',
           '''(String(j.phone).length>10?document.createTextNode(""):el("button",{cls:"callbtn",type:"button","aria-label":"Call from the clinic number",onclick:doCall},[svg(IC.call),el("span",{cls:"lbl",text:"Call"})]))'''))

# ------------------------------------------------------------------------------------------------ calls_console.py
CC = []

CC.append(('''def fmt_num(p):
    """'5000014075' -> '50000 14075' (the mock-up's grouping; the FULL number, D819)."""
    p = (p or "").strip()
    return (p[:5] + " " + p[5:]) if len(p) == 10 and p.isdigit() else p
''', '''_S871_CC2 = ("20", "27", "30", "31", "32", "33", "34", "36", "39", "40", "41", "43", "44", "45", "46", "47", "48",
             "49", "51", "52", "53", "54", "55", "56", "57", "58", "60", "61", "62", "63", "64", "65", "66", "81", "82",
             "84", "86", "90", "91", "92", "93", "94", "95", "98")


def _s871_key(s):
    """S871: the WhatsApp chat key as the inbox keeps it -- an Indian number's 10 digits, a number abroad whole."""
    d = re.sub(r"\\D", "", str(s or ""))
    if d.startswith("00"):
        d = d[2:]
    if len(d) < 10:
        return ""
    if len(d) == 10 or (len(d) == 12 and d.startswith("91")) or (len(d) == 11 and d.startswith("0")):
        return d[-10:]
    if len(d) <= 15 and d[0] != "0":
        return d
    return d[-10:]


def fmt_num(p):
    """'5000014075' -> '50000 14075' (the mock-up's grouping; the FULL number, D819).
    S871: a number abroad -> '+<code> 12345 67890 · abroad'."""
    p = (p or "").strip()
    if p.isdigit() and len(_s871_key(p)) > 10:
        p = _s871_key(p)
        n = 1 if p[:1] in ("1", "7") else (2 if p[:2] in _S871_CC2 else 3)
        r = p[n:]
        return "+%s %s %s · abroad" % (p[:n], r[:5], r[5:])
    return (p[:5] + " " + p[5:]) if len(p) == 10 and p.isdigit() else p
'''))

CC.append(('''"phone": re.sub(r"\\D", "", r["phone"] or "")[-10:], "kind": kind,''',
           '''"phone": _s871_key(r["phone"]), "kind": kind,'''))

# review MUST 1: wa_items kept only 10-digit keys -- a chat from abroad would vanish from the Console
CC.append(('''        if len(it["phone"]) == 10 and (phones is None or it["phone"] in phones):''',
           '''        if 10 <= len(it["phone"]) <= 15 and (phones is None or it["phone"] in phones):   # S871: a number abroad too'''))

# review MUST 2: Done / Not a patient refused any key but 10 digits
CC.append(('''    if act not in WZ_ACTS or not re.match(r"\\d{10}\\Z", phone or "") or''',
           '''    if act not in WZ_ACTS or not re.match(r"\\d{10,15}\\Z", phone or "") or'''))
CC.append(('''        if not re.match(r"\\d{10}\\Z", ph) or act not in WZ_ACTS or''',
           '''        if not re.match(r"\\d{10,15}\\Z", ph) or act not in WZ_ACTS or'''))

CC.append(('''    ph = re.sub(r"\\D", "", phone10 or "")[-10:]
    if len(ph) != 10:
        return False, "No 10-digit number on this row.", 400''', '''    if len(_s871_key(phone10)) > 10:                                    # S871: a number abroad is never cut to 10 digits
        return False, "This number is from abroad -- the clinic line cannot call it. Reply on WhatsApp instead.", 400
    ph = re.sub(r"\\D", "", phone10 or "")[-10:]
    if len(ph) != 10:
        return False, "No 10-digit number on this row.", 400'''))

CC.append(('''          <button type="button" class="awb sec" onclick="callBack('{{ a.phone }}',this)">Call</button>''',
           '''          {% if a.phone|length <= 10 %}<button type="button" class="awb sec" onclick="callBack('{{ a.phone }}',this)">Call</button>{% endif %}'''))

CC.append(('''function callBack(ph,b){
  if(!confirm(''', '''function callBack(ph,b){
  if(String(ph||'').replace(/[^0-9]/g,'').length>10){ toast('This number is from abroad — the clinic line cannot call it. Reply on WhatsApp instead.'); return; }   /* S871 */
  if(!confirm('''))

CC.append(('''/* S747: your review buttons -- one POST each;''',
           '''/* S871: a Call button for a number abroad is not shown (the clinic line cannot ring it). */
document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('button[onclick^="callBack("]').forEach(function(b){var m=(b.getAttribute('onclick')||'').match(/callBack[(]'([^']*)'/);if(m&&m[1].replace(/[^0-9]/g,'').length>10)b.style.display='none';});});
/* S747: your review buttons -- one POST each;'''))


def apply(text, pairs, name):
    for i, (old, new) in enumerate(pairs, 1):
        n = text.count(old)
        if n != 1:
            raise SystemExit("STOP: %s anchor %d found %d times (want 1) -- nothing written" % (name, i, n))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    res = {}
    for name, pairs in (("portal_inbox.py", PI), ("calls_console.py", CC)):
        raw = open(os.path.join(src, name), "rb").read()
        md5 = hashlib.md5(raw).hexdigest()
        if md5 != FROM[name]:
            raise SystemExit("STOP: %s is %s, not the FROM %s -- nothing written" % (name, md5, FROM[name]))
        res[name] = apply(raw.decode("utf-8"), pairs, name)
    os.makedirs(out, exist_ok=True)
    for name, text in res.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("%s %s" % (hashlib.md5(text.encode("utf-8")).hexdigest(), name))


if __name__ == "__main__":
    main()

#!/usr/bin/python3
# make_s801.py -- kit S801_WA_LIST_MOBILES (S437, 12-Nov-2026, the parent). Usage: make_s801.py <live wa_ladder.py> <out dir>
# S798's list read the mobile from finance.db patient_ref.mobile -- empty on the box (the installer's own line: "no mobile 27").
# The full mobiles are in the Call Console's patient mirror, /root/wa/console.db table patients (phone10, patient_uid, clinic_id),
# rebuilt every 10 minutes. Exact replacements on the live bytes (wa_ladder.py 8b6bd641 -- S798); every anchor must occur once.
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("8b6bd641"), "not the live wa_ladder.py (8b6bd641)"
t = b.decode("utf-8")
def rp(a, n):
    global t
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    t = t.replace(a, n)
rp('VERSION = "S798 1.1"\n', 'VERSION = "S801 1.2"\n')
rp('''OLD_OPTOUT = os.environ.get("WA_LADDER_OLD_OPTOUT", "/root/wa/wa_opt_outs.csv")
''', '''OLD_OPTOUT = os.environ.get("WA_LADDER_OLD_OPTOUT", "/root/wa/wa_opt_outs.csv")
CONSOLE_DB = os.environ.get("WA_LADDER_CONSOLE_DB", "/root/wa/console.db")     # S801: the Call Console's patient mirror
''')
rp('''READS (read-only): finance.db -- dx_visit (the follow-up date given at each visit), patient_visit (who came, when),
patient_ref (name, mobile), online_booking; the WhatsApp Inbox's store (incoming messages); the older opt-out file.
''', '''READS (read-only): finance.db -- dx_visit (the follow-up date given at each visit), patient_visit (who came, when),
patient_ref (name), online_booking; the Call Console's patient mirror /root/wa/console.db (the FULL mobile, by clinic ID or
patient key -- S801: patient_ref keeps the last four digits only); the WhatsApp Inbox's store; the older opt-out file.
''')
rp('''  * no plain 10-digit mobile on record -> held;  the number is on the stop list -> held;
''', '''  * no plain 10-digit mobile on record, or more than one -> held;  the number is on the stop list -> held;
''')
rp('''# ------------------------------------------------------------------ the day's lists
def _d(s):
''', '''# ------------------------------------------------------------------ the mobiles (S801)
def _key(v):
    s = str(v if v is not None else "").strip()
    return s[:-2] if re.match(r"^\\d+\\.0$", s) else s


def console_mobiles():
    """({clinic_id: {mobiles}}, {patient_uid: {mobiles}}, error) from the Call Console's patient mirror, read-only."""
    by_cid, by_uid = {}, {}
    if not os.path.exists(CONSOLE_DB):
        return by_cid, by_uid, "the Call Console's patient list is not at %s" % CONSOLE_DB
    try:
        con = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB, uri=True, timeout=10)
        try:
            for ph, uid, cid in con.execute("SELECT phone10, patient_uid, clinic_id FROM patients"):
                mob = m10(ph)
                if not mob:
                    continue
                if _key(cid):
                    by_cid.setdefault(_key(cid), set()).add(mob)
                if _key(uid):
                    by_uid.setdefault(_key(uid), set()).add(mob)
        finally:
            con.close()
    except sqlite3.Error as e:
        return {}, {}, "the Call Console's patient list could not be read (%s)" % type(e).__name__
    return by_cid, by_uid, ""


# ------------------------------------------------------------------ the day's lists
def _d(s):
''')
rp('''        today_vis = [r[0] or "" for r in con.execute("SELECT DISTINCT clinic_id FROM patient_visit WHERE visit_date=?", (day,))]
''', '''        today_vis = [(r[0] or "", r[1] or "") for r in con.execute("SELECT DISTINCT clinic_id, patient_uid FROM patient_visit WHERE visit_date=?", (day,))]
''')
rp('''    def person(cid, date):
        name, mob, l4 = ref.get(cid, ("", "", ""))
        return {"name": name or "?", "cid": cid or "", "mobile": mob, "last4": l4, "date": _nice(date), "hold": "", "tick": False}
''', '''    c_cid, c_uid, c_err = console_mobiles()

    def person(cid, date, uid=""):
        name, mob, l4 = ref.get(cid, ("", "", ""))
        many = 0
        if not mob:                                                    # S801: patient_ref has no full mobile -> the Call Console's list
            cand = c_cid.get(_key(cid)) or c_uid.get(_key(uid)) or set()
            if len(cand) == 1:
                mob = next(iter(cand))
            elif len(cand) > 1:
                many = len(cand)
        return {"name": name or "?", "cid": cid or "", "mobile": mob, "last4": l4, "date": _nice(date), "hold": "", "tick": False, "many": many}
''')
rp('''        raw[k].append(person(cid, fu))
    for cid in today_vis:
        raw["post_visit"].append(person(cid, day))
''', '''        raw[k].append(person(cid, fu, uid))
    for cid, uid in today_vis:
        raw["post_visit"].append(person(cid, day, uid))
''')
rp('''            raw["appt"].append({"name": name or "?", "cid": "", "mobile": mob, "last4": mob[-4:], "date": _nice(at), "hold": "", "tick": False})
''', '''            raw["appt"].append({"name": name or "?", "cid": "", "mobile": mob, "last4": mob[-4:], "date": _nice(at), "hold": "", "tick": False, "many": 0})
''')
rp('''            elif not mob:
                r["hold"] = "no mobile number on record"
''', '''            elif not mob:
                r["hold"] = ("%d different mobiles on record" % r["many"]) if r.get("many") else "no mobile number on record"
''')
rp('''    fresh.update({"stop_scan": "", "stop_error": st_err, "stop_error_at": "", "stop_stale": True})
''', '''    fresh.update({"stop_scan": "", "stop_error": st_err, "stop_error_at": "", "stop_stale": True, "mobile_error": c_err})
''')
rp('''  document.getElementById('lis').innerHTML=L?'<div class="err">'+esc(L)+'</div>':'';
''', '''  var MB=f.mobile_error?'The patient mobile numbers could not be read: '+f.mobile_error+'. Tell Claude.':'';
  document.getElementById('lis').innerHTML=(L?'<div class="err">'+esc(L)+'</div>':'')+(MB?'<div class="err">'+esc(MB)+'</div>':'');
''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
with open(os.path.join(out, "portal", "wa_ladder.py"), "wb") as fh:
    fh.write(t.encode("utf-8"))
print("wa_ladder.py", hashlib.md5(t.encode("utf-8")).hexdigest())

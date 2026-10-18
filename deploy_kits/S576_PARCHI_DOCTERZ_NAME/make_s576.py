#!/usr/bin/env python3
"""make_s576.py -- kit S576_PARCHI_DOCTERZ_NAME (S319, 18-Oct-2026). Builds the new /root/finance/slip_log.py from the
live bytes (FROM 87f07d57) by two counted, anchored edits. Each anchor must occur exactly once or nothing is written.
    python3 make_s576.py <FROM slip_log.py> <OUT slip_log.py>"""
import hashlib, sys
FROM = "87f07d57f61a5c0e031d6ff0f01585d0"
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM:
    sys.exit("FROM md5 is %s, expected %s -- refusing" % (hashlib.md5(b).hexdigest(), FROM))
s = b.decode("utf-8")
EDITS = [
 ('# ---------------------------------------------------------------- the patient master\ndef patient(con, clinic_id):',
  '# ---------------------------------------------------------------- the patient master\n'
  'def _s576_norm(n):\n'
  '    """S576: names compared without case or extra spaces."""\n'
  '    return " ".join(str(n or "").upper().split())\n'
  '\n'
  '\n'
  'def _docterz_newest_name(con, clinic_id):\n'
  '    """S576 -- THE OWNER, 17-Oct-2026: the parchi showed, for one Docterz ID, the name that ID carried on its first\n'
  '    visit, while Docterz had used another name on every visit since. The master (the tracker\'s Patient_Master_Join,\n'
  '    refreshed by finance_patient_sync) keeps the first name it saw. Docterz is the record: its newest day line for the\n'
  '    ID names the person. \'\' when Docterz has no line for the ID. Never raises."""\n'
  '    try:\n'
  '        d = con.execute("SELECT patient FROM clinic_day_line WHERE clinic_id=? AND patient<>\'\' "\n'
  '                        "ORDER BY business_date DESC LIMIT 1", (clinic_id,)).fetchone()\n'
  '    except Exception:                                    # noqa: BLE001 -- no Docterz table on this box\n'
  '        return ""\n'
  '    return ((d[0] if d else "") or "").strip()\n'
  '\n'
  '\n'
  'def patient(con, clinic_id):'),
 ('    if r:\n        return (r["name"] or "", r["phone_last4"] or "")\n',
  '    if r:\n'
  '        name = r["name"] or ""\n'
  '        newest = _docterz_newest_name(con, clinic_id)    # S576: Docterz\'s newest name wins when it differs\n'
  '        if newest and _s576_norm(newest) != _s576_norm(name):\n'
  '            name = newest\n'
  '        return (name, r["phone_last4"] or "")\n'),
]
for old, new in EDITS:
    n = s.count(old)
    if n != 1:
        sys.exit("anchor found %d times (must be 1): %r" % (n, old[:60]))
    s = s.replace(old, new)
open(out, "wb").write(s.encode("utf-8"))
print("built", out, hashlib.md5(s.encode("utf-8")).hexdigest(), "2 edits")

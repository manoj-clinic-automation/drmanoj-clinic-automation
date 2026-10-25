#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s652.py -- builds kit S652_SHAVEZ_PROCROOM_LINE's two files from the LIVE bytes (S650's TO, installed 10:03 IST 25-Oct).

  python3 make_s652.py <dir holding the live aaj_duties.json and aaj_seed.py> <out dir>

  aaj_duties.json  1 edit : one 'fetch' line, shavez.procroom_morning, asking the Scan App chat's S648 door
                            GET /scanapp/procroom/morning/api/open (fields open / text) -- shipped as aaj_duties.json.kit
  aaj_seed.py      1 edit : Shavez's line after his attendance check, in his first section, on
Each base must be the pinned live file and each piece must occur exactly once, or nothing is written."""
import hashlib
import os
import sys

BASE = {"aaj_duties.json": "90219853b4a25b051fa3f53f6c09d74d", "aaj_seed.py": "64d9a607fda40b34a96ed72fa688979b"}

D_OLD = '''   "fetch": {"url": "/register/attcorr/api/line", "field": "check_open", "text_field": "check_text"}
  }
 ]
}'''
D_NEW = '''   "fetch": {"url": "/register/attcorr/api/line", "field": "check_open", "text_field": "check_text"}
  },
  {
   "id": "shavez.procroom_morning",
   "person": "shavez",
   "kind": "fetch",
   "group": "open",
   "hi": "Kal ke procedures: kit bhariye aur Save kijiye",
   "en": "Shavez: yesterday's procedure slips to fill on Kal ke procedures, back to 01-10-2026 (S652; read on the page from the Scan App's own door, S648)",
   "tile": "Kal ke procedures",
   "door": "/scanapp/procroom/morning",
   "fetch": {"url": "/scanapp/procroom/morning/api/open", "field": "open", "text_field": "text"}
  }
 ]
}'''
S_OLD = """            {'id': 'shavez.attcorr_check',                     # S650 (D786, 25-Oct-2026): after reception saves
             'hi': 'Attendance correction check kijiye',
             'en': "After reception saves: checks the month's attendance corrections against the signed sheet.",
             'when': 'first',
             'on': True,
             'opens': 'Staff Register'}]},"""
S_NEW = """            {'id': 'shavez.attcorr_check',                     # S650 (D786, 25-Oct-2026): after reception saves
             'hi': 'Attendance correction check kijiye',
             'en': "After reception saves: checks the month's attendance corrections against the signed sheet.",
             'when': 'first',
             'on': True,
             'opens': 'Staff Register'},
            {'id': 'shavez.procroom_morning',                  # S652 (25-Oct-2026): the Scan App's door (S648) says how many days wait
             'hi': 'Kal ke procedures: kit bhariye aur Save kijiye',
             'en': "Yesterday's procedure slips: fills the kit used on Kal ke procedures and saves (every day still open since 1 October).",
             'when': 'first',
             'on': True,
             'opens': 'Kal ke procedures'}]},"""
EDITS = {"aaj_duties.json": [(D_OLD, D_NEW)], "aaj_seed.py": [(S_OLD, S_NEW)]}
OUTNAME = {"aaj_duties.json": "aaj_duties.json.kit"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for name, edits in EDITS.items():
        raw = open(os.path.join(src, name), "rb").read()
        if md5(raw) != BASE[name]:
            sys.exit("STOP: %s is %s, not the pinned live %s -- nothing written" % (name, md5(raw)[:8], BASE[name][:8]))
        txt = raw.decode("utf-8")
        for i, (old, new) in enumerate(edits, 1):
            n = txt.count(old)
            if n != 1:
                sys.exit("STOP: %s edit %d: the piece occurs %d times, not once -- nothing written" % (name, i, n))
            txt = txt.replace(old, new, 1)
        b = txt.encode("utf-8")
        open(os.path.join(out, OUTNAME.get(name, name)), "wb").write(b)
        print("%-16s %s -> %s  %d counted edit(s)" % (name, BASE[name][:8], md5(b), len(edits)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s615.py -- kit S615 (session S336, 22-Oct-2026): exact, counted edits turning the live
/root/state_backup/clinic_state_backup.py (S476, be57fe75) into the S615 file.
    python3 edits_s615.py LIVE OUT [KIT]   (exit 0 only if every anchor occurs once and OUT = KIT)

THE GAP (AF-19, S608, F-972): three things on the server were in NO backup -- every inclusion list read
(this file's SRC_FILES / SRC_DIRS / SRC_TREES; code_bundle.py takes root/wa *.py and *.sh only and names
att_config.py as excluded; sheets_pull, assetapp, petty, gas_export and the finance backup hold their own stores):
  /root/wa/wa_logs/               every incoming WhatsApp push, one YYYY-MM-DD.jsonl a day (the inbox reads it)
  /root/wa/wa_inbox/send_log.jsonl  every WhatsApp send with MyOperator's answer (S608, live 21-Oct)
  /root/att_config.py             the attendance settings, secrets included -- so the ENCRYPTED bundle, never code
They join the encrypted nightly (01:50): the same encryption, read-back and refusal stances as everything else here.
"""
import hashlib
import sys

EDITS = [
    ('    "/root/portal/clinic_users.json",\n]\n',
     '    "/root/portal/clinic_users.json",\n'
     '    # S615 (F-972, S608), 22-Oct-2026: two files in no backup at all. att_config.py holds the attendance settings\n'
     '    # WITH their secrets -- which is why it is here, inside the encrypted bundle, and named out of the code bundle.\n'
     '    # send_log.jsonl is every WhatsApp send and MyOperator\'s answer (the inbox\'s send log, live 21-Oct).\n'
     '    "/root/att_config.py",\n'
     '    "/root/wa/wa_inbox/send_log.jsonl",\n'
     ']\n'),
    ('    "/root/finance/spine/orders",\n]\nTREE_SKIP_PARTS',
     '    "/root/finance/spine/orders",\n'
     '    # S615 (AF-19), 22-Oct-2026: every incoming WhatsApp push, one YYYY-MM-DD.jsonl a day -- the recovery safety\n'
     '    # net the inbox reads forward from. Patient messages: encrypted here like the case pack. A TREE, ONE source.\n'
     '    "/root/wa/wa_logs",\n'
     ']\nTREE_SKIP_PARTS'),
]


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edits applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""make_s896.py -- how kit S896's two PC files were made from the live bytes (exact anchors). python3 make_s896.py <live_dir> <out_dir>"""
import hashlib, os, sys
L, K = sys.argv[1], sys.argv[2]
def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()[:8]
def rep(s, old, new):
    assert s.count(old)==1, old[:50]; return s.replace(old,new)
p=os.path.join(L,"docterz_pickup.py"); assert md5(p)=="ddbed001", md5(p)
s=open(p,encoding="utf-8").read()
s=rep(s,'VERSION = "S892 (S239 rev 4)"','VERSION = "S896 (S239 rev 5)"')
s=rep(s,'NAME_PREFIXES = ("consultation_report", "followup_logs", "clinical_data_report")\n',
      'NAME_PREFIXES = ("consultation_report", "followup_logs", "clinical_data_report")\n'
      'SPARE_FLAG = "_SPARE_MODE.txt"      # S896: present in the archive folder -> this PC runs as the spare and SENDS NOTHING\n')
s=rep(s,'''        p = Pass(a.tracker, a.downloads, a.archive, dry_run=a.dry_run)
        return p.refresh_latest() if a.refresh_latest else p.run()
''','''        p = Pass(a.tracker, a.downloads, a.archive, dry_run=a.dry_run)
        if os.path.exists(os.path.join(a.archive, SPARE_FLAG)):
            # S896 (the plan of 20-Nov-2026, section 5): the server makes the lists from the switch evening. This PC keeps
            # fetching, running, archiving and making its list and ledgers -- the undo -- and sends nothing: not the
            # call sheet, not the patient join, not the Sheet. Remove the flag file and it sends again as before.
            p.vps_upload = lambda path, timeout=30: (True, "SPARE MODE: %s not sent (the server makes the list)" % os.path.basename(path))
            p.patient_push = lambda: (True, ["SPARE MODE: the patient join is not sent (the server makes it)"])
            p.say("SPARE MODE (%s present): this PC sends nothing" % SPARE_FLAG)
            if a.refresh_latest:
                return p.refresh_latest(sheet_push=lambda path: (True, ["SPARE MODE: the Sheet is not written from this PC"]))
            return p.run()
        return p.refresh_latest() if a.refresh_latest else p.run()
''')
open(os.path.join(K,"docterz_pickup.py"),"w",encoding="utf-8",newline="").write(s); print("docterz_pickup.py", md5(os.path.join(K,"docterz_pickup.py")))
p=os.path.join(L,"watch_and_push_followups.py"); assert md5(p)=="8561f3d7", md5(p)
s=open(p,encoding="utf-8").read()
s=rep(s,'PATTERN = "Staff_Action_Today_*.xlsx"\n','PATTERN = "Staff_Action_Today_*.xlsx"\n'
      '# S896: with this file present the PC is the spare -- a new workbook is noted and marked seen, never pushed.\n'
      'SPARE_FLAG = r"D:\\Downloads\\DocterzArchive\\_SPARE_MODE.txt"\n')
s=rep(s,'''def run_push(filepath):
    """Run the proven push script against this exact file. Return True on success."""
    if not os.path.exists(PUSH_SCRIPT):''','''def run_push(filepath):
    """Run the proven push script against this exact file. Return True on success."""
    if os.path.exists(SPARE_FLAG):
        log("SPARE MODE: %s not pushed (the server makes the list)" % os.path.basename(filepath))
        return True
    if not os.path.exists(PUSH_SCRIPT):''')
open(os.path.join(K,"watch_and_push_followups.py"),"w",encoding="utf-8",newline="").write(s); print("watch_and_push_followups.py", md5(os.path.join(K,"watch_and_push_followups.py")))

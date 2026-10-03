#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""pack_medical_kit.py -- kit S458_MEDICAL_PC_KIT. Packs the Medical PC's reinstall kit FROM THAT PC'S OWN FILES, as the
owner's PC mirrors them (D:\Downloads\margsync\medical_SendToClinic -- the pull refreshes it every ten minutes).
Nothing is read from a kit folder and nothing on the Medical PC is touched: the kit holds what the working PC runs.

    python3 -B pack_medical_kit.py <mirror folder> <deploy_kits folder> [YYYY-MM-DD]

Writes <deploy_kits>/PC_KITS/medical/kit.zip and KIT_INFO.txt. The zip is byte-reproducible for a given day.
Run again after the Sanjeevni side changes a tool on that PC (the mirror must show the new file first).
"""
import datetime
import hashlib
import io
import os
import sys
import zipfile

# the tools the working PC needs; a name that is not in the mirror stops the pack
TOOLS = ["medical_agent.py", "agent_guard.py", "START_AGENT.cmd", "ENABLE_AGENT_THIS_ACCOUNT.bat",
         "marg_watch.py", "marg_txt.py", "marg_push.py", "MARG_TXT_LIVE.txt",
         "xlsx_stdlib.py", "medical_census.py",
         "SEND_TO_CLINIC.bat",
         "TURN_OFF_ALL.bat", "TURN_ON_ALL.bat",
         "find_sale_report.ps1", "marg_export_macro_v3.ahk", "marg_macro_calib.txt"]
# NOT PACKED, on purpose: GUARD_AND_SEND.bat, guard_and_send.py, marg_report.py -- the August manual send, retired when the
# agent began pushing by itself (S240/S259); and marg_report.py on that PC carries two real numbers with names in its
# worked examples, which no kit in the repository may hold (F-185).
FOLDERS = ["xlrd"]                       # taken whole (the .xls reader the text route uses)
NEVER = ("token.txt",)
OWN = ["setup_pc.py", "README_REINSTALL_MEDICAL.txt"]
PY_FILE = "pyportable_3.11.9.zip"


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) not in (3, 4):
        print(__doc__)
        return 2
    mirror, kits = os.path.abspath(argv[1]), os.path.abspath(argv[2])
    day = datetime.date.fromisoformat(argv[3]) if len(argv) == 4 else datetime.date.today()
    here = os.path.dirname(os.path.abspath(__file__))
    files = {}
    for n in TOOLS:
        p = os.path.join(mirror, n)
        if not os.path.isfile(p):
            print("STOP: %s is not in the mirror %s" % (n, mirror))
            return 1
        files["payload/" + n] = open(p, "rb").read()
    for d in FOLDERS:
        base = os.path.join(mirror, d)
        got = 0
        for root, _dirs, names in os.walk(base):
            if "__pycache__" in root:
                continue
            for n in sorted(names):
                if n.endswith((".pyc", ".pyo")):
                    continue
                rel = os.path.relpath(os.path.join(root, n), mirror).replace(os.sep, "/")
                files["payload/" + rel] = open(os.path.join(root, n), "rb").read()
                got += 1
        if not got:
            print("STOP: the folder %s is not in the mirror" % d)
            return 1
    assert not any(os.path.basename(k) in NEVER for k in files), "a secret is in the list"
    for n in OWN:
        raw = open(os.path.join(here, n), "rb").read()
        if n.endswith(".txt"):                               # a README is read in Notepad
            raw = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        files[n] = raw
    sums = "".join("%s  %s\n" % (md5b(files[k]), k) for k in sorted(files))
    files["MD5SUMS.txt"] = sums.encode("ascii")
    buf = io.BytesIO()
    stamp = (day.year, day.month, day.day, 12, 0, 0)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for k in sorted(files):
            zi = zipfile.ZipInfo(k, date_time=stamp)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zi.create_system = 3
            z.writestr(zi, files[k], compresslevel=6)
    data = buf.getvalue()
    out = os.path.join(kits, "PC_KITS", "medical")
    os.makedirs(out, exist_ok=True)
    py = os.path.join(kits, "PC_KITS", "_shared", PY_FILE)
    if not os.path.isfile(py):
        print("STOP: %s is not there" % py)
        return 1
    newest = max(os.path.getmtime(os.path.join(mirror, n)) for n in TOOLS)
    info = ("# deploy_kits/PC_KITS/medical -- the Medical PC's setup kit, as the Clinic PCs page serves it (kit S458).\n"
            "# kit.zip = setup_pc.py, its README and payload/: the tools exactly as that PC ran them when the kit was packed\n"
            "# (read from the owner's PC's mirror of D:\\SendToClinic). The installer only fills what is missing. The bundled\n"
            "# Python is deploy_kits/PC_KITS/_shared/<python_file>. No secret (token.txt is never packed), no patient, no number.\n"
            "version=installer %s; the tools as on that PC, newest dated %s\n"
            "packed=%s\nkit_md5=%s\npython_file=%s\npython_md5=%s\n"
            % ("S458.1", datetime.date.fromtimestamp(newest).strftime("%d-%b-%Y"), day.strftime("%d-%b-%Y"),
               md5b(data), PY_FILE, md5b(open(py, "rb").read())))
    with open(os.path.join(out, "kit.zip"), "wb") as fh:
        fh.write(data)
    with open(os.path.join(out, "KIT_INFO.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write(info)
    print("kit.zip %s  %d bytes  %d files (%d tools)" % (md5b(data), len(data), len(files), sum(1 for k in files if k.startswith("payload/"))))
    for k in sorted(files):
        if k.startswith("payload/") and "/xlrd/" not in k:
            print("   %s  %s" % (md5b(files[k])[:8], k[8:]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

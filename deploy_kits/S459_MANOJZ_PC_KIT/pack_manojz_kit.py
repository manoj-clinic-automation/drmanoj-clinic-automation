#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""pack_manojz_kit.py -- kit S459_MANOJZ_PC_KIT. Packs Dr Manoj's PC's setup kit for the Clinic PCs page: the installer and
its README only. This PC's state is NOT in the kit -- the 03:10 nightly zips it to the SSD and the installer restores from there.

    python3 -B pack_manojz_kit.py <deploy_kits folder> [YYYY-MM-DD]

Writes <deploy_kits>/PC_KITS/manojz/kit.zip and KIT_INFO.txt. The zip is byte-reproducible for a given day.
"""
import datetime
import hashlib
import io
import os
import sys
import zipfile

OWN = ["setup_pc.py", "README_REINSTALL_MANOJZ.txt"]
PY_FILE = "pyportable_3.11.9.zip"


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    kits = os.path.abspath(argv[1])
    day = datetime.date.fromisoformat(argv[2]) if len(argv) == 3 else datetime.date.today()
    here = os.path.dirname(os.path.abspath(__file__))
    files = {}
    for n in OWN:
        raw = open(os.path.join(here, n), "rb").read()
        if n.endswith(".txt"):
            raw = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        files[n] = raw
    files["MD5SUMS.txt"] = "".join("%s  %s\n" % (md5b(files[k]), k) for k in sorted(files)).encode("ascii")
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
    py = os.path.join(kits, "PC_KITS", "_shared", PY_FILE)
    if not os.path.isfile(py):
        print("STOP: %s is not there" % py)
        return 1
    out = os.path.join(kits, "PC_KITS", "manojz")
    os.makedirs(out, exist_ok=True)
    info = ("# deploy_kits/PC_KITS/manojz -- Dr Manoj's PC's setup kit, as the Clinic PCs page serves it (kit S459).\n"
            "# kit.zip = setup_pc.py and its README. It holds no data and no secret: the installer restores this PC's state\n"
            "# from the newest nightly zip on the SSD (F:\\ClinicBackup\\DrManojClinic_Automation\\05_PC_STATE\\manojz) and only\n"
            "# puts back what is not there. The bundled Python (deploy_kits/PC_KITS/_shared/<python_file>) only runs the installer.\n"
            "version=installer S459.1; restores from the nightly state copy on the SSD\n"
            "packed=%s\nkit_md5=%s\npython_file=%s\npython_md5=%s\n"
            % (day.strftime("%d-%b-%Y"), md5b(data), PY_FILE, md5b(open(py, "rb").read())))
    with open(os.path.join(out, "kit.zip"), "wb") as fh:
        fh.write(data)
    with open(os.path.join(out, "KIT_INFO.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write(info)
    print("kit.zip %s  %d bytes  %d files" % (md5b(data), len(data), len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

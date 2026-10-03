#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s460.py -- kit S460_CLINIC_PCS_TWO_MORE. The Clinic PCs page of the kit's pc_kits.py (--new) beside the one
being replaced (--old), on scratch copies of the kits, with made-up logins. Nothing live is read or written.
Last line:  WALK_S460 GREEN <n> checks  or  WALK_S460 RED.

    python3 -B walk_s460.py --new built/pc_kits.py --old /root/finance/pc_kits.py --kits <deploy_kits>/PC_KITS
"""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import sys
import tempfile

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("  ok  " if cond else "  FAIL", name, ("  -- " + str(detail)[:300]) if (detail and not cond) else ""))


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--kits", required=True)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="s460_walk_")
    try:
        return walk(a, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def walk(a, tmp):
    kits = os.path.join(tmp, "PC_KITS")
    shutil.copytree(a.kits, kits)
    os.environ["PC_KITS_ROOT"] = kits
    os.environ["PC_KIT_CODES"] = os.path.join(tmp, "codes.json")
    os.environ["PC_KIT_LOG"] = os.path.join(tmp, "log.txt")
    os.environ["RECEPTION_KEYS"] = os.path.join(tmp, "reception_keys.txt")
    new, old = load(a.new, "pc_kits_new"), load(a.old, "pc_kits_old")
    from flask import Flask
    who = {"user": "manoj", "role": "doctor"}
    state = {"login": True}
    app = Flask("walk_s460")
    new.init(app, lambda: None, lambda need: (who, None) if state["login"] else (None, "no"),
             lambda con: {"checks": [{"key": k, "state": "ok", "detail": "fine", "hint": ""} for k in ("reception", "watcher", "pipeline")]})
    c = app.test_client()

    # 1. the Reception PC's road is untouched
    info_r = new.kit_info("reception")
    check("the three kits on the scratch copy are whole", all(new.kit_info(p) for p in ("reception", "medical", "manojz")),
          [p for p in ("reception", "medical", "manojz") if not new.kit_info(p)])
    code = "A" * 32
    check("the Reception PC's setup file is byte for byte what it was", info_r and new.setup_file("reception", code, info_r) == old.setup_file("reception", code, info_r))
    check("the Reception PC's entry is unchanged", new.PC_BY_ID["reception"] == old.PC_BY_ID["reception"])

    # 2. the two new setup files
    for pc, expect, others, pyhome, label, fname in (
            ("medical", "MEDICAL", ("RECEPTIONPC", "MANOJZ"), 'set "PYHOME=D:\\SendToClinic"', "the Medical PC", "ClinicSetup_Medical.cmd"),
            ("manojz", "MANOJZ", ("RECEPTIONPC", "MEDICAL"), 'set "PYHOME="', "Dr Manoj's PC", "ClinicSetup_DrManojPC.cmd")):
        info = new.kit_info(pc)
        raw = new.setup_file(pc, code, info) if info else b""
        text = raw.decode("ascii", "replace")
        check("%s: the setup file is plain letters, Windows line ends, nothing left to fill in" % pc,
              raw and all(b < 128 for b in raw) and b"\n" not in raw.replace(b"\r\n", b"") and not re.search(r"__[A-Z0-9]+__", text), re.findall(r"__[A-Z0-9]+__", text))
        check("%s: it carries its code, this server, its kit's md5 and the Python part's" % pc,
              all(x in text for x in ('set "CODE=%s"' % code, 'set "SRV=%s"' % new.SERVER_URL, 'set "KITMD5=%s"' % info["kit_md5"], 'set "PYMD5=%s"' % info["python_md5"])))
        check("%s: it expects %s, stops on the clinic's other PCs, and names itself '%s'" % (pc, expect, label),
              'if /i "%%PCNAME%%"=="%s" goto :go' % expect in text and ("in (%s)" % " ".join(others)) in text and expect not in text.split("do if")[0].split("in (")[-1]
              and "setting up %s" % label in text and "This file sets up %s only" % label in text, text[:900])
        check("%s: where that PC keeps its own Python" % pc, pyhome + "\r\n" in text, [l for l in text.splitlines() if "PYHOME=" in l])
        check("%s: it runs the kit's own installer and nothing else of ours" % pc, '"%PY%" -B "%W%\\kit\\setup_pc.py" --kit "%W%\\kit"' in text
              and "INSTALL_RECEPTION_AGENT" not in text and "--enroll" not in text and "share_setup" not in text)
        labels = set(re.findall(r"^:([A-Za-z0-9_]+)\s*$", text.replace("\r", ""), re.M))
        gotos = set(re.findall(r"goto :([A-Za-z0-9_]+)", text)) | set(re.findall(r"call :([A-Za-z0-9_]+)", text))
        check("%s: every jump in the file lands on a label that is there" % pc, gotos <= labels, sorted(gotos - labels))
        check("%s: no line has an odd number of quote marks" % pc, not [l for l in text.splitlines() if l.count('"') % 2 and not l.strip().lower().startswith("rem")],
              [l for l in text.splitlines() if l.count('"') % 2][:2])
        check("%s: the page names the file %s" % (pc, fname), new.PC_BY_ID[pc]["file"] == fname)

    # 3. the page and the button, as the owner presses them
    r = c.get("/finance/pcs")
    page = r.get_data(as_text=True)
    check("the page shows three buttons", r.status_code == 200 and page.count("<button type=submit>") == 3 and "/finance/pcs/setup/medical" in page and "/finance/pcs/setup/manojz" in page, page.count("<button"))
    check("...and says for each new PC what only a person can do", "the Marg engineer restores it" in page and "ClinicBackup SSD" in page)
    check("...and no longer says their kits are being packed", "is not on the server yet" not in page)
    for pc, fname in (("medical", "ClinicSetup_Medical.cmd"), ("manojz", "ClinicSetup_DrManojPC.cmd")):
        r = c.post("/finance/pcs/setup/" + pc, headers={"Sec-Fetch-Site": "same-origin"})
        body = r.get_data()
        m = re.search(rb'set "CODE=([A-Za-z0-9_-]{20,64})"', body)
        check("%s: the press hands out %s" % (pc, fname), r.status_code == 200 and fname in r.headers.get("Content-Disposition", "") and m is not None, r.status_code)
        kc = m.group(1).decode() if m else "x"
        r = c.get("/finance/api/pc-kit/fetch?part=kit", headers={"X-Kit-Code": kc})
        check("%s: its code fetches THAT PC's kit, whole" % pc, r.status_code == 200 and hashlib.md5(r.get_data()).hexdigest() == new.kit_info(pc)["kit_md5"], r.status_code)
        r = c.get("/finance/api/pc-kit/fetch?part=python", headers={"X-Kit-Code": kc})
        check("%s: ...and the Python part" % pc, r.status_code == 200 and hashlib.md5(r.get_data()).hexdigest() == new.kit_info(pc)["python_md5"], r.status_code)
        r = c.post("/finance/api/pc-kit/enroll", headers={"X-Kit-Code": kc}, json={"code": kc, "public_key": "ab" * 32, "computer": pc.upper()})
        check("%s: its code cannot put a key into the Reception PC's key list" % pc, r.status_code >= 400 and not os.path.exists(os.environ["RECEPTION_KEYS"]), r.status_code)
    r = c.get("/finance/api/pc-kit/fetch?part=kit", headers={"X-Kit-Code": "B" * 32})
    check("a code nobody was given fetches nothing", r.status_code == 401, r.status_code)
    r = c.post("/finance/pcs/setup/medical", headers={"Sec-Fetch-Site": "cross-site"})
    check("a press from another site is still refused", r.status_code == 403, r.status_code)
    r = c.post("/finance/pcs/setup/shavez", headers={"Sec-Fetch-Site": "same-origin"})
    check("a PC that is only planned has no kit to hand out", r.status_code == 404, r.status_code)
    state["login"] = False
    r = c.post("/finance/pcs/setup/medical", headers={"Sec-Fetch-Site": "same-origin"})
    check("without the owner's login there is no setup file", r.status_code == 403 and b"CODE=" not in r.get_data(), r.status_code)
    state["login"] = True
    with open(os.path.join(kits, "medical", "kit.zip"), "ab") as fh:
        fh.write(b"x")
    page = c.get("/finance/pcs").get_data(as_text=True)
    r = c.post("/finance/pcs/setup/medical", headers={"Sec-Fetch-Site": "same-origin"})
    check("a kit that is not the bytes KIT_INFO.txt names: its button goes, the other two stay, nothing is handed out",
          page.count("<button type=submit>") == 2 and "/finance/pcs/setup/medical" not in page and r.status_code == 404, (page.count("<button"), r.status_code))

    print("%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("   FAILED: " + f)
    print("WALK_S460 GREEN %d checks" % len(PASS) if not FAIL else "WALK_S460 RED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

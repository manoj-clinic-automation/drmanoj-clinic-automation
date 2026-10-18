#!/usr/bin/env python3
"""make_s579.py -- kit S579: builds the three edited live files from their PINNED live bytes, by exact counted edits.
    python3 make_s579.py <finance_app.py> <portal.py> <casepack_page.html> <out_dir>
Refuses (exit 1) if an input is not the pinned md5 or an anchor is not found exactly once; writes <out_dir>/<name> and prints
each output's md5, which must equal the kit's EXPECT lines (the installer compares). The fourth change, tile_grants.json, is a
data step in the installer (it is edited by other kits too, so it is merged, not replaced)."""
import hashlib
import os
import sys

PIN = {"finance_app.py": "87cc4266f9cd05f3633f23e1f36488a0",
       "portal.py": "f8b059f61fa8b885f024f4f4ce73e4f2",
       "casepack_page.html": "08807cdfbfd595f6425f5cc277a38dbb"}

MOUNT = '''# --- S514_VOICENOTES_INBOX end ---

# --- S579_SURGERY_CASES begin -- one record per surgery: papers, implants, vendors' ledgers, the hospital's payments (owner, 18-Oct-2026, D735) ---
# PARENT (clinic). Its own unit 'surgery' (shavez maker; the doctor checker -- the money pages his alone); its own surg_* tables, made
# on the first request (F-303), with the unit's row and its two logins. Reads patient_ref and the three bank-statement tables READ-ONLY.
# Papers are kept under /root/wa/casepack/surgery_papers (inside the Case Pack's tree, which the nightly encrypted backup carries).
# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import surgery_cases                                       # noqa: E402
    surgery_cases.init(app, db, require, audit, unit="surgery")
except Exception as _ex_sg:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('surgery_cases', repr(_ex_sg)[:200]))
    print("surgery_cases NOT mounted: %s" % _ex_sg, file=sys.stderr)
# --- S579_SURGERY_CASES end ---
'''

UNIT_OLD = '''        return "packs"       # S408: Month-end packs (the doctor checker) and Shavez's checklist (maker) -- PARENT (clinic), D624.
'''
UNIT_NEW = UNIT_OLD + '''    if path == "/finance/surgery" or path.startswith("/finance/surgery/"):
        return "surgery"     # S579: Surgery cases (owner, 18-Oct-2026, D735) -- shavez maker, the doctor checker; rows made by the installer.
'''

TILE_OLD = '''    {"icon": "\\U0001F4CB", "name": "Surgical Case Pack",
     "desc": "Estimate \\u00b7 OT list \\u00b7 consent \\u00b7 Ayushman", "live": True,
     "url": "/portal/casepack",
     "roles": ["doctor"]},
'''
TILE_NEW = TILE_OLD + '''    {"icon": "\\U0001F3E5", "name": "Surgery cases",
     # S579 NEW (owner, 18-Oct-2026, D735). PARENT (clinic). One record per surgery: the papers scanned (pre-approval to discharge,
     # X-rays, MLC, police memo), the implants, the vendors' ledgers and the hospital's payments. Its own server unit ('surgery':
     # shavez maker, the doctor checker). Granted by name in tile_grants.json to shavez; masked for bhawna (the owner: private to me).
     "desc": "Papers \\u00b7 implants \\u00b7 vendor ledgers \\u00b7 hospital payments", "live": True,
     "url": "/finance/surgery",
     "roles": ["doctor"]},
'''
GROUP_OLD = '''    "Surgical Case Pack": "Clinic", "Send WhatsApp": "Clinic",
'''
GROUP_NEW = GROUP_OLD + '''    "Surgery cases": "Clinic",                                   # S579
'''

CP_OLD = ("if(pbSel){ el.style.display='block'; el.textContent='✓ '+pbSel.Patient_Name+' · UID '+pbSel.Patient_UID+"
          "(pbSel.Clinic_Specific_Id?(' · CID '+pbSel.Clinic_Specific_Id):'')+(pbSel.Age?(' · '+pbSel.Age+'y'):''); "
          "document.getElementById('pb_clear').style.display='inline-block'; }")
CP_NEW = CP_OLD[:-1] + (
    " /* S579: the owner -- 'the casepack patient selection should have option to continue to this flow' */"
    " var _sg=document.createElement('a'); _sg.textContent=' → Continue to surgery case (papers · implants · payments)';"
    " _sg.href='#'; _sg.style.cssText='display:inline-block;margin-left:10px;color:var(--accent,#39b6ff);text-decoration:underline';"
    " _sg.onclick=function(ev){ ev.preventDefault(); var p='';"
    " try{ var e=chooseEstimate(); p=(e&&e.payer)||''; }catch(_e){}"
    " window.open('/finance/surgery/new?cid='+encodeURIComponent(pbSel.Clinic_Specific_Id||'')+'&name='+encodeURIComponent(pbSel.Patient_Name||'')"
    "+'&payer='+encodeURIComponent(p)+'&cp='+encodeURIComponent((window.loadedCase&&window.loadedCase.case_id)||''),'_blank'); };"
    " el.appendChild(_sg); }")


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, old, new, name):
    n = text.count(old)
    if n != 1:
        sys.exit("STOP: %s: an anchor is found %d times, not once" % (name, n))
    return text.replace(old, new)


def main(fa, po, cp, out):
    os.makedirs(out, exist_ok=True)
    res = {}
    for name, path in (("finance_app.py", fa), ("portal.py", po), ("casepack_page.html", cp)):
        b = open(path, "rb").read()
        if md5(b) != PIN[name]:
            sys.exit("STOP: %s is %s, not the pinned %s" % (path, md5(b), PIN[name]))
        t = b.decode("utf-8")
        if name == "finance_app.py":
            t = edit(t, "# --- S514_VOICENOTES_INBOX end ---\n", MOUNT, name)
            t = edit(t, UNIT_OLD, UNIT_NEW, name)
        elif name == "portal.py":
            t = edit(t, TILE_OLD, TILE_NEW, name)
            t = edit(t, GROUP_OLD, GROUP_NEW, name)
        else:
            t = edit(t, CP_OLD, CP_NEW, name)
        nb = t.encode("utf-8")
        open(os.path.join(out, name), "wb").write(nb)
        res[name] = md5(nb)
        print("%s %s" % (res[name], name))
    return res


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:5])

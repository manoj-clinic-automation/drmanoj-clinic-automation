#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_grants_s586.py -- S586_PORTAL_TILE_GROUPS (D739): the one edit to /root/portal/tile_grants.json, in place.

    python3 merge_grants_s586.py <tile_grants.json>            # edits the file; prints before/after md5 and version

Idempotent: running it twice changes nothing the second time. It never removes a grant or a mask line that is there
today -- it only ADDS:
  users.manoj.folders  = ["*"]                      -- every group folded into one tile with a submenu
  users.bhawna.folders = ["Staff"]                  -- only Staff folded; the rest flat
  users.bhawna.only    = the seven tiles' names     -- Kal ka hisaab, Physiotherapy, Petty book, Clinic, Report baaki,
                                                        OPD & X-ray/Proc Slips, and the four Staff tiles (one folder)
  users.bhawna.mask   += Patient records, Check karein   (his word, 15:48 IST 18-Oct)
  defaults.groups_by_role.staff = the new labels, work first and attendance last (his ruling of 03-Sep)
  version + 1, and a line in _note.
"only" and "folders" are DISPLAY ONLY: portal.py reads them to decide what a home screen SHOWS. Every page keeps its own gate.
"""
import sys, json, hashlib

BHAWNA_ONLY = ["Kal ka hisaab", "Physiotherapy", "Petty book", "Clinic", "Report baaki", "OPD & X-ray/Proc Slips",
               "Attendance", "Staff Register", "Salary — approve & lock", "Staff Ledger"]
STAFF_ORDER = ["Calls & WhatsApp", "Patients", "Docterz & clinic day", "Sanjeevni Medicos", "Assets & papers",
               "Accounts & month-end", "Staff"]
NOTE = (" | v%d (S586, 18-Oct-2026, D739, PARENT): the home screens regrouped. manoj: every group FOLDED into one tile that"
        " opens its submenu (folders ['*']). bhawna: 'only' her seven -- Kal ka hisaab, Physiotherapy, Petty book, Clinic,"
        " Report baaki, OPD & X-ray/Proc Slips and the Staff folder (Attendance, Staff Register, Salary, Staff Ledger);"
        " Patient records and Check karein masked at the owner's word. Staff section order renamed to the new labels."
        " Eight tiles retired in portal.py (UPI Sheet, Monthly Accounting, Vehicle Tracking, CC Statement Saver, Inbox Janitor,"
        " Revenue Reconciler, Case Pack PC fallback, CC Statements to Tally); Renewals opens /scanapp/renewals."
        " 'only' and 'folders' are display only -- nothing granted, nothing withdrawn, every page's own gate unchanged.")


def md5p(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = sys.argv[1]
    before = md5p(p)
    g = json.load(open(p, encoding="utf-8"))
    users = g.setdefault("users", {})
    changed = False

    m = users.setdefault("manoj", {})
    if m.get("folders") != ["*"]:
        m["folders"] = ["*"]; changed = True

    b = users.setdefault("bhawna", {})
    if b.get("folders") != ["Staff"]:
        b["folders"] = ["Staff"]; changed = True
    if b.get("only") != BHAWNA_ONLY:
        b["only"] = list(BHAWNA_ONLY); changed = True
    mask = b.setdefault("mask", [])
    for nm in ("Patient records", "Check karein"):
        if nm not in mask:
            mask.append(nm); changed = True

    d = g.setdefault("defaults", {})
    gbr = d.setdefault("groups_by_role", {})
    if gbr.get("staff") != STAFF_ORDER:
        gbr["staff"] = list(STAFF_ORDER); changed = True

    if changed:
        g["version"] = int(g.get("version", 0)) + 1
        if "S586" not in (g.get("_note") or ""):
            g["_note"] = (g.get("_note") or "") + (NOTE % g["version"])
        tmp = p + ".s586tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(g, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        import os
        os.replace(tmp, p)
    after = md5p(p)
    print("tile_grants.json  %s -> %s  version %s  %s" % (before[:8], after[:8], g.get("version"), "CHANGED" if changed else "already merged (nothing changed)"))


if __name__ == "__main__":
    main()

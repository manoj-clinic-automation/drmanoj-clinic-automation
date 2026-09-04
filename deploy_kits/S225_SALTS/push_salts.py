#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
push_salts.py -- S225 §8 item 6 (manojz leg): Amir's salt WORK LIST goes server-side, once.

Reads D:\Downloads\Sanjeevni_Salt_Fix_for_Amir.xlsx -- the S207 work list built from Dr Manoj's answers of 28-Aug
(sheets: 1 Rename salts · 2 Create salts · 3 Change items · 5 Waiting · 6 Cleanups; sheet 4 "Already correct" is
not a task and is not sent) -- plus the salt names from D:\Downloads\margsync\_analysis\Sanjeevni_Salt_Corrections.xlsx
sheet 2 (for the doctor's dropdown on the 7 waiting rows), and POSTs them through the /vendors machine door (the
one the finance front gate already opens to the manojz token). A DONE tick or an answer already on the server is
never overwritten by a later push.

Run on manojz:   python -B push_salts.py        (--dry-run to look only)
Needs openpyxl (on manojz since S198) and the S224_MARG_PURCHASES kit beside this one (token + door).
"""
import hashlib, io, os, sys, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(KITS, "S224_MARG_PURCHASES"))
DEF_XLSX = os.environ.get("SALT_FIX_XLSX", r"D:\Downloads\Sanjeevni_Salt_Fix_for_Amir.xlsx")
DEF_NAMES = os.environ.get("SALT_NAMES_XLSX", r"D:\Downloads\margsync\_analysis\Sanjeevni_Salt_Corrections.xlsx")
DEF_BASE = "https://followup.dr-manoj.in/finance/purchase/api"
SHEETS = (("1 Rename salts", "rename", "Old name"), ("2 Create salts", "create", "Salt name to create"),
          ("3 Change items", "change", "Item"), ("5 Waiting", "waiting", "Item"), ("6 Cleanups", "cleanup", "What"))


def read_tasks(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    tasks = []
    for sheet, section, first_hdr in SHEETS:
        if sheet not in wb.sheetnames:
            continue
        rows = [r for r in wb[sheet].iter_rows(values_only=True)]
        hi = next((i for i, r in enumerate(rows) if r and r[0] and str(r[0]).strip().startswith(first_hdr)), None)
        if hi is None:
            continue
        seq = 0
        for r in rows[hi + 1:]:
            if not r or r[0] is None or not str(r[0]).strip():
                continue
            seq += 1
            tasks.append(dict(section=section, seq=seq, a=str(r[0]).strip(), b=str(r[1] or "").strip() if len(r) > 1 else "",
                              c=str(r[2] or "").strip() if len(r) > 2 and section != "waiting" else ""))
    return tasks


def read_names(path):
    if not os.path.exists(path):
        return []
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if len(wb.sheetnames) < 2:
        return []
    out = []
    for r in wb[wb.sheetnames[1]].iter_rows(values_only=True):
        if r and r[0] and not str(r[0]).startswith("Every salt"):
            s = str(r[0]).strip()
            if s and s not in out:
                out.append(s)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--dry-run" in argv
    if not os.path.exists(DEF_XLSX):
        print("salts: work list not found: %s" % DEF_XLSX)
        return 2
    tasks = read_tasks(DEF_XLSX)
    names = read_names(DEF_NAMES)
    md5 = hashlib.md5(io.open(DEF_XLSX, "rb").read()).hexdigest()
    by = {}
    for t in tasks:
        by[t["section"]] = by.get(t["section"], 0) + 1
    print("salts: %d task(s) -- %s; %d salt names for the dropdown; work list %s" % (len(tasks), ", ".join("%s %d" % kv for kv in sorted(by.items())), len(names), md5[:8]))
    if not tasks:
        return 2
    if dry:
        print("salts: dry run -- nothing sent")
        return 0
    import push_purchases as PP
    tok, where = PP.read_token()
    if not tok:
        print("salts: no token available -- nothing sent")
        return 2
    try:
        st, body = PP._post(DEF_BASE + "/vendors", {"pairs": {}, "salt_tasks": tasks, "salts": names, "source": os.path.basename(DEF_XLSX),
                                                    "source_md5": md5, "host": "manojz"}, tok)
    except urllib.error.HTTPError as e:
        print("salts: server said %s -- nothing recorded" % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("salts: could not reach the server (%s)" % e.__class__.__name__)
        return 2
    print("salts: sent (token from %s), server %s: %s" % (where, st, body))
    return 0


if __name__ == "__main__":
    sys.exit(main())

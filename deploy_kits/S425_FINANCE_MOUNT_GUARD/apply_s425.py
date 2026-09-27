#!/usr/bin/env python3
"""apply_s425.py -- kit S425_FINANCE_MOUNT_GUARD (session 284, 27-Sep-2026).

The hazard found when finance_app.py was read whole at S284: the FIRST twelve module mounts (S208 ... S241: stock_app,
darpan_app, staff_pages + joiner_app, returns_desk, finance_clinic_day, clinic_register, purchase_app, bank_mpr_status,
clinic_day_pdf, marg_door, amir_day) are bare imports -- a fault in any one of them takes the WHOLE finance app down
at start (every money page, the health page, the approvals). Every mount from S243 on is already guarded (S209):
"a fault inside a module must never take the console down".

This patch, on EXACT bytes only (FROM 7486f3e6, the S422 build) and predicted TO:
  1. `_MOUNT_FAILED = []` just before the first mount;
  2. each of the eleven old sections' code wrapped in try/except -- the same lines, indented, nothing else changed;
     a failure is printed to the journal (as the guarded ones do) AND recorded in _MOUNT_FAILED;
  3. ONE health-page row, 'Parts of the finance app that did not load' (key 'mounts'): RED naming the part when any
     mount failed (recorded, or a guarded module absent from sys.modules), green 'all N parts loaded' otherwise --
     so a guarded failure is loud on the page he reads instead of silent in a journal.
usage: apply_s425.py <finance_app.py>   (idempotent)"""
import hashlib
import re
import sys

FROM = "7486f3e652bdf777666af134da5b0054"
FIRST = "# --- S208_STOCK_LEDGER begin"
LAST_END = "# --- S241_AMIR_DAY end ---"
TAG = "# ---- S425: PARTS OF THE FINANCE APP THAT DID NOT LOAD"
GUARDED_LATER = ("darpan_kal", "reports_tile", "accountant_upi_cash", "clinic_money", "petty_book", "bank_sms",
                 "owner_sheets", "slip_log", "records", "freshness_page", "sale_check", "stockmatch", "porders", "packs")
OLD = ("stock_app", "darpan_app", "staff_pages", "joiner_app", "returns_desk", "finance_clinic_day", "clinic_register",
       "purchase_app", "bank_mpr_status", "clinic_day_pdf", "marg_door", "amir_day")
B2 = "    # ---- B2: THE NEVER-FIRED WITNESS"
ROW = '''    # ---- S425: PARTS OF THE FINANCE APP THAT DID NOT LOAD -------------------
    # Every module mount is guarded (S209, S425): a broken part no longer takes the app down -- so this row is
    # what keeps a broken part LOUD. Red names the part; the clinic-finance journal says why.
    try:
        _mf = [n for n, _w in (globals().get("_MOUNT_FAILED") or [])]
        _mf += [m for m in %r if m not in sys.modules and m not in _mf]
        _all = %d
        if _mf:
            add("mounts", "Parts of the finance app that did not load", "bad",
                "%%d of %%d did not load: %%s" %% (len(_mf), _all, ", ".join(_mf)),
                "Every other page keeps working. The reason is in the journal of clinic-finance.")
        else:
            add("mounts", "Parts of the finance app that did not load", "ok",
                "all %%d parts loaded" %% _all)
    except Exception as ex:                                       # noqa: BLE001
        add("mounts", "Parts of the finance app that did not load", "info",
            "could not be read (%%s)" %% ex)

''' % (GUARDED_LATER, len(OLD) + len(GUARDED_LATER) - 1)     # staff_pages + joiner_app are one part


def md5(b):
    return hashlib.md5(b).hexdigest()


def transform(s):
    i, j = s.index(FIRST), s.index(LAST_END) + len(LAST_END)
    region = s[i:j]
    out, sect, body = [], None, []
    for line in region.split("\n"):
        m = re.match(r"# --- (S\d+_[A-Z_]+) (begin|end)", line)
        if m and m.group(2) == "begin":
            sect, body = m.group(1), []
            out.append(line)
            continue
        if m and m.group(2) == "end":
            code = [l for l in body if l.strip() and not l.lstrip().startswith("#")]
            comments_top = []
            k = 0
            while k < len(body) and (body[k].lstrip().startswith("#") or not body[k].strip()):
                comments_top.append(body[k]); k += 1
            rest = body[k:]
            assert rest and all(l.strip() and not l.lstrip().startswith("#") for l in rest), sect
            mods = [re.match(r"import (\w+)", l).group(1) for l in rest if l.startswith("import ")]
            label = "+".join(mods)
            out += comments_top
            out.append("try:                                                          # S425: guarded, as every later mount (S209)")
            out += ["    " + l for l in rest]
            out.append("except Exception as _ex_m:                                    # noqa: BLE001")
            out.append("    _MOUNT_FAILED.append((%r, repr(_ex_m)[:200]))" % label)
            out.append("    print(\"%s NOT mounted: %%s\" %% _ex_m, file=sys.stderr)" % label)
            out.append(line)
            sect = None
            continue
        if sect:
            body.append(line)
        else:
            out.append(line)
    new_region = "\n".join(out)
    s = s[:i] + ("# S425: every mount below records a failure here; the health page reads it (row 'mounts').\n"
                 "_MOUNT_FAILED = []\n\n") + new_region + s[j:]
    assert s.count(B2) == 1
    return s.replace(B2, ROW + B2)


def apply(path, check_from=True):
    raw = open(path, "rb").read()
    s = raw.decode("utf-8")
    if TAG in s:
        return "already"
    if check_from and md5(raw) != FROM:
        raise SystemExit("REFUSED: finance_app.py is %s, not the S422 bytes %s -- it has moved; the kit must be rebuilt"
                         " from the new bytes" % (md5(raw), FROM))
    open(path, "wb").write(transform(s).encode("utf-8"))
    return "patched"


if __name__ == "__main__":
    print("finance_app.py :", apply(sys.argv[1]))

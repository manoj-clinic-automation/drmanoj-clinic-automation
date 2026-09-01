#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_orders_portal.py - S216 orders build, SERVER side
==========================================================
Base = the live casepack_portal.py (pin 3146bdbf...).
Three ANCHORED patches. Adds a server-side medicine list; changes nothing else.

WHY SERVER-SIDE (owner ruling, 01-Sep-2026):
  The OT medicine catalogue was hard-coded in the page and `OT_EXTRA` - the
  array meant for his own additions - was EMPTY. Nothing he typed was ever
  remembered. The only persistent store on that page is browser localStorage,
  which the page itself warns is "on this device only". A medicine list he has
  to rebuild after every browser clean-up is not a list. It lives beside the
  case and consent ledgers instead, and is backed up with them.

NEVER DESTROYS: a save writes a dated .bak of the previous file first, the same
discipline the consent archive uses.
"""
import sys, hashlib

BASE_MD5 = "3146bdbfc710dd00a12ef584e327ab0a"

A_PATHS = 'PAGE_HTML      = os.path.join(CASEPACK_DIR, "casepack_page.html")'
N_PATHS = ('PAGE_HTML      = os.path.join(CASEPACK_DIR, "casepack_page.html")\n'
           'MED_LIST       = os.path.join(CASEPACK_DIR, "med_list.csv")')

A_COLS = ('CONSENT_COLS = ["Case_ID","Consent_No","Kind","Issue_Date","Content_MD5","Procedure",\n'
          '                "Polio_Module","Change_Note","File","Issued_By","Written_At"]')

N_COLS = A_COLS + '''

MED_COLS = ["Item","Route","Freq","Ayushman","Package","Active","Sort"]

# The owner's own post-op medicines, from MY_TEMPLATES_S216.txt. Seeded ONCE if
# the list does not exist; after that the file is his and is never re-seeded.
MED_SEED = [
    ("5% DNS",              "IV",  "",    "", "", "1", "10"),
    ("NS",                  "IV",  "",    "", "", "1", "11"),
    ("Ringer Lactate",      "IV",  "",    "", "", "1", "12"),
    ("Inj Pantawin 40",     "IV",  "OD",  "", "", "1", "20"),
    ("Inj Aciloc",          "IV",  "BD",  "", "", "1", "21"),
    ("Inj Vinbactum DS",    "IV",  "BD",  "", "", "1", "30"),
    ("Inj Q Bact 1.5",      "IV",  "BD",  "", "", "1", "31"),
    ("Inj Tazar 4.5",       "IV",  "TDS", "", "", "1", "32"),
    ("Inj Vintaz P 4.5",    "IV",  "TDS", "", "", "1", "33"),
    ("Inj Dynapar",         "IV",  "TDS", "", "", "1", "40"),
    ("Inj Lonac",           "IV",  "TDS", "", "", "1", "41"),
    ("Inj Butrum 2 Mg",     "IM",  "SOS", "", "", "1", "50"),
    ("Inj Pcm 100 Ml",      "IV",  "SOS", "", "", "1", "51"),
]

def _med_rows():
    """The medicine list. Seeded from the owner's template the first time only."""
    if not os.path.exists(MED_LIST):
        _med_write([dict(zip(MED_COLS, r)) for r in MED_SEED])
    return _read_csv(MED_LIST)

def _med_write(rows):
    """Replace the list. The previous file is kept, dated, never deleted."""
    if os.path.exists(MED_LIST):
        stamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy2(MED_LIST, MED_LIST + ".bak_" + stamp)
        except Exception:
            pass
    with open(MED_LIST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MED_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: str(r.get(k, "") or "") for k in MED_COLS})'''

A_ROUTE = '''    @app.route("/portal/casepack/consents/<case_id>")'''

N_ROUTE = '''    @app.route("/portal/casepack/meds")
    @guard
    def casepack_meds():
        """The owner's medicine list — read."""
        try:
            return jsonify({"ok": True, "rows": _med_rows()})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/meds", methods=["POST"])
    @guard
    def casepack_meds_save():
        """Replace the medicine list. Refuses an empty list — that is far more
        likely to be a bug in the page than an intention, and the previous file
        would already have been backed up for nothing."""
        try:
            b = request.get_json(force=True) or {}
            rows = b.get("rows")
            if not isinstance(rows, list) or not rows:
                return jsonify({"ok": False, "error": "refused: empty list"}), 400
            if len(rows) > 400:
                return jsonify({"ok": False, "error": "refused: too many rows"}), 400
            clean = []
            for r in rows:
                item = str((r or {}).get("Item", "")).strip()
                if not item:
                    continue
                clean.append({
                    "Item":     item[:120],
                    "Route":    str(r.get("Route", "")).strip()[:12],
                    "Freq":     str(r.get("Freq", "")).strip()[:12],
                    "Ayushman": "1" if str(r.get("Ayushman", "")).strip() in ("1", "true", "True") else "",
                    "Package":  "1" if str(r.get("Package", "")).strip() in ("1", "true", "True") else "",
                    "Active":   "" if str(r.get("Active", "1")).strip() in ("", "0", "false", "False") else "1",
                    "Sort":     str(r.get("Sort", "")).strip()[:8],
                })
            if not clean:
                return jsonify({"ok": False, "error": "refused: no usable rows"}), 400
            _med_write(clean)
            return jsonify({"ok": True, "count": len(clean)})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/casepack/consents/<case_id>")'''


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)
    n = [0]; ref = [src]
    def patch(old, new, label):
        c = ref[0].count(old)
        assert c == 1, "ANCHOR FAIL (%s): found %d, expected 1" % (label, c)
        ref[0] = ref[0].replace(old, new); n[0] += 1
    patch(A_PATHS, N_PATHS, "O1 med list path")
    patch(A_COLS,  N_COLS,  "O2 seed + read/write helpers")
    patch(A_ROUTE, N_ROUTE, "O3 the two routes")
    out = ref[0]
    # shutil is needed by _med_write
    if "\nimport shutil" not in out and "import shutil" not in out.split("\n\n")[0]:
        i = out.index("import ")
        line_end = out.index("\n", i)
        out = out[:line_end+1] + "import shutil\n" + out[line_end+1:]
        n[0] += 1
        print("  O4 shutil import added")
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()

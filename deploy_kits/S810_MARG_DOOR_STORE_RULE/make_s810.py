#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s810.py ROOT OUT -- kit S810 (13-Nov-2026, Sanjeevni session 441): build the two changed files FROM THE LIVE BYTES.

  ROOT/marg_ingest/marg_router.py  318086e3 -> the store rule in verify() + its selftest checks
  ROOT/finance/reports_tile.py     4eaeadbd -> one Hindi line for the store refusal + its selftest check

Every patch is an exact anchor that must occur once; any other count stops the build (nothing written).
The same marg_router.py is placed on manojz (D:\\Downloads\\margsync\\MargPull\\marg_router.py) -- one judgement, two copies."""
import hashlib, os, sys

FROM = {"marg_ingest/marg_router.py": "318086e36b0088f2da57b95d19a86b98",
        "finance/reports_tile.py":   "4eaeadbdbb7ea02c14849ff03ebaa42b"}

R_DOC_A = ('      / _NEAR / _MIXED -- and index.csv carries the evidence in "notes".\n')
R_DOC_B = R_DOC_A + ('    * S810 (D913, 13-Nov-2026): a stock file -- closing stock, stock valuation, batch\n'
                     '      stock -- of any store other than WHOLE STORES is REFUSED with the store named.\n'
                     '      Only the whole shop\'s stock is filed (the title is the only place the store shows).\n')

R_RULE_A = ('# --------------------------------------------------------------------------- #\n'
            '# verification AT SOURCE\n'
            '# --------------------------------------------------------------------------- #\n\n'
            'def verify(')
R_RULE_B = ('# --------------------------------------------------------------------------- #\n'
            '# S810 (D913, plan v4 section 4): only a WHOLE STORES stock file is filed\n'
            '# --------------------------------------------------------------------------- #\n'
            '# Marg prints the store(s) chosen at "Select Store" before the report\'s name in its title:\n'
            '#   "WHOLE STORES CLOSING STOCK AS ON ..."   "MAIN STORE CLOSING STOCK AS ON ..."\n'
            '#   "DTH,MAIN STORE,STOCK VALUATION AS ON ..."   "SCRAP STORE,WHOLE,CLOSING STOCK AS ON ..."\n'
            '# The archive\'s file name does not carry the store, so the title is the only place it can be\n'
            '# judged -- here, at the door, once. A choice that includes WHOLE passes; a title that names no\n'
            '# store passes (never seen; never refused on a guess). Every reader already picks WHOLE STORES for\n'
            '# itself, so nothing was ever miscounted -- the gap was a wrong file filed as good.\n'
            'STORE_RULE_TYPES = ("STOCK_CLOSING", "STOCK_VALUATION", "BATCH_STOCK")\n'
            'RE_STORE_TITLE = re.compile(r"^\\s*(.*?)[\\s,:]*(?:CLOSING\\s+STOCK|STOCK\\s+VALUATION)\\b", re.I)\n'
            'STORE_REFUSAL = "only -- the WHOLE STORES report is needed"\n\n\n'
            'def store_problem(title, typ):\n'
            '    """S810: "" when a stock file is the whole shop\'s (or names no store, or is not a stock type);\n'
            '    else the refusal, the store(s) named: "MAIN STORE only -- the WHOLE STORES report is needed"."""\n'
            '    if typ not in STORE_RULE_TYPES:\n'
            '        return ""\n'
            '    m = RE_STORE_TITLE.match(title or "")\n'
            '    if not m:\n'
            '        return ""\n'
            '    names = [norm(x).strip(" :").upper() for x in re.split(r"[,:]", m.group(1))]\n'
            '    names = [n for n in names if n]\n'
            '    if not names or any(n.split()[0] == "WHOLE" for n in names):\n'
            '        return ""\n'
            '    return "%s %s" % (", ".join(names), STORE_REFUSAL)\n\n\n'
            + R_RULE_A)

R_VER_A = ('    if problems:\n'
           '        return "REFUSED", " | ".join(problems)\n\n'
           '    if sig and sig.get("deep_verify") == "marg_report":\n')
R_VER_B = ('    if sig:                                                       # S810 (D913): WHOLE STORES only\n'
           '        _sp = store_problem(title, sig.get("type", ""))\n'
           '        if _sp:\n'
           '            problems.append(_sp)\n'
           + R_VER_A)

R_ST_A = '    out("SELFTEST " + ("OK" if ok else "FAILED"))\n'
R_ST_B = ('    # S810 (D913): the store rule, on the titles Marg has really printed (MargArchive, Aug-Oct 2026)\n'
          '    for _t, _ty, _want in (\n'
          '            ("WHOLE STORES CLOSING STOCK AS ON 12-11-2026", "STOCK_CLOSING", ""),\n'
          '            ("MAIN STORE CLOSING STOCK AS ON 26-08-2026", "STOCK_CLOSING", "MAIN STORE"),\n'
          '            ("DTH CLOSING STOCK AS ON 26-08-2026", "STOCK_CLOSING", "DTH"),\n'
          '            ("SCRAP STORE CLOSING STOCK AS ON 26-08-2026", "STOCK_CLOSING", "SCRAP STORE"),\n'
          '            ("DTH,MAIN STORE,CLOSING STOCK AS ON 08-10-2026", "STOCK_CLOSING", "DTH, MAIN STORE"),\n'
          '            ("SCRAP STORE,WHOLE,CLOSING STOCK AS ON 01-07-2026", "STOCK_CLOSING", ""),\n'
          '            ("DTH,MAIN STORE,STOCK VALUATION AS ON 06-09-2026", "STOCK_VALUATION", "DTH, MAIN STORE"),\n'
          '            ("WHOLE STORES STOCK VALUATION AS ON 31-10-2026", "STOCK_VALUATION", ""),\n'
          '            ("WHOLE STORES : STOCK VALUATION : 31-10-2026", "STOCK_VALUATION", ""),\n'
          '            ("MAIN STORE : STOCK VALUATION : 31-10-2026", "STOCK_VALUATION", "MAIN STORE"),\n'
          '            ("WHOLE STORES CLOSING STOCK AS ON 22-10-2026", "BATCH_STOCK", ""),\n'
          '            ("SCRAP STORE CLOSING STOCK AS ON 22-10-2026", "BATCH_STOCK", "SCRAP STORE"),\n'
          '            ("CLOSING STOCK AS ON 12-11-2026", "STOCK_CLOSING", ""),\n'
          '            ("MAIN STORE CLOSING STOCK AS ON 26-08-2026", "STOCK_EXPIRY", ""),\n'
          '            ("MAIN STORE PURCHASE STATEMENT", "PURCHASE_BILLWISE", "")):\n'
          '        _got = store_problem(_t, _ty)\n'
          '        ck("S810 store rule: %s / %s -> %s" % (_ty, _t[:34], _want or "passes"),\n'
          '           (_got == "") if not _want else (_got == "%s %s" % (_want, STORE_REFUSAL)))\n'
          '    class _S8(object):\n'
          '        def __init__(self, rows):\n'
          '            self.rows = rows; self.nrows = len(rows); self.ncols = max(len(r) for r in rows)\n'
          '        def cell_value(self, r, c):\n'
          '            return self.rows[r][c] if c < len(self.rows[r]) else ""\n'
          '    _h8 = ["S.No.", "Description", "Total Stock", "Unit"]\n'
          '    for _t8, _ok8 in (("MAIN STORE CLOSING STOCK AS ON 12-11-2026", False), ("WHOLE STORES CLOSING STOCK AS ON 12-11-2026", True)):\n'
          '        _sh8 = _S8([[_t8], _h8, ["1.0", "A", "1", "PCS"], ["TOTAL", "", "1", ""]])\n'
          '        _sg8, _st8, _ = identify(_t8, _h8, sigs)\n'
          '        _v8, _r8 = verify("", _sh8, _sg8, _t8, _h8, 1, "2026-11-12", "2026-11-12", None, None)\n'
          '        ck("S810 verify(): %s -> %s" % (_t8[:24], "VERIFIED" if _ok8 else "REFUSED, the store named"),\n'
          '           _st8 == "IDENTIFIED" and ((_v8 == "VERIFIED") if _ok8 else (_v8 == "REFUSED" and _r8 == "MAIN STORE %s" % STORE_REFUSAL)))\n\n'
          + R_ST_A)

T_HI_A = '    if reader_stop(reason):                                     # S556: the reader stopped at a line -- no redo cures it\n'
T_HI_B = ('    ms = S810_STORE.search(str(reason or ""))\n'
          '    if ms:                                                      # S810 (D913): a single store\'s stock, refused at the door\n'
          '        return "Yeh sirf %s ki report hai. Select Store mein WHOLE chuniye, phir dobara nikaaliye." % ms.group(1).strip()\n'
          + T_HI_A)
T_RE_A = 'S679_PARTY = re.compile(r"bill ([A-Z]{1,3}[0-9]{3,9}) is billed to (?:the|a) party account")\n'
T_RE_B = (T_RE_A + 'S810_STORE = re.compile(r"(?:^|\\| )([^|]+?) only -- the WHOLE STORES report is needed")   # marg_router.store_problem\'s words\n')
T_ST_A = ('    ck("Hindi reasons cover the reader\'s witness names", "total" in hindi_failed(["TOTAL units = sum of every line"]).lower()\n')
T_ST_B = ('    ck("S810: a single store\'s stock refused at the door -> the store named, WHOLE asked for",\n'
          '       hindi_reason("MAIN STORE only -- the WHOLE STORES report is needed", "REFUSED")\n'
          '       == "Yeh sirf MAIN STORE ki report hai. Select Store mein WHOLE chuniye, phir dobara nikaaliye."\n'
          '       and "DTH, MAIN STORE ki" in hindi_reason("TRUNCATED -- x | DTH, MAIN STORE only -- the WHOLE STORES report is needed", "REFUSED"))\n'
          + T_ST_A)

PATCHES = {"marg_ingest/marg_router.py": [(R_DOC_A, R_DOC_B), (R_RULE_A, R_RULE_B), (R_VER_A, R_VER_B), (R_ST_A, R_ST_B)],
           "finance/reports_tile.py":   [(T_RE_A, T_RE_B), (T_HI_A, T_HI_B), (T_ST_A, T_ST_B)]}


def main(root, out):
    built = {}
    for rel, steps in PATCHES.items():
        p = os.path.join(root, rel)
        raw = open(p, "rb").read()
        got = hashlib.md5(raw).hexdigest()
        if got != FROM[rel]:
            print("STOP: %s is %s, expected %s -- nothing built" % (rel, got[:8], FROM[rel][:8]))
            return 2
        txt = raw.decode("utf-8")
        for i, (a, b) in enumerate(steps, 1):
            n = txt.count(a)
            if n != 1:
                print("STOP: %s anchor %d occurs %d times -- nothing built" % (rel, i, n))
                return 2
            txt = txt.replace(a, b, 1)
        built[rel] = txt.encode("utf-8")
    for rel, data in built.items():
        dst = os.path.join(out, os.path.basename(rel))
        with open(dst, "wb") as fh:
            fh.write(data)
        print("%s  %s" % (hashlib.md5(data).hexdigest(), rel))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

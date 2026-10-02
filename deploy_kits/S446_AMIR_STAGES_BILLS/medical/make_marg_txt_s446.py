# -*- coding: utf-8 -*-
r"""make_marg_txt_s446.py -- builds marg_txt.py S446 (F-674) from the LIVE bytes, by anchored edits.

    python -B make_marg_txt_s446.py <live marg_txt.py> <out marg_txt.py>

The live medical-PC file is md5 38d85298f1627ab22b59c9f3459d8764 (S397). Anything else: stop.
Every anchor must occur exactly once in the live bytes, else stop. Nothing else is touched.

THE CHANGE
  Marg prints `***` in an item line's SECOND number column -- the three-character column between the
  bill's own line number and the medicine name (the reader's own comment calls the item line
  "seq code NAME<20> PACK"; RE_ITEM wants digits there) -- when the figure does not fit. Line 52 of
  the 30-Sep-2026 sale:  '            4 *** FINGER EXTENSION SPL 1*1             1      180.00'.
  Such a line is now read with that column empty (no figure): the line is accepted, and its cells are
  exactly what Marg prints and what Marg's own Excel export carries ('4 *** FINGER EXTENSION SPL 1*1'
  -- the spine's clean_raw already strips that form from Excel sale lines). The stars must fill that
  column exactly: right after the line number, one space each side, a name after. `***` in any other
  column (line number, quantity, amount, a bill's money, a total) is refused exactly as before, and
  every other check is untouched.
"""
import hashlib
import sys

FROM_MD5 = "38d85298f1627ab22b59c9f3459d8764"

EDITS = [
    # 1. the version the watcher logs ("converted by marg_txt S446")
    (b'VERSION = "S397"\n',
     b'VERSION = "S446"\n'),
    # 2. the docstring says what changed
    (b'    python marg_txt.py report.txt out.XLS      convert one file\n',
     b'S446 (F-674, 02-Oct-2026): Marg prints *** in an item line\'s second number column (the three-character\n'
     b'  column between the bill\'s line number and the medicine name) when its figure does not fit. That line\n'
     b'  is read with the column empty: its cells are what Marg prints, as Marg\'s own Excel export has them\n'
     b'  ("4 *** FINGER EXTENSION SPL 1*1"). The stars must fill that column exactly; *** anywhere else, and\n'
     b'  every other check, refuses as before.\n'
     b'\n'
     b'    python marg_txt.py report.txt out.XLS      convert one file\n'),
    # 3. the one new pattern, beside the item pattern it widens
    (b'RE_ITEM = re.compile(r"^\\s{6,}\\d+\\s+\\d+\\s")\n',
     b'RE_ITEM = re.compile(r"^\\s{6,}\\d+\\s+\\d+\\s")\n'
     b'RE_ITEM_STARS = re.compile(r"^\\s{6,}\\d+ \\*\\*\\* \\S")    # S446: *** fills the second column, nothing else\n'),
    # 4. the item branch takes that line too; everything after it is unchanged
    (b'        if RE_ITEM.match(s):\n',
     b'        if RE_ITEM.match(s) or RE_ITEM_STARS.match(s):          # S446 (F-674)\n'),
    # 5. the selftest proves it, and proves *** elsewhere still refuses
    (b'    x1, _ = convert(T); x2, _ = convert(T)\n',
     b'    ST = T.replace(b"            2  16 DISPO SYRINGE NIPRO", b"            2 *** DISPO SYRINGE NIPRO")\n'
     b'    sr_ = to_rows(ST)\n'
     b'    ck("S446: *** in an item\'s second column is read with that column empty, the line as Marg prints it",\n'
     b'       [r for r in sr_ if r[0] == "" and r[1][:1].isdigit()][2][1] == "2 *** DISPO SYRINGE NIPRO  1*1"\n'
     b'       and len(sr_) == len(rows))\n'
     b'    for bad_, why_ in ((ST.replace(b"NIPRO  1*1             1        7.00", b"NIPRO  1*1           ***        7.00"),\n'
     b'                        "*** in the quantity"),\n'
     b'                       (ST.replace(b"             1        7.00", b"             1         ***"), "*** in the amount"),\n'
     b'                       (T.replace(b"            2  16 DISPO", b"          ***  16 DISPO"), "*** in the line number"),\n'
     b'                       (T.replace(b"            2  16 DISPO", b"            2 **  DISPO"), "** not filling the column")):\n'
     b'        try:\n'
     b'            to_rows(bad_); ck("S446 refused: " + why_, False)\n'
     b'        except Refused:\n'
     b'            ck("S446 refused: " + why_, True)\n'
     b'    x1, _ = convert(T); x2, _ = convert(T)\n'),
]


def main(src, dst):
    raw = open(src, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM_MD5:
        print("STOP: %s is md5 %s, not the pinned %s" % (src, got, FROM_MD5))
        return 2
    out = raw
    for i, (old, new) in enumerate(EDITS, 1):
        n = out.count(old)
        if n != 1:
            print("STOP: anchor %d occurs %d times (must be exactly once): %r" % (i, n, old[:60]))
            return 3
        out = out.replace(old, new)
    compile(out, dst, "exec")
    with open(dst, "wb") as fh:
        fh.write(out)
    print("built %s  md5 %s  (from %s, %d anchored edits)" % (dst, hashlib.md5(out).hexdigest(), FROM_MD5[:8], len(EDITS)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

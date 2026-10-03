#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_marg_txt_s454.py -- kit S454_BILL_REGISTER, part 1 (D666): the medical PC's text reader learns Marg's PENDING ORDERS (PURCHASE).

Built from the LIVE bytes (CLAUDE.md rule 2): the reader the medical PC runs (marg_txt S446, 70f920c4 -- the heartbeat names it, and the
Drive kit copy is the same bytes) plus anchored edits, each anchor exactly once or the build stops and writes nothing:
  * a third kind, ORDER, by the title and the column heads, with *** End of Report *** at the end -- the file's name is never looked at;
  * order_rows(): the eleven-column sheet (supplier, phones, item, packing, entry number, date, order qty, receive, pending, rate, value),
    a title row, the heads, one row per item line, the TOTAL row last (order_block_s454.py beside this file);
  * convert() dispatches ORDER; VERSION S454; ORDER_SAMPLE (the repository's sample of 02-Oct, phone numbers blanked) and its selftest.
Nothing that SALE or STOCK read changes: the same text gives the same bytes as before (the proof shows it).

    python -B make_marg_txt_s454.py --live <marg_txt.py> --out <dir>
"""
import argparse
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = "70f920c445ec82fc8c1e069f1f758efb"
E = []


def edit(old, new):
    E.append((old, new))


edit('VERSION = "S446"\n', 'VERSION = "S454"\n')
edit("    python marg_txt.py report.txt out.XLS      convert one file\n",
     "S454 (D666, 03-Oct-2026): Marg's PENDING ORDERS (PURCHASE) -- Darpan's order sheet, saved as text the default way -- is a third kind,\n"
     "  ORDER: recognised by its title and column heads with *** End of Report *** at the end (the file's name is never looked at). It\n"
     "  becomes an eleven-column sheet: supplier, phones, item, packing, entry number, date, order qty, receive, pending, rate, value -- a\n"
     "  title row, the heads, one row per item line, the TOTAL row last; the date is not the first column. An item line is split on the\n"
     "  packing's own shape followed by the entry number (a name that fills its column leaves one space). Refused, with the reason: a\n"
     "  line of a kind not known here; a supplier's lines not coming to its subtotal in units; the lines not coming to the TOTAL; no\n"
     "  TOTAL; the file cut short. Values are checked within a rupee a line (Marg rounds each line's value).\n\n"
     "    python marg_txt.py report.txt out.XLS      convert one file\n")
edit('    """"SALE", "STOCK" or None."""\n', '    """"SALE", "STOCK", "ORDER" (S454) or None."""\n')
edit('    if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):\n        return "STOCK"\n    return None\n',
     '    if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):\n        return "STOCK"\n'
     '    if ORDER_TITLE in head and RE_ORDER_HEAD.search(head):                 # S454 (D666)\n        return "ORDER"\n    return None\n')
edit('    rows = stock_rows(raw) if k == "STOCK" else to_rows(raw)\n',
     '    rows = stock_rows(raw) if k == "STOCK" else (order_rows(raw) if k == "ORDER" else to_rows(raw))     # S454: ORDER\n')
INSERT_BEFORE = "def _cols(header_line):\n"
SELFTEST_ANCHOR = "    if sample:\n        raw = open(sample, \"rb\").read()\n"
SELFTEST = r'''    # S454 (D666): the pending-orders sheet -- the repository's sample of 02-Oct (phone numbers blanked)
    O_ = ORDER_SAMPLE
    ck("S454: the pending-orders sheet is recognised as ORDER; the sale and the stock stay themselves",
       kind(O_) == "ORDER" and kind(T) == "SALE" and kind(S_) == "STOCK" and kind(T) != "ORDER")
    orr = order_rows(O_)
    it_ = orr[2:-1]
    ck("S454: 11 suppliers, 32 lines, 4,046 units; the TOTAL row last", len({r[0] for r in it_}) == 11 and len(it_) == 32
       and orr[-1][0] == "TOTAL" and orr[-1][6] == 4046.0 and orr[-1][10] == 41226.0, (len({r[0] for r in it_}), len(it_), orr[-1][6]))
    ck("S454: the heads, eleven, the date not the first column", orr[1] == ORDER_HEAD and orr[1][0] == "SUPPLIER" and orr[1][5] == "DATED"
       and all(len(r) == 11 for r in orr))
    ck("S454: the supplier whose block breaks across the page keeps its four lines",
       [r[2] for r in it_ if r[0] == "RAVI MEDICAL AGENCY"] == ["DECA INSTABOLIN 50", "ETOBONE P", "MET4MIN GL 1", "OPTIFENAC TBR"])
    ck("S454: a name that fills its column is read whole, the packing apart (one space)",
       any(r[2] == "KNEE IMMOBILISER UNIS" and r[3] == "1*1" and r[4] == "OP-0288" for r in it_))
    ck("S454: the supplier with one line and no subtotal is read; the town is not part of a supplier",
       [r[2] for r in it_ if r[0] == "KRISHNA MEDICOS"] == ["NARCOGEN FORTE"] and "DRUG DEAL" in {r[0] for r in it_})
    ck("S454: '20:0' as printed, a plain number a number, the stray full stop dropped from a packing",
       any(r[2] == "TENDOZAC TAB" and r[6] == "20:0" for r in it_) and any(r[2] == "CCM" and r[6] == 5.0 for r in it_)
       and any(r[2] == "PRETOL 8" and r[3] == "1*10" for r in it_))
    _cut = O_[:O_.index(b"*** End of Report ***")]
    for bad_, why_ in ((O_.replace(b"  VERC 16               1*10     OP-0329   02-10-2026      10:0         -      10:0    95.25     953\n", b""),
                        "a line removed (the subtotal fails)"),
                       (O_.replace(b"TOTAL                                                      4046      4046", b"TOTAL                                                      4047      4047"),
                        "the TOTAL altered"),
                       (_cut, "the last line cut off (no End of Report)"),
                       (O_.replace(b"KRISHNA MEDICOS", b"  SOMETHING ODD HERE\nKRISHNA MEDICOS"), "a line of a kind not known"),
                       (O_.replace(b"TOTAL                                                      4046      4046            41226\n", b""), "no TOTAL")):
        try:
            order_rows(bad_)
            ck("S454 refused: " + why_, False)
        except Refused as ex_:
            ck("S454 refused: %s -- %s" % (why_, str(ex_)[:70]), True)
    ck("S454: a cut-off sheet is not recognised as ORDER (no End line); a sale with the order title elsewhere is not either",
       kind(_cut) is None and kind(T + b"PENDING ORDERS (PURCHASE)") != "ORDER")
    xo, io_ = convert(O_)
    ck("S454: the order sheet gives the same bytes every time", xo == convert(O_)[0] and io_["kind"] == "ORDER" and io_["rows"] == 35,
       hashlib.md5(xo).hexdigest()[:8])
'''


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(live, out, check_pin=True):
    raw = open(live, "rb").read()
    if check_pin and md5b(raw) != FROM:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing written" % (live, md5b(raw), FROM))
    txt = raw.decode("utf-8")
    for old, new in E:
        n = txt.count(old)
        if n != 1:
            raise SystemExit("STOP: an anchor occurs %d times (must be exactly once): %r" % (n, old[:80]))
        txt = txt.replace(old, new, 1)
    blk = open(os.path.join(HERE, "order_block_s454.py"), "rb").read().decode("utf-8").strip("\n") + "\n\n\n"
    if txt.count(INSERT_BEFORE) != 1:
        raise SystemExit("STOP: the insertion anchor occurs %d times" % txt.count(INSERT_BEFORE))
    txt = txt.replace(INSERT_BEFORE, blk + INSERT_BEFORE, 1)
    sample = open(os.path.join(HERE, "order_sample_s454.txt"), "rb").read().decode("latin-1")
    if any(ch.isdigit() for l in sample.splitlines() if "Ph." in l or "Phone" in l for ch in l.split("Ph")[-1]):
        raise SystemExit("STOP: the sample carries a digit beside a phone label -- no phone number may enter the reader")
    const = ("ORDER_SAMPLE = (\n" + "".join("    %r\n" % (l + "\n") for l in sample.split("\n")[:-1]) + ").encode(\"latin-1\")\n\n\n")
    anchor = "def selftest(sample=None):\n"
    if txt.count(anchor) != 1:
        raise SystemExit("STOP: the selftest anchor occurs %d times" % txt.count(anchor))
    txt = txt.replace(anchor, const + anchor, 1)
    if txt.count(SELFTEST_ANCHOR) != 1:
        raise SystemExit("STOP: the selftest insertion anchor occurs %d times" % txt.count(SELFTEST_ANCHOR))
    txt = txt.replace(SELFTEST_ANCHOR, SELFTEST + SELFTEST_ANCHOR, 1)
    b = txt.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "marg_txt.py"), "wb") as fh:
        fh.write(b)
    print("built marg_txt.py %s -> %s  (%d edits, the ORDER block, ORDER_SAMPLE, the selftest)" % (FROM[:8], md5b(b), len(E)))
    return md5b(b)


MANIFEST_FROM = "bdd277686cb76f944d4569e666a9d89f"


def manifest(live, out, new_md5):
    """KIT_MANIFEST.txt from the live one (bdd27768, S446): the reader's line carries the new md5, one comment line above it."""
    raw = open(live, "rb").read()
    if md5b(raw) != MANIFEST_FROM:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing written" % (live, md5b(raw), MANIFEST_FROM))
    txt = raw.decode("utf-8")
    old = "marg_txt.py | D:\\SendToClinic\\marg_txt.py | %s\r\n" % FROM          # the manifest is written with CRLF
    if txt.count(old) != 1:
        raise SystemExit("STOP: the manifest's reader line occurs %d times" % txt.count(old))
    txt = txt.replace(old, "# S454 (D666) -- the reader also takes Darpan's PENDING ORDERS (PURCHASE) text as a third kind, ORDER (S454's walk and selftest).\r\n"
                           "marg_txt.py | D:\\SendToClinic\\marg_txt.py | %s\r\n" % new_md5, 1)
    b = txt.encode("utf-8")
    with open(os.path.join(out, "KIT_MANIFEST.txt"), "wb") as fh:
        fh.write(b)
    print("built KIT_MANIFEST.txt %s -> %s" % (MANIFEST_FROM[:8], md5b(b)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    ap.add_argument("--manifest", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    nm = build(a.live, a.out)
    if a.manifest:
        manifest(a.manifest, a.out, nm)

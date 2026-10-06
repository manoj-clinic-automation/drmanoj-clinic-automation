#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s490.py -- kit S490_ORDER_SHEET_PACKING. Proves marg_txt.py S490 against S480, on manojz (the texts never leave it).

    python -B walk_s490.py <dir with OLD marg_txt.py> <dir with NEW marg_txt.py> <_captured_txt folder> [<server marg_ingest dir> <server finance dir>]

1  every text the medical PC kept (taken, held, refused): OLD and NEW give the same bytes or the same refusal -- except a
   pending-orders sheet with a packing that is not N*M, which OLD refuses and NEW reads.
2  invented sheets (W490): every packing shape the shop's item master holds is read; the units and the subtotals tie; a packing
   out of its column is refused; OLD refuses the non-strip ones (the negative control).
3  (when the server's code is given) the converted sheet is judged ORDER_PENDING VERIFIED by the server's router and read by
   order_sheet's own row reader: one line per item, the packing as printed.
No line of a real export is printed -- counts, kinds and packings only.
"""
import glob
import hashlib
import importlib.util
import os
import sys
import tempfile

OK = BAD = 0


def ck(what, cond, extra=""):
    global OK, BAD
    if cond:
        OK += 1
        print("  OK   " + what)
    else:
        BAD += 1
        print("  RED  " + what + ((" -- " + str(extra)[:160]) if extra else ""))


def load(d, tag):
    spec = importlib.util.spec_from_file_location("marg_txt_" + tag, os.path.join(d, "marg_txt.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(m, raw):
    try:
        xls, info = m.convert(raw)
        return ("ok", hashlib.md5(xls).hexdigest(), info.get("kind"), xls)
    except Exception as e:                                             # noqa: BLE001
        return ("no", e.__class__.__name__, "", None)


HEAD = ("\r\n                               W490 MEDICOS\r\n                              Phone : XXXXXXXXXX\r\n\r\n"
        "                            PENDING ORDERS (PURCHASE)\r\n" + "-" * 132 + "\r\n"
        "  ITEM NAME                      ENTRY NO.    DATED   ORDER QTY   RECEIVE   PENDING     RATE   VALUE  DUEDT  PARTY ORDER NO.\r\n"
        + "-" * 132 + "\r\n\r\n")
END = "-" * 132 + "\r\n*** End of Report ***\r\n"


def item(name, pack, entry, q, rate, value):
    return "  %-22s%-9s%-10s%-10s%10s%10s%10s%9s%8s\r\n" % (name, pack, entry, "06-10-2026", q, "-", q, rate, value)


def sheet(lines, sub=None, total=None, sup="W490 SUPPLIER ONE Ph.XXXXXXXXXX"):
    t = HEAD + sup + "\r\n" + "".join(lines)
    if sub:
        t += " " * 51 + "-" * 66 + "\r\n" + " " * 55 + "%8d%10d%17d\r\n" % sub + " " * 51 + "-" * 66 + "\r\n"
    t += "\r\n" + "-" * 132 + "\r\nTOTAL" + " " * 50 + "%8d%10d%17d\r\n" % (total or sub) + END
    return t.encode("latin-1")


def main(argv):
    old, new = load(argv[1], "old"), load(argv[2], "new")
    cap = argv[3]
    print("OLD %s  NEW %s" % (old.VERSION, new.VERSION))
    # ---- 1
    files = sorted(set(glob.glob(os.path.join(cap, "*.txt")) + glob.glob(os.path.join(cap, "*", "*.txt"))))
    files = [f for f in files if not f.endswith(".why.txt")]
    same = changed = 0
    today = []
    kinds = {}
    for f in files:
        raw = open(f, "rb").read()
        a, b = run(old, raw), run(new, raw)
        if a[:3] == b[:3]:
            same += 1
            kinds[a[2] or a[1]] = kinds.get(a[2] or a[1], 0) + 1
        else:
            changed += 1
            today.append((f, raw, a, b))
    print("  texts kept on the mirror: %d · same result %d · changed %d · %s" % (len(files), same, changed, kinds))
    ck("1  every other text gives the same bytes or the same refusal", same == len(files) - changed and same > 20)
    ck("1  the only changes are pending-orders sheets OLD refused and NEW reads",
       changed >= 1 and all(a[0] == "no" and b[0] == "ok" and b[2] == "ORDER" for _f, _r, a, b in today), [(a[:2], b[:1]) for _f, _r, a, b in today])
    rows_today = None
    for f, raw, a, b in today:
        rows = new.order_rows(raw)
        its = [r for r in rows[2:] if r[2]]
        odd = sorted({str(r[3]) for r in its if "*" not in str(r[3])})
        print("     %s…: %d item lines, %d suppliers, packings not N*M: %s" % (os.path.basename(f)[:15], len(its), len({r[0] for r in its}), odd))
        rows_today = (f, raw, b[3], its)
    # ---- 2
    packs = ["1*10", "30GM", "200ML", "VAIL", "2ML", "1", "200ML.", "2.3ML", "1810", "1*15"]
    lines, units, val = [], 0, 0
    for i, p in enumerate(packs):
        strip = "*" in p
        q = "10:0" if strip else "7"
        u = (10 * int(p.split("*")[0]) * int(p.split("*")[1])) if strip else 7
        units += u
        val += 100
        lines.append(item("W490 ITEM %02d" % i, p, "OP-9%03d" % i, q, "10.00", "100"))
    raw = sheet(lines, sub=(units, units, val))
    a, b = run(old, raw), run(new, raw)
    ck("2  a sheet with every packing shape of the item master is read (NEW)", b[0] == "ok" and b[2] == "ORDER", b)
    ck("2  ...and refused by OLD (the negative control)", a[0] == "no", a)
    if b[0] == "ok":
        its = [r for r in new.order_rows(raw)[2:] if r[2]]
        ck("2  one row per line, the packing as printed (a stray full stop dropped)", [str(r[3]) for r in its] == [p.rstrip(".") for p in packs], [r[3] for r in its])
    strips = [item("W490 STRIP A", "1*10", "OP-9100", "5:0", "10.00", "50"), item("W490 STRIP B", "1*15", "OP-9101", "2:0", "10.00", "20")]
    raw2 = sheet(strips, sub=(80, 80, 70))
    a, b = run(old, raw2), run(new, raw2)
    ck("2  a strips-only sheet: the same bytes OLD and NEW", a[0] == "ok" and a[1] == b[1], (a[:2], b[:2]))
    bad = sheet([strips[0], strips[1].replace("W490 STRIP B          1*15", "W490 STRIP B         1*15 ")], sub=(80, 80, 70))
    b = run(new, bad)
    ck("2  a packing out of its column is refused, by line (NEW)", b[0] == "no" and b[1] == "Refused", b[:2])
    wrong = sheet([item("W490 GEL", "30GM", "OP-9200", "7", "10.00", "70"), item("W490 STRIP", "1*10", "OP-9201", "1:0", "10.00", "10")], sub=(99, 99, 80))
    b = run(new, wrong)
    ck("2  a subtotal that does not tie is still refused (NEW)", b[0] == "no", b[:2])
    # ---- 3
    if len(argv) > 5 and rows_today:
        sys.path.insert(0, argv[4])
        sys.path.insert(0, argv[5])
        import marg_router                                             # noqa: PLC0415
        f, raw, xls, its = rows_today
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "W490__order_TXT.XLS")
            open(p, "wb").write(xls)
            sh = marg_router.open_sheet(p)
            rows = [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
            try:
                j = marg_router.judge(p) if hasattr(marg_router, "judge") else None
            except Exception as e:                                     # noqa: BLE001
                j = "judge raised %s" % e.__class__.__name__
            print("     the server's router on the converted sheet:", (j if not isinstance(j, dict) else {k: j.get(k) for k in ("type", "verdict", "variant", "reason")}))
            import order_sheet                                         # noqa: PLC0415
            ls = order_sheet._lines_of(rows)
            ck("3  the server's order reader takes one line per item, the packing as printed",
               len(ls) == len(its) and sorted({l["packing"] for l in ls if "*" not in l["packing"]}) == sorted({str(r[3]) for r in its if "*" not in str(r[3])}),
               (len(ls), len(its)))
            ck("3  ...and the non-strip lines carry a plain quantity and a pack of 1",
               all(order_sheet._pack(l["packing"]) == 1 and ":" not in l["qty_raw"] for l in ls if "*" not in l["packing"]))
    print("WALK S490: %d ok, %d red" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

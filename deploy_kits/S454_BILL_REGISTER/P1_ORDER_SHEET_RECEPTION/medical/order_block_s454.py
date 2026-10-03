# ------------------------------------------------------------------------ the pending-orders sheet (S454)
ORDER_TITLE = "PENDING ORDERS (PURCHASE)"
RE_ORDER_HEAD = re.compile(r"^\s*ITEM NAME\s+ENTRY NO\.\s+DATED\s+ORDER QTY\s+RECEIVE\s+PENDING\s+RATE\s+VALUE\b", re.M)
ORDER_HEAD = ["SUPPLIER", "PHONES", "ITEM NAME", "PACKING", "ENTRY NO.", "DATED", "ORDER QTY", "RECEIVE", "PENDING", "RATE", "VALUE"]
_Q = r"\d+(?::\d+)?"
# an item line: two spaces, the name, ONE space or more, the packing's own shape (a stray full stop allowed), the entry number, the
# date, order qty, receive, pending, rate, value -- and the two trailing heads (due date, party order no.) when Marg fills them.
# A name that fills its column leaves a single space before the packing, so the split is on the packing + entry shape, never on
# "two or more spaces".
RE_ORDER_ITEM = re.compile(r"^  (\S.*?) +(\d+\*\d+)\.? +([A-Z]{1,4}-\d+) +(\d\d-\d\d-\d{4}) +(" + _Q + r") +(-|" + _Q + r") +(" + _Q +
                           r") +(\d+(?:\.\d+)?) +(\d+)(?: +(\d\d-\d\d-\d{4}))?(?: +(\S{1,30}))?\s*$")
RE_ORDER_SUP = re.compile(r"^(\S.*?)\s*Ph\.(.*)$")
RE_ORDER_PHONE = re.compile(r"^[0-9X+\-]{5,16}$")
RE_ORDER_SUB = re.compile(r"^\s{20,}(\d+)\s+(\d+)\s+(\d+)\s*$")
RE_ORDER_TOTAL = re.compile(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s*$")


def _order_units(q, packing):
    """Marg's units: 'a:b' = a packs of the packing (1*10 -> 10) plus b loose; a plain number stands as it is."""
    if q == "-":
        return 0
    m = re.match(r"^(\d+):(\d+)$", q)
    if not m:
        return int(q)
    pm = re.match(r"^(\d+)\*(\d+)$", packing)
    pack = int(pm.group(1)) * int(pm.group(2)) if pm else 1
    return int(m.group(1)) * pack + int(m.group(2))


def _order_cell(q):
    """A quantity as Marg's sheet would carry it: '20:0' as printed, a plain whole number a number."""
    return float(q) if q.isdigit() else q


def order_rows(raw):
    """The eleven-column pending-orders sheet: a title row, the heads, one row per item line, the TOTAL row.
    Refused, with the reason, when a line is of a kind not known here, a supplier's lines do not come to its
    subtotal in units, the lines do not come to the TOTAL in units, there is no TOTAL, or the file is cut short.
    The value is checked with a tolerance of one rupee a line (Marg rounds each line's value)."""
    t = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n")
    if ORDER_TITLE not in t[:4000] or not RE_ORDER_HEAD.search(t[:4000]):
        raise NotThisReport("not a pending-orders text export")
    if END not in t[-400:]:
        raise Refused("no End of Report -- the file is incomplete")
    lines = t.split("\n")
    hi = next(i for i, l in enumerate(lines) if RE_ORDER_HEAD.match(l))
    shop = next((l.strip() for l in lines[:hi] if l.strip()), "")
    rows = [[ORDER_TITLE] + [""] * 10, list(ORDER_HEAD)]
    sups, cur, total, seen_end, furniture = [], None, None, False, False
    tu = tp = tv = 0

    def close(s, n):
        if s is None:
            return
        if not s["items"]:
            raise Refused("line %d: %s has no item line" % (n, s["name"]))
        if s["sub"] is None and len(s["items"]) > 1:
            raise Refused("line %d: %s has %d lines and no subtotal" % (n, s["name"], len(s["items"])))
    for n, l in enumerate(lines[hi + 1:], hi + 2):
        s = l.rstrip()
        st = s.strip()
        if not st:
            continue
        if st == END:
            seen_end = True
            break
        if set(st.replace(" ", "")) <= set("-="):
            continue                                            # a ruled line
        if furniture:                                           # the next page's shop name, title, page number and heads
            if RE_ORDER_HEAD.match(s):
                furniture = False
            elif st == shop or (ORDER_TITLE in st and re.search(r"Page No\.\.\d+$", st)):
                pass
            else:
                raise Refused("line %d: a line of a kind this reader does not know: %r" % (n, st[:60]))
            continue
        if re.match(r"^Continued\.\.\d+$", st):
            furniture = True
            continue
        m = RE_ORDER_TOTAL.match(s)
        if m:
            close(cur, n)
            cur = None
            total = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            continue
        m = RE_ORDER_ITEM.match(s)
        if m:
            if cur is None:
                raise Refused("line %d: an item line with no supplier above it" % n)
            name, pack, entry, date, oq, rec, pend, rate, val = m.groups()[:9]
            u, pu = _order_units(oq, pack), _order_units(pend, pack)
            cur["items"].append((u, pu, int(val)))
            rows.append([cur["name"], cur["phones"], name.strip(), pack, entry, date, _order_cell(oq), _order_cell(rec),
                         _order_cell(pend), float(rate), float(val)])
            continue
        m = RE_ORDER_SUB.match(s)
        if m:
            if cur is None or not cur["items"] or cur["sub"] is not None:
                raise Refused("line %d: a subtotal where none belongs" % n)
            cur["sub"] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            k = len(cur["items"])
            su, sp, sv = (sum(x[i] for x in cur["items"]) for i in range(3))
            if cur["sub"][0] != su or cur["sub"][1] != sp:
                raise Refused("line %d: %s's lines come to %d units, its subtotal says %d" % (n, cur["name"], su, cur["sub"][0]))
            if abs(cur["sub"][2] - sv) > k:
                raise Refused("line %d: %s's line values come to %d, its subtotal says %d" % (n, cur["name"], sv, cur["sub"][2]))
            continue
        m = RE_ORDER_SUP.match(s)
        if m and not s.startswith(" "):
            close(cur, n)
            nm = re.sub(r"\s{2,}.*$", "", m.group(1)).strip()
            ph = []
            for p in m.group(2).split():
                if not RE_ORDER_PHONE.match(p):
                    raise Refused("line %d: %s's phone cannot be read" % (n, nm))
                if p not in ph:
                    ph.append(p)
            cur = dict(name=nm, phones=", ".join(ph), items=[], sub=None)
            sups.append(cur)
            continue
        raise Refused("line %d: a line of a kind this reader does not know: %r" % (n, st[:60]))
    if not seen_end:
        raise Refused("no End of Report -- the file is incomplete")
    if total is None:
        raise Refused("no TOTAL line")
    close(cur, len(lines))
    nl = 0
    for sp_ in sups:
        for u, pu, v in sp_["items"]:
            tu, tp, tv, nl = tu + u, tp + pu, tv + v, nl + 1
    if not nl:
        raise Refused("no items")
    if total[0] != tu or total[1] != tp:
        raise Refused("the TOTAL printed (%d units) is not the sum of the lines (%d)" % (total[0], tu))
    if abs(total[2] - tv) > nl:
        raise Refused("the TOTAL value printed (%d) is not the sum of the line values (%d) within a rupee a line" % (total[2], tv))
    rows.append(["TOTAL", "", "", "", "", "", float(total[0]), "", float(total[1]), "", float(total[2])])
    return rows

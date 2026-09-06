

# ---------------------------------------------------------------------------
# S228 LOSS DESK -- THE SHEET THE OWNER SHARES. The owner, 06-Sep-2026: "a real
# assessment of the loss of pharmacy from my side, item and qty wise, for my
# record"; shareable to Darpan "on screen and printable -- A4 portrait, core data
# only". So: item, shortage, MRP each, loss at MRP, a total, and one open box per
# line for Darpan's answer. Nothing else -- no lane, no cause, no purchase rate.
# Built from the FROZEN json of the share, never from live prices, so the sheet
# reprints tomorrow exactly as it was handed over.
_SROW = 34.0          # a row a pen can write in, and a pack line the rule does not cut
_SC = [("#", _L + 14, "r", 0), ("Item", _L + 20, "l", 168), ("Short", _L + 250, "r", 0),
       ("MRP each", _L + 312, "r", 0), ("Loss at MRP", _L + 378, "r", 0),
       ("Darpan's answer", _L + 388, "l", 0)]
_SBOX = (_L + 386, _R - _L - 386)


class _SDoc(_Doc):
    """The loss sheet: taller rows, one hand box per line."""

    def shead(self, cont=False):
        p = self.pdf
        self.need(_SROW + 20)
        self.gap(6)
        if cont:
            p.text(_L, self.y - 10, "(continued)", 9, bold=True)
            self.y -= 14
        p.rect(_L, self.y - 14 + 3, _R - _L, 14, 0.9)
        yy = self.y - 14 + 6
        for label, x, align, _w in _SC:
            p.text(x, yy, label, 7.5, bold=True, align=align)
        self.y -= 14
        p.line(_L, self.y + 3, _R, self.y + 3, 0.6)

    def srow(self, i, r):
        if self.need(_SROW + 2):
            self.shead(cont=True)
        p = self.pdf
        yy = self.y - 13                       # the figures
        py = self.y - 23                       # the pack line, clear of the rule below
        loss = r.get("loss_mrp_p")
        vals = [str(i), r["item"], r.get("short_text") or _units(-abs(r["short_units"]), r.get("pack") or 1),
                _rs(r.get("mrp_unit_p")) if r.get("mrp_unit_p") is not None else "no MRP",
                _rs(loss) if loss is not None else "not priced"]
        for (label, x, align, w), v in zip(_SC[:5], vals):
            s = _fit(v, 9, w) if w else _latin(v)
            p.text(x, yy, s, 9, bold=(label == "Item"), align=align,
                   gray=(0.45 if (label in ("MRP each", "Loss at MRP") and loss is None) else 0.0))
        if r.get("packing"):
            p.text(_L + 20, py, _fit("pack %s" % r["packing"], 7, 168), 7, gray=0.45)
        x1, x2 = _SBOX[0] + 1.5, _SBOX[0] + _SBOX[1] - 1.5
        top, bot = self.y - 2.0, self.y - _SROW + 4.0
        p.line(x1, bot, x2, bot, 0.7, 0.45); p.line(x1, top, x2, top, 0.7, 0.45)
        p.line(x1, bot, x1, top, 0.7, 0.45); p.line(x2, bot, x2, top, 0.7, 0.45)
        self.y -= _SROW
        p.line(_L, self.y + 3, _R, self.y + 3, 0.3, 0.8)


def render_loss_share(s):
    """s -- one row of stock_loss_share, its `lines` already parsed. Frozen data
    only: this function must never look anything up."""
    lines = s.get("lines") or []
    total = s.get("total_p") or 0
    doc = _SDoc("Stock shortage sheet %d - count #%d" % (s.get("no") or 1, s.get("count_id") or 0),
                "%s - %s" % (CLINIC, STORE),
                "SHEET %d - COUNT #%d" % (s.get("no") or 1, s.get("count_id") or 0))
    p = doc.pdf
    p.text(_L, doc.y - 15, "%s - %s" % (CLINIC, STORE), 14, bold=True)
    doc.y -= 21
    p.text(_L, doc.y - 13, "STOCK SHORTAGE - SHEET %d FOR %s" % (s.get("no") or 1,
                                                                 (s.get("to_whom") or "DARPAN").upper()), 12, bold=True)
    doc.y -= 19
    p.line(_L, doc.y, _R, doc.y, 0.8)
    doc.y -= 6
    doc.line_text("Stock count #%d - sheet made %s IST by %s - %d item%s"
                  % (s.get("count_id") or 0, s.get("made_text") or "-", s.get("made_by") or "-",
                     len(lines), "" if len(lines) == 1 else "s"), 9, gray=0.2)
    doc.line_text("TOTAL SHORTAGE ON THIS SHEET, AT MRP:  %s" % _rs(total), 12, bold=True)
    if s.get("unpriced"):
        doc.line_text("%d line%s on this sheet has no MRP on record and is not in the total."
                      % (s["unpriced"], "" if s["unpriced"] == 1 else "s"), 8.5, gray=0.4)
    doc.gap(2)
    doc.para("These items were counted on the shelf and found short against the computer's stock. "
             "Please write against each line what you know of it - where it went, who took it, whether "
             "it is somewhere else in the shop, or that you do not know. Bring the sheet back; anything "
             "found on the shelf or accounted for is taken off this list.", 8.5, 0.25)
    doc.line_text("25 strips 4 tabs = 25 strips and 4 loose tablets; pc = pieces.", 8, gray=0.4)
    doc.shead()
    for i, r in enumerate(lines, 1):
        doc.srow(i, r)
    doc.need(_SROW + 6)
    p = doc.pdf
    p.rect(_L, doc.y - 15 + 3, _R - _L, 15, 0.94)
    p.text(_L + 20, doc.y - 15 + 6, "%d item%s short" % (len(lines), "" if len(lines) == 1 else "s"), 9, bold=True)
    p.text(_L + 378, doc.y - 15 + 6, _rs(total), 9.5, bold=True, align="r")
    doc.y -= 15
    doc.gap(10)
    doc.line_text("Answered by: ______________________    Date: ____________    Returned to: ______________________",
                  9, gray=0.2)
    return doc.finish("Sheet %d of count #%d - frozen %s IST - fingerprint %s"
                      % (s.get("no") or 1, s.get("count_id") or 0, s.get("made_text") or "-",
                         (s.get("md5") or "")[:8]))

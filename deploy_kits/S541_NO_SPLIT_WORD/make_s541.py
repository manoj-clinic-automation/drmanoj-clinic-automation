#!/usr/bin/env python3
"""make_s541.py -- kit S541 (session 313, 13-Oct-2026; D718; F-869).
Builds the new /root/finance/finance_clinic_day.py, clinic_day_pdf.py, packs.py and clinic_money.py from their LIVE bytes
(f6729d83, 150192e2, 382081fa -- each read whole at S313; clinic_money.py b3ddc8d2, its every 'split' string read, widened at
the owner's word 07:26 IST 13-Oct: "everywhere this part of split bill does not come") by exact, counted, anchored edits. Every new text is built in
memory first (F-792); nothing is written unless every anchor of every file occurs exactly once.
    python3 make_s541.py <fcd FROM> <fcd out> <pdf FROM> <pdf out> <packs FROM> <packs out> <money FROM> <money out>"""
import hashlib
import sys

FROM = {"fcd": "f6729d8345a3d77adacfecd4e33475b4", "pdf": "150192e227bbeb539e6df686e25ae2b2", "packs": "382081fa886000065e648d63dc793ece",
        "money": "b3ddc8d2ac884b4d92058c588c3378b3"}
EDITS = {"fcd": 0, "pdf": 0, "packs": 0, "money": 0}


class Refuse(Exception):
    pass


def once(src, old, new, f):
    n = src.count(old)
    if n != 1:
        raise Refuse("%s: anchor found %d times: %r" % (f, n, old[:90]))
    EDITS[f] += 1
    return src.replace(old, new, 1)


def between(src, start, end, new, f):
    """Replace src[start .. end) -- end itself is kept."""
    if src.count(start) != 1 or src.count(end) != 1:
        raise Refuse("%s: span anchors found %d / %d times: %r" % (f, src.count(start), src.count(end), start[:70]))
    i, j = src.index(start), src.index(end)
    if j <= i:
        raise Refuse("%s: span end before start: %r" % (f, start[:70]))
    EDITS[f] += 1
    return src[:i] + new + src[j:]


# ===================================================================== finance_clinic_day.py
F_DOC_OLD = '''READ-ONLY. Every route here is a SELECT. This module writes nothing, anywhere, ever.
"""
import calendar
import datetime as dt
import json
'''
F_DOC_NEW = '''READ-ONLY. Every route here is a SELECT. This module writes nothing, anywhere, ever.

S541 (13-Oct-2026, D718; F-869) -- THE OWNER, 05:28-05:34: "in the main place those payments were recorded as they were and
the split payment should totally disappear from any description" · "clearly 600 is the consultation and the other is whatever
entered in the patient bill whether it is x-ray or a procedure". A bill Docterz calls 'Split Payment' is shown line by line as it
was actually paid: its parts (clinic_day_tender) matched to its items -- one to one, a group of items to one part, or, where the
parts allow nothing else, one item shown in two parts. No parts: "mode not known", never guessed. The day's total never moves.
The SPLIT PAYMENTS card and the month table's Split column are gone. F-869: only a CONSULTATION line with a Razorpay number is
portal money. bill_parts / mode_texts / day_tender are read by clinic_day_pdf.py too -- one matching, two outputs.
"""
import calendar
import datetime as dt
import itertools
import json
'''

F_CHAN_START = 'def _channel_of(ref):'
F_CHAN_END = '\n\n\ndef _our_online_entries(con, date):'
F_CHAN_NEW = '''def _channel_of(ref, section="consult"):
    """S257 D510: "portal" when a Razorpay id was on the line, else "icici". The mode word is never consulted.
    S541 (F-869): only a CONSULTATION line is the booking -- the booked fee is the consultation fee. Another line of the same
    visit (an X-ray, a procedure) carrying the number is money the counter took, expected in ICICI."""
    return "portal" if (ref or "").strip() and (section or "") == "consult" else "icici"'''

F_BLOCK_ANCHOR = '''         ("Wallet", "online"), ("Split Payment", "split")]


def init('''
F_BLOCK_NEW = '''         ("Wallet", "online"), ("Split Payment", "split")]


# --- S541_NO_SPLIT_WORD begin -- every line shown as it was actually paid (D718; F-869) ---------------------------------
# A bill Docterz calls 'Split Payment' carries its real parts in clinic_day_tender ("Cash: .., Online Payment: .." on the
# line). Per bill -- the clinic ID of the day -- the parts are matched to its items: each item wholly to one part wherever
# the parts allow it (one to one, or a group of items to one part); where they do not, the items are filled in the page's
# order (the consultation first) and ONE item is shown in two parts. A bill with no parts reads "mode not known".
_SPLIT = "Split Payment"
_PART_RANK = {"Cash": 0, "Online Payment": 1, "Net Banking": 2, "Patient APP": 3, "Wallet": 4, "Debit Card": 5,
              "Credit Card": 6}
_SHORT = {"Online Payment": "Online", "Debit Card": "Card", "Credit Card": "Card", "Net Banking": "Net banking",
          "Patient APP": "Patient app"}
_SECTION_RANK = dict((k, i) for i, (k, _t) in enumerate(SECTIONS))
NOT_KNOWN = "mode not known"


def _allocate(items, parts):
    """items [(key, paise)] in page order, parts [(tender, paise)] -> ({key: [(tender, paise), ...]}, kind).
    kind: one (each item its own part) | grouped (items share a part) | two_parts (an item spans two parts) |
    unmatched (the parts do not add up to the items: nothing is matched)."""
    if not parts or sum(a for _k, a in items) != sum(p for _t, p in parts):
        return {}, "unmatched"
    n, m = len(items), len(parts)
    want = [p for _t, p in parts]
    if n <= 8:
        for combo in itertools.product(range(m), repeat=n):
            sums = [0] * m
            for (_k, a), j in zip(items, combo):
                sums[j] += a
            if sums == want:
                kind = "one" if all(combo.count(j) <= 1 for j in range(m)) else "grouped"
                return dict((k, [(parts[j][0], a)]) for (k, a), j in zip(items, combo)), kind
    left = list(want)
    out = {}
    for k, a in items:
        whole = next((j for j in range(m) if left[j] >= a), None)
        if whole is not None:
            left[whole] -= a
            out[k] = [(parts[whole][0], a)]
            continue
        bits = []
        for j in range(m):
            take = min(a, left[j])
            if take > 0:
                bits.append((parts[j][0], take))
                left[j] -= take
                a -= take
        out[k] = bits
    return out, "two_parts"


def bill_parts(con, date):
    """Every 'Split Payment' bill of the day: [{clinic_id, items [((section, sn), paise)], parts [(tender, paise)],
    alloc {(section, sn): [(tender, paise)]}, kind}]. kind not_known when the bill has no parts. Read-only."""
    try:
        lines = list(con.execute("SELECT section, sn, clinic_id, amount_p FROM clinic_day_line "
                                 "WHERE business_date=? AND mode=?", (date, _SPLIT)))
    except Exception:                                             # noqa: BLE001
        return []
    if not lines:
        return []
    parts = {}
    try:
        for r in con.execute("SELECT clinic_id, tender, amount_p FROM clinic_day_tender WHERE business_date=?", (date,)):
            got = parts.setdefault((r["clinic_id"] or "").strip(), {})
            got[r["tender"]] = got.get(r["tender"], 0) + int(r["amount_p"] or 0)
    except Exception:                                             # noqa: BLE001
        parts = {}
    bills = {}
    for l in lines:
        bills.setdefault((l["clinic_id"] or "").strip(), []).append(l)
    out = []
    for cid in sorted(bills):
        ls = sorted(bills[cid], key=lambda l: (_SECTION_RANK.get(l["section"], 9), l["sn"]))
        items = [((l["section"], l["sn"]), int(l["amount_p"] or 0)) for l in ls]
        pr = sorted((parts.get(cid) or {}).items(), key=lambda kv: (_PART_RANK.get(kv[0], 9), kv[0]))
        if not cid or not pr:
            alloc, kind = {}, "not_known"
        else:
            alloc, kind = _allocate(items, pr)
        out.append(dict(clinic_id=cid, items=items, parts=pr, alloc=alloc, kind=kind))
    return out


def _part_words(bits):
    return " + ".join("%s ₹%s" % (_SHORT.get(t, t), _rupees(p)) for t, p in bits)


def mode_texts(con, date):
    """{(section, sn): words} for every 'Split Payment' line of the day -- the words its Mode column shows instead.
    Plain text; the caller escapes it."""
    out = {}
    for b in bill_parts(con, date):
        for key, _a in b["items"]:
            bits = b["alloc"].get(key)
            if b["kind"] == "unmatched":
                out[key] = "the bill: " + _part_words(b["parts"])
            elif not bits:
                out[key] = NOT_KNOWN
            elif len(bits) == 1:
                out[key] = bits[0][0]
            else:
                out[key] = _part_words(bits)
    return out


def _mode_word(l, modes):
    m = (modes or {}).get((l["section"], l["sn"]))
    if m:
        return m
    return NOT_KNOWN if (l["mode"] or "").strip() == _SPLIT else l["mode"]


def day_tender(con, row):
    """_tender(row) with no 'split' bucket: every bill's matched parts in cash / online / card / other, and whatever no part
    covers in 'unknown'. The sum is the old sum by construction -- the day's total never moves."""
    t = _tender(row)
    split = t.pop("split", 0)
    t["unknown"] = 0
    if not split:
        return t
    add, other, got = {"cash": 0, "online": 0, "card": 0}, {}, 0
    if con is not None:
        known = dict(KNOWN)
        for b in bill_parts(con, row["business_date"]):
            if b["kind"] in ("not_known", "unmatched"):
                continue
            for bits in b["alloc"].values():
                for tn, p in bits:
                    k = known.get(tn)
                    if k in add:
                        add[k] += p
                    else:
                        other[tn] = other.get(tn, 0) + p
                    got += p
    if got > split:                                               # the lines say more than the day's own figure: trust neither
        t["unknown"] = split
        return t
    for k, v in add.items():
        t[k] += v
    for tn in sorted(other):
        t["other"].append((tn, other[tn]))
    t["unknown"] = split - got
    return t
# --- S541_NO_SPLIT_WORD end ---


def init('''

F_DETAIL_START = '''    splits = []
    try:
        splits = list(con.execute('''
F_DETAIL_END = '''
    if not lines:
        out.append("""<div class="card"><p>No entries were stored for this day.'''
F_DETAIL_NEW = '''    modes = mode_texts(con, date)                                     # S541 (D718): each line as it was actually paid
'''

F_SECT_CALL_OLD = '''        out.append(_section(title, rows, slips, key))
    out.append(_splits_block(splits))
'''
F_SECT_CALL_NEW = '''        out.append(_section(title, rows, slips, key, modes))
'''

F_SPLITS_START = 'def _splits_block(rows):'
F_SPLITS_END = 'def _people(lines):'

F_TL_START = '''    if t["split"]:
'''
F_TL_END = '''    return " · ".join(bits) or "—"'''
F_TL_NEW = '''    for label, p in t["other"]:
        bits.append("%s ₹%s" % (_esc(label), _rupees(p)))
    if t.get("unknown"):                                              # S541: what no part of a bill covers -- never guessed
        bits.append('<span class="unk" title="Docterz did not say how this was paid">Mode not known ₹%s</span>'
                    % _rupees(t["unknown"]))
'''

F_MONTH_START = 'def _month_table(rows, first, prev, nxt, y, m):'
F_MONTH_END = '\n\n\ndef _foot(span, u):'
F_MONTH_NEW = '''def _month_table(rows, first, prev, nxt, y, m):
    head = """
      <div class="card">
        <div class="bar">
          <h2>%s %s</h2>
          <div class="nav noprint">
            <a href="?m=%04d-%02d">‹ previous</a>
            <a href="?m=%04d-%02d">next ›</a>
            <a class="btn" href="javascript:window.print()">Print / Save as PDF</a>
          </div>
        </div>""" % (calendar.month_name[m], y, prev.year, prev.month, nxt.year, nxt.month)
    if not rows:
        return head + "<p>No days stored for this month.</p></div>"
    con = globals().get("_MPR_CON")
    tot = dict(n=0, total=0, cons=0, xray=0, proc=0, cash=0, online=0, card=0, unknown=0)
    tl = [(r, day_tender(con, r)) for r in rows]                        # S541: each bill by its parts; no Split column
    show_unk = any(t["unknown"] for _r, t in tl)
    body = []
    for r, t in tl:
        for k, v in (("n", r["total_count"]), ("total", r["total_amount_p"]),
                     ("cons", r["cons_amount_p"]), ("xray", r["xray_amount_p"]),
                     ("proc", r["proc_amount_p"]), ("cash", t["cash"]),
                     ("online", t["online"]), ("card", t["card"]), ("unknown", t["unknown"])):
            tot[k] += v or 0
        unk = ("<td class='r'>%s</td>" % (_rupees(t["unknown"]) if t["unknown"] else "—")) if show_unk else ""
        body.append(
            "<tr><td class='d'><a href='/finance/clinic/day/%s'>%s</a></td><td class='n'>%d</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r tot'>%s</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>%s"
            "<td class='n'>%s / %s</td>%s</tr>" % (
                r["business_date"], _human(r["business_date"]), r["total_count"],
                _rupees(r["cons_amount_p"]), _rupees(r["xray_amount_p"]),
                _rupees(r["proc_amount_p"]), _rupees(r["total_amount_p"]),
                _rupees(t["cash"]) if t["cash"] else "—",
                _rupees(t["online"]) if t["online"] else "—",
                _rupees(t["card"]) if t["card"] else "—",
                unk,
                r["morning"] if r["morning"] is not None else "—",
                r["evening"] if r["evening"] is not None else "—",
                _mpr_cell(con, r["business_date"])))                    # S225_DAY_MPR_LINE
    return head + """
        <div class="tscroll"><table class="grid month">
          <thead><tr>
            <th>Day</th><th class="n">Bills</th>
            <th class="r">Consult</th><th class="r">X-ray</th><th class="r">Proc</th>
            <th class="r">Total</th>
            <th class="r">Cash</th><th class="r">Online</th><th class="r">Card</th>%s
            <th class="n">M / E</th><th class="n">Bank</th>
          </tr></thead>
          <tbody>%s</tbody>
          <tfoot><tr><td>%d days</td><td class="n">%d</td>
            <td class="r">%s</td><td class="r">%s</td><td class="r">%s</td>
            <td class="r tot">%s</td>
            <td class="r">%s</td><td class="r">%s</td><td class="r">%s</td>%s
            <td></td><td></td></tr></tfoot>
        </table></div>
      </div>""" % (
        '<th class="r">Mode not known</th>' if show_unk else "",
        "".join(body), len(rows), tot["n"],
        _rupees(tot["cons"]), _rupees(tot["xray"]), _rupees(tot["proc"]),
        _rupees(tot["total"]), _rupees(tot["cash"]), _rupees(tot["online"]),
        _rupees(tot["card"]), ('<td class="r">%s</td>' % _rupees(tot["unknown"])) if show_unk else "")'''

F_SIMPLE = [
    ('channel=_channel_of(r["gateway_ref"])))', 'channel=_channel_of(r["gateway_ref"], r["section"])))'),
    ('"%s (part of a split bill %s)"', '"%s (part of bill %s)"'),
    ('    body = [_headline(latest),', '    body = [_headline(latest, con),'),
    ('def _section(title, rows, slips=None, key=""):', 'def _section(title, rows, slips=None, key="", modes=None):'),
    ('_rupees(l["amount_p"]), _esc(l["mode"]) or "—",', '_rupees(l["amount_p"]), _esc(_mode_word(l, modes)) or "—",'),
    ('def _headline(latest):', 'def _headline(latest, con=None):'),
    ('''        t = _tender(r)
        out.append("""''', '''        t = day_tender(con, r)                                         # S541: no Split -- each bill by its parts
        out.append("""'''),
    ('      A <b>Split</b> figure is a bill paid by more than one method; the breakdown is on the bill.\n',
     '      Each line shows how it was paid; a line paid two ways shows both parts.\n'),
    ('.split{background:#fff5e0;padding:1px 5px;border-radius:4px}', '.unk{background:#fff5e0;padding:1px 5px;border-radius:4px}'),
    (' .split{background:none;padding:0}', ' .unk{background:none;padding:0}'),
    ('.sn{width:34px}.cid{width:74px}.amt{width:86px}.mode{width:120px}.sh{width:76px}',
     '.sn{width:34px}.cid{width:74px}.amt{width:86px}.mode{width:170px}.sh{width:76px}\n.grid td.mode{white-space:normal}'),
    (' .sn{width:20pt}.cid{width:46pt}.amt{width:52pt}.mode{width:66pt}.sh{width:44pt}',
     ' .sn{width:20pt}.cid{width:46pt}.amt{width:52pt}.mode{width:100pt}.sh{width:44pt}'),
]


def build_fcd(src):
    f = "fcd"
    src = once(src, F_DOC_OLD, F_DOC_NEW, f)
    src = between(src, F_CHAN_START, F_CHAN_END, F_CHAN_NEW, f)
    src = once(src, F_BLOCK_ANCHOR, F_BLOCK_NEW, f)
    src = between(src, F_DETAIL_START, F_DETAIL_END, F_DETAIL_NEW, f)
    src = once(src, F_SECT_CALL_OLD, F_SECT_CALL_NEW, f)
    src = between(src, F_SPLITS_START, F_SPLITS_END, "", f)
    src = between(src, F_TL_START, F_TL_END, F_TL_NEW, f)
    src = between(src, F_MONTH_START, F_MONTH_END, F_MONTH_NEW, f)
    for old, new in F_SIMPLE:
        src = once(src, old, new, f)
    return src


# ===================================================================== clinic_day_pdf.py
P_DOC_OLD = '''READ-ONLY. Every route here is a SELECT. This module writes nothing, anywhere, ever.

ROUTES'''
P_DOC_NEW = '''READ-ONLY. Every route here is a SELECT. This module writes nothing, anywhere, ever.

S541 (13-Oct-2026, D718): the word 'Split' is gone from the PDF as from the A4 page -- each line's Mode is how it was actually
paid, from finance_clinic_day's own matching of a bill's parts to its items (one place, two outputs); the "Paid as" line counts
every bill by its parts; the SPLIT PAYMENTS table is gone. A bill with no parts reads "mode not known", never guessed.

ROUTES'''

P_IMP_OLD = '''    slip_lookup = None

bp = Blueprint("clinic_day_pdf", __name__)
'''
P_IMP_NEW = '''    slip_lookup = None

try:
    import finance_clinic_day as _fcd                             # S541: the one matching of a bill's parts to its lines
except Exception:                                                 # noqa: BLE001
    _fcd = None

bp = Blueprint("clinic_day_pdf", __name__)
'''

P_DATA_START = '''    splits = []
    if _table_exists(con, TENDERS):'''
P_DATA_END = '''

def _latest(con):'''
P_DATA_NEW = '''    if _fcd is not None:                                               # S541 (D718)
        modes, tender = _fcd.mode_texts(con, date), _fcd.day_tender(con, day)
    else:
        modes, tender = {}, _tender(day)
        tender["unknown"] = tender.pop("split", 0)
    return {"day": day, "lines": lines, "sections": sections, "people": _people(lines),
            "tender": tender, "modes": modes, "slips": slips, "books": books}
'''

P_SPLITS_START = '''    if d["splits"]:
'''
P_SPLITS_END = '''    doc.gap(10)
    for ln in _wrap("Every figure'''

P_MODEOF_OLD = '''def render_pdf(d, who=""):'''
P_MODEOF_NEW = '''def _mode_of(d, l):
    """S541: a line's Mode -- how it was actually paid (a bill's part, or the mode as recorded); never 'Split'."""
    m = (d.get("modes") or {}).get((l["section"], l["sn"]))
    if m:
        return m
    return "mode not known" if (l["mode"] or "").strip() == "Split Payment" else l["mode"]


def render_pdf(d, who=""):'''

P_SIMPLE = [
    ('    def table_row(self, i, l, title, slip=""):', '    def table_row(self, i, l, title, slip="", mode=None):'),
    ('        p.text(_COL["mode"], yy, _fit(_latin(l["mode"]) or "-", 8.5, 98), 8.5, align="c")\n',
     '''        mt = _latin(mode if mode is not None else l["mode"]) or "-"
        ms = 8.5 if _width(mt, 8.5) <= 98 else 7.5                       # S541: a line paid two ways, in smaller type
        p.text(_COL["mode"], yy, _fit(mt, ms, 112), ms, align="c")
'''),
    ('            doc.table_row(i, l, title, slip=(slip_lookup.slip_no(slips, key, l["clinic_id"]) if slip_lookup else ""))\n',
     '            doc.table_row(i, l, title, slip=(slip_lookup.slip_no(slips, key, l["clinic_id"]) if slip_lookup else ""),\n'
     '                          mode=_mode_of(d, l))\n'),
    ('    for label, key in (("Cash", "cash"), ("Online", "online"), ("Card", "card"), ("Split", "split")):',
     '    for label, key in (("Cash", "cash"), ("Online", "online"), ("Card", "card")):'),
    ('''    for label, pp in t["other"]:
        bits.append("%s Rs %s" % (label, _inr(pp)))
''', '''    for label, pp in t["other"]:
        bits.append("%s Rs %s" % (label, _inr(pp)))
    if t.get("unknown"):                                              # S541: what no part of a bill covers
        bits.append("Mode not known Rs %s" % _inr(t["unknown"]))
'''),
    ('"A Split figure is a bill paid by more than one method; the breakdown is on the bill.",',
     '"Each line shows how it was paid; a line paid two ways shows both parts.",'),
]


def build_pdf(src):
    f = "pdf"
    src = once(src, P_DOC_OLD, P_DOC_NEW, f)
    src = once(src, P_IMP_OLD, P_IMP_NEW, f)
    src = between(src, P_DATA_START, P_DATA_END, P_DATA_NEW, f)
    src = between(src, P_SPLITS_START, P_SPLITS_END, "", f)
    src = once(src, P_MODEOF_OLD, P_MODEOF_NEW, f)
    for old, new in P_SIMPLE:
        src = once(src, old, new, f)
    return src


# ===================================================================== packs.py (wording only)
K_SIMPLE = [
    ('''"'Wallet' with no booking Rs (entry error)", "Split, parts not in the export Rs", "Check")]''',
     '''"'Wallet' with no booking Rs (entry error)", "Mode not known Rs (not in the export)", "Check")]'''),
    ('''    income.append(("Split payments", "counted by their own cash / online / card parts (Docterz prints them on the line)"))
    if tot[13]:
        income.append(("of which split payments whose parts the export did not carry Rs", tot[13]))
''', '''    if tot[13]:                                                         # S541 (D718): no 'split' word in the pack
        income.append(("of which the payment mode was not in the export Rs", tot[13]))
'''),
]


def build_packs(src):
    for old, new in K_SIMPLE:
        src = once(src, old, new, "packs")
    return src


# ===================================================================== clinic_money.py (the morning match: wording; F-869)
M_SIMPLE = [
    ('''def _channel_of(ref):
    """S257 D510: "portal" when a Razorpay id was on the line, else "icici". Never the mode word."""
    return "portal" if (ref or "").strip() else "icici"''',
     '''def _channel_of(ref, section="consult"):
    """S257 D510: "portal" when a Razorpay id was on the line, else "icici". Never the mode word.
    S541 (F-869): only a CONSULTATION line is the booking; another line of the visit carrying the number is ICICI money."""
    return "portal" if (ref or "").strip() and (section or "") == "consult" else "icici"'''),
    ('channel=_channel_of(r["gateway_ref"])))', 'channel=_channel_of(r["gateway_ref"], r["section"])))'),
    ('"%s (part of split bill %s)"', '"%s (part of bill %s)"'),
    ('''        notes.append("%d split bill%s ha%s no legs recorded — that money counts in the day's total but not by tender."''',
     '''        notes.append("%d bill%s ha%s no payment parts recorded — that money counts in the day's total but not by mode."'''),
    ('"it is in the day\'s cash or card, or the bill is split. Not in the bank by nature."',
     '"it is in the day\'s cash or card, or part of a bill paid two ways. Not in the bank by nature."'),
]


def build_money(src):
    for old, new in M_SIMPLE:
        src = once(src, old, new, "money")
    return src


def main(a):
    if len(a) != 8:
        print(__doc__)
        return 2
    jobs = [("fcd", a[0], a[1], build_fcd), ("pdf", a[2], a[3], build_pdf), ("packs", a[4], a[5], build_packs),
            ("money", a[6], a[7], build_money)]
    out = []
    for f, src_p, dst_p, fn in jobs:
        raw = open(src_p, "rb").read()
        md5 = hashlib.md5(raw).hexdigest()
        if not md5.startswith(FROM[f]):
            print("REFUSED: %s is %s, expected %s" % (src_p, md5, FROM[f]))
            return 1
        try:
            new = fn(raw.decode("utf-8"))
        except Refuse as e:
            print("REFUSED: %s" % e)
            return 1
        out.append((dst_p, new.encode("utf-8")))
    for dst_p, b in out:
        with open(dst_p, "wb") as fh:
            fh.write(b)
        print("%s  %s" % (hashlib.md5(b).hexdigest(), dst_p))
    print("edits: finance_clinic_day %(fcd)d · clinic_day_pdf %(pdf)d · packs %(packs)d · clinic_money %(money)d" % EDITS)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

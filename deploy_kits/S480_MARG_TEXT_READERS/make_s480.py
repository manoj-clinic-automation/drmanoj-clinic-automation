#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s480.py -- kit S480_MARG_TEXT_READERS (D675; F-726 b, F-728, F-729, F-730).

Every file this kit changes is BUILT FROM THE LIVE BYTES by anchored edits: each anchor must occur exactly once, else the build stops
and nothing is written. The blocks that are added whole are read from this folder (txt_block_s480.py, txt_selftest_block_s480.py,
sig_blocks_s480.json). Nothing here opens a database or the network.

  --medical DIR   DIR holds the medical PC's marg_txt.py (ed17bb76) and marg_watch.py (297cc3d9)        -> marg_txt.py, marg_watch.py
  --server        reads /root/marg_ingest and /root/finance (or --ingest / --finance)                    -> the nine server files
  --manojz DIR    DIR is D:\\Downloads\\margsync (MargPull\\signatures.json, MargPull\\marg_report.py, PUSH_STOCK_DAILY.bat)
  --out DIR       where the built files are written (never beside the live ones)
  --check         with --medical / --manojz: also require the built file to be this folder's own file, byte for byte

The FROM pin of every file is checked before its first edit; a file that moved since the brief stops the build.
"""
import argparse
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = "S480_MARG_TEXT_READERS"
FROM = {
    "marg_txt.py": "ed17bb763c202f81cb8b3708fac61b52",
    "marg_watch.py": "297cc3d9ff5edddc894390426bdc463a",
    "ingest/signatures.json": "64943ac6719a0f2ee06a15ef56d8c3d1",
    "ingest/marg_report.py": "eeab56055be76fec9531399ce9a0556e",
    "ingest/lib/marg_report.py": "eeab56055be76fec9531399ce9a0556e",
    "ingest/marg_take.py": "b41195e4ce853272ecf25b06343e3e16",
    "ingest/lib/push_expected.py": "4b3b700c1640591a3723d4fce3de5603",
    "finance/marg_report.py": "f9370dde648f629461d4efac2b4805af",
    "finance/marg_door.py": "6a2366638234bf0ddf9c7d6c745c975b",
    "finance/salts_refresh.py": "40cb26159c59d55d33d871abe36646ef",
    "finance/reports_tile.py": "9d2244a6d56d3791428982565f620a97",
    "manojz/signatures.json": "7f72c572808218fbfc008373336beea8",
    "manojz/marg_report.py": "28b47d447cfd966411742055717a5c56",
    "manojz/PUSH_STOCK_DAILY.bat": "5cbec862593e201884b8f372775c7db2",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rd(p):
    with io.open(p, "rb") as fh:
        return fh.read()


def block(name):
    return rd(os.path.join(HERE, name)).decode("utf-8")


def edit(name, src, pairs):
    """Anchored edits: every OLD must occur exactly once in what the edits before it left."""
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            raise SystemExit("!! %s: anchor %d occurs %d times, not once -- nothing built (%r)" % (name, i, n, old[:70]))
        src = src.replace(old, new)
    return src


def pinned(name, raw):
    if md5(raw) != FROM[name]:
        raise SystemExit("!! %s is %s, not its FROM pin %s -- someone changed it since the brief; nothing built" % (name, md5(raw), FROM[name]))
    return raw.decode("utf-8")


# ----------------------------------------------------------------------------------------------------------------- marg_txt.py (A, B.1)
def build_marg_txt(src, old_bytes):
    cut = block("txt_block_s480.py")
    st = block("txt_selftest_block_s480.py")
    out = edit("marg_txt.py", src, [
        ("    python marg_txt.py report.txt out.XLS      convert one file\n",
         "S480 (D675, 05-Oct-2026 -- \"the system reads every report the shop exports, in text\"): Marg's Excel export is its text page cut into\n"
         "  cells at the column heads (measured: three same-moment pairs, 4,141 cells, none different). So every other report is read by ONE\n"
         "  cutter (page_to_sheet: a word belongs to the column in which it ends; a line that is one run of words is one cell) and a short\n"
         "  spec (TEXT_SPECS: title, heads, end, integrity check) -- purchase (four shapes), the salt, category and item lists, the short sale\n"
         "  statement, sale return (two shapes), the batch-wise valuation, expiry, the stock register. The three readers above are not\n"
         "  touched: every text they took converts to the same bytes. AN EMPTY REPORT IS AN ANSWER: a sale report with no bill, dated a day\n"
         "  BEFORE the day it was exported, is a no-sale day (title, heads, its one total row); dated the export day it is refused in the\n"
         "  staff's words -- today is not over. Other empties are recognised and refused as EMPTY until a real empty sample is verified.\n\n"
         "    python marg_txt.py report.txt out.XLS      convert one file\n"),
        ('VERSION = "S454"\n', 'VERSION = "S480"\n'),
        ('''def kind(raw):
    """"SALE", "STOCK", "ORDER" (S454) or None."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\\xd0\\xcf\\x11\\xe0", b"PK\\x03\\x04", b"%PDF"):
        return None
    t = raw.decode("latin-1")
    head = t[:4000]
    if END not in t[-400:]:
        return None
    if TITLE in head and "BILL NO." in head and "CASH" in head:
        return "SALE"
    if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):
        return "STOCK"
    if ORDER_TITLE in head and RE_ORDER_HEAD.search(head):                 # S454 (D666)
        return "ORDER"
    return None
''', '''def kind(raw):
    """"SALE", "STOCK", "ORDER" (S454) -- the three live kinds answer first -- then the kind word of a TEXT_SPECS entry (S480):
    PURCHASE, SALT, CATEGORY, ITEMS, SALE_SHORT, RETURN, VALUATION, EXPIRY, LEDGER. Or None."""
    if not raw or len(raw) > MAX_BYTES or raw[:4] in (b"\\xd0\\xcf\\x11\\xe0", b"PK\\x03\\x04", b"%PDF"):
        return None
    t = raw.decode("latin-1")
    head = t[:4000]
    if END in t[-400:]:
        # S480: SALE is the statement whose own head line carries CASH -- a short statement's bill rows say .CASH too
        if TITLE in head and any(l.startswith("BILL NO.") and "CASH" in l for l in head.replace("\\r", "\\n").split("\\n")):
            return "SALE"
        if RE_STOCK_TITLE.search(head) and RE_STOCK_HEAD.search(head):
            return "STOCK"
        if ORDER_TITLE in head and RE_ORDER_HEAD.search(head):                 # S454 (D666)
            return "ORDER"
    sp = spec_of(raw)                                                          # S480: the end test is each spec's own
    return sp["kind"] if sp else None
'''),
        ("def _cols(header_line):\n", cut + "def _cols(header_line):\n"),
        ('''def to_rows(raw):
    """The nine-column sheet, as a list of rows of cells (str, or float for a number)."""
''', '''def to_rows(raw, exported_at=None):
    """The nine-column sheet, as a list of rows of cells (str, or float for a number). S480: exported_at is the file's own time --
    it decides whether a report with no bill is a day that is over (see _empty_day)."""
    return _sale_rows(raw, exported_at)[0]


def _sale_rows(raw, exported_at=None):
    """(rows, extra) -- extra is {} for a report with bills, {"empty": True, "as_on": dd-mm-yyyy} for a no-sale day."""
'''),
        ('''    rows = [[title, "", "", "", "", "", "", "", ""], list(HEAD)]
    seen_end = False
''', '''    rows = [[title, "", "", "", "", "", "", "", ""], list(HEAD)]
    seen_end = False
    foot = None                                                          # S480: a DAY TOTAL row that carries the bill count
'''),
        ('''            else:
                rows.append(["", "", label] + nums)
            continue
''', '''            else:
                rows.append(["", "", label] + nums)
                m0 = re.search(r"Total No\\. of\\s+(Bills:\\s*\\d+)", s)             # S480: the zero-bill day prints its count here
                if m0:
                    foot = (m0.group(1), nums)
            continue
'''),
        ('''    if not any(r[2] == "GRAND TOTAL :" for r in rows):
        raise Refused("no GRAND TOTAL line")
    return rows
''', '''    if not any(r[2] == "GRAND TOTAL :" for r in rows):
        empty = _empty_day(rows, foot, exported_at)                      # S480 (D675 a, F-729): the no-sale day
        if empty is None:
            raise Refused("no GRAND TOTAL line")
        return empty
    return rows, {}
'''),
        ('''def convert(raw):
    """(xls_bytes, info) for a text export; raises NotThisReport / Refused."""
    k = kind(raw)
    rows = stock_rows(raw) if k == "STOCK" else (order_rows(raw) if k == "ORDER" else to_rows(raw))     # S454: ORDER
    return ole2(workbook_stream(rows)), {"rows": len(rows), "version": VERSION, "kind": k or "SALE"}
''', '''def convert(raw, exported_at=None):
    """(xls_bytes, info) for a text export; raises NotThisReport / Refused. S480: exported_at -- the file's own time, or a kept
    copy's stamp -- is what tells a no-sale day from a report of today; info carries "empty" and "as_on" for a no-sale day."""
    k = kind(raw)
    extra = {}
    if k == "STOCK":
        rows = stock_rows(raw)
    elif k == "ORDER":                                                   # S454
        rows = order_rows(raw)
    elif k in (None, "SALE"):
        rows, extra = _sale_rows(raw, exported_at)
    else:                                                                # S480: a report read through the cutter
        rows = spec_rows(raw)
    info = {"rows": len(rows), "version": VERSION, "kind": k or "SALE"}
    info.update(extra)
    return ole2(workbook_stream(rows)), info
'''),
        ("def selftest(sample=None):\n", st + "def selftest(sample=None):\n"),
        ('''    if sample:
        raw = open(sample, "rb").read()
        xls, info = convert(raw)
''', '''    _selftest_s480(ck)                                                   # S480: one check per spec, the three byte-equalities, the empty day
    if sample:
        raw = open(sample, "rb").read()
        xls, info = convert(raw, exported_at=os.path.getmtime(sample))
'''),
        ('''        x, info = convert(open(sys.argv[1], "rb").read())
''', '''        x, info = convert(open(sys.argv[1], "rb").read(), exported_at=os.path.getmtime(sys.argv[1]))
'''),
    ])
    # the bytes marg_txt S454 makes of its own three samples, measured here from the live file itself (never typed in)
    g = {"__name__": "marg_txt_s454"}
    exec(compile(old_bytes, "marg_txt_s454.py", "exec"), g)
    for k, name in (("SALE", "SELFTEST_SAMPLE"), ("STOCK", "STOCK_SAMPLE"), ("ORDER", "ORDER_SAMPLE")):
        out = edit("marg_txt.py", out, [("@@MD5_%s@@" % k, md5(g["convert"](g[name])[0]))])
    return out


# --------------------------------------------------------------------------------------------------------------- marg_watch.py (D, B.1)
def build_marg_watch(src):
    return edit("marg_watch.py", src, [
        ("OFF SWITCH (S259)\n",
         "S480 (05-Oct-2026, D675; F-728): NO MARG TEXT IS DROPPED UNLOGGED. One export writes the page twice (user_<id>.txt, then report.txt);\n"
         "    a list, a valuation, an expiry report or a register saved under the first name was judged \"not a Marg report\", not kept and not\n"
         "    logged, and its twin then skipped as already seen. Now a text the reader does not take is KEPT and logged whenever it carries\n"
         "    Marg's end mark in its tail, the firm's name in its head, or a report word in its first 4,000 bytes -- whatever the file is\n"
         "    called. The note's kind is one word per report (PURCHASE, SALT, CATEGORY, ITEMS, SALE_SHORT, RETURN, VALUATION, EXPIRY, LEDGER\n"
         "    beside SALE, STOCK, ORDER); the census lists every such text. The reader is given the file's own time (a kept copy's stamp), so\n"
         "    a sale report with no bill is taken as a no-sale day only when its day is over; refused as \"today\", its bytes are NOT remembered\n"
         "    as seen -- the same report exported on a later day is taken.\n\n"
         "OFF SWITCH (S259)\n"),
        ('''TXT_SEEN = set()        # md5s of text already judged this run -- converted, or not ours
''', '''TXT_SEEN = set()        # md5s of text already judged this run -- converted, or not ours
# S480 (F-728): what makes a text a Marg report, whatever its file is called. A text the reader does not take is KEPT when it carries
# Marg's end mark in its tail, the firm's name in its head, or any of these words in its first 4,000 bytes.
KEEP_WORDS = (b"STATEMENT", b"PENDING ORDERS", b"CLOSING STOCK", b"ITEM LIST", b"LIST OF ITEMS", b"STOCK VALUATION", b"EXP. BEFORE",
              b"STOCK REGISTER", b"SALE RETURN")
FIRM = b"SANJEEVNI MEDICOS"
END_MARK = b"*** End of Report ***"
# S480 (D.2): the title words of each report the reader has a spec for -> the one word its refusal note carries, and what a reason calls it
KIND_TITLES = (("PURCHASE STATEMENT", "PURCHASE", "a purchase statement"), ("SALT WISE ITEM LIST", "SALT", "a salt-wise item list"),
               ("CATEGORY WISE ITEM LIST", "CATEGORY", "a category-wise item list"), ("LIST OF ITEMS", "ITEMS", "a list of items"),
               ("SALE RETURN", "RETURN", "a sale return report"), ("STOCK VALUATION", "VALUATION", "a stock valuation"),
               ("EXP. BEFORE", "EXPIRY", "a stock expiry report"), ("STOCK REGISTER", "LEDGER", "a stock register"))
TODAY_NOTE = "the reader refused it: aaj ki report -- kal ki tareekh chun kar dobara banaiye"      # fixed words; never a line of the file
EMPTY_NOTE = "the reader refused it: an empty report -- kept, not yet verified"
'''),
        ('''    if "BILL WISE SALES STATEMENT" not in head:
        first = next((l.strip() for l in t.splitlines() if l.strip()), "")[:80]
        return "not a bill-wise sales statement (it begins: %r)" % first
''', '''    if "BILL WISE SALES STATEMENT" not in head:
        k = _kind_of(raw)                                       # S480 (D.2): the kind it recognised is named
        what = dict((x[1], x[2]) for x in KIND_TITLES).get(k)
        if what and k == "LEDGER" and "Issued :" not in t[-1200:]:
            return "%s without its closing 'Received : / Issued :' lines (cut short?)" % what
        if what and k != "LEDGER" and "*** End of Report ***" not in tail:
            return "%s without the '*** End of Report ***' line at the end (cut short?)" % what
        if what:
            return "%s the reader cannot take (its title or column heads are not the ones it knows)" % what
        first = next((l.strip() for l in t.splitlines() if l.strip()), "")[:80]
        return "not a report the reader knows (it begins: %r)" % first
'''),
        ('''def _kind_of(raw):
    head = raw[:4000].decode("latin-1", "replace")
    if "PENDING ORDERS (PURCHASE)" in head:
        return "ORDER"
    if "CLOSING STOCK" in head:
        return "STOCK"
    if "BILL WISE SALES STATEMENT" in head:
        return "SALE"
    return ""
''', '''def _kind_of(raw):
    """One word for the report a text looks like, by its own title words -- never by its file's name. S480: one word per spec."""
    head = raw[:4000].decode("latin-1", "replace")
    if "PENDING ORDERS (PURCHASE)" in head:
        return "ORDER"
    if "CLOSING STOCK" in head:
        return "STOCK"
    if "BILL WISE SALES STATEMENT" in head:
        short = "BILL VALUE" in head and not any(l.startswith("BILL NO.") and "CASH" in l for l in head.splitlines())
        return "SALE_SHORT" if short else "SALE"
    for words, k, _what in KIND_TITLES:                         # S480 (D.2)
        if words in head:
            return k
    return ""


def _is_marg_text(path, raw):
    """S480 (D.1, F-728): is this text a Marg report -- by what is in it, whatever the file is called?"""
    head = raw[:4000]
    return bool(REPORTISH.match(os.path.basename(path)) or END_MARK in raw[-400:] or FIRM in head or any(w in head for w in KEEP_WORDS))


def _exported_at(path):
    """S480 (B.1): when a text was exported -- the file's own time; for a copy kept in _captured_txt\\\\refused, the stamp in its name."""
    m = re.match(r"^(\\d{8}-\\d{6})__", os.path.basename(path))
    if m and os.path.basename(os.path.dirname(os.path.abspath(path))).lower() == "refused":
        try:
            return time.mktime(time.strptime(m.group(1), "%Y%m%d-%H%M%S"))
        except (ValueError, OverflowError):
            pass
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _convert(marg_txt, raw, when):
    """S480: convert() with the export time. An older marg_txt beside this file (the two arrive in either order) takes the text alone."""
    try:
        return marg_txt.convert(raw, exported_at=when)
    except TypeError as ex:
        if "exported_at" not in str(ex):
            raise
        return marg_txt.convert(raw)
'''),
        ('''    w = " ".join(str(why or "").split())
    if w.startswith("the reader refused it"):
''', '''    w = " ".join(str(why or "").split())
    if w.startswith("the reader refused it") and "aaj ki report" in w and "kal ki tareekh" in w:
        return TODAY_NOTE                                       # S480 (B.1): the reader's own fixed words for a zero-bill report of today
    if w.startswith("the reader refused it: an empty report"):
        return EMPTY_NOTE                                       # S480 (D675 a): recognised, kept, not yet verified
    if w.startswith("the reader refused it"):
'''),
        ('''    name = re.split(r"[\\\\/]", str(path))[-1][:120]
    return {"name": name, "md5": tmd5, "kind": _kind_of(raw), "reason": _note_reason(why)}
''', '''    name = re.split(r"[\\\\/]", str(path))[-1][:120]
    kind, reason = _kind_of(raw), _note_reason(why)
    if kind and kind not in ("SALE", "STOCK", "ORDER"):         # S480 (D.2): the owner's line names a refused text by what it is
        reason = ("%s text -- %s" % (kind, reason))[:240]
    return {"name": name, "md5": tmd5, "kind": kind, "reason": reason}
'''),
        ('''    for l in head.splitlines():
        t = l.strip()
        if t:
            return t[:90] if ("STATEMENT" in t or "REPORT" in t.upper()) else ""
    return ""
''', '''    for l in head.splitlines()[:14]:                            # S480 (D.3): the title may stand under a letterhead
        t = l.strip()
        if t and any(w.decode("latin-1") in t for w in KEEP_WORDS):
            return t[:90]
    for l in head.splitlines():
        t = l.strip()
        if t:
            return t[:90] if ("STATEMENT" in t or "REPORT" in t.upper()) else ""
    return ""
'''),
        ('''        if REPORTISH.match(os.path.basename(path)) or b"STATEMENT" in raw[:4000] or b"PENDING ORDERS" in raw[:4000]:   # S454: + order sheet
''', '''        if _is_marg_text(path, raw):                            # S480 (F-728): the content decides, whatever the file is called
'''),
        ('''    try:
        xls, info = marg_txt.convert(raw)
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])
        TXT_VERDICT[path] = (time.time(), "NOT TAKEN: the reader refused it: %s" % str(ex)[:300])
        TXT_SEEN.add(tmd5)
        return False
''', '''    try:
        xls, info = _convert(marg_txt, raw, _exported_at(path))  # S480 (B.1): the file's own time says whether an empty day is over
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])
        TXT_VERDICT[path] = (time.time(), "NOT TAKEN: the reader refused it: %s" % str(ex)[:300])
        if ex.__class__.__name__ == "TodayNotOver":             # S480: the same bytes exported on a later day ARE taken -- this
            if stat_key:                                        # file is judged, its bytes are not remembered as seen
                TXT_STAT[path] = stat_key
        else:
            TXT_SEEN.add(tmd5)
        return False
'''),
        ('''        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))
''', '''        # S480 (F-728, D.1-D.3, B.1): a Marg text under ANY name is kept or taken; the kind words; the census; the empty day
        if hasattr(marg_txt, "_s480_samples"):
            M_ = marg_txt._s480_samples()
            TXT_SEEN.clear(); TXT_STAT.clear()
            SL = M_["SALT_WISE_ITEM_LIST"]
            cutsl = SL[:SL.rindex(b"***")]
            u1 = os.path.join(tdir, "17476", "user_aa1.txt"); open(u1, "wb").write(cutsl)
            n480 = len(NOTE_SINK); m480 = []
            capture(u1, sp2, cap2, m480.append)
            kept480 = [f for f in os.listdir(refd) if hashlib.md5(cutsl).hexdigest() in f and f.endswith(".txt") and not f.endswith(".why.txt")]
            ck("S480: a salt list cut short and saved as user_<id>.txt is KEPT and logged, its note says SALT (before: dropped, no line)",
               len(kept480) == 1 and any("NOT TAKEN" in m for m in m480) and len(NOTE_SINK) == n480 + 1 and NOTE_SINK[-1]["kind"] == "SALT"
               and NOTE_SINK[-1]["reason"].startswith("SALT text -- a salt-wise item list without"))
            tw = os.path.join(tdir, "17476", "report.txt"); open(tw, "wb").write(cutsl)
            capture(tw, sp2, cap2, m480.append)
            ck("S480: its report.txt twin with the same bytes is not kept twice and sends no second note",
               len([f for f in os.listdir(refd) if hashlib.md5(cutsl).hexdigest() in f and f.endswith(".why.txt")]) == 1
               and len(NOTE_SINK) == n480 + 1)
            u2 = os.path.join(tdir, "17476", "user_aa2.txt"); open(u2, "wb").write(SL)
            ck("S480: the complete salt list under the same kind of name is TAKEN, as marg_txt's own .XLS",
               capture(u2, sp2, cap2, lambda m: None) is True
               and any(md5_of(os.path.join(sp2, f)) == hashlib.md5(marg_txt.convert(SL)[0]).hexdigest() for f in os.listdir(sp2)))
            ck("S480: every report's kind word reaches the note",
               sorted(set(note_of("x.txt", "0" * 32, M_[k_][:-60], "cut")["kind"] for k_ in M_))
               == sorted(["PURCHASE", "SALT", "CATEGORY", "ITEMS", "SALE_SHORT", "RETURN", "VALUATION", "EXPIRY", "LEDGER"]))
            cen = text_census([tdir])
            ck("S480: the census lists a text by its title even under a letterhead, and still never the notes",
               any("user_aa1.txt" in l and "SALT WISE ITEM LIST" in l for l in cen) and not any("shopping" in l for l in cen)
               and _title_of(u2) == "SALT WISE ITEM LIST")
            vfile = os.path.join(tdir, "val.txt"); open(vfile, "wb").write(M_["STOCK_VALUATION_BATCHWISE"])
            ck("S480: under a letterhead the census reads the report's title, not the shop's name",
               _title_of(vfile).startswith("WHOLE STORES STOCK VALUATION"))
            E_ = marg_txt.EMPTY_DAY_SAMPLE                       # AS ON 02-01-2030
            day = lambda d, h=10: time.mktime((2030, 1, d, h, 0, 0, 0, 0, -1))
            e1 = os.path.join(tdir, "17476", "user_ab1.txt"); open(e1, "wb").write(E_); os.utime(e1, (day(2), day(2)))
            m480 = []
            t1 = capture(e1, sp2, cap2, m480.append)
            emd5 = hashlib.md5(E_).hexdigest()
            ck("S480: a zero-bill sale report exported on its own day is refused in the staff's words, kept, and NOT remembered as seen",
               t1 is False and emd5 not in TXT_SEEN and any("kal ki tareekh" in m for m in m480)
               and NOTE_SINK[-1]["md5"] == emd5 and NOTE_SINK[-1]["reason"] == TODAY_NOTE and NOTE_SINK[-1]["kind"] == "SALE")
            old480 = os.path.join(refd, "20300102-094321__user_ab1__%s.txt" % emd5)
            kept_e = [f for f in os.listdir(refd) if emd5 in f and f.endswith(".txt") and not f.endswith(".why.txt")]
            os.replace(os.path.join(refd, kept_e[0]), old480); os.utime(old480, (day(9), day(9)))
            TXT_STAT.clear()
            ck("S480: its kept copy, offered again at a start, stays refused by the stamp in its name (whatever the copy's own file time)",
               len(kept_e) == 1 and capture_text(old480, sp2, cap2, lambda m: None) is False and emd5 not in TXT_SEEN
               and len([f for f in os.listdir(refd) if emd5 in f and f.endswith(".why.txt")]) == 1)
            e2 = os.path.join(tdir, "17476", "report.txt"); open(e2, "wb").write(E_); os.utime(e2, (day(3), day(3)))
            ck("S480: the SAME bytes exported the next day are taken as a no-sale day, as marg_txt's own EMPTY sheet",
               capture(e2, sp2, cap2, lambda m: None) is True
               and any(md5_of(os.path.join(sp2, f)) == hashlib.md5(marg_txt.convert(E_, exported_at=day(3))[0]).hexdigest()
                       for f in os.listdir(sp2)))
        else:
            ck("S480: marg_txt S480 is beside this file (an older reader: the S480 checks cannot run)", False)
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))
'''),
        ('''    out("marg_watch S454 P4C starting -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again)"
''', '''    out("marg_watch S480 starting -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again)"
'''),
    ])


# ------------------------------------------------------------------------------------------------- marg_report.py (B.2; every copy)
def build_marg_report(name, src):
    return edit(name, src, [
        ('''    last_bill_key = None

    for r in range(hdr_row + 1, sh.nrows):
''', '''    last_bill_key = None
    lone_total, lone_bills = None, None        # S480: a DAY TOTAL row met before any date row

    for r in range(hdr_row + 1, sh.nrows):
'''),
        ('''        if "DAY TOTAL" in c2:
            if cur:
                days[cur]["declared"] = {k: paise(_cell(sh, r, COL[k]))
                                         for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
            continue
''', '''        if "DAY TOTAL" in c2:
            if cur:
                days[cur]["declared"] = {k: paise(_cell(sh, r, COL[k]))
                                         for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
            else:
                # S480 (D675 a): a day with no bill prints no date row -- only "Total No. of Bills: 0 ... DAY TOTAL"
                lone_total = {k: paise(_cell(sh, r, COL[k]))
                              for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
                m = RE_BILLS_FOOTER.search(c1) or RE_BILLS_FOOTER.search(c0)
                lone_bills = int(m.group(1)) if m else None
            continue
'''),
        ('''    errors, warnings = [], []

    if grand is None:
        errors.append(
''', '''    errors, warnings = [], []

    # S480 (D675 a, F-729): AN EMPTY REPORT IS AN ANSWER, NOT A FAULT. A single day's statement (AS ON) with its heads, no bill row,
    # no item line and the one row "Total No. of Bills: 0 ... DAY TOTAL" of zeros is a day on which nothing was sold. The day comes
    # from the TITLE, because an empty day prints no date row. Every other check below is unchanged.
    empty = False
    if (not order and grand is None and items_seen == 0 and variant == "single-day" and span[0]
            and lone_total is not None and lone_bills == 0 and all(v == 0 for v in lone_total.values())):
        empty = True
        days[span[0]] = {"date": span[0], "bills": [], "items": [], "declared": dict(lone_total)}
        order.append(span[0])
        footer_bills = 0
    bill_rows = sum(len(days[d]["bills"]) for d in order)

    if grand is None and not bill_rows and not empty:
        errors.append(
            "no bill row and no GRAND TOTAL row, and not the zero-bill day Marg prints (AS ON one day, "
            "Total No. of Bills: 0, DAY TOTAL 0.00) — the file is incomplete, or of a kind this reader does not know.")
    if grand is None and bill_rows:               # S480: TRUNCATED only where at least one bill row exists
        errors.append(
'''),
        ('''        "ok": not errors,
''', '''        "ok": not errors,
        "empty": empty,                # S480 (D675 a): a no-sale day -- one day, from the title, no bills
'''),
    ])


# ----------------------------------------------------------------------------------------------------------- signatures.json (B.3, E)
def _sig_blocks():
    return json.loads(block("sig_blocks_s480.json"))


def build_signatures(name, src, add_category):
    B = _sig_blocks()
    pairs = []
    if add_category:                                    # the server's copy gains the block manojz's copy already has (S270)
        pairs.append(('''    {
      "type": "STOCK_VALUATION",
      "variant": "STRIPS_TAB",
''', B["CATEGORY"] + '''    {
      "type": "STOCK_VALUATION",
      "variant": "STRIPS_TAB",
'''))
    pairs += [
        ('''      "deep_verify": "marg_report",
      "uploadable": true,
      "end_marker": "GRAND TOTAL"
    },
''', '''      "deep_verify": "marg_report",
      "uploadable": true,
      "end_marker": "Total No. of",
      "end_marker_note": %s
    },
''' % json.dumps(B["DETAIL_NOTE"], ensure_ascii=False)),
        ('''      "end_marker_note": "S201: NO end_marker -- no sample of this variant exists to derive one from, so truncation is NOT detected here. Do not guess one; capture a real export first."
''', '''      "end_marker": "Total No. of",
      "end_marker_note": %s
''' % json.dumps(B["SUMMARY1_NOTE"], ensure_ascii=False)),
        ('''    {
      "type": "SALT_WISE_ITEM_LIST",
''', B["LEDGER_TEXT"] + '''    {
      "type": "SALT_WISE_ITEM_LIST",
'''),
        ('''    {
      "type": "STOCK_VALUATION",
      "variant": "STRIPS_TAB",
''', B["VALUATION_BATCHWISE"] + '''    {
      "type": "STOCK_VALUATION",
      "variant": "STRIPS_TAB",
'''),
    ]
    out = edit(name, src, pairs)
    json.loads(out)                                     # it must still be JSON
    return out


# -------------------------------------------------------------------------------------------------------------------- marg_take.py (B.4)
def build_marg_take(src):
    return edit("marg_take.py", src, [
        ('''# ------------------------------------------------------------------ the door
def take(raw, name="", source="manual", db=None, archive=None):
''', '''def _s480_empty_day(path):
    """S480 (D675 a, F-729): the ISO day of a VERIFIED sale report that carries no bill -- a no-sale day -- else ''. The day is the
    title's (an empty day prints no date row); the reader (marg_report.read_report) says so with empty=True."""
    try:
        import marg_report as MR                                 # noqa: PLC0415
        rep = MR.read_report(path)
        if rep.get("ok") and rep.get("empty") and rep.get("days"):
            return rep["days"][0].get("date") or ""
    except Exception:                                            # noqa: BLE001
        pass
    return ""


# ------------------------------------------------------------------ the door
def take(raw, name="", source="manual", db=None, archive=None):
'''),
        ('''            if typ == "SALE_BILLWISE" and verdict == "VERIFIED":
                rows = MI.sale_lines(local)
                nlines = len(rows)
                con.execute("DELETE FROM mi_sale_line WHERE md5=?", (md5,))
                con.executemany(
                    "INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name, "
                    "pack, qty_raw, qty_strips, qty_loose, amount_p, expiry_ym, batch) VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?)", [(md5,) + t for t in rows])
''', '''            empty_day = ""
            # S480 (A.2): the short statement (SUMMARY1 -- BILL VALUE, no item lines) lands as the signature says: no line is read from
            # it, the file is deleted as every sale file is (S186), and it is never the day's sale report.
            if typ == "SALE_BILLWISE" and verdict == "VERIFIED" and (r.get("variant", "") or "") != "SUMMARY1":
                empty_day = _s480_empty_day(local)               # S480 (D675 a, F-729): a no-sale day
                rows = MI.sale_lines(local)
                nlines = len(rows)
                if empty_day and not rows:
                    r["date_from"] = r["date_to"] = empty_day    # the title's day; mi_sale_line is not touched for this md5
                else:
                    con.execute("DELETE FROM mi_sale_line WHERE md5=?", (md5,))
                    con.executemany(
                        "INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name, "
                        "pack, qty_raw, qty_strips, qty_loose, amount_p, expiry_ym, batch) VALUES "
                        "(?,?,?,?,?,?,?,?,?,?,?,?,?)", [(md5,) + t for t in rows])
'''),
        ('''            when = MI.now_ist().isoformat()
''', '''            when = MI.now_ist().isoformat()
            reason = (r.get("reason", "") or "")[:300]
            if empty_day and not nlines:
                reason = "EMPTY \\u2014 no sale on %s" % empty_day    # S480 (B.4): the chain (S481) reads this row
'''),
        ('''                 (r.get("reason", "") or "")[:300], os.path.basename(dest), kept, nlines,
''', '''                 reason, os.path.basename(dest), kept, nlines,
'''),
        ('''                       reason=(r.get("reason", "") or "")[:300], lines=nlines, kept=kept,
''', '''                       reason=reason, lines=nlines, kept=kept,
'''),
    ])


# ---------------------------------------------------------------------------------------------------------------- push_expected.py (B.5)
def build_push_expected(src):
    return edit("push_expected.py", src, [
        ('''        for d in rep.get("days") or []:
            for it in d.get("items") or []:
                bd = dkey(it.get("bill_date"))
''', '''        for d in rep.get("days") or []:
            if rep.get("empty"):                               # S480 (D675 a, F-729): a no-sale day is a sale day with no lines
                ed = dkey(d.get("date"))
                if ed is not None and ed > after and not (upto and ed > upto):
                    days.add(ed)
            for it in d.get("items") or []:
                bd = dkey(it.get("bill_date"))
'''),
    ])


# -------------------------------------------------------------------------------------------------------------------- marg_door.py (G)
def build_marg_door(src):
    return edit("marg_door.py", src, [
        ('''_S454_KINDS = {"SALE": "SALE_BILLWISE", "STOCK": "STOCK_CLOSING", "ORDER": "ORDER_PENDING", "": ""}
''', '''_S454_KINDS = {"SALE": "SALE_BILLWISE", "STOCK": "STOCK_CLOSING", "ORDER": "ORDER_PENDING", "": "",
               # S480 (D.2 / G): one word per text spec of marg_txt S480. PURCHASE is four signature types, not one: its row carries no
               # type, and the watcher writes the kind into the reason ("PURCHASE text -- ...").
               "PURCHASE": "", "SALT": "SALT_WISE_ITEM_LIST", "CATEGORY": "CATEGORY_WISE_ITEM_LIST", "ITEMS": "ITEM_MASTER",
               "SALE_SHORT": "SALE_BILLWISE", "RETURN": "SALE_RETURN", "VALUATION": "STOCK_VALUATION", "EXPIRY": "STOCK_EXPIRY",
               "LEDGER": "STOCK_ITEM_LEDGER"}
'''),
    ])


# ---------------------------------------------------------------------------------------------------------------- salts_refresh.py (F)
def build_salts_refresh(src):
    return edit("salts_refresh.py", src, [
        ('''    sh = _sheet(path, ingest)
    cur, out = None, []
    for r in range(3, sh.nrows):
''', '''    sh = _sheet(path, ingest)
    cur, out = None, []
    # S480 (F-730 / F-726 b): the sheet's own first cell -- the firm's name, printed again at the head of every page -- and Marg's
    # advertisement line are never a salt. (Every item that opened a page was filed under the firm's name.)
    firm = str(sh.cell_value(0, 0)).strip().upper() if sh.nrows else ""
    for r in range(3, sh.nrows):
'''),
        ('''        elif not pk and not re.match(r"^\\d", a) and a.upper() != "SALT WISE ITEM LIST":
            cur = a.upper()
''', '''        elif (not pk and not re.match(r"^\\d", a) and a.upper() != "SALT WISE ITEM LIST"
              and a.upper() != firm and not re.search(r"MARG ERP|QRCODE|\\bCall\\b", a, re.I)):
            cur = a.upper()
'''),
    ])


# ----------------------------------------------------------------------------------------------------------------- reports_tile.py (A.2)
def build_reports_tile(src):
    return edit("reports_tile.py", src, [
        ('''    q = ("SELECT md5, type, verdict, reason, pc_verdict, date_from, date_to, received_at, stamp, drive_name, server_name "
''', '''    q = ("SELECT md5, type, variant, verdict, reason, pc_verdict, date_from, date_to, received_at, stamp, drive_name, server_name "
'''),
        ('''    ok = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), day_from=y_iso, day_to=y_iso) if r["verdict"] == "VERIFIED"]
    if not ok and _table_exists(cx, "marg_push_staging"):
''', '''    # S480 (A.2): the day's sale report is SALE_BILLWISE with variant DETAIL only. The short statement (SUMMARY1 -- BILL VALUE, no item
    # lines) lands and is archived, but it never ticks this row.
    _s480 = [r for r in _mi_rows(cx, ("SALE_BILLWISE",), day_from=y_iso, day_to=y_iso) if r["verdict"] == "VERIFIED"]
    ok = [r for r in _s480 if (r.get("variant") or "DETAIL") == "DETAIL"]
    _s480 = [r for r in _s480 if (r.get("variant") or "") == "SUMMARY1"]
    if not ok and _table_exists(cx, "marg_push_staging"):
'''),
        ('''    st = _pick(ok, bad, today_iso)
    st.update(key="SALE_BILLWISE", label="Bill-wise sale report", pair=True,
''', '''    if _s480 and not ok:           # S480: only the short form came for this day -- the tile's own "Item detail nahi hai" words
        bad = sorted([dict(r, verdict="REFUSED", reason="no item detail -- the short Bill Wise statement (BILL VALUE), not Report Type DETAIL")
                      for r in _s480] + bad, key=lambda r: _norm_ts(r.get("received_at")), reverse=True)
    st = _pick(ok, bad, today_iso)
    st.update(key="SALE_BILLWISE", label="Bill-wise sale report", pair=True,
'''),
    ])


# ------------------------------------------------------------------------------------------------------------ PUSH_STOCK_DAILY.bat (B.5)
def build_bat(src):
    return edit("PUSH_STOCK_DAILY.bat", src, [
        ("set KIT=D:\\dr-manoj-git\\drmanoj-clinic-automation\\deploy_kits\\S208_STOCK_LEDGER\r\n",
         "set KIT=D:\\dr-manoj-git\\drmanoj-clinic-automation\\deploy_kits\\S480_MARG_TEXT_READERS\r\n"),
    ])


def put(out, rel, text, crlf=False):
    p = os.path.join(out, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    b = text.encode("utf-8")
    with io.open(p, "wb") as fh:
        fh.write(b)
    print("%s  %s" % (md5(b), rel))
    return b


def same(rel, built, label):
    mine = rd(os.path.join(HERE, rel))
    if mine != built:
        raise SystemExit("!! the built %s (%s) is not this kit's %s (%s) -- nothing to place" % (label, md5(built), rel, md5(mine)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="S480: build every patched file from the live bytes (anchored edits)")
    ap.add_argument("--medical")
    ap.add_argument("--server", action="store_true")
    ap.add_argument("--ingest", default="/root/marg_ingest")
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--manojz")
    ap.add_argument("--out", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    out = a.out
    if os.path.abspath(out) == HERE:
        raise SystemExit("!! --out must not be the kit folder (a published kit is frozen)")
    if a.medical:
        ob = rd(os.path.join(a.medical, "marg_txt.py"))
        t = put(out, "marg_txt.py", build_marg_txt(pinned("marg_txt.py", ob), ob))
        w = put(out, "marg_watch.py", build_marg_watch(pinned("marg_watch.py", rd(os.path.join(a.medical, "marg_watch.py")))))
        if a.check:
            same("marg_txt.py", t, "marg_txt.py")
            same("marg_watch.py", w, "marg_watch.py")
    if a.server:
        I, F = a.ingest, a.finance
        sig = put(out, "ingest/signatures.json",
                  build_signatures("signatures.json", pinned("ingest/signatures.json", rd(os.path.join(I, "signatures.json"))), True))
        r1 = put(out, "ingest/marg_report.py",
                 build_marg_report("marg_ingest/marg_report.py", pinned("ingest/marg_report.py", rd(os.path.join(I, "marg_report.py")))))
        r2 = put(out, "ingest/lib/marg_report.py",
                 build_marg_report("marg_ingest/lib/marg_report.py",
                                   pinned("ingest/lib/marg_report.py", rd(os.path.join(I, "lib", "marg_report.py")))))
        put(out, "ingest/marg_take.py", build_marg_take(pinned("ingest/marg_take.py", rd(os.path.join(I, "marg_take.py")))))
        pe = put(out, "ingest/lib/push_expected.py",
                 build_push_expected(pinned("ingest/lib/push_expected.py", rd(os.path.join(I, "lib", "push_expected.py")))))
        put(out, "finance/marg_report.py",
            build_marg_report("finance/marg_report.py", pinned("finance/marg_report.py", rd(os.path.join(F, "marg_report.py")))))
        put(out, "finance/marg_door.py", build_marg_door(pinned("finance/marg_door.py", rd(os.path.join(F, "marg_door.py")))))
        put(out, "finance/salts_refresh.py", build_salts_refresh(pinned("finance/salts_refresh.py", rd(os.path.join(F, "salts_refresh.py")))))
        put(out, "finance/reports_tile.py", build_reports_tile(pinned("finance/reports_tile.py", rd(os.path.join(F, "reports_tile.py")))))
        # the copies that must be the same bytes everywhere are this kit's own files
        same("signatures.json", sig, "signatures.json")
        same("marg_report.py", r1, "marg_ingest/marg_report.py")
        same("marg_report.py", r2, "marg_ingest/lib/marg_report.py")
        same("push_expected.py", pe, "lib/push_expected.py")
    if a.manojz:
        M = a.manojz
        sig = put(out, "manojz/signatures.json",
                  build_signatures("MargPull/signatures.json",
                                   pinned("manojz/signatures.json", rd(os.path.join(M, "MargPull", "signatures.json"))), False))
        pinned("manojz/marg_report.py", rd(os.path.join(M, "MargPull", "marg_report.py")))     # replaced whole by the kit's (masked fixtures)
        braw = rd(os.path.join(M, "PUSH_STOCK_DAILY.bat"))
        if md5(braw) != FROM["manojz/PUSH_STOCK_DAILY.bat"]:
            raise SystemExit("!! PUSH_STOCK_DAILY.bat is %s, not its FROM pin -- nothing built" % md5(braw))
        bat = build_bat(braw.decode("latin-1"))
        p = os.path.join(out, "manojz", "PUSH_STOCK_DAILY.bat")
        with io.open(p, "wb") as fh:
            fh.write(bat.encode("latin-1"))
        print("%s  manojz/PUSH_STOCK_DAILY.bat" % md5(bat.encode("latin-1")))
        if a.check:
            same("signatures.json", sig, "MargPull/signatures.json")
    print("MAKE_S480 DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""make_marg_watch_s488.py -- kit S488_DATES_AND_WAITS, Part E: marg_watch.py S480 (58b54f37) -> S488, by anchored edits.

Reads the live bytes of deploy_kits/S480_MARG_TEXT_READERS/marg_watch.py (= the medical PC's D:\\SendToClinic\\marg_watch.py),
stops unless they are the FROM pin, applies five anchored edits (every anchor must occur exactly once, else STOP), writes
marg_watch.py beside this script (LF only) and prints the new md5. Run with python -B.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = [p for p in (os.path.abspath(os.path.join(HERE, *[".."] * k)) for k in (2, 3)) if os.path.isdir(os.path.join(p, "deploy_kits", "S480_MARG_TEXT_READERS"))][0]   # the kit folder or a scratch folder
SRC = os.path.join(REPO, "deploy_kits", "S480_MARG_TEXT_READERS", "marg_watch.py")
DST = os.path.join(HERE, "marg_watch.py")
FROM = "58b54f37865cb487720b95eaa4aedde5"


def stop(msg):
    print("STOP: " + msg)
    sys.exit(1)


def once(text, anchor, what):
    n = text.count(anchor)
    if n != 1:
        stop("anchor '%s' occurs %d times (must be exactly once)" % (what, n))
    return text.index(anchor)


raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != FROM:
    stop("%s is %s, not the FROM pin %s" % (SRC, hashlib.md5(raw).hexdigest(), FROM))
if b"\r" in raw:
    stop("the source carries CR bytes")
t = raw.decode("utf-8")

# ---------------------------------------------------------------------------------------------------------- edit 1: header note
A1 = "    as seen -- the same report exported on a later day is taken.\n\nOFF SWITCH (S259)\n"
NEW1 = r"""    as seen -- the same report exported on a later day is taken.

S488 (06-Oct-2026, kit S488_DATES_AND_WAITS part E): A REFUSED TEXT WITH A PERSON'S DETAIL STAYS OFF DRIVE. A refused sale report or
    stock register carries patients' names, and a .why.txt the whole reason, which can quote a line. share_refused now copies a kept
    text's BODY to Drive's FromMedical\\refused_text only when _may_leave says it can carry no person's detail: its kind is one whose
    rows never name a person (PURCHASE, SALT, CATEGORY, ITEMS, VALUATION, EXPIRY, STOCK), its first 25 lines carry no person word, and
    no mobile-shaped number stands in it but the shop's own "Phone :" line and Marg's advertisement line (phi_scan.py's patterns, the
    server's, copied here). Any other body leaves <stem>.withheld.txt in its place, one line. Every .why.txt on Drive is two lines --
    its stamp and the reason as a note carries it -- never the whole reason and no "from:" line. Each pass also sweeps Drive's folder:
    a body that may not leave, or whose kept text is gone, is removed for its .withheld.txt; a .why.txt not in that form is rewritten.
    _captured_txt\\refused on this PC is untouched (the body and the whole reason stay here), and capture is not changed.

OFF SWITCH (S259)
"""
i = once(t, A1, "header S480 paragraph end / OFF SWITCH")
t = t[:i] + NEW1 + t[i + len(A1):]

# ---------------------------------------------------------------------------------------------------------- edit 2: share_refused
A2s = "def share_refused(spool, fm, now=None):\n"
A2e = "\n\n\nMAX_SHARE = 5 * 1024 * 1024\n"
i = once(t, A2s, "def share_refused")
j = once(t, A2e, "MAX_SHARE line")
if not i < j:
    stop("share_refused does not stand before MAX_SHARE")
old_fn = t[i:j]
print("old share_refused: %d lines, md5 %s" % (old_fn.count("\n") + 1, hashlib.md5(old_fn.encode()).hexdigest()))
NEW2 = r'''# S488 (E.1) -- what of a refused text may leave this PC for Drive. Conservative on purpose: a wrong "clean" is the failure that
# matters. The four patterns are phi_scan.py's (the server's, S274 / kit S336), copied here letter for letter, applied to the lines.
PHI_MOBILE_RE = re.compile(r"(?<![0-9])[6-9][0-9]{9}(?![0-9])")
PHI_PERSON_WORDS = re.compile(r"\b(SALE|SALES|PATIENT|PATIENTS|MOBILE|LEDGER|PRESCRIB\w*|DOCTOR|CUSTOMER|ADDRESS)\b", re.I)
PHI_SHOP_LINE_RE = re.compile(r"^\s*PHONE\s*:", re.I)          # the shop's own header line (in the first 8 lines)
PHI_AD_LINE_RE = re.compile(r"\bMARG\b", re.I)                 # Marg's advertisement line names Marg (in the last 3 lines)
PHI_PREAMBLE_LINES, PHI_SHOP_LINES, PHI_AD_LINES = 25, 8, 3
# The kinds (_kind_of's words) whose rows never name a person. Every sale shape, the sale return, the stock register (LEDGER), ORDER
# (suppliers' Ph. numbers) and an unrecognised text ("") are not here. Each admitted spec of marg_txt S480 was read: none has a
# patient, doctor, customer, mobile or address column (PARTY / SUPPLIER NAME on a purchase is the supplier, as phi_scan reads it).
SHARE_KINDS = ("PURCHASE", "SALT", "CATEGORY", "ITEMS", "VALUATION", "EXPIRY", "STOCK")
WITHHELD_LINE = "kept on the medical PC only (a person's detail, or not established): %s"
WHY_STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
WHY_LINE_SAFE = re.compile(r"the reader refused it \(line \d+\)")   # _note_reason's own output: passed through it again, its line
#                                                                     number would be cut and the file rewritten on every pass


def _may_leave(raw):
    """S488 (E.1): may this refused text's BODY be copied to Drive? True only when every test holds; not established is False.
    The kind is admitted (SHARE_KINDS); the first 25 filled lines carry no person word; no ten-digit run starting 6-9 stands in any
    line -- as printed, or with a single space between digits closed up -- except the shop's own "Phone :" line among the first 8
    lines and a line naming MARG among the last 3 filled lines. An empty, binary, oversized or unrecognised text may not leave."""
    try:
        if not isinstance(raw, (bytes, bytearray)) or not raw or len(raw) > MAX_SHARE or b"\x00" in raw:
            return False
        raw = bytes(raw)
        if raw[:4] in EXCEL_MAGICS + PDF_MAGIC:
            return False
        if _kind_of(raw) not in SHARE_KINDS:
            return False
        lines = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        filled = [(i, l) for i, l in enumerate(lines) if l.strip()]
        if not filled or PHI_PERSON_WORDS.search(" ".join(l for _i, l in filled[:PHI_PREAMBLE_LINES])):
            return False
        tail = set(i for i, _l in filled[-PHI_AD_LINES:])
        for i, l in filled:
            if PHI_MOBILE_RE.search(l) or PHI_MOBILE_RE.search(re.sub(r"(?<=\d) (?=\d)", "", l)):
                if (i < PHI_SHOP_LINES and PHI_SHOP_LINE_RE.match(l)) or (i in tail and PHI_AD_LINE_RE.search(l)):
                    continue                                    # the shop's or Marg's own number, not a person's
                return False
        return True
    except Exception:                                           # noqa: BLE001 -- not established: it stays on this PC
        return False


def _read_or_none(p, n=-1):
    try:
        with open(p, "rb") as fh:
            return fh.read(n)
    except OSError:
        return None


def _share_put(q, data):
    """S488: write DATA (bytes) to Q on Drive unless Q already holds exactly it -- compared by content, never by size. 1 if written."""
    if _read_or_none(q) == data:
        return 0
    with open(q, "wb") as fh:
        fh.write(data)
    return 1


def _safe_why(text, when):
    """S488 (E.2): the two lines a .why.txt may carry on Drive -- its stamp and the reason as a note carries it (_note_reason); no
    'from:' line, never the whole reason. TEXT is the kept .why.txt or, its local source gone, Drive's own copy. WHEN stamps a text
    whose first line is not a stamp."""
    text = text or ""
    lines = text.splitlines()
    stamp = lines[0].strip() if lines and WHY_STAMP_RE.match(lines[0].strip()) else \
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(when))
    m = re.search(r"^why:\s*(.*)", text, re.M | re.S)
    w = " ".join((m.group(1) if m else "").split())
    w = w if WHY_LINE_SAFE.fullmatch(w) else _note_reason(w).strip()
    return ("%s\nwhy:  %s\n" % (stamp, w or "kept as refused (its reason was not kept)")).encode("utf-8")


def _withhold(dst, name, raw):
    """S488 (E.2): the body NAME may not be on Drive -- removed if it is there, and <stem>.withheld.txt (one line) stands for it."""
    n = 0
    q = os.path.join(dst, name)
    if os.path.exists(q):
        os.remove(q)
        n += 1
    k = _kind_of(raw) if raw else ""
    return n + _share_put(os.path.join(dst, name[:-4] + ".withheld.txt"), ((WITHHELD_LINE % (k or "unknown")) + "\n").encode("utf-8"))


def _share_sweep(src, dst):
    """S488 (E.2): Drive's refused_text, every file, at every pass -- a body whose kept text may not leave or is gone is removed and
    its .withheld.txt stands for it; a .why.txt not in the safe form is rewritten (from the kept one, or from its own why: line).
    What is removed stays in Drive's own bin for 30 days."""
    n = 0
    for name in sorted(os.listdir(dst)):
        q, low = os.path.join(dst, name), name.lower()
        try:
            if not os.path.isfile(q) or low.endswith(".withheld.txt"):
                continue
            p = os.path.join(src, name)
            if low.endswith(".why.txt"):
                t = _read_or_none(p)
                when = os.path.getmtime(p) if t is not None else os.path.getmtime(q)
                if t is None:
                    t = _read_or_none(q) or b""
                n += _share_put(q, _safe_why(t.decode("utf-8", "replace"), when))
            elif low.endswith(".txt"):
                raw = _read_or_none(p)
                if raw is not None and _may_leave(raw):
                    continue
                n += _withhold(dst, name, raw if raw is not None else (_read_or_none(q, 4000) or b""))
        except OSError:
            continue
    return n


def share_refused(spool, fm, now=None):
    """S396.1: a report the reader would not take, offered beside the census so it can be looked at without anyone going to the
    medical PC. Only what is already in _captured_txt\\refused, only the last CENSUS_DAYS, at most 18 files offered. S454 P4C: a
    text's note marker (<stem>.note) is copied with it, so the list on Drive still shows which notes are done.
    S488 (E.2): a body is copied only when _may_leave says so (and, as before, a copy of the same size is not written again); any
    other leaves <stem>.withheld.txt in its place. Every .why.txt on Drive is the safe two lines (_safe_why), compared by content.
    The .note as before. Then Drive's folder is swept (_share_sweep). The local folder is never written here."""
    now = now or time.time()
    src = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
    if not os.path.isdir(src):
        return 0
    dst = os.path.join(fm, "refused_text")
    n = 0
    for name in sorted(os.listdir(src), reverse=True)[:18]:
        p, low = os.path.join(src, name), name.lower()
        try:
            st = os.stat(p)
            if not os.path.isfile(p) or now - st.st_mtime > CENSUS_DAYS * 86400 or st.st_size > MAX_SHARE:
                continue
            os.makedirs(dst, exist_ok=True)
            q = os.path.join(dst, name)
            if low.endswith(".why.txt"):
                with open(p, "rb") as fh:
                    t = fh.read().decode("utf-8", "replace")
                n += _share_put(q, _safe_why(t, st.st_mtime))
            elif low.endswith(".withheld.txt"):
                continue                                        # never a name kept in refused; never copied
            elif low.endswith(".txt"):
                with open(p, "rb") as fh:
                    raw = fh.read()
                if not _may_leave(raw):
                    n += _withhold(dst, name, raw)
                elif not (os.path.exists(q) and os.path.getsize(q) == st.st_size):
                    shutil.copyfile(p, q)
                    n += 1
            elif low.endswith(".note"):
                if not (os.path.exists(q) and os.path.getsize(q) == st.st_size):
                    shutil.copyfile(p, q)
                    n += 1
        except OSError:
            continue
    if os.path.isdir(dst):
        n += _share_sweep(src, dst)
    return n'''
t = t[:i] + NEW2 + t[j:]

# ---------------------------------------------------------------------------------------------------------- edit 3: the selftest's S396.1 case
A3s = '        fmd = os.path.join(d, "FromMedical"); os.makedirs(fmd)\n'
A3e = '        ck("...and only once, however often it is looked at",\n'
i = once(t, A3s, "selftest fmd line")
j = once(t, A3e, "selftest '...and only once'")
if not i < j:
    stop("the selftest case is not in order")
old_case = t[i:j]
print("old selftest case: %d lines, md5 %s" % (old_case.count("\n"), hashlib.md5(old_case.encode()).hexdigest()))
NEW3 = r'''        fmd = os.path.join(d, "FromMedical"); os.makedirs(fmd)
        rtd = os.path.join(fmd, "refused_text")
        n1, n2 = share_refused(sp2, fmd), share_refused(sp2, fmd)
        stems = sorted(set(f[:-8] for f in os.listdir(refd) if f.endswith(".why.txt")))
        kinds = dict((s, _kind_of(open(os.path.join(refd, s + ".txt"), "rb").read())) for s in stems)
        ck("S396.1 / S488: a refused SALE text (or a note kept under a report's name) is NOT copied beside the census -- its "
           ".withheld.txt, its reason (two safe lines) and its note are, once",
           n1 == len(os.listdir(refd)) >= 2 and n2 == 0 and "SALE" in kinds.values()
           and sorted(os.listdir(rtd)) == sorted(s + x for s in stems for x in (".withheld.txt", ".why.txt", ".note"))
           and all(open(os.path.join(rtd, s + ".withheld.txt"), encoding="utf-8").read()
                   == WITHHELD_LINE % (kinds[s] or "unknown") + "\n" for s in stems)
           and all(len(open(os.path.join(rtd, s + ".why.txt"), encoding="utf-8").read().splitlines()) == 2
                   and "from:" not in open(os.path.join(rtd, s + ".why.txt"), encoding="utf-8").read() for s in stems)
           and any(f.endswith(".why.txt") for f in os.listdir(refd)))
'''
t = t[:i] + NEW3 + t[j:]

# ---------------------------------------------------------------------------------------------------------- edit 4: the S488 selftest cases
A4 = ("                       for f in os.listdir(sp2)))\n"
      "        else:\n"
      '            ck("S480: marg_txt S480 is beside this file')
i = once(t, A4, "end of the S480 selftest block")
k = i + len("                       for f in os.listdir(sp2)))\n")
NEW4 = r'''            # S488 (E.1): what of a refused text may leave for Drive -- every admitted kind's made-up text may, nothing else may
            adm = ("PURCHASE_BILLWISE", "PURCHASE_ITEMWISE", "PURCHASE_SUPPLIERWISE", "PURCHASE_BILLITEMWISE", "SALT_WISE_ITEM_LIST",
                   "CATEGORY_WISE_ITEM_LIST", "ITEM_MASTER", "STOCK_VALUATION_BATCHWISE", "STOCK_EXPIRY")
            ck("S488 (E.1): a purchase (four shapes), the salt, category and item lists, a valuation, an expiry report and the closing "
               "stock may leave", all(_may_leave(M_[k_]) for k_ in adm) and _may_leave(STK))
            ck("S488 (E.1): a sale (both shapes), a sale return (both), the stock register, an order sheet, an empty day, a note, "
               "nothing, a spreadsheet -- may not",
               not any(_may_leave(M_[k_]) for k_ in M_ if k_ not in adm) and not _may_leave(T) and not _may_leave(marg_txt.ORDER_SAMPLE)
               and not _may_leave(E_) and not _may_leave(b"milk, bread") and not _may_leave(b"") and not _may_leave(None)
               and not _may_leave(b"\xd0\xcf\x11\xe0" + M_["ITEM_MASTER"]))
            IM = M_["ITEM_MASTER"].split(b"\r\n")
            ph = lambda a, b: (a + b * 9).encode()              # a ten-digit run made here, never written out in this file
            ck("S488 (E.1): a person word at the head, a 'Phone :' line below line 8, a Marg line not at the end, a spaced ten-digit "
               "run -- each holds a list back",
               not _may_leave(b"\r\n".join(IM).replace(b"OTHER PRODUCTS", b"CUSTOMER LIST", 1))
               and not _may_leave(b"\r\n".join(IM[:9] + [b"Phone : " + ph("9", "7")] + IM[9:]))
               and not _may_leave(b"\r\n".join(IM[:9] + [b"MARG ERP " + ph("8", "6")] + IM[9:]))
               and not _may_leave(b"\r\n".join(IM).replace(b"DEMOCIN TAB", b"DEMOCIN " + ph("9", "8")[:5] + b" " + ph("9", "8")[5:], 1)))
            _s488_share_cases(ck, os.path.join(d, "w488"))      # S488 (walk 7.6, the medical PC)
'''
t = t[:k] + NEW4 + t[k:]

# ---------------------------------------------------------------------------------------------------------- edit 5: the walk 7.6 cases
A5 = 'def selftest(out):\n    """Proves the thing that matters: an OVERWRITTEN export is still kept."""\n'
i = once(t, A5, "def selftest")
NEW5 = r'''def _s488_share_cases(ck, base, share=None):
    """S488 (walk 7.6, the medical PC): made-up W488 texts kept as refused the way capture keeps them (_keep_refused: the body and
    the whole reason with its from: line), a body and a whole-reason .why.txt planted on the scratch Drive beforehand, then SHARE --
    share_refused, or the OLD file's for the negative control -- run twice into BASE\\FromMedical. Invented names and digits only."""
    import marg_txt
    share = share or share_refused
    M_ = marg_txt._s480_samples()
    mob = lambda a, b: a + b * 9                                # a ten-digit run made here, never written out in this file
    spool = os.path.join(base, "spool")
    refd = _ref_dir(spool)
    rtd = os.path.join(base, "FromMedical", "refused_text")
    os.makedirs(refd, exist_ok=True)
    os.makedirs(rtd, exist_ok=True)
    whys = {}

    def keep(tag, raw, why):
        h = hashlib.md5(raw).hexdigest()
        _keep_refused(os.path.join(base, "MARGERP", tag + ".txt"), raw, h, spool, lambda m: None, why)
        s = [f for f in os.listdir(refd) if h in f and f.endswith(".why.txt")][0][:-8]
        whys[s] = why
        return s
    sale = marg_txt.SELFTEST_SAMPLE.replace(b"TEST ONE", b"W488 ONE")[:-40]
    reg = M_["STOCK_ITEM_LEDGER_TEXT"].replace(b"TEST ONE 1001", b"W488 PERSON")
    lst = M_["ITEM_MASTER"].replace(b"DEMOGEL", b"W488GEL")[:-30]
    ten = M_["ITEM_MASTER"].replace(b"DEMOCIN TAB", ("W488 TAB " + mob("9", "8")).encode(), 1)
    phl = M_["ITEM_MASTER"].replace(b"DEMOGEL", b"W488PHGEL")
    cut = phl.index(b"\r\n") + 2
    phl = (phl[:cut] + (" " * 22 + "Phone : " + mob("9", "7") + "\r\n").encode() + phl[cut:].rstrip(b"\r\n") + b"\r\n"
           + ("MARG ERP W488 for Chemist  Call " + mob("8", "6") + "\r\n").encode())
    s_sale = keep("report", sale, "the reader refused it: line 7: a line of a kind this reader does not know: 'A000001 W488 ONE .CASH'")
    s_reg = keep("user_w4881", reg, "the reader refused it: line 12: a figure that cannot be read: 'W488 PERSON TEST DOCTOR'")
    s_lst = keep("user_w4882", lst, _why_not(lst))
    s_ten = keep("user_w4883", ten, "the reader refused it: line 10: a figure that cannot be read: 'W488 TAB %s'" % mob("9", "8"))
    s_phl = keep("user_w4884", phl, _why_not(phl))
    gone = marg_txt.SELFTEST_SAMPLE.replace(b"TEST ONE", b"W488 GONE")
    s_gone = "20300101-000000__report__%s" % hashlib.md5(gone).hexdigest()
    shutil.copyfile(os.path.join(refd, s_sale + ".txt"), os.path.join(rtd, s_sale + ".txt"))          # planted beforehand
    shutil.copyfile(os.path.join(refd, s_sale + ".why.txt"), os.path.join(rtd, s_sale + ".why.txt"))
    with open(os.path.join(rtd, s_gone + ".txt"), "wb") as fh:
        fh.write(gone)
    with open(os.path.join(rtd, s_gone + ".why.txt"), "wb") as fh:
        fh.write(b"2030-01-01 00:00:00\r\nfrom: C:\\W488\\report.txt\r\nwhy:  the reader refused it: line 7: a line of a kind this "
                 b"reader does not know: 'A000001 W488 GONE .CASH'\r\n")
    snap = lambda dd: dict((f, open(os.path.join(dd, f), "rb").read()) for f in sorted(os.listdir(dd)))
    loc0 = snap(refd)
    n1 = share(spool, os.path.join(base, "FromMedical"))
    d1 = snap(rtd)
    n2 = share(spool, os.path.join(base, "FromMedical"))
    d2 = snap(rtd)
    on = lambda s, x: d1.get(s + x)
    held = lambda k: ((WITHHELD_LINE % k) + "\n").encode("utf-8")
    want = dict((s, _note_reason(w)) for s, w in whys.items())
    want[s_gone] = "the reader refused it (line 7)"
    first = dict((s, open(os.path.join(refd, s + ".why.txt"), encoding="utf-8").read().splitlines()[0]) for s in whys)
    first[s_gone] = "2030-01-01 00:00:00"

    def safe(dd, f):
        b = dd.get(f)
        s = f[:-8]
        return (b is not None and s in want and b == ("%s\nwhy:  %s\n" % (first[s], want[s])).encode("utf-8")
                and b"from:" not in b and b"W488" not in b and WHY_STAMP_RE.match(first[s]) is not None)
    ck("S488 (7.6): of a sale report, a stock register and an item list kept as refused, ONLY the list's body reaches Drive",
       on(s_lst, ".txt") == lst and on(s_sale, ".txt") is None and on(s_reg, ".txt") is None)
    ck("S488 (7.6): the sale report and the register each leave <stem>.withheld.txt -- one line, naming the kind",
       on(s_sale, ".withheld.txt") == held("SALE") and on(s_reg, ".withheld.txt") == held("LEDGER"))
    ck("S488 (7.6): Drive's folder holds exactly the admitted bodies, the .withheld.txt of the rest, every reason and every note",
       sorted(d1) == sorted([s + x for s in (s_sale, s_reg, s_ten) for x in (".withheld.txt", ".why.txt", ".note")]
                            + [s + x for s in (s_lst, s_phl) for x in (".txt", ".why.txt", ".note")]
                            + [s_gone + ".withheld.txt", s_gone + ".why.txt"]))
    dw = [f for f in d1 if f.lower().endswith(".why.txt")]
    ck("S488 (7.6): every .why.txt on Drive is the safe two lines -- the stamp and the note's reason; no 'from:', never the whole reason",
       len(dw) == 6 and all(safe(d1, f) for f in dw))
    ck("S488 (7.6): a body and a whole-reason .why.txt planted beforehand are swept -- also where the kept text is gone (its reason "
       "remade from Drive's own why: line)",
       on(s_sale, ".txt") is None and on(s_gone, ".txt") is None and on(s_gone, ".withheld.txt") == held("SALE")
       and safe(d1, s_gone + ".why.txt") and safe(d1, s_sale + ".why.txt"))
    ck("S488 (7.6): an item list with a ten-digit run in a body line is withheld",
       on(s_ten, ".txt") is None and on(s_ten, ".withheld.txt") == held("ITEMS"))
    ck("S488 (E.1): the shop's own 'Phone :' line and Marg's advertisement line do not hold an item list back",
       on(s_phl, ".txt") == phl)
    ck("S488 (7.6): a second pass writes nothing, and every .why.txt there stays the safe form",
       n1 > 0 and n2 == 0 and d2 == d1 and all(safe(d2, f) for f in d2 if f.lower().endswith(".why.txt")))
    ck("S488 (E.3): the local _captured_txt\\refused is untouched -- the bodies and the whole reasons stay on this PC",
       snap(refd) == loc0 and len(loc0) == 15)


'''
t = t[:i] + NEW5 + t[i:]

out = t.encode("utf-8")
if b"\r" in out:
    stop("CR bytes in the result")
compile(out, DST, "exec")
with open(DST, "wb") as fh:
    fh.write(out)
print("wrote %s  md5 %s  (%d bytes, %d lines)" % (DST, hashlib.md5(out).hexdigest(), len(out), out.count(b"\n")))

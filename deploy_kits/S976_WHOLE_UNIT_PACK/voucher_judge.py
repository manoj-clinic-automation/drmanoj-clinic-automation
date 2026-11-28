#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  voucher_judge.py  ·  v1.0  ·  kit S965_VOUCHER_JUDGE  ·  Session 532 (Sanjeevni)  ·  26-Nov-2026
#
#  THE JUDGE OF MARG'S STOCK VOUCHERS (D1083, D1086; F-1690 - F-1692). Read only: it writes nothing anywhere.
#  Marg's own Stock Issue / Stock Receive period reports (kept by S963 / S964 in mi_voucher_now / mi_voucher_line_now) against every
#  correction the system asked of Amir:
#    * the count rounds' vouchers (stock_voucher_line, with Amir's typed number in stock_voucher_entered; a voided batch asks nothing),
#    * Amir's one-line tap jobs that ask a STOCK ISSUE / RECEIVE (amir_job, the quantity in its own words),
#    * the Expiry watch's wrong-batch fixes (stock_batch_fix): a RECEIVE into the minus batch + an ISSUE from the stocked batch, a pair.
#  Each ask is matched to ONE Marg voucher line: the same kind, the same item (Marg's name, its 15/20/24-letter cut, the rename memory),
#  the same units, on or after the day it was asked; a batch fix also batch for batch. Amir's typed voucher number is preferred, never trusted.
#  States, ask side:  in_marg (voucher no . day) . waiting (asked, Amir has not said done) . not_in_marg (Amir said done, the report covers the
#                     days since, nothing found) . beyond (asked after the newest report's last day: the next report decides).
#  States, Marg side: asked (matched) . twice (a second line equal to a matched one: keyed twice) . more (more units than asked) .
#                     less (fewer than asked) . unasked (no correction asked for it).
#  A judgment is words on the owner's pages only; nothing is told to staff by this file.
#  v1.1 S967 (27-Nov, kit A1 of S534_FINAL_BUILD_PLAN, D1090 D1091 D1092): F-1706 -- an ask asked AGAIN after Amir's done mark (an S957:
#  re-ask newer than the done tap) clears that mark: the ask is waiting again, never 'not in Marg' on an older tap. And the WHOLE-ITEM
#  RE-JUDGE (plan §2.3): every old correction read against the stock of record today -- Marg = shelf -> settled by later entries; a shelf
#  only from an old count -> count first; a fresh count that still differs -> one correction for today's gap; a batch-only part stays with
#  the Expiry watch's night asks (his word 27-11). Still read only.
#  v1.2 S969 (27-Nov, kit A2): a Write off from the Stock check desk (amir_job key S969:wo:...) takes its pack and units from the desk's own
#  row (stock_desk_action) -- never parsed from the Hindi words with a guessed pack. Still read only.
#  v1.3 S971 (27-Nov, kit B of S534_FINAL_BUILD_PLAN, D1091): a reversal Amir is asked to key (amir_job key S971:rev:...) takes its pack and
#  units from its own row (stock_inquiry_job); a job the owner WITHDREW (done_how 'withdrawn') asks nothing; the cancel window is the
#  setting stock.voucher_cancel_days (7). Matching is otherwise unchanged (cold review M1: a line keyed before its ask is told by the
#  inquiry, never taken by the judge). Still read only: the writes of kit B are voucher_inquiry.py's.
import datetime as dt
import json
import re
import sqlite3

VERSION = "1.3"
KIT = "S965_VOUCHER_JUDGE"
KIT_S967 = "S967_STOCKCHECK_ONE_PAGE"
CUTS = (15, 20, 24)
GRACE_DAYS = 1                                            # a voucher keyed the day before the ask's row was frozen still answers it


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (t,)).fetchone() is not None


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().upper())


def bnorm(s):
    return re.sub(r"[^0-9A-Z]", "", str(s or "").upper())


def _day(s):
    s = str(s or "").strip()
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", s[:10])
    if m:
        return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
    return s[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s[:10]) else ""


def vno(kind, n):
    """Amir's typed '8' -> Marg's printed number (L000008 / AD00008)."""
    s = re.sub(r"\D", "", str(n or ""))
    if not s:
        return ""
    return ("L%06d" if kind == "ISSUE" else "AD%05d") % int(s)


# ------------------------------------------------------------------ names
def renames(con):
    """{norm(name): set of every printed form of the same item} from the done, not-undone renames."""
    out = {}
    if not _has(con, "marg_item_rename"):
        return out
    try:
        for o, n in con.execute("SELECT old_name, new_name FROM marg_item_rename WHERE done_at IS NOT NULL AND undone_at IS NULL"):
            g = {norm(o), norm(n)}
            for f in list(g):
                out.setdefault(f, set()).update(g)
    except sqlite3.Error:
        pass
    return out


def forms(name, ren):
    f = {norm(name)}
    f |= ren.get(norm(name), set())
    return f


def _prefix(short, long_):
    return len(long_) > len(short) and long_[:len(short)] == short and (len(short) >= 15 or (len(short) >= 12 and long_[len(short)] == " "))


def name_match(ask_forms, printed):
    """One item under two spellings: exact; else one is the cut of the other -- Marg prints a voucher item cut at 15, 20 or 24 letters, and a
    rename's planned name may be shorter than the name Marg holds -- at 15 letters or more, or at a word's end from 12 letters."""
    p = norm(printed)
    if p in ask_forms:
        return True
    return any(_prefix(p, f) or _prefix(f, p) for f in ask_forms)


# ------------------------------------------------------------------ Marg's side
NAME_DDL = ("CREATE TABLE IF NOT EXISTS mi_voucher_name (kind TEXT NOT NULL, no TEXT NOT NULL, n INTEGER NOT NULL, printed TEXT NOT NULL, "
            "item TEXT NOT NULL, source TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY (kind, no, n))")
# AD00010's two lines: Marg's report cuts both to 'KNEE IMMOBILIZE'; his Marg screen (photos 26-11 20:16-20:23) names them.
SEED_NAMES = (("RECEIVE", "AD00010", 1, "KNEE IMMOBILIZE", "KNEE IMMOBILIZER L UNISON", "the owner's Marg screen, 26-11-2026 20:18 IST"),
              ("RECEIVE", "AD00010", 2, "KNEE IMMOBILIZE", "KNEE IMMOBILIZER M TYNOR", "the owner's Marg screen, 26-11-2026 20:18 IST"))


def ensure_names(con, seed=True):
    """The name table (a voucher line's full name, where Marg's report cut it and something settled it). The installer seeds AD00010."""
    con.execute(NAME_DDL)
    if seed:
        for kind, no, n, printed, item, src in SEED_NAMES:
            con.execute("INSERT OR IGNORE INTO mi_voucher_name (kind, no, n, printed, item, source, at) VALUES (?,?,?,?,?,?,?)",
                        (kind, no, n, printed, item, src, "2026-11-26T20:18:00"))


def marg_names(con):
    """Every full item name Marg prints today: the newest whole closing stock (stock_snapshot) and the stock of record."""
    out = set()
    try:
        if _has(con, "stock_snapshot"):
            days = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
            iso = sorted((_day(d), d) for d in days if _day(d))
            if iso:
                out |= {norm(r[0]) for r in con.execute("SELECT item FROM stock_snapshot WHERE as_on=?", (iso[-1][1],))}
        if _has(con, "stock_of_record"):
            out |= {norm(r[0]) for r in con.execute("SELECT item FROM stock_of_record")}
    except sqlite3.Error:
        pass
    return out


def _by_register(con, ln, cands):
    """A cut name settled by a one-item Stock Register: the candidate whose register holds this voucher number on this day and figure."""
    if not _has(con, "mi_register_line") or not _has(con, "mi_register"):
        return None
    hits = set()
    try:
        for item, in_, d, q in con.execute(
                "SELECT r.item, l.bill_no, l.day, l.qty_u FROM mi_register r JOIN mi_register_line l ON l.md5=r.md5 AND l.seq=r.seq WHERE r.ok=1 "
                "AND l.bill_no=?", (ln["no"],)):
            if _day(d) == ln["day"] and abs(int(q or 0)) == int(ln["units"]) and norm(item) in cands:
                hits.add(norm(item))
    except sqlite3.Error:
        return None
    return hits.pop() if len(hits) == 1 else None


def marg_lines(con):
    """Every voucher line Marg's newest reports hold, with its voucher's day; each under its FULL Marg name: the name table first, else the
    one Marg item its printed (cut) name fits, else a one-item Stock Register that holds the voucher. A cut name that still fits several
    items keeps its printed name and lists them (ambiguous). [] when no report was ever read."""
    if not _has(con, "mi_voucher_line_now"):
        return []
    out = []
    cols = [d[1] for d in con.execute("PRAGMA table_info(mi_voucher_line_now)")]
    want = [c for c in ("kind", "no", "n", "day", "item", "packing", "per", "batch", "qty", "units", "unit", "expiry", "rate_p", "value_p") if c in cols]
    named = {}
    if _has(con, "mi_voucher_name"):
        named = {(k, no, int(n)): (norm(p), it, str(sc or "")) for k, no, n, p, it, sc in con.execute("SELECT kind, no, n, printed, item, source FROM mi_voucher_name")}   # S973: + its source
    names = marg_names(con)
    for r in con.execute("SELECT %s FROM mi_voucher_line_now ORDER BY day, kind, no, n" % ", ".join(want)):
        d = dict(zip(want, r))
        d["day"] = _day(d.get("day"))
        d["key"] = "%s|%s|%s" % (d["kind"], d["no"], d.get("n"))
        d["printed"] = norm(d["item"])
        nm = named.get((d["kind"], d["no"], int(d.get("n") or 0)))
        if nm and nm[0] == d["printed"]:                   # the owner's word holds only while the line is the one he named
            d["item"], d["named_by"] = norm(nm[1]), ("the voucher's scan" if nm[2].startswith("scan") else "your Marg screen")   # S973
        elif d["printed"] not in names and names:
            c = sorted(n for n in names if name_match({n}, d["printed"]))
            if len(c) == 1:
                d["item"] = c[0]
            elif len(c) > 1:
                hit = _by_register(con, d, set(c))
                if hit:
                    d["item"], d["named_by"] = hit, "Marg's Stock Register"
                else:
                    d["ambiguous"] = c
        d["item"] = norm(d["item"])
        out.append(d)
    return out


def spans(con):
    """{ISSUE: [(from, to), ...], RECEIVE: [...]} -- each sound report's own period (a gap between two reports is covered by neither)."""
    out = {}
    if not _has(con, "mi_voucher_file"):
        return out
    for kind, f, t in con.execute("SELECT kind, date_from, date_to FROM mi_voucher_file WHERE ok=1"):
        out.setdefault(kind, []).append((_day(f), _day(t)))
    return out


def covered(S, kind, day):
    """True when a sound report of this kind covers this ISO day (S from spans())."""
    return any(f <= str(day or "") <= t for f, t in S.get(kind, []))


def export_day(con, kind, day):
    """The ISO day the newest sound report of this kind covering `day` was exported ('' when unknown). A voucher keyed that day after the
    export is not in it (second look M1)."""
    if not _has(con, "mi_voucher_file"):
        return ""
    try:
        r = con.execute("SELECT MAX(exported) FROM mi_voucher_file WHERE ok=1 AND kind=? AND date_from<=? AND date_to>=?", (kind, day, day)).fetchone()
    except sqlite3.Error:
        return ""
    e = str((r or [""])[0] or "")
    return "%s-%s-%s" % (e[:4], e[4:6], e[6:8]) if re.match(r"\d{8}-", e) else ""


def reports(con):
    """{ISSUE: (from, to), RECEIVE: (from, to)} -- the days the newest sound reports cover (the union per kind)."""
    out = {}
    if not _has(con, "mi_voucher_file"):
        return out
    for kind, f, t in con.execute("SELECT kind, MIN(date_from), MAX(date_to) FROM mi_voucher_file WHERE ok=1 GROUP BY kind"):
        out[kind] = (_day(f), _day(t))
    return out


# ------------------------------------------------------------------ what was asked
_QTY = re.compile(r"(\d+)\s*:\s*(\d+)")


def _units_from_words(text, pack):
    """'6 patte + 11 goli' . '6:11' . '25 nag' . '4 goli' . '1 patte + 1 goli' -> units; None when the words carry no quantity."""
    t = str(text or "")
    m = _QTY.search(t)
    if m:
        return int(m.group(1)) * max(int(pack or 1), 1) + int(m.group(2))
    p = re.search(r"(\d+)\s*patte", t)
    g = re.search(r"(\d+)\s*goli", t)
    n = re.search(r"(\d+)\s*nag", t)
    if p or g:
        return (int(p.group(1)) if p else 0) * max(int(pack or 1), 1) + (int(g.group(1)) if g else 0)
    if n:
        return int(n.group(1))
    return None


def _pack_of(con, name):
    for t, col in (("stock_voucher_line", "pack"), ("stock_count_item", "pack_size")):
        if _has(con, t):
            try:
                r = con.execute("SELECT %s FROM %s WHERE item=? ORDER BY rowid DESC LIMIT 1" % (col, t), (name,)).fetchone()
                if r and r[0]:
                    return int(r[0])
            except sqlite3.Error:
                pass
    if _has(con, "stock_batch_fix"):
        r = con.execute("SELECT pack FROM stock_batch_fix WHERE item=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()
        if r and r[0]:
            return int(r[0])
    return 1


def _desk_units(con, key):
    """S969: (pack, units) of a Stock check desk Write off (amir_job key S969:wo:...), from stock_desk_action; S971: of a reversal asked by
    the inquiry (S971:rev:...), from stock_inquiry_job; None otherwise."""
    if str(key or "").startswith("S971:rev:") and _has(con, "stock_inquiry_job"):
        try:
            r = con.execute("SELECT pack, units FROM stock_inquiry_job WHERE job_key=?", (str(key),)).fetchone()
        except sqlite3.Error:
            return None
        return (max(int(r[0] or 1), 1), int(r[1])) if (r and r[1]) else None
    if not str(key or "").startswith("S969:wo:") or not _has(con, "stock_desk_action"):
        return None
    try:
        r = con.execute("SELECT pack, units FROM stock_desk_action WHERE job_key=? AND kind='writeoff'", (str(key),)).fetchone()
    except sqlite3.Error:
        return None
    return (max(int(r[0] or 1), 1), int(r[1])) if (r and r[1]) else None


def asks(con):
    """Every correction asked of Amir that moves Marg's stock by a voucher: [dict(id, src, ref, kind, item, pack, units, batch, day, done_day,
    typed, pair, why)]. A count line voided or with nothing to move asks nothing; a superseded batch fix asks nothing."""
    out = []
    # 1 · the count rounds' vouchers (one batch = one Marg voucher)
    if _has(con, "stock_voucher_line"):
        ent, void, ent_at = {}, set(), {}
        if _has(con, "stock_voucher_entered"):
            for cid, rno, kind, bno, no, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                                "FROM stock_voucher_entered ORDER BY id"):
                ent[(cid, rno, kind, bno)] = (str(no or "").strip(), _day(eon) or _day(at), _day(at))
                ent_at[(cid, rno, kind, bno)] = str(at or "").replace(" ", "T")[:19]          # S967: the done mark's own moment
        if _has(con, "stock_voucher_void"):
            void = {tuple(r) for r in con.execute("SELECT count_id, round_no, kind, batch_no FROM stock_voucher_void")}
        for i, cid, rno, kind, bno, item, pack, ch, made_at, reason in con.execute(
                "SELECT id, count_id, round_no, kind, batch_no, item, pack, change, made_at, reason FROM stock_voucher_line ORDER BY id"):
            k = (cid, rno, kind, bno)
            if k in void or not ch:
                continue
            no, eday, _ = ent.get(k, ("", "", ""))
            out.append(dict(id="c%d" % i, src="count", ref="count %d · round %d · %s %d" % (cid, rno, kind.lower(), bno), kind=kind, item=str(item),
                            pack=int(pack or 1), units=abs(int(ch)), batch=None, day=_day(made_at), done_day=(eday if no else ""),
                            typed=(vno(kind, no) if no else ""), pair=None, why=str(reason or "")[:80], group="count:%d:%d:%s:%d" % k,
                            done_ts=(ent_at.get(k, "") if no else ""), asked_ts=str(made_at or "").replace(" ", "T")[:19]))
    # 2 · the tap jobs that ask a voucher in their own words (the count's own lines asked again are the SAME correction: merged)
    if _has(con, "amir_job"):
        for i, key, subj, txt, sub, cat, done, how in con.execute("SELECT id, key, subject, text_hi, sub_hi, created_at, done_at, done_how FROM amir_job "
                                                                  "WHERE kind='tap' ORDER BY id"):
            if str(how or "") == "withdrawn":                 # S971: the owner withdrew it -- it asks nothing (never 'not in Marg')
                continue
            t = str(txt or "")
            m = re.search(r"STOCK\s+(ISSUE|RECEIVE)", t.upper())
            if not m:
                continue
            kind = m.group(1)
            dk = _desk_units(con, key)                       # S969: a desk Write off -- its own pack and units
            pack = dk[0] if dk else _pack_of(con, subj)
            u = dk[1] if dk else _units_from_words(t, pack)
            if not u:
                continue
            same = [a for a in out if a["src"] in ("count", "job") and a["kind"] == kind and norm(a["item"]) == norm(subj)]
            if same and str(key).startswith(("fix:S569", "fix:S572", "S829:", "S957:")):
                a = same[-1]                                  # the same correction asked again: Amir's tap is its 'done'; a newer, larger figure wins
                a["jobs"] = a.get("jobs", []) + [str(key)]
                a.setdefault("history", []).append(dict(key=str(key), asked=_day(cat), done=_day(done)))
                if u > a["units"]:
                    a["units"], a["day"] = u, _day(cat)
                cts, dts = str(cat or "").replace(" ", "T")[:19], str(done or "").replace(" ", "T")[:19]
                if done:
                    a.setdefault("_dones", []).append(dts)
                elif cts:
                    a.setdefault("_opens", []).append(cts)
                continue
            out.append(dict(id="j%d" % i, src="job", ref=str(key), kind=kind, item=str(subj), pack=pack, units=u, batch=None, day=_day(cat),
                            done_day=_day(done), typed="", pair=None, why=str(sub or "")[:80], group="job:%d" % i, jobs=[str(key)],
                            done_ts=str(done or "").replace(" ", "T")[:19], asked_ts=str(cat or "").replace(" ", "T")[:19]))
    # F-1706 (S967; review S4: decided on time, never on the order of ids): the newest done tap against the newest re-ask still open.
    # A done mark known only by its day stands for the end of that day (a re-ask the same day never clears it).
    for a in out:
        if "_dones" not in a and "_opens" not in a:
            continue
        own = a.get("done_ts") or (a["done_day"] + "T23:59:59" if a.get("done_day") else "")
        merged = [x for x in a.pop("_dones", []) if x]
        dones = merged + ([own] if own else [])
        opens = a.pop("_opens", [])
        nd, no_ = (max(dones) if dones else ""), (max(opens) if opens else "")
        if no_ and no_ > nd:
            a["done_day"], a["done_ts"] = "", ""                              # asked again after the newest done mark: waiting again
            if nd:
                a["reasked"] = no_[:10]                                       # (second look 6: only when there was a done mark to clear)
        elif nd:                                                              # second look 1: the day keeps Amir's typed Marg day; a merged tap only moves it later
            a["done_day"], a["done_ts"] = max([a.get("done_day") or ""] + [x[:10] for x in merged]), nd
            a.pop("reasked", None)
    # 3 · the wrong-batch fixes: a pair
    if _has(con, "stock_batch_fix"):
        for i, kind, item, pack, minus, units, iss, aday, status, done in con.execute(
                "SELECT id, kind, item, pack, minus_batch, units, issue_batch, asked_day, status, done_at FROM stock_batch_fix ORDER BY id"):
            if not units:
                continue
            dd = _day(done) if status == "done" else ""
            base = dict(src="batch", item=str(item), pack=int(pack or 1), units=int(units), day=_day(aday), typed="", pair="b%d" % i,
                        why="wrong batch", group="batch:%d" % i, status=status,
                        superseded=(status == "superseded"))
            out.append(dict(base, id="b%dR" % i, ref="batch fix %d · receive" % i, kind="RECEIVE", batch=str(minus or ""),
                            done_day=(dd or ("x" if status in ("receive_only",) else ""))))
            out.append(dict(base, id="b%dI" % i, ref="batch fix %d · issue" % i, kind="ISSUE", batch=str(iss or ""),
                            done_day=(dd or ("x" if status in ("issue_only",) else ""))))
    for a in out:
        if a.get("done_day") == "x":
            a["done_day"] = a["day"]
    return out


# ------------------------------------------------------------------ the judge
CANCEL_DAYS = 7                                             # an issue and a receive of the same item, batch and units within a week cancel out


def _int_setting(con, key, default, lo=0, hi=60):
    """S971: a whole-number setting of the owner's (the setting table), within lo..hi; the default otherwise."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        v = int(str(r[0]).strip()) if r and str(r[0]).strip() else default
        return v if lo <= v <= hi else default
    except (sqlite3.Error, ValueError, TypeError):
        return default
ASK_WORD = dict(in_marg="in Marg", waiting="waiting on Amir", not_in_marg="Amir said done — not in Marg", beyond="after the newest report — the next one decides", gap="no report covers its day",
                wrong_batch="in Marg, wrong batch", part="in Marg, not the asked figure", fixed_other="Marg's batch figures agree — no voucher of its own",
                before="before the reports' first day", superseded="an earlier figure, since remade")
LINE_WORD = dict(asked="asked", more="more than asked", less="less than asked", twice="keyed twice", unasked="nobody asked",
                 cancel="keyed and undone — no effect", wrong_batch="wrong batch", evened="more than asked — evened later", sum="asked (two corrections in one line)", cut="size not printed")


def _lo(a):
    return (dt.date.fromisoformat(a["day"]) - dt.timedelta(days=GRACE_DAYS)).isoformat() if a.get("day") else ""


def _fits(a, ln, used, batch="exact"):
    if ln["key"] in used or ln["kind"] != a["kind"] or not name_match(a["forms"], ln["item"]):
        return False
    lo = _lo(a)
    if lo and ln["day"] and ln["day"] < lo:
        return False
    if batch == "exact" and a["batch"] not in (None, "") and bnorm(ln.get("batch")) != bnorm(a["batch"]):
        return False
    if batch == "other" and (a["batch"] in (None, "") or bnorm(ln.get("batch")) == bnorm(a["batch"])):
        return False
    return True


def judge(con, today=None):
    """{ok, reports, asks, lines, vouchers, items, totals} -- read only."""
    today = today or dt.date.today().isoformat()
    cancel_days = _int_setting(con, "stock.voucher_cancel_days", CANCEL_DAYS, 0, 30)      # S971: his setting
    L = marg_lines(con)
    R = reports(con)
    SP = spans(con)
    A = asks(con)
    ren = renames(con)
    for a in A:
        a["forms"] = forms(a["item"], ren)
        a["match"], a["state"], a["lines"] = None, "", []
    used = {}

    def take(a, ln, state):
        used[ln["key"]] = a["id"]
        a["lines"].append(ln)
        a["match"] = a["match"] or ln
        ln["ask"], ln["state"] = a["id"], state

    order = sorted(A, key=lambda a: (a["day"] or "", a["id"]))
    # 1 · the exact answer: kind, item, units, batch, on or after the ask (Amir's typed number first)
    for a in A:                                               # keyed (Amir's typed number) before the reports' first day: theirs to judge, not ours
        cov = R.get(a["kind"])
        if cov and a.get("typed") and a.get("done_day") and a["done_day"] < cov[0]:
            a["state"], a["match"] = "before", None
    for ln in L:
        if ln.get("ambiguous"):
            used[ln["key"]] = "cut"
            ln["state"] = "cut"

    def exact(pool, typed_only=False):
        for a in pool:
            if a["match"] or a["state"]:
                continue
            c = [ln for ln in L if _fits(a, ln, used) and int(ln["units"]) == a["units"] and (not typed_only or ln["no"] == a["typed"])]
            if c:
                c.sort(key=lambda ln: (ln["no"] != a["typed"], ln["day"]))
                take(a, c[0], "asked")
    exact([a for a in order if not a.get("superseded") and a.get("typed")], typed_only=True)   # the number Amir typed claims its own line first
    exact([a for a in order if not a.get("superseded")])
    # 2 · two corrections of one item keyed as one line (a count's two rounds)
    for ln in L:
        if ln["key"] in used:
            continue
        open_ = [a for a in order if not a["match"] and not a["state"] and not a.get("superseded") and a["batch"] is None and _fits(a, ln, {})]
        hit = next(((x, y) for i, x in enumerate(open_) for y in open_[i + 1:] if x["units"] + y["units"] == int(ln["units"])), None)
        if hit:
            for a in hit:
                a["lines"].append(ln)
                a["match"] = ln
            used[ln["key"]] = hit[0]["id"]
            ln["ask"], ln["state"] = "%s+%s" % (hit[0]["id"], hit[1]["id"]), "sum"
    # 3 · an issue and a receive nobody asked that cancel out (same item, batch, units, within a week)
    free = [ln for ln in L if ln["key"] not in used]
    for x in free:
        if x["key"] in used or x["kind"] != "ISSUE":
            continue
        for y in free:
            if y["key"] in used or y["kind"] != "RECEIVE" or norm(y["item"]) != norm(x["item"]) or int(y["units"]) != int(x["units"]):
                continue
            if bnorm(y.get("batch")) != bnorm(x.get("batch")):
                continue
            if abs((dt.date.fromisoformat(x["day"]) - dt.date.fromisoformat(y["day"])).days) > cancel_days:
                continue
            for ln, o in ((x, y), (y, x)):
                used[ln["key"]] = "cancel"
                ln["state"], ln["pair"] = "cancel", "%s %s" % (o["no"], o["day"])
            break
    exact([a for a in order if a.get("superseded")])       # an earlier figure, since remade, answered by a line nothing else claims
    # 4 · a batch fix keyed from the wrong batch (right item, kind and units)
    for a in order:
        if a["match"] or a["state"] or a["src"] != "batch":
            continue
        c = [ln for ln in L if _fits(a, ln, used, "other") and int(ln["units"]) == a["units"]]
        if c:
            take(a, sorted(c, key=lambda ln: ln["day"])[0], "wrong_batch")
            a["state"] = "wrong_batch"
    # 5 · a different figure: each line left over to the nearest open ask of its item (batch for batch where asked)
    for ln in L:
        if ln["key"] in used:
            continue
        c = [a for a in order if not a["match"] and not a["state"] and not a.get("superseded") and _fits(a, ln, used)]
        if c:
            c.sort(key=lambda a: (abs(a["units"] - int(ln["units"])), a["day"] or ""))
            a = c[0]
            take(a, ln, "more" if int(ln["units"]) > a["units"] else "less")
            a["state"] = "part"
    # 6 · 'more than asked' evened later by a job asking the difference back (OSTOVAXL 25 vs 21, then L000030's 4)
    for ln in L:
        if ln.get("state") not in ("more", "less"):
            continue
        a = next(x for x in A if x["id"] == ln["ask"])
        diff = abs(int(ln["units"]) - a["units"])
        ev = next((x for x in A if x["src"] == "job" and x["match"] and x["kind"] != ln["kind"] and x["units"] == diff
                   and norm(x["match"]["item"]) == norm(ln["item"])), None)
        if ev:
            ln["state"], ln["evened"] = "evened", "%s %s" % (ev["match"]["no"], ev["match"]["day"])
            a["state"] = "in_marg"
    # the ask side
    for a in A:
        if a["state"]:
            continue
        if a["match"]:
            a["state"] = "in_marg"
            continue
        if a.get("superseded"):
            a["state"] = "superseded"                         # an earlier figure, since remade: asks nothing now
            continue
        cov = R.get(a["kind"])
        if a["src"] == "batch" and a.get("status") == "done" or (a["src"] == "batch" and a.get("done_day")):
            a["state"] = "fixed_other"
        elif cov and a.get("done_day") and cov[0] <= a["done_day"] <= cov[1] and not covered(SP, a["kind"], a["done_day"]):
            a["state"] = "gap"                                # said done on a day no report covers (review S5): a report of that period decides
        elif not cov or (a["day"] and a["day"] > cov[1]):
            a["state"] = "beyond"
        elif a.get("done_day") and a["done_day"] < cov[0]:
            a["state"] = "before"
        elif a.get("done_day") and (a["done_day"] > cov[1] or (export_day(con, a["kind"], cov[1]) or "9999") <= a["done_day"]):
            a["state"] = "beyond"                             # done after the newest report's last day, or on its export day (review M1, second look M1)
        elif a.get("done_day"):
            a["state"] = "not_in_marg"
        else:
            a["state"] = "waiting"
    # the Marg side: what nobody asked (a twin of an asked line is 'keyed twice')
    for ln in L:
        if ln.get("state"):
            continue
        twin = [x for x in L if x is not ln and x.get("ask") and x["kind"] == ln["kind"] and norm(x["item"]) == norm(ln["item"])
                and int(x["units"]) == int(ln["units"]) and bnorm(x.get("batch")) == bnorm(ln.get("batch"))]
        ln["state"] = "twice" if twin else "unasked"
        if twin:
            ln["twin"] = "%s %s" % (twin[0]["no"], twin[0]["day"])
    for ln in L:
        ln["word"] = LINE_WORD.get(ln["state"], ln["state"])
    for a in A:
        a["word"] = ASK_WORD.get(a["state"], a["state"])
    # vouchers, each with its lines (the pages fold them)
    V = {}
    for ln in L:
        v = V.setdefault((ln["kind"], ln["no"]), dict(kind=ln["kind"], no=ln["no"], day=ln["day"], lines=[]))
        v["lines"].append(ln)
    RED = ("twice", "unasked", "more", "less", "wrong_batch")
    vouchers = []
    for v in sorted(V.values(), key=lambda v: (v["day"], v["no"])):
        s = [ln["state"] for ln in v["lines"]]
        v["flags"] = sum(1 for x in s if x in RED)
        v["state"] = ("unasked" if all(x == "unasked" for x in s) else "flag" if v["flags"] else "cut" if "cut" in s
                      else "cancel" if all(x == "cancel" for x in s) else "asked")
        vouchers.append(v)
    # per item: Marg's printed names and every form of the asks, one entry each
    items = {}
    for ln in L:
        items.setdefault(norm(ln["item"]), {"lines": [], "asks": []})["lines"].append(ln)
    for a in A:
        items.setdefault(norm(a["match"]["item"]) if a["match"] else norm(a["item"]), {"lines": [], "asks": []})["asks"].append(a)
    tot = dict(vouchers=len(vouchers), lines=len(L), asks=len(A))
    for k in ASK_WORD:
        tot["ask_" + k] = sum(1 for a in A if a["state"] == k)
    for k in LINE_WORD:
        tot["line_" + k] = sum(1 for ln in L if ln["state"] == k)
    return dict(ok=bool(L), version=VERSION, reports=R, spans=SP, asks=A, lines=L, vouchers=vouchers, items=items, totals=tot, at=today)



# ------------------------------------------------------------------ S967: the whole item re-judged (plan S534 §2.3, D1090 D1091 D1092)
HELD = {"VINBACTUM DS": "held -- your word 26-11: old Marg residue, ignore for now (D1077)"}
OLD_STATES = ("not_in_marg", "part", "wrong_batch")          # the old cards: said done and not in Marg, or in Marg not as asked
WAY_STATES = ("waiting", "beyond", "gap")                     # on its way to Marg: the next report decides
V_WORD = dict(settled="settled by later entries", count_first="count first", fresh_gap="today's gap", held="held", look="look first",
              unknown="not in the record")


def sst(units, pack):
    """st() with a sign: '+1:4' / '−2:12' / '0'."""
    try:
        v = int(round(float(units)))
    except (TypeError, ValueError):
        return "—"
    return ("−" if v < 0 else ("+" if v > 0 else "")) + st(abs(v), pack)


def dmy(iso):
    s = str(iso or "")[:10]
    return "%s-%s-%s" % (s[8:10], s[5:7], s[:4]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else s


def record_rows(con):
    """{norm(item): row} of the stock of record (stock_record's table, read as it stands); {} when it is not there."""
    if not _has(con, "stock_of_record"):
        return {}
    out = {}
    try:
        cols = [d[1] for d in con.execute("PRAGMA table_info(stock_of_record)")]
        for r in con.execute("SELECT * FROM stock_of_record"):
            d = dict(zip(cols, r))
            try:
                d["forms"] = [norm(x) for x in json.loads(d.get("forms_json") or "[]")]
            except (TypeError, ValueError):
                d["forms"] = []
            out[norm(d["item"])] = d
    except sqlite3.Error:
        return {}
    return out


def record_for(RR, names):
    """The record's row for an item known by any of `names` (its forms): the exact name, a printed form the record keeps, else the one row
    whose name is the cut of it (or it the cut of the row's). None when none, or several, fit."""
    F = {norm(n) for n in names if n}
    for f in F:
        if f in RR:
            return RR[f]
    for d in RR.values():
        if F & set(d.get("forms") or []):
            return d
    c = [d for k, d in RR.items() if name_match(F, k)]
    return c[0] if len(c) == 1 else None


def whole_item(R, item="", fresh_from=None):
    """THE WHOLE-ITEM VERDICT on today's record row R: dict(v, word, short, gap, gap_t, marg_t, shelf_t, base, base_kind). v: settled .
    count_first . fresh_gap . held . look . unknown."""
    nm = norm((R or {}).get("item") or item)
    if nm in HELD:
        return dict(v="held", word=HELD[nm], gap=None, gap_t="—", marg_t="—", shelf_t="—", base="", base_kind="")
    if R is None:
        return dict(v="unknown", word="not in the stock of record -- nothing can be judged on the whole item", gap=None, gap_t="—", marg_t="—",
                    shelf_t="—", base="", base_kind="")
    pack = int(R.get("pack") or 1) or 1
    g = R.get("gap_units")
    out = dict(gap=(int(round(float(g))) if g is not None else None), gap_t=(sst(g, pack) if g is not None else "—"),
               marg_t=st(int(round(float(R.get("marg_units") or 0))), pack), shelf_t=(st(int(round(float(R["shelf_units"]))), pack) if R.get("shelf_units") is not None else "—"),
               base=dmy(R.get("base_day")), base_kind=R.get("base_kind") or "", pack=pack, key=R.get("k20") or "", item=R.get("item"))
    old = (R.get("base_kind") == "count") or ("old_base" in str(R.get("marg_flag") or "")) or bool(fresh_from and str(R.get("base_day") or "") < fresh_from)
    if R.get("state") == "consumable":
        return dict(out, v="held", word="a clinic consumable -- never judged as a shop difference")
    if R.get("state") == "marg_behind":
        return dict(out, v="look", word="Marg's figure is behind a bill -- the purchase side is settled first")
    if g is None or R.get("state") == "no_shelf":
        return dict(out, v="count_first", word="no shelf figure yet -- count first on Darpan's next list")
    if abs(float(g)) < 0.5:
        return dict(out, v="settled", word="Marg agrees with the shelf today (%s) -- settled by later entries; nothing to Amir" % out["marg_t"])
    if old:
        return dict(out, v="count_first", word="the shelf is only the count of %s carried forward (Marg %s, shelf %s) -- count first on Darpan's next list; "
                    "the old ask is overtaken" % (out["base"], out["marg_t"], out["shelf_t"]))
    return dict(out, v="fresh_gap", word="a fresh count of %s still differs by %s (Marg %s, shelf %s) -- one correction for today's gap, never the old figure" % (
        out["base"], out["gap_t"], out["marg_t"], out["shelf_t"]))


def rejudge(con, J=None, RR=None, fresh_from=None):
    """The old cards (asks said done and not in Marg, or in Marg not as asked), one entry per item, re-judged on the whole item:
    [dict(item, verdict (whole_item), asks=[dict(ask, src, state, word, asked, done)], batch_only, batch_note)]. Each ask also gets
    a['rejudge'] = the verdict's v. Read only."""
    J = J or judge(con)
    RR = record_rows(con) if RR is None else RR
    by = {}
    for a in J.get("asks") or []:
        if a.get("state") not in OLD_STATES:
            continue
        names = set(a.get("forms") or {norm(a["item"])})
        if a.get("match"):
            names.add(norm(a["match"]["item"]))
        R = record_for(RR, names)
        k = norm(R["item"]) if R else norm(a["item"])
        e = by.setdefault(k, dict(item=(R["item"] if R else a["item"]), R=R, asks=[], lines=[]))
        e["asks"].append(a)
    for ln in J.get("lines") or []:                           # Marg's side: a line keyed twice, or more / less than asked (the 'not as asked' cards)
        if ln.get("state") not in ("twice", "more", "less"):
            continue
        R = record_for(RR, {norm(ln["item"])})
        k = norm(R["item"]) if R else norm(ln["item"])
        e = by.setdefault(k, dict(item=(R["item"] if R else ln["item"]), R=R, asks=[], lines=[]))
        e["lines"].append(ln)
    out = []
    for k, e in by.items():
        V = whole_item(e["R"], e["item"], fresh_from)
        for a in e["asks"]:
            a["rejudge"] = V["v"]
        bat = [a for a in e["asks"] if a["src"] == "batch"]
        out.append(dict(item=e["item"], key=(e["R"] or {}).get("k20") or "", verdict=V, batch_only=(bool(e["asks"]) and len(bat) == len(e["asks"])),
                        marg_lines=[dict(no=ln["no"], day=dm(ln["day"]), kind=ln["kind"], q=st(ln["units"], ln.get("per") or 1), state=ln["state"],
                                         word=ln.get("word") or LINE_WORD.get(ln["state"], ln["state"]), ref=(ln.get("twin") or "")) for ln in e["lines"]],
                        batch_note=("the batch part stays with the Expiry watch's night asks to Amir (your word 27-11) -- this desk raises nothing on it"
                                    if bat else ""),
                        asks=[dict(ask=_ask_line(a), src=_src_word(a), state=a["state"], word=a.get("word") or ASK_WORD.get(a["state"], a["state"]),
                                   asked=dm(a["day"]), done=dm(a.get("done_day")), forms=sorted(a.get("forms") or [])) for a in e["asks"]]))
    order = dict(fresh_gap=0, count_first=1, look=2, settled=3, held=4, unknown=5)
    out.sort(key=lambda x: (order.get(x["verdict"]["v"], 9), x["item"]))
    return out


# ------------------------------------------------------------------ the owner's pages (Stock check's two boxes, the tags, the ledger's lines)
def st(units, pack):
    """'16:3' strips:tabs for a packed item, '25' pieces for pack 1."""
    try:
        v = int(units)
    except (TypeError, ValueError):
        return "—"
    p = max(int(pack or 1), 1)
    return ("%d:%d" % (v // p, v % p)) if p > 1 else "%d" % v


def dm(iso):
    s = str(iso or "")
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) >= 10 else s


def _vline(ln):
    per = int(ln.get("per") or 1)
    return dict(item=ln["item"], q=st(ln["units"], per), batch=ln.get("batch") or "", state=ln["state"], word=ln["word"],
                ref=(ln.get("twin") or ln.get("pair") or ln.get("evened") or ""))


def _ask_line(a):
    q = st(a["units"], a["pack"])
    b = ("into %s" % (a["batch"] or "no batch") if a["kind"] == "RECEIVE" else "from %s" % (a["batch"] or "no batch")) if a["batch"] is not None else ""
    return ("%s %s %s" % (a["kind"].title(), q, b)).strip()


def _src_word(a):
    return {"count": "the 06-Sep count", "job": "Amir's card", "batch": "a wrong-batch fix (Expiry watch)"}.get(a["src"], a["src"])


TAG = dict(unasked=("red", "Nobody asked"), twice=("red", "Keyed twice"), more=("red", "More than asked"), less=("red", "Less than asked"),
           wrong_batch=("red", "Wrong batch"), not_in_marg=("red", "Not in Marg"), waiting=("amb", "Waiting on Amir"), part=("red", "Not as asked"),
           beyond=("amb", "After the newest report"), gap=("amb", "No report covers it"))


def page(con, today=None):
    """The JSON of the Stock check's voucher section and its item tags. Read only. Never raises past a plain {ok: False}."""
    try:
        J = judge(con, today)
    except Exception as ex:                                   # noqa: BLE001
        return dict(ok=False, reason="The vouchers could not be judged: %s" % type(ex).__name__)
    if not J["ok"]:
        return dict(ok=False, reason="No Stock Issue / Stock Receive report has been read yet.", registers=registers(con))
    today = J["at"]
    A, L = J["asks"], J["lines"]
    cash = {}
    try:
        for kind, no, c in con.execute("SELECT kind, no, cash FROM mi_voucher_now"):
            cash[(kind, no)] = c
    except sqlite3.Error:
        pass
    rep = {}
    for kind in ("ISSUE", "RECEIVE"):
        V = [v for v in J["vouchers"] if v["kind"] == kind]
        f, t = J["reports"].get(kind, ("", ""))
        nos = sorted(int(re.sub(r"\D", "", v["no"]) or 0) for v in V)
        gaps = [n for n in range(nos[0], nos[-1] + 1) if n not in set(nos)] if nos else []
        rep[kind] = dict(frm=dm(f) + ("-" + f[:4] if f else ""), to=dm(t) + ("-" + t[:4] if t else ""), n=len(V),
                         lines=sum(len(v["lines"]) for v in V), first=(V[0]["no"] if V else ""), last=(V[-1]["no"] if V else ""),
                         missing=[vno(kind, n) for n in gaps])
    by_v = {(v["kind"], v["no"]): v for v in J["vouchers"]}

    def vcard(v):
        return dict(kind=v["kind"], no=v["no"], day=dm(v["day"]), cash=("cash" if cash.get((v["kind"], v["no"]), 1) else "party"),
                    lines=[_vline(x) for x in v["lines"]], flags=v["flags"])
    moves = [vcard(v) for v in sorted(J["vouchers"], key=lambda v: (v["day"], v["no"]), reverse=True)
             if any(x["state"] == "unasked" for x in v["lines"])]   # a cut line is in 'cut', not here
    # corrections asked of Amir
    nim = [dict(item=a["item"], ask=_ask_line(a), src=_src_word(a), asked=dm(a["day"]), done=dm(a.get("done_day")),
                typed=a["typed"], typed_has=(bool(a["typed"]) and (a["kind"], a["typed"]) in by_v),
                typed_lines=([x["item"] for x in by_v[(a["kind"], a["typed"])]["lines"]] if (a["kind"], a["typed"]) in by_v else []))
           for a in A if a["state"] == "not_in_marg"]
    off = {}
    for ln in L:
        if ln["state"] in ("twice", "more", "less", "wrong_batch"):
            off.setdefault(norm(ln["item"]), dict(item=ln["item"], lines=[], asks=[]))["lines"].append(ln)
    for a in A:
        if a["state"] in ("part", "wrong_batch"):
            k = norm(a["match"]["item"]) if a["match"] else norm(a["item"])
            off.setdefault(k, dict(item=a["item"], lines=[], asks=[]))["asks"].append(a)
    offl = []
    for k, o in off.items():
        lines = sorted({id(x): x for x in o["lines"] + [y for a in o["asks"] for y in a["lines"]]}.values(), key=lambda x: (x["day"], x["no"]))
        words = sorted({x["word"] for x in lines if x["state"] in ("twice", "more", "less", "wrong_batch")})
        offl.append(dict(item=o["item"], words=words, asks=[dict(ask=_ask_line(a), src=_src_word(a), asked=dm(a["day"])) for a in o["asks"]],
                         lines=[dict(_vline(x), no=x["no"], day=dm(x["day"]), kind=x["kind"]) for x in lines]))
    offl.sort(key=lambda o: o["item"])
    wait = {}
    for a in A:
        if a["state"] in ("waiting", "beyond", "gap"):
            w = wait.setdefault(a["group"], dict(item=a["item"], src=_src_word(a), asked=dm(a["day"]), iso=a["day"] or "", asks=[],
                                                 beyond=(a["state"] == "beyond"), gap=(dm(a.get("done_day")) if a["state"] == "gap" else "")))
            w["asks"].append(_ask_line(a))
    waiting = sorted(wait.values(), key=lambda w: (w["iso"], w["item"]))
    done_v = []
    for v in sorted(J["vouchers"], key=lambda v: (v["day"], v["no"]), reverse=True):
        if v["state"] != "asked":
            continue
        srcs = sorted({_src_word(next(a for a in A if a["id"] == x["ask"].split("+")[0])) for x in v["lines"] if x.get("ask") and x["state"] != "cancel"})
        c = vcard(v)
        c["src"] = " · ".join(srcs)
        done_v.append(c)
    cancels = [dict(_vline(x), no=x["no"], day=dm(x["day"]), kind=x["kind"]) for x in L if x["state"] == "cancel"]
    other = [dict(item=a["item"], ask=_ask_line(a), asked=dm(a["day"]), done=dm(a.get("done_day"))) for a in A if a["state"] == "fixed_other"]
    # the tags per printed name (the page matches a row's name, or its cut)
    tags = {}

    def tg(name, t):
        lst = tags.setdefault(norm(name), [])
        if t not in lst:
            lst.append(t)
    for ln in L:
        if ln["state"] in TAG:
            c, w = TAG[ln["state"]]
            tg(ln["item"], [c, "%s · %s" % (w, ln["no"])])
    for a in A:
        if a["state"] in ("not_in_marg", "waiting", "beyond", "gap"):
            c, w = TAG[a["state"]]
            tg(a["item"], [c, w])
            for f in a["forms"]:
                tg(f, [c, w])
        elif a["state"] == "in_marg" and a["match"] and a["match"]["day"] >= (dt.date.fromisoformat(today) - dt.timedelta(days=30)).isoformat():
            tg(a["match"]["item"], ["grn", "In Marg · %s · %s" % (a["match"]["no"], dm(a["match"]["day"]))])
    cut = [dict(kind=x["kind"], no=x["no"], day=dm(x["day"]), printed=x["printed"], q=st(x["units"], x.get("per") or 1), cands=x["ambiguous"])
           for x in L if x.get("ambiguous")]
    T = J["totals"]
    chips = dict(cut=len(cut), moves=len(moves), not_in_marg=len(nim), off=len(offl), waiting=len(waiting), done=len(done_v))
    return dict(ok=True, version=VERSION, at=today, reports=rep, moves=moves, not_in_marg=nim, off=offl, waiting=waiting, done=done_v,
                cancels=cancels, other=other, tags=tags, chips=chips, totals=T, registers=registers(con), cut=cut,
                named=[dict(no=x["no"], day=dm(x["day"]), printed=x["printed"], item=x["item"], by=x["named_by"]) for x in L if x.get("named_by")])


ASK_DDL = ("CREATE TABLE IF NOT EXISTS mi_voucher_regask (kind TEXT NOT NULL, no TEXT NOT NULL, n INTEGER NOT NULL, item TEXT NOT NULL, "
           "at TEXT NOT NULL, PRIMARY KEY (kind, no, n, item))")


def ask_registers(con, who="voucher check"):
    """A cut name that fits several items: Marg's one-item Stock Register of each, for the voucher's day, asked on the owner's own list
    (the Marg watch's register asks, marg_billwatch.reg_ask_item -- an ask already made is not made again). -> number newly asked.
    Never raises."""
    n = 0
    try:
        L = [x for x in marg_lines(con) if x.get("ambiguous")]
        if not L:
            return 0
        import marg_billwatch as BW                           # noqa: PLC0415 -- beside this file: the register asks' own writer
        con.execute(ASK_DDL)
        for x in L:
            for c in x["ambiguous"]:
                if con.execute("SELECT 1 FROM mi_voucher_regask WHERE kind=? AND no=? AND n=? AND item=?", (x["kind"], x["no"], int(x.get("n") or 0), c)).fetchone():
                    continue                                  # asked once already: never again, whatever became of it (review S8)
                ok, _msg, _code = BW.reg_ask_item(con, who, c, x["day"], x["day"])
                if not ok and _code == 503:
                    continue                                  # the database busy: asked again at the next read (second look N3)
                con.execute("INSERT OR IGNORE INTO mi_voucher_regask (kind, no, n, item, at) VALUES (?,?,?,?,?)",
                            (x["kind"], x["no"], int(x.get("n") or 0), c, dt.datetime.now().isoformat(timespec="seconds")))
                n += 1 if ok else 0
        con.commit()
    except Exception:                                         # noqa: BLE001
        return n
    return n


def registers(con):
    """F-1690: every one-item Stock Register read (asked or not), newest first -- item, period, opening, closing, lines."""
    out = []
    if not _has(con, "mi_register"):
        return out
    try:
        for md5, seq, item, pack, per, f, t, o, c, n, ok, at in con.execute(
                "SELECT md5, seq, item, pack, per, date_from, date_to, opening_u, closing_u, n_lines, ok, stored_at FROM mi_register "
                "ORDER BY stored_at DESC LIMIT 30"):
            out.append(dict(item=item, frm=dm(_day(f)), to=dm(_day(t)), opening=st(o, per), closing=st(c, per), lines=n, ok=bool(ok),
                            at=str(at or "")[:16].replace("T", " ")))
    except sqlite3.Error:
        pass
    return out


def item_lines(con, names, J=None):
    """The item ledger's voucher lines for one item (every printed form of its name): [dict(day, kind, no, q, units, batch, state, word, ref,
    voucher=[the voucher's every line])] -- each voucher's lines folded under its row on the page. And the open asks for the item."""
    J = J or judge(con)
    if not J["ok"]:
        return [], []
    ren = renames(con)
    F = set()
    for n in names:
        F |= forms(n, ren)
    by_v = {(v["kind"], v["no"]): v for v in J["vouchers"]}
    out = []
    for ln in J["lines"]:
        if not name_match(F, ln["item"]):
            continue
        v = by_v[(ln["kind"], ln["no"])]
        out.append(dict(day=ln["day"], kind=ln["kind"], no=ln["no"], units=int(ln["units"]) * (1 if ln["kind"] == "RECEIVE" else -1),
                        q=st(ln["units"], ln.get("per") or 1), batch=ln.get("batch") or "", state=ln["state"], word=ln["word"],
                        ref=(ln.get("twin") or ln.get("pair") or ln.get("evened") or ""), voucher=[_vline(x) for x in v["lines"]]))
    asks_open = [dict(ask=_ask_line(a), state=a["state"], word=a["word"], src=_src_word(a), asked=dm(a["day"]), done=dm(a.get("done_day")))
                 for a in J["asks"] if a["state"] in ("waiting", "not_in_marg", "beyond", "gap") and (F & a["forms"])]
    return out, asks_open


if __name__ == "__main__":                                   # python3 voucher_judge.py DB : the totals and every flag (item names only)
    import sys
    con = sqlite3.connect(sys.argv[1])
    J = judge(con)
    print(J["totals"], J["reports"])
    for a in J["asks"]:
        if a["state"] != "in_marg":
            print("ASK", a["state"], a["id"], a["kind"], a["item"], a["units"], a["batch"], a["day"], a.get("done_day"), a["typed"])
    for ln in J["lines"]:
        if ln["state"] != "asked":
            print("LINE", ln["state"], ln["kind"], ln["no"], ln["day"], ln["item"], ln["units"], ln.get("batch"), ln.get("ask", ""), ln.get("twin", ""))


# ---- S973 (27-Nov-2026, Sanjeevni session 540, kit S973_VOUCHER_SCANS; kit C of S534_FINAL_BUILD_PLAN, D1091 plan 2.4) --------------------
#  THE CUT-NAME ROUTE AHEAD OF THE REGISTER: a cut name that fits several items asks the voucher's PRINT first (voucher_scan.cut_asks -- a
#  print card on Amir's page, for vouchers dated on or after stock.scan_ask_from); Marg's one-item Stock Register is asked only when no
#  print ask is open for that voucher (it closed unclear, or with no scan in the question days) -- plan 2.4. A name the scan settled is
#  told 'the voucher's scan' (marg_lines above). Everything else in the judge is unchanged.
import sys as _s973_sys
KIT_S973 = "S973_VOUCHER_SCANS"
VERSION = "1.4"
_ask_registers_before_s973 = ask_registers


def ask_registers(con, who="voucher check"):                 # noqa: F811 -- S973: the print first; the register only when no print ask is open
    try:
        import voucher_scan as VS                             # noqa: PLC0415 -- beside this file
    except Exception:                                         # noqa: BLE001
        return _ask_registers_before_s973(con, who)
    try:
        if VS.on(con) and not con.in_transaction:
            VS.cut_asks(con)
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_judge S973: cut asks stopped: %s" % str(ex)[:200], file=_s973_sys.stderr)
    n = 0
    try:
        L = [x for x in marg_lines(con) if x.get("ambiguous") and not VS.scan_open(con, x["kind"], x["no"], x["day"])]
        if not L:
            return 0
        import marg_billwatch as BW                           # noqa: PLC0415 -- beside this file: the register asks' own writer
        con.execute(ASK_DDL)
        for x in L:
            for c in x["ambiguous"]:
                if con.execute("SELECT 1 FROM mi_voucher_regask WHERE kind=? AND no=? AND n=? AND item=?", (x["kind"], x["no"], int(x.get("n") or 0), c)).fetchone():
                    continue                                  # asked once already: never again, whatever became of it (review S8)
                ok, _msg, _code = BW.reg_ask_item(con, who, c, x["day"], x["day"])
                if not ok and _code == 503:
                    continue                                  # the database busy: asked again at the next read (second look N3)
                con.execute("INSERT OR IGNORE INTO mi_voucher_regask (kind, no, n, item, at) VALUES (?,?,?,?,?)",
                            (x["kind"], x["no"], int(x.get("n") or 0), c, dt.datetime.now().isoformat(timespec="seconds")))
                n += 1 if ok else 0
        con.commit()
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()                                    # never leave the reader's transaction open (the next read must not be blocked)
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_judge S973: register asks stopped: %s" % str(ex)[:200], file=_s973_sys.stderr)
        return n
    return n
# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S975 (28-Nov-2026, Sanjeevni session 542, kit S975_STOCKCHECK_V10; F-1738) -----------------------------------------------------------
#  A fresh count that finds MORE on the shelf than in Marg is never a loss and never 'today's gap -- waits for your call' (CCM, 28-11:
#  shelf 1:0 against Marg 0:0 was told red in box 3 while the count list said 'noted, never a loss'). The whole-item verdict 'surplus'
#  says so; a claim or an ask on it is handled as a fresh gap was (voucher_inquiry closes only on settled / held, as before).
VERSION = "1.5"
KIT_S975 = "S975_STOCKCHECK_V10"
V_WORD = dict(V_WORD, surplus="more than Marg — noted")
_whole_item_before_s975 = whole_item


def whole_item(R, item="", fresh_from=None):                   # noqa: F811 -- S975: a fresh surplus is its own verdict
    V = _whole_item_before_s975(R, item, fresh_from)
    try:                                                       # a whole-unit item (CCM = bottle): its stored count is a pack per bottle --
        import qty_words as _QW                                # never 'surplus' on that figure until the record's pack is put right (second look 3)
        wh = _QW.whole_unit_of(V.get("item") or item)
    except Exception:                                          # noqa: BLE001
        wh = None
    if V.get("v") == "fresh_gap" and V.get("gap") is not None and V["gap"] > 0 and not wh:
        V = dict(V, v="surplus", word="a fresh count of %s finds more on the shelf than in Marg (%s; Marg %s, shelf %s) -- noted, never a loss; "
                                     "nothing waits for your call" % (V.get("base"), V.get("gap_t"), V.get("marg_t"), V.get("shelf_t")))
    if wh and V.get("v") == "fresh_gap":                        # CCM: the stored count is a pack per bottle -- look, never red 'your call'
        V = dict(V, v="look", word="Marg counts %s by the %s, the stock record by a pack of %s -- this count cannot be judged yet; see the item ledger" % (
            V.get("item") or item, wh, V.get("pack")))
    return V
# ---- S975 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S976 (28-Nov-2026, Sanjeevni session 543, kit S976_WHOLE_UNIT_PACK; F-1742) ---------------------------------------------------------
#  A whole-unit item (the desk's list, "CCM = bottle"): Marg's voucher prints its quantity in bottles ('3'); the reading kept from the
#  medical PC took it as 3 packs of its packing (1*40 -> 120). Such a line is read as the bottles Marg printed (per 1); the item's pack is 1; and
#  S975's 'look first -- this count cannot be judged yet' stands only while the record still gives it a pack above 1. Every other item
#  and line is exactly as before.
KIT_S976 = "S976_WHOLE_UNIT_PACK"


def _s976_whole(con, name):
    try:
        import stock_figure as _SF976                         # noqa: PLC0415
        return _SF976._s976_whole(con, name)
    except Exception:                                         # noqa: BLE001
        return None


_pack_of_before_s976 = _pack_of


def _pack_of(con, name):                                      # noqa: F811 -- S976
    p = _pack_of_before_s976(con, name)
    if int(p or 1) > 1 and _s976_whole(con, name):
        return 1
    return p


_marg_lines_before_s976 = marg_lines


def marg_lines(con):                                          # noqa: F811 -- S976: a whole-unit item's line in the bottles Marg printed
    out = _marg_lines_before_s976(con)
    for d in out:
        try:
            q = str(d.get("qty") or "").strip()
            per = int(d.get("per") or 1)
            if per > 1 and re.fullmatch(r"-?\d+", q) and int(d.get("units") or 0) == abs(int(q)) * per and _s976_whole(con, d.get("item")):
                d["units"], d["per"], d["s976"] = abs(int(q)), 1, "read in the item's whole pieces, as Marg printed it"   # per 1: told "3", never "0:3" (cold review M1)
        except (TypeError, ValueError):
            continue
    return out


_whole_item_before_s976 = whole_item


def whole_item(R, item="", fresh_from=None):                   # noqa: F811 -- S976: 'look' only while the record's pack is above 1
    V = _whole_item_before_s976(R, item, fresh_from)
    if V.get("v") == "look" and int(V.get("pack") or 1) <= 1 and str(V.get("word") or "").startswith("Marg counts "):
        V = _whole_item_before_s975(R, item, fresh_from)
        if V.get("v") == "fresh_gap" and V.get("gap") is not None and V["gap"] > 0:
            V = dict(V, v="surplus", word="a fresh count of %s finds more on the shelf than in Marg (%s; Marg %s, shelf %s) -- noted, never a loss; "
                                         "nothing waits for your call" % (V.get("base"), V.get("gap_t"), V.get("marg_t"), V.get("shelf_t")))
    return V
# ---- S976 end ---------------------------------------------------------------------------------------------------------------------------

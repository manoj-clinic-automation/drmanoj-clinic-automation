#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s482.py -- kit S482_BILL_CHAIN (D675 b, D676; F-731, F-732, F-733).

Every file this kit changes is BUILT FROM THE LIVE BYTES by anchored edits: each anchor must occur exactly once, else the build stops
and nothing is written. The two blocks that are added whole are read from this folder (chain_block_s482.py, tile_block_s482.py).
Nothing here opens a database or the network.

  --server        reads /root/marg_ingest and /root/finance (or --ingest / --finance)   -> ingest/marg_take.py, ingest/marg_ingest.py,
                                                                                            finance/reports_tile.py, finance/spine/marg_read.py
  --manojz DIR    DIR is D:\\Downloads\\margsync\\MargPull (marg_gate.py)                  -> manojz/marg_gate.py
  --out DIR       where the built files are written (never beside the live ones)

The FROM pin of every file is checked before its first edit; a file that moved since the brief stops the build.
"""
import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = "S482_BILL_CHAIN"
FROM = {
    "ingest/marg_take.py": "3ac9bbe03abf5c01c4ebc1bfffd30da2",
    "ingest/marg_ingest.py": "7f6b4dc25d1c247c8b45f05108e600ca",
    "finance/reports_tile.py": "406e452b2e3cf5991e89100ee867e1d6",
    "finance/spine/marg_read.py": "7ec9b325687de465ea6942affb25dec1",
    "manojz/marg_gate.py": "52f502d1ee1a59e37086fb3e514f7874",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rd(p):
    with io.open(p, "rb") as fh:
        return fh.read()


def block(name):
    return rd(os.path.join(HERE, name)).decode("utf-8").replace("\r\n", "\n")


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


# ------------------------------------------------------------------------------------------------------- marg_take.py (Part A: the chain)
def build_marg_take(src):
    return edit("marg_take.py", src, [
        # A.1-A.3: the table, rebuild_chain, chain_state -- one block, before the door
        ("# ------------------------------------------------------------------ the door\ndef take(raw, name=\"\", source=\"manual\", db=None, archive=None):\n",
         block("chain_block_s482.py")
         + "# ------------------------------------------------------------------ the door\ndef take(raw, name=\"\", source=\"manual\", db=None, archive=None):\n"),
        # A.2: called at the end of take() whenever a SALE_BILLWISE is VERIFIED (an EMPTY day is one)
        ('                 "", "", "", when, source))\n'
         '            con.commit()\n'
         '            res.update(status="TAKEN",',
         '                 "", "", "", when, source))\n'
         '            con.commit()\n'
         '            if typ == "SALE_BILLWISE" and verdict == "VERIFIED":     # S482 (D675 b): a sale report or an EMPTY day landed -- the chain is rewritten\n'
         '                _s482_chain(con)\n'
         '            res.update(status="TAKEN",'),
    ])


# ----------------------------------------------------------------------------------------------- marg_ingest.py (Part D: F-733, the chain)
def build_marg_ingest(src):
    return edit("marg_ingest.py", src, [
        ('def _connect(db):\n    con = sqlite3.connect(db, timeout=30)\n',
         'def _s482_empty_day(path):\n'
         '    """S482 (F-733), the door\'s own test (marg_take._s480_empty_day): the ISO day of a VERIFIED sale report that carries no bill --\n'
         '    a no-sale day -- else \'\'. The day is the title\'s; the reader (marg_report.read_report) says so with empty=True."""\n'
         '    try:\n'
         '        import marg_report as MR                                 # noqa: PLC0415\n'
         '        rep = MR.read_report(path)\n'
         '        if rep.get("ok") and rep.get("empty") and rep.get("days"):\n'
         '            return rep["days"][0].get("date") or ""\n'
         '    except Exception:                                            # noqa: BLE001\n'
         '        pass\n'
         '    return ""\n'
         '\n'
         '\n'
         'def _s482_rebuild_chain(con):\n'
         '    """S482 (D675 b): a sale report that arrives by Drive alone must not leave the bill chain stale -- the door\'s own rebuild\n'
         '    (marg_take.rebuild_chain), fail-soft: the collector never fails a file because of this."""\n'
         '    try:\n'
         '        import marg_take                                         # noqa: PLC0415\n'
         '        marg_take.rebuild_chain(con)\n'
         '    except Exception as e:                                       # noqa: BLE001\n'
         '        print("marg_ingest: the bill chain was not rebuilt now (%s) -- the next sale report rebuilds it" % str(e)[:120], file=sys.stderr)\n'
         '        try:\n'
         '            con.rollback()\n'
         '        except Exception:                                        # noqa: BLE001\n'
         '            pass\n'
         '\n'
         '\n'
         'def _connect(db):\n    con = sqlite3.connect(db, timeout=30)\n'),
        # (1) a SUMMARY1 sheet carries no item line: none is read from it (sale_lines raised on it and the file stayed at rest);
        #     an EMPTY day: lines 0, the title's day -- exactly as the door does since S480
        ('            nlines = 0\n'
         '            if typ == "SALE_BILLWISE" and verdict == "VERIFIED":\n'
         '                rows = sale_lines(local)\n'
         '                nlines = len(rows)\n'
         '                if not dry:\n'
         '                    con.execute("DELETE FROM mi_sale_line WHERE md5=?", (f["md5"],))\n',
         '            nlines = 0\n'
         '            empty_day = ""\n'
         '            # S482 (F-733), as the door (marg_take.take) does since S480: the short statement (SUMMARY1 -- BILL VALUE, no item lines)\n'
         '            # lands with no line read from it; a sale report with no bill is an EMPTY day -- lines 0, the title\'s day, the door\'s reason.\n'
         '            if typ == "SALE_BILLWISE" and verdict == "VERIFIED" and (res.get("variant", "") or "") != "SUMMARY1":\n'
         '                empty_day = _s482_empty_day(local)\n'
         '                rows = sale_lines(local)\n'
         '                nlines = len(rows)\n'
         '                if empty_day and not rows:\n'
         '                    res = dict(res, date_from=empty_day, date_to=empty_day)   # the title\'s day; mi_sale_line is not touched for this md5\n'
         '                elif not dry:\n'
         '                    con.execute("DELETE FROM mi_sale_line WHERE md5=?", (f["md5"],))\n'),
        # (2) the door's exact words, so the chain reads both
        ('                     res.get("date_to", "") or "", verdict, (res.get("reason", "") or "")[:300],\n',
         '                     res.get("date_to", "") or "", verdict,\n'
         '                     ("EMPTY \\u2014 no sale on %s" % empty_day) if (empty_day and not nlines) else (res.get("reason", "") or "")[:300],\n'),
        # (3) the chain, after a sale report is written
        ('                     os.path.basename(dest), kept, nlines, pct, pcv, agree, now_ist().isoformat()))\n'
         '                con.commit()\n',
         '                     os.path.basename(dest), kept, nlines, pct, pcv, agree, now_ist().isoformat()))\n'
         '                con.commit()\n'
         '                if typ == "SALE_BILLWISE" and verdict == "VERIFIED":   # S482 (D675 b): as take() does\n'
         '                    _s482_rebuild_chain(con)\n'),
    ])


# ---------------------------------------------------------------------------------------------- reports_tile.py (Part A.4: the gap lines)
def build_reports_tile(src):
    return edit("reports_tile.py", src, [
        ('    if banner:\n'
         '        line += " \u00b7 " + banner["text_en"]\n',
         '    if banner:\n'
         '        line += " \u00b7 " + banner["text_en"]\n'
         '    chain = _s482_chain(cx)                                    # S482 (D675 b): a pure read of mi_bill_chain -- never rebuilt here\n'
         '    for _g in (chain or {}).get("lines") or []:               # one English clause per open gap, only while a gap exists\n'
         '        line += " \u00b7 " + _g["text_en"]\n'),
        ('            "s454_scan": _s454_scan_line(cx)}                  # S454 P2 (7.3): apart from the report rows -- their counts stay right\n',
         '            "s454_scan": _s454_scan_line(cx),                  # S454 P2 (7.3): apart from the report rows -- their counts stay right\n'
         '            "bill_chain": chain}                               # S482 (D675 b): the chain\'s state and its lines (None: not readable)\n'),
        ('                 % (_esc(sl["text"]), _esc(sl["url"])))\n'
         '    if s["unknown_today"]:\n',
         '                 % (_esc(sl["text"]), _esc(sl["url"])))\n'
         '    cl = (s.get("bill_chain") or {}).get("lines") or []\n'
         '    if cl:                                                      # S482 (D675 b): one line per open gap in Marg\'s bill numbers; it leaves when a re-export closes the gap\n'
         '        body += "<div class=card id=s482chain>%s</div>" % "".join(\n'
         '            "<div class=line><span class=\'big bad\'>%s</span></div>" % _esc(g["text_hi"]) for g in cl)\n'
         '    if s["unknown_today"]:\n'),
        ('# ---- S454 part 2 end -----------------------------------------------------------------------------------------------------------------\n'
         '\n'
         '\n'
         'if __name__ == "__main__":\n',
         '# ---- S454 part 2 end -----------------------------------------------------------------------------------------------------------------\n'
         '\n'
         '\n'
         + block("tile_block_s482.py")
         + 'if __name__ == "__main__":\n'),
    ])


# ------------------------------------------------------------------------------------------------- spine/marg_read.py (Part C: F-732)
def build_marg_read(src):
    return edit("marg_read.py", src, [
        ('    days = []\n'
         '    day_sum = 0.0\n'
         '    for i, r in enumerate(rows):\n'
         '        r = pad(r, 9)\n'
         "        f = furniture(r, (r'BILL\\s+WISE\\s+SALES\\s+STATEMENT',))\n",
         '    days = []\n'
         '    day_sum = 0.0\n'
         '    title_day = ""                 # S482 (F-732): the day the title names (AS ON dd-mm-yyyy) -- an empty day prints no DATE row\n'
         '    empty = False                  # S482: the EMPTY footer was read\n'
         '    for i, r in enumerate(rows):\n'
         '        r = pad(r, 9)\n'
         "        f = furniture(r, (r'BILL\\s+WISE\\s+SALES\\s+STATEMENT',))\n"),
        ('        if f is None and c[0] == "BILL NO.":\n'
         '            f = "COLHDR"\n'
         '        if f:\n'
         '            R.cls(f)\n'
         '            continue\n'
         '        if RE_DATE.match(c[0]) and not any(c[1:]):\n'
         '            R.cls("DATE")\n'
         '            date = iso(c[0])\n'
         '            day_sum = 0.0\n'
         '            continue\n'
         '        if c[2].startswith("DAY TOTAL"):\n',
         '        if f is None and c[0] == "BILL NO.":\n'
         '            f = "COLHDR"\n'
         '        if f:\n'
         '            R.cls(f)\n'
         '            if f == "TITLE":\n'
         "                tm = re.search(r'AS\\s+ON\\s+(\\d{2}-\\d{2}-\\d{4})', \" \".join(c), re.I)\n"
         '                title_day = iso(tm.group(1)) if tm else title_day\n'
         '            continue\n'
         '        if RE_DATE.match(c[0]) and not any(c[1:]):\n'
         '            R.cls("DATE")\n'
         '            date = iso(c[0])\n'
         '            day_sum = 0.0\n'
         '            continue\n'
         "        if c[0].startswith(\"Total No. of\") and re.match(r'^Bills\\s*:\\s*0$', c[1]) and c[2].startswith(\"DAY TOTAL\"):\n"
         '            # S482 (F-732): the EMPTY footer -- "Total No. of | Bills: 0 | DAY TOTAL : | 0.0 ..." on ONE row is a day with no bill.\n'
         '            # It is recognised BEFORE the DAY TOTAL branch (which caught it and left the two footer witnesses unanswered). A DETAIL\n'
         '            # sheet\'s footer ("Total No. of | Bills: N | GRAND TOTAL :", with its DAY TOTAL on a row of its own) never comes here.\n'
         '            R.cls("EMPTY_FOOTER")\n'
         '            grand = num(c[3]) if num(c[3]) is not None else 0.0\n'
         '            nfoot = 0\n'
         '            empty = True\n'
         '            continue\n'
         '        if c[2].startswith("DAY TOTAL"):\n'),
        ('    ds = sorted({b["date"] for b in bills})\n'
         '    R.data = dict(date_from=ds[0] if ds else "", date_to=ds[-1] if ds else "", days=ds, bills=bills)\n'
         '    return R\n',
         '    ds = sorted({b["date"] for b in bills})\n'
         '    R.data = dict(date_from=ds[0] if ds else "", date_to=ds[-1] if ds else "", days=ds, bills=bills)\n'
         '    if empty and not bills:        # S482 (F-732): an EMPTY day -- no bill, and the day is the title\'s\n'
         '        R.check("an empty day is named by its title (AS ON)", bool(title_day), title_day)\n'
         '        R.data.update(empty=True, date_from=title_day, date_to=title_day, days=[title_day] if title_day else [])\n'
         '    return R\n'),
    ])


# -------------------------------------------------------------------------------------------------- manojz marg_gate.py (Part E: F-731)
def build_marg_gate(src):
    return edit("marg_gate.py", src, [
        ('def build_multipart(file_bytes, filename="REPORT_1.XLS", field="file"):\n',
         'def _s482_empty_sheet(row):\n'
         '    """S482 (F-731): a VERIFIED sale sheet of at most three rows -- its title, its heads and the one \'Bills: 0\' footer -- is an\n'
         '    EMPTY day: there is no bill in it for the sale-bill route, which answers 422 no_item_detail for ever. `rows` is a string in\n'
         '    index.csv; a blank or zero row count is UNKNOWN, never empty (a sheet with bill rows is never caught by this)."""\n'
         '    try:\n'
         '        return 1 <= int((row or {}).get("rows") or 0) <= 3\n'
         '    except (TypeError, ValueError):\n'
         '        return False\n'
         '\n'
         '\n'
         'def build_multipart(file_bytes, filename="REPORT_1.XLS", field="file"):\n'),
        # build_picture: an empty day is not "NOT SENT" (and is not copied into _UPLOAD_NOW every cycle)
        ('    sent_here = {m for m, v in state.get("sent", {}).items()\n'
         '                 if v.get("result") in ("accepted", "duplicate")}\n',
         '    sent_here = {m for m, v in state.get("sent", {}).items()\n'
         '                 if v.get("result") in ("accepted", "duplicate", "empty_day")}   # S482 (F-731)\n'),
        # do_send: the empty day is recorded and skipped, before anything else is decided about it
        ('    todo = []\n'
         '    for md5, name, path, row in candidates:\n'
         '        if not args.resend_all:\n'
         '            if md5 in sent and sent[md5].get("result") in ("accepted", "duplicate"):\n'
         '                continue\n',
         '    todo = []\n'
         '    for md5, name, path, row in candidates:\n'
         '        if _s482_empty_sheet(row):\n'
         '            # S482 (F-731): an EMPTY day is never sent -- not even by --resend-all: the sale-bill route cannot take it. A failure is\n'
         '            # never written to `sent`, so the test is on the index row. NOT counted by delivered_stamps: a later real DETAIL sheet\n'
         '            # of that date must still be sent.\n'
         '            if (sent.get(md5) or {}).get("result") != "empty_day":\n'
         '                sent[md5] = {"result": "empty_day", "http": None,\n'
         '                             "business_date": row.get("date_to"), "when": now_str(),\n'
         '                             "export_stamp": row.get("export_stamp") or "",\n'
         '                             "note": "an empty day \\u2014 nothing for the sale-bill route (F-731); the door already has it"}\n'
         '            print("  skipping %s (%s) -- an empty day: no bill to send; the server\'s door already has it"\n'
         '                  % (md5[:8], row.get("date_to")))\n'
         '            continue\n'
         '        if not args.resend_all:\n'
         '            if md5 in sent and sent[md5].get("result") in ("accepted", "duplicate", "empty_day"):\n'
         '                continue\n'),
        # nothing left to send: the note of an earlier failure is stale (it was removed only after a send that had something to send)
        ('    if not todo:\n'
         '        save_state(archive, state)\n'
         '        print("  everything in the outbox is already on the server. Nothing to send.")\n'
         '        return 0\n',
         '    if not todo:\n'
         '        save_state(archive, state)\n'
         '        _att = os.path.join(archive, ATTENTION_NAME)\n'
         '        if os.path.exists(_att) and not args.dry_run:      # S482 (F-731): nothing waits any more -- the last failure\'s note is stale\n'
         '            os.remove(_att)\n'
         '        print("  everything in the outbox is already on the server. Nothing to send.")\n'
         '        return 0\n'),
        ('    print("selftest: %d/%d" % (len(checks) - len(failed), len(checks)))\n',
         '    # ---- S482 (F-731): the empty day is told by its row count, and only by a KNOWN one\n'
         '    ck("S482: a verified sale sheet of three rows is an empty day", _s482_empty_sheet({"rows": "3"}))\n'
         '    ck("S482: a sheet with bill rows is never an empty day", not _s482_empty_sheet({"rows": "18"}))\n'
         '    ck("S482: an unknown row count is not an empty day",\n'
         '       not _s482_empty_sheet({"rows": ""}) and not _s482_empty_sheet({}) and not _s482_empty_sheet({"rows": "x"}))\n'
         '\n'
         '    print("selftest: %d/%d" % (len(checks) - len(failed), len(checks)))\n'),
    ])


BUILDERS = {
    "ingest/marg_take.py": build_marg_take,
    "ingest/marg_ingest.py": build_marg_ingest,
    "finance/reports_tile.py": build_reports_tile,
    "finance/spine/marg_read.py": build_marg_read,
    "manojz/marg_gate.py": build_marg_gate,
}


def put(out, name, text):
    p = os.path.join(out, *name.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    b = text.encode("utf-8")
    with io.open(p, "wb") as fh:
        fh.write(b)
    print("built %-28s %s -> %s  (%d bytes)" % (name, FROM[name][:8], md5(b)[:8], len(b)))
    return md5(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", action="store_true")
    ap.add_argument("--ingest", default="/root/marg_ingest")
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--manojz", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    todo = []
    if a.server:
        todo += [("ingest/marg_take.py", os.path.join(a.ingest, "marg_take.py")), ("ingest/marg_ingest.py", os.path.join(a.ingest, "marg_ingest.py")),
                 ("finance/reports_tile.py", os.path.join(a.finance, "reports_tile.py")),
                 ("finance/spine/marg_read.py", os.path.join(a.finance, "spine", "marg_read.py"))]
    if a.manojz:
        todo += [("manojz/marg_gate.py", os.path.join(a.manojz, "marg_gate.py"))]
    if not todo:
        raise SystemExit("!! nothing asked: --server and / or --manojz DIR")
    built = [(name, BUILDERS[name](pinned(name, rd(path)))) for name, path in todo]      # every pin and every anchor first ...
    for name, text in built:                                                               # ... then the writes
        put(a.out, name, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

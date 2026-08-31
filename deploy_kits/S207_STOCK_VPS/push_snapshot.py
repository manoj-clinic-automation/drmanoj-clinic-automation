#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""push_snapshot.py — send the newest Marg closing stock to the clinic server.

Runs on MANOJZ, where the archive and the token already are. This is the link
that makes the loop close by itself: without it, differences sit open forever
because nothing ever tells the server that Marg's numbers changed.

    python3 push_snapshot.py [--archive DIR] [--url URL] [--dry-run]

Exit 0 sent (or dry-run) · 1 a real failure · 2 nothing to send / unreachable.

THE TOKEN IS NEVER PASSED ON THE COMMAND LINE and never printed. It is read
the way marg_gate.py reads it -- off the medical share, falling back to the
local cache -- because a hand-copied token went stale once and answered 401
for five days (see REINSTALL_MANOJZ.md section 4).

WHAT IT SENDS
    Item, quantity, packing, pack size, and the last purchase rate in paise so
    a shortage can be priced. No patient data. No bill numbers. Nothing that
    is not already a stock figure.

F-235 GUARD
    A category-filtered export carries the SAME store name and as-on date as
    the full one and a byte-identical header. Sending the 81-row orthotics
    file as if it were the shop would silently zero 295 items. So the largest
    export for the newest date wins, and a smaller one for the same date is
    refused with a message that says why.
"""
import argparse, glob, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
for rel in ("../S206_SANJEEVNI_MARG_PURCHASE", "../S205_LIVE_TOOLS/manojz"):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, rel)))

DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
DEF_URL = "https://followup.dr-manoj.in/stock/api/snapshot"
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"
DEF_TOKEN_CACHE = r"D:\Downloads\margsync\SendToClinic\token.txt"
FILTERED_MAX = 200


# --- the S206 supersede rule (S212_SUPERSEDE, adopted S214) -----------------
# Two exports of one period are not two datasets; the later (or wider)
# replaces the earlier. Applied to FLOW reports only (sale / purchase):
# snapshot reports (STOCK_CLOSING, STOCK_EXPIRY) keep their own F-235
# largest-for-date pickers, where "latest stamp wins" would be the WRONG rule
# -- a later category-filtered export must not beat the whole-shop one.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "S212_SUPERSEDE")))
import marg_effective as _ME_sup


def _effective(paths):
    """Flow-report file list with superseded exports removed, loudly."""
    kept, superseded = _ME_sup.effective(sorted(paths))
    for _p, _by in superseded:
        print("  superseded export not counted: %s  (replaced by %s)"
              % (os.path.basename(_p), os.path.basename(_by)))
    return kept


def read_token(unc=DEF_TOKEN_UNC, cache=DEF_TOKEN_CACHE):
    """Live copy first, cache second. Never printed, never logged, never
    returned in an error message."""
    for p in (unc, cache):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                t = (fh.read() or "").strip()
            if t:
                return t, ("share" if p == unc else "cache")
        except OSError:
            continue
    return None, None


def as_on_key(s):
    """Marg writes dd-mm-yyyy. Comparing that as TEXT is wrong and it is wrong
    QUIETLY: "31-03-2026" > "27-08-2026" because "31" > "27", so the newest
    export the shop has is beaten by the year-opening one from five months
    earlier. Caught on the first dry run against the real archive, which picked
    31-Mar and would have posted 974 items of opening stock as if they were
    today's shelf. Returns (yyyy, mm, dd); an unreadable date sorts FIRST, so it
    can never win."""
    t = (s or "").strip().replace("/", "-")
    parts = t.split("-")
    if len(parts) == 3:
        try:
            d, m, y = (int(x) for x in parts)
            if y > 1900 and 1 <= m <= 12 and 1 <= d <= 31:
                return (y, m, d)
            # tolerate yyyy-mm-dd too, in case a later export changes shape
            y2, m2, d2 = (int(x) for x in parts)
            if y2 > 1900:
                return (y2, m2, d2)
        except ValueError:
            pass
    return (0, 0, 0)


def newest_full(archive):
    # Gather first, then choose, then report. Deciding and logging in the same
    # pass produced a line that called a MARCH export "a smaller export for the
    # same date" -- it was neither. A log line that is wrong is worse than none,
    # because the next person believes it.
    import marg_stock as MS
    cands = []
    for p in glob.glob(os.path.join(archive, "STOCK_CLOSING", "*", "*")):
        try:
            r = MS.read_closing(p)
        except Exception:
            continue
        if r.get("store") == "WHOLE STORES":
            cands.append((os.path.basename(p), r))
    if not cands:
        return None, []
    best_name, best = max(cands, key=lambda c: (as_on_key(c[1].get("as_on")),
                                                len(c[1]["rows"])))
    bk = as_on_key(best.get("as_on"))
    rejected = [(n, len(r["rows"])) for n, r in cands
                if n != best_name and as_on_key(r.get("as_on")) == bk]
    return best, rejected


def rates(archive):
    """Last purchase rate per item, in paise per unit."""
    import marg_purchase as MP
    out = {}
    for p in _effective(glob.glob(os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.XLS"))):
        try:
            rep = MP.read_purchase(p)
        except Exception:
            continue
        for r in rep["rows"]:
            nr = r.get("net_rate") or r.get("rate")
            if nr:
                try:
                    out[r["item"]] = int(round(float(nr) * 100))
                except (TypeError, ValueError):
                    pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="send the newest Marg stock to the server")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--url", default=DEF_URL)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.isdir(a.archive):
        print("ARCHIVE NOT REACHABLE -- %s" % a.archive)
        return 2
    full, rejected = newest_full(a.archive)
    if full is None:
        print("no WHOLE STORES closing export found")
        return 2
    for name, n in rejected:
        print("  skipped %s (%d rows vs %d) -- same as-on date, fewer items: "
              "a category filter, not the shop (F-235)"
              % (name, n, len(full["rows"])))
    if len(full["rows"]) < FILTERED_MAX:
        print("REFUSING: the largest export for %s has only %d rows. That is a "
              "filtered subset, not the shop. Nothing sent."
              % (full.get("as_on"), len(full["rows"])))
        return 2

    rt = rates(a.archive)
    items, seen = [], set()
    for row in full["rows"]:
        n = row["item"]
        if not n or n.upper() in ("DESCRIPTION", "TOTAL") or n in seen:
            continue
        seen.add(n)
        d = {"item": n, "qty": int(row["units"] or 0),
             "packing": row["packing"], "pack_size": int(row["pack_size"] or 1)}
        if n in rt:
            d["rate_p"] = rt[n]
        items.append(d)
    body = {"as_on": full.get("as_on"), "source": "push_snapshot", "items": items}
    print("as on %s : %d items, %d priced"
          % (body["as_on"], len(items), sum(1 for i in items if "rate_p" in i)))
    if a.dry_run:
        print("dry run -- nothing sent")
        return 0

    tok, where = read_token()
    if not tok:
        print("no token available (share or cache) -- nothing sent")
        return 2
    req = urllib.request.Request(
        a.url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Finance-Cron": tok})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("server said %s -- nothing recorded" % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("could not reach the server (%s) -- nothing recorded"
              % e.__class__.__name__)
        return 2
    print("sent (token from %s): %d items, %d difference(s) closed by themselves"
          % (where, out.get("items", 0), out.get("reconciled", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

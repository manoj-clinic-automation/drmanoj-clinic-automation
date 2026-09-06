#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""push_snapshot.py — send the newest Marg closing stock to the clinic server.

Runs on MANOJZ, where the archive and the token already are. This is the link
that makes the loop close by itself: without it, differences sit open forever
because nothing ever tells the server that Marg's numbers changed.

    python3 push_snapshot.py [--archive DIR] [--url URL] [--dry-run]

Exit 0 sent (or dry-run) · 1 a real failure · 2 nothing to send / unreachable.

S208 SECOND CORRECTION -- THE URL WAS OUTSIDE THE PROXY. /stock/... 404s from
the outside: the web server proxies only /finance to this app, so the request
never reached it. The ledger now lives at /finance/stock/... and needs no web
server change at all.

S208 CORRECTION -- THE HEADER WAS WRONG AND EVERY REAL RUN WOULD HAVE BEEN
REFUSED. token.txt holds the MARG token (marg_gate.py and pipeline_status.py
both send it as X-Finance-Marg). This script sent it as X-Finance-Cron, which
is a DIFFERENT secret, on a path the Marg token was not allowed to open. The
front gate refused it 401 before the route ran. --dry-run returns before the
network call, so no proof this kit carried could ever have caught it.

THE TOKEN IS NEVER PASSED ON THE COMMAND LINE and never printed. It is read
the way marg_gate.py reads it -- off the medical share, falling back to the
local cache -- because a hand-copied token went stale once and answered 401
for five days (see REINSTALL_MANOJZ.md section 4).

WHAT IT SENDS
    Item, quantity, packing, pack size, and the last purchase rate in paise so
    a shortage can be priced. No patient data. No bill numbers. Nothing that
    is not already a stock figure.

F-235 GUARD, AS CORRECTED BY F-322
    A category-filtered export carries the SAME store name and as-on date as
    the full one and a byte-identical header. Sending the 81-row orthotics
    file as if it were the shop would silently zero 295 items.

    The guard was written as "the largest export for the date wins". That is
    too strong, and on 06-Sep-2026 it cost the owner a morning: he merged a
    duplicate item in Marg -- exactly the cleanup he had been asked for -- and
    re-exported. The merged export is legitimately ONE ROW SMALLER, so the
    guard refused it and re-sent the pre-merge file. The page kept showing the
    gap he had just closed, and the marker said the new file had been pushed.

    The right test is the router's own, and it is now literally the same
    number: an export is a FILTERED SUBSET only when it is at or below 60% of
    the day's largest (marg_router.SUBSET_MAX_FRACTION), or below the absolute
    floor. Anything above that is a full store export, and among full exports
    THE LATEST CAPTURE WINS -- which is also the owner's standing rule for
    sale reports: the server keeps the newer export of a day.

    81 of 374 is 22%: still refused. 438 of 439 is 99.8%: accepted, and it
    supersedes.
"""
import argparse, glob, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
for rel in ("../S206_SANJEEVNI_MARG_PURCHASE", "../S205_LIVE_TOOLS/manojz"):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, rel)))

DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
DEF_URL = "https://followup.dr-manoj.in/finance/stock/api/snapshot"
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"
DEF_TOKEN_CACHE = r"D:\Downloads\margsync\SendToClinic\token.txt"
FILTERED_MAX = 200
# Kept identical to marg_router.SUBSET_MAX_FRACTION on purpose: one rule
# about what a subset is, written down in two places, must be one number.
SUBSET_MAX_FRACTION = 0.60


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

    # S221 LATEST WINS -- the capture stamp is in the filename, so use it. A
    # shelf counted after the last bill supersedes one counted at midday.
    def _taken(name):
        parts = str(name).split("__")
        return parts[2] if len(parts) > 2 else ""

    # F-322 (S226). Choose the DAY first, then separate the day's exports into
    # full ones and filtered subsets, then let the latest full one win. Row
    # count is a GUARD, never a tiebreaker: making it a tiebreaker is what made
    # a merge look like a filter.
    bk = max(as_on_key(r.get("as_on")) for _, r in cands)
    same = [(n, r) for n, r in cands if as_on_key(r.get("as_on")) == bk]
    biggest = max(len(r["rows"]) for _, r in same)
    full_ones, subsets = [], []
    for n, r in same:
        if len(r["rows"]) <= SUBSET_MAX_FRACTION * biggest:
            subsets.append((n, len(r["rows"])))
        else:
            full_ones.append((n, r))
    best_name, best = max(full_ones, key=lambda c: (_taken(c[0]), len(c[1]["rows"])))
    rejected = [(n, k, "subset") for n, k in subsets]
    rejected += [(n, len(r["rows"]), "older")
                 for n, r in full_ones if n != best_name]
    return best, rejected


def rates(archive):
    """Last purchase rate per item, in paise per unit."""
    import marg_purchase as MP
    out = {}
    for p in sorted(glob.glob(os.path.join(archive, "PURCHASE_ITEMWISE", "*", "*.XLS"))):
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


def verify(url):
    """Prove the join: does the server accept THIS machine's token on THIS path?

    This is the check whose absence made the first version of this script
    useless. It sends a deliberately EMPTY body, so the only thing it can
    prove is who the server thinks we are:

        400 bad_request  -> the token was accepted and the route ran. GREEN.
        401              -> the front gate refused us before the route ran.
        403              -> the route itself refused us.

    Nothing is written to the database in any of those cases.
    """
    tok, where = read_token()
    if not tok:
        print("no token available (share or cache) -- cannot verify")
        return 2
    req = urllib.request.Request(
        url, data=json.dumps({"as_on": "", "items": []}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Finance-Marg": tok})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("unexpected %s -- the server accepted an EMPTY snapshot. "
                  "Tell Claude; do not run the real push." % r.status)
            return 1
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:200]
        except Exception:                                      # noqa: BLE001
            pass
        if e.code == 400 and "bad_request" in body:
            print("GREEN -- the server accepted this machine's token "
                  "(from %s) and nothing was written." % where)
            return 0
        if e.code == 401:
            print("REFUSED AT THE FRONT GATE (401). The path is not open to "
                  "this token -- finance_app.py was not patched, or not "
                  "restarted. Nothing was written.")
            return 1
        if e.code == 403:
            print("REFUSED BY THE ROUTE (403). The gate let us in but the "
                  "handler did not accept the token -- stock_app.py is the "
                  "old one. Nothing was written.")
            return 1
        print("server said %s -- nothing was written." % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("could not reach the server (%s)" % e.__class__.__name__)
        return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description="send the newest Marg stock to the server")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--url", default=DEF_URL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="prove the server accepts this machine's token. "
                         "Sends an EMPTY body, so nothing is written.")
    a = ap.parse_args(argv)

    if a.verify:
        return verify(a.url)

    if not os.path.isdir(a.archive):
        print("ARCHIVE NOT REACHABLE -- %s" % a.archive)
        return 2
    full, rejected = newest_full(a.archive)
    if full is None:
        print("no WHOLE STORES closing export found")
        return 2
    for name, n, why in rejected:
        if why == "subset":
            print("  skipped %s (%d rows vs %d) -- same as-on date and at or "
                  "below %d%% of it: a category filter, not the shop (F-235)"
                  % (name, n, len(full["rows"]), int(SUBSET_MAX_FRACTION * 100)))
        else:
            print("  superseded %s (%d rows) -- a full export of the same day, "
                  "taken earlier than the one being sent (F-322)"
                  % (name, n))
    if len(full["rows"]) < FILTERED_MAX:
        print("REFUSING: the largest export for %s has only %d rows. That is a "
              "filtered subset, not the shop. Nothing sent."
              % (full.get("as_on"), len(full["rows"])))
        return 2

    rt = rates(a.archive)
    # F-322b (S226). Two rows with the SAME item name in one whole-store export
    # are one product held under two item masters in Marg. This used to keep the
    # first and DROP the rest in silence -- on 05-Sep that turned
    # LACTOVAX SYP (-2) + LACTOVAX SYP (7) into -2, and the drift page showed a
    # seven-unit gap that was never on the shelf. The stock of a product is the
    # sum of its masters, and a merge that happens here is said out loud.
    items, by_name, merged = [], {}, []
    for row in full["rows"]:
        n = row["item"]
        if not n or n.upper() in ("DESCRIPTION", "TOTAL"):
            continue
        q = int(row["units"] or 0)
        if n in by_name:
            by_name[n]["qty"] += q
            if n not in merged:
                merged.append(n)
            continue
        d = {"item": n, "qty": q,
             "packing": row["packing"], "pack_size": int(row["pack_size"] or 1)}
        if n in rt:
            d["rate_p"] = rt[n]
        by_name[n] = d
        items.append(d)
    for n in merged:
        print("  two item masters under one name, added together: %s = %d"
              % (n, by_name[n]["qty"]))
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
        headers={"Content-Type": "application/json", "X-Finance-Marg": tok})
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

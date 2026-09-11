#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""push_purchases.py -- send every archived Marg PURCHASE export to the server.

Runs on MANOJZ, from this kit folder, exactly like push_snapshot.py. The
contract it implements is S224_PURCHASE_PUSH_CONTRACT.md -- one export per
POST, money in paise, dates ISO -- and nothing here writes to Marg or leaves
the machine except that POST.

    python push_purchases.py --dry-run        table + one sample JSON, send nothing
    python push_purchases.py --verify         healthz, then prove the token (writes nothing)
    python push_purchases.py                  send every VERIFIED export not yet sent
    python push_purchases.py --all            re-send even the ones the ledger says went
    python push_purchases.py --vendors        POST the stockist name->number pairs
    python push_purchases.py --feed           POST the pull heartbeat (A3)

Exit 0 sent (or dry-run) · 1 a real failure · 2 nothing to send / unreachable.
A refusal prints REFUSING so the .bat can grep it (S221 rule: a refusal must
never read as Done).

WHAT COUNTS AS "SENT"
    The ledger D:\\Downloads\\margsync\\_analysis\\purchase_push_state.json holds
    {md5: {when, http, result}}. An md5 with http 200 is not sent again unless
    --all. A 400 or a network failure is recorded and retried next run. The
    server is idempotent on md5 anyway; the ledger only saves the bytes.

SUPERSEDE, APPLIED HERE AND ON THE SERVER
    Same type + same period_from/period_to: the later export_stamp wins. This
    script marks the older one "superseded locally by <stamp>" in the table
    but STILL SENDS IT, oldest stamp first, so the server holds the whole
    history and applies its own identical rule. Nothing is ever deleted.

THE TOKEN (copied from push_snapshot.py, S208 correction)
    token.txt holds the MARG token, sent as X-Finance-Marg -- never
    X-Finance-Cron (F-237). Read off the medical share first, the local cache
    second. Never on the command line, never printed, never in an error.

F-185
    The exports carry the shop's own phone and Marg's sales numbers in their
    header and footer. Those rows are furniture and never become JSON. The
    vendor pairs ARE numbers, by design: they go to the server only, and this
    script prints their COUNT and nothing else.
"""
import argparse
import csv
import datetime as dt
import glob
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
_p206 = os.path.join(KITS, "S206_SANJEEVNI_MARG_PURCHASE")
if _p206 not in sys.path:
    sys.path.insert(0, _p206)
import marg_purchase_rows as PR     # noqa: E402  the shared parser (both legs)
import marg_purchase as MP          # noqa: E402  ITEM WISE, the S206 reader

DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
DEF_ANALYSIS = r"D:\Downloads\margsync\_analysis"
DEF_PULL_FILE = r"D:\Downloads\margsync\MargPull\_last_pull.txt"
DEF_VENDORS_FILE = r"D:\Downloads\margsync\_config\stockist_phones.json"
DEF_BASE = "https://followup.dr-manoj.in/finance/purchase/api"
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"
DEF_TOKEN_CACHE = r"D:\Downloads\margsync\SendToClinic\token.txt"
LEDGER_NAME = "purchase_push_state.json"
SAMPLE_NAME = "purchase_push_sample.json"
TYPES = ("PURCHASE_ITEMWISE", "PURCHASE_BILLWISE",
         "PURCHASE_SUPPLIERWISE", "PURCHASE_BILLITEMWISE")
ASLEEP_AFTER_MIN = 35
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
STAMP_RE = re.compile(r"__(\d{8}-\d{6})__")


# ---------------------------------------------------------------- token
def read_token(unc=None, cache=None):
    """Live copy first, cache second. Never printed, never logged, never
    returned in an error message. The defaults are read at CALL time so a
    selftest can point them at a temp folder."""
    unc = unc or DEF_TOKEN_UNC
    cache = cache or DEF_TOKEN_CACHE
    for p in (unc, cache):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                t = (fh.read() or "").strip()
            if t:
                return t, ("share" if p == unc else "cache")
        except OSError:
            continue
    return None, None


def _post(url, body, tok, timeout=90):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "X-Finance-Marg": tok})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def _http_error_body(e):
    try:
        return e.read().decode("utf-8", "replace")[:300]
    except Exception:                                          # noqa: BLE001
        return ""


# --------------------------------------------------------------- verify
def verify(base):
    """GET healthz (no auth), then POST an EMPTY body with the token.

        400 malformed -> the token was accepted and the route ran. GREEN.
        401           -> the front gate refused us (path not open to this token).
        403           -> the route refused the token.
    Nothing is written in any of those cases."""
    rc = 0
    try:
        with urllib.request.urlopen(base + "/healthz", timeout=30) as r:
            hz = json.loads(r.read().decode("utf-8"))
        print("healthz: ok=%s exports=%s last_received=%s"
              % (hz.get("ok"), hz.get("exports"), hz.get("last_received")))
    except urllib.error.HTTPError as e:
        print("healthz answered %s -- the purchase app is not mounted at %s"
              % (e.code, base))
        rc = 1
    except Exception as e:                                     # noqa: BLE001
        print("could not reach the server for healthz (%s)" % e.__class__.__name__)
        return 2
    tok, where = read_token()
    if not tok:
        print("no token available (share or cache) -- cannot verify")
        return 2
    try:
        st, body = _post(base + "/push", {}, tok, timeout=30)
        print("unexpected %s -- the server accepted an EMPTY push. Tell Claude; "
              "do not run the real push." % st)
        return 1
    except urllib.error.HTTPError as e:
        body = _http_error_body(e)
        if e.code == 400 and "malformed" in body.lower():
            print("GREEN -- the server accepted this machine's token (from %s) "
                  "and nothing was written." % where)
            return rc
        if e.code == 401:
            print("REFUSED AT THE FRONT GATE (401). /finance/purchase is not open "
                  "to the Marg token -- finance_app.py not patched, or not "
                  "restarted. Nothing was written.")
            return 1
        if e.code == 403:
            print("REFUSED BY THE ROUTE (403). purchase_app.py did not accept "
                  "the token. Nothing was written.")
            return 1
        if e.code == 404:
            print("NOT MOUNTED (404) -- the purchase app is not installed on the "
                  "server yet. Nothing was written.")
            return 1
        print("server said %s -- nothing was written." % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("could not reach the server (%s)" % e.__class__.__name__)
        return 2


# --------------------------------------------------------------- ledger
def load_ledger(path):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:                                          # noqa: BLE001
        return {}


def save_ledger(path, ledger):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def now_ist():
    return dt.datetime.now(IST)


# -------------------------------------------------------------- archive
def _resolve(archive, row):
    """The archived file. index.csv once recorded a Linux session path for
    one row (the BILLITEMWISE rescue), so the path is rebuilt from the
    archive root when the recorded one does not exist here."""
    ap = row.get("archived_path") or ""
    name = os.path.basename(ap.replace("\\", "/"))
    cands = [ap, os.path.join(archive, row["type"], (row.get("date_from") or "")[:7], name)]
    for p in cands:
        if p and os.path.isfile(p):
            return p
    hits = glob.glob(os.path.join(archive, row["type"], "*", "*%s*" % row["md5"][:8]))
    return hits[0] if hits else None


def index_rows(archive):
    """VERIFIED purchase rows of index.csv, one per md5 (first seen wins)."""
    out, seen = [], set()
    with io.open(os.path.join(archive, "index.csv"), "r", encoding="utf-8-sig",
                 newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("type") not in TYPES or row.get("verdict") != "VERIFIED":
                continue
            if row["md5"] in seen:
                continue
            seen.add(row["md5"])
            out.append(row)
    return out


def plan(archive, ledger, resend_all=False):
    """Every export with its parsed body, the supersede mark, and the decision."""
    rows = index_rows(archive)
    items = []
    for row in rows:
        stamp = row.get("export_stamp") or ""
        p = _resolve(archive, row)
        it = {"type": row["type"].replace("PURCHASE_", ""), "md5": row["md5"],
              "stamp": stamp, "path": p, "file": os.path.basename(p) if p else "",
              "period_from": row.get("date_from"), "period_to": row.get("date_to"),
              "body": None, "error": None, "superseded_by": None}
        if p is None:
            it["error"] = "file not found under the archive"
        else:
            try:
                body = PR.payload(p, it["type"], read_purchase=MP.read_purchase)
                # index.csv is the archive's memory: its md5 and stamp win over
                # anything recomputed, and the two must agree or the file is
                # not the one the index describes.
                if body["md5"] != it["md5"]:
                    raise ValueError("md5 on disk %s != index %s" % (body["md5"][:8], it["md5"][:8]))
                body["export_stamp"] = stamp or body["export_stamp"]
                it["period_from"] = body["period_from"] or it["period_from"]
                it["period_to"] = body["period_to"] or it["period_to"]
                body["period_from"], body["period_to"] = it["period_from"], it["period_to"]
                it["body"] = body
            except Exception as e:                             # noqa: BLE001
                it["error"] = "%s: %s" % (e.__class__.__name__, str(e)[:120])
        items.append(it)
    # same type + same period -> later stamp wins (the server does the same)
    by_key = {}
    for it in items:
        by_key.setdefault((it["type"], it["period_from"], it["period_to"]), []).append(it)
    for group in by_key.values():
        best = max(group, key=lambda x: x["stamp"])
        for it in group:
            if it is not best:
                it["superseded_by"] = best["stamp"]
    items.sort(key=lambda x: (TYPES.index("PURCHASE_" + x["type"]),
                              x["period_from"] or "", x["stamp"]))
    for it in items:
        prev = ledger.get(it["md5"]) or {}
        if it["error"]:
            it["decision"] = "skip: " + it["error"]
        elif prev.get("http") == 200 and not resend_all:
            it["decision"] = "skip: sent %s (%s)" % (prev.get("when", "?")[:16],
                                                    prev.get("result", ""))
        else:
            it["decision"] = "send"
    return items


def sum_rows_p(typ, rows):
    """What the rows add up to, in paise -- shown against the grand total."""
    if typ in ("BILLWISE", "SUPPLIERWISE"):
        return sum((r.get("cash_p") or 0) + (r.get("credit_p") or 0) for r in rows)
    return sum(r.get("amount_p") or 0 for r in rows)


def rupees(p):
    if p is None:
        return "-"
    return "{:,.2f}".format(p / 100.0)


def print_table(items):
    print("%-13s %-10s %-10s %-15s %5s %14s  %s"
          % ("TYPE", "FROM", "TO", "STAMP", "ROWS", "GRAND Rs", "DECISION"))
    for it in items:
        n = it["body"]["n_rows"] if it["body"] else 0
        g = it["body"]["grand_amount_p"] if it["body"] else None
        mark = ("  [superseded locally by %s]" % it["superseded_by"]) if it["superseded_by"] else ""
        if it["body"] and g is not None and sum_rows_p(it["type"], it["body"]["rows"]) != g:
            mark += "  [rows sum %s: Marg's own item/TOTAL variance]" % rupees(
                sum_rows_p(it["type"], it["body"]["rows"]))
        print("%-13s %-10s %-10s %-15s %5d %14s  %s%s"
              % (it["type"], it["period_from"] or "?", it["period_to"] or "?",
                 it["stamp"], n, rupees(g), it["decision"], mark))


# --------------------------------------------------------------- vendors
def vendor_pairs(path=DEF_VENDORS_FILE):
    with io.open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    pairs = d.get("pairs") or {}
    return {str(k).strip(): str(v).strip() for k, v in pairs.items()
            if str(k).strip() and str(v).strip()}


def push_vendors(base, dry_run, path=DEF_VENDORS_FILE):
    try:
        pairs = vendor_pairs(path)
    except Exception as e:                                     # noqa: BLE001
        print("vendors: cannot read the pairs file (%s)" % e.__class__.__name__)
        return 2
    print("vendors: %d name->number pair(s) read" % len(pairs))
    if not pairs:
        print("vendors: nothing to send")
        return 2
    if dry_run:
        print("vendors: dry run -- nothing sent")
        return 0
    tok, where = read_token()
    if not tok:
        print("vendors: no token available (share or cache) -- nothing sent")
        return 2
    try:
        st, body = _post(base + "/vendors", {"pairs": pairs, "source": "stockist_phones.json",
                                              "host": "manojz"}, tok)
    except urllib.error.HTTPError as e:
        print("vendors: server said %s -- nothing recorded" % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("vendors: could not reach the server (%s) -- nothing recorded"
              % e.__class__.__name__)
        return 2
    print("vendors: sent %d pair(s) (token from %s), server %s" % (len(pairs), where, st))
    return 0


# ------------------------------------------------------------------ feed
def parse_last_pull(path=DEF_PULL_FILE):
    """The last END line of _last_pull.txt -> (aware IST datetime, note).
    'END 04-09-2026  6:40:21.70 -- ok'. START-only (a pull in progress) is not
    an END; the previous END still counts."""
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            lines = [l.strip() for l in fh if l.strip()]
    except OSError:
        return None, "no _last_pull.txt"
    ends = [l for l in lines if l.startswith("END")]
    if not ends:
        return None, "no END line"
    last = ends[-1]
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})", last)
    if not m:
        return None, "END line without a time"
    d, mo, y, hh, mm, ss = (int(x) for x in m.groups())
    when = dt.datetime(y, mo, d, hh, mm, ss, tzinfo=IST)
    note = last.split("--", 1)[1].strip() if "--" in last else ""
    return when, note


def feed_body(path=DEF_PULL_FILE, now=None, asleep_after=ASLEEP_AFTER_MIN):
    now = now or now_ist()
    when, note = parse_last_pull(path)
    if when is None:
        return {"pull_last": None, "pull_age_min": None, "state": "asleep",
                "host": "manojz"}
    age = int((now - when).total_seconds() // 60)
    return {"pull_last": when.isoformat(), "pull_age_min": age,
            "state": "asleep" if age > asleep_after else "ok", "host": "manojz"}


def push_feed(base, dry_run, path=DEF_PULL_FILE):
    body = feed_body(path)
    print("feed: pull_last=%s age=%s min state=%s"
          % (body["pull_last"], body["pull_age_min"], body["state"]))
    if dry_run:
        print("feed: dry run -- nothing sent")
        return 0
    tok, where = read_token()
    if not tok:
        print("feed: no token available (share or cache) -- nothing sent")
        return 2
    try:
        st, _ = _post(base + "/feed", body, tok, timeout=30)
    except urllib.error.HTTPError as e:
        print("feed: server said %s -- nothing recorded" % e.code)
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("feed: could not reach the server (%s) -- nothing recorded"
              % e.__class__.__name__)
        return 2
    print("feed: sent (token from %s), server %s" % (where, st))
    return 0


# ------------------------------------------------------------------ main
def run_push(a):
    if not os.path.isdir(a.archive):
        print("REFUSING: ARCHIVE NOT REACHABLE -- %s" % a.archive)
        return 2
    ledger_path = os.path.join(a.analysis, LEDGER_NAME)
    ledger = load_ledger(ledger_path)
    items = plan(a.archive, ledger, a.all)
    if not items:
        print("REFUSING: no VERIFIED purchase export in index.csv")
        return 2
    print_table(items)
    to_send = [it for it in items if it["decision"] == "send"]
    bad = [it for it in items if it["error"]]
    print("%d export(s), %d to send, %d unreadable" % (len(items), len(to_send), len(bad)))

    if a.dry_run:
        sample = (to_send or [it for it in items if it["body"]] or [None])[0]
        if sample is not None:
            if not os.path.isdir(a.analysis):
                os.makedirs(a.analysis)
            sp = os.path.join(a.analysis, SAMPLE_NAME)
            with io.open(sp, "w", encoding="utf-8") as fh:
                json.dump(sample["body"], fh, indent=1)
            print("sample JSON (%s %s..%s) written to %s"
                  % (sample["type"], sample["period_from"], sample["period_to"], sp))
        print("dry run -- nothing sent")
        return 0
    if not to_send:
        print("nothing to send -- every readable export is already on the server")
        return 0 if not bad else 1

    tok, where = read_token()
    if not tok:
        print("REFUSING: no token available (share or cache) -- nothing sent")
        return 2
    sent = failed = 0
    for it in to_send:
        entry = {"when": now_ist().isoformat(timespec="seconds"), "http": None,
                 "result": "", "type": it["type"], "file": it["file"]}
        try:
            st, body = _post(a.base + "/push", it["body"], tok)
            try:
                res = json.loads(body)
            except ValueError:
                res = {}
            entry["http"] = st
            entry["result"] = str(res.get("reason") or "ok")
            sent += 1
            print("sent  %-13s %s..%s %s rows -> %s %s"
                  % (it["type"], it["period_from"], it["period_to"],
                     it["body"]["n_rows"], st, entry["result"]))
        except urllib.error.HTTPError as e:
            entry["http"] = e.code
            entry["result"] = _http_error_body(e)[:120]
            failed += 1
            print("FAILED %-13s %s..%s -> server said %s"
                  % (it["type"], it["period_from"], it["period_to"], e.code))
            ledger[it["md5"]] = entry
            if e.code in (401, 403, 404):
                print("REFUSING to continue: %s means every push would fail the "
                      "same way. Run --verify." % e.code)
                save_ledger(ledger_path, ledger)
                return 1
        except Exception as e:                                 # noqa: BLE001
            entry["result"] = "unreachable: " + e.__class__.__name__
            failed += 1
            print("FAILED %-13s %s..%s -> could not reach the server (%s)"
                  % (it["type"], it["period_from"], it["period_to"],
                     e.__class__.__name__))
            ledger[it["md5"]] = entry
            save_ledger(ledger_path, ledger)
            return 2
        ledger[it["md5"]] = entry
        save_ledger(ledger_path, ledger)
    print("done (token from %s): %d sent, %d failed, %d unreadable"
          % (where, sent, failed, len(bad)))
    return 0 if not failed and not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="send archived Marg purchase exports to the server")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--analysis", default=DEF_ANALYSIS, help="ledger + sample folder")
    ap.add_argument("--base", default=DEF_BASE, help="the /finance/purchase/api base URL")
    ap.add_argument("--pull-file", default=DEF_PULL_FILE)
    ap.add_argument("--vendors-file", default=DEF_VENDORS_FILE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true", help="re-send exports the ledger says went")
    ap.add_argument("--verify", action="store_true",
                    help="healthz + prove the token with an EMPTY body; writes nothing")
    ap.add_argument("--vendors", action="store_true", help="POST the stockist pairs")
    ap.add_argument("--feed", action="store_true", help="POST the pull heartbeat")
    a = ap.parse_args(argv)
    a.base = a.base.rstrip("/")

    if a.verify:
        return verify(a.base)
    rcs = []
    if a.vendors:
        rcs.append(push_vendors(a.base, a.dry_run, a.vendors_file))
    if a.feed:
        rcs.append(push_feed(a.base, a.dry_run, a.pull_file))
    if a.vendors or a.feed:
        return max(rcs)
    return run_push(a)


if __name__ == "__main__":
    sys.exit(main())

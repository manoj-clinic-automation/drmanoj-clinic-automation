#!/usr/bin/env python3
"""att_source_summary.py -- kit S535_PUNCH_SOURCE_WATCH (session 305, 12-Oct-2026). READ-ONLY; it need not be run by hand.

Each night at 01:25 (cron, tagged S535_PUNCH_WATCH) it reads what the punch listener recorded about who sends it
requests (/root/attlistener_sources.jsonl, written by attlistener_v2.py since S535) beside punches.csv, and writes one
small summary: /root/finance/punch_sources_summary.json. The 01:35 code bundle carries /root/finance/*.json to Drive,
and the 03:10 nightly brings it to the owner's PC, so the assistant reads it there -- nobody runs anything.

What it answers, for step 2 of the punch-listener change (D713): is there ONE mark -- an address, or a header the
machine sends -- that is on EVERY genuine punch, with one value, every day? And did every row punches.csv gained since
the watch began arrive with a recorded source line (the watch missed nothing)? It changes no file but its own output.
The listener's own test calls from this box (127.0.0.1 / ::1) are counted apart and never judged.
S957 (26-Nov-2026): a punches.csv row whose time the listener corrected (S792: the server's time stored, the machine's in the last
column) is matched on the machine's time too. A punch the door refused (S957, the line's "door" is "refused") is counted apart and
never judged as the machine's. Since S957 the door's mark is the key to the punch door, and this file travels with the nightly
bundle: a header's VALUE (outside the generic ones) is written only as its length, and every address only as its first two parts,
unless ATT_SUMMARY_KEEP=1 (the S957 installer, into its own 0700 scratch, never to OUT's default path).
"""
import json, os, sys
from collections import Counter, defaultdict
from datetime import datetime

SOURCE_LOG = os.environ.get("ATT_SOURCE_LOG", "/root/attlistener_sources.jsonl")
PUNCH_CSV = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
OUT = os.environ.get("ATT_SOURCE_SUMMARY", "/root/finance/punch_sources_summary.json")
LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")
# headers every HTTP sender carries, constant or not -- never a mark of WHICH machine sent it
GENERIC = ("host", "request_code", "accept", "accept-encoding", "content-type", "connection", "transfer-encoding",
           "expect", "user-agent")


def read_lines(path):
    rows, bad = [], 0
    if not os.path.exists(path):
        return rows, bad
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad


def read_punch_rows(path, since):
    """punches.csv rows whose received_at is at or after `since` -> [(user_id, datetime)]"""
    out = []
    if not since or not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split(",")
            if len(p) >= 5 and p[0] != "user_id" and p[4] >= since:
                out.append((p[0], p[1], p[5] if len(p) >= 6 else ""))     # S957: + the machine's time (S792)
    return out


def summarise(rows, bad, punch_rows):
    outside = [r for r in rows if r.get("ip") not in LOOPBACK]
    punches = [r for r in outside if r.get("punch") and r.get("door") != "refused"]          # S957
    refused = [r for r in outside if r.get("punch") and r.get("door") == "refused"]
    since = rows[0].get("t") if rows else None
    until = rows[-1].get("t") if rows else None
    days = sorted({(r.get("t") or "")[:10] for r in punches})

    by_ip = defaultdict(lambda: {"punch": 0, "other": 0, "first": None, "last": None})
    for r in outside:
        d = by_ip[r.get("ip", "")]
        d["punch" if r.get("punch") else "other"] += 1
        d["first"] = d["first"] or r.get("t")
        d["last"] = r.get("t")

    names = Counter()
    vals = defaultdict(Counter)
    for r in punches:
        for k, v in (r.get("headers") or {}).items():
            names[k.lower()] += 1
            vals[k.lower()][v] += 1
    headers = {}
    one_mark = []
    for k in sorted(names):
        distinct = len(vals[k])
        headers[k] = {"on_punches": names[k], "distinct_values": distinct,
                      "commonest": [[v, n] for v, n in vals[k].most_common(3)]}
        if punches and names[k] == len(punches) and distinct == 1 and k not in GENERIC:
            one_mark.append(k)
    ips_on_punches = sorted({r.get("ip") for r in punches})

    seen = {(str(r.get("user_id")), r.get("datetime")) for r in punches}
    missing = [x[:2] for x in punch_rows if x[:2] not in seen and not (len(x) > 2 and x[2] and (x[0], x[2]) in seen)]   # S957

    if not punches:
        verdict = "NO PUNCH YET -- nothing to judge."
    elif missing:
        verdict = ("WATCH INCOMPLETE -- %d punches.csv rows since the watch began have no source line; "
                   "do not build step 2 on this." % len(missing))
    elif one_mark:
        verdict = ("ONE MARK on every punch (%d punches, %d days): header %s, one value throughout%s."
                   % (len(punches), len(days), ", ".join(one_mark),
                      "; the address too" if len(ips_on_punches) == 1 else
                      "; the address changed %d times -- the address alone would NOT be safe" % (len(ips_on_punches) - 1)))
    elif len(ips_on_punches) == 1:
        verdict = ("ADDRESS ONLY -- every punch came from one address (%d punches, %d days) but no header was one "
                   "value throughout; an address can change with the internet line." % (len(punches), len(days)))
    else:
        verdict = "NO SINGLE MARK -- neither one header value nor one address covers every punch; step 2 is not safe."

    if os.environ.get("ATT_SUMMARY_KEEP") != "1":                       # S957: never the mark, never a full address
        def _mask_ip(a):
            a = str(a or "")
            return ".".join(a.split(".")[:2] + ["x", "x"]) if a.count(".") == 3 else (a.split(":")[0] + ":x" if ":" in a else a)
        for k, h in headers.items():
            if k not in GENERIC:
                h["commonest"] = [["<%d chars>" % len(str(v)), n] for v, n in h["commonest"]]
        merged = {}
        for a, d0 in by_ip.items():
            m_ = merged.setdefault(_mask_ip(a), {"punch": 0, "other": 0, "first": None, "last": None})
            m_["punch"] += d0["punch"]
            m_["other"] += d0["other"]
            m_["first"] = min(x for x in (m_["first"], d0["first"]) if x) if (m_["first"] or d0["first"]) else None
            m_["last"] = max(x for x in (m_["last"], d0["last"]) if x) if (m_["last"] or d0["last"]) else None
        by_ip = merged
        ips_shown = sorted({_mask_ip(a) for a in ips_on_punches})
    else:
        ips_shown = ips_on_punches
    return {
        "kit": "S535_PUNCH_SOURCE_WATCH", "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_log": SOURCE_LOG, "since": since, "until": until, "days_with_punches": days,
        "lines": len(rows), "unreadable_lines": bad,
        "loopback_lines": len(rows) - len(outside), "punch_lines": len(punches),
        "by_address": dict(by_ip), "addresses_on_punches": ips_shown, "addresses_on_punches_count": len(ips_on_punches),
        "headers_on_punches": headers, "one_mark_headers": one_mark,
        "punches_csv_rows_since": len(punch_rows), "punches_csv_rows_without_source_line": len(missing),
        "missing_examples": [list(x) for x in missing[:5]],
        "refused_by_door": len(refused), "fixed_by": "S957",
        "verdict": verdict,
    }


def main():
    rows, bad = read_lines(SOURCE_LOG)
    since = rows[0].get("t") if rows else None
    s = summarise(rows, bad, read_punch_rows(PUNCH_CSV, since))
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1, sort_keys=True)
    os.replace(tmp, OUT)
    print("%s  %s" % (s["built"], s["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

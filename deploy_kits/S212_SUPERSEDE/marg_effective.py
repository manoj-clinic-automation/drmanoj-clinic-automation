#!/usr/bin/env python3
"""
marg_effective.py -- which archived exports actually count.

THE PROBLEM, specified by the owner at S206 Phase 0 and not built until now:

    "Amir's month-to-date export, always from the 1st -- plus the SUPERSEDE
     RULE in the router. Two exports of one month are not two datasets; the
     later replaces the earlier. Without that rule the archive double-counts
     silently."

`marg_router.py` skips a file only when its CONTENT MD5 has been seen before.
That is the right test for the same file arriving twice. It is the wrong test
for two DIFFERENT exports covering overlapping periods: different bytes, both
kept, both equally valid-looking. Anything that then sums "every file of this
type" counts the overlap twice.

Today the sale archive already carries three such pairs (18-Aug twice, 24-Aug
twice, and a 23_to_24 range spanning both). The purchase archive is clean --
but the moment Amir exports month-to-date on every visit, as planned, every
export contains the previous one and the double-count becomes the normal case.

WHY THIS IS A READER, NOT A ROUTER CHANGE
    The router is live on manojz and its index is the pipeline's memory. A
    read-side rule needs no live file touched, fixes the archive that already
    exists rather than only files that arrive later, and cannot corrupt
    index.csv. If it is later moved into the router, the rule does not change.

NOTHING IS EVER DELETED OR MOVED. A superseded file stays exactly where it is;
it is simply not counted twice.
"""
import os
import re
import glob

RANGE = re.compile(r"__(\d{4}-\d{2}-\d{2})(?:_to_(\d{4}-\d{2}-\d{2}))?__")
STAMP = re.compile(r"__(\d{8}-\d{6})__")


def span(name):
    """('2026-08-01','2026-08-26') from a canonical archive filename, or None.

    A single-date name is a one-day span, which is what makes a day file and a
    range file directly comparable.
    """
    m = RANGE.search(name or "")
    if not m:
        return None
    a = m.group(1)
    return (a, m.group(2) or a)


def stamp(name):
    """The export stamp, which breaks ties between two exports of one period."""
    m = STAMP.search(name or "")
    return m.group(1) if m else ""


def covers(outer, inner):
    """True when `outer` spans everything `inner` does."""
    return outer[0] <= inner[0] and outer[1] >= inner[1]


def rank(name):
    """Bigger is better: a wider span first, then the later export stamp."""
    s = span(name)
    return ((s[1] > s[0]) if s else False, stamp(name))


def effective(paths):
    """-> (kept, superseded). Both lists, because a dropped file must be nameable.

    A file is superseded when ANOTHER file of the same type covers its whole
    span and outranks it. Equal spans are broken by the export stamp, so a
    re-export of the same day replaces the earlier one rather than adding to it.
    """
    named = [(p, span(os.path.basename(p))) for p in paths]
    usable = [(p, s) for p, s in named if s]
    kept, superseded = [], []
    for p, s in usable:
        beaten_by = None
        for q, t in usable:
            if q == p:
                continue
            if covers(t, s) and (t != s or True):
                if s == t:
                    if rank(os.path.basename(q)) > rank(os.path.basename(p)):
                        beaten_by = q
                        break
                elif covers(t, s) and not covers(s, t):
                    beaten_by = q
                    break
        if beaten_by:
            superseded.append((p, beaten_by))
        else:
            kept.append(p)
    # a file with no readable span is never silently dropped
    kept.extend(p for p, s in named if not s)
    return sorted(kept), sorted(superseded)


def effective_for(archive, report_type):
    """The files of one report type that should be counted."""
    pats = [os.path.join(archive, report_type, "*", "*.XLS"),
            os.path.join(archive, report_type, "*", "*.xlsx"),
            os.path.join(archive, report_type, "*", "*.xls")]
    paths = sorted({p for pat in pats for p in glob.glob(pat)})
    return effective(paths)

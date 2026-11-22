#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""regress_s928.py -- kit S928_STOCK_ONE_RULE. The live-shape proof (the S837 rule): the figures of record on COPIES of the live
databases, old files against new, every difference explained by S928 itself or the install stops.
    python3 -B regress_s928.py dump <dir with the files> <COPY of finance.db> <COPY of spine.db> <out.json>
    python3 -B regress_s928.py compare <old.json> <new.json>
dump: {name: {marg, taps, shelf, arrived, evening}} over the newest capture's names + the count's, plus 'short': the items short_supplies
names (new files only; [] on the old). compare: a difference in marg/taps/shelf/arrived is EXPLAINED when the new dump names the item among
its short supplies (the bill over the tap), marks its base an evening count, or a delivery scanned earlier on the day of a spot count
(no longer added to that count); any other difference FAILS. No patient data is read or
printed (stock tables only; names are medicines)."""
import json
import os
import re
import sqlite3
import sys


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def dump(fin, dbp, spp, out):
    os.environ.update(FINANCE_DB=dbp, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1")
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    assert SW.__file__.startswith(fin) and SF.__file__.startswith(fin)
    if os.environ.get("ASSETS_DB"):                            # a scratch scan store (the synth's); on the box the module's own path
        import purchase_app as PA                              # noqa: E402
        PA._assets_db = os.environ["ASSETS_DB"]
    con = sqlite3.connect(dbp, timeout=60)
    sp = SW.Spine(spp)
    res = dict(kit=getattr(SF, "KIT", "?"), ready=bool(SF.ready(sp)), items={}, short=[])
    if res["ready"]:
        ctx = SF.Ctx(con, sp)
        cap = SF.capture_at(sp, None, ctx)
        names = sorted({str(r["name"]) for r in sp.q("SELECT DISTINCT name FROM sp_close_name WHERE md5=?", cap["md5"]) if r["name"]} | set(SF.count_family(con, ctx))) if cap else []
        for n in names:
            F = SF.figures(con, sp, [n], None, ctx)[n]
            M, S = F["marg"], F["shelf"]
            res["items"][n] = dict(marg=(round(float(M["figure"]), 2) if M else None), taps=(round(float(M.get("taps") or 0), 2) if M else None),
                                   shelf=(S.get("shelf") if S else None), arrived=(round(float(S.get("arrived") or 0), 2) if S else None),
                                   evening=bool((S or {}).get("base_evening")), named=(S or {}).get("named"), base_kind=(S or {}).get("base_kind"))
        if hasattr(SF, "short_supplies"):
            try:
                res["short"] = sorted({str(x["item"]) for x in SF.short_supplies(con, sp, ctx)})
            except Exception as e:                            # noqa: BLE001
                res["short_error"] = str(e)[:200]
    with open(out, "w") as fh:
        json.dump(res, fh)
    say("dump: %s items, ready %s, short %d (%s)" % (len(res["items"]), res["ready"], len(res["short"]), res["kit"]))


def compare(oldp, newp):
    O, N = json.load(open(oldp)), json.load(open(newp))
    if not (O.get("ready") and N.get("ready")):
        say("RESULT: NOT READY (old %s, new %s)" % (O.get("ready"), N.get("ready")))
        sys.exit(2)
    short = set(N.get("short") or [])
    names = sorted(set(O["items"]) | set(N["items"]))
    diff, unexplained = [], []
    for n in names:
        o, w = O["items"].get(n), N["items"].get(n)
        if o is None or w is None:
            unexplained.append((n, "only in %s" % ("old" if w is None else "new")))
            continue
        same = all(o.get(k) == w.get(k) for k in ("marg", "taps", "shelf", "arrived"))
        if same:
            continue
        why = []
        if n in short:
            why.append("the bill over the tap")
        if w.get("evening") and w.get("base_kind") != "count":
            why.append("an evening spot count")
        if (w.get("base_kind") in ("spot", "darpan") and o.get("arrived") is not None and w.get("arrived") is not None
                and float(w["arrived"]) < float(o["arrived"]) and o.get("marg") == w.get("marg")):
            why.append("a delivery inside the count")     # A5b: a spot base counts scan arrivals from its moment, not its day
        line = "%s: marg %s->%s taps %s->%s shelf %s->%s arrived %s->%s" % (n, o.get("marg"), w.get("marg"), o.get("taps"), w.get("taps"), o.get("shelf"), w.get("shelf"), o.get("arrived"), w.get("arrived"))
        if why:
            diff.append(line + "  [" + ", ".join(why) + "]")
        else:
            unexplained.append((n, line))
    say("INFO %d items compared; %d differ, every one explained by S928; %d unexplained" % (len(names), len(diff), len(unexplained)))
    da = sum((N["items"][n].get("arrived") or 0) - (O["items"][n].get("arrived") or 0) for n in names if n in O["items"] and n in N["items"] and n in short)
    ds = sum((N["items"][n].get("shelf") or 0) - (O["items"][n].get("shelf") or 0) for n in names if n in O["items"] and n in N["items"] and N["items"][n].get("evening") and N["items"][n].get("base_kind") != "count" and N["items"][n].get("shelf") is not None and O["items"][n].get("shelf") is not None)
    say("INFO the bill over the tap moves the arrivals by %+.0f units over %d items; the evening rule moves the shelf by %+.0f units" % (da, len([n for n in short if n in N["items"]]), ds))
    for d in diff[:60]:
        say("  explained  " + d)
    for n, d in unexplained[:60]:
        say("  RED  " + d)
    say("RESULT: %s" % ("ALL PASS" if not unexplained else "%d FAIL" % len(unexplained)))
    sys.exit(0 if not unexplained else 1)


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4]), os.path.abspath(sys.argv[5]))
    else:
        compare(sys.argv[2], sys.argv[3])

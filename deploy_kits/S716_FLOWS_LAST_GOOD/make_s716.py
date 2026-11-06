#!/usr/bin/env python3
"""make_s716.py -- S716_FLOWS_LAST_GOOD (S388, Sanjeevni, 06-Nov-2026): two small changes to S714's Marg report flows.
    python3 -B make_s716.py <dir holding reports_tile.py and marg_flows.py> <out dir>
  1  the in-app Marg reports list shows each report's newest GOOD file, and a refused one that came after it underneath (S714's live read:
     the sale line said "refused 05-11 14:46" although that day's report had come in and been taken)
  2  every report line on "Aaj ki reports" that is not the morning pair (which has "Kaise banayein") carries "Steps dekhiye" to its own
     flow page -- F-1110's server half (the plain cause of a refusal is the medical PC's to say; its kit is the owner's word)
"""
import hashlib
import os
import sys

FROM = {"reports_tile.py": "cb0d5e0c323dca7d01bd0d8380ef7308", "marg_flows.py": "7af3f3ec2b68f6ab80a962733c13bc4f"}

RT = [
    ('''def _s714_last(cx, types):
    """The newest file the door filed under one of these mi_file types: dict(at, verdict, reason_hi) or None.  Reads only."""
    if not types or not _table_exists(cx, "mi_file"):
        return None
    r = cx.execute("SELECT received_at, verdict, reason FROM mi_file WHERE type IN (%s) ORDER BY replace(received_at,'T',' ') DESC LIMIT 1"
                   % ",".join("?" * len(types)), tuple(types)).fetchone()
    if not r:
        return None
    v = str(r[1] or "")
    return dict(at=str(r[0] or ""), verdict=v, reason_hi=("" if v == "VERIFIED" else hindi_reason(r[2], v)))''',
     '''def _s714_last(cx, types):
    """S716: the newest GOOD file the door filed under one of these mi_file types -- dict(at, verdict='VERIFIED', reason_hi='', later=None
    | dict(at, reason_hi) for a refused file that came after it) -- else the newest refused one, else None.  Reads only."""
    if not types or not _table_exists(cx, "mi_file"):
        return None
    q = ("SELECT received_at, verdict, reason FROM mi_file WHERE type IN (%s)%s ORDER BY replace(received_at,'T',' ') DESC LIMIT 1"
         % (",".join("?" * len(types)), "%s"))
    good = cx.execute(q % " AND verdict='VERIFIED'", tuple(types)).fetchone()
    last = cx.execute(q % "", tuple(types)).fetchone()
    if not last:
        return None
    if good is None:
        v = str(last[1] or "")
        return dict(at=str(last[0] or ""), verdict=v, reason_hi=hindi_reason(last[2], v), later=None)
    later = None
    if str(last[1] or "") != "VERIFIED" and str(last[0] or "").replace("T", " ") > str(good[0] or "").replace("T", " "):
        later = dict(at=str(last[0] or ""), reason_hi=hindi_reason(last[2], str(last[1] or "")))
    return dict(at=str(good[0] or ""), verdict="VERIFIED", reason_hi="", later=later)'''),
    ('''    elif r.get("owed_days") is not None:                        # S444: owed, red, with its days
        state = "<span class='state bad'>&#9675; %d din se baaki</span>" % int(r["owed_days"])
    else:
        state = "<span class='state due'>&#9675; baaki</span>"
    return ("<div class=line><span class=big>%s</span> <span class=small>%s</span>%s</div>"
            % (_esc(r["label"]), _esc(r.get("hint", "")), state))''',
     '''    elif r.get("owed_days") is not None:                        # S444: owed, red, with its days
        state = "<span class='state bad'>&#9675; %d din se baaki</span>" % int(r["owed_days"])
    else:
        state = "<span class='state due'>&#9675; baaki</span>"
    fid = _s716_flow_of(r.get("key"))                           # S716 (F-1110, server half): this report's own steps
    steps = (" <a class=small href='/finance/flows/%s'>Steps dekhiye &rsaquo;</a>" % _esc(fid)) if fid else ""
    return ("<div class=line><span class=big>%s</span> <span class=small>%s</span>%s%s</div>"
            % (_esc(r["label"]), _esc(r.get("hint", "")), state, steps))


def _s716_flow_of(typ):
    """S716: the flow page of a report's mi_file type (marg_flows.TYPES, read backwards), or ''."""
    try:
        import marg_flows as MF                                 # noqa: PLC0415
        return next((fid for fid, ts in MF.TYPES.items() if typ in ts), "")
    except Exception:                                           # noqa: BLE001 -- a row never fails for a link
        return ""'''),
]

MF = [
    ('''        elif r.get("verdict") == "VERIFIED":
            st = '<span class="st ok">&#10003; %s %s</span>' % ("Last report received" if en else "Pichhli report aa gayi", _e(ddmm(r.get("at"))))''',
     '''        elif r.get("verdict") == "VERIFIED":
            st = '<span class="st ok">&#10003; %s %s</span>' % ("Last report received" if en else "Pichhli report aa gayi", _e(ddmm(r.get("at"))))
            lt = r.get("later")                                  # S716: a refused file after the last good one, said underneath
            if lt:
                st += '<span class="st bad" style="font-weight:600">%s %s</span>' % (
                    "A later file was refused" if en else "Uske baad ek file manzoor nahi hui", _e(ddmm(lt.get("at"))))'''),
    ('''KIT = "S714_MARG_FLOWS"''', '''KIT = "S714_MARG_FLOWS"                                       # S716: the in-app list shows the last GOOD file first'''),
]

EDITS = {"reports_tile.py": RT, "marg_flows.py": MF}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    sd, od = sys.argv[1], sys.argv[2]
    os.makedirs(od, exist_ok=True)
    for name in ("reports_tile.py", "marg_flows.py"):
        raw = open(os.path.join(sd, name), "rb").read()
        if md5(raw) != FROM[name]:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
        src = raw.decode("utf-8")
        for i, (a, b) in enumerate(EDITS[name], 1):
            n = src.count(a)
            if n != 1:
                sys.exit("REFUSED: %s edit %d matches %d times" % (name, i, n))
            src = src.replace(a, b)
        out = src.encode("utf-8")
        open(os.path.join(od, name), "wb").write(out)
        print("%s  %s -> %s" % (name, FROM[name][:8], md5(out)))


if __name__ == "__main__":
    main()

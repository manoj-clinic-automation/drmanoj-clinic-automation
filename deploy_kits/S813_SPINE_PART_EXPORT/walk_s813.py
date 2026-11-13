#!/usr/bin/env python3
"""walk_s813.py -- S813_SPINE_PART_EXPORT.  Made-up reports only (no Marg file, no patient).
    python3 walk_s813.py <spine_build.py to test>     -> 'WALK GREEN n/n' (exit 0) or 'WALK RED ...' (exit 1)
The control: run it on the LIVE spine_build.py -- it must be RED (the live file has no part rule)."""
import importlib.util
import sys


def load(path):
    spec = importlib.util.spec_from_file_location("sb_walk", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rep(md5, a, b, n, key="bills"):
    return {"md5": md5, "name": md5 + ".XLS", "_accepted": True, "data": {"date_from": a, "date_to": b, key: [{}] * n}}


def authority(B, reports, key="bills"):
    """The authority loop exactly as spine_build runs it (latest stamp wins, unless a part list)."""
    exports = {r["md5"]: r for r in reports}
    auth = {}
    for r in reports:
        if hasattr(B, "part_list") and B.part_list(r, auth, exports, key):
            continue
        for d in B.dates(r["data"]["date_from"], r["data"]["date_to"]):
            auth[d] = r["md5"]
    return auth


def main(path):
    B = load(path)
    res = []

    def chk(name, ok):
        res.append((name, bool(ok)))

    N1, N11, N13, N30 = "2026-11-01", "2026-11-11", "2026-11-13", "2026-11-30"
    # 1 the 11-Nov case: 29 bills, then 4 of the same period -> the 29 stay the authority
    a = authority(B, [rep("full29", N1, N11, 29), rep("part4", N1, N11, 4)])
    chk("11-Nov: the 4-bill list does not retire the 29-bill list", a.get(N1) == "full29" and a.get(N11) == "full29")
    # 2 a later, fuller list takes over
    a = authority(B, [rep("old25", N1, N11, 25), rep("new29", N1, N11, 29)])
    chk("a later, fuller list takes over", a.get(N1) == "new29")
    # 3 a later list of the same size takes over (the ordinary day)
    a = authority(B, [rep("old29", N1, N11, 29), rep("new29b", N1, N11, 29)])
    chk("a later list of the same size takes over", a.get(N5 := "2026-11-05") == "new29b")
    # 4 half or more is not a part list (15 of 29)
    a = authority(B, [rep("old29", N1, N11, 29), rep("new15", N1, N11, 15)])
    chk("15 of 29 (half or more) takes over", a.get(N1) == "new15")
    # 5 under half and more than two short is a part list (14 of 29)
    a = authority(B, [rep("old29", N1, N11, 29), rep("new14", N1, N11, 14)])
    chk("14 of 29 is a part list", a.get(N1) == "old29")
    # 6 the 'more than two short' edge
    a = authority(B, [rep("old5", N1, N11, 5), rep("new3", N1, N11, 3)])
    chk("3 of 5 (two short) takes over", a.get(N1) == "new3")
    a = authority(B, [rep("old5", N1, N11, 5), rep("new2", N1, N11, 2)])
    chk("2 of 5 (three short, under half) is a part list", a.get(N1) == "old5")
    a = authority(B, [rep("old2", N1, N11, 2), rep("new0", N1, N11, 0)])
    chk("0 of 2 (two short) takes over", a.get(N1) == "new0")
    # 7 an older report of a WIDER period does not judge a shorter one
    a = authority(B, [rep("month", N1, N30, 40), rep("week", N1, "2026-11-07", 3)])
    chk("a month's list does not make a week's list a part list", a.get(N1) == "week" and a.get(N13) == "month")
    # 8 a later list of a WIDER period with few rows is judged against the older one inside it
    a = authority(B, [rep("old29", N1, N11, 29), rep("wide3", N1, N13, 3)])
    chk("1-13 Nov with 3 rows does not retire 1-11 Nov with 29", a.get(N1) == "old29" and a.get(N11) == "old29")
    # 9 no older authority -> taken as it is
    a = authority(B, [rep("alone", N1, N11, 1)])
    chk("a first list is taken as it is", a.get(N1) == "alone")
    # 10 the item lines use the same rule
    a = authority(B, [rep("lines71", N1, N11, 71, "lines"), rep("lines5", N1, N11, 5, "lines")], "lines")
    chk("item lines: 5 lines after 71 is a part list", a.get(N1) == "lines71")
    # 11 the part list names the fuller report it was a part of
    r1, r2 = rep("full29", N1, N11, 29), rep("part4", N1, N11, 4)
    authority(B, [r1, r2])
    chk("the part list names the fuller report", r2.get("_part") == "full29.XLS" and "_part" not in r1)
    # 12 a report that failed its own witness cannot make a later one a part list (the cold review's should-fix)
    bad29 = rep("bad29", N1, N11, 29)
    bad29["_accepted"] = False
    a = authority(B, [bad29, rep("new4", N1, N11, 4)])
    chk("a rejected older report does not make a later one a part list", a.get(N1) == "new4")
    # 13 the version says so
    chk("BUILD_VERSION is S813.1", getattr(B, "BUILD_VERSION", "") == "S813.1")
    bad = [n for n, ok in res if not ok]
    if bad:
        print("WALK RED %d/%d -- %s" % (len(res) - len(bad), len(res), "; ".join(bad)))
        return 1
    print("WALK GREEN %d/%d" % (len(res), len(res)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

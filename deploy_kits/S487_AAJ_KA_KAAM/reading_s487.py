#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reading_s487.py -- S487_AAJ_KA_KAAM: the REAL box read once, said in a few lines (the installer's eyes).

  build <dir holding owner_console.py> <finance dir> <finance.db> <out.json>
        makes a reading exactly as the service's builder does (finance.db copied through a read-only door; the app's own
        modules loaded from the finance dir without a cache file; nothing live written) and writes it to <out.json>
  show  <reading.json>
        says an existing reading
  mounted <finance dir> <finance.db>
        THE POSITIVE PROOF THAT THE LIST IS MOUNTED: loads the finance app from <finance dir> exactly as the console's builder
        does (the database copied through a read-only door, FINANCE_DB pointed at the copy BEFORE the app is loaded, no cache
        file written) and asks the app itself: are the list's five doors among its routes, and did every part mount?
        Last line: MOUNT OK ... or MOUNT RED <why>. (The login gate answers before routing, so a door behind it proves nothing.)
  lists <dir holding aaj_kaam.py and aaj_duties.json> <finance.db>
        every person's list from the list engine, through its own read-only door, as COUNTS ONLY: open and late per login,
        what the floor hides, any line that cannot be read. A line of the kit's own duties file that cannot be read is RED
        (the kit's own lines must read on this box); a line of the duty map that cannot be read is said, as the console says it.
        Last line: LISTS OK ... or LISTS RED <why>.
Printed: one line of the seven sections' chips; one line per piece that could not be read, with its reason (the page shows
those in grey, in plain words -- the reason is for the assistant). No amount is printed. Last line: READING OK unread=<n>
or READING RED <why>.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
WANT = ["needs", "money", "work", "att", "sanj", "papers", "system"]


def say(snap):
    if not isinstance(snap, dict) or not snap.get("ok"):
        print("READING RED the reading is not a reading")
        return 1
    if snap.get("order") != WANT or any(k not in (snap.get("sections") or {}) for k in WANT):
        print("READING RED the seven sections are not all there: %s" % snap.get("order"))
        return 1
    if snap.get("failed"):
        why = "; ".join("%s (%s)" % (k, snap["sections"][k].get("why", "?")) for k in snap["failed"])
        print("READING RED a whole section could not be made: %s" % why[:400])
        return 1
    ls = snap.get("lists") or {}
    if ls.get("engine") is not True:
        print("READING RED the staff's lines were not cut from the list engine: %s" % str(ls.get("err") or ls)[:300])
        return 1
    g = snap.get("guard") or {}

    if g.get("env_is_copy") is not True or g.get("app_db_is_copy") is False:
        print("READING RED the app's modules were not pointed at the copy: %s" % g)
        return 1
    chips = []
    for k in WANT:
        s = snap["sections"][k]
        chips.append("%s %s" % (s.get("name"), str(s.get("chip") or "")))
    print("   the reading (%s, %s s): %s" % (snap.get("as_of"), snap.get("took_s"), " | ".join(chips))[:600])
    if float(snap.get("took_s") or 0) > 60:
        print("READING RED it took %s s; a reading is stopped at 120 s" % snap.get("took_s"))
        return 1
    unread = [l for k in WANT for l in snap["sections"][k].get("lines") or [] if l.get("why") and "could not be" in (l.get("text") or "")]
    for l in unread:
        print("   not read: %s [%s]" % (str(l.get("text"))[:90], str(l.get("why"))[:200]))
    print("READING OK unread=%d" % len(unread))
    return 0


def mounted(fin, db):
    import shutil                                                      # noqa: PLC0415
    import sqlite3                                                     # noqa: PLC0415
    import tempfile                                                    # noqa: PLC0415
    tmp = tempfile.mkdtemp(prefix="s487_mount_")
    try:
        copy = os.path.join(tmp, "finance.db")
        src = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=10)
        dst = sqlite3.connect(copy)
        src.backup(dst)
        dst.close()
        src.close()
        os.environ["FINANCE_DB"] = copy                                # BEFORE any module of the app is loaded
        sys.path.insert(0, fin)
        os.chdir(fin)
        import finance_app as fa                                       # noqa: PLC0415
        if getattr(fa, "DB_PATH", copy) != copy:
            print("MOUNT RED the app was not pointed at the copy (%s)" % getattr(fa, "DB_PATH", None))
            return 1
        rules = {r.rule for r in fa.app.url_map.iter_rules()}
        need = ["/finance/aaj", "/finance/aaj/api/list", "/finance/aaj/api/line", "/finance/aaj/api/tick", "/finance/aaj/api/switch"]
        missing = [u for u in need if u not in rules]
        failed = [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]
        ident = [u for u in need if u not in getattr(fa, "IDENTITY_ONLY_PATHS", ())]
        if missing or failed or ident:
            print("MOUNT RED doors not among the app's routes: %s · parts that did not mount: %s · doors not in the signed-in-only list: %s"
                  % (missing or "none", failed or "none", ident or "none"))
            return 1
        print("MOUNT OK the list's five doors are among the app's %d routes; every part mounted" % len(rules))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def lists(d, db):
    os.environ.setdefault("AAJ_DUTIES_JSON", os.path.join(d, "aaj_duties.json"))
    sys.path.insert(0, d)
    import time                                                        # noqa: PLC0415
    import aaj_kaam as ak                                              # noqa: PLC0415
    t0 = time.time()
    ak.build_all(db, with_raw=False)                                   # as a staff door builds it
    took = time.time() - t0
    allp = ak.build_all(db)
    if allp.get("map_err") or allp.get("extra_err"):
        print("LISTS RED %s" % str(allp.get("map_err") or allp.get("extra_err"))[:300])
        return 1
    items = allp["items"]
    own = [i for i in items if i["kind"] == "sql" and i["err"] and not i["from_map"]]
    if own:
        print("LISTS RED a line of the kit's own duties file cannot be read on this box: %s" % "; ".join("%s [%s]" % (i["id"], i["err"]) for i in own)[:400])
        return 1
    logins = []
    for i in items:
        for p in [i["person"]] + list(i.get("also") or []):
            if p != "manoj" and p not in logins:
                logins.append(p)
    for p in allp["works"]:
        if p not in logins:
            logins.append(p)
    said, seen = [], {}
    for p in logins:
        lst = ak.list_for(allp, p)
        key = tuple(sorted(i["id"] for k in lst["sections"] for i in lst["sections"][k]))
        if not lst["has"]:
            continue
        if key in seen:                                                # two logins, one list (the desk's two people)
            said[seen[key]][0] += " / " + lst["name"]
            continue
        seen[key] = len(said)
        said.append([lst["name"], "%d open, %d late" % (lst["open"], lst["late"])])
    v = allp.get("views") or {}
    print("   the lists, nothing before %s%s: %s" % (ak.dm(allp["floor"]), "".join("; %s from %s" % (t, ak.dm(x)) for t, x in sorted(v.items()) if x != allp["floor"]),
                                                    " | ".join("%s %s" % (a, b) for a, b in said))[:900])
    hid = sum(max(0, (i.get("n_all") or 0) - i["n"]) for i in items if i["kind"] == "sql" and not i["err"])
    print("   the floor hides %d older item(s) the plain count would show; %s" % (hid, "the lists are ON for staff" if allp["on"] else "the lists are OFF for staff"))
    unread = [i for i in items if i["kind"] == "sql" and i["err"]]
    for i in unread:
        print("   not read: %s [%s]" % (i["id"], str(i["err"])[:160]))
    for i in items:
        if i["kind"] == "sql" and not i["err"] and i.get("behind"):
            print("   reaches behind the floor, so it is listed without a count or a day: %s (oldest %s)" % (i["id"], ak.dm(i["since"])))
    print("   a list is built in %.2f s (a staff page asks for one every two minutes)" % took)
    if took > 3.0:
        print("LISTS RED a list takes %.1f s to build on this box; the staff's pages would weigh on the service" % took)
        return 1
    print("LISTS OK people=%d lines=%d unread=%d" % (len(said), len(items), len(unread)))
    return 0


def main(argv):
    if len(argv) == 4 and argv[1] == "mounted":
        try:
            return mounted(argv[2], argv[3])
        except BaseException as e:                                     # noqa: BLE001
            print("MOUNT RED %s: %s" % (type(e).__name__, str(e)[:300]))
            return 1
    if len(argv) == 3 and argv[1] == "show":
        try:
            with open(argv[2], encoding="utf-8") as fh:
                return say(json.load(fh))
        except Exception as e:                                         # noqa: BLE001
            print("READING RED %s: %s" % (type(e).__name__, str(e)[:200]))
            return 1
    if len(argv) == 4 and argv[1] == "lists":
        try:
            return lists(argv[2], argv[3])
        except BaseException as e:                                     # noqa: BLE001
            print("LISTS RED %s: %s" % (type(e).__name__, str(e)[:300]))
            return 1
    if len(argv) == 6 and argv[1] == "build":
        kit, fin, db, out = argv[2:6]
        os.environ.setdefault("AAJ_DUTIES_JSON", os.path.join(kit, "aaj_duties.json"))
        os.environ.setdefault("CONSOLE_FRESHNESS", os.path.join(fin, "freshness.json"))
        os.environ.setdefault("CONSOLE_BEAT", os.path.join(fin, "reception_heartbeat.json"))
        try:
            sys.path.insert(0, kit)
            import owner_console as oc                                 # noqa: PLC0415
            oc.FIN = fin                                               # the app's modules are the box's own, read where they live
            os.chdir(fin)
            return say(oc.build(db, out))
        except BaseException as e:                                     # noqa: BLE001
            print("READING RED %s: %s" % (type(e).__name__, str(e)[:300]))
            return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

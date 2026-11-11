#!/usr/bin/python3
# walk_s785.py -- kit S785_XRAY_DOORS. Usage: walk_s785.py <dir holding portal/portal.py and finance/owner_console.py> <root> [--control]
# <root> is where the rest of the app lives (/root). Nothing is written anywhere; check_screens is a stand-in (no database touched).
import json, os, sys, types
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CONTROL = "--control" in sys.argv
NEW, ROOT = ARGS[0], ARGS[1]
N = [0]
fails = []
def check(name, ok):
    N[0] += 1
    if not ok:
        fails.append(name)
    print(("PASS " if ok else "FAIL ") + name)
sys.path[:0] = [os.path.join(NEW, "portal"), os.path.join(NEW, "finance"), os.path.join(ROOT, "portal"), os.path.join(ROOT, "finance")]
try:
    import portal as P
    t = [x for x in P.TILES if x["name"] == "X-ray photos"]
    names = [x["name"] for x in P.TILES]
    check("portal: the 'X-ray photos' tile exists", len(t) == 1)
    check("portal: it opens his X-ray page", bool(t) and t[0]["url"] == "/finance/records/xray-check")
    check("portal: the doctors only", bool(t) and t[0]["roles"] == ["doctor"])
    check("portal: in the Patients group, after Patient records", bool(t) and t[0].get("group") == "Patients"
          and names.index("X-ray photos") == names.index("Patient records") + 1)
    g = json.load(open(os.path.join(ROOT, "portal", "tile_grants.json")))
    bh = ((g.get("users") or {}).get("bhawna") or {}).get("only")
    check("portal: Dr Bhawna's 'only' list keeps it off her home", bh is None or "X-ray photos" not in bh)
except Exception as ex:                                  # noqa: BLE001
    print("portal stopped: %s %s" % (type(ex).__name__, str(ex)[:120]))
    for _ in range(5):
        check("portal (did not import)", False)
fake = types.ModuleType("check_screens")
fake.STAFF_DAYS = 7
STATE = {"all": 9, "recent": 6, "boom": False}
def _parked(con, recent=False):
    if STATE["boom"]:
        raise RuntimeError("made-up failure")
    return [object()] * (STATE["recent"] if recent else STATE["all"])
fake._parked = _parked
sys.modules["check_screens"] = fake
try:
    import owner_console as O
    ln = O._s785_xray_line(None)
    check("console: 3 photos older than 7 days -> a Needs-you line", bool(ln) and ln["text"].startswith("3 X") and "waiting more than 7 days" in ln["text"]
          and ln.get("href") == "/finance/records/xray-check" and ln.get("link") == "X-ray photos")
    STATE.update(all=6, recent=6)
    check("console: none older -> no line", O._s785_xray_line(None) is None)
    STATE.update(boom=True)
    check("console: a failure never breaks the section", O._s785_xray_line(None) is None)
    STATE.update(boom=False, all=8, recent=6)
    sec = O.sec_needs(None, {"aaj": {"items": [], "floor": "2026-10-01"}, "tile": {}})
    check("console: Needs you opens with the line and counts it", sec["open"] is True and sec["chip"] == "1"
          and any(x["text"].startswith("2 X") and "more than 7 days" in x["text"] for x in sec["lines"]))
    STATE.update(all=5, recent=5)
    sec = O.sec_needs(None, {"aaj": {"items": [], "floor": "2026-10-01"}, "tile": {}})
    check("console: nothing older -> 'Nothing is waiting for you' as before", sec["open"] is False
          and sec["lines"][0]["text"].startswith("Nothing is waiting"))
except Exception as ex:                                  # noqa: BLE001
    print("console stopped: %s %s" % (type(ex).__name__, str(ex)[:120]))
    for _ in range(5):
        check("console (did not run)", False)
bad = len(fails)
if CONTROL:
    print("CONTROL: red (%d of %d fail on this file)" % (bad, N[0]) if bad else "CONTROL: NOT red")
    sys.exit(0 if bad else 1)
print("WALK OK %d/%d" % (N[0], N[0]) if not bad else "WALK RED %d of %d" % (N[0] - bad, N[0]))
sys.exit(1 if bad else 0)

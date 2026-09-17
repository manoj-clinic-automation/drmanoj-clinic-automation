#!/usr/bin/env python3
"""walk_s302.py -- on the box, BEFORE anything is placed. A scratch copy of /root/marg_ingest with the new
three files: the router's own selftest is green; every export this box has kept is read by the OLD router
and the NEW one and judged identically (the new reading only ever applies to a print-layout report, which
is never kept here); the new signature is never uploadable and its type is in PHI_TYPES. Prints no cell content.
    python3 -B walk_s302.py <old marg_ingest dir> <new scratch dir>     -> last line WALK OK ... / WALK RED ..."""
import sys, os, subprocess, importlib.util
OLD, NEW = sys.argv[1], sys.argv[2]
def load(d, name, mod="marg_router"):
    sys.path.insert(0, d)
    try:
        spec = importlib.util.spec_from_file_location(name, os.path.join(d, mod + ".py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    finally:
        sys.path.remove(d)
    return m
try:
    r = subprocess.run([sys.executable, "-B", os.path.join(NEW, "marg_router.py"), "--selftest"], cwd=NEW, capture_output=True, text=True, timeout=120)
    assert "SELFTEST OK" in r.stdout, "the router selftest is not green: %s" % (r.stdout + r.stderr)[-300:]
    Ro, Rn = load(OLD, "r_old"), load(NEW, "r_new")
    So, Sn = Ro.load_signatures(os.path.join(OLD, "signatures.json")), Rn.load_signatures(os.path.join(NEW, "signatures.json"))
    new = [s for s in Sn if s["type"] == "SALE_DAILY_PRINT"]
    assert len(new) == 1 and new[0].get("uploadable") is False, "the new signature is missing or uploadable"
    assert len(Sn) == len(So) + 1, "the signature registry changed by more than one block"
    def judge(R, S, p):
        try:
            sh = R.open_sheet(p)
        except Exception:                                     # noqa: BLE001
            return ("UNREADABLE",)
        t, h, hr, c0 = R.read_preamble(sh)
        sig, st, _ = R.identify(t, h, S)
        a, b, c, d = R.dates_from(t, sh, hr, c0)
        return (st, (sig or {}).get("type", ""), (sig or {}).get("variant", ""), a, b)
    files = []
    for root, _d, fs in os.walk(os.path.join(OLD, "archive")):
        files += [os.path.join(root, f) for f in fs if f.lower().endswith((".xls", ".xlsx"))]
    changed, unread = 0, 0
    for p in files:
        a, b = judge(Ro, So, p), judge(Rn, Sn, p)
        unread += a == ("UNREADABLE",)
        changed += a != b
    assert changed == 0, "%d kept export(s) are judged differently by the new router" % changed
    MI = load(NEW, "mi_new", "marg_ingest")
    assert "SALE_DAILY_PRINT" in MI.PHI_TYPES, "SALE_DAILY_PRINT is not in PHI_TYPES"
    print("WALK OK router selftest green; %d kept exports judged identically (%d unreadable by both); the new type is never uploadable and is PHI here" % (len(files), unread))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)

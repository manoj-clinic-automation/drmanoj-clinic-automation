#!/usr/bin/python3
# walk_s792.py -- kit S792_PUNCH_CLOCK (S430, 11-Nov-2026, the parent). Usage: walk_s792.py <dir holding attlistener_v2.py,
# owner_console.py, fix_punch_clock.py> [--control]. Everything on made-up files in a scratch folder: a listener on a spare port,
# synthetic punch files, a stand-in att_core. Never the live punches.csv. Last line "WALK OK n/n" | "WALK RED k of n" | "CONTROL: ...".
import datetime as D, importlib, json, os, shutil, socket, subprocess, sys, tempfile, time, types, urllib.request
K = os.path.abspath(sys.argv[1]); CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s792w."); RES = []
F = "%Y-%m-%d %H:%M:%S"


def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))


def port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


PORT = port(); CSV = os.path.join(T, "punches.csv")
open(CSV, "w").write("user_id,datetime,io_mode,verify_mode,received_at\n5,2026-11-10 09:00:00,0,1,2026-11-10 09:00:01\n")
ENV = dict(os.environ, ATT_LISTENER_PORT=str(PORT), ATT_PUNCH_CSV=CSV, ATT_LISTENER_LOG=os.path.join(T, "l.log"),
           ATT_SOURCE_LOG=os.path.join(T, "s.jsonl"), ATT_ONLINE_WINDOW_S="4", ATT_ONLINE_GAP_S="1.5", ATT_COUNT_LOOPBACK="1")


def start():
    p = subprocess.Popen([sys.executable, "-B", os.path.join(K, "attlistener_v2.py")], env=ENV, cwd=T,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", PORT), 0.2).close(); return p
        except OSError:
            time.sleep(0.1)
    return p


def call(body=None, rc="receive_cmd"):
    data = b"" if body is None else (len(body).to_bytes(4, "little") + body + b"\x00")
    rq = urllib.request.Request("http://127.0.0.1:%d/iclock" % PORT, data=data or None, method="POST" if data else "GET",
                                headers={"request_code": rc})
    with urllib.request.urlopen(rq, timeout=5) as r:
        return r.headers.get("response_code")


def punch(uid, machine):
    return call(json.dumps({"user_id": uid, "io_time": machine.strftime("%Y%m%d%H%M%S"), "io_mode": 0, "verify_mode": 1}).encode(),
                "realtime_glog")


def rows():
    import csv
    return list(csv.reader(open(CSV, encoding="utf-8")))[1:]


def poll(sec):
    t0 = time.time()
    while time.time() - t0 < sec:
        call(); time.sleep(0.4)


try:
    lp = start()
    behind = D.datetime.now() - D.timedelta(hours=3)
    a0 = punch(901, behind)                              # not yet steadily online: the machine's time stands
    poll(4.6)
    a1 = punch(902, behind)                              # online for the window: the server's time
    a2 = punch(902, behind)                              # the machine re-sends it
    a3 = punch(903, D.datetime.now())                    # a right clock: kept
    time.sleep(2.2)                                      # silence longer than the gap: an outage
    a4 = punch(904, behind)                              # sent after the outage: the machine's time stands
    R = {r[0]: r for r in rows()}
    now = D.datetime.now()
    ck("L1 every punch acknowledged OK, a call without a punch ERROR_NO_CMD", [a0, a1, a2, a3, a4] == ["OK"] * 5 and call() == "ERROR_NO_CMD")
    ck("L2 before the machine has been steadily online: its time is stored (and kept in machine_time)",
       "901" in R and R["901"][1] == behind.strftime(F) and len(R["901"]) == 6 and R["901"][5] == behind.strftime(F))
    ck("L3 steadily online and 3 h off: the SERVER's time is stored, the machine's in machine_time",
       "902" in R and abs((D.datetime.strptime(R["902"][1], F) - now).total_seconds()) < 30 and R["902"][5] == behind.strftime(F)
       and R["902"][1] == R["902"][4])
    ck("L4 the machine re-sending it adds no row", sum(1 for r in rows() if r[0] == "902") == 1)
    ck("L5 a right clock is left as it is", "903" in R and R["903"][1] == R["903"][5])
    ck("L6 after a silence (an outage) a late punch keeps the machine's time", "904" in R and R["904"][1] == behind.strftime(F))
    lp.terminate(); lp.wait(5)
    lp = start()
    a5 = punch(902, behind)
    ck("L7 after a restart, the corrected punch re-sent is still known (no second row)", a5 == "OK" and sum(1 for r in rows() if r[0] == "902") == 1)
    ck("L8 the old row (no machine_time) is untouched", rows()[0] == ["5", "2026-11-10 09:00:00", "0", "1", "2026-11-10 09:00:01"])
    log = open(os.path.join(T, "l.log"), encoding="utf-8").read()
    ck("L9 the listener's log says when it stored the server's time", "CLOCK  user 902" in log)
    lp.terminate(); lp.wait(5)
except Exception as e:  # noqa: BLE001
    ck("L the listener", False, repr(e)[:160])
    try:
        lp.terminate()
    except Exception:  # noqa: BLE001
        pass

# ---- the one-off correction on a made-up file shaped like 11-Nov
FX = os.path.join(T, "fx.csv")
base = ["user_id,datetime,io_mode,verify_mode,received_at",
        "21,2026-11-10 09:30:00,0,1,2026-11-10 09:30:02",            # yesterday, normal
        "7,2026-11-10 08:00:00,0,1,2026-11-10 12:00:00",             # yesterday, late -- another day: untouched
        "21,2026-11-11 06:28:48,0,1,2026-11-11 08:08:01",
        "8,2026-11-11 06:49:38,0,1,2026-11-11 09:00:15",
        "18,2026-11-11 06:55:31,0,1,2026-11-11 09:31:38",
        "12,2026-11-11 06:57:15,0,1,2026-11-11 09:54:37",
        "30,2026-11-11 07:10:00,0,1,2026-11-11 09:58:00",            # a burst of three: a backlog -- untouched
        "31,2026-11-11 07:20:00,0,1,2026-11-11 09:58:10",
        "32,2026-11-11 07:30:00,0,1,2026-11-11 09:58:20",
        "101,2026-11-11 10:09:32,0,1,2026-11-11 10:22:17",
        "40,2026-11-11 10:40:00,0,1,2026-11-11 10:40:01"]           # right clock: untouched
open(FX, "w", newline="").write("\n".join(base) + "\n")
try:
    o1 = subprocess.run([sys.executable, "-B", os.path.join(K, "fix_punch_clock.py"), FX, "2026-11-11"], capture_output=True, text=True).stdout
    same = open(FX).read() == "\n".join(base) + "\n"
    o2 = subprocess.run([sys.executable, "-B", os.path.join(K, "fix_punch_clock.py"), FX, "2026-11-11", "--apply"], capture_output=True, text=True).stdout
    L = open(FX).read().split("\n")
    got = {ln.split(",")[0]: ln.split(",") for ln in L[1:] if ln}
    ck("F1 without --apply nothing is written; it names 5 rows", same and "corrected: 5" in o1, o1.strip())
    ck("F2 applied: the five that arrived alone get the server's time, the machine's kept",
       "APPLIED" in o2 and got["21"][1] == "2026-11-11 08:08:01" and got["8"][1] == "2026-11-11 09:00:15" and got["18"][1] == "2026-11-11 09:31:38"
       and got["12"][1] == "2026-11-11 09:54:37" and got["101"][1] == "2026-11-11 10:22:17" and got["18"][5] == "2026-11-11 06:55:31")
    ck("F3 the burst (a backlog), the right clock and the other days are byte-identical; the header gains machine_time",
       all(b in L for b in base[1:3] + base[7:10] + base[11:]) and L[0] == base[0] + ",machine_time")
    o3 = subprocess.run([sys.executable, "-B", os.path.join(K, "fix_punch_clock.py"), FX, "2026-11-11", "--apply"], capture_output=True, text=True).stdout
    ck("F4 a second run changes nothing", "corrected: 0" in o3 and open(FX).read().split("\n") == L)
except Exception as e:  # noqa: BLE001
    ck("F the correction", False, repr(e)[:160])

# ---- his console's line (a stand-in att_core pointing at the corrected made-up file)
try:
    sys.path.insert(0, K)
    for p in [x for x in os.environ.get("S792_LIBS", "").split(os.pathsep) if x]:
        sys.path.append(p)
    fake = types.ModuleType("att_core"); fake.cfg = types.SimpleNamespace(PUNCH_CSV=FX); sys.modules["att_core"] = fake
    OC = importlib.import_module("owner_console")
    ln = OC._s792_clock_line("2026-11-11")
    ln2 = OC._s792_clock_line("2026-11-10")
    ck("C1 his console: an amber line on the day -- how far off and how many punches carry the server's time",
       ln is not None and ln.get("dot") == "w" and "2 h 57 min" in ln["text"] and "5 punches" in ln["text"], ln)
    ck("C2 nothing on a day with no correction", ln2 is None)
except Exception as e:  # noqa: BLE001
    ck("C his console", False, repr(e)[:160])
shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))

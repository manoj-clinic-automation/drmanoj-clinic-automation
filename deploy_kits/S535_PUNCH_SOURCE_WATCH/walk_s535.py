#!/usr/bin/env python3
"""walk_s535.py -- kit S535's live-shape walk. Starts the FROM listener and the TO listener side by side on two spare
local ports, each with its own throw-away files, sends both the same requests in the device's own shape, and requires:
  W1 every reply identical (status, response_code header, empty body) -- the device can see no difference;
  W2 punches.csv identical apart from the received_at column -- nothing stored differently;
  W3 the TO side's source log has one line per punch (re-sends too) with address, user, time and headers;
  W4 a header named like a key or password is masked in the source log;
  W5 other requests are capped at 30 per sender per day;
  W6 NEGATIVE CONTROL: with the source log unwritable the TO side still answers exactly as the FROM side;
  W7 the summary reads the log, finds the one mark (dev_id), and finds no punch missing a source line;
  W8 NEGATIVE CONTROL: a punches.csv row with no source line is reported as WATCH INCOMPLETE.
  python3 walk_s535.py <FROM attlistener_v2.py> <TO attlistener_v2.py> <att_source_summary.py> [python]"""
import http.client, json, os, shutil, socket, struct, subprocess, sys, tempfile, time

FROM_PY, TO_PY, SUM_PY = sys.argv[1:4]
PY = sys.argv[4] if len(sys.argv) > 4 else sys.executable
FAIL = []


def check(ok, what):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok:
        FAIL.append(what)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def start(py, d, source_log=None):
    port = free_port()
    env = dict(os.environ, ATT_LISTENER_PORT=str(port), ATT_PUNCH_CSV=os.path.join(d, "punches.csv"),
               ATT_LISTENER_LOG=os.path.join(d, "listener.log"))
    env["ATT_SOURCE_LOG"] = source_log or os.path.join(d, "sources.jsonl")
    p = subprocess.Popen([PY, py], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); return p, port
        except OSError:
            time.sleep(0.05)
    p.kill(); raise SystemExit("listener did not start: " + p.stderr.read().decode()[:400])


def frame(obj):
    j = json.dumps(obj).encode()
    return struct.pack("<I", len(j) + 1) + j + b"\x00"


def send(port, rc, body=b"", extra=None, method="POST"):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    h = {"request_code": rc, "dev_id": "SB251CB-TEST-0001", "trans_id": "7"}
    h.update(extra or {})
    c.request(method, "/", body=body, headers=h)
    r = c.getresponse(); b = r.read()
    out = (r.status, r.getheader("response_code"), b)
    c.close(); return out


def requests_set():
    seq = []
    for i in range(6):
        seq.append(("receive_cmd", b"", None))
    for uid, t in (("3", "20261012090102"), ("5", "20261012091544"), ("3", "20261012090102"),   # the 3rd a re-send
                   ("11", "20261012131500")):
        seq.append(("realtime_glog", frame({"user_id": uid, "io_time": t, "io_mode": 0, "verify_mode": 1}), None))
    seq.append(("realtime_glog", b"garbage-no-json", None))                    # malformed: ERROR_NO_CMD both sides
    seq.append(("realtime_glog", frame({"user_id": "7", "io_time": "20261012100000", "io_mode": 1, "verify_mode": 1}),
                {"comm_key": "123456", "Authorization": "Basic abc"}))         # masked headers
    for i in range(35):
        seq.append(("receive_cmd", b"", None))                                 # heartbeats past the cap
    return seq


def csv_core(path):
    if not os.path.exists(path):
        return []
    return [",".join(l.rstrip("\n").split(",")[:4]) for l in open(path)]


def run_pair(d_from, d_to, to_source_log=None):
    pf, portf = start(FROM_PY, d_from)
    pt, portt = start(TO_PY, d_to, to_source_log)
    try:
        replies = []
        for rc, body, extra in requests_set():
            replies.append((send(portf, rc, body, extra), send(portt, rc, body, extra)))
        replies.append((send(portf, "receive_cmd", method="GET"), send(portt, "receive_cmd", method="GET")))
    finally:
        pf.terminate(); pt.terminate(); pf.wait(5); pt.wait(5)
    return replies


def main():
    root = tempfile.mkdtemp(prefix="walk_s535_")
    try:
        a, b = os.path.join(root, "from"), os.path.join(root, "to")
        os.makedirs(a); os.makedirs(b)
        print("W1-W5  the two listeners side by side")
        replies = run_pair(a, b)
        check(all(x == y for x, y in replies), "W1 every reply identical (%d requests)" % len(replies))
        check(sum(1 for x, _ in replies if x[1] == "OK") == 5 and all(x[2] == b"" for x, _ in replies),
              "W1 5 punches acked OK (one a re-send), every body empty")
        ca, cb = csv_core(os.path.join(a, "punches.csv")), csv_core(os.path.join(b, "punches.csv"))
        check(ca == cb and len(ca) == 5, "W2 punches.csv identical apart from received_at (%d lines, header + 4)" % len(ca))
        lines = [json.loads(l) for l in open(os.path.join(b, "sources.jsonl"))]
        p = [l for l in lines if l["punch"]]
        check(len(p) == 5 and {(l["user_id"], l["datetime"]) for l in p} ==
              {("3", "2026-10-12 09:01:02"), ("5", "2026-10-12 09:15:44"), ("11", "2026-10-12 13:15:00"),
               ("7", "2026-10-12 10:00:00")}, "W3 one source line per punch, re-send included, user and time read")
        check(all(l["ip"] == "127.0.0.1" and l["headers"].get("dev_id") == "SB251CB-TEST-0001" for l in p),
              "W3 address and the device's headers on every punch line")
        m = [l for l in p if l["user_id"] == "7"][0]["headers"]
        check(m.get("comm_key", "").startswith("<masked") and m.get("Authorization", "").startswith("<masked")
              and "123456" not in open(os.path.join(b, "sources.jsonl")).read(), "W4 key- and auth-named headers masked")
        other = [l for l in lines if not l["punch"]]
        check(len(other) == 30, "W5 other requests capped at 30 per sender per day (recorded %d of 43)" % len(other))
        check(not os.path.exists(os.path.join(a, "sources.jsonl")), "W5 the FROM side writes no source log")

        print("W6  NEGATIVE CONTROL: the source log unwritable")
        a2, b2 = os.path.join(root, "from2"), os.path.join(root, "to2")
        os.makedirs(a2); os.makedirs(b2); os.makedirs(os.path.join(b2, "is_a_dir"))
        replies2 = run_pair(a2, b2, os.path.join(b2, "is_a_dir"))
        check(all(x == y for x, y in replies2), "W6 replies still identical with the watch failing")
        check(csv_core(os.path.join(a2, "punches.csv")) == csv_core(os.path.join(b2, "punches.csv")),
              "W6 punches.csv still identical with the watch failing")

        print("W7-W8  the summary")
        out = os.path.join(root, "summary.json")
        env = dict(os.environ, ATT_SOURCE_LOG=os.path.join(b, "sources.jsonl"),
                   ATT_PUNCH_CSV=os.path.join(b, "punches.csv"), ATT_SOURCE_SUMMARY=out)
        # the walk's lines come from 127.0.0.1; to judge them as the device's, relabel them to an outside address
        src = os.path.join(b, "sources.jsonl")
        rel = [dict(json.loads(l), ip="203.0.113.7") for l in open(src)]
        with open(src, "w") as f:
            f.write("".join(json.dumps(r) + "\n" for r in rel))
        r = subprocess.run([PY, SUM_PY], env=env, capture_output=True, text=True)
        s = json.load(open(out))
        check(r.returncode == 0 and "dev_id" in s["one_mark_headers"] and s["verdict"].startswith("ONE MARK")
              and s["punches_csv_rows_without_source_line"] == 0, "W7 one mark found (dev_id), none missing: " + s["verdict"])
        with open(os.path.join(b, "punches.csv"), "a") as f:
            f.write("99,2026-10-12 12:00:00,0,1,%s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
        subprocess.run([PY, SUM_PY], env=env, capture_output=True, text=True)
        s = json.load(open(out))
        check(s["verdict"].startswith("WATCH INCOMPLETE") and s["punches_csv_rows_without_source_line"] == 1,
              "W8 a row with no source line is reported: " + s["verdict"][:60])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("WALK: %s" % ("GREEN" if not FAIL else "RED (%d)" % len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

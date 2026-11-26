#!/usr/bin/env python3
"""walk_s957.py -- kit S957_PUNCH_DOOR (the parent, S523, 26-Nov-2026). The walk: made-up stores only, made-up marks, no real number.

    python3 walk_s957.py walk <dir> <legs.json>
<dir> holds attlistener_v2.py, att_source_summary.py, callback_clock.py, presence.py, calls_console.py and freshness.py.
On the kit's TO files every check passes ("ALL PASS", exit 0). On the FROM files (no door, no presence.py) it must go red
without a crash -- the CONTROL. A scratch listener is started on 127.0.0.1 (a free port) with every path in a temp folder.
"""
import csv
import datetime as dt
import http.client
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time

PASS, FAIL = [], []
MARK_H, MARK_V = "dev_id", "WALKMARK7"


def ok(cond, what):
    (PASS if cond else FAIL).append(what)
    print(("PASS  " if cond else "FAIL  ") + what)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def safe(fn, what):
    try:
        fn()
    except Exception as e:                               # noqa: BLE001
        ok(False, "%s -- raised %s: %s" % (what, type(e).__name__, str(e)[:120]))


# ------------------------------------------------------------------------------------------------ A the listener's door
class Box:
    def __init__(self, d):
        self.root = tempfile.mkdtemp(prefix="s957w_")
        for k, v in (("ATT_PUNCH_CSV", "punches.csv"), ("ATT_LISTENER_LOG", "att.log"), ("ATT_SOURCE_LOG", "src.jsonl"),
                     ("ATT_DOOR_CONF", "door.json"), ("ATT_DOOR_STATE", "door.state.json"), ("ATT_REFUSED_CSV", "refused.csv")):
            os.environ[k] = os.path.join(self.root, v)
        self.L = load(os.path.join(d, "attlistener_v2.py"), "attl_%d" % id(self))
        for k, v in (("PUNCH_CSV", "punches.csv"), ("LOG_FILE", "att.log"), ("SOURCE_LOG", "src.jsonl"), ("DOOR_CONF", "door.json"),
                     ("DOOR_STATE", "door.state.json"), ("REFUSED_CSV", "refused.csv")):
            setattr(self.L, k, os.path.join(self.root, v))
        self.L._seen.clear()
        from http.server import ThreadingHTTPServer
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), self.L.Handler)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def p(self, n):
        return os.path.join(self.root, n)

    def conf(self, mode, header=MARK_H, value=MARK_V, raw=None):
        with open(self.p("door.json"), "w") as f:
            f.write(raw if raw is not None else json.dumps({"mode": mode, "header": header, "value": value}))
        t = time.time() + len(os.listdir(self.root))       # a new mtime every write
        os.utime(self.p("door.json"), (t, t))

    def send(self, uid=None, when=None, mark=MARK_V, hname=MARK_H, rc="realtime_glog"):
        body = b"{}" if uid is None else json.dumps({"user_id": uid, "io_time": when, "io_mode": 0, "verify_mode": 1}).encode()
        hdr = {"request_code": rc, "Content-Type": "application/octet-stream"}
        if mark is not None:
            hdr[hname] = mark
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("POST", "/", body=b"\x00\x00\x00\x00" + body + b"\x00", headers=hdr)
        r = c.getresponse()
        r.read()
        ack = dict((k.lower(), v) for k, v in r.getheaders()).get("response_code")
        c.close()
        return ack

    def rows(self, name="punches.csv"):
        if not os.path.exists(self.p(name)):
            return []
        with open(self.p(name)) as f:
            return list(csv.DictReader(f))

    def state(self):
        try:
            return json.load(open(self.p("door.state.json")))
        except Exception:                                # noqa: BLE001
            return {}

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.root, ignore_errors=True)


def part_a(d, legs):
    print("[A] the punch door (attlistener_v2.py)")
    b = Box(d)
    try:
        ok(b.send(7, "20261120090000", mark=None) == "OK" and len(b.rows()) == 1,
           "A1 no door file: the door is open, a punch without the mark is stored as before")
        b.conf("enforce")
        ok(b.send(7, "20261120091000") == "OK" and len(b.rows()) == 2, "A2 enforce: a punch with the mark is stored, ack OK")
        st = b.state()
        ok(st.get("mode") == "enforce" and st.get("last_ok_iso") and st.get("last_admitted_iso"), "A2 the state: enforce, last_ok + last_admitted")
        ok(b.send(9, "20261120092000", mark=None) == "OK", "A3 enforce: a punch WITHOUT the mark is still acknowledged OK")
        ok(len(b.rows()) == 2, "A3 ... and NOT in punches.csv")
        rf = b.rows("refused.csv")
        ok(len(rf) == 1 and rf[0]["user_id"] == "9" and rf[0]["reason"] == "no mark" and rf[0]["ip"] == "127.0.0.1",
           "A3 ... kept aside in the refused file (user, time, address, reason)")
        ok(oct(os.stat(b.p("refused.csv")).st_mode & 0o777) == "0o600", "A3 the refused file is 0600")
        st = b.state()
        ok(st.get("refused_total") == 1 and st.get("last_failure_iso") and st["last_failure_iso"] >= st["last_ok_iso"],
           "A3 the state: refused 1, the newest refusal after the last all-clear")
        src = [json.loads(x) for x in open(b.p("src.jsonl"))]
        ok(src and src[-1].get("door") == "refused" and src[-2].get("door") == "mark", "A3 the source line says door refused / mark")
        ok(b.send(9, "20261120093000", mark="WALKMARK8") == "OK" and len(b.rows()) == 2 and b.rows("refused.csv")[-1]["reason"] == "wrong mark",
           "A4 a WRONG mark value: refused, kept aside ('wrong mark')")
        before = b.state().get("last_ok_iso")
        time.sleep(1.1)
        b.send(7, "20261120094000")
        st = b.state()
        ok(len(b.rows()) == 3 and st.get("last_ok_iso") == before and st.get("last_admitted_iso") > before,
           "A5 a good punch after a refusal is stored, but the all-clear does not move (the leg stays red)")
        b.L.DOOR_RED_H = 0.0001
        time.sleep(1.1)
        b.send(7, "20261120095000")
        ok(b.state().get("last_ok_iso", "") > (b.state().get("last_failure_iso") or ""), "A5 ... after DOOR_RED_H it moves again")
        b.L.DOOR_RED_H = 24
        ok(b.send(None, None, mark=None, rc="receive_cmd") == "ERROR_NO_CMD" and b.state().get("refused_total") == 2,
           "A6 a heartbeat without the mark: ERROR_NO_CMD, nothing counted")
        ok(b.send(7, "20261120100000", hname="DEV_ID") == "OK" and len(b.rows()) == 5, "A7 the header's name in other letters: admitted")
        n = len(b.rows())
        ok(b.send(7, "20261120100000") == "OK" and len(b.rows()) == n, "A8 a re-send with the mark: acknowledged, not stored twice")
        b.conf("watch")
        ok(b.send(11, "20261120101000", mark=None) == "OK" and len(b.rows()) == n + 1 and b.state().get("would_refuse_total") == 1
           and b.state().get("mode") == "watch", "A9 watch mode (the file changed under the running listener): stored, counted as would-refuse")
        b.conf("enforce", raw="{not json")
        ok(b.send(12, "20261120102000", mark=None) == "OK" and len(b.rows()) == n + 2, "A10 an unreadable door file: open (as before S957)")
        b.conf("enforce", value="")
        ok(b.send(13, "20261120103000", mark=None) == "OK" and len(b.rows()) == n + 3, "A10 a door file with no value: open")
        b.conf("enforce")
        b.L.DOOR_STATE = b.root                          # a folder: the state cannot be written
        ok(b.send(7, "20261120104000") == "OK" and len(b.rows()) == n + 4, "A11 the state unwritable: the punch is still stored and acked")
        b.L.DOOR_STATE = b.p("door.state.json")
        b.L.REFUSED_CSV = b.root
        ok(b.send(14, "20261120105000", mark=None) == "OK" and len(b.rows()) == n + 4, "A11 the refused file unwritable: still refused, acked")
        b.L.REFUSED_CSV = b.p("refused.csv")
        # A12 a week's punches replayed: every one admitted, in order, none refused
        b.conf("enforce")
        r0, f0 = len(b.rows()), len(b.rows("refused.csv"))
        sent = 0
        for day in range(16, 23):
            for uid in (1, 2, 3, 5, 8, 12, 18, 21, 101):
                for hh in (9, 18):
                    b.send(uid, "202611%02d%02d%02d00" % (day, hh, uid % 60)); sent += 1
        ok(len(b.rows()) - r0 == sent and len(b.rows("refused.csv")) == f0, "A12 a week replayed (%d punches): all stored, none refused" % sent)
        # A13 the TO listener carries no mark: no header value, no long number
        txt = open(os.path.join(d, "attlistener_v2.py"), encoding="utf-8").read()
        ok("DOOR_CONF" in txt and not re.search(r"\b\d{9,}\b", txt.replace("0o600", "")), "A13 the listener's code holds no mark and no long number")
        # A15 re-admitting refused punches (door_s957.py readmit, the kit's tool)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        DS = load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "door_s957.py"), "door_s957w")
        n0, rf0 = len(b.rows()), b.rows("refused.csv")
        with open(b.p("refused.csv"), "a") as f:
            f.write("7,2026-11-20 09:10:00,0,1,2026-11-20 09:10:00,127.0.0.1,no mark\n")      # already in the punch file
        DS.readmit(b.p("refused.csv"), b.p("punches.csv"), yes=False)
        ok(len(b.rows()) == n0 and os.path.exists(b.p("refused.csv")), "A15 readmit without --yes: counts only, nothing changed")
        DS.readmit(b.p("refused.csv"), b.p("punches.csv"), yes=True, since="2026-11-21")
        ok(len(b.rows()) == n0 and os.path.exists(b.p("refused.csv")), "A15 readmit --since after every refused row: nothing taken")
        DS.readmit(b.p("refused.csv"), b.p("punches.csv"), yes=True)
        added = [r for r in b.rows()[n0:]]
        ok(len(added) == len(rf0) and not os.path.exists(b.p("refused.csv"))
           and any(x.startswith("refused.csv.readmitted_") for x in os.listdir(b.root))
           and all(r["machine_time"] == r["datetime"] for r in added),
           "A15 readmit: every refused row not already there added once (%d), the refused file renamed" % len(rf0))
    finally:
        b.close()
    # A14 the health leg
    try:
        sys.path.insert(0, d)
        fr = load(os.path.join(d, "freshness.py"), "fr_s957")
        lg = [x for x in json.load(open(legs, encoding="utf-8"))["legs"] if x.get("name") == "punch door"]
        ok(len(lg) == 1 and lg[0]["kind"] == "state_json" and lg[0]["target"] == "/root/punch_door.state.json"
           and lg[0]["fail_field"] == "last_failure_iso" and lg[0]["max_age_h"] == 74 and lg[0]["group"] == "Attendance",
           "A14 the legs file declares 'punch door' (state_json, fail_field, 74 h, Attendance)")
        tmp = tempfile.mkdtemp(prefix="s957l_")
        sp = os.path.join(tmp, "st.json")
        leg = dict(lg[0] if lg else {"name": "x", "kind": "state_json", "field": "last_ok_iso", "fail_field": "last_failure_iso",
                                     "max_age_h": 74}, target=sp)
        n_ = dt.datetime.now()
        json.dump({"last_ok_iso": n_.strftime("%Y-%m-%dT%H:%M:%S")}, open(sp, "w"))
        g = fr.check_leg(leg, time.time())["verdict"]
        json.dump({"last_ok_iso": (n_ - dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                   "last_failure_iso": n_.strftime("%Y-%m-%dT%H:%M:%S")}, open(sp, "w"))
        r = fr.check_leg(leg, time.time())["verdict"]
        ok(g == fr.OK and r == fr.STALE, "A14 the leg: green after an admitted punch, red at once after a refusal")
        a = json.load(open(legs, encoding="utf-8"))["legs"]
        ok(len({x["name"] for x in a}) == len(a), "A14 leg names unique (%d legs)" % len(a))
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:                               # noqa: BLE001
        ok(False, "A14 the health leg -- raised %s: %s" % (type(e).__name__, str(e)[:120]))


# ------------------------------------------------------------------------------------------------ B the nightly summary
def part_b(d):
    print("[B] the nightly source summary (att_source_summary.py)")
    S = load(os.path.join(d, "att_source_summary.py"), "summ_s957")
    hdr = {MARK_H: MARK_V, "accept-language": "en-us", "user-agent": "Mozilla/4.0"}

    def line(t, uid, when, door="mark", h=None, ip="100.64.1.2"):
        return {"t": t, "ip": ip, "punch": True, "user_id": str(uid), "datetime": when, "headers": h or hdr, "door": door,
                "request_code": "realtime_glog", "ack": "OK"}
    rows = [line("2026-11-11 09:40:00", 8, "2026-11-11 07:01:00"), line("2026-11-11 09:41:00", 9, "2026-11-11 09:41:00")]
    prow = [("8", "2026-11-11 09:40:00", "2026-11-11 07:01:00"), ("9", "2026-11-11 09:41:00", "")]
    s = S.summarise(rows, 0, prow)
    ok(s["punches_csv_rows_without_source_line"] == 0 and s["verdict"].startswith("ONE MARK") and MARK_H in s["one_mark_headers"],
       "B1 a row whose time the listener corrected is matched on the machine's time -> ONE MARK")
    s = S.summarise(rows, 0, prow + [("5", "2026-11-11 10:00:00", "")])
    ok(s["verdict"].startswith("WATCH INCOMPLETE") and s["punches_csv_rows_without_source_line"] == 1, "B2 a real row with no source line -> INCOMPLETE")
    rows2 = rows + [line("2026-11-12 01:00:00", 9, "2026-11-12 01:00:00", door="refused", h={MARK_H: "OTHER", "accept-language": "en-us"},
                         ip="198.51.100.7")]
    s = S.summarise(rows2, 0, prow)
    ok(s["verdict"].startswith("ONE MARK") and s.get("refused_by_door") == 1 and s["headers_on_punches"][MARK_H]["distinct_values"] == 1,
       "B3 a refused punch is counted apart and never judged as the machine's")
    os.environ.pop("ATT_SUMMARY_KEEP", None)
    s = S.summarise(rows2, 0, prow)
    blob = json.dumps(s)
    ok(MARK_V not in blob and "100.64.1.2" not in blob and "OTHER" not in blob and s["headers_on_punches"][MARK_H]["commonest"][0][0] == "<9 chars>"
       and "100.64.x.x" in s["by_address"] and s["verdict"].startswith("ONE MARK"),
       "B5 the nightly file (it travels with the bundle) never holds the mark or a full address")
    os.environ["ATT_SUMMARY_KEEP"] = "1"
    s = S.summarise(rows2, 0, prow)
    ok(s["headers_on_punches"][MARK_H]["commonest"][0][0] == MARK_V, "B5 ATT_SUMMARY_KEEP=1 (the installer's scratch only): the value kept")
    os.environ.pop("ATT_SUMMARY_KEEP", None)
    tmp = tempfile.mkdtemp(prefix="s957s_")
    pc = os.path.join(tmp, "p.csv")
    open(pc, "w").write("user_id,datetime,io_mode,verify_mode,received_at,machine_time\n8,2026-11-11 09:40:00,0,1,2026-11-11 09:40:00,"
                        "2026-11-11 07:01:00\n4,2026-10-12 09:00:00,0,1,2026-10-12 09:00:01\n")
    got = S.read_punch_rows(pc, "2026-10-01")
    ok(got == [("8", "2026-11-11 09:40:00", "2026-11-11 07:01:00"), ("4", "2026-10-12 09:00:00", "")],
       "B4 the punch file is read with the machine's time (five-column rows too)")
    shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ C presence
def part_c(d):
    print("[C] presence.py and the call-back clock's duty")
    sys.path.insert(0, d)
    import calls_console as CC                           # noqa: E402
    PR = load(os.path.join(d, "presence.py"), "presence")
    sys.modules["presence"] = PR
    tmp = tempfile.mkdtemp(prefix="s957p_")
    m = os.path.join(tmp, "staff_master.csv")
    with open(m, "w") as f:
        f.write("user_id,name,wd_start,wd_end,sun_start,sun_end,active\n1,Shivani A,09:00,18:00,,,Y\n2,Alisha B,10:00,20:30,10:00,14:00,Y\n"
                "3,Shavez C,09:00,20:30,,,Y\n4,Old D,09:00,18:00,,,N\n")
    pf = os.path.join(tmp, "punches.csv")
    sil = os.path.join(tmp, "sil.json")
    os.environ["PRESENCE_SILENCE_STATE"] = sil
    os.environ["SR_DB_PATH"] = os.path.join(tmp, "absent.db")   # never the real staff register
    os.environ.update({"SR_STAFF_MASTER": m, "SR_PUNCH_CSV": pf})   # never the box's real staff list or punch file (the S523 box run)
    os.environ.pop("PORTAL_PRESENCE_ROSTER", None)
    D = "2026-11-25"                                     # a Wednesday

    def punches(*rows):
        with open(pf, "w") as f:
            f.write("user_id,datetime,io_mode,verify_mode,received_at,machine_time\n")
            for u, t in rows:
                f.write("%s,%s %s:00,0,1,%s %s:00,\n" % (u, D, t, D, t))

    def at(hm, day=D):
        return dt.datetime.strptime("%s %s" % (day, hm), "%Y-%m-%d %H:%M")

    def on(hm, day=D):
        return {k: v["by"] for k, v in PR.today(CC, at(hm, day), m, pf)["people"].items() if v["on_duty"]}

    if os.path.exists(sil):
        os.remove(sil)
    punches(("1", "08:50"), ("3", "09:05"), ("3", "13:00"), ("2", "10:02"), ("2", "10:03"))
    ok(on("08:55") == {}, "C1 08:55: punched in before the shift -> not yet on duty")
    ok(on("12:00") == {"shivani": "punch", "shavez": "punch", "alisha": "punch"}, "C1 12:00: the three punched in are on duty")
    t = PR.today(CC, at("14:00"), m, pf)
    ok(t["people"]["shavez"]["out"] is not None and not t["people"]["shavez"]["on_duty"], "C2 a punch-out (two punches, 4 h apart) ends the duty")
    ok(t["people"]["alisha"]["out"] is None and t["people"]["alisha"]["on_duty"], "C3 a double tap at the door (one minute apart) is not a punch-out")
    punches(("1", "08:50"), ("1", "09:25"))
    ok(on("14:00") == {"shivani": "punch"}, "C3 a re-tap on arrival 35 min later is not a punch-out")
    punches(("1", "08:50"), ("3", "09:05"), ("3", "13:00"), ("2", "10:02"), ("2", "10:03"))
    ok("old" not in t["people"], "C3 an inactive person is not read")
    ok(on("18:30") == {"alisha": "punch"}, "C4 18:30: Shivani's shift has ended")
    punches()
    ok(on("09:20") == {}, "C5 no punch at all, 09:20: nobody on duty yet")
    ok(on("09:40") == {"shivani": "roster", "shavez": "roster"} and PR.today(CC, at("09:40"), m, pf)["basis"] == "roster",
       "C5 no punch at all by 09:30: the roster stands in (shift-wise)")
    ok(on("10:30") == {"shivani": "roster", "shavez": "roster", "alisha": "roster"}, "C5 10:30: Alisha's shift too, by roster")
    import sqlite3
    srdb = os.path.join(tmp, "sr.db")
    c_ = sqlite3.connect(srdb)
    c_.execute("CREATE TABLE festival_day (fest_date TEXT PRIMARY KEY, name TEXT, clinic_closed INTEGER)")
    c_.execute("INSERT INTO festival_day VALUES (?,?,?)", (D, "made-up", 1))
    c_.execute("INSERT INTO festival_day VALUES (?,?,?)", ("2026-11-24", "made-up leave day", 0))
    c_.commit()
    c_.close()
    os.environ["SR_DB_PATH"] = srdb
    ok(on("10:30") == {} and PR.today(CC, at("10:30"), m, pf)["closed"], "C5 a day the register marks the clinic closed: no roster")
    ok(len(on("10:30", "2026-11-24")) == 3, "C5 a festival leave day (clinic open): the roster as usual")
    os.environ["SR_DB_PATH"] = os.path.join(tmp, "absent.db")
    ok(len(on("10:30")) == 3, "C5 the register unreadable: not a holiday")
    punches(("99", "08:30"))
    ok(on("09:40") == {}, "C5 a punch today by someone not on the staff list: the machine works, no roster")
    punches()
    os.environ["PORTAL_PRESENCE_ROSTER"] = "0"
    ok(on("10:30") == {}, "C6 PORTAL_PRESENCE_ROSTER 0: no roster")
    os.environ["PORTAL_PRESENCE_ROSTER_AFTER"] = "11:00"
    os.environ.pop("PORTAL_PRESENCE_ROSTER", None)
    ok(on("10:30") == {} and len(on("11:05")) == 3, "C6 PORTAL_PRESENCE_ROSTER_AFTER 11:00 moves the fallback")
    os.environ.pop("PORTAL_PRESENCE_ROSTER_AFTER", None)
    punches(("1", "09:01"))
    ok(on("12:00") == {"shivani": "punch"}, "C7 one person punched: the punches rule, the others are absent")
    json.dump({"last_ok_iso": "2026-11-25 11:00:00", "last_failure_iso": "2026-11-25 11:40:00"}, open(sil, "w"))   # the watch's own format
    ok(on("12:00") == {"shivani": "punch", "shavez": "roster", "alisha": "roster"}, "C8 the machine silent: the roster for those with no punch")
    punches(("1", "09:01"), ("1", "11:30"))
    ok("shivani" not in on("12:00"), "C8 ... a punch-out still ends the duty (a punch always wins)")
    json.dump({"last_ok_iso": "2026-11-25 09:00:00", "last_failure_iso": "2026-11-25 09:40:00"}, open(sil, "w"))
    ok(not PR.machine_silent(sil, at("12:00")) and PR.machine_silent(sil, at("09:50")),
       "C8 a silence failure 2 h old is not 'silent now' (the watch may be off); 10 min old is")
    json.dump({"last_ok_iso": "2026-11-25T09:00:00", "last_failure_iso": "2026-11-25T09:40:00"}, open(sil, "w"))
    ok(PR.machine_silent(sil, at("09:50")), "C8 the 'T' form is read too")
    json.dump({"last_ok_iso": "2026-11-25 11:45:00", "last_failure_iso": "2026-11-25 11:40:00"}, open(sil, "w"))
    ok(not PR.machine_silent(sil), "C8 the machine back (all-clear newer): not silent")
    open(sil, "w").write("{bad")
    ok(not PR.machine_silent(sil), "C8 an unreadable silence state is not silence")
    punches()
    ok(on("11:00", "2026-11-29") == {"alisha": "roster"}, "C9 a Sunday follows the Sunday columns (empty = off)")
    os.remove(pf)
    ok(PR.today(CC, at("12:00"), m, pf)["ok"] is False, "C10 the punch file missing: duty not known")
    ok(PR.clock_on_duty(CC, at("12:00"), ["shivani", "alisha"], "reception", ("shavez",))[1] == "duty not known",
       "C10 the clock's answer: duty not known")
    punches(("1", "09:01"))
    os.remove(sil)
    os.environ.update({"SR_STAFF_MASTER": m, "SR_PUNCH_CSV": pf})
    CC._CFG = None
    who, why = PR.clock_on_duty(CC, at("12:00"), ["shivani", "alisha"], "reception", ("shavez",))
    ok(who == ["shivani", "reception"] and why == "on duty", "C11 the clock: Shivani on duty + reception ('on duty')")
    punches()
    who, why = PR.clock_on_duty(CC, at("12:00"), ["shivani", "alisha"], "reception", ("shavez",))
    ok(who == ["shivani", "alisha", "reception"] and why.startswith("on duty by roster"), "C11 no punch by 09:30: 'on duty by roster'")
    who, why = PR.clock_on_duty(CC, at("09:10"), ["shivani", "alisha"], "reception", ("shavez",))
    ok(who == ["reception", "shavez"] and why == "no phone staff on duty", "C11 09:10, nobody punched: reception + the backup")
    # the clock itself delegates
    sys.argv = [sys.argv[0]]
    CB = load(os.path.join(d, "callback_clock.py"), "cbc_s957")
    CB.PORTAL_DIR = d
    who, why = CB.on_duty(CC, at("12:00"))
    ok(why.startswith("on duty by roster") and "reception" in who, "C12 callback_clock.on_duty reads through presence.py")
    hide = tempfile.mkdtemp(prefix="s957h_")
    sys.modules.pop("presence", None)
    saved = list(sys.path)
    sys.path[:] = [x for x in sys.path if not os.path.exists(os.path.join(x or ".", "presence.py"))]   # the kit folder holds one too
    CB.PORTAL_DIR = hide
    who, why = CB.on_duty(CC, at("12:00"))
    ok(why.startswith("duty not known") and "reception" in who, "C12 presence.py absent: every phone staff login (duty not known)")
    sys.path[:] = saved
    for k in ("SR_STAFF_MASTER", "SR_PUNCH_CSV", "PRESENCE_SILENCE_STATE", "SR_DB_PATH"):
        os.environ.pop(k, None)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(hide, ignore_errors=True)


def main(argv):
    if len(argv) != 4 or argv[1] != "walk":
        raise SystemExit(__doc__)
    d, legs = os.path.abspath(argv[2]), os.path.abspath(argv[3])
    os.environ["TZ"] = "Asia/Kolkata"
    try:
        time.tzset()
    except Exception:                                    # noqa: BLE001
        pass
    safe(lambda: part_a(d, legs), "[A]")
    safe(lambda: part_b(d), "[B]")
    safe(lambda: part_c(d), "[C]")
    print("%d checks, %d failed" % (len(PASS) + len(FAIL), len(FAIL)))
    print("ALL PASS" if not FAIL else "RED")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

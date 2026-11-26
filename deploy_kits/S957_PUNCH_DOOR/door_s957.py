#!/usr/bin/env python3
"""door_s957.py -- kit S957_PUNCH_DOOR (the parent, S523, 26-Nov-2026). Run by the installer on the box; it need not be run by hand.
It prints counts and words only -- never the mark, never an address, never a user.

  decide <summary.json> <door conf to write>
      Reads the source watch's own summary (att_source_summary.py, S957's version, run on the LIVE source log and punch file) and
      writes the door's configuration (0600): mode "enforce" when the verdict is ONE MARK and dev_id is one of the marks;
      mode "watch" when dev_id is on every punch with one value but the verdict is not clean; nothing at all otherwise.
      Prints: DECIDE <enforce|watch|none> (<why>)

  replay <listener.py> <source log> <door conf> <days>
      Starts the given listener on 127.0.0.1 (a free port, every file in a temp folder) with that door, and replays every punch
      the machine sent in the last <days> days (from the source log: its headers as recorded, its user and time), then one punch
      with the mark taken off and one with a wrong mark. Prints: REPLAY punches N distinct M stored S refused R spoof_no_mark
      refused|ADMITTED spoof_wrong refused|ADMITTED  (the installer wants S = M and R = 0: every distinct genuine punch STORED)

  readmit [--since YYYY-MM-DD] [--yes]
      Only if refused punches were genuine (say, a replaced machine before its new mark is written). Without --yes it only
      prints the refused rows' counts by day and reason. With --yes it copies every refused row (from --since on, when given)
      that is not in /root/punches.csv already into it, in the listener's own columns, and renames the refused file to
      <name>.readmitted_<time> (rows before --since stay in that renamed file). Then restart the listener
      (systemctl restart attlistener) so it knows the added rows. Prints counts only.
"""
import datetime as dt
import http.client
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading

MARK = "dev_id"
LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")


def decide(summary, conf):
    s = json.load(open(summary, encoding="utf-8"))
    v = str(s.get("verdict") or "")
    h = (s.get("headers_on_punches") or {}).get(MARK) or {}
    n = int(s.get("punch_lines") or 0)
    value = (h.get("commonest") or [[None]])[0][0]
    one = h.get("distinct_values") == 1 and h.get("on_punches") == n and n > 0 and value
    if v.startswith("ONE MARK") and MARK in (s.get("one_mark_headers") or []) and one:
        mode, why = "enforce", "ONE MARK: %d punches over %d days carry it" % (n, len(s.get("days_with_punches") or []))
    elif one:
        mode, why = "watch", "the mark is on every punch, but the watch says: %s" % v.split(" -- ")[0]
    else:
        print("DECIDE none (%s)" % v.split(" -- ")[0][:80])
        return 0
    fd = os.open(conf + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"mode": mode, "header": MARK, "value": value, "kit": "S957",
                   "written": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "evidence": v[:200]}, f, indent=1, sort_keys=True)
    os.chmod(conf + ".tmp", 0o600)
    os.replace(conf + ".tmp", conf)
    print("DECIDE %s (%s)" % (mode, why))
    return 0


def replay(listener, src, conf, days):
    root = tempfile.mkdtemp(prefix="s957r_")
    try:
        for k, v in (("ATT_PUNCH_CSV", "p.csv"), ("ATT_LISTENER_LOG", "l.log"), ("ATT_SOURCE_LOG", "s.jsonl"),
                     ("ATT_DOOR_STATE", "d.state.json"), ("ATT_REFUSED_CSV", "r.csv")):
            os.environ[k] = os.path.join(root, v)
        os.environ["ATT_DOOR_CONF"] = conf
        spec = importlib.util.spec_from_file_location("attl_replay", listener)
        L = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(L)
        L.log = lambda *_a, **_k: None
        from http.server import ThreadingHTTPServer
        srv = ThreadingHTTPServer(("127.0.0.1", 0), L.Handler)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        cut = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        lines = []
        with open(src, encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:                        # noqa: BLE001
                    continue
                if r.get("punch") and r.get("ip") not in LOOPBACK and r.get("door") != "refused" and (r.get("t") or "") >= cut \
                        and r.get("user_id") and r.get("datetime"):
                    lines.append(r)

        def send(r, drop=False, wrong=False):
            hdr = {k: v for k, v in (r.get("headers") or {}).items() if not str(v).startswith("<masked")}
            hdr.pop("Host", None)
            hdr.pop("host", None)
            for k in list(hdr):
                if k.lower() == MARK:
                    if drop:
                        del hdr[k]
                    elif wrong:
                        hdr[k] = str(hdr[k]) + "0"
            io = dt.datetime.strptime(r["datetime"][:19], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M%S")
            body = json.dumps({"user_id": r["user_id"], "io_time": io, "io_mode": 0, "verify_mode": 1}).encode()
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            c.request("POST", "/", body=b"\x00\x00\x00\x00" + body + b"\x00", headers=hdr)
            c.getresponse().read()
            c.close()

        for r in lines:
            send(r)
        st = json.load(open(os.environ["ATT_DOOR_STATE"])) if os.path.exists(os.environ["ATT_DOOR_STATE"]) else {}
        refused = int(st.get("refused_total") or 0)
        distinct = {(str(r["user_id"]), r["datetime"][:19]) for r in lines}
        stored = set()
        if os.path.exists(os.environ["ATT_PUNCH_CSV"]):
            import csv as _csv
            with open(os.environ["ATT_PUNCH_CSV"], newline="") as f:
                for row in _csv.DictReader(f):
                    stored.add((row["user_id"], row["datetime"]))
        got = len(distinct & stored)
        verdicts = []
        for how in ("drop", "wrong"):
            if not lines:
                verdicts.append("untested")
                continue
            r = dict(lines[-1], user_id="999", datetime="2001-01-01 00:00:0%d" % (1 if how == "drop" else 2))
            def _ref():
                try:
                    return int(json.load(open(os.environ["ATT_DOOR_STATE"])).get("refused_total") or 0)
                except Exception:                        # noqa: BLE001
                    return 0
            before = _ref()
            send(r, drop=(how == "drop"), wrong=(how == "wrong"))
            after = _ref()
            verdicts.append("refused" if after == before + 1 else "ADMITTED")
        srv.shutdown()
        srv.server_close()
        print("REPLAY punches %d distinct %d stored %d refused %d spoof_no_mark %s spoof_wrong %s"
              % (len(lines), len(distinct), got, refused, verdicts[0], verdicts[1]))
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def readmit(refused="/root/punches_refused.csv", punches="/root/punches.csv", yes=False, since=""):
    import csv as _csv
    from collections import Counter
    if not os.path.exists(refused):
        print("READMIT nothing: no refused file")
        return 0
    with open(refused, newline="", encoding="utf-8") as f:
        allr = list(_csv.DictReader(f))
    by = Counter(((r.get("datetime") or "")[:10], r.get("reason") or "?") for r in allr)
    for (d, why), n in sorted(by.items()):
        print("READMIT refused %s  %-10s %d" % (d, why, n))
    if not yes:
        print("READMIT counts only -- nothing changed (add --yes to take them back%s)" % (", from --since" if since else ""))
        return 0
    taken = [r for r in allr if not since or (r.get("datetime") or "")[:10] >= since]
    keep = [r for r in allr if r not in taken]
    if not taken:
        print("READMIT nothing taken: no refused row from %s on" % since)
        return 0
    have = set()
    with open(punches, newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            have.add((row.get("user_id"), row.get("datetime")))
    add, dup = [], 0
    for row in taken:
        k = (row.get("user_id"), row.get("datetime"))
        if not k[0] or not k[1] or k in have:
            dup += 1
            continue
        have.add(k)
        add.append("%s,%s,%s,%s,%s,%s\n" % (k[0], k[1], row.get("io_mode", ""), row.get("verify_mode", ""),
                                             row.get("received_at", ""), k[1]))
    if add:
        with open(punches, "a", encoding="utf-8") as f:
            f.writelines(add)
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    done = "%s.readmitted_%s" % (refused, stamp)
    cols = ["user_id", "datetime", "io_mode", "verify_mode", "received_at", "ip", "reason"]
    if not keep:
        os.rename(refused, done)
    else:
        for path, rows in ((done, taken), (refused + ".s957tmp", keep)):
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                w = _csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
        os.replace(refused + ".s957tmp", refused)
    print("READMIT %d rows added to the punch file, %d already there or unreadable; the taken rows kept in .readmitted_%s; "
          "%d older rows stay refused. Now: systemctl restart attlistener" % (len(add), dup, stamp, len(keep)))
    return 0


if __name__ == "__main__":
    a = sys.argv
    if len(a) == 4 and a[1] == "decide":
        sys.exit(decide(a[2], a[3]))
    if a[1:2] == ["readmit"]:
        _since = a[a.index("--since") + 1] if "--since" in a and a.index("--since") + 1 < len(a) else ""
        sys.exit(readmit(yes="--yes" in a, since=_since))
    if len(a) == 6 and a[1] == "replay":
        sys.exit(replay(a[2], a[3], a[4], float(a[5])))
    raise SystemExit(__doc__)

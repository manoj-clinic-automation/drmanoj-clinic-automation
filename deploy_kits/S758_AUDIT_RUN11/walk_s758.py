#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s758.py -- kit S758_AUDIT_RUN11's walk. Runs on COPIES only; made-up bills on a made-up day (2030-03-01).

  python3 walk_s758.py <dir with the files to test: finance_ingest.py, code_bundle.py, clinic_health_report.py>
                       <the live /root/finance (day_resync, marg_report ...)> <a finance.db to COPY, or a schema .sql> [--control]

Last line: 'WALK OK n/n' or 'WALK RED at check k: ...'; with --control: 'CONTROL: red at check k ...' (the files tested are not
the kit's) or 'CONTROL: GREEN -- wrong'."""
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tarfile
import tempfile

ARGS = [x for x in sys.argv[1:] if not x.startswith("--")]
CONTROL = "--control" in sys.argv
CODE, FIN, DB = ARGS[0], ARGS[1], ARGS[2]
sys.path[:0] = [os.path.abspath(CODE), os.path.abspath(FIN)]
TMP = tempfile.mkdtemp(prefix="w758.")
os.environ["SANJEEVNI_OFF_DIR"] = os.path.join(TMP, "off")
os.makedirs(os.environ["SANJEEVNI_OFF_DIR"])
N = {"n": 0}


def red(msg):
    print("WALK RED at check %d: %s" % (N["n"], msg))
    if CONTROL:
        print("CONTROL: red at check %d (%s)" % (N["n"], msg[:120]))
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1)


def check(ok, msg):
    N["n"] += 1
    if not ok:
        red(msg)


def fresh(tag):
    p = os.path.join(TMP, "w_%s.db" % tag)
    if DB.endswith(".sql"):
        c = sqlite3.connect(p)
        for st in open(DB, encoding="utf-8").read().split(";\n"):
            if st.strip():
                try:
                    c.execute(st)
                except sqlite3.Error:
                    pass
        for code in ("medical", "clinic"):
            try:
                c.execute("INSERT INTO business_unit(code, name) VALUES (?,?)", (code, code))
            except sqlite3.Error:
                pass
        c.commit()
        c.close()
    else:
        s = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
        d = sqlite3.connect(p)
        s.backup(d)
        d.close()
        s.close()
    c = sqlite3.connect(p, timeout=30)
    c.row_factory = sqlite3.Row
    return c, p


DAY = "2030-03-01"
LINES = ("bill_date,bill_no,clinic_id,patient_name,phone_last4,description,amount,mode,gross,disc,mobile\n"
         "%s,WALK-P1,,PROSIJER WALKNAME,,,98.00,cash,97.56,0.00,\n"
         "%s,WALK-S1,,WALKNAME TWO,,,300.00,upi,300.00,0.00,\n"
         "%s,WALK-S2,,WALKNAME THREE,,,150.00,cash,150.00,0.00,\n") % (DAY, DAY, DAY)


def prep(c):
    c.execute("DELETE FROM day_entry WHERE unit='medical' AND business_date=?", (DAY,))
    c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) "
              "VALUES ('medical',?,'submitted','app','walk','2030-03-02T08:31:00')", (DAY,))
    c.commit()


def exc(c):
    return c.execute("SELECT severity, status, detail FROM recon_exception WHERE unit='medical' AND business_date=? AND kind='noncash_at_ingest'",
                     (DAY,)).fetchone()


# ---------------------------------------------------------------- 1-5 · AF-37: the S672 failure is no longer silent
import finance_ingest as FI                               # noqa: E402
import day_resync as DR                                   # noqa: E402

c, _ = fresh("ingest")
prep(c)
real = getattr(DR, "at_ingest", None)


def boom(*a, **k):
    raise RuntimeError("walk: the deduction fails")


DR.at_ingest = boom
try:
    r = FI.ingest_day(c, "medical", DAY, "marg_export", LINES, run_by="walk", source_ref="push:walk", commit=False)
    c.commit()
finally:
    DR.at_ingest = real
e = exc(c)
check(e is not None and e["status"] == "open" and e["severity"] == "high" and "do not approve" in (e["detail"] or ""),
      "AF-37: a failed deduction left no open exception on the day: %s" % (dict(e) if e else None))
check(r.get("ok") and r.get("rows_read") in (0, 3) and (DB.endswith(".sql") or os.environ.get("S758_WALK_SCHEMA_ONLY") == "1" or r.get("rows_read") == 3),
      "AF-37: the ingest itself did not stand: %s" % r)       # a schema-only database reads no bill; a real copy reads all three
check("RuntimeError" in (e["detail"] or ""), "AF-37: the exception does not say what failed")
r2 = FI.ingest_day(c, "medical", DAY, "marg_export", LINES, run_by="walk", source_ref="push:walk2", commit=False)
c.commit()
e2 = exc(c)
check(r2.get("ok") and e2 is not None and e2["status"] == "resolved", "AF-37: a good ingest did not resolve it: %s" % (dict(e2) if e2 else None))
DR.at_ingest = boom
try:
    FI.ingest_day(c, "medical", DAY, "marg_export", LINES, run_by="walk", source_ref="push:walk3", commit=False)
    c.commit()
finally:
    DR.at_ingest = real
check(exc(c)["status"] == "open" and c.execute("SELECT COUNT(*) FROM recon_exception WHERE unit='medical' AND business_date=? "
                                                "AND kind='noncash_at_ingest'", (DAY,)).fetchone()[0] == 1,
      "AF-37: a second failure did not re-open the same one row")
c.close()

# ---------------------------------------------------------------- 6-12 · ask 3: the two siblings
import code_bundle as CB                                  # noqa: E402

check(hasattr(CB, "s758_summary") and hasattr(CB, "s758_siblings"), "ask 3: code_bundle has no siblings")
c, p = fresh("summary")
prep(c)
FI.ingest_day(c, "medical", DAY, "marg_export", LINES, run_by="walk", source_ref="push:walk", commit=True)
c.close()
os.environ.pop("X", None)
s = CB.s758_summary(p)
raw = json.dumps(s, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
check(isinstance(s.get("tables"), dict) and s["tables"].get("day_entry", 0) >= 1 and "error" not in s["tables"], "ask 3: the table counts: %s" % str(s.get("tables"))[:200])
check(isinstance(s.get("days"), dict) and "error" not in s["days"], "ask 3: the days: %s" % str(s.get("days"))[:200])
check("WALKNAME" not in raw and "PROSIJER" not in raw and "WALK-S1" not in raw, "ask 3: a patient name or a bill number is in the summary")
check(len(raw.encode("utf-8")) < 1024 * 1024, "ask 3: the summary is over 1 MB")
# a made-up bundle and a stand-in Drive
tb = os.path.join(TMP, "b.tar.gz")
with tarfile.open(tb, "w:gz") as tf:
    for name, data in (("root/finance/x.py", b"print(1)\n"), (CB.MANIFEST, ("%s  root/finance/x.py\n" % hashlib.md5(b"print(1)\n").hexdigest()).encode())):
        ti = tarfile.TarInfo(name)
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
txt = CB.s758_md5sums_text(tb, {"files": 1, "tar_md5": "t", "finance_app_md5": "f"})
check(txt.startswith("# code_nightly.MD5SUMS") and "root/finance/x.py" in txt and txt.count("\n") == 2, "ask 3: the MD5SUMS text: %r" % txt[:200])


class FakeDrive:
    def __init__(self, names):
        self.files = {n: {"id": "id_" + n, "name": n} for n in names}
        self.content, self.meta = {}, {}

    def list(self, fid):
        return list(self.files.values())

    def update_content(self, fid, path):
        self.content[fid] = open(path, "rb").read()

    def get(self, fid):
        return {"id": fid, "md5Checksum": hashlib.md5(self.content.get(fid, b"")).hexdigest()}

    def patch_meta(self, fid, body):
        self.meta[fid] = body


CB.OUT_DIR = TMP
CB.S758_DB = p
logs = []
CB.log = lambda *a: logs.append(" ".join(str(x) for x in a))
fd = FakeDrive([CB.S758_SUMS, CB.S758_SUMMARY])
CB.s758_siblings(fd, "folder", tb, {"files": 1, "tar_md5": "t", "finance_app_md5": "f"})
check(len(fd.content) == 2 and json.loads(fd.content["id_" + CB.S758_SUMMARY].decode())["kit"] == "S758"
      and sum("verified by read-back" in l for l in logs) == 2, "ask 3: the two slots were not filled and verified: %s" % logs[-3:])
logs.clear()
fd2 = FakeDrive([])
CB.s758_siblings(fd2, "folder", tb, {"files": 1, "tar_md5": "t", "finance_app_md5": "f"})
check(not fd2.content and sum("missing in the Drive folder" in l for l in logs) == 2, "ask 3: a missing slot is not a plain warning: %s" % logs)

# ---------------------------------------------------------------- 13-15 · AF-36: the health mail's last 24 hours
import clinic_health_report as HR                         # noqa: E402

wl = os.path.join(TMP, "watchdog.log")
now = dt.datetime.now()
with open(wl, "w") as fh:
    fh.write("[2026-07-03 09:00:00] restart clinic-finance (an old one)\n")
    fh.write("[%s] restart wa-receiver (a recent one)\n" % (now - dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"))
    fh.write("[%s] all well, nothing to do\n" % (now - dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))
    fh.write("restart with no time at all\n")
HR.WATCHDOG_LOG = wl
acts = HR.watchdog_actions_last_24h()
check(not any("an old one" in a for a in acts), "AF-36: July's line is still in the last 24 hours: %s" % acts)
check(any("a recent one" in a for a in acts), "AF-36: the recent restart is missing: %s" % acts)
check(not any(a == "restart with no time at all" for a in acts) and any("no readable time" in a for a in acts),
      "AF-36: the undated line: %s" % acts)

shutil.rmtree(TMP, ignore_errors=True)
print("WALK OK %d/%d" % (N["n"], N["n"]))
if CONTROL:
    print("CONTROL: GREEN -- wrong, the control must go red")
    sys.exit(1)

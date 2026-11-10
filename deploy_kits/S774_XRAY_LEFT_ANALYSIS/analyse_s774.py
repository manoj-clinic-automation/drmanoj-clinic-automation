#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""analyse_s774.py -- S774_XRAY_LEFT_ANALYSIS (the parent, S422, 10-Nov-2026). READ-ONLY.
The owner, 13:01 IST: "I do not want to leave any work for staff in Check karein as much as possible."
On a SCRATCH copy of finance.db (made by run_S774.sh, deleted after): plays the S772 filing (the check folder listed from the
copy's own parked rows; no Drive), then sorts every picture STILL parked by why, using the film's dates and IDs (xray_filmdate),
and counts what each candidate extra rule would place. Mails COUNTS ONLY -- no name, no clinic ID, no Drive id.
usage: analyse_s774.py <dir with records.py> <scratch db>"""
import collections
import datetime as dt
import importlib.util
import json
import os
import smtplib
import sqlite3
import sys
import tempfile
from email.mime.text import MIMEText

app, dbp = sys.argv[1], sys.argv[2]
assert "s774" in dbp, "scratch only"
stub = tempfile.mkdtemp(prefix="s774_")
os.environ["RECORDS_DRIVE_STUB"] = stub
sys.path.insert(0, app)
spec = importlib.util.spec_from_file_location("rec774", os.path.join(app, "records.py"))
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
rec.ensure(con)
rec.xray_ensure(con)
inbox, test, check = (rec.setting(con, k) for k in ("xray_inbox_id", "xray_test_id", "xray_check_id"))
for fid in (inbox, test):
    json.dump([], open(os.path.join(stub, "list_%s.json" % fid), "w"))


def listing():
    return [{"id": r["src_id"], "name": r["orig_name"], "mimeType": "image/jpeg", "md5Checksum": "m" + r["src_id"],
             "modifiedTime": rec._s752_utc(r["file_time"]) or "2026-11-09T13:40:00.000Z"}
            for r in con.execute("SELECT src_id, orig_name, file_time FROM xray_filing WHERE state='check'")]


L = []
say = L.append
n0 = con.execute("SELECT COUNT(*) FROM xray_filing WHERE state='check'").fetchone()[0]
for rnd in range(3):                                   # three runs, the mailbox 'doing' each run's items in between
    json.dump(listing(), open(os.path.join(stub, "list_%s.json" % check), "w"))
    items, notes = rec.xray_actions(con)
    done = []
    for i in items:
        if i["action"] == "file":
            done.append({"id": i["id"], "action": "file", "dest_id": "s774DEST" + i["id"][-10:], "name": i["name"]})
        elif i["action"] == "dup":
            done.append({"id": i["id"], "action": "dup"})
    rec.xray_done(con, done)
left = [dict(r) for r in con.execute("SELECT * FROM xray_filing WHERE state='check'")]
say("S774 X-RAY LEFT ANALYSIS -- read-only, scratch copy -- %s IST" % (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).strftime("%d-%b-%Y %H:%M"))
say("parked now %d; after three S772 runs (scratch) still parked %d" % (n0, len(left)))
say("")


def xpats(day):
    return set(rec._s752_day(con, day, {})[0])


def visitors(day):
    s = {r[0] for r in con.execute("SELECT DISTINCT clinic_id FROM slip WHERE day=? AND state='ok' AND clinic_id<>''", (day,))}
    s |= {r[0] for r in con.execute("SELECT DISTINCT clinic_id FROM clinic_day_line WHERE business_date=? AND clinic_id<>''", (day,))}
    return s


def loose(cid, orig):
    st = rec._s752_tokens(rec.xray_stem(orig))
    return bool(st) and any(rec._s752_name_loose(st, rec._s752_tokens(n)) for n in rec._s772_names(con, cid))


def strict(cid, orig):
    return rec._s772_strict(con, cid, orig)


def near_days(d, k=2):
    return [rec._s772_shift(d, i) for i in range(-k, k + 1)]


why = collections.Counter()
rule = collections.Counter()
month = collections.Counter()
for r in left:
    sid, orig = r["src_id"], r["orig_name"] or ""
    first = str(r["file_time"] or r["day"] or "")[:10]
    month[first[:7]] += 1
    fr = rec._s772_film(con, sid)
    fid, how = rec.xray_id(orig)
    has_name = bool(rec._s752_tokens(rec.xray_stem(orig)))
    if fr is None:
        why["film not read"] += 1
        continue
    ds, ids = fr
    ds = [d for d in ds if rec._s772_shift(first, -rec.S772_FILM_WINDOW) <= d <= first]
    if not ds:
        why["no date read on the film"] += 1
        continue
    # what the film's ID says
    xr_hits, vis_hits = set(), set()
    for x in ids:
        for d in ds:
            for dd in near_days(d):
                if x in xpats(dd):
                    xr_hits.add((x, dd))
                elif x in visitors(dd):
                    vis_hits.add((x, dd))
    xs = {x for x, _ in xr_hits}
    if len(xr_hits) == 1:
        x, dd = next(iter(xr_hits))
        one_off = any(rec._s752_one_off(x, o) for o in xpats(dd) if o != x)
        nm = "strict" if strict(x, orig) else ("loose" if loose(x, orig) else ("no name on file" if not has_name else "name differs"))
        why["film ID = one X-ray patient of the film's day; name %s%s" % (nm, "; a neighbour ID that day" if one_off else "")] += 1
        if nm in ("loose", "no name on file") and not one_off:
            rule["R1 film ID + film date (+-2), name loose or none, no one-digit neighbour that day"] += 1
        elif nm == "name differs" and not one_off and fid and fid == x:
            rule["R1b film ID = file ID, film date, name differs"] += 1
        continue
    if len(xr_hits) > 1:
        why["film ID matches several X-ray days/patients"] += 1
        continue
    if vis_hits and len({x for x, _ in vis_hits}) == 1:
        x, dd = sorted(vis_hits)[0]
        nm = "loose" if loose(x, orig) or not has_name else "differs"
        why["film ID visited that day but NO X-ray on slip/Docterz (unbilled?); name %s" % nm] += 1
        if nm == "loose":
            rule["R3 file to the film's ID (visited that day) + an 'X-ray to bill' line for Shavez"] += 1
        continue
    pre = "film ID not seen within 2 days; " if ids else "no film ID; "
    # the name on the film's day
    cands = set()
    for d in ds:
        for p in xpats(d):
            if loose(p, orig):
                cands.add((p, d))
    if not has_name:
        why[pre + "no name on the file"] += 1
    elif len(cands) == 1:
        why[pre + "ONE X-ray patient of the film's day shares a word of the name"] += 1
        rule["R2 one loose name match among the film day's X-ray patients"] += 1
    elif len(cands) > 1:
        why[pre + "several X-ray patients that day share a word"] += 1
    else:
        vc = {(p, d) for d in ds for p in visitors(d) if loose(p, orig)}
        if len(vc) == 1:
            why[pre + "no X-ray patient matches, ONE visitor that day does (unbilled?)"] += 1
            rule["R3b one loose name match among the film day's visitors + 'X-ray to bill'"] += 1
        else:
            why[pre + "nobody that day matches the name (%s)" % ("several visitors" if vc else "none")] += 1

say("== why each is still parked")
for k, v in sorted(why.items(), key=lambda x: -x[1]):
    say("  %3d  %s" % (v, k))
say("")
say("== what each candidate extra rule would place (of the %d)" % len(left))
for k, v in sorted(rule.items()):
    say("  %3d  %s" % (v, k))
say("  %3d  left for a person after all of them" % (len(left) - sum(rule.values())))
say("")
say("== still parked, by the month first seen: %s" % dict(sorted(month.items())))
rep = "\n".join(L)
print(rep)
env = {}
try:
    for raw in open("/root/wa/.env"):
        s = raw.strip()
        if s and not s.startswith("#") and "=" in s:
            k, v = s.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    u, p = env.get("WATCHDOG_SMTP_USER", ""), env.get("WATCHDOG_SMTP_PASS", "")
    if u and p:
        m = MIMEText(rep, "plain", "utf-8")
        m["Subject"], m["From"], m["To"] = "S774 X-ray left analysis -- report", u, env.get("WATCHDOG_SMTP_TO", u)
        s = smtplib.SMTP(env.get("WATCHDOG_SMTP_HOST", "smtp.gmail.com"), int(env.get("WATCHDOG_SMTP_PORT", "587")), timeout=30)
        s.starttls()
        s.login(u, p)
        s.sendmail(u, [x.strip() for x in m["To"].split(",")], m.as_string())
        s.quit()
        print("mail: sent")
except Exception as ex:                                # noqa: BLE001
    print("mail: failed (%s)" % type(ex).__name__)

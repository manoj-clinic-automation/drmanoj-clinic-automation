#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s617.py -- kit S617 (S336, 22-Oct-2026): the set-up cards on /finance/pcs read their 'Now' lines live.

    python3 walk_s617.py OLD NEW [--box]

Made-up files only (a freshness state, a certificate log, an uptime, a folder for the disk): the server, CyberPanel and
website cards carry a 'Now' block that says what those files say -- all on time / late, all healthy / a problem, a check
too old, a file missing -- and every card says when its notes were checked; with those taken out, the page is the old
page plus the Websites card's two new lines and the header's sentence, byte for byte. No password-shaped word.
--box: the same against this machine's real files, read only: none of the live lines says 'could not be read'.
Exit 0 = GREEN (last line 'WALK OK ...'); the S527 file goes RED.
"""
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time

old_p, new_p = sys.argv[1], sys.argv[2]
BOX = "--box" in sys.argv
passed, failed = [], []


def check(c, label):
    (passed if c else failed).append(label)
    print(("  ok   " if c else "  FAIL ") + label)
    return c


def load(p, tag):
    s = importlib.util.spec_from_file_location("sn_" + tag, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


O = load(old_p, "o")
N = load(new_p, "n")
if not check(hasattr(N, "now_html") and hasattr(N, "NOW_FNS"), "the notes read their 'Now' lines"):
    print("WALK RED S617: no live lines (the S527 file)")
    sys.exit(1)
T = tempfile.mkdtemp(prefix="s617_walk_")
try:
    NOW = time.mktime(time.strptime("2099-01-02 03:30:00", "%Y-%m-%d %H:%M:%S"))
    ist = lambda ts: time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts + 19800))
    fr, cl, up = os.path.join(T, "fresh.json"), os.path.join(T, "cert.log"), os.path.join(T, "uptime")
    N.FRESHNESS_STATE, N.CERTWATCH_LOG, N.PROC_UPTIME, N.ROOT_FS = fr, cl, up, T
    for p in (O, N):
        p.PUNCH_CSV = os.path.join(T, "punches.csv")
        p.STAFF_MASTER = os.path.join(T, "sm.csv")
    open(os.path.join(T, "sm.csv"), "w").write("user_id,name\n9001,Walk Staff\n")
    open(os.path.join(T, "punches.csv"), "w").write("x\n")
    os.utime(os.path.join(T, "punches.csv"), (NOW - 3600, NOW - 3600))
    open(up, "w").write("%d.00 123.00\n" % (3 * 86400 + 600))
    json.dump({"last_run_iso": ist(NOW - 1800), "legs_checked": 34, "not_ok_legs": []}, open(fr, "w"))
    cstamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(NOW + 19800 - 3 * 3600))
    open(cl, "w").write("[%s IST] CHECK all 8 watched sites healthy\n" % cstamp)

    h = N.section(NOW)
    t = re.sub(r"<[^>]+>", " ", h)
    t = re.sub(r"\s+", " ", t.replace("&mdash;", "-"))
    check(h.count("<div class=now>") == 3, "three cards carry a Now block (the server, CyberPanel, the websites)")
    check(h.count("Notes checked 22-Oct-2026.") == len(N.CARDS), "every set-up card says when its notes were checked (%d)" % len(N.CARDS))
    check("GB free of" in t and "% used)" in t, "the disk, read now")
    check("Running since" in t and "(3 days)" in t, "how long the server has been running (3 days)")
    check("all 34 on time at the check of" in t and "has not reported for over three hours" not in t, "the nightly jobs: all 34 on time")
    check(t.count("Certificates (the padlock): all 8 clinic addresses healthy at the check of") == 2,
          "this morning's certificate check, on both CyberPanel and the websites")
    check("clinic Gmail" in t and "FTP is off (since 18-Oct)" in t, "the Websites card: mail through the clinic Gmail, the vendor's FTP off")
    check("updates its card the same day" in t, "the page says a change to a set-up updates its card")
    # late jobs, a problem certificate, both checks old
    json.dump({"last_run_iso": ist(NOW - 5 * 3600), "legs_checked": 34,
               "not_ok_legs": [{"name": "clinic state backup (off-box)"}, "punch file"]}, open(fr, "w"))
    open(cl, "w").write("[%s IST] CHECK all 8 watched sites healthy\n[%s IST] CHECK 1 problem(s): drmanojagarwal.com|WARN\n"
                        % (cstamp, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(NOW + 19800 - 40 * 3600))))
    t2 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", N.section(NOW)).replace("&mdash;", "-"))
    check("2 of 34 late or missing" in t2 and "clinic state backup (off-box), punch file" in t2 and "has not reported for over three hours" in t2,
          "late jobs are named, and an old check says so")
    check("1 problem(s): drmanojagarwal.com|WARN" in t2 and "more than a day old" in t2,
          "the newest certificate line is the one shown, and an old one says so")
    for f in (fr, cl, up):
        os.remove(f)
    N.ROOT_FS = os.path.join(T, "no-such")
    t3 = N.section(NOW)
    check(t3.count("could not be read just now") >= 4 and t3.count("<div class=now>") == 3,
          "every missing file says so in words, and the page still renders")
    # with the S617 additions taken out, the old page byte for byte
    json.dump({"last_run_iso": ist(NOW), "legs_checked": 1, "not_ok_legs": []}, open(fr, "w"))
    hn = N.section(NOW)
    ho = O.section(NOW)
    hn = re.sub(r"<div class=now>.*?</div>", "", hn, flags=re.S).replace("<p class=kit>Notes checked 22-Oct-2026.</p>", "")
    hn = hn.replace(" The lines marked <b>Now</b> are read from the server each time this page opens; each card says when its "
                    "notes were last checked, and a change to a set-up updates its card the same day.", "")
    hn = re.sub(r"<li><b>Its mail</b>.*?</li><li>The website vendor's FTP login.*?</li>", "", hn, flags=re.S)
    css_n = re.search(r"<style>(.*?)</style>", hn, re.S).group(1)
    hn = hn.replace(css_n, re.sub(r"\.now\{.*?\.now b\{color:#fff\}", "", css_n, flags=re.S))
    check(hn == ho, "with the additions taken out, the page is the old page byte for byte")
    check(not re.search(r"(?i)password\s*[:=]|passwd|token\s*[:=]|BEGIN [A-Z ]*PRIVATE KEY", N.section(NOW)),
          "no password-, token- or key-shaped text on the page")
finally:
    shutil.rmtree(T, ignore_errors=True)

if BOX:
    L = load(new_p, "box")
    hb = L.section()
    nows = re.findall(r"<div class=now>(.*?)</div>", hb, re.S)
    check(len(nows) == 3 and not any("could not be read" in x for x in nows),
          "on this machine every live line reads (%s)" % "; ".join(re.sub(r"<[^>]+>", "", x)[:90] for x in nows[:1]))
print("")
print(("WALK OK" if not failed else "WALK RED") + " S617: %d passed, %d failed" % (len(passed), len(failed)))
sys.exit(0 if not failed else 1)

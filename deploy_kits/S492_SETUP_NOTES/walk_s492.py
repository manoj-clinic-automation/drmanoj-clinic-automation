#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s492.py -- S492_SETUP_NOTES (session 298, 07-Oct-2026). Hermetic (F-709): pc_kits.py is copied to a scratch folder
and edited there; three throwaway Flask apps (the file as it is, the edited file with the notes, the edited file WITHOUT
the notes); a made-up owner login; an empty scratch kits root; a scratch punch file whose age the walk sets itself.
Nothing on the box is written and no real file is read except pc_kits.py and this kit's own files.

  1. the three edits apply to the real bytes and give the predicted bytes.
  2. the page, as the owner: everything that was on it is still on it, in the same order; then 'Other set-ups' with the
     biometric card (seven folded blocks -- the menu, the reset steps numbered -- and the not-written-down list) and the five
     'To be built' lines.
  3. the punch file: fresh -> 'Punches arriving' with its day; five days old -> 'Needs a look'; unreadable -> 'No record'
     -- and its age asked in four time zones (the box's own, India, UTC, Los Angeles), because the first install went red
     on exactly that: right in UTC, five and a half hours short on the box.
     The codes: a made-up staff list shows code and name only, in code order, a name escaped, no other column; an
     unreadable list says so in words.
  4. not the owner -> 403 and not one word of the notes.
  5. nothing secret-shaped in the section; every link goes to one of five known places; the HTML closes what it opens.
  6. the guards: without setup_notes.py the edited page is BYTE-FOR-BYTE the page of the file as it is today; a note that
     raises leaves the page whole.
Last line: WALK_S492 GREEN|RED.
   usage: walk_s492.py --apply apply_s492.py --notes setup_notes.py --finance /root/finance --to <md5 the edit must give>
"""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

FAILS, CHECKS = [], 0
OWNER = [True]


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name)
        print("  FAIL %s %s" % (name, str(detail)[:400]))


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def load(folder, name, dbp):
    """pc_kits.py of `folder` as its own module, mounted in its own throwaway app; returns (module, test client).
    Only `folder` may supply setup_notes.py: every other place on the path that holds one (this kit's own folder, where
    this script lives) is taken off the path while the module loads, so 'without the notes' is really without them."""
    from flask import Flask
    for m in [k for k in sys.modules if k == "setup_notes"]:
        del sys.modules[m]
    saved = list(sys.path)
    sys.path[:] = [folder] + [q for q in saved if not os.path.exists(os.path.join(q or os.getcwd(), "setup_notes.py"))]
    try:
        spec = importlib.util.spec_from_file_location(name, os.path.join(folder, "pc_kits.py"))
        K = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(K)
    finally:
        sys.path[:] = saved
    app = Flask(name)

    def dbf():
        c = sqlite3.connect(dbp, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def require(*roles, **kw):
        if OWNER[0]:
            return {"user": "wmanoj", "role": "checker", "roles": ["checker"]}, None
        return None, ("not permitted", 403)

    K.init(app, dbf, require, lambda con: {"checks": []})
    return K, app.test_client()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--notes", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--to", required=True)
    ap.add_argument("--save", default="")
    a = ap.parse_args()
    live = os.path.join(a.finance, "pc_kits.py")
    before = md5(live)
    scr = tempfile.mkdtemp(prefix="s492_walk_")
    try:
        old, new, bare = (os.path.join(scr, d) for d in ("old", "new", "bare"))
        for d in (old, new, bare):
            os.makedirs(d)
            shutil.copy2(live, os.path.join(d, "pc_kits.py"))
        for d in (new, bare):
            r = subprocess.run([sys.executable, "-B", a.apply, os.path.join(d, "pc_kits.py")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            check("1 the edits apply (%s)" % os.path.basename(d), r.returncode == 0, r.stderr.decode()[-300:])
        check("1 the edited file is its predicted bytes", md5(os.path.join(new, "pc_kits.py")) == a.to, md5(os.path.join(new, "pc_kits.py")))
        r = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "pc_kits.py")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("1 a second apply refuses and writes nothing", r.returncode != 0 and md5(os.path.join(new, "pc_kits.py")) == a.to)
        shutil.copy2(a.notes, os.path.join(new, "setup_notes.py"))

        kits = os.path.join(scr, "kits"); os.makedirs(kits)
        dbp = os.path.join(scr, "finance.db")
        con = sqlite3.connect(dbp)
        con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        con.execute("CREATE TABLE bank_sms_settlement (id INTEGER PRIMARY KEY, received_at TEXT)")
        con.execute("CREATE TABLE bank_sms_yes (id INTEGER PRIMARY KEY, received_at TEXT)")
        con.commit(); con.close()
        punch = os.path.join(scr, "punches.csv")
        open(punch, "w").write("user_id,datetime,io_mode,verify_mode,received_at\n")
        os.environ["PC_KITS_ROOT"] = kits
        os.environ["PC_KIT_LOG"] = os.path.join(scr, "pc_kit_log.txt")
        os.environ["PC_KIT_CODES"] = os.path.join(scr, "pc_kit_codes.json")
        os.environ["ATT_PUNCH_CSV"] = punch
        master = os.path.join(scr, "staff_master.csv")
        open(master, "w", encoding="utf-8").write("user_id,name,department,base_salary\n101,Walk Person,Front,987654\n17,Old <b>Hand</b>,Back,123456\nx,No Code,Back,1\n")
        os.environ["ATT_STAFF_MASTER"] = master

        Kold, c_old = load(old, "pc_kits_old", dbp)
        Kbare, c_bare = load(bare, "pc_kits_bare", dbp)
        check("6 without setup_notes.py the module still loads, the notes are None", getattr(Kbare, "_setup_notes", 0) is None)
        Knew, c_new = load(new, "pc_kits_new", dbp)
        check("2 with setup_notes.py the module loads it", getattr(Knew, "_setup_notes", None) is not None)

        # 2 the page as the owner
        p_old = c_old.get("/finance/pcs").get_data(as_text=True)
        r = c_new.get("/finance/pcs")
        page = r.get_data(as_text=True)
        check("2 the page answers 200", r.status_code == 200, r.status_code)
        cut = page.find("<style>.sn{")
        end = page.find("<p class=how>")
        check("2 the section sits after the phones and before the closing paragraph", 0 < page.find("Reception mobile") < cut < end, (cut, end))
        sec = page[cut:end]
        check("2 taking the section out gives the old page, byte for byte", page[:cut] + page[end:] == p_old)
        for w in ("<h1 style='margin-top:18px'>Other set-ups</h1>", "No password, PIN or key is ever written on this page",
                  "Biometric attendance machine", "Secureye S-B251CB/WiFi", "How it is set up", "What uses the punches", "If something goes wrong",
                  "Adding or removing a person", "After a factory reset, or with a replacement machine", "The codes to enrol with",
                  "The machine&#x27;s menu, and where each thing is", "1 Register \u00b7 2 Set COMM \u00b7 3 Set time \u00b7 4 Advanced \u00b7 5 Set bell \u00b7 6 ViewInfo",
                  "MENU \u2192 2 Set COMM \u2192 2 TCP/IP..", "MENU \u2192 3 Set time", "MENU \u2192 1 Register \u2192 1 New Reg.",
                  "1 Delete All Rec \u00b7 2 All Delete Data \u00b7 3 Default Setting \u00b7 4 Update Firmware", "Machine ID 1", "DateFormat YMD",
                  "by their names", "Nothing was pressed to test this", "All EnrollData and Upload Reg. Data",
                  "Not written down yet", "<pre class=cp>systemctl restart attlistener</pre>", "<b>2209031616</b>", "at reception",
                  "Airtel_Airtrl_mano_8080", "Server Set", "<b>093.127.195.049</b>", "<b>8041</b>", "DHCP <b>Yes</b>", "BL Computers",
                  "Its menu opens with your finger", "with the code they had", "To be built", "Hostinger", "CyberPanel", "SSH login",
                  "Websites", "Bitwarden"):
            check("2 the section says %r" % w[:44], w in sec)
        check("2 seven folded blocks", sec.count("<details class=sn>") == 7 and sec.count("</details>") == 7, sec.count("<details"))
        ol = sec[sec.find("<ol>"):sec.find("</ol>")]
        check("2 the reset steps are numbered, eleven of them: what a reset is, then Wi-Fi, the server, the clock, the settings, the fingers, the test", sec.count("<ol>") == 1 and ol.count("<li>") == 11
              and 0 < ol.find("<b>What a reset is on this machine.</b>") < ol.find("<b>Wi-Fi.</b>") < ol.find("<b>The server.</b>") < ol.find("<b>The clock.</b>") < ol.find("<b>General Setting.</b>")
              < ol.find("<b>Your finger first.</b>") < ol.find("with the code they had") < ol.find("One test punch"), ol.count("<li>"))
        check("2 the label's network address is not on the page", not re.search(r"(?i)\b([0-9a-f]{2}[-:]){5}[0-9a-f]{2}\b", sec))
        check("2 five 'To be built' lines, each its own row", sec.count("<span class='st info'>To be built</span>") == 5 and sec.count("<div class=tb>") == 5, sec.count("To be built</span>"))
        check("2 one thing not written down yet", sec.count("<li>", sec.find("Not written down yet")) - sec.count("<li>", sec.find("<div class=tb>")) == 1)
        cod = sec[sec.find("The codes to enrol with"):sec.find("Not written down yet")]
        check("3 the codes: code and name only, in code order, the name escaped", "<div><b>17</b> Old &lt;b&gt;Hand&lt;/b&gt;</div><div><b>101</b> Walk Person</div>" in cod, cod[-300:])
        check("3 the codes: no other column of the staff list, no row without a code", "987654" not in sec and "123456" not in sec and "Front" not in sec and "No Code" not in sec)
        Knew._setup_notes.STAFF_MASTER = os.path.join(scr, "not_there.csv")
        sx = c_new.get("/finance/pcs").get_data(as_text=True)
        check("3 the codes: an unreadable staff list says so in words, the page whole", "could not read its staff list" in sx and "Walk Person" not in sx and sx.count("<details class=sn>") == 7)
        Knew._setup_notes.STAFF_MASTER = master
        # 3 the punch file
        day = time.strftime("%d-%b", time.gmtime(os.path.getmtime(punch) + 19800))
        check("3 fresh: 'Punches arriving' with its day", "<span class='st ok'>Punches arriving</span>" in sec and ("The last punch reached the server on %s " % day) in sec)
        # the age of the punch file must not depend on the box's time zone (the first install, 07-Oct-2026: right in UTC,
        # five and a half hours short in India time) -- so it is asked in three zones, the box's own first
        zone0 = os.environ.get("TZ")
        for zone in (None, "Asia/Kolkata", "UTC", "America/Los_Angeles"):
            if zone is not None:
                os.environ["TZ"] = zone
                time.tzset()
            t1 = time.time() - 600
            os.utime(punch, (t1, t1))
            s1 = c_new.get("/finance/pcs").get_data(as_text=True)
            when = time.strftime("%d-%b %H:%M", time.gmtime(t1 + 19800))
            check("3 ten minutes old (%s): 'Punches arriving', the time in India time" % (zone or "the box's zone"),
                  "<span class='st ok'>Punches arriving</span>" in s1 and ("The last punch reached the server on %s." % when) in s1, when)
            t5 = time.time() - 5 * 86400 - 600
            os.utime(punch, (t5, t5))
            s5 = c_new.get("/finance/pcs").get_data(as_text=True)
            check("3 five days old (%s): 'Needs a look', says since when" % (zone or "the box's zone"),
                  "<span class='st warn'>Needs a look</span>" in s5 and "No punch has reached the server since" in s5 and "(5 days)" in s5)
            t3 = time.time() - 74 * 3600 + 900
            os.utime(punch, (t3, t3))
            s3 = c_new.get("/finance/pcs").get_data(as_text=True)
            check("3 a quarter-hour inside the 74 hours (%s): still 'Punches arriving'" % (zone or "the box's zone"), "<span class='st ok'>Punches arriving</span>" in s3)
        if zone0 is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = zone0
        time.tzset()
        os.remove(punch)
        s0 = c_new.get("/finance/pcs").get_data(as_text=True)
        check("3 unreadable: 'No record', in words", "<span class='st info'>No record</span>" in s0 and "could not read its punch file" in s0)
        # 4 not the owner
        OWNER[0] = False
        r = c_new.get("/finance/pcs")
        body = r.get_data(as_text=True)
        check("4 not the owner: 403 and not a word of the notes", r.status_code == 403 and "Biometric" not in body and "Other set-ups" not in body and "8041" not in body, r.status_code)
        OWNER[0] = True
        # 5 nothing secret-shaped; known links only; the HTML closes
        text = re.sub(r"<style>.*?</style>", "", sec, flags=re.S)
        bad = re.findall(r"\b[6-9][0-9]{9}\b", text) + re.findall(r"\b[0-9a-f]{32,}\b", text) + re.findall(r"(?i)(password|pin|token|key)\s*[:=]\s*\S+", text)
        check("5 no number, no hash, no credential-shaped text", not bad, str(bad)[:200])
        hrefs = set(re.findall(r"href='([^']+)'", sec))
        check("5 only the five known links", hrefs == {"https://attendance.dr-manoj.in", "/register/review", "/register/salary", "/finance/freshness"} or
              hrefs <= {"https://attendance.dr-manoj.in", "/register/review", "/register/salary", "/finance/freshness", "/finance/health"}, str(hrefs))
        for tag in ("div", "details", "ul", "ol", "li", "p", "span", "pre", "summary", "b", "a", "i"):
            check("5 <%s> closes" % tag, len(re.findall(r"<%s[\s>]" % tag, sec)) == sec.count("</%s>" % tag), (tag, len(re.findall(r"<%s[\s>]" % tag, sec)), sec.count("</%s>" % tag)))
        check("5 no form, no script, no input in the section", not re.search(r"<(form|script|input|button|iframe)\b", sec))
        # 6 the guards
        p_bare = c_bare.get("/finance/pcs").get_data(as_text=True)
        check("6 without setup_notes.py: the page of today, byte for byte", p_bare == p_old)

        def boom(*a_, **k_):
            raise RuntimeError("walk")
        keep = Knew._setup_notes.section
        Knew._setup_notes.section = boom
        r = c_new.get("/finance/pcs")
        check("6 a note that raises: the page whole, 200, as today", r.status_code == 200 and r.get_data(as_text=True) == p_old, r.status_code)
        Knew._setup_notes.section = keep
        for path, want in (("/finance/api/pc-kit/fetch?part=kit", 401), ("/finance/pcs/phone/nophone", 405)):
            check("6 the other doors answer as before: %s" % path, c_new.get(path).status_code == c_old.get(path).status_code == want, c_new.get(path).status_code)
        if a.save:
            open(punch, "w").write("x\n")
            open(a.save, "w", encoding="utf-8").write(c_new.get("/finance/pcs").get_data(as_text=True))
        check("hermetic: the box's pc_kits.py untouched", md5(live) == before)
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S492 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()

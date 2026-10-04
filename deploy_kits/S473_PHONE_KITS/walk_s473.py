#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s473.py -- S473_PHONE_KITS (session 293, 04-Oct-2026). Hermetic (F-709): pc_kits.py copied to a scratch folder and
edited there, a throwaway Flask app with a made-up owner login, a scratch kits root holding the two templates, a scratch
database, a made-up bank-SMS key module and a made-up phone token (both made at run time -- never a real one, none written).

  1. the two templates: whole (md5 = KIT_INFO), each placeholder present, NO key-shaped string, no geofence, only the server's
     and wa.me addresses.
  2. the page: 'Phones', both cards, a button each, what the server last heard, the person-lists.
  3. the press: the fold phone's file is MacroDroid_DrManojPhone_<date>.mdr, valid JSON, 2 macros, the made-up key in both
     HTTP actions, no placeholder left; the reception file carries the made-up token; both logged.
  4. refusals: a cross-site press 403 (no file); an unknown phone 404; a box that cannot read the key 503 (no file).
Last line: WALK_S473 GREEN|RED.
   usage: walk_s473.py --apply apply_s473.py --finance /root/finance --kits <deploy_kits/PC_KITS folder of this kit's repo>
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types

FAILS, CHECKS = [], 0


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name)
        print("  FAIL %s %s" % (name, str(detail)[:400]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--kits", required=True)
    a = ap.parse_args()
    scr = tempfile.mkdtemp(prefix="s473_walk_")
    try:
        new = os.path.join(scr, "new"); os.makedirs(new)
        shutil.copy2(os.path.join(a.finance, "pc_kits.py"), os.path.join(new, "pc_kits.py"))
        r = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "pc_kits.py")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("apply on scratch", r.returncode == 0, r.stderr.decode()[-300:])
        # 1 the templates
        kits = os.path.join(scr, "kits"); shutil.copytree(a.kits, kits)
        for ph, placeholder, n_macros in (("foldphone", "{{BANK_SMS_KEY}}", 2), ("receptionmobile", "{{PHONE_TOKEN}}", 1)):
            d = os.path.join(kits, "macrodroid", ph)
            info = dict(l.strip().split("=", 1) for l in open(os.path.join(d, "KIT_INFO.txt"), encoding="utf-8") if "=" in l and not l.startswith("#"))
            raw = open(os.path.join(d, "macros.template.mdr"), "rb").read()
            s = raw.decode("utf-8")
            check("1 %s template whole (md5 = KIT_INFO)" % ph, hashlib.md5(raw).hexdigest() == info.get("template_md5"), info.get("template_md5"))
            check("1 %s carries its placeholder twice" % ph, s.count(placeholder) == 2, s.count(placeholder))
            check("1 %s has %d macro(s)" % (ph, n_macros), len(json.loads(s)["macroList"]) == n_macros)
            bad = re.findall(r'[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}', s) + re.findall(r'\b[0-9a-f]{40,}\b', s) + re.findall(r'\b[6-9][0-9]{9}\b', s)
            check("1 %s carries no key-shaped string, no number" % ph, not bad, len(bad))
            check("1 %s geofence empty" % ph, json.loads(s).get("geofenceData", {}).get("geofenceMap", {}) == {})
            urls = set(re.findall(r'https?://[^"\s{]+', s))
            check("1 %s only the server's and wa.me addresses" % ph, all(u.startswith("https://followup.dr-manoj.in/") or u.startswith("https://wa.me/") for u in urls), str(urls))
        # the throwaway app
        dbp = os.path.join(scr, "finance.db")
        con = sqlite3.connect(dbp)
        con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        con.execute("CREATE TABLE bank_sms_settlement (id INTEGER PRIMARY KEY, received_at TEXT)")
        con.execute("CREATE TABLE bank_sms_yes (id INTEGER PRIMARY KEY, received_at TEXT)")
        tok = "walk-" + secrets.token_hex(12)
        con.execute("INSERT INTO setting VALUES ('supplier_msg.phone_token', ?, 'walk')", (tok,))
        con.execute("INSERT INTO setting VALUES ('supplier_msg.phone_last', '2026-10-04T08:15:00 200', 'walk')")
        con.execute("INSERT INTO bank_sms_settlement (received_at) VALUES ('2026-10-04 06:58:11')")
        con.commit(); con.close()
        key = "walk-" + secrets.token_hex(10)
        fake_bs = types.ModuleType("bank_sms"); fake_bs._key = lambda: key
        sys.modules["bank_sms"] = fake_bs
        os.environ["PC_KITS_ROOT"] = kits
        os.environ["PC_KIT_LOG"] = os.path.join(scr, "pc_kit_log.txt")
        os.environ["PC_KIT_CODES"] = os.path.join(scr, "pc_kit_codes.json")
        sys.path.insert(0, new)
        spec = importlib.util.spec_from_file_location("pc_kits_walk", os.path.join(new, "pc_kits.py"))
        K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
        from flask import Flask
        app = Flask("walk473")
        def dbf():
            c = sqlite3.connect(dbp, check_same_thread=False); c.row_factory = sqlite3.Row; return c
        K.init(app, dbf, lambda *roles, **kw: ({"user": "wmanoj", "role": "checker", "roles": ["checker"]}, None), lambda con: {"checks": []})
        c = app.test_client()
        # 2 the page
        r = c.get("/finance/pcs")
        page = r.get_data(as_text=True)
        check("2 the page answers", r.status_code == 200, r.status_code)
        for w in ("Clinic PCs &amp; phones", "<h1 style='margin-top:18px'>Phones</h1>", "Dr Manoj’s phone (Fold)", "Reception mobile", "last bank SMS received 04-Oct 06:58",
                  "last asked the order queue 04-Oct 08:15 (answered)", "Install MacroDroid", "Also on this phone"):
            check("2 the page says %r" % w[:40], w in page)
        check("2 two phone buttons", page.count("Set up this phone again") == 2, page.count("Set up this phone again"))
        # 3 the press
        same = {"Sec-Fetch-Site": "same-origin"}
        r = c.post("/finance/pcs/phone/foldphone", headers=same)
        body = r.get_data()
        check("3 fold press 200, octet-stream", r.status_code == 200 and r.mimetype == "application/octet-stream", r.status_code)
        check("3 fold file name", re.fullmatch(r'attachment; filename="MacroDroid_DrManojPhone_\d{8}\.mdr"', r.headers.get("Content-Disposition", "")) is not None, r.headers.get("Content-Disposition"))
        j = json.loads(body.decode("utf-8"))
        vals = [h["paramValue"] for m in j["macroList"] for act in m["m_actionList"] for h in act.get("requestConfig", {}).get("headerParams", []) if h["paramName"] == "X-Bank-Sms-Key"]
        check("3 the made-up key is in both HTTP actions, no placeholder left", vals == [key, key] and "{{BANK_SMS_KEY}}" not in body.decode("utf-8"), str(len(vals)))
        check("3 fold file has 2 macros, the retired one gone", [m["m_name"] for m in j["macroList"]] == ["Bank SMS to Clinic Server", "Bank SMS 2 ( Yes Bank) to Clinic Server"])
        r = c.post("/finance/pcs/phone/receptionmobile", headers=same)
        s2 = r.get_data(as_text=True)
        j2 = json.loads(s2)
        vals2 = [h["paramValue"] for m in j2["macroList"] for act in m["m_actionList"] for h in act.get("requestConfig", {}).get("headerParams", []) if h["paramName"] == "X-Phone-Token"]
        check("3 reception file carries the made-up token twice, no placeholder", r.status_code == 200 and vals2 == [tok, tok] and "{{PHONE_TOKEN}}" not in s2, str(len(vals2)))
        log = open(os.environ["PC_KIT_LOG"], encoding="utf-8").read() if os.path.exists(os.environ["PC_KIT_LOG"]) else ""
        check("3 both presses logged, no key in the log", log.count("the MacroDroid file was made") == 2 and key not in log and tok not in log, log[-300:])
        # 4 refusals
        r = c.post("/finance/pcs/phone/foldphone", headers={"Sec-Fetch-Site": "cross-site"})
        check("4 a cross-site press is refused (403, no file)", r.status_code == 403 and b"macroList" not in r.get_data())
        r = c.post("/finance/pcs/phone/nophone", headers=same)
        check("4 an unknown phone 404", r.status_code == 404)
        fake_bs._key = lambda: ""
        r = c.post("/finance/pcs/phone/foldphone", headers=same)
        check("4 a box that cannot read the key: 503, no file", r.status_code == 503 and b"macroList" not in r.get_data(), r.status_code)
        check("hermetic: the box's pc_kits.py untouched", hashlib.md5(open(os.path.join(a.finance, "pc_kits.py"), "rb").read()).hexdigest() == K.__dict__.get("__walk_from__", hashlib.md5(open(os.path.join(a.finance, "pc_kits.py"), "rb").read()).hexdigest()))
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S473 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()

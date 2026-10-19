#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""setup_s599.py -- kit S599_WA_INBOX_TEMPLATES_STAFF (session S329, 19-Oct-2026) · D744.

    setup_s599.py check   -- read-only: every WhatsApp key the server holds, held against MyOperator (a read of the
                             approved-template list -- nothing is sent); the portal's live template switch and key
    setup_s599.py apply   -- write /root/wa/wa_inbox/config.json (names the proved key's SOURCE, never the key) and set
                             the portal's template switch live (and its key, if the portal's own is the refused one)
    setup_s599.py test    -- two real messages to the owner's OWN number: one text from the inbox, one approved template
                             (drmanoj_post_visit, name "Test"); then the staff replies brought in from the portal log and sheet
    setup_s599.py undo    -- portal_config.py and config.json back as they were

No key is ever printed; a key is named by where it lives. The owner's number is shown by its last 4 digits only.
"""
import os, re, sys, json, shutil, hashlib, datetime, subprocess, urllib.request, urllib.error

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
PORTAL_DIR = os.environ.get("S599_PORTAL_DIR", "/root/portal")
PCFG = os.path.join(PORTAL_DIR, "portal_config.py")
STORE = os.environ.get("INBOX_STORE", "/root/wa/wa_inbox")
CONFIG = os.path.join(STORE, "config.json")
BK = os.environ.get("S599_BACKUP", "/root/s599_backup")
CHECK_URL = os.environ.get("S599_CHECK_URL", "https://publicapi.myoperator.co/chat/templates")
COMPANY_ID = "68384350414b9847"
WABA_ID_DEFAULT = "2101222617483538"
SOURCES = ["env:/root/wa/.env:MYOP_AUTH_TOKEN", "env:/root/wa/wa_approve.env:MYOP_AUTH_TOKEN", "wa_send", "portal:MYOP_AUTH_TOKEN"]
sys.path.insert(0, PORTAL_DIR)
sys.path.append("/root/wa")


def die(msg, changed=False):
    print("!! STOPPED: %s" % msg)
    print("   %s Send a photo of this screen to Claude." % ("Check the lines above." if changed else "Nothing was changed."))
    sys.exit(1)


def read_env(path):
    vals = {}
    try:
        for raw in open(path, encoding="utf-8"):
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return vals


def portal_effective():
    """The template switch and key exactly as the RUNNING portal sees them: portal_config.py first, else its own environment."""
    env = {}
    try:
        pid = subprocess.run(["systemctl", "show", "-p", "MainPID", "--value", "clinic-portal"], capture_output=True,
                             text=True, timeout=10).stdout.strip()
        if pid and pid != "0":
            raw = open("/proc/%s/environ" % pid, "rb").read().split(b"\0")
            env = dict(x.decode("utf-8", "replace").split("=", 1) for x in raw if b"=" in x)
    except Exception:                                                   # noqa: BLE001
        env = {}
    cfg = {}
    if os.path.exists(PCFG):
        code = ("import json,sys;sys.path.insert(0,%r);import portal_config as c;"
                "print(json.dumps({k:getattr(c,k,None) for k in ('PORTAL_WA_DRYRUN','MYOP_AUTH_TOKEN')}))" % PORTAL_DIR)
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
        if p.returncode == 0:
            try:
                cfg = json.loads(p.stdout.strip().splitlines()[-1])
            except Exception:                                           # noqa: BLE001
                cfg = {}
    def get(k, d=""):
        v = cfg.get(k)
        return v if v else env.get(k, d)
    return {"dry": str(get("PORTAL_WA_DRYRUN", "1") or "1"), "token": get("MYOP_AUTH_TOKEN", ""),
            "dry_from": "portal_config.py" if cfg.get("PORTAL_WA_DRYRUN") else ("the service environment" if env.get("PORTAL_WA_DRYRUN") else "the default"),
            "has_cfg": os.path.exists(PCFG)}


def token_from(src, eff):
    kind, _, rest = src.partition(":")
    if kind == "env":
        path, _, name = rest.rpartition(":")
        return read_env(path).get(name, "")
    if kind == "portal":
        return eff["token"]
    if kind == "wa_send":
        try:
            import wa_send
            return wa_send.load_config().get("token") or ""
        except Exception:                                               # noqa: BLE001
            return ""
    return ""


def key_works(tok):
    waba = read_env("/root/wa/.env").get("MYOP_WABA_ID") or WABA_ID_DEFAULT
    url = "%s?waba_id=%s&waba_template_status=approved&limit=1&offset=0" % (CHECK_URL, waba)
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("X-MYOP-COMPANY-ID", COMPANY_ID)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200, r.status
    except urllib.error.HTTPError as e:
        return False, e.code
    except Exception as e:                                              # noqa: BLE001
        return False, type(e).__name__


def check(quiet=False):
    eff = portal_effective()
    seen, results = {}, []
    for src in SOURCES:
        tok = token_from(src, eff)
        if not tok:
            results.append((src, None, "absent"))
            continue
        h = hashlib.sha256(tok.encode()).hexdigest()[:12]
        if h in seen:
            results.append((src, seen[h][0], "same key as %s" % seen[h][1]))
            continue
        ok, code = key_works(tok)
        seen[h] = (ok, src)
        results.append((src, ok, "works" if ok else "refused (%s)" % code))
    good = [s for s, ok, _ in results if ok]
    portal_ok = None
    if eff["token"]:
        ph = hashlib.sha256(eff["token"].encode()).hexdigest()[:12]
        portal_ok = seen.get(ph, (None,))[0]
    if not quiet:
        names = {"env:/root/wa/.env:MYOP_AUTH_TOKEN": "/root/wa/.env MYOP_AUTH_TOKEN",
                 "env:/root/wa/wa_approve.env:MYOP_AUTH_TOKEN": "/root/wa/wa_approve.env MYOP_AUTH_TOKEN",
                 "wa_send": "the text sender's key (WA_SEND_TOKEN chain)", "portal:MYOP_AUTH_TOKEN": "the portal's own key"}
        for s, ok, why in results:
            print("    %-46s %s" % (names[s], why))
        print("    the portal's template switch: %s (%s)" % ("LIVE" if eff["dry"] == "0" else "TEST MODE", eff["dry_from"]))
    return good, eff, portal_ok


def py_literal_edit(text, name, value):
    """Set NAME = value in portal_config.py: replace the one existing top-level line, or append. Refuses two lines."""
    pat = re.compile(r"^%s\s*=.*$" % re.escape(name), re.M)
    hits = pat.findall(text)
    if len(hits) > 1:
        raise ValueError("portal_config.py sets %s on more than one line" % name)
    line = "%s = %r   # S599 (D744, 19-Oct-2026)" % (name, value)
    if hits:
        return pat.sub(lambda m: line, text, count=1)
    return text.rstrip("\n") + "\n\n" + line + "\n"


def apply():
    good, eff, portal_ok = check()
    if not good:
        die("no WhatsApp key on the server is accepted by MyOperator -- the inbox and the templates cannot send")
    src = good[0]
    os.makedirs(STORE, mode=0o700, exist_ok=True)
    os.makedirs(BK, mode=0o700, exist_ok=True)
    cb = os.path.join(BK, "config.json.before_s599")
    if not os.path.exists(cb) and not os.path.exists(cb + ".ABSENT"):
        try:
            mine = json.load(open(CONFIG)).get("kit") == "S599"
        except Exception:                                               # noqa: BLE001
            mine = False
        if os.path.exists(CONFIG) and not mine:
            shutil.copy2(CONFIG, cb)
        elif not os.path.exists(CONFIG):
            open(cb + ".ABSENT", "w").close()
    old = os.umask(0o077)
    try:
        with open(CONFIG, "w") as fh:
            json.dump({"token_source": src, "proved_at": datetime.datetime.now(IST).isoformat(timespec="seconds"),
                       "kit": "S599"}, fh, indent=1)
    finally:
        os.umask(old)
    print("    the inbox now uses: %s (written to %s -- the key's place, not the key)" % (src, CONFIG))
    text = open(PCFG, encoding="utf-8").read() if eff["has_cfg"] else ""
    new = text
    if eff["dry"] != "0":
        new = py_literal_edit(new, "PORTAL_WA_DRYRUN", "0")
    if portal_ok is not True:
        good_tok = token_from(src, eff)
        new = py_literal_edit(new, "MYOP_AUTH_TOKEN", good_tok)
    if new == text:
        print("    portal_config.py: nothing to change (templates already live, its key already works)")
        return
    b = os.path.join(BK, "portal_config.py.before_s599")
    if not os.path.exists(b):
        if eff["has_cfg"]:
            shutil.copy2(PCFG, b)
        else:
            open(b + ".ABSENT", "w").close()
        os.chmod(b if eff["has_cfg"] else b + ".ABSENT", 0o600)
    tmp = PCFG + ".s599tmp"
    old = os.umask(0o077)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(new)
    finally:
        os.umask(old)
    p = subprocess.run([sys.executable, "-c", "import py_compile,sys;py_compile.compile(sys.argv[1],doraise=True)", tmp],
                       capture_output=True, text=True)
    if p.returncode != 0:
        os.remove(tmp)
        die("the edited portal_config.py would not compile")
    if eff["has_cfg"]:
        os.chmod(tmp, os.stat(PCFG).st_mode & 0o7777)
    os.replace(tmp, PCFG)
    eff2 = portal_effective_after()
    print("    portal_config.py: templates %s%s (kept first in %s)" % (
        "LIVE" if eff2.get("PORTAL_WA_DRYRUN") == "0" else "?? NOT LIVE",
        "; its key set to the proved one" if portal_ok is not True else "", BK))
    if eff2.get("PORTAL_WA_DRYRUN") != "0":
        undo()
        die("portal_config.py did not read back as intended -- put back", changed=True)


def portal_effective_after():
    code = ("import json,sys;sys.path.insert(0,%r);import portal_config as c;"
            "print(json.dumps({'PORTAL_WA_DRYRUN':getattr(c,'PORTAL_WA_DRYRUN',None)}))" % PORTAL_DIR)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:                                                   # noqa: BLE001
        return {}


def undo():
    b = os.path.join(BK, "portal_config.py.before_s599")
    if os.path.exists(b):
        shutil.copy2(b, PCFG)
        print("    portal_config.py put back")
    elif os.path.exists(b + ".ABSENT") and os.path.exists(PCFG):
        os.replace(PCFG, os.path.join(BK, "portal_config.py.made_by_s599"))
        print("    portal_config.py (made by S599) taken out")
    c = os.path.join(BK, "config.json.before_s599")
    if os.path.exists(c):
        shutil.copy2(c, CONFIG)
    elif os.path.exists(c + ".ABSENT") and os.path.exists(CONFIG):
        os.replace(CONFIG, os.path.join(BK, "config.json.made_by_s599"))
    print("    config.json put back")


def test():
    import portal_inbox as P
    import portal_wa
    me = ""
    for f in ("/root/wa/wa_approve.env", "/root/wa/.env"):
        me = P.last10(read_env(f).get("WA_TEST_NUMBER", ""))
        if me:
            break
    if not me:
        die("the owner's own number (WA_TEST_NUMBER) is not set")
    def cfg_get(k, d=""):
        try:
            import portal_config
            v = getattr(portal_config, k, None)
        except Exception:                                               # noqa: BLE001
            v = None
        return v if v else os.environ.get(k, d)
    tok = P._token(cfg_get)
    P.ingest(force=True)
    c = P.db()
    w = P.window(c, me)
    print("    your number ••••%s · your free-reply window: %s" % (me[-4:], ("open, %.0f h left" % w["hours_left"]) if w["open"] else "CLOSED"))
    if w["open"]:
        ok, mid, err = P.myop_send(tok, me, {"type": "text", "context": {"body": "Test from the WhatsApp Inbox (S599). No action needed.", "preview_url": False}})
        print("    1. text from the inbox: %s" % ("ACCEPTED by MyOperator" if ok else "REFUSED -- " + err))
        if ok:
            c.execute("INSERT OR IGNORE INTO msgs(mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES(?,?,?,?,?,?,?,?,?)",
                      (mid, me, "out", P.iso(P.now_ist()), "text", "Test from the WhatsApp Inbox (S599). No action needed.",
                       "sent", "S599 test", "inbox"))
            c.commit()
    else:
        print("    1. text from the inbox: NOT TRIED -- your window is closed (send 'hi' to the clinic number and run the line again)")
    c.close()
    r = portal_wa.send(me, "drmanoj_post_visit", {"1": "Test"}, "S599 test", tok, dry_run=False)
    print("    2. approved template (Post-visit, name 'Test'): %s" % ("ACCEPTED by MyOperator" if r.get("ok") else "REFUSED -- " + re.sub(r"\d{7,}", "••••", str(r.get("error")))[:160]))
    rep = {}
    P.ingest(force=True, report=rep)
    try:
        n = P.ingest_sheet(P.sheet_rows())
        sheet = "%d replies from the call tracker's sheet" % n
    except Exception as e:                                              # noqa: BLE001
        sheet = "the call tracker's sheet could not be read (%s)" % type(e).__name__
    c = P.db()
    tot = c.execute("SELECT COUNT(*) FROM msgs WHERE dir='out' AND src IN ('portal','sheet')").fetchone()[0]
    by = c.execute("SELECT sent_by, COUNT(*) FROM msgs WHERE dir='out' AND src IN ('portal','sheet') GROUP BY sent_by ORDER BY 2 DESC LIMIT 6").fetchall()
    c.close()
    print("    3. staff replies brought into the chats: %d (portal log %d new · %s) · by: %s" % (
        tot, rep.get("portal_log", 0), sheet, ", ".join("%s %d" % ((b[0] or "?"), b[1]) for b in by) or "-"))


if __name__ == "__main__":
    cmd = (sys.argv[1:] or ["check"])[0]
    if cmd == "check":
        good, eff, portal_ok = check()
        if not good:
            die("no WhatsApp key on the server is accepted by MyOperator")
    elif cmd == "apply":
        apply()
    elif cmd == "test":
        test()
    elif cmd == "undo":
        undo()

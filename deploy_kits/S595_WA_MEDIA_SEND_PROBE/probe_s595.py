#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s595.py -- kit S595_WA_MEDIA_SEND_PROBE (session S329, 19-Oct-2026) · D744, the WhatsApp Inbox's first step.

    /root/wa/venv/bin/python3 -B probe_s595.py           -- send the three test files to the owner's own number
    DRY=1 /root/wa/venv/bin/python3 -B probe_s595.py     -- every check, nothing sent

WHY: the WhatsApp Inbox (D744) must send a photo, a PDF and a voice note back to a patient. The live server has only ever sent text and
templates through MyOperator. Before the inbox is built, this proves -- once, on the owner's own phone -- which of the three MyOperator
accepts, and in which message shape, so the build is done once.

WHAT IT DOES, AND ONLY THIS:
  1. reads the owner's own number (WA_TEST_NUMBER -- the same one the approval page's test mode already uses) and the live send settings
     the way the running sender does (wa_send.load_config + MYOP_AUTH_TOKEN from /root/wa/.env); prints nothing but the last 4 digits;
  2. checks WhatsApp's 24-hour rule for that number (wa_send.window_state, the live sender's own check) -- a photo / PDF / voice note can
     only go inside the window; if it is closed it stops and says so;
  3. puts the kit's four TEST files (a made-up photo, a one-page PDF, a 3-second tone as a voice note, the same tone as an MP3) in a new
     folder with a random name under the website, checks each opens from the internet, and asks the server to remove the folder after
     30 minutes;
  4. sends photo, PDF, voice note to the owner's own number -- each tried first in the shape the text messages use (data.context), and only
     if MyOperator refuses it, in the flat shape (data.*); the voice note falls back to the MP3 if the OGG is refused;
  5. writes what was accepted to /root/finance/s595_probe.json (no number, no token) -- the nightly bundle carries it to the build.
Nothing live is changed: no program, no setting, no sheet, no database.
"""
import os, re, sys, json, time, shutil, secrets, base64, hashlib, subprocess, datetime, urllib.request, urllib.error, http.client

sys.path.insert(0, "/root/wa")
KDIR = os.path.dirname(os.path.abspath(__file__))
DRY = os.environ.get("DRY", "0") == "1"
SITE_DIR = os.environ.get("S595_SITE_DIR", "/home/drmanojagarwal.com/public_html")
SITE_URL = os.environ.get("S595_SITE_URL", "https://drmanojagarwal.com")
OUT = os.environ.get("S595_OUT", "/root/finance/s595_probe.json")
ENV_FILES = ("/root/wa/wa_approve.env", "/root/wa/.env")
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
MD5 = {'test_photo.jpg': 'ed72c24a258c7cbedd9b6b3aa62c9b5d', 'test_document.pdf': '2d5488e4ee8d9a1f1ee83da055f50352', 'test_voice.ogg': 'aeba2a49de1652689b08252c7fd00556', 'test_voice.mp3': 'f3cff9b1abc5b3724461d42a7cf78b91'}
FILES = {
    "photo":    ("test_photo.jpg", "image", "image/jpeg", "Clinic server test photo (S595). No action needed."),
    "pdf":      ("test_document.pdf", "document", "application/pdf", "Clinic server test PDF (S595). No action needed."),
    "voice":    ("test_voice.ogg", "audio", "audio/ogg", ""),
    "voice_mp3": ("test_voice.mp3", "audio", "audio/mpeg", ""),
}


def mask(s):
    return re.sub(r"\d{7,}", lambda m: "••••" + m.group(0)[-4:], str(s))


def die(msg, cleanup=None):
    if cleanup:
        shutil.rmtree(cleanup, ignore_errors=True)
    print("!! STOPPED: %s" % msg)
    print("   Nothing was sent. Send a photo of this screen to Claude.")
    sys.exit(1)


def env_val(key):
    for p in ENV_FILES:
        try:
            for raw in open(p, encoding="utf-8"):
                line = raw.strip()
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    return os.environ.get(key, "")


def post(cfg, token, body):
    headers = {"Authorization": "Bearer " + token, "X-MYOP-COMPANY-ID": cfg["company_id"],
               "Content-Type": "application/json", "Accept": "application/json"}
    conn = http.client.HTTPSConnection("publicapi.myoperator.co", timeout=40)
    try:
        conn.request("POST", "/chat/messages", json.dumps(body), headers)
        r = conn.getresponse()
        status, text = r.status, r.read().decode("utf-8", "replace")
    finally:
        conn.close()
    try:
        j = json.loads(text)
    except ValueError:
        j = {"raw": text[:300]}
    ok = status in (200, 201) and str(j.get("status", "")).lower() == "success"
    d = j.get("data") if isinstance(j.get("data"), dict) else {}
    mid = d.get("message_id") or d.get("id") or ""
    why = "" if ok else (j.get("message") or j.get("error") or j.get("errors") or j.get("raw") or "")
    return ok, status, mid, mask(json.dumps(why) if not isinstance(why, str) else why)[:200]


def body_for(cfg, num, kind, link, fname, mime, caption, shape):
    media = {"link": link, "filename": fname, "mime_type": mime}
    if caption and kind != "audio":
        media["caption"] = caption
    data = {"type": kind, "context": media} if shape == "context" else dict({"type": kind}, **media)
    return {"phone_number_id": cfg["phone_number_id"], "customer_country_code": cfg["country_code"],
            "customer_number": num, "data": data, "reply_to": None, "myop_ref_id": None}


def fetch_ok(url, size):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "clinic-s595-check"})
        with urllib.request.urlopen(req, timeout=20) as r:
            got = r.read()
            return r.status == 200 and len(got) == size, "%s %s" % (r.status, r.headers.get("Content-Type", "?"))
    except urllib.error.HTTPError as e:
        return False, "HTTP %s" % e.code
    except Exception as e:                                   # noqa: BLE001
        return False, str(e)[:80]


def main():
    import wa_send                                           # the live sender's own settings and 24-hour check
    cfg = wa_send.load_config()
    token = env_val("MYOP_AUTH_TOKEN") or cfg.get("token") or ""
    if not token:
        die("no MyOperator send token found (MYOP_AUTH_TOKEN / WA_SEND_TOKEN)")
    num = wa_send.last10(env_val("WA_TEST_NUMBER"))
    if len(num) != 10:
        die("the owner's own number (WA_TEST_NUMBER) is not set")
    print("[1] owner's own number ••••%s · sender settings read (token not shown)" % num[-4:])

    try:
        is_open, last_dt, age = wa_send.window_state(cfg, num)
    except Exception as e:                                   # noqa: BLE001
        die("could not read the WhatsApp inbox sheet for the 24-hour check (%s)" % mask(str(e))[:120])
    if not is_open:
        when = last_dt.astimezone(IST).strftime("%d-%b %H:%M IST") if last_dt else "never"
        die("WhatsApp's 24-hour window is closed for your number (your last message to the clinic: %s). "
            "Send any message (e.g. 'hi') from your phone to the clinic WhatsApp number, wait one minute, then run the same line again" % when)
    print("[2] 24-hour window open (your last message %.1f h ago)" % (age.total_seconds() / 3600))

    if not os.path.isdir(SITE_DIR):
        die("the website folder %s is not there" % SITE_DIR)
    folder = "s595-" + secrets.token_hex(12)
    pub = os.path.join(SITE_DIR, folder)
    st = os.stat(SITE_DIR)
    os.makedirs(pub, mode=0o755)
    os.chown(pub, st.st_uid, st.st_gid)
    urls = {}
    for k, (fn, kind, mime, cap) in FILES.items():
        # the kit carries each test file as base64 text (.b64): a binary passed through the PC hand-over can change, and .gitignore keeps
        # *.mp3 out of git. Decoded here and held against its MD5 before it is put up.
        raw = base64.b64decode(open(os.path.join(KDIR, fn + ".b64"), "rb").read())
        if hashlib.md5(raw).hexdigest() != MD5[fn]:
            die("the kit's test file %s did not decode to its recorded bytes" % fn, cleanup=pub)
        dst = os.path.join(pub, fn)
        with open(dst, "wb") as fh:
            fh.write(raw)
        os.chmod(dst, 0o644)
        os.chown(dst, st.st_uid, st.st_gid)
        url = "%s/%s/%s" % (SITE_URL, folder, fn)
        ok, how = fetch_ok(url, len(raw))
        if not ok:
            die("the test file %s does not open from the internet (%s)" % (fn, how), cleanup=pub)
        urls[k] = url
    sched = subprocess.run(["systemd-run", "--quiet", "--on-active=1800", "--unit=s595-cleanup-%s" % folder[-6:],
                            "/bin/rm", "-rf", pub], capture_output=True, text=True)
    print("[3] four test files open from the internet (random folder %s…); removal in 30 minutes: %s"
          % (folder[:9], "scheduled" if sched.returncode == 0 else "NOT scheduled -- removed at the end instead"))

    result = {"at": datetime.datetime.now(IST).isoformat(timespec="seconds"), "kit": "S595", "dry": DRY, "sent": {}}
    if DRY:
        print("-- DRY RUN: nothing sent")
        if sched.returncode != 0:
            shutil.rmtree(pub, ignore_errors=True)
        return

    order = [("photo", "photo"), ("pdf", "PDF"), ("voice", "voice note")]
    for key, label in order:
        fn, kind, mime, cap = FILES[key]
        done = None
        tries = [(key, "context"), (key, "flat")] + ([("voice_mp3", "context"), ("voice_mp3", "flat")] if key == "voice" else [])
        notes = []
        for fkey, shape in tries:
            fn2, kind2, mime2, cap2 = FILES[fkey]
            ok, status, mid, why = post(cfg, token, body_for(cfg, num, kind2, urls[fkey], fn2, mime2, cap2, shape))
            if ok:
                done = {"accepted": True, "file": fn2, "type": kind2, "mime": mime2, "shape": shape, "message_id_head": str(mid)[:10]}
                break
            notes.append(mask("%s/%s: HTTP %s %s" % (fn2, shape, status, why)))
            time.sleep(1)
        if done:
            print("[4] %-10s ACCEPTED by MyOperator (%s, %s shape)" % (label, done["file"], done["shape"]))
        else:
            done = {"accepted": False, "refusals": notes}
            print("[4] %-10s REFUSED -- %s" % (label, " | ".join(notes)[:300]))
        result["sent"][key] = done
        time.sleep(2)

    if sched.returncode != 0:
        time.sleep(60)
        shutil.rmtree(pub, ignore_errors=True)
    old = os.umask(0o077)
    try:
        with open(OUT, "w") as fh:
            json.dump(result, fh, indent=1)
    finally:
        os.umask(old)
    n = sum(1 for v in result["sent"].values() if v.get("accepted"))
    print("[5] %d of 3 accepted · recorded in %s" % (n, OUT))
    print("DONE. Look at your phone's WhatsApp from the clinic number: a photo, a PDF and a voice note should have arrived. Tell Claude what came.")


if __name__ == "__main__":
    main()

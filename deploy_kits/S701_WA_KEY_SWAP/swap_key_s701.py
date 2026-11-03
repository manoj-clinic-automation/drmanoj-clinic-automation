#!/usr/bin/env python3
"""swap_key_s701.py -- kit S701_WA_KEY_SWAP (the parent, S382, 03-Nov-2026): the clinic's WhatsApp key (MyOperator's
'Authentication' Bearer value), replaced EVERYWHERE the server holds it, BY VALUE.

  find    read-only: the current key's holders (files, unit files, the crontab, running services' environments), what
          would change, what would restart. Never prints a key (only its length and an 8-character fingerprint).
  apply   asks for the NEW key (hidden). Checks its shape; asks MyOperator (read-only template list) whether it works;
          writes it in place of the old one in every live holder (each file backed up first, mode 600); reloads systemd
          when a unit file changed; restarts every service that reads the key only at start; checks afterwards that no
          live holder keeps the old key and that the inbox reads the new one.
  undo    puts every file back as it was before the last apply (only where the file is still as apply left it) and
          restarts the same services.

WHY BY VALUE: the key lives in several places (/root/wa/.env, /root/wa/wa_approve.env, the portal's own settings, ...)
and S381 proved they all hold the SAME key; a place nobody listed would keep the old key and fail later. Every file that
holds the old key is found by reading it, whatever its name.

THE TEST: MyOperator's gateway answers HTTP 500 for a refused key AND, on and off, for a good one (ticket 691386; S600:
a made-up key also gets 500). So only a 200 proves a key. The rule: the new key is written when MyOperator accepts it
(200) at least once in six tries; or, when MyOperator accepts neither key, when the new key has the old one's shape (same
length, the same kind of characters) -- the old one is then revoked by the Regenerate and keeping it gains nothing (exit 3:
written, not yet proven). Nothing is written when MyOperator still accepts the OLD key and never the new one, or when it
answers 401/403 to the new key (a clear 'wrong key').
ORDER (cold review R1, blocker 2): every check that can stop the swap runs BEFORE the owner is asked to press Regenerate;
after it only the paste itself can be refused, and the same line can simply be run again.
"""
import datetime, getpass, hashlib, json, os, re, shutil, stat, string, subprocess, sys, time, urllib.error, urllib.request

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
E = os.environ.get
ROOTS = [r for r in E("S701_ROOTS", "/root:/etc/systemd/system:/etc/environment:/etc/default:/etc/profile.d:/usr/local/bin:"
                                     "/etc/cron.d:/etc/crontab").split(":") if r]
REPORT_ROOTS = [r for r in E("S701_REPORT_ROOTS", "/etc/nginx").split(":") if r]      # read, never changed
PROC = E("S701_PROC", "/proc")
SYSTEMCTL = E("S701_SYSTEMCTL", "systemctl")
CRONTAB = E("S701_CRONTAB", "crontab")
BK = E("S701_BACKUP", "/root/s701_backup")
WA_ENV = E("S701_WA_ENV", "/root/wa/.env")
APPROVE_ENV = E("S701_APPROVE_ENV", "/root/wa/wa_approve.env")
SEND_ENV = E("S701_SEND_ENV", "/root/wa/wa_send.env")
PCFG = E("S701_PORTAL_CFG", "/root/portal/portal_config.py")
REPO = E("S701_REPO", "/root/deploy/repo")
CHECK_URL = E("S701_CHECK_URL", "https://publicapi.myoperator.co/chat/templates")
COMPANY_ID = "68384350414b9847"
WABA_ID_DEFAULT = "2101222617483538"
TRIES = int(E("S701_TRIES", "6"))
GAP_S = float(E("S701_GAP_S", "5"))
INBOX_CHECK = E("S701_INBOX_CHECK", "1") == "1"
VPY = E("S701_VPY", "/root/wa/venv/bin/python3")
PORTAL_DIR = E("S701_PORTAL_DIR", "/root/portal")
READERS = [u for u in E("S701_READERS", "clinic-portal,wa-approve,wa-send-api").split(",") if u]   # read the key only at start
SKIP_DIRS = {".git", "venv", ".venv", "node_modules", "__pycache__", ".cache", "site-packages", "dist-packages", ".npm", ".local"}
SKIP_EXT = {".mp3", ".wav", ".ogg", ".oga", ".m4a", ".mp4", ".webm", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf",
            ".xlsx", ".xls", ".docx", ".zip", ".gz", ".tgz", ".tar", ".bz2", ".xz", ".7z", ".pyc", ".so", ".woff", ".woff2", ".ttf"}
NOCHANGE_EXT = {".log", ".jsonl", ".csv", ".db", ".sqlite", ".sqlite3", ".md"}
BACKUP_PAT = re.compile(r"(/backups?/|/s\d{3,4}_backup/|/[A-Za-z0-9]+_backups/|\.bak\b|\.bak_|_bak\b|_BACKUP_|\.before\b|"
                        r"\.before_|before_s\d|\.orig$|\.old$|\.prev$|\.s701tmp$)", re.I)
CODE_KEYS = re.compile(r"MYOP_AUTH_TOKEN|WA_SEND_TOKEN|\bWA_TOKEN\b|^\s*(?:import|from)\s+(?:waba|wa_send|wa_send_api)\b", re.M)
UNIT_DIRS = tuple(E("S701_UNIT_DIRS", "/etc/systemd/,/lib/systemd/,/usr/lib/systemd/").split(","))
TRANSIENT = {"crond", "cron", "atd"}          # a job they started carries its own environment; never restarted for it
MAX_READ = 50 * 1024 * 1024
MAX_CHANGE = 1024 * 1024
ALLOWED = set(string.ascii_letters + string.digits + "-_.~+/=:")


def say(s=""):
    print(s, flush=True)


def stop(msg, changed=False):
    say("!! STOPPED: %s" % msg)
    say("   %s Send a photo of this screen to Claude." % ("Check the lines above." if changed else "Nothing was changed."))
    sys.exit(1)


def fp(k):
    return hashlib.sha256(k.encode()).hexdigest()[:8]


def now():
    return datetime.datetime.now(IST).strftime("%d-%b-%Y %H:%M:%S IST")


def read_env(path):
    vals = {}
    try:
        for raw in open(path, encoding="utf-8"):
            line = raw.strip()
            if line.startswith("export "):
                line = line[7:].strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return vals


def pcfg_value(name):
    try:
        t = open(PCFG, encoding="utf-8").read()
    except OSError:
        return ""
    m = re.findall(r"^%s\s*=\s*([\"'])(.*?)\1" % re.escape(name), t, re.M)
    return m[-1][1] if m else ""


def current_keys():
    """Every place the server is KNOWN to name the WhatsApp key. They must agree (S381)."""
    found = {}
    for label, val in (("/root/wa/.env MYOP_AUTH_TOKEN", read_env(WA_ENV).get("MYOP_AUTH_TOKEN", "")),
                       ("/root/wa/wa_approve.env MYOP_AUTH_TOKEN", read_env(APPROVE_ENV).get("MYOP_AUTH_TOKEN", "")),
                       ("/root/wa/wa_send.env WA_SEND_TOKEN", read_env(SEND_ENV).get("WA_SEND_TOKEN", "") or read_env(SEND_ENV).get("WA_TOKEN", "")),
                       ("/root/wa/.env WA_SEND_TOKEN", read_env(WA_ENV).get("WA_SEND_TOKEN", "") or read_env(WA_ENV).get("WA_TOKEN", "")),
                       ("portal_config.py MYOP_AUTH_TOKEN", pcfg_value("MYOP_AUTH_TOKEN"))):
        if val:
            found[label] = val
    return found


def key_works(tok):
    waba = read_env(WA_ENV).get("MYOP_WABA_ID") or WABA_ID_DEFAULT
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


def ask(tok, tries=TRIES):
    codes = []
    for i in range(tries):
        ok, code = key_works(tok)
        codes.append(str(code))
        if ok:
            return ok, codes
        if i < tries - 1:
            time.sleep(GAP_S)
    return False, codes


# ------------------------------------------------------------------ the search by value
def classify(path, size):
    low = path.lower()
    if BACKUP_PAT.search(path) or low.startswith(BK.lower().rstrip("/") + "/"):
        return "a backup copy -- left as it is"
    if REPO and (path == REPO or path.startswith(REPO.rstrip("/") + "/")):
        return "the repository copy -- left as it is (a key in the repository must be removed there)"
    for ext in NOCHANGE_EXT:
        if low.endswith(ext):
            return "a log or data file -- left as it is"
    if size > MAX_CHANGE:
        return "larger than 1 MB -- left as it is"
    return ""


def scan(old_keys, roots=None, report_only=False):
    """[(path, count, reason_if_not_changed)] for every regular file holding any old key."""
    needles = [k.encode() for k in old_keys]
    hits, skipped = [], 0
    for root in (roots if roots is not None else ROOTS):
        if not os.path.exists(root):
            continue
        walk = [(os.path.dirname(root), [], [os.path.basename(root)])] if os.path.isfile(root) else os.walk(root)
        for d, dirs, files in walk:
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not os.path.islink(os.path.join(d, x))]
            for f in files:
                p = os.path.join(d, f)
                try:
                    st = os.lstat(p)
                except OSError:
                    continue
                if not stat.S_ISREG(st.st_mode) or st.st_size == 0:
                    continue
                if os.path.splitext(f)[1].lower() in SKIP_EXT or st.st_size > MAX_READ:
                    skipped += 1
                    continue
                try:
                    with open(p, "rb") as fh:
                        data = fh.read()
                except OSError:
                    continue
                n = sum(data.count(k) for k in needles)
                if n:
                    why = "report only" if report_only else classify(p, st.st_size)
                    if not why and b"\0" in data:
                        why = "not a text file -- left as it is"
                    hits.append((p, n, why))
    return hits, skipped


def crontab_holds(old_keys):
    try:
        p = subprocess.run([CRONTAB, "-l"], capture_output=True, text=True, timeout=20)
    except Exception:                                                   # noqa: BLE001
        return None, 0
    if p.returncode != 0:
        return None, 0
    return p.stdout, sum(p.stdout.count(k) for k in old_keys)


def unit_of(pid):
    try:
        for line in open(os.path.join(PROC, pid, "cgroup"), encoding="utf-8", errors="replace"):
            m = re.search(r"/([^/]+\.service)\b", line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return ""


def env_units(old_keys):
    """Services whose running processes were started with the old key in their environment."""
    needles = [k.encode() for k in old_keys]
    units, loose = set(), []
    try:
        pids = [x for x in os.listdir(PROC) if x.isdigit()]
    except OSError:
        return units, loose
    for pid in pids:
        try:
            raw = open(os.path.join(PROC, pid, "environ"), "rb").read()
        except OSError:
            continue
        if any(k in raw for k in needles):
            u = unit_of(pid)
            if u and u[:-8] in TRANSIENT:
                loose.append(pid)
            elif u:
                units.add(u[:-8])
            else:
                loose.append(pid)
    return units, loose


def sysctl(*args, timeout=90):
    try:
        p = subprocess.run([SYSTEMCTL] + list(args), capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except Exception as e:                                              # noqa: BLE001
        return 99, type(e).__name__


def active(u):
    return sysctl("is-active", u, timeout=20)[1] == "active"


def unit_refs(paths):
    """Active services whose unit text names a changed file (EnvironmentFile=, ExecStart=)."""
    out = set()
    rc, txt = sysctl("list-units", "--type=service", "--state=active", "--no-legend", "--plain", timeout=30)
    for line in txt.splitlines():
        u = line.split()[0] if line.split() else ""
        if not u.endswith(".service"):
            continue
        rc, cat = sysctl("cat", u, timeout=20)
        if any(p in cat for p in paths):
            out.add(u[:-8])
    return out


def code_refs():
    """Active services whose ExecStart script names the key's settings or imports the senders (waba / wa_send): they may
    hold the key in memory from their start, which /proc cannot show."""
    out = set()
    rc, txt = sysctl("list-units", "--type=service", "--state=active", "--no-legend", "--plain", timeout=30)
    for line in txt.splitlines():
        u = line.split()[0] if line.split() else ""
        if not u.endswith(".service"):
            continue
        rc, cat = sysctl("cat", u, timeout=20)
        for script in re.findall(r"(/[\w./-]+\.py)\b", cat):
            try:
                if os.path.getsize(script) <= MAX_CHANGE * 4 and CODE_KEYS.search(open(script, encoding="utf-8", errors="replace").read()):
                    out.add(u[:-8])
            except OSError:
                pass
    return out


def plan(old_keys):
    hits, skipped = scan(old_keys)
    rep, _ = scan(old_keys, roots=REPORT_ROOTS, report_only=True)
    cron_txt, cron_n = crontab_holds(old_keys)
    eu, loose = env_units(old_keys)
    change = [(p, n) for p, n, why in hits if not why]
    leave = [(p, n, why) for p, n, why in hits if why] + [(p, n, "outside the places this tool changes -- report only") for p, n, _w in rep]
    concern = [(p, n, why) for p, n, why in leave if not why.startswith("a backup copy")]
    return {"change": change, "leave": leave, "concern": concern, "skipped": skipped, "cron_txt": cron_txt, "cron_n": cron_n,
            "env_units": eu, "loose_pids": loose}


def show_plan(pl, olds):
    say("   the key now: %s" % ", ".join("%d characters, fingerprint %s" % (len(k), fp(k)) for k in olds))
    say("   files that hold it and WILL change (%d):" % len(pl["change"]))
    for p, n in pl["change"]:
        say("      %s  (%d place%s)" % (p, n, "" if n == 1 else "s"))
    if pl["cron_n"]:
        say("      the crontab  (%d place%s)" % (pl["cron_n"], "" if pl["cron_n"] == 1 else "s"))
    if pl["leave"]:
        say("   files that hold it and are LEFT as they are (%d):" % len(pl["leave"]))
        for p, n, why in pl["leave"]:
            say("      %s  -- %s" % (p, why))
    say("   services started with it in their environment: %s" % (", ".join(sorted(pl["env_units"])) or "none"))
    if pl["loose_pids"]:
        say("   processes outside any service holding it: %s (not restarted -- named here)" % ", ".join(pl["loose_pids"]))
    say("   media and archives not read: %d files" % pl["skipped"])


# ------------------------------------------------------------------ the writes
def bk_name(p):
    return os.path.join(BK, p.strip("/").replace("/", "__") + ".before")


def write_same_mode(p, data):
    st = os.stat(p)
    tmp = p + ".s701tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.chmod(tmp, stat.S_IMODE(st.st_mode))
    try:
        os.chown(tmp, st.st_uid, st.st_gid)
    except (PermissionError, OSError):
        pass
    os.replace(tmp, p)


def md5b(b):
    return hashlib.md5(b).hexdigest()


def restart(units):
    res = []
    for u in sorted(units):
        if not active(u):
            res.append((u, "not running -- left"))
            continue
        pid = sysctl("show", "-p", "MainPID", "--value", u, timeout=20)[1].strip()
        if not pid or pid == "0":                  # a finished one-shot shows 'active (exited)': restarting it would RUN it again
            res.append((u, "no running process (a one-shot) -- left"))
            continue
        rc, _ = sysctl("restart", u)
        ok = False
        for _i in range(10):
            time.sleep(float(E("S701_RESTART_WAIT", "1.5")))
            if active(u):
                ok = True
                break
        res.append((u, "restarted" if (rc == 0 and ok) else "!! DID NOT COME BACK (rc %s)" % rc))
    return res


def inbox_reads(new):
    """The inbox's own lookup of the key (config.json names its source) -- run under the runner's python."""
    if not INBOX_CHECK:
        return True, "skipped"
    code = ("import sys,hashlib; sys.path.insert(0, sys.argv[1]); import inbox_retry, portal_inbox as P; "
            "t=P._token(inbox_retry.cfg_get) or ''; print(hashlib.sha256(t.encode()).hexdigest()[:8])")
    try:
        p = subprocess.run([VPY, "-B", "-c", code, PORTAL_DIR], capture_output=True, text=True, timeout=60, cwd="/tmp")
        got = (p.stdout or "").strip().splitlines()[-1] if p.stdout.strip() else "(%s)" % (p.stderr or "")[-120:].strip()
    except Exception as e:                                              # noqa: BLE001
        got = type(e).__name__
    return got == fp(new), got


def get_new(args):
    if "--stdin" in args:
        raw = sys.stdin.readline()
    else:
        try:
            raw = getpass.getpass("   Paste the NEW key from MyOperator's API page and press Enter (it will not show; Enter alone = skip): ")
        except (EOFError, KeyboardInterrupt):
            raw = ""
    return raw.strip().strip('"').strip("'")


def load_manifest():
    try:
        return json.load(open(os.path.join(BK, "manifest_latest.json")))
    except Exception:                                                   # noqa: BLE001
        return {}


def apply(args):
    say("== the WhatsApp key: swap (%s) ==" % now())
    cur = current_keys()
    if not cur:
        stop("the server holds no WhatsApp key in the known places -- nothing to replace. Do NOT press Regenerate")
    olds = sorted(set(cur.values()))
    if len(olds) > 1:
        for lab, v in cur.items():
            say("      %-42s %d characters, fingerprint %s" % (lab, len(v), fp(v)))
        stop("the known places hold DIFFERENT keys (above) -- Claude settles which is live first. Do NOT press Regenerate")
    old = olds[0]
    say("1. every place that holds the current key (read-only) ...")
    pl = plan([old])
    show_plan(pl, [old])
    if not pl["change"] and not pl["cron_n"]:
        stop("no live file holds the current key -- nothing to replace. Do NOT press Regenerate")
    if pl["concern"]:
        stop("the current key is also in a place this tool does not change (the LEFT lines above that are not backup copies) -- "
             "Claude looks at it first. Do NOT press Regenerate")
    units = set(READERS) | set(pl["env_units"]) | unit_refs([p for p, _n in pl["change"]]) | code_refs()
    say("   services that will restart: %s" % (", ".join(sorted(u for u in units if active(u))) or "none"))
    man0 = load_manifest()
    already = man0.get("new_fp") == fp(old) and not (man0.get("final") or {}).get("left_live")
    if already:
        say("   ALREADY: the key in place is the one this tool swapped in at %s%s." % (man0.get("at", "?"),
            "" if man0.get("verdict") == "PROVEN" or (man0.get("final") or {}).get("accepted_after") else
            " -- NOT YET PROVEN then: if WhatsApp still fails, paste the key from MyOperator's page again"))
        say("2. Press Enter to leave it. (Paste a key only if you pressed Regenerate AGAIN since then.)")
    else:
        say("2. All checks are green. NOW, on MyOperator's API page, press Regenerate and copy the new key.")
    new = get_new(args)
    if not new:
        if already:
            say("ALREADY SWAPPED -- nothing to do.")
            return 0
        say("   no key pasted -- the key is left as it is. Run the same line again when you have the new key.")
        return 2
    again = (" Copy it again from MyOperator's API page and run the same line again. WhatsApp sends are refused until the new "
             "key is in.")
    if new == old:
        stop("that is the key the server already has -- press Regenerate on MyOperator's API page, then copy the NEW one.")
    if any(ch.isspace() for ch in new) or not set(new) <= ALLOWED or not (20 <= len(new) <= 300):
        stop("what was pasted does not look like a key (%d characters%s).%s" % (
            len(new), ", with spaces" if any(ch.isspace() for ch in new) else "", again))
    say("   new key: %d characters, fingerprint %s  (the old: %d, %s)" % (len(new), fp(new), len(old), fp(old)))
    say("3. asking MyOperator (read-only: the approved-template list) ...")
    nok, ncodes = ask(new, tries=max(TRIES, 12))         # about a minute: a fresh key may take a moment to be live
    say("   the NEW key: %s  (answers %s)" % ("ACCEPTED" if nok else "not accepted", " ".join(ncodes)))
    if not nok and set(ncodes) & {"401", "403"}:
        stop("MyOperator says the new key is WRONG (%s).%s You do not need to press Regenerate again if you still have the key "
             "you copied -- paste that one." % ("/".join(sorted(set(ncodes) & {"401", "403"})), again))
    verdict = "PROVEN"
    if not nok:
        ook, ocodes = ask(old, tries=2)
        say("   the OLD key: %s  (answers %s)" % ("still ACCEPTED" if ook else "not accepted", " ".join(ocodes)))
        if ook:
            stop("MyOperator still accepts the OLD key and never accepted the new one -- the paste is wrong, or Regenerate was "
                 "not pressed.%s" % again)
        if len(new) != len(old):
            stop("MyOperator accepts neither key and the new one has a different shape (%d characters, the old %d).%s" % (
                len(new), len(old), again))
        verdict = "NOT YET PROVEN"
        say("   MyOperator accepts neither key just now (their gateway's own fault, ticket 691386); the new key has the old one's")
        say("   shape and the old one is revoked by the Regenerate -- the new key is written; the inbox's retries will prove it.")
    pl = plan([old])                       # read again: minutes may have passed while the key was being copied
    if not pl["change"] and not pl["cron_n"]:
        show_plan(pl, [old])
        stop("no live file holds the old key any more (above) -- Claude looks first")
    if pl["concern"]:                      # the old key is revoked now: the live files are swapped anyway; the new place is reported
        say("   !! a new place holds the old key since the first read (it is reported at the end; the live files are swapped now)")
    # ---- backups
    os.makedirs(BK, mode=0o700, exist_ok=True)
    os.chmod(BK, 0o700)
    stamp = datetime.datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    man = {"kit": "S701", "at": now(), "stamp": stamp, "old_fp": fp(old), "new_fp": fp(new), "verdict": verdict, "files": [],
           "crontab": False, "units": []}
    for p, _n in pl["change"]:
        b = bk_name(p)
        data = open(p, "rb").read()
        with open(b, "wb") as fh:
            fh.write(data)
        os.chmod(b, 0o600)
        if open(b, "rb").read() != data:
            stop("the backup of %s did not read back -- nothing changed" % p)
        man["files"].append({"path": p, "before_md5": md5b(data), "after_md5": ""})
    if pl["cron_n"]:
        cb = os.path.join(BK, "crontab.before")
        with open(cb, "w") as fh:
            fh.write(pl["cron_txt"])
        os.chmod(cb, 0o600)
        man["crontab"] = True
    say("4. backups kept in %s (mode 600): %d file(s)%s" % (BK, len(man["files"]), " + the crontab" if man["crontab"] else ""))
    # ---- writes
    changed_paths, oldb, newb = [], old.encode(), new.encode()
    try:
        for ent in man["files"]:
            p = ent["path"]
            data = open(p, "rb").read()
            if md5b(data) != ent["before_md5"]:
                raise RuntimeError("%s changed while the swap ran" % p)
            out = data.replace(oldb, newb)
            write_same_mode(p, out)
            back = open(p, "rb").read()
            if back != out or oldb in back or back.count(newb) != data.count(oldb):
                raise RuntimeError("%s did not read back as written" % p)
            ent["after_md5"] = md5b(back)
            changed_paths.append(p)
        if man["crontab"]:
            nt = pl["cron_txt"].replace(old, new)
            tf = os.path.join(BK, "crontab.new")
            with open(tf, "w") as fh:
                fh.write(nt)
            os.chmod(tf, 0o600)
            if subprocess.run([CRONTAB, tf], capture_output=True, timeout=20).returncode != 0:
                raise RuntimeError("the crontab could not be written")
            now_txt, n_old = crontab_holds([old])
            os.remove(tf)
            if n_old or now_txt is None or now_txt.count(new) != pl["cron_n"]:
                raise RuntimeError("the crontab did not read back as written")
            man["cron_after_md5"] = md5b(now_txt.encode())
            man["cron_before_md5"] = md5b(pl["cron_txt"].encode())
    except Exception as ex:                                             # noqa: BLE001
        say("!! a write failed: %s -- putting everything back" % ex)
        _restore(man, quiet=False)
        stop("the key was not swapped; every file is as it was (with the OLD key, which the Regenerate has revoked: WhatsApp "
             "sends are refused until the same line runs again and the new key goes in)", changed=True)
    with open(os.path.join(BK, "manifest_%s.json" % stamp), "w") as fh:
        json.dump(man, fh, indent=1)
    os.chmod(os.path.join(BK, "manifest_%s.json" % stamp), 0o600)
    with open(os.path.join(BK, "manifest_latest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    os.chmod(os.path.join(BK, "manifest_latest.json"), 0o600)
    say("5. the new key written in %d file(s)%s, each read back: old key 0 times, new key as many times as the old" % (
        len(changed_paths), " and the crontab" if man["crontab"] else ""))
    # ---- systemd and restarts
    unit_files = [p for p in changed_paths if p.startswith(UNIT_DIRS)]
    if unit_files:
        rc, _ = sysctl("daemon-reload")
        say("   systemd reloaded (a unit file changed): rc %s" % rc)
    units = set(READERS) | set(pl["env_units"]) | unit_refs(changed_paths) | code_refs()
    man["units"] = sorted(units)
    res = restart(units)
    say("6. services that read the key only at start:")
    bad = 0
    for u, r in res:
        say("      %-28s %s" % (u, r))
        bad += r.startswith("!!")
    with open(os.path.join(BK, "manifest_latest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    # ---- after
    pl2 = plan([old])
    left_live = [p for p, _n in pl2["change"]] + (["the crontab"] if pl2["cron_n"] else []) + [p for p, _n, _w in pl2["concern"]]
    say("7. after: live files still holding the OLD key: %s; services still started with it: %s" % (
        ", ".join(left_live) or "none", ", ".join(sorted(pl2["env_units"])) or "none"))
    ib, got = inbox_reads(new)
    say("   the inbox reads the NEW key: %s" % ("yes" if ib else "NO (it reads %s)" % got))
    fok, fcodes = ask(new, tries=3)
    say("   MyOperator, the new key once more: %s  (answers %s)" % ("ACCEPTED" if fok else "not accepted just now", " ".join(fcodes)))
    man["final"] = {"left_live": left_live, "inbox": ib, "accepted_after": fok, "restart_failed": bad}
    with open(os.path.join(BK, "manifest_latest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    if left_live or pl2["env_units"] or not ib or bad:
        say("!! the swap is written but something above is not right -- Send a photo of this screen to Claude.")
        say("   Undo (puts every file back): the same line with UNDO=1 before bash.")
        return 1
    say("")
    if verdict == "PROVEN":
        say("THE KEY IS SWAPPED (PROVEN). The old key is in no live file and no running service.")
        return 0
    say("THE KEY IS SWAPPED BUT NOT YET PROVEN: MyOperator answered neither key%s. The old key is in no live file and no running"
        % (", then accepted the new one" if fok else ""))
    say("service. Send a photo of this screen to Claude.")
    return 0 if fok else 3


def _restore(man, quiet=True):
    out = []
    for ent in man["files"]:
        p, b = ent["path"], bk_name(ent["path"])
        try:
            cur = md5b(open(p, "rb").read())
        except OSError:
            cur = ""
        if ent.get("after_md5") and cur not in (ent["after_md5"], ent["before_md5"]):
            out.append("!! %s changed since the swap -- left; its old copy is %s" % (p, b))
            continue
        if cur == ent["before_md5"]:
            out.append("   %s already as before" % p)
            continue
        write_same_mode(p, open(b, "rb").read())
        out.append("   %s put back%s" % (p, "" if md5b(open(p, "rb").read()) == ent["before_md5"] else " -- !! does NOT read back"))
    if man.get("crontab"):
        cb = os.path.join(BK, "crontab.before")
        try:
            cur_c = subprocess.run([CRONTAB, "-l"], capture_output=True, text=True, timeout=20).stdout
        except Exception:                                               # noqa: BLE001
            cur_c = None
        cm = md5b(cur_c.encode()) if cur_c is not None else ""
        if man.get("cron_before_md5") and cm == man["cron_before_md5"]:
            out.append("   the crontab already as before")
        elif not man.get("cron_after_md5") or cm == man["cron_after_md5"]:
            rc = subprocess.run([CRONTAB, cb], capture_output=True, timeout=20).returncode
            out.append("   the crontab put back (rc %s)" % rc)
        else:
            out.append("!! the crontab changed since the swap -- left; its old copy is %s" % cb)
    for line in out:
        say(line)
    return out


def undo(_args):
    say("== the WhatsApp key: undo the last swap (%s) ==" % now())
    try:
        man = json.load(open(os.path.join(BK, "manifest_latest.json")))
    except Exception:                                                   # noqa: BLE001
        stop("no swap to undo (no %s/manifest_latest.json)" % BK)
    out = _restore(man)
    if any(e["path"].startswith(UNIT_DIRS) for e in man["files"]):
        sysctl("daemon-reload")
    for u, r in restart(set(man.get("units") or READERS)):
        say("      %-28s %s" % (u, r))
    bad = sum(1 for line in out if line.startswith("!!"))
    say("UNDONE -- every file is as it was before %s." % man.get("at", "the swap") if not bad else "!! undo incomplete (above)")
    return 1 if bad else 0


def find(_args):
    say("== the WhatsApp key: where the server holds it (read-only, %s) ==" % now())
    cur = current_keys()
    for lab, v in cur.items():
        say("      %-42s %d characters, fingerprint %s" % (lab, len(v), fp(v)))
    olds = sorted(set(cur.values()))
    if not olds:
        stop("no WhatsApp key in the known places")
    if len(olds) > 1:
        say("!! the known places hold DIFFERENT keys")
    pl = plan(olds)
    show_plan(pl, olds)
    units = set(READERS) | set(pl["env_units"]) | unit_refs([p for p, _n in pl["change"]]) | code_refs()
    if pl["concern"]:
        say("!! the key is also in a place the swap does not change (the LEFT lines that are not backup copies) -- Claude looks first")
    say("   services the swap would restart: %s" % ", ".join(sorted(u for u in units if active(u))))
    return 0 if len(olds) == 1 and not pl["concern"] else 1


def walk_guard():
    """S701_WALK=1 (the walk): refuse unless EVERY place this tool reads or writes is inside the temp folder."""
    if E("S701_WALK") != "1":
        return
    import tempfile
    t = os.path.realpath(tempfile.gettempdir()) + "/"
    places = [BK, WA_ENV, APPROVE_ENV, SEND_ENV, PCFG, PROC, SYSTEMCTL, CRONTAB, PORTAL_DIR] + ROOTS + REPORT_ROOTS
    bad = [p for p in places if not os.path.realpath(p).startswith(t)]
    if bad or "127.0.0.1" not in CHECK_URL:
        stop("the walk's settings point outside the temp folder (%s) -- refused" % ", ".join(bad or [CHECK_URL]))


if __name__ == "__main__":
    os.umask(0o077)
    walk_guard()
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"find": find, "apply": apply, "undo": undo}.get(mode)
    if not fn:
        say(__doc__)
        sys.exit(2)
    sys.exit(fn(sys.argv[2:]))

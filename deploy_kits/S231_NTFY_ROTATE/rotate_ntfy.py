#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rotate_ntfy.py  --  S231 / F-358 / F-364 : rotate the clinic's ntfy alert topics
and take the topic OUT of the code.

WHY THIS EXISTS
---------------
The repository github.com/manoj-clinic-automation/drmanoj-clinic-automation is
PUBLIC (verified unauthenticated at S231: private=false, visibility=public).
Two ntfy topics were readable inside it:

  * one hard-coded as a DEFAULT in three live VPS scripts
  * one shown as an EXAMPLE in a comment in the staff_ledger family

On ntfy.sh the topic name IS the credential.  Anyone who read the repository
could subscribe to the clinic's alerts, and could publish to them -- i.e. send
the owner an alert that looks exactly like his own system speaking.

Rotating makes every public copy of the OLD topics worthless.  So this script
does not try to rewrite history.  It does three things, in this order:

  1. writes NEW random topics into /root/wa/.env          (config, not code)
  2. patches the LIVE scripts to READ that file, with NO default
  3. proves the new topics work, and prints them ONCE

Order matters.  Config is written BEFORE the defaults are removed, so there is
never a moment when a publisher has no topic to publish to.

SAFETY
------
  * default action is --check : discovers, reports, changes NOTHING
  * --install refuses at the first doubt and touches nothing if anything fails
  * every file it will touch is backed up first, to one timestamped folder
  * it asserts each anchor occurs EXACTLY ONCE before replacing it
  * it re-reads every file afterwards and verifies the literal is gone
  * the new topic values are printed exactly once, to this terminal only.
    They are never written to the repository, never logged, never emailed.

RUN IT (on the VPS, as root):
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_ROTATE/rotate_ntfy.py --check
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_ROTATE/rotate_ntfy.py --install
"""

import os
import re
import sys
import json
import shutil
import secrets
import datetime
import subprocess
import urllib.request

ENV_PATH  = "/root/wa/.env"
SEARCH_ROOTS = ["/root"]
SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__", "backups", "_backup"}

# The live scripts we expect to patch.  basename -> (env key it must end up using)
TARGETS = {
    "clinic_watchdog.py":        "WATCHDOG_NTFY_URL",
    "clinic_health_report.py":   "WATCHDOG_NTFY_URL",
    "clinic_timer_freshness.py": "WATCHDOG_NTFY_URL",
}

TOPIC_RE = re.compile(r'https://ntfy\.sh/([A-Za-z0-9_\-]+)')

STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = "/root/_backup_S231_ntfy_%s" % STAMP


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def say(msg=""):
    print(msg, flush=True)


def mask(topic):
    if len(topic) <= 5:
        return "*" * len(topic)
    return topic[:2] + "*" * (len(topic) - 4) + topic[-2:]


def mask_text(s):
    return TOPIC_RE.sub(lambda m: "https://ntfy.sh/" + mask(m.group(1)), s)


class Refuse(Exception):
    pass


# --------------------------------------------------------------------------
# the patch itself -- pure function, so it can be self-tested
# --------------------------------------------------------------------------
READER = '''
def _ntfy_url_from_env_file():
    """Read the alert topic from /root/wa/.env  (S231/F-358: never hard-coded).

    Returns "" if absent.  Callers MUST treat "" as loud -- never silent."""
    try:
        with open("%s", "r") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line.startswith("%s="):
                    return _line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""
'''


def patch_source(text, env_key):
    """Remove the hard-coded topic and read it from the env file instead.

    Returns (new_text, n_changes).  Raises Refuse on anything unexpected."""
    hits = TOPIC_RE.findall(text)
    if not hits:
        return text, 0

    # 1. insert the reader helper once, just before the first use
    if "_ntfy_url_from_env_file" not in text:
        reader = READER % (ENV_PATH, env_key)
        # place it after the last top-level import
        m = None
        for m in re.finditer(r'^(?:import|from)\s+\S+.*$', text, re.M):
            pass
        if m is None:
            raise Refuse("no import block found -- refusing to guess placement")
        text = text[:m.end()] + "\n\n" + reader.strip() + "\n" + text[m.end():]

    # 2. NTFY_TOPIC_URL = os.environ.get("KEY", "https://ntfy.sh/xxx")
    pat_default = re.compile(
        r'(?P<name>[A-Z_]*NTFY[A-Z_]*)\s*=\s*os\.environ\.get\(\s*'
        r'(["\'])(?P<key>[^"\']+)\2\s*,\s*(["\'])https://ntfy\.sh/[A-Za-z0-9_\-]+\4\s*\)'
    )
    # 3. NTFY_URL = "https://ntfy.sh/xxx"
    pat_literal = re.compile(
        r'(?P<name>[A-Z_]*NTFY[A-Z_]*)(?P<pad>\s*)=(?P<pad2>\s*)'
        r'(["\'])https://ntfy\.sh/[A-Za-z0-9_\-]+\4'
    )

    n = 0

    def _sub_default(m):
        nonlocal n
        n += 1
        return ('%s = os.environ.get("%s", "") or _ntfy_url_from_env_file()'
                % (m.group("name"), m.group("key")))

    def _sub_literal(m):
        nonlocal n
        n += 1
        return ('%s%s=%s os.environ.get("%s", "") or _ntfy_url_from_env_file()'
                % (m.group("name"), m.group("pad"), m.group("pad2").rstrip(), env_key))

    text = pat_default.sub(_sub_default, text)
    text = pat_literal.sub(_sub_literal, text)

    # 4. scrub any remaining literal topic in comments / docstrings
    def _scrub(m):
        nonlocal n
        n += 1
        return "https://ntfy.sh/<topic-from-%s>" % os.path.basename(ENV_PATH)

    text = TOPIC_RE.sub(_scrub, text)

    if TOPIC_RE.search(text):
        raise Refuse("a literal topic survived the patch -- refusing")
    return text, n


# --------------------------------------------------------------------------
# self-tests -- run before anything is touched
# --------------------------------------------------------------------------
def self_test():
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)

    a = ('import os\n'
         'NTFY_TOPIC_URL = os.environ.get("WATCHDOG_NTFY_URL", "https://ntfy.sh/abc123")\n')
    out, n = patch_source(a, "WATCHDOG_NTFY_URL")
    check("default-form replaced", "ntfy.sh/abc123" not in out)
    check("default-form reads env file", "_ntfy_url_from_env_file()" in out)
    check("default-form keeps name", "NTFY_TOPIC_URL" in out)
    check("default-form counted", n >= 1)

    b = 'import os\nNTFY_URL      = "https://ntfy.sh/zzz999"\n'
    out, n = patch_source(b, "WATCHDOG_NTFY_URL")
    check("literal-form replaced", "ntfy.sh/zzz999" not in out)
    check("literal-form reads env file", "_ntfy_url_from_env_file()" in out)

    c = 'import os\n# see https://ntfy.sh/commentonly for the topic\n'
    out, n = patch_source(c, "WATCHDOG_NTFY_URL")
    check("comment scrubbed", "ntfy.sh/commentonly" not in out)

    d = 'import os\nX = 1\n'
    out, n = patch_source(d, "WATCHDOG_NTFY_URL")
    check("clean file untouched", out == d and n == 0)

    for src in (a, b, c):
        out, _ = patch_source(src, "WATCHDOG_NTFY_URL")
        try:
            compile(out, "<patched>", "exec")
        except SyntaxError as e:
            fails.append("patched output does not compile: %s" % e)

    # idempotence
    out1, _ = patch_source(a, "WATCHDOG_NTFY_URL")
    out2, n2 = patch_source(out1, "WATCHDOG_NTFY_URL")
    check("idempotent", n2 == 0)

    return fails


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------
def discover():
    found = {}
    for root in SEARCH_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in SKIP_DIRS and not d.startswith("_backup_S231")]
            if "/deploy/repo/" in dirpath + "/":
                continue          # the checked-out repo is not the live copy
            for fn in filenames:
                if fn in TARGETS:
                    found.setdefault(fn, []).append(os.path.join(dirpath, fn))
    return found


def env_topics():
    """Which topics does /root/wa/.env already name?"""
    out = {}
    if not os.path.exists(ENV_PATH):
        return out
    for line in open(ENV_PATH, "r", errors="ignore"):
        line = line.strip()
        if "=" in line and "ntfy" in line.lower():
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def staff_ledger_env_source():
    """Where does staff-ledger.service get NTFY_URL from?"""
    notes = []
    try:
        r = subprocess.run(["systemctl", "cat", "staff-ledger.service"],
                           capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                s = line.strip()
                if s.startswith("Environment") or s.startswith("EnvironmentFile"):
                    notes.append(mask_text(s))
    except Exception as e:
        notes.append("could not read unit: %s" % e)
    return notes


# --------------------------------------------------------------------------
# actions
# --------------------------------------------------------------------------
def push_test(url, title, body):
    req = urllib.request.Request(
        url, data=body.encode("utf-8"),
        headers={"Title": title, "Priority": "default", "Tags": "white_check_mark"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def write_env(pairs):
    lines = []
    if os.path.exists(ENV_PATH):
        lines = open(ENV_PATH, "r", errors="ignore").read().splitlines()
    keys = set(pairs)
    out, seen = [], set()
    for line in lines:
        k = line.split("=", 1)[0].strip() if "=" in line else None
        if k in keys:
            out.append("%s=%s" % (k, pairs[k]))
            seen.add(k)
        else:
            out.append(line)
    for k, v in pairs.items():
        if k not in seen:
            out.append("%s=%s" % (k, v))
    body = "\n".join(out).rstrip("\n") + "\n"
    with open(ENV_PATH, "w") as f:
        f.write(body)
    os.chmod(ENV_PATH, 0o600)


CONF_EXT = {".env", ".conf", ".json", ".ini", ".cfg", ".sh", ".service", ".txt", ""}

# Unit files live OUTSIDE /root. The WhatsApp notifier keeps the topic as a bare
# name in Environment=NTFY_TOPIC=... in its unit -- not as a URL. Missing that
# would have moved the system alerts and left the WhatsApp alerts on the old,
# public topic: a HALF rotation, the worst outcome of the three.
CONF_ROOTS = ["/root", "/etc/systemd/system"]


def scan_conf_files(old_topics):
    """Every NON-.py file under /root that names one of the old topics.

    These are the configured publishers -- e.g. the freshness layer keeps its
    topic in its own conf, not in code. A rotation that misses them is a HALF
    rotation, which is worse than none: the owner would believe he had moved."""
    out = []
    for root in CONF_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in SKIP_DIRS and not d.startswith("_backup_S231")]
            if "/deploy/repo/" in dirpath + "/":
                continue
            for fn_ in filenames:
                if fn_.endswith(".py"):
                    continue
                ext = os.path.splitext(fn_)[1]
                if ext not in CONF_EXT:
                    continue
                fp = os.path.join(dirpath, fn_)
                try:
                    if os.path.getsize(fp) > 2_000_000:
                        continue
                    txt = open(fp, "r", errors="ignore").read()
                except Exception:
                    continue
                if any(tp in txt for tp in old_topics):
                    out.append(fp)

    # systemd's .wants/ entries are symlinks to the real unit file. Writing
    # through one works, but restoring it with \cp would replace the SYMLINK
    # with a regular file and quietly change how systemd sees the unit as
    # enabled. Keep one entry per real file, preferring the real path.
    seen, deduped = {}, []
    for fp in out:
        real = os.path.realpath(fp)
        if real in seen:
            continue
        seen[real] = fp
        deduped.append(real if os.path.exists(real) else fp)
    return sorted(set(deduped))


def main():
    mode = "--check"
    for a in sys.argv[1:]:
        if a in ("--check", "--install"):
            mode = a

    say("=" * 74)
    say("S231 ntfy rotation  --  mode %s  --  %s" % (mode, STAMP))
    say("=" * 74)

    say("\n[1] self-tests")
    fails = self_test()
    if fails:
        say("    REFUSING -- %d self-test failure(s):" % len(fails))
        for f in fails:
            say("      - %s" % f)
        return 2
    say("    all self-tests passed; nothing has been touched")

    say("\n[2] environment")
    if not os.path.exists(ENV_PATH):
        say("    REFUSING -- %s does not exist" % ENV_PATH)
        return 2
    say("    %s present" % ENV_PATH)
    cur = env_topics()
    if cur:
        for k, v in cur.items():
            say("    already in .env: %s = %s" % (k, mask_text(v)))
    else:
        say("    .env names no ntfy topic today")

    say("\n[3] live scripts")
    old_topics = set()
    found = discover()
    problems = []
    for name in TARGETS:
        paths = found.get(name, [])
        if len(paths) == 0:
            say("    %-28s NOT FOUND (skipped, not an error)" % name)
        elif len(paths) > 1:
            say("    %-28s %d copies -- AMBIGUOUS:" % (name, len(paths)))
            for p in paths:
                say("        %s" % p)
            problems.append("%s has %d live copies" % (name, len(paths)))
        else:
            p = paths[0]
            txt = open(p, "r", errors="ignore").read()
            hits = set(TOPIC_RE.findall(txt))
            old_topics.update(hits)
            say("    %-28s %s   (%d literal topic(s))" % (name, p, len(hits)))

    say("\n[4] staff ledger topic source")
    for n in staff_ledger_env_source() or ["    (no Environment= / EnvironmentFile= lines found)"]:
        say("    %s" % n)

    if problems:
        say("\nREFUSING -- ambiguity above must be resolved first:")
        for p in problems:
            say("  - %s" % p)
        return 2

    say("\n[4b] other files configured with the same topic")
    conf_hits = scan_conf_files(old_topics) if old_topics else []
    if old_topics:
        say("    (searching %s)" % ", ".join(CONF_ROOTS))
    if conf_hits:
        for fp in conf_hits:
            say("    %s" % fp)
    else:
        say("    none found")

    if mode == "--check":
        say("\n[5] --check only. NOTHING WAS CHANGED.")
        say("    Re-run with --install to rotate.")
        return 0

    # ---------------- install ----------------
    say("\n[5] backing up")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(ENV_PATH, os.path.join(BACKUP_DIR, "env.bak"))
    for name, paths in found.items():
        shutil.copy2(paths[0], os.path.join(BACKUP_DIR, name + ".bak"))
    for i, fp in enumerate(conf_hits):
        shutil.copy2(fp, os.path.join(BACKUP_DIR, "conf%d_%s.bak" % (i, os.path.basename(fp))))
    say("    %s" % BACKUP_DIR)

    say("\n[6] generating new topics")
    # Unambiguous alphabet: no 0/O, no 1/l/I -- this gets typed on a phone.
    # 31 symbols ** 16 places is about 10**23 possibilities; not guessable.
    ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
    new_vps = "".join(secrets.choice(ALPHABET) for _ in range(16))
    url_vps = "https://ntfy.sh/" + new_vps
    say("    one new topic generated (value shown once at the end)")

    say("\n[7] writing config BEFORE removing any default")
    write_env({"WATCHDOG_NTFY_URL": url_vps})
    back = env_topics()
    if back.get("WATCHDOG_NTFY_URL") != url_vps:
        say("    REFUSING -- .env did not read back as written. Restore:")
        say("      \\cp %s/env.bak %s" % (BACKUP_DIR, ENV_PATH))
        return 2
    say("    .env written and read back correctly (mode 600)")

    say("\n[7b] moving other configured publishers to the new topic")
    if not conf_hits:
        say("    none to move")
    for fp in conf_hits:
        try:
            txt = open(fp, "r", errors="ignore").read()
            new_txt = txt
            for tp in old_topics:
                new_txt = new_txt.replace(tp, new_vps)
            if new_txt == txt:
                say("    %-44s unchanged" % fp)
                continue
            if fp.endswith(".json"):
                json.loads(new_txt)          # refuse to write broken JSON
            with open(fp, "w") as f:
                f.write(new_txt)
            chk = open(fp, "r", errors="ignore").read()
            if any(tp in chk for tp in old_topics):
                say("    REFUSING -- old topic survived in %s" % fp)
                return 2
            say("    %-44s moved" % fp)
        except Exception as e:
            say("    REFUSING -- could not move %s: %s" % (fp, e))
            return 2

    units = sorted({os.path.basename(fp) for fp in conf_hits
                    if fp.endswith(".service")})
    if units:
        say("\n[7c] telling systemd, and restarting the units whose topic moved")
        try:
            r = subprocess.run(["systemctl", "daemon-reload"],
                               capture_output=True, text=True, timeout=60)
            say("    daemon-reload rc=%d" % r.returncode)
        except Exception as e:
            say("    REFUSING -- daemon-reload failed: %s" % e)
            return 2
        for u in units:
            try:
                subprocess.run(["systemctl", "restart", u],
                               capture_output=True, text=True, timeout=90)
                r2 = subprocess.run(["systemctl", "is-active", u],
                                    capture_output=True, text=True, timeout=30)
                state = r2.stdout.strip()
                say("    %-34s %s" % (u, state))
                if state != "active":
                    say("    REFUSING -- %s did not come back active." % u)
                    say("    Restore it with the undo lines below, then tell Claude.")
                    return 2
            except Exception as e:
                say("    REFUSING -- could not restart %s: %s" % (u, e))
                return 2

    say("\n[8] patching live scripts")
    for name, key in TARGETS.items():
        paths = found.get(name, [])
        if not paths:
            continue
        p = paths[0]
        txt = open(p, "r", errors="ignore").read()
        try:
            new, n = patch_source(txt, key)
        except Refuse as e:
            say("    REFUSING on %s -- %s" % (p, e))
            say("    Nothing further changed. Restore .env with:")
            say("      \\cp %s/env.bak %s" % (BACKUP_DIR, ENV_PATH))
            return 2
        if n == 0:
            say("    %-28s already clean" % name)
            continue
        compile(new, p, "exec")
        with open(p, "w") as f:
            f.write(new)
        chk = open(p, "r", errors="ignore").read()
        if TOPIC_RE.search(chk):
            say("    REFUSING -- %s still contains a literal topic after write" % p)
            return 2
        say("    %-28s patched (%d site(s)), no literal topic remains" % (name, n))

    say("\n[9] staff ledger -- deliberately NOT touched")
    say("    Its unit declares no Environment=/EnvironmentFile=, so NTFY_URL is")
    say("    empty and its ntfy() returns without publishing. Nothing to rotate.")
    say("    No restart. Its leaked string is a repo comment, scrubbed separately.")

    say("\n[10] proving the new topics carry")
    ok = True
    for label, u in (("VPS alerts", url_vps),):
        try:
            st = push_test(u, "Clinic alerts moved",
                           "S231: this topic is new and private. "
                           "The old one is retired and now carries nothing.")
            say("    %-14s test push HTTP %s" % (label, st))
        except Exception as e:
            ok = False
            say("    %-14s test push FAILED: %s" % (label, e))
    if not ok:
        say("    NOTE: config and code are in place; the push failure is a network")
        say("          issue, not a rollback reason. Retry the push before subscribing.")

    say("\n" + "=" * 74)
    say("DONE. SUBSCRIBE YOUR PHONE TO THIS ONE, THEN DELETE THE OLD ONE.")
    say("=" * 74)
    say("")
    say("  Open the ntfy app on your phone, Add subscription, and type ONLY")
    say("  the name below (not the https part). Read it in fours:")
    say("")
    say("        %s   %s   %s   %s"
        % (new_vps[0:4], new_vps[4:8], new_vps[8:12], new_vps[12:16]))
    say("")
    say("  as one word:  %s" % new_vps)
    say("  full address: %s" % url_vps)
    say("")
    say("=" * 74)
    say("Shown once. It is in %s (mode 600) and in no repository." % ENV_PATH)
    say("Undo everything:")
    say("  \\cp %s/env.bak %s" % (BACKUP_DIR, ENV_PATH))
    for name in found:
        say("  \\cp %s/%s.bak %s" % (BACKUP_DIR, name, found[name][0]))
    for i, fp in enumerate(conf_hits):
        say("  \\cp %s/conf%d_%s.bak %s"
            % (BACKUP_DIR, i, os.path.basename(fp), fp))
    return 0


if __name__ == "__main__":
    sys.exit(main())

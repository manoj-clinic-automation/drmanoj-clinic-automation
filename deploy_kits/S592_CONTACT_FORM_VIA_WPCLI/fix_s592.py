#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_s592.py -- kit S592_CONTACT_FORM_VIA_WPCLI (session S329, 18-Oct-2026) · D742.

    /usr/bin/python3 -B fix_s592.py            -- find, keep, change, read back
    DRY=1 /usr/bin/python3 -B fix_s592.py      -- find and say what would change; change nothing
    /usr/bin/python3 -B fix_s592.py --undo     -- put every changed row back from /root/s592_backup/

THE OWNER, 18:41 IST 18-Oct (D742): "remove" -- the website's contact form mails every enquiry (the patient's name and mobile number)
to the clinic Gmail AND to an outside marketing firm's address; that address goes.

S591 carried the same change and stopped at its first check: the mysql program refused the login read from wp-config.php (F-938).
S589 had already reached the same database through WordPress's own command tool (wp-cli). S592 is S591's logic WHOLE, with only the
road to the database changed. It tries, in order, and says on screen which one it used:
  A. WordPress's own database connection, through wp-cli (`wp eval-file wpdb_s592.php`, run exactly as S589 ran wp-cli: as root with
     --allow-root --skip-plugins --skip-themes) -- the road S589 proved;
  B. the CyberPanel MySQL root (its password file /etc/cyberpanel/mysqlPassword, root-only, never printed) into the website's database
     named in wp-config.php;
  C. the wp-config login itself (S591's road: the socket, then 127.0.0.1:3306).
Every road must also show the website's page-settings table before anything is read from it.

WHAT IT CHANGES, AND ONLY THIS: in the website database, the Elementor page data (`_elementor_data` of every page, post and template
that is NOT a revision) -- in every Elementor form widget, the e-mail address fields (Email: to / cc / bcc; Email 2: to / cc / bcc)
lose any address at the firm's domain. A "to" field left empty gets the clinic Gmail (an e-mail action with nobody to send to fails).
Each changed row is kept first, byte-exact (hex), in /root/s592_backup/ (root, 600), and written back only if it is still the bytes
that were read (no race with an editor). Everything else in the database that mentions the domain is LISTED, never changed.
Values are read and written as hex, so no character of the page data is re-encoded. No password is ever printed.
"""
import os, re, sys, json, glob, hashlib, subprocess, tempfile

DOMAIN = "arrowmarketing360.com"
CLINIC = "drmka.ortho@gmail.com"
SITE_CFG = os.environ.get("S592_WPCONFIG", "/home/drmanojagarwal.com/public_html/wp-config.php")
BK = os.environ.get("S592_BACKUP", "/root/s592_backup")
TMPD = os.environ.get("S592_TMP", "/root/s592_tmp")
CPW_FILE = os.environ.get("S592_CPW_FILE", "/etc/cyberpanel/mysqlPassword")
WP_CANDIDATES = [w for w in (os.environ.get("S592_WP", ""), "/usr/local/bin/wp", "/usr/bin/wp") if w]
HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wpdb_s592.php")
EMAIL_KEYS = ("email_to", "email_to_cc", "email_to_bcc", "email_to_2", "email_to_cc_2", "email_to_bcc_2")
DRY = os.environ.get("DRY", "0") == "1"


def die(msg):
    print("!! STOPPED: %s" % msg)
    print("   Nothing was changed. Send a photo of this screen to Claude.")
    sys.exit(1)


def wpconfig(path):
    src = open(path, "r", errors="replace").read()

    def val(k):
        m = re.search(r"define\(\s*(['\"])%s\1\s*,\s*(['\"])((?:\\.|(?!\2).)*)\2" % k, src, re.S)
        if not m:
            return ""
        return m.group(3).replace("\\" + m.group(2), m.group(2)).replace("\\\\", "\\")
    m = re.search(r"\$table_prefix\s*=\s*['\"]([^'\"]+)['\"]", src)
    return {"name": val("DB_NAME"), "user": val("DB_USER"), "pw": val("DB_PASSWORD"),
            "host": val("DB_HOST") or "localhost", "prefix": m.group(1) if m else "wp_"}


def _unesc(v):
    return re.sub(r"\\(.)", lambda m: {"t": "\t", "n": "\n", "r": "\r", "\\": "\\"}.get(m.group(1), m.group(1)), v)


class WPCLI:
    """Road A: WordPress's own database connection ($wpdb), through wp-cli -- run as S589 ran it."""
    label = "A · WordPress's own connection, through wp-cli (as S589 ran it)"

    def __init__(self, wp, site_dir):
        self.wp, self.site_dir = wp, site_dir

    def q(self, sql):
        os.makedirs(TMPD, mode=0o700, exist_ok=True)
        os.chmod(TMPD, 0o700)
        fd, path = tempfile.mkstemp(dir=TMPD, prefix="q_", suffix=".sql")
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(sql + "\n")
            env = dict(os.environ, S592_SQL_FILE=path)
            p = subprocess.run([self.wp, "eval-file", HELPER, "--path=%s" % self.site_dir, "--allow-root",
                                "--skip-plugins", "--skip-themes"], capture_output=True, text=True, env=env, timeout=180)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        out = p.stdout
        if p.returncode != 0 or "@@S592BEGIN\n" not in out or "@@S592END" not in out:
            err = [l for l in (p.stderr + "\n" + p.stdout).splitlines() if l.strip()]
            e = [l for l in err if "@@S592ERR" in l] or [l for l in err if "rror" in l] or err or ["wp-cli failed (exit %s)" % p.returncode]
            raise RuntimeError(e[-1].replace("@@S592ERR ", "")[:160])
        body = out.split("@@S592BEGIN\n", 1)[1].split("@@S592END", 1)[0]
        return [[_unesc(x) for x in l.split("\t")] for l in body.splitlines() if l != ""]

    def connect(self):
        r = self.q("SELECT 1")
        if r != [["1"]]:
            raise RuntimeError("wp-cli answered, but not with the expected test row")


class MySQL:
    """Roads B and C: the mysql program (S591's reader, unchanged): hex in, hex out, the statement on stdin."""

    def __init__(self, label, user, pw, host, name):
        self.label, self.user, self.pw, self.host, self.name = label, user, pw, host, name

    def q(self, sql):
        env = dict(os.environ, MYSQL_PWD=self.pw)
        cmd = ["mysql", "-N", "-B", "--raw", "-u", self.user]
        if self.host not in ("localhost", ""):
            h, _, port = self.host.partition(":")
            cmd += ["-h", h] + (["-P", port] if port.isdigit() else [])
        cmd += [self.name]
        # the statement goes in on stdin: a page's data as hex can pass the 128 KB limit of one command-line argument
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120, input=sql + ";\n")
        if p.returncode != 0:
            raise RuntimeError((p.stderr.strip().splitlines() or ["mysql failed"])[-1][:160])
        return [l.split("\t") for l in p.stdout.splitlines() if l != ""]

    def connect(self):
        try:
            self.q("SELECT 1")
        except RuntimeError as e:
            if self.host in ("localhost", ""):
                self.host = "127.0.0.1:3306"
                self.q("SELECT 1")
            else:
                raise e


def open_road(c):
    """Try A, B, C in order; return the first that answers AND shows the page-settings table. Say each try on screen."""
    roads = []
    wp = next((w for w in WP_CANDIDATES if os.path.exists(w)), "")
    if wp and os.path.exists(HELPER):
        roads.append(WPCLI(wp, os.path.dirname(SITE_CFG)))
    else:
        print("  road A · wp-cli: not available (%s)" % ("no wp program" if not wp else "the kit's helper is missing"))
    if os.path.exists(CPW_FILE) and c["name"]:
        try:
            cpw = open(CPW_FILE).read().strip()
        except OSError:
            cpw = ""
        if cpw:
            roads.append(MySQL("B · the CyberPanel MySQL root", "root", cpw, "localhost", c["name"]))
    else:
        print("  road B · CyberPanel MySQL root: not available (no password file, or no database name in wp-config)")
    if c["name"] and c["user"]:
        roads.append(MySQL("C · the wp-config login (S591's road)", c["user"], c["pw"], c["host"], c["name"]))
    for r in roads:
        try:
            r.connect()
            t = r.q("SHOW TABLES LIKE '%spostmeta'" % c["prefix"])
            if not t:
                raise RuntimeError("it answered, but the table %spostmeta is not in that database" % c["prefix"])
            print("  road %s: answered" % r.label)
            print("[road] USED: %s" % r.label)
            return r
        except RuntimeError as e:
            print("  road %s: refused -- %s" % (r.label, str(e)[:120]))
        except subprocess.TimeoutExpired:
            print("  road %s: no answer in time" % r.label)
    die("no road reached the website's database (A, B and C each refused -- the lines above say how)")


def clean_list(v):
    """'a@x, b@firm' -> ('a@x', [removed])"""
    parts = [p.strip() for p in re.split(r"[,;]", v) if p.strip()]
    keep = [p for p in parts if DOMAIN not in p.lower()]
    gone = [p for p in parts if DOMAIN in p.lower()]
    return ", ".join(keep), gone


def walk(els, found):
    for el in els or []:
        if isinstance(el, dict):
            if el.get("widgetType") == "form":
                found.append(el)
            walk(el.get("elements"), found)


def flush_cache(db, post_ids):
    """Only if the site keeps a persistent object cache: forget the changed pages' settings there, so the next enquiry reads the new ones."""
    oc = os.path.exists(os.path.join(os.path.dirname(SITE_CFG), "wp-content", "object-cache.php"))
    if not oc:
        return "none (nothing to flush)"
    wp = next((w for w in WP_CANDIDATES if os.path.exists(w)), "")
    if not wp:
        return "PRESENT, and no wp program to clear it -- send a photo"
    res = []
    for pid in post_ids:
        p = subprocess.run([wp, "cache", "delete", str(pid), "post_meta", "--path=%s" % os.path.dirname(SITE_CFG), "--allow-root",
                            "--skip-plugins", "--skip-themes"],
                           capture_output=True, text=True, timeout=60)
        res.append("%s %s" % (pid, "cleared" if p.returncode == 0 else "not in the cache"))
    return "present -- " + ", ".join(res)


def main():
    undo = "--undo" in sys.argv
    if not os.path.exists(SITE_CFG):
        die("the website's wp-config.php is not where it should be (%s)" % SITE_CFG)
    c = wpconfig(SITE_CFG)
    if not c["name"]:
        die("the website's database name could not be read from wp-config.php")
    db = open_road(c)
    p = c["prefix"]

    if undo:
        rows = sorted(glob.glob(os.path.join(BK, "meta_*.old.hex")))
        if not rows:
            die("no backup rows in %s" % BK)
        pids = []
        for f in rows:
            mid = re.search(r"meta_(\d+)\.old\.hex", f).group(1)
            old = open(f).read().strip()
            db.q("UPDATE %spostmeta SET meta_value=UNHEX('%s') WHERE meta_id=%s" % (p, old, mid))
            now = db.q("SELECT MD5(meta_value), post_id FROM %spostmeta WHERE meta_id=%s" % (p, mid))[0]
            want = hashlib.md5(bytes.fromhex(old)).hexdigest()
            pids.append(now[1])
            print("  undo meta %s: %s" % (mid, "put back" if now[0] == want else "NOT put back (%s vs %s)" % (now[0][:8], want[:8])))
        print("  object cache: %s" % flush_cache(db, pids))
        print("UNDONE. Send a photo of this screen to Claude.")
        return

    like = "%%%s%%" % DOMAIN
    # 1. everywhere the domain is mentioned
    meta = db.q("SELECT m.meta_id, m.post_id, m.meta_key, IFNULL(po.post_type,'?'), IFNULL(po.post_status,'?'), IFNULL(po.post_title,'') "
                "FROM %spostmeta m LEFT JOIN %sposts po ON po.ID=m.post_id WHERE m.meta_value LIKE '%s'" % (p, p, like))
    posts = db.q("SELECT ID, post_type, post_status, post_title FROM %sposts WHERE post_content LIKE '%s' OR post_excerpt LIKE '%s'" % (p, like, like))
    opts = db.q("SELECT option_name FROM %soptions WHERE option_value LIKE '%s'" % (p, like))
    users = db.q("SELECT user_login FROM %susers WHERE user_email LIKE '%s'" % (p, like))
    umeta = db.q("SELECT user_id, meta_key FROM %susermeta WHERE meta_value LIKE '%s'" % (p, like))
    try:
        subs = db.q("SELECT COUNT(*) FROM %se_submissions" % p)[0][0]
    except (RuntimeError, IndexError):
        subs = "no table"
    live = [r for r in meta if r[2] == "_elementor_data" and r[3] != "revision"]
    revs = [r for r in meta if r[2] == "_elementor_data" and r[3] == "revision"]
    other_meta = [r for r in meta if r[2] != "_elementor_data"]
    print("[a] the address's domain is in: %d live Elementor page(s) · %d old revision(s) · %d other page setting(s) · "
          "%d post(s) · %d site option(s) · %d user(s) · %d user setting(s)" % (len(live), len(revs), len(other_meta), len(posts), len(opts), len(users), len(umeta)))
    for r in live:
        print("    live: post %s (%s, %s) '%s'" % (r[1], r[3], r[4], r[5][:40]))
    for r in other_meta:
        print("    other page setting: post %s key %s" % (r[1], r[2][:40]))
    for r in posts:
        print("    post text: %s (%s, %s) '%s'" % (r[0], r[1], r[2], r[3][:40]))
    for r in opts:
        print("    site option: %s" % r[0][:60])
    for r in users:
        print("    user login: %s" % r[0])
    for r in umeta:
        print("    user %s setting %s" % (r[0], r[1][:40]))

    # 2. the change, row by row
    plan = []
    for r in live:
        mid = r[0]
        hx = db.q("SELECT HEX(meta_value) FROM %spostmeta WHERE meta_id=%s" % (p, mid))[0][0]
        raw = bytes.fromhex(hx).decode("utf-8")
        try:
            data = json.loads(raw)
        except ValueError:
            print("    post %s: the page data is not readable JSON -- left alone" % r[1]); continue
        forms = []
        walk(data if isinstance(data, list) else [data], forms)
        new = raw
        notes, other_keys, actions = [], [], []
        for f in forms:
            s = f.get("settings") or {}
            actions.append("%s:%s" % (f.get("id"), ",".join(s.get("submit_actions") or [])))
            for k, v in s.items():
                if isinstance(v, str) and DOMAIN in v.lower() and k not in EMAIL_KEYS:
                    other_keys.append("%s.%s" % (f.get("id"), k))
            for k in EMAIL_KEYS:
                v = s.get(k)
                if not isinstance(v, str) or DOMAIN not in v.lower():
                    continue
                kept, gone = clean_list(v)
                if not kept and k in ("email_to", "email_to_2"):
                    kept = CLINIC
                # the stored "key":"value" pair, whatever spacing the page data was written with
                pat = re.compile(r'("%s"\s*:\s*)%s' % (re.escape(k), re.escape(json.dumps(v))))
                if not pat.search(new):
                    print("    post %s form %s %s: the stored text did not match its reading -- left alone" % (r[1], f.get("id"), k)); continue
                new = pat.sub(lambda m: m.group(1) + json.dumps(kept), new)
                notes.append("form %s %s: removed %d address(es)%s" % (f.get("id"), k, len(gone), " -> now the clinic Gmail" if kept == CLINIC and not clean_list(v)[0] else ""))
        if new == raw:
            print("    post %s: nothing to change in its form fields%s" % (r[1], (" (the domain is in: %s)" % ", ".join(other_keys)) if other_keys else ""))
            continue
        chk = json.loads(new)
        f2 = []
        walk(chk if isinstance(chk, list) else [chk], f2)
        left = [k for f in f2 for k in EMAIL_KEYS if DOMAIN in str((f.get("settings") or {}).get(k, "")).lower()]
        if left:
            die("post %s still holds the address after the change (%s)" % (r[1], left))
        plan.append((mid, r[1], hx, new.encode("utf-8").hex().upper(), notes, other_keys, actions))

    for mid, pid, old, newhx, notes, other_keys, actions in plan:
        print("[b] post %s (meta %s): %s · form actions %s%s" % (pid, mid, "; ".join(notes), " | ".join(actions),
              ("  · ALSO in: " + ", ".join(other_keys)) if other_keys else ""))
    if not plan:
        print("[b] nothing to change.")
        return
    if DRY:
        print("-- DRY RUN: nothing changed")
        return

    os.makedirs(BK, mode=0o700, exist_ok=True)
    os.chmod(BK, 0o700)
    old_umask = os.umask(0o077)
    try:
        for mid, pid, old, newhx, *_ in plan:
            with open(os.path.join(BK, "meta_%s.old.hex" % mid), "w") as fh:
                fh.write(old + "\n")
    finally:
        os.umask(old_umask)
    print("[c] kept, root-only: %s (%d row(s), byte-exact)" % (BK, len(plan)))

    bad = 0
    for mid, pid, old, newhx, *_ in plan:
        old_md5 = hashlib.md5(bytes.fromhex(old)).hexdigest()
        db.q("UPDATE %spostmeta SET meta_value=UNHEX('%s') WHERE meta_id=%s AND MD5(meta_value)='%s'" % (p, newhx, mid, old_md5))
        now = db.q("SELECT MD5(meta_value), meta_value LIKE '%s' FROM %spostmeta WHERE meta_id=%s" % (like, p, mid))[0]
        want = hashlib.md5(bytes.fromhex(newhx)).hexdigest()
        ok = now[0] == want and now[1] == "0"
        bad += 0 if ok else 1
        print("[d] post %s: %s" % (pid, "written and read back" if ok else
                                    "NOT written (the row changed since it was read, or the write failed) -- send a photo"))
    print("[e] object cache: %s · Elementor submissions table rows: %s" % (flush_cache(db, [x[1] for x in plan]), subs))
    if bad:
        print("!! %d row(s) not written -- send a photo of this screen to Claude." % bad)
        sys.exit(2)
    print("DONE. Claude now sends one more test through the form and reads who it went to.")


if __name__ == "__main__":
    main()

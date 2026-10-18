#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_s591.py -- kit S591_CONTACT_FORM_ONE_RECIPIENT (session S326, 18-Oct-2026) · D742.

    /usr/bin/python3 -B fix_s591.py            -- find, keep, change, read back
    DRY=1 /usr/bin/python3 -B fix_s591.py      -- find and say what would change; change nothing
    /usr/bin/python3 -B fix_s591.py --undo     -- put every changed row back from /root/s591_backup/

THE OWNER, 18:41 IST 18-Oct (D742): "remove" -- the website's contact form mails every enquiry (the patient's name and mobile number)
to the clinic Gmail AND to an outside marketing firm's address; that address goes.

WHAT IT CHANGES, AND ONLY THIS: in the website database, the Elementor page data (`_elementor_data` of every page, post and template
that is NOT a revision) -- in every Elementor form widget, the e-mail address fields (Email: to / cc / bcc; Email 2: to / cc / bcc)
lose any address at the firm's domain. A "to" field left empty gets the clinic Gmail (an e-mail action with nobody to send to fails).
Each changed row is kept first, byte-exact (hex), in /root/s591_backup/ (root, 600), and written back only if it is still the bytes
that were read (no race with an editor). Everything else in the database that mentions the domain is LISTED, never changed.
Values are read and written as hex, so no character of the page data is re-encoded.
"""
import os, re, sys, json, glob, hashlib, subprocess

DOMAIN = "arrowmarketing360.com"
CLINIC = "drmka.ortho@gmail.com"
SITE_CFG = os.environ.get("S591_WPCONFIG", "/home/drmanojagarwal.com/public_html/wp-config.php")
BK = os.environ.get("S591_BACKUP", "/root/s591_backup")
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


class DB:
    def __init__(self, c):
        self.c = c
        self.host = c["host"]

    def q(self, sql):
        env = dict(os.environ, MYSQL_PWD=self.c["pw"])
        cmd = ["mysql", "-N", "-B", "--raw", "-u", self.c["user"]]
        if self.host not in ("localhost", ""):
            h, _, port = self.host.partition(":")
            cmd += ["-h", h] + (["-P", port] if port.isdigit() else [])
        cmd += [self.c["name"]]
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


def main():
    undo = "--undo" in sys.argv
    if not os.path.exists(SITE_CFG):
        die("the website's wp-config.php is not where it should be (%s)" % SITE_CFG)
    c = wpconfig(SITE_CFG)
    if not (c["name"] and c["user"]):
        die("the website's database settings could not be read")
    db = DB(c)
    try:
        db.connect()
    except RuntimeError as e:
        die("the website's database refused the login (%s)" % e)
    p = c["prefix"]

    if undo:
        rows = sorted(glob.glob(os.path.join(BK, "meta_*.old.hex")))
        if not rows:
            die("no backup rows in %s" % BK)
        for f in rows:
            mid = re.search(r"meta_(\d+)\.old\.hex", f).group(1)
            old = open(f).read().strip()
            db.q("UPDATE %spostmeta SET meta_value=UNHEX('%s') WHERE meta_id=%s" % (p, old, mid))
            now = db.q("SELECT MD5(meta_value) FROM %spostmeta WHERE meta_id=%s" % (p, mid))[0][0]
            want = hashlib.md5(bytes.fromhex(old)).hexdigest()
            print("  undo meta %s: %s" % (mid, "put back" if now == want else "NOT put back (%s vs %s)" % (now[:8], want[:8])))
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
    except RuntimeError:
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

    for mid, pid, old, newhx, *_ in plan:
        old_md5 = hashlib.md5(bytes.fromhex(old)).hexdigest()
        db.q("UPDATE %spostmeta SET meta_value=UNHEX('%s') WHERE meta_id=%s AND MD5(meta_value)='%s'" % (p, newhx, mid, old_md5))
        now = db.q("SELECT MD5(meta_value), meta_value LIKE '%s' FROM %spostmeta WHERE meta_id=%s" % (like, p, mid))[0]
        want = hashlib.md5(bytes.fromhex(newhx)).hexdigest()
        print("[d] post %s: %s" % (pid, "written and read back" if now[0] == want and now[1] == "0" else
                                    "NOT written (the row changed since it was read, or the write failed) -- send a photo"))
    oc = os.path.exists(os.path.join(os.path.dirname(SITE_CFG), "wp-content", "object-cache.php"))
    print("[e] object cache file: %s · Elementor submissions table rows: %s" % ("present" if oc else "none (nothing to flush)", subs))
    print("DONE. Claude now sends one more test through the form and reads who it went to.")


if __name__ == "__main__":
    main()

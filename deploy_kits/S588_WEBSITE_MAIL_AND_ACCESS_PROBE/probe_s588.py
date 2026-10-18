#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_s588.py -- kit S588_WEBSITE_MAIL_AND_ACCESS_PROBE (session S326, 18-Oct-2026). READ ONLY.

    /usr/bin/python3 -B probe_s588.py            (as root, on the VPS)

Two questions from the Growth chat (board message growth_S320_1, Runbook v241 §2A item 5), answered from the box itself:
  MAIL    -- why the website (WordPress, drmanojagarwal.com) sends no mail: the mail program's settings, whether the
             server can reach Gmail's doors 25 / 587 / 465, the queue, the mail log's last fortnight, the site's mail plugins.
  ACCESS  -- whether the website vendor still holds any way in: Linux logins with a shell, the last logins, SSH keys,
             the SSH settings, FTP users, CyberPanel users, WordPress administrators, the doors open to the world.

What it does NOT do: change any setting, file, user, key or database row; restart anything; send any mail.
It writes ONE file, its own report: /root/finance/s588_probe.json (the nightly backup carries /root/finance/*.json,
so the assistant reads the whole report the next morning). It never prints or stores a password, a key's body or a
token: database passwords are read only to log in, handed to mysql in its environment, and dropped. E-mail addresses
are masked to their first letter and domain.
"""
import os, re, json, glob, socket, subprocess, datetime, time

REPORT = os.environ.get("S588_REPORT", "/root/finance/s588_probe.json")
R = {"kit": "S588_WEBSITE_MAIL_AND_ACCESS_PROBE", "read_only": True}
SCREEN = []


def now_ist():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)).strftime("%d-%b-%Y %H:%M IST")


def run(cmd, timeout=20, env=None, inp=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, input=inp)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "not installed"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except Exception as e:                                     # noqa: BLE001
        return 1, "", str(e)[:200]


def mask_email(s):
    return re.sub(r"\b([A-Za-z0-9])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", r"\1***@\2", s or "")


def mysql(sql, user, pw, host="localhost", db=None):
    """Rows as lists of strings, or (None, why). The password goes in the child's environment only."""
    env = dict(os.environ)
    env["MYSQL_PWD"] = pw
    cmd = ["mysql", "-N", "-B", "-u", user]
    if host and host not in ("localhost", "127.0.0.1"):
        h, _, port = host.partition(":")
        cmd += ["-h", h] + (["-P", port] if port.isdigit() else [])
    if db:
        cmd += [db]
    cmd += ["-e", sql]
    rc, out, err = run(cmd, env=env)
    env["MYSQL_PWD"] = ""
    if rc != 0:
        return None, (err.strip().splitlines() or ["mysql failed"])[-1][:160]
    return [l.split("\t") for l in out.splitlines() if l.strip()], ""


def section(name, fn):
    try:
        R[name] = fn()
    except Exception as e:                                     # noqa: BLE001
        R[name] = {"error": "could not read: %s" % str(e)[:200]}


# ------------------------------------------------------------------------------------------------------------- MAIL
def mail_settings():
    rc, out, err = run(["postconf", "-n"])
    keep = ("relayhost", "myhostname", "mydomain", "myorigin", "inet_interfaces", "inet_protocols", "mydestination",
            "smtp_sasl_auth_enable", "smtp_sasl_password_maps", "smtp_tls_security_level", "default_transport",
            "relay_transport", "sender_dependent_relayhost_maps", "smtpd_milters", "non_smtpd_milters")
    d = {}
    for l in out.splitlines():
        k, _, v = l.partition(" = ")
        if k.strip() in keep:
            d[k.strip()] = v.strip()
    rc2, out2, _ = run(["systemctl", "is-active", "postfix"])
    return {"postconf_rc": rc, "postfix_active": out2.strip(), "settings": d}


def doors():
    out = {}
    for host, port in (("gmail-smtp-in.l.google.com", 25), ("smtp.gmail.com", 587), ("smtp.gmail.com", 465)):
        t0 = time.time()
        try:
            s = socket.create_connection((host, port), timeout=7)
            banner = ""
            if port in (25, 587):
                s.settimeout(7)
                try:
                    banner = s.recv(120).decode("ascii", "replace").strip()[:60]
                except Exception:                              # noqa: BLE001
                    banner = "(no greeting)"
            s.close()
            out["%s:%d" % (host, port)] = "open%s" % ((" -- " + banner) if banner else "")
        except Exception as e:                                 # noqa: BLE001
            out["%s:%d" % (host, port)] = "blocked or unreachable (%s, %.0fs)" % (type(e).__name__, time.time() - t0)
    return out


def queue():
    rc, out, err = run(["postqueue", "-p"])
    last = (out.strip().splitlines() or [err.strip() or "?"])[-1]
    return {"rc": rc, "summary": last[:120]}


def mail_log():
    files = [f for f in ("/var/log/mail.log", "/var/log/mail.log.1", "/var/log/maillog", "/var/log/maillog-1")
             if os.path.exists(f)]
    cnt = {"sent": 0, "deferred": 0, "bounced": 0, "expired": 0}
    tail, reasons = [], {}
    for f in files:
        try:
            with open(f, "r", errors="replace") as fh:
                for l in fh:
                    m = re.search(r"status=(sent|deferred|bounced|expired)", l)
                    if not m:
                        continue
                    cnt[m.group(1)] += 1
                    if m.group(1) != "sent":
                        why = re.sub(r"\d+\.\d+\.\d+\.\d+", "<ip>", l.split("status=", 1)[1])[:160]
                        key = re.sub(r"\s+", " ", why)[:110]
                        reasons[key] = reasons.get(key, 0) + 1
                    tail.append(mask_email(re.sub(r"\s+", " ", l.strip()))[:240])
        except OSError as e:
            tail.append("could not read %s: %s" % (f, e))
    rc, jout, _ = run(["journalctl", "-u", "postfix", "--since", "-14 days", "--no-pager", "-q"], timeout=40)
    jcnt = {k: len(re.findall(r"status=%s" % k, jout)) for k in cnt}
    jtail = [mask_email(re.sub(r"\s+", " ", l))[:240] for l in jout.splitlines() if "status=" in l][-8:]
    top = sorted(reasons.items(), key=lambda kv: -kv[1])[:6]
    return {"files": files, "counts_in_files": cnt, "counts_journal_14d": jcnt, "why_not_sent": top,
            "last_lines": (tail[-8:] or jtail)}


def wp_sites():
    sites = []
    for cfg in sorted(glob.glob("/home/*/public_html/wp-config.php")):
        site = cfg.split("/")[2]
        d = {"site": site}
        try:
            src = open(cfg, "r", errors="replace").read()
        except OSError as e:
            d["error"] = str(e); sites.append(d); continue
        def val(k):
            m = re.search(r"define\(\s*['\"]%s['\"]\s*,\s*['\"]([^'\"]*)['\"]" % k, src)
            return m.group(1) if m else ""
        name, user, pw, host = val("DB_NAME"), val("DB_USER"), val("DB_PASSWORD"), val("DB_HOST") or "localhost"
        m = re.search(r"\$table_prefix\s*=\s*['\"]([^'\"]+)['\"]", src)
        p = m.group(1) if m else "wp_"
        d["mail_constants_in_config"] = sorted(set(re.findall(r"define\(\s*['\"](WPMS_[A-Z_]+|SMTP_[A-Z_]+|FLUENTMAIL[A-Z_]*)['\"]", src)))
        if not (name and user):
            d["error"] = "no database settings read"; sites.append(d); continue
        rows, why = mysql("SELECT option_value FROM %soptions WHERE option_name='active_plugins'" % p, user, pw, host, name)
        if rows is None:
            d["error"] = why; sites.append(d); continue
        plug = re.findall(r'"([^"/]+)/[^"]+\.php"', rows[0][0]) if rows else []
        d["active_plugins"] = plug
        d["mail_plugins_active"] = [x for x in plug if re.search(r"smtp|mail|fluent", x, re.I)]
        rows, _ = mysql("SELECT option_name FROM %soptions WHERE option_name IN ('wp_mail_smtp','fluentmail-settings',"
                        "'postman_options','swpsmtp_options','easy_wp_smtp')" % p, user, pw, host, name)
        d["smtp_settings_present"] = [r[0] for r in (rows or [])]
        rows, _ = mysql("SELECT option_value FROM %soptions WHERE option_name='admin_email'" % p, user, pw, host, name)
        d["admin_email"] = mask_email(rows[0][0]) if rows else ""
        rows, why = mysql("SELECT u.user_login, u.user_registered, u.user_email, m.meta_value FROM %susers u JOIN %susermeta m "
                          "ON m.user_id=u.ID AND m.meta_key='%scapabilities' ORDER BY u.ID" % (p, p, p), user, pw, host, name)
        d["users"] = [{"login": r[0], "registered": r[1][:10], "email": mask_email(r[2]),
                       "roles": re.findall(r'"([a-z_]+)";b:1', r[3])} for r in (rows or [])]
        if rows is None:
            d["users_error"] = why
        pw = ""
        sites.append(d)
    return sites


def spf():
    out = {}
    for dom in ("drmanojagarwal.com",):
        rc, o, e = run(["dig", "+short", "TXT", dom], timeout=10)
        if rc == 127:
            rc, o, e = run(["host", "-t", "TXT", dom], timeout=10)
        out[dom] = [l.strip()[:200] for l in o.splitlines() if "spf" in l.lower()] or ["(no SPF record seen)" if rc == 0 else "(could not ask: %s)" % e.strip()[:60]]
    return out


# ----------------------------------------------------------------------------------------------------------- ACCESS
NOSHELL = ("nologin", "false", "sync", "halt", "shutdown")


def shell_users():
    out = []
    for l in open("/etc/passwd"):
        f = l.rstrip("\n").split(":")
        if len(f) >= 7 and not f[6].endswith(NOSHELL):
            out.append({"user": f[0], "uid": f[2], "home": f[5], "shell": f[6]})
    return out


def last_logins():
    rc, out, err = run(["last", "-n", "60", "-w", "-F"])
    seen, rows = set(), []
    for l in out.splitlines():
        if not l.strip() or l.startswith(("reboot", "wtmp", "shutdown")):
            continue
        p = l.split()
        key = (p[0], p[2] if len(p) > 2 else "")
        if key in seen:
            continue
        seen.add(key)
        rows.append(re.sub(r"\s+", " ", l)[:140])
        if len(rows) >= 15:
            break
    rc2, lo, _ = run(["lastlog"])
    ever = [re.sub(r"\s+", " ", l)[:120] for l in lo.splitlines()[1:] if "**Never logged in**" not in l]
    return {"recent_distinct": rows, "lastlog_ever_logged_in": ever}


def ssh_keys():
    files = ["/root/.ssh/authorized_keys", "/root/.ssh/authorized_keys2"] + glob.glob("/home/*/.ssh/authorized_keys*")
    out = []
    for f in files:
        if not os.path.exists(f):
            continue
        try:
            for i, l in enumerate(open(f, "r", errors="replace")):
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                m = re.search(r"(ssh-(rsa|ed25519|dss)|ecdsa-sha2-\S+|sk-\S+)\s+(\S+)(?:\s+(.*))?$", l)
                if not m:
                    out.append({"file": f, "line": i + 1, "type": "unreadable"}); continue
                rc, fp, _ = run(["ssh-keygen", "-lf", "/dev/stdin"], inp="%s %s\n" % (m.group(1), m.group(3)))
                out.append({"file": f, "line": i + 1, "type": m.group(1), "fingerprint": (fp.split()[1] if fp.split()[1:] else "?"),
                            "comment": mask_email((m.group(4) or "").strip())[:60],
                            "options": l[:m.start()].strip()[:60]})
        except OSError as e:
            out.append({"file": f, "error": str(e)})
    return out


def sshd():
    rc, out, err = run(["sshd", "-T"])
    keep = ("port", "permitrootlogin", "passwordauthentication", "pubkeyauthentication", "kbdinteractiveauthentication",
            "challengeresponseauthentication", "allowusers", "allowgroups")
    return {k: v for k, _, v in (l.partition(" ") for l in out.splitlines()) if k in keep} or {"error": err.strip()[:120]}


def cyberpanel():
    try:
        pw = open("/etc/cyberpanel/mysqlPassword").read().strip()
    except OSError as e:
        return {"error": "no CyberPanel database password file (%s)" % e.strerror}
    d = {}
    cols, why = mysql("SHOW COLUMNS FROM users", "root", pw, db="cyberpanel")
    if cols is None:
        d["ftp_error"] = why
    else:
        names = [c[0] for c in cols]
        pick = [c for c in names if c.lower() in ("user", "dir", "status", "ulbandwidth", "quotasize", "domain_id", "date")]
        rows, why = mysql("SELECT %s FROM users" % ", ".join("`%s`" % c for c in pick or names[:1]), "root", pw, db="cyberpanel")
        d["ftp_users"] = [dict(zip(pick, r)) for r in (rows or [])]
        if rows is None:
            d["ftp_error"] = why
    cols, why = mysql("SHOW COLUMNS FROM loginSystem_administrator", "root", pw, db="cyberpanel")
    if cols is None:
        d["panel_error"] = why
    else:
        names = [c[0] for c in cols]
        pick = [c for c in names if c.lower() in ("username", "firstname", "lastname", "email", "type", "api", "securitylevel",
                                                   "state", "acl_id", "owner")]
        rows, why = mysql("SELECT %s FROM loginSystem_administrator" % ", ".join("`%s`" % c for c in pick), "root", pw, db="cyberpanel")
        d["panel_users"] = [{k: (mask_email(v) if k.lower() == "email" else v) for k, v in zip(pick, r)} for r in (rows or [])]
        if rows is None:
            d["panel_error"] = why
    pw = ""
    rc, out, _ = run(["systemctl", "is-active", "pure-ftpd"])
    d["pure_ftpd"] = out.strip()
    return d


def listening():
    rc, out, err = run(["ss", "-ltnpH"])
    rows = []
    for l in out.splitlines():
        p = l.split()
        if len(p) < 4:
            continue
        local = p[3]
        proc = re.search(r'users:\(\("([^"]+)"', l)
        world = not (local.startswith("127.") or local.startswith("[::1]") or local.startswith("localhost"))
        rows.append({"addr": local, "proc": proc.group(1) if proc else "?", "world": world})
    rc2, fw, _ = run(["firewall-cmd", "--list-all"])
    rc3, uf, _ = run(["ufw", "status"])
    return {"listening": rows, "firewalld": fw.strip()[:600] if rc2 == 0 else "(not running)",
            "ufw": uf.strip()[:300] if rc3 == 0 else "(not running)"}


def main():
    R["when"] = now_ist()
    R["host"] = socket.gethostname()
    for name, fn in (("mail_settings", mail_settings), ("outbound_doors", doors), ("mail_queue", queue),
                     ("mail_log", mail_log), ("spf", spf), ("wordpress", wp_sites),
                     ("shell_users", shell_users), ("logins", last_logins), ("ssh_keys", ssh_keys), ("sshd", sshd),
                     ("cyberpanel", cyberpanel), ("doors_open", listening)):
        section(name, fn)

    # ---- the screen: short, plain, nothing secret
    ms = R.get("mail_settings", {})
    st = ms.get("settings", {}) if isinstance(ms, dict) else {}
    SCREEN.append("S588 READ-ONLY CHECK -- %s -- nothing was changed" % R["when"])
    SCREEN.append("")
    SCREEN.append("MAIL")
    SCREEN.append("  mail program: %s · relay: %s" % (ms.get("postfix_active", "?"), st.get("relayhost") or "none (sends direct)"))
    for k, v in (R.get("outbound_doors") or {}).items():
        SCREEN.append("  door %-32s %s" % (k, v[:50]))
    q = R.get("mail_queue", {})
    SCREEN.append("  waiting in the queue: %s" % (q.get("summary", "?") if isinstance(q, dict) else "?"))
    ml = R.get("mail_log", {})
    if isinstance(ml, dict):
        c = ml.get("counts_in_files") if any((ml.get("counts_in_files") or {}).values()) else ml.get("counts_journal_14d")
        SCREEN.append("  mail log: sent %s · deferred %s · bounced %s" % ((c or {}).get("sent", "?"), (c or {}).get("deferred", "?"), (c or {}).get("bounced", "?")))
        for why, n in (ml.get("why_not_sent") or [])[:2]:
            SCREEN.append("  not sent x%d: %s" % (n, why[:90]))
    for s in (R.get("wordpress") or []) if isinstance(R.get("wordpress"), list) else []:
        if s.get("error"):
            SCREEN.append("  website %s: %s" % (s["site"], s["error"][:70]))
        else:
            SCREEN.append("  website %s: mail plugin %s · %d plugins on" % (s["site"], ", ".join(s.get("mail_plugins_active") or []) or "none", len(s.get("active_plugins") or [])))
    SCREEN.append("")
    SCREEN.append("ACCESS")
    su = R.get("shell_users")
    SCREEN.append("  logins with a shell: %s" % (", ".join(u["user"] for u in su) if isinstance(su, list) else "?"))
    sk = R.get("ssh_keys")
    if isinstance(sk, list):
        SCREEN.append("  SSH keys: %d -- %s" % (len(sk), "; ".join("%s %s" % (k.get("file", "").split("/")[2] if k.get("file", "").startswith("/home/") else "root",
                                                                     k.get("comment") or "(no name)") for k in sk)[:120]))
    sd = R.get("sshd", {})
    SCREEN.append("  SSH password login: %s · root login: %s" % (sd.get("passwordauthentication", "?"), sd.get("permitrootlogin", "?")))
    cp = R.get("cyberpanel", {})
    if isinstance(cp, dict) and cp.get("error"):
        SCREEN.append("  FTP / CyberPanel users: %s" % cp["error"][:90])
    elif isinstance(cp, dict):
        SCREEN.append("  FTP (%s): %s" % (cp.get("pure_ftpd", "?"), ", ".join(str(u.get("User") or u.get("user") or list(u.values())[:1]) for u in cp.get("ftp_users") or []) or cp.get("ftp_error", "none")))
        SCREEN.append("  CyberPanel users: %s" % (", ".join(str(u.get("userName") or u.get("username") or "?") for u in cp.get("panel_users") or []) or cp.get("panel_error", "none")))
    for s in (R.get("wordpress") or []) if isinstance(R.get("wordpress"), list) else []:
        adm = [u["login"] for u in s.get("users") or [] if "administrator" in u.get("roles", [])]
        SCREEN.append("  WordPress admins (%s): %s" % (s["site"], ", ".join(adm) or s.get("users_error", "none")))
    lo = R.get("doors_open", {})
    if isinstance(lo, dict):
        w = sorted({(r["addr"].rsplit(":", 1)[-1], r["proc"]) for r in lo.get("listening", []) if r.get("world")}, key=lambda x: int(x[0]) if x[0].isdigit() else 0)
        SCREEN.append("  doors open to the world: %s" % ", ".join("%s %s" % x for x in w)[:150])
    SCREEN.append("")
    try:
        tmp = REPORT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(R, fh, ensure_ascii=False, indent=1)
        os.chmod(tmp, 0o600)
        os.replace(tmp, REPORT)
        SCREEN.append("Full report: %s (the assistant reads it). Send a photo of this screen to Claude." % REPORT)
    except OSError as e:
        SCREEN.append("The full report could not be written (%s). Send a photo of this screen to Claude." % e.strerror)
    print("\n".join(SCREEN))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""email_agent.py — the ping-pong Gmail query agent (S194 ⭐5).

Reads the clinic Gmail for command emails FROM a trusted sender, runs the
READ-ONLY dr_query tool, and replies with the answer in the same thread.

SAFE BY CONSTRUCTION:
  * dr_query opens finance.db mode=ro — it physically cannot write; its `sql`
    mode is SELECT/WITH only. This agent NEVER runs anything else.
  * Only UNSEEN mail whose From is in `trusted` and whose Subject starts with
    the trigger is processed; everything else is left untouched.
  * The reply is sent ONLY to the matched trusted address, never to the raw
    From — so a spoofed From cannot exfiltrate anything (worst case: the owner
    gets an email he didn't ask for).
  * No secret is ever printed or logged. The app password lives only in the
    root-only config file.

Config: /root/deploy/email_agent.json  (see email_agent.example.json)
  { "user": "drmka.ortho@gmail.com", "app_password": "<16-char app password>",
    "trusted": ["drmanojkragarwal@gmail.com","drmka.ortho@gmail.com"],
    "subject_trigger": "Q:", "imap_host": "imap.gmail.com",
    "smtp_host": "smtp.gmail.com", "smtp_port": 465,
    "python": "/usr/bin/python3", "dr_query": "/root/deploy/dr_query.py",
    "max_reply_chars": 12000, "cmd_timeout_s": 25 }

Run:
  python3 email_agent.py --once       # one poll — this is what the timer runs
  python3 email_agent.py --selftest   # offline: config + dr_query, no network
"""
import email, imaplib, json, os, shlex, smtplib, subprocess, sys, time
from email.message import EmailMessage
from email.utils import parseaddr

CONFIG = os.environ.get("EMAIL_AGENT_CONFIG", "/root/deploy/email_agent.json")
ALLOWED = {"day", "marg", "cash", "custody", "flags", "tables", "sql", "help"}
LOG = os.environ.get("EMAIL_AGENT_LOG", "/root/deploy/email_agent.log")


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
    print(line)


def load_config():
    with open(CONFIG, encoding="utf-8") as fh:
        c = json.load(fh)
    c.setdefault("subject_trigger", "Q:")
    c.setdefault("imap_host", "imap.gmail.com")
    c.setdefault("smtp_host", "smtp.gmail.com")
    c.setdefault("smtp_port", 465)
    c.setdefault("python", sys.executable or "/usr/bin/python3")
    c.setdefault("dr_query", "/root/deploy/dr_query.py")
    c.setdefault("max_reply_chars", 12000)
    c.setdefault("cmd_timeout_s", 25)
    c["trusted"] = [a.strip().lower() for a in c.get("trusted", []) if a.strip()]
    return c


def run_query(cfg, command):
    """command is the text after the trigger, e.g. 'cash 30' or 'sql SELECT ...'.
    Returns (ok, text). Only the allowlisted verbs reach dr_query."""
    command = command.strip()
    if not command or command.lower() in ("help", "?"):
        return True, ("Commands (read-only):\n"
                      "  day <YYYY-MM-DD>\n  marg <YYYY-MM-DD>\n  cash <N days>\n"
                      "  custody\n  flags [YYYY-MM-DD]\n  tables\n  sql <SELECT ...>\n"
                      "Send as the email subject, e.g.  Q: cash 30")
    try:
        parts = shlex.split(command)
    except ValueError:
        return False, "Could not parse the command."
    if not parts:
        return False, "Empty command."
    verb = parts[0].lower()
    if verb not in ALLOWED:
        return False, ("'%s' is not an allowed command. Allowed: %s"
                       % (verb, ", ".join(sorted(ALLOWED))))
    if verb == "sql":
        # everything after 'sql' is ONE query arg; dr_query enforces SELECT-only
        query = command[command.lower().index("sql") + 3:].strip()
        argv = [cfg["python"], cfg["dr_query"], "sql", query]
    else:
        argv = [cfg["python"], cfg["dr_query"]] + parts
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=cfg["cmd_timeout_s"])
    except subprocess.TimeoutExpired:
        return False, "The query took too long and was stopped."
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr.strip() else "")
    out = out.strip() or "(no output)"
    if len(out) > cfg["max_reply_chars"]:
        out = out[:cfg["max_reply_chars"]] + "\n… (truncated)"
    return (p.returncode == 0), out


def process_once(cfg):
    M = imaplib.IMAP4_SSL(cfg["imap_host"])
    try:
        M.login(cfg["user"], cfg["app_password"])
        M.select("INBOX")
        typ, data = M.search(None, "UNSEEN")
        ids = data[0].split() if data and data[0] else []
        log("poll: %d unseen" % len(ids))
        handled = 0
        for num in ids:
            typ, md = M.fetch(num, "(RFC822)")
            if typ != "OK" or not md or not md[0]:
                continue
            msg = email.message_from_bytes(md[0][1])
            frm = parseaddr(msg.get("From", ""))[1].strip().lower()
            subj = (msg.get("Subject", "") or "").strip()
            trig = cfg["subject_trigger"]
            if frm not in cfg["trusted"]:
                continue                      # not trusted — leave untouched
            if not subj.lower().startswith(trig.lower()):
                continue                      # not a command — leave untouched
            command = subj[len(trig):].strip()
            log("cmd from %s: %r" % (frm, command))
            ok, text = run_query(cfg, command)
            # reply ONLY to the matched trusted address
            reply = EmailMessage()
            reply["From"] = cfg["user"]
            reply["To"] = frm
            reply["Subject"] = ("Re: " + subj)[:200]
            mid = msg.get("Message-ID")
            if mid:
                reply["In-Reply-To"] = mid
                reply["References"] = mid
            body = ("%s\n\n%s\n\n— clinic query agent (read-only)"
                    % (("Result:" if ok else "Could not run that:"), text))
            reply.set_content(body)
            with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"]) as S:
                S.login(cfg["user"], cfg["app_password"])
                S.send_message(reply)
            M.store(num, "+FLAGS", "\\Seen")
            handled += 1
        log("handled %d command(s)" % handled)
        return handled
    finally:
        try:
            M.logout()
        except Exception:
            pass


def selftest():
    # offline: config shape + dr_query is present and read-only. No network.
    problems = []
    if not os.path.exists(CONFIG):
        problems.append("config missing: %s (copy email_agent.example.json)" % CONFIG)
    else:
        try:
            cfg = load_config()
            for k in ("user", "app_password", "trusted"):
                if not cfg.get(k):
                    problems.append("config: '%s' is empty" % k)
            if cfg.get("app_password", "").startswith("<"):
                problems.append("config: app_password still the placeholder")
        except Exception as e:
            problems.append("config unreadable: %s" % e)
    dq = "/root/deploy/dr_query.py"
    try:
        cfg2 = load_config() if os.path.exists(CONFIG) else {}
        dq = cfg2.get("dr_query", dq)
    except Exception:
        pass
    if not os.path.exists(dq):
        problems.append("dr_query not found: %s" % dq)
    else:
        r = subprocess.run([sys.executable, dq, "selftest"], capture_output=True, text=True, timeout=20)
        if "SELFTEST OK" not in (r.stdout or ""):
            problems.append("dr_query selftest did not pass")
    # command router refuses non-allowlisted verbs (no network involved)
    ok_bad, _ = run_query({"python": sys.executable, "dr_query": dq,
                           "cmd_timeout_s": 10, "max_reply_chars": 999}, "rm -rf /")
    if ok_bad:
        problems.append("router accepted a non-allowlisted command!")
    if problems:
        print("SELFTEST FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("SELFTEST OK — config present, dr_query read-only, router allowlist enforced.")
    return 0


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--once":
        cfg = load_config()
        process_once(cfg)
        return 0
    print("usage: email_agent.py [--once | --selftest]")
    return 2


if __name__ == "__main__":
    sys.exit(main())

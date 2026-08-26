#!/usr/bin/env python3
"""email_agent.py — the ping-pong Gmail query agent (S194 ⭐5, hardened S195).

Reads the clinic Gmail for command emails FROM a trusted sender, runs the
READ-ONLY dr_query tool, and replies with the answer in the same thread.

SAFE BY CONSTRUCTION:
  * dr_query opens finance.db mode=ro — it physically cannot write; its `sql`
    mode is SELECT/WITH only. This agent NEVER runs anything else.
  * Only mail whose From is in `trusted` and whose Subject starts with the
    trigger is processed; everything else is left untouched.
  * The reply is sent ONLY to the matched trusted address, never to the raw
    From — so a spoofed From cannot exfiltrate anything (worst case: the owner
    gets an email he didn't ask for).
  * No secret is ever printed or logged. The app password lives only in the
    root-only config file.

S195 HARDENING (owner asked S194):
  (a) "Already answered" is tracked with a Gmail LABEL (`done_label`), NOT the
      read/unread flag. A `Q:` the owner opens (reads) before the 3-min poll is
      therefore still answered — the old `UNSEEN` filter skipped read mail and
      missed the 18:27 `Q: sql …`. The poll asks Gmail for `subject:<trigger>
      -label:<done_label>` so it stays server-side-narrow (no full-inbox fetch),
      and every message is re-checked for the label before replying (no double
      reply). The label is applied only AFTER a reply is actually sent.
  (b) ALWAYS reply, even on error. If the command errors OR the query itself
      raises, an error reply still goes back so the owner is never left waiting
      in silence. The message is marked done only when a reply was truly sent;
      a transient send failure leaves it for the next poll to retry.

Config: /root/deploy/email_agent.json  (see email_agent.example.json)
  { "user": "drmka.ortho@gmail.com", "app_password": "<16-char app password>",
    "trusted": ["drmanojkragarwal@gmail.com","drmka.ortho@gmail.com"],
    "subject_trigger": "Q:", "done_label": "clinic-agent-done",
    "imap_host": "imap.gmail.com", "smtp_host": "smtp.gmail.com",
    "smtp_port": 465, "python": "/usr/bin/python3",
    "dr_query": "/root/deploy/dr_query.py", "max_reply_chars": 12000,
    "cmd_timeout_s": 25, "max_per_poll": 25 }

Run:
  python3 email_agent.py --once       # one poll — this is what the timer runs
  python3 email_agent.py --selftest   # offline: config + dr_query, no network
"""
import email, imaplib, json, os, re, shlex, smtplib, subprocess, sys, time
from email.message import EmailMessage
from email.header import decode_header, make_header
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
    c.setdefault("done_label", "clinic-agent-done")
    c.setdefault("imap_host", "imap.gmail.com")
    c.setdefault("smtp_host", "smtp.gmail.com")
    c.setdefault("smtp_port", 465)
    c.setdefault("python", sys.executable or "/usr/bin/python3")
    c.setdefault("dr_query", "/root/deploy/dr_query.py")
    c.setdefault("max_reply_chars", 12000)
    c.setdefault("cmd_timeout_s", 25)
    c.setdefault("max_per_poll", 25)
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


def decoded_subject(msg):
    """The Subject as a person typed it, not as the wire carries it.

    Two different things happen to a long or non-plain subject, and the agent
    was reading the raw header, so it saw neither correctly:

    1. FOLDING. A subject longer than about 75 characters is split across
       continuation lines, and a space in the middle of the command becomes
       "\n ". `Q: sql SELECT ... FROM v_cash_ledger WHERE\n unit='medical'`
       still starts with the trigger, so it is not skipped -- but the SQL that
       reaches dr_query carries an embedded newline. Unfolding is exact: the
       newline is removed and the whitespace that was already there is kept,
       giving back the byte-identical string the sender typed.

    2. ENCODED WORDS. One non-ASCII character anywhere -- a rupee sign is
       enough -- and Gmail RFC2047-encodes that run in place, so the middle of
       the command arrives as `=?utf-8?q?=E2=82=B9=27?=`. That is then passed
       to the query as literal gibberish.

    Unfold first, then decode. Both must happen, in that order: an encoded word
    can itself be split across a fold.
    """
    raw = msg.get("Subject", "") or ""
    raw = re.sub(r"\r?\n([ \t])", r"\1", raw)        # unfold, exactly
    try:
        out = str(make_header(decode_header(raw)))
    except Exception:
        out = raw                                     # undecodable: use as-is
    return re.sub(r"\s+", " ", out).strip()          # one line, however it came


def _search_ids(M, cfg):
    """Return (ids, how). Prefer Gmail's raw search so we can exclude the
    done-label server-side and stay narrow. Fall back to a plain SUBJECT search
    (the per-message label check below then does the exclusion)."""
    trig = cfg["subject_trigger"]
    done = cfg["done_label"]
    gmq = 'subject:%s -label:%s' % (trig, done)
    try:
        typ, data = M.search(None, "X-GM-RAW", '"%s"' % gmq)
        if typ == "OK":
            return (data[0].split() if data and data[0] else []), "gmail-raw"
        log("X-GM-RAW search returned %s — falling back to SUBJECT" % typ)
    except Exception as e:
        log("X-GM-RAW search unavailable (%s) — falling back to SUBJECT" % e)
    typ, data = M.search(None, '(SUBJECT "%s")' % trig)
    ids = data[0].split() if typ == "OK" and data and data[0] else []
    return ids, "subject"


def _labels_raw(M, num):
    """The raw X-GM-LABELS text for a message (lowercased), or '' on any error."""
    try:
        typ, md = M.fetch(num, "(X-GM-LABELS)")
        if typ == "OK" and md and md[0]:
            item = md[0]
            if isinstance(item, tuple):
                item = item[0]
            if isinstance(item, bytes):
                item = item.decode("utf-8", "replace")
            return str(item).lower()
    except Exception:
        pass
    return ""


def _mark_done(M, num, done_label):
    """Apply the done label (authority) and mark seen (tidiness). Best-effort."""
    ok = False
    try:
        M.store(num, "+X-GM-LABELS", '"%s"' % done_label)
        ok = True
    except Exception as e:
        log("warning: could not apply done label: %s" % e)
    try:
        M.store(num, "+FLAGS", "\\Seen")
    except Exception:
        pass
    return ok


def _send_reply(cfg, to_addr, subj, in_reply_to, ok, text):
    reply = EmailMessage()
    reply["From"] = cfg["user"]
    reply["To"] = to_addr
    reply["Subject"] = ("Re: " + subj)[:200]
    if in_reply_to:
        reply["In-Reply-To"] = in_reply_to
        reply["References"] = in_reply_to
    body = ("%s\n\n%s\n\n— clinic query agent (read-only)"
            % (("Result:" if ok else "Could not run that:"), text))
    reply.set_content(body)
    with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"]) as S:
        S.login(cfg["user"], cfg["app_password"])
        S.send_message(reply)


def process_once(cfg):
    M = imaplib.IMAP4_SSL(cfg["imap_host"])
    try:
        M.login(cfg["user"], cfg["app_password"])
        M.select("INBOX")
        # Make sure the label exists so `-label:` is meaningful from the first run.
        try:
            M.create(cfg["done_label"])
        except Exception:
            pass
        ids, how = _search_ids(M, cfg)
        log("poll: %d candidate(s) via %s for subject %r (excluding label %r)"
            % (len(ids), how, cfg["subject_trigger"], cfg["done_label"]))
        handled = 0
        for num in ids[: cfg["max_per_poll"]]:
            # Already answered? (server-side exclusion + this belt-and-braces check
            # cover both search paths and guarantee no double reply.)
            if cfg["done_label"].lower() in _labels_raw(M, num):
                continue
            typ, md = M.fetch(num, "(RFC822)")
            if typ != "OK" or not md or not md[0]:
                continue
            msg = email.message_from_bytes(md[0][1])
            frm = parseaddr(msg.get("From", ""))[1].strip().lower()
            subj = decoded_subject(msg)
            trig = cfg["subject_trigger"]
            if frm not in cfg["trusted"]:
                continue                      # not trusted — leave untouched
            if not subj.lower().startswith(trig.lower()):
                log("ignored (no %r prefix) from %s: %r" % (trig, frm, subj[:80]))
                continue                      # not a command — leave untouched
            command = subj[len(trig):].strip()
            log("cmd from %s: %r" % (frm, command))
            # (b) ALWAYS produce a reply — even if the query itself raises.
            try:
                ok, text = run_query(cfg, command)
            except Exception as e:
                ok, text = False, "The query agent hit an error: %s" % e
            mid = msg.get("Message-ID")
            try:
                _send_reply(cfg, frm, subj, mid, ok, text)
            except Exception as e:
                # Do NOT mark done — next poll retries this same message.
                log("SEND FAILED for %s (%r): %s — will retry next poll"
                    % (frm, command, e))
                continue
            # Reply is out the door — now it is safe to mark this one answered.
            _mark_done(M, num, cfg["done_label"])
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
            if not cfg.get("done_label"):
                problems.append("config: 'done_label' is empty")
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
    # the long-subject fault: Gmail encodes anything long or non-ASCII, and the
    # trigger check reads the DECODED text or it reads nothing useful at all.
    import email as _em
    _long = ("Q: sql SELECT business_date, closing_p FROM v_cash_ledger "
             "WHERE unit='medical' ORDER BY business_date DESC LIMIT 5")
    _m = EmailMessage()
    _m["Subject"] = _long                     # EmailMessage encodes on set
    _wire = _em.message_from_bytes(_m.as_bytes())     # fold it as an MTA would
    if "\n" in (_wire.get("Subject") or ""):
        pass                                          # good: this IS the folded case
    else:
        problems.append("test setup: the long subject was not folded, so this "
                        "check proves nothing")
    if decoded_subject(_wire) != _long:
        problems.append("a folded long subject does not come back intact: %r"
                        % decoded_subject(_wire)[:70])
    if not decoded_subject(_wire).lower().startswith("q:"):
        problems.append("a long 'Q:' subject would still be skipped")
    _nonascii = "Q: sql SELECT 'drawer \u20b9' , closing_p FROM v_cash_ledger LIMIT 3"
    _n = EmailMessage(); _n["Subject"] = _nonascii
    if decoded_subject(_em.message_from_bytes(_n.as_bytes())) != _nonascii:
        problems.append("a subject with one non-ASCII character is mangled: %r"
                        % decoded_subject(_em.message_from_bytes(_n.as_bytes()))[:70])
    _b64 = _em.message_from_string(
        "Subject: =?UTF-8?B?UTogY2FzaCAzMA==?=\n\n")   # 'Q: cash 30'
    if decoded_subject(_b64) != "Q: cash 30":
        problems.append("base64 subject not decoded: %r" % decoded_subject(_b64))
    _plain = _em.message_from_string("Subject: Q: cash 30\n\n")
    if decoded_subject(_plain) != "Q: cash 30":
        problems.append("plain subject broken by the decoder")

    if problems:
        print("SELFTEST FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("SELFTEST OK — config present, done_label set, dr_query read-only, "
          "router allowlist enforced, folded and encoded subjects recovered.")
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

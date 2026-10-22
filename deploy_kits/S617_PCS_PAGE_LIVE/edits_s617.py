#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s617.py -- kit S617 (session S336, 22-Oct-2026): exact, counted edits turning the live
/root/finance/setup_notes.py (S527, d32423d1) into the S617 file.
    python3 edits_s617.py LIVE OUT [KIT]   (exit 0 only if every anchor occurs once and OUT = KIT)

THE OWNER, his board note of 22-Oct-2026 (his pick 07:12 IST): "clinic pc tile - keep the content and data updated there,
so that it stays current always".  The PC and phone cards of /finance/pcs are already read live (health rows, heartbeats,
the kits on the server).  The 'Other set-ups' cards were typed once (S492, S527) and could only age.  Now:
  * a 'Now' block on the server, CyberPanel and website cards, read from this box each time the page opens: the disk, how
    long the server has been running, the nightly jobs and backups as the freshness check last found them, and this
    morning's certificate check -- each read guarded and read-only; a read that fails says so in words;
  * every card says the day its notes were last checked; the page says that a change to a set-up updates its card;
  * the Websites card brought up to date: mail through the clinic Gmail (S590), forms to the clinic Gmail only (S592),
    the vendor's FTP login removed and FTP off (S589).
Display only: no door, no form, nothing written.  Never a password, key or token -- the file's one rule stands.
"""
import hashlib
import sys

HELPERS = r'''

# ---------------------------------------------------------------------------------------------------------------------
# S617 (the owner, 22-Oct-2026: "keep the content and data updated there, so that it stays current always"): the cards'
# 'Now' lines, read from this box each time the page opens. Every read is guarded and read-only; one that fails says so.
# ---------------------------------------------------------------------------------------------------------------------
FRESHNESS_STATE = os.environ.get("FRESHNESS_STATE_FILE", "/root/finance/freshness.state.json")
CERTWATCH_LOG = os.environ.get("CERTWATCH_LOG_FILE", "/root/wa/cert_watch.log")
ROOT_FS = os.environ.get("SETUP_NOTES_ROOT_FS", "/")
PROC_UPTIME = os.environ.get("SETUP_NOTES_PROC_UPTIME", "/proc/uptime")
NOTES_CHECKED = "22-Oct-2026"      # the day every card below was last read against the server and the records


def _jobs_line(now_ts=None):
    """The nightly jobs and backups as the freshness check (08:05, then hourly) last found them."""
    try:
        with open(FRESHNESS_STATE, encoding="utf-8") as fh:
            st = json.load(fh)
        ran = dt.datetime.fromisoformat(str(st["last_run_iso"]))
        n = int(st.get("legs_checked") or 0)
        bad = [str(x.get("name") or x.get("leg") or x) if isinstance(x, dict) else str(x) for x in (st.get("not_ok_legs") or [])]
        now = dt.datetime.utcfromtimestamp(time.time() if now_ts is None else now_ts) + dt.timedelta(hours=5, minutes=30)
        old = (now - ran).total_seconds() > 3 * 3600
        tail = (" <b>The nightly check has not reported for over three hours</b> &mdash; open the freshness page." if old else "")
        link = " (<a href='/finance/freshness'>freshness page</a>)"
        if not bad:
            return ("The nightly jobs and backups: <b>all %d on time</b> at the check of %s.%s%s"
                    % (n, ran.strftime("%d-%b %H:%M"), tail, link))
        return ("The nightly jobs and backups: <b>%d of %d late or missing</b> at the check of %s &mdash; %s.%s%s"
                % (len(bad), n, ran.strftime("%d-%b %H:%M"), html.escape(", ".join(bad[:6])), tail, link))
    except Exception:                                          # noqa: BLE001 -- a note never breaks the page
        return "The nightly jobs' check could not be read just now (<a href='/finance/freshness'>freshness page</a>)."


def _certs_line(now_ts=None):
    """This morning's certificate check (06:40), from the last CHECK line of its own log."""
    try:
        with open(CERTWATCH_LOG, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 16384))
            tail = fh.read().decode("utf-8", "replace")
        hits = [ln for ln in tail.splitlines() if "] CHECK " in ln and ln.startswith("[")]
        if not hits:
            return "The morning certificate check: no result in its log yet."
        ln = hits[-1]
        ran = dt.datetime.strptime(ln[1:20], "%Y-%m-%d %H:%M:%S")
        msg = ln.split("] CHECK ", 1)[1].strip()
        msg = re.sub(r"^all (\d+) watched sites healthy$", r"all \1 clinic addresses healthy", msg)   # the owner's words
        now = dt.datetime.utcfromtimestamp(time.time() if now_ts is None else now_ts) + dt.timedelta(hours=5, minutes=30)
        old = (now - ran).total_seconds() > 30 * 3600
        return ("Certificates (the padlock): <b>%s</b> at the check of %s.%s"
                % (html.escape(msg), ran.strftime("%d-%b %H:%M"),
                   " <b>That check is more than a day old</b> &mdash; it may not have run." if old else
                   ("" if msg.startswith("all ") else " The daily health mail has the detail.")))
    except Exception:                                          # noqa: BLE001
        return "The morning certificate check could not be read just now."


def _server_lines(now_ts=None):
    out = []
    try:
        u = shutil.disk_usage(ROOT_FS)
        gb = 1024.0 ** 3
        out.append("Disk: <b>%.0f GB free</b> of %.0f GB (%d%% used)." % (u.free / gb, u.total / gb, round(100.0 * u.used / u.total)))
    except Exception:                                          # noqa: BLE001
        out.append("Disk: could not be read just now.")
    try:
        with open(PROC_UPTIME, encoding="ascii") as fh:
            up = float(fh.read().split()[0])
        now_ts = time.time() if now_ts is None else now_ts
        out.append("Running since <b>%s</b> (%s)." % (_ist(now_ts - up).strftime("%d-%b-%Y %H:%M"),
                   "restarted today" if up < 86400 else "%d days" % int(up // 86400)))
    except Exception:                                          # noqa: BLE001
        out.append("How long it has been running could not be read just now.")
    out.append(_jobs_line(now_ts))
    return out


NOW_FNS = {"server": _server_lines, "certs": lambda now_ts=None: [_certs_line(now_ts)]}


def now_html(kind, now_ts=None):
    """The card's 'Now' block: lines read from this box as the page opens."""
    fn = NOW_FNS.get(kind)
    if fn is None:
        return ""
    try:
        lines = fn(now_ts)
    except Exception:                                          # noqa: BLE001
        lines = ["Could not be read just now."]
    return "<div class=now><b>Now</b> <small>(read as this page opened)</small><ul>%s</ul></div>" % "".join(
        "<li>%s</li>" % ln for ln in lines)


def staff_codes():'''

EDITS = [
    ("import html\nimport os\nimport time\n", "import html\nimport json\nimport os\nimport re\nimport shutil\nimport time\n"),
    ("\n\ndef staff_codes():", HELPERS),
    ('        "label": "Hostinger — the server",\n        "chip": "Renews 10-Jun-2028",\n',
     '        "label": "Hostinger — the server",\n        "chip": "Renews 10-Jun-2028",\n        "now": "server",   # S617\n'),
    ('        "label": "CyberPanel",\n        "chip": "Notes",\n',
     '        "label": "CyberPanel",\n        "chip": "Notes",\n        "now": "certs",    # S617\n'),
    ('        "label": "Websites",\n        "chip": "4 names",\n',
     '        "label": "Websites",\n        "chip": "4 names",\n        "now": "certs",    # S617\n'),
    ('                "Backed up weekly to Google Drive by WordPress\'s own backup plug-in (UpdraftPlus).",\n',
     '                "Backed up weekly to Google Drive by WordPress\'s own backup plug-in (UpdraftPlus).",\n'
     '                "<b>Its mail</b> — the contact forms and WordPress\'s own messages — goes out through the "\n'
     '                "<b>clinic Gmail</b> (since 18-Oct), and every form mails the clinic Gmail <b>only</b> (since 18-Oct).",\n'
     '                "The website vendor\'s FTP login is removed and FTP is off (since 18-Oct); no SSH or CyberPanel login "\n'
     '                "of theirs remained.",\n'),
    ('''    out = ["<div class=pc><div class=row><div class=pcn>%s</div><span class='st info'>%s</span></div><p class=what>%s</p>"
           % (html.escape(c["label"]), html.escape(c["chip"]), c["what"])]
''', '''    out = ["<div class=pc><div class=row><div class=pcn>%s</div><span class='st info'>%s</span></div><p class=what>%s</p>"
           % (html.escape(c["label"]), html.escape(c["chip"]), c["what"])]
    if c.get("now"):
        out.append(now_html(c["now"], now_ts))                 # S617: read from this box as the page opens
'''),
    ('''    out.append("</div>")
    return "".join(out)


def section(now_ts=None):''', '''    out.append("<p class=kit>Notes checked %s.</p>" % html.escape(c.get("checked") or NOTES_CHECKED))   # S617
    out.append("</div>")
    return "".join(out)


def section(now_ts=None):'''),
    ('''           "then forgotten. No password, PIN or key is ever written on this page.</p>",''',
     '''           "then forgotten. No password, PIN or key is ever written on this page. The lines marked <b>Now</b> are read from "
           "the server each time this page opens; each card says when its notes were last checked, and a change to a "
           "set-up updates its card the same day.</p>",'''),
    ('       ".nw{white-space:nowrap}', '       ".now{margin:8px 0 2px;padding:8px 10px;border-radius:8px;background:#0b1b29;border:1px solid var(--line);font-size:13px;color:#d5e2ee}"\n'
     '       ".now small{color:#9fb3c6}.now ul{margin:4px 0 0;padding-left:18px}.now li{margin:4px 0}.now b{color:#fff}"\n'
     '       ".nw{white-space:nowrap}'),
    ('def card_html(c):\n', 'def card_html(c, now_ts=None):\n'),
    ('    out.extend(card_html(c) for c in CARDS)', '    out.extend(card_html(c, now_ts) for c in CARDS)'),
]


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edits applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

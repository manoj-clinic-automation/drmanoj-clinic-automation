#!/usr/bin/python3
# make_s807.py -- kit S807_WA_BATCH_PAGE_GUARD (S440, 12-Nov-2026, the parent). Usage: make_s807.py <live portal_followups.py> <out dir>
# F-1301: the old follow-up batch page /portal/wa/followups is LIVE and unlabelled, standing on a list of 13-Aug. After this kit
#   - the page's data and its send door work on TODAY's list only: the file must be named Staff_Action_Today_YYYY-MM-DD.xlsx
#     and that date must be today (IST); any other list is refused in plain words, and no row of it is shown;
#   - the send door reads the list again at the moment of sending; the page must have been opened on that same list (the
#     server's strip tells the page the list's date and the page sends it back); a row goes only when its S.N, name and
#     number are a sendable row of today's list, and the number and the words then come from the LIST, not from the request;
#   - a sender failure stops the batch there and is never tried again;
#   - the page says LIVE or TEST at its top, with the list's date -- put there by the server, the page file is untouched.
# The parser, the template ladder, the one sender (portal_wa.send) and its log are as they were.
# Every edit is an anchor that must occur exactly once in the live file (98547bc4, S172).
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("98547bc4"), "not the live portal_followups.py (98547bc4)"
t = b.decode("utf-8")
def rp(a, n):
    global t
    assert t.count(a) == 1, "anchor not once (%d): %s" % (t.count(a), a[:70])
    t = t.replace(a, n)

# ---- the head: what S807 added
rp('(use the single-send widget / wa.me fallback for those).\n"""\n',
   '(use the single-send widget / wa.me fallback for those).\n\n'
   'S807 (F-1301, 12-Nov-2026): the page works on TODAY\'s list only. A list is today\'s when its file is named\n'
   'Staff_Action_Today_YYYY-MM-DD.xlsx and that date is today (IST). Any other list is refused by the data door AND by the\n'
   'send door. The send door reads the list again at the moment of sending, wants the page to have been opened on that same\n'
   'list, sends a row only when its S.N, name and number are a sendable row of today\'s list -- the number and the words are\n'
   'then taken from the list -- and stops at the first sender failure (never tried again). The page says LIVE or TEST at its\n'
   'top (the server puts the strip in; followups_page.html is untouched).\n"""\n')
rp('import os, re, glob\n', 'import os, re, glob\nimport datetime as _dt, html as _html, json as _json\n')

# ---- the rule and the strip, as plain functions (the walk calls them)
rp('\n\ndef od_template(od):\n', '''

# ------------------- S807 (F-1301): today's list only ----------------------- #
VERSION = "S807 1.1"
IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
_LIST_NAME = re.compile(r"Staff_Action_Today_(20\\d{2})-(\\d{2})-(\\d{2})\\.xlsx")
LIST_DATE_HEADER = "X-List-Date"
MESSAGES_URL = "/portal/messages"
SEND_TEMPLATES = ("drmanoj_post_visit", "drmanoj_followup_tomorrow", "drmanoj_followup_due",
                  "drmanoj_followup_missed", "drmanoj_followup_dropout")


def today_ist():
    return _dt.datetime.now(IST).date()


def list_date(path):
    """The day a list file is FOR: its name must be exactly Staff_Action_Today_YYYY-MM-DD.xlsx. None for any other
    name -- the folder's name and the file's write time are NOT used (a copy made today is not today's list)."""
    m = _LIST_NAME.fullmatch(os.path.basename(path or ""))
    if not m:
        return None
    try:
        return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _say_date(d):
    return "%d %s %d" % (d.day, d.strftime("%b"), d.year)


def list_state(path):
    """{file, file_date, today, fresh, why} for one list file (None = no file). fresh is True ONLY when the list's own
    date is today (IST); why says in plain words why nothing can be sent otherwise. The file is not opened."""
    today = today_ist()
    st = {"file": os.path.basename(path) if path else "", "file_date": "", "today": today.isoformat(),
          "fresh": False, "why": ""}
    if not path:
        st["why"] = "No follow-up list is on the server. Nothing can be sent from this page."
        return st
    fd = list_date(path)
    if fd is None:
        st["why"] = ("The follow-up list on the server is not named for a day (Staff_Action_Today_YYYY-MM-DD.xlsx), so "
                     "it cannot be shown to be today's. Nothing can be sent from this page.")
        return st
    st["file_date"] = fd.isoformat()
    if fd != today:
        st["why"] = ("The follow-up list on the server is dated %s -- it is not today's (%s). Nothing can be sent "
                     "from this page until today's list arrives." % (_say_date(fd), _say_date(today)))
        return st
    st["fresh"] = True
    return st


def sendable_rows(parsed):
    """{(S.N, name, number): row} for the sendable rows of a parsed list. A key that two DIFFERENT rows share maps to
    None -- such a row cannot be told apart and is refused."""
    out = {}
    for sec in parsed.get("sections", []):
        for r in sec.get("rows", []):
            if r.get("sendable") and r.get("phone"):
                k = (r.get("sn"), r.get("name"), r.get("phone"))
                out[k] = r if (k not in out or out[k] == r) else None
    return out


def match_row(item, rows):
    """The row of today's list that a posted item IS: the same S.N, name and number, each exactly as the list has it
    (the page posts them unchanged). None for anything else -- no guessing, no tidying of the number."""
    if not isinstance(item, dict):
        return None
    sn, nm, ph = item.get("sn"), item.get("name"), item.get("phone")
    if type(sn) is not int or not isinstance(nm, str) or not isinstance(ph, str):
        return None
    return rows.get((sn, nm, ph))


def banner_html(st, dry):
    """The strip at the top of the page: LIVE or TEST, and the list's date. Built by the server on every load. On
    today's list it also tells the page the list's date, which the page's send request then carries back."""
    live = not dry
    mode = "LIVE" if live else "TEST"
    fresh = bool(st.get("fresh"))
    if fresh:
        about = "Today's list (%s)." % _say_date(_dt.date.fromisoformat(st["file_date"]))
        says = ("A message sent from this page goes to the patient's WhatsApp." if live
                else "Messages from this page are only logged; nothing goes to any patient.")
        bg = "#7a1f1f" if live else "#6b5417"
    else:
        about = st.get("why") or "Nothing can be sent from this page."
        says = ""
        bg = "#3d4f4d"
    script = ""
    if fresh:
        script = ('<script>(function(){var d=%s,f=window.fetch;if(!f)return;window.fetch=function(u,o){'
                  'if(String(u).indexOf("/portal/wa/followups/send")>=0){o=o||{};var h={},s=o.headers||{};'
                  'for(var k in s){h[k]=s[k];}h["%s"]=d;o.headers=h;}return f.call(this,u,o);};})();</script>'
                  % (_json.dumps(st["file_date"]), LIST_DATE_HEADER))
    return ('<!--s807--><div id="s807-banner" data-v="%s" data-mode="%s" data-fresh="%s" style="background:%s;color:#fff;'
            'font:600 13.5px/1.45 -apple-system,\\'Segoe UI\\',Roboto,Arial,sans-serif;padding:10px 14px;'
            'border-bottom:1px solid rgba(255,255,255,.25)"><span style="display:inline-block;border:1.5px solid #fff;'
            'border-radius:6px;padding:0 7px;margin-right:8px;font-weight:800;letter-spacing:.04em">%s</span>%s '
            '<span style="font-weight:400">%s The daily messages are on <a href="%s" style="color:#fff">WhatsApp '
            'messages</a>.</span></div>%s<!--/s807-->'
            % (_html.escape(VERSION), mode, "1" if fresh else "0", bg, mode,
               _html.escape(about), _html.escape(says), MESSAGES_URL, script))


_BODY_TAG = re.compile(r"<body[^>]*>", re.I)


def with_banner(page, st, dry):
    """The page file's text with the strip put straight after its <body> tag (in front, if there is no such tag)."""
    b = banner_html(st, dry)
    m = _BODY_TAG.search(page)
    if not m:
        return b + page
    return page[:m.end()] + b + page[m.end():]


def od_template(od):
''')

# ---- the page: the strip goes in on every load
rp('        if os.path.exists(fp):\n'
   '            return Response(open(fp, encoding="utf-8").read(),\n'
   '                            mimetype="text/html; charset=utf-8")\n',
   '        if os.path.exists(fp):\n'
   '            with open(fp, encoding="utf-8") as fh:\n'
   '                page = fh.read()\n'
   '            try:                                   # S807: LIVE or TEST on its face, and the list\'s date\n'
   '                st = list_state(find_latest())\n'
   '            except Exception:\n'
   '                st = {"fresh": False, "why": "The follow-up list could not be read. Nothing can be sent from this page."}\n'
   '            resp = Response(with_banner(page, st, _dry()), mimetype="text/html; charset=utf-8")\n'
   '            resp.headers["Cache-Control"] = "no-store"\n'
   '            return resp\n')

# ---- the data door: today's list only; a refused list shows no row
rp('            path = find_latest()\n'
   '            if not path:\n'
   '                return jsonify({"ok": False,\n'
   '                                "error": "no Staff_Action_Today file found in " + FOLLOWUP_DIR})\n'
   '            d = parse(path)\n'
   '            d["ok"] = True; d["dry"] = _dry()\n'
   '            return jsonify(d)\n',
   '            path = find_latest()\n'
   '            st = list_state(path)                  # S807 (F-1301): today\'s list only\n'
   '            mode = "TEST" if _dry() else "LIVE"\n'
   '            if not st["fresh"]:\n'
   '                return jsonify({"ok": False, "error": st["why"], "stale": True,\n'
   '                                "dry": _dry(), "mode": mode, "list": st})\n'
   '            d = parse(path)\n'
   '            d["ok"] = True; d["dry"] = _dry()\n'
   '            d["mode"] = mode; d["list"] = st\n'
   '            return jsonify(d)\n')

# ---- the send door: the list is read again at the moment of sending; the row comes from the list
rp('        who = get_user() or "portal"\n'
   '        tok = _token(); dry = _dry()\n'
   '        results = []\n'
   '        sent = 0\n'
   '        for it in items[:500]:\n'
   '            r = wa_send(it.get("phone", ""), it.get("template", ""),\n'
   '                        it.get("values") or {}, who, tok, dry_run=dry)\n'
   '            if r.get("ok"):\n'
   '                sent += 1\n'
   '            results.append({"sn": it.get("sn"), "name": it.get("name", ""),\n'
   '                            "ok": r.get("ok"), "mode": r.get("mode"),\n'
   '                            "error": r.get("error", "")})\n',
   '        # S807 (F-1301): the list is read AGAIN now. Not today\'s -> nothing is sent. The page must have been opened on\n'
   '        # this same list (the strip gave it the list\'s date; its request carries it back) -- a page left open from an\n'
   '        # earlier day is told to reload. A row goes only when its S.N, name and number ARE a sendable row of today\'s\n'
   '        # list; the number and the words are then taken from the list, never from the request.\n'
   '        try:\n'
   '            path = find_latest()\n'
   '            st = list_state(path)\n'
   '            if not st["fresh"]:\n'
   '                return jsonify({"ok": False, "error": st["why"], "stale": True}), 409\n'
   '            if request.headers.get(LIST_DATE_HEADER, "") != st["file_date"]:\n'
   '                return jsonify({"ok": False, "stale": True,\n'
   '                                "error": "This page was opened on an earlier list. Reload the page, then tick and "\n'
   '                                         "send again -- nothing was sent."}), 409\n'
   '            rows = sendable_rows(parse(path))\n'
   '        except Exception as e:\n'
   '            return jsonify({"ok": False, "error": "Today\'s list could not be read -- nothing was sent (%s)."\n'
   '                            % str(e)[:120]}), 409\n'
   '        who = get_user() or "portal"\n'
   '        tok = _token(); dry = _dry()\n'
   '        results = []\n'
   '        sent = 0\n'
   '        stopped = ""\n'
   '        for it in items[:500]:\n'
   '            if not isinstance(it, dict):\n'
   '                continue\n'
   '            base = {"sn": it.get("sn"), "name": it.get("name", "")}\n'
   '            if stopped:                            # after a sender failure nothing more goes in this batch\n'
   '                results.append(dict(base, ok=False, mode="NOT SENT", error=stopped))\n'
   '                continue\n'
   '            row = match_row(it, rows)\n'
   '            tpl = it.get("template", "")\n'
   '            if row is None:\n'
   '                results.append(dict(base, ok=False, mode="REFUSED", error="not on today\'s list -- not sent"))\n'
   '                continue\n'
   '            if not isinstance(tpl, str) or tpl not in SEND_TEMPLATES:\n'
   '                results.append(dict(base, ok=False, mode="REFUSED", error="not a follow-up message -- not sent"))\n'
   '                continue\n'
   '            try:\n'
   '                r = wa_send(row["phone"], tpl, values_for(tpl, row), who, tok, dry_run=dry)\n'
   '                if not isinstance(r, dict):\n'
   '                    raise ValueError("the sender gave no answer")\n'
   '            except Exception as e:                 # never tried again; the rest of the batch is not sent\n'
   '                stopped = "the sender failed on an earlier row -- this one was not sent"\n'
   '                results.append(dict(base, ok=False, mode="FAILED",\n'
   '                                    error="the sender failed (%s) -- not tried again" % str(e)[:80]))\n'
   '                continue\n'
   '            if r.get("ok"):\n'
   '                sent += 1\n'
   '            results.append({"sn": it.get("sn"), "name": it.get("name", ""),\n'
   '                            "ok": r.get("ok"), "mode": r.get("mode"),\n'
   '                            "error": r.get("error", "")})\n')

os.makedirs(os.path.join(out, "portal"), exist_ok=True)
with open(os.path.join(out, "portal", "portal_followups.py"), "wb") as fh:
    fh.write(t.encode("utf-8"))
print("made", hashlib.md5(t.encode("utf-8")).hexdigest())

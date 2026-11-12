#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portal_followups.py — Follow-up batch WhatsApp (S172, Phase A.2)
================================================================
Reads the daily "Staff_Action_Today_YYYY-MM-DD.xlsx" that the follow-up tracker
produces (today: written on the clinic PC and pushed to the VPS; when the tracker
moves to the VPS it writes the SAME path and nothing here changes). The batch
screen never cares who wrote the file — it reads a FILE at a fixed dir. (D-stable)

It parses the "Call Sheet", turns each follow-up row into a ready-to-send item
(template auto-picked from OD = overdue days), and lets the doctor/agent
checkbox rows section-wise + patient-wise and fire them through the ONE canonical
sender (portal_wa.send) — same log, same DRY-RUN switch, same family-correct keys.

Template ladder by OD (overdue days), matching WABA_Approved_Templates (S137):
    OD  < 0   -> drmanoj_followup_tomorrow   (due tomorrow)
    0 <= OD<=3 -> drmanoj_followup_due        (due today / grace)
    4 <= OD<=10-> drmanoj_followup_missed     (missed)
    OD  > 10   -> drmanoj_followup_dropout    (dropout; var 3 = days overdue)

Only rows in a FOLLOW-UP section with a valid 10-digit mobile + name are marked
sendable. Procedure call-backs and other sections are shown but not WABA-sendable
(use the single-send widget / wa.me fallback for those).

S807 (F-1301, 12-Nov-2026): the page works on TODAY's list only. A list is today's when its file is named
Staff_Action_Today_YYYY-MM-DD.xlsx and that date is today (IST). Any other list is refused by the data door AND by the
send door. The send door reads the list again at the moment of sending, wants the page to have been opened on that same
list, sends a row only when its S.N, name and number are a sendable row of today's list -- the number and the words are
then taken from the list -- and stops at the first sender failure (never tried again). The page says LIVE or TEST at its
top (the server puts the strip in; followups_page.html is untouched).
"""

import os, re, glob
import datetime as _dt, html as _html, json as _json
import openpyxl

FOLLOWUP_DIR = os.environ.get("PORTAL_FOLLOWUP_DIR", "/root/wa/followups")
FILE_GLOB    = os.environ.get("PORTAL_FOLLOWUP_GLOB", "Staff_Action_Today*.xlsx")
SHEET_NAME   = "Call Sheet"

SECTION_RE = re.compile(r"^\s*\d+\.\s+(.+?)\s*(?:\u2014|\u2013|\s-\s|$)")


def find_latest(dirpath=None):
    d = dirpath or FOLLOWUP_DIR
    files = glob.glob(os.path.join(d, FILE_GLOB))
    return max(files, key=os.path.getmtime) if files else None


# ------------------- S807 (F-1301): today's list only ----------------------- #
VERSION = "S807 1.1"
IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
_LIST_NAME = re.compile(r"Staff_Action_Today_(20\d{2})-(\d{2})-(\d{2})\.xlsx")
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
            'font:600 13.5px/1.45 -apple-system,\'Segoe UI\',Roboto,Arial,sans-serif;padding:10px 14px;'
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
    """(template_name, ok) from overdue-days integer."""
    if od is None:
        return (None, False)
    if od < 0:
        return ("drmanoj_followup_tomorrow", True)
    if od <= 3:
        return ("drmanoj_followup_due", True)
    if od <= 10:
        return ("drmanoj_followup_missed", True)
    return ("drmanoj_followup_dropout", True)


def _fmt_date(raw, year):
    if not raw:
        return ""
    s = str(raw).strip()
    m = re.match(r"(\d{1,2})[-\s/]([A-Za-z]{3})", s)
    if m:
        return "%02d %s %s" % (int(m.group(1)), m.group(2).title(), year)
    return s


def parse(path):
    """Read the Call Sheet -> {file, year, sections:[{name, rows:[...]}]}.
    Read-only; never writes. Rows carry a full phone (doctor-session use) plus a
    masked phone for display."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if SHEET_NAME not in wb.sheetnames:
        raise ValueError("sheet '%s' not found in %s" % (SHEET_NAME, os.path.basename(path)))
    ws = wb[SHEET_NAME]
    rows = list(ws.iter_rows(values_only=True))

    year = "2026"
    for r in rows[:3]:
        for c in (r or []):
            m = re.search(r"(20\d{2})", str(c or ""))
            if m:
                year = m.group(1); break

    sections = []; cur = None; in_table = False
    for r in rows:
        a = str(r[0]).strip() if (r and r[0] is not None) else ""
        sm = SECTION_RE.match(a)
        if sm:
            cur = {"name": sm.group(1).strip(), "rows": []}
            sections.append(cur); in_table = False
            continue
        if a.upper() == "S.N":
            in_table = True; continue
        if in_table and cur is not None and a.isdigit():
            def g(i):
                return r[i] if (len(r) > i and r[i] is not None) else ""
            name = str(g(2)).strip()
            phone = re.sub(r"\D", "", str(g(3)))
            if len(phone) == 11 and phone[0] == "0":
                phone = phone[1:]
            date_raw = str(g(5)).strip()
            od = None
            if str(g(6)).strip() != "":
                try:
                    od = int(float(g(6)))
                except Exception:
                    od = None
            status = str(g(7)).strip()
            tpl, ok = od_template(od)
            sec_is_fu = "FOLLOW" in (cur["name"] or "").upper()
            sendable = bool(sec_is_fu and ok and len(phone) == 10 and name)
            cur["rows"].append({
                "sn": int(a), "name": name,
                "phone": phone if len(phone) == 10 else "",
                "phone_mask": ("\u2022\u2022\u2022\u2022" + phone[-4:]) if len(phone) >= 4 else "",
                "od": od, "date_raw": date_raw, "date_fmt": _fmt_date(date_raw, year),
                "status": status, "diagnosis": str(g(4)).strip(),
                "template": tpl if (ok and sec_is_fu) else "",
                "sendable": sendable})
    return {"file": os.path.basename(path), "year": year, "sections": sections}


def values_for(template_name, row):
    """Build the WABA body values dict for a follow-up row + chosen template."""
    name = row.get("name", ""); date = row.get("date_fmt", ""); od = row.get("od")
    if template_name == "drmanoj_post_visit":
        return {"1": name}
    if template_name == "drmanoj_followup_dropout":
        return {"1": name, "2": date, "3": str(od if od is not None else "")}
    if template_name in ("drmanoj_followup_tomorrow", "drmanoj_followup_due",
                         "drmanoj_followup_missed"):
        return {"1": name, "2": date}
    return {"1": name, "2": date}


# --------------------------- portal wiring ---------------------------------- #
def register(app, guard, get_user, cfg_get, wa_send):
    """wa_send = portal_wa.send  (the ONE canonical sender). cfg_get = portal config."""
    from flask import request, jsonify, Response

    def _token(): return cfg_get("MYOP_AUTH_TOKEN", "") or os.environ.get("MYOP_AUTH_TOKEN", "")
    def _dry():   return (cfg_get("PORTAL_WA_DRYRUN", "1") or "1") != "0"
    WA_DIR = os.environ.get("PORTAL_WA_DIR", "/root/wa/wa_portal")

    @app.route("/portal/wa/followups")
    @guard
    def fu_page():
        fp = os.path.join(WA_DIR, "followups_page.html")
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as fh:
                page = fh.read()
            try:                                   # S807: LIVE or TEST on its face, and the list's date
                st = list_state(find_latest())
            except Exception:
                st = {"fresh": False, "why": "The follow-up list could not be read. Nothing can be sent from this page."}
            resp = Response(with_banner(page, st, _dry()), mimetype="text/html; charset=utf-8")
            resp.headers["Cache-Control"] = "no-store"
            return resp
        return Response("followups_page.html not installed at " + fp, status=500,
                        mimetype="text/plain")

    @app.route("/portal/wa/followups/data")
    @guard
    def fu_data():
        try:
            path = find_latest()
            st = list_state(path)                  # S807 (F-1301): today's list only
            mode = "TEST" if _dry() else "LIVE"
            if not st["fresh"]:
                return jsonify({"ok": False, "error": st["why"], "stale": True,
                                "dry": _dry(), "mode": mode, "list": st})
            d = parse(path)
            d["ok"] = True; d["dry"] = _dry()
            d["mode"] = mode; d["list"] = st
            return jsonify(d)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/wa/followups/send", methods=["POST"])
    @guard
    def fu_send():
        b = request.get_json(force=True, silent=True) or {}
        items = b.get("items") or []
        if not items:
            return jsonify({"ok": False, "error": "no rows selected"}), 400
        # S807 (F-1301): the list is read AGAIN now. Not today's -> nothing is sent. The page must have been opened on
        # this same list (the strip gave it the list's date; its request carries it back) -- a page left open from an
        # earlier day is told to reload. A row goes only when its S.N, name and number ARE a sendable row of today's
        # list; the number and the words are then taken from the list, never from the request.
        try:
            path = find_latest()
            st = list_state(path)
            if not st["fresh"]:
                return jsonify({"ok": False, "error": st["why"], "stale": True}), 409
            if request.headers.get(LIST_DATE_HEADER, "") != st["file_date"]:
                return jsonify({"ok": False, "stale": True,
                                "error": "This page was opened on an earlier list. Reload the page, then tick and "
                                         "send again -- nothing was sent."}), 409
            rows = sendable_rows(parse(path))
        except Exception as e:
            return jsonify({"ok": False, "error": "Today's list could not be read -- nothing was sent (%s)."
                            % str(e)[:120]}), 409
        who = get_user() or "portal"
        tok = _token(); dry = _dry()
        results = []
        sent = 0
        stopped = ""
        for it in items[:500]:
            if not isinstance(it, dict):
                continue
            base = {"sn": it.get("sn"), "name": it.get("name", "")}
            if stopped:                            # after a sender failure nothing more goes in this batch
                results.append(dict(base, ok=False, mode="NOT SENT", error=stopped))
                continue
            row = match_row(it, rows)
            tpl = it.get("template", "")
            if row is None:
                results.append(dict(base, ok=False, mode="REFUSED", error="not on today's list -- not sent"))
                continue
            if not isinstance(tpl, str) or tpl not in SEND_TEMPLATES:
                results.append(dict(base, ok=False, mode="REFUSED", error="not a follow-up message -- not sent"))
                continue
            try:
                r = wa_send(row["phone"], tpl, values_for(tpl, row), who, tok, dry_run=dry)
                if not isinstance(r, dict):
                    raise ValueError("the sender gave no answer")
            except Exception as e:                 # never tried again; the rest of the batch is not sent
                stopped = "the sender failed on an earlier row -- this one was not sent"
                results.append(dict(base, ok=False, mode="FAILED",
                                    error="the sender failed (%s) -- not tried again" % str(e)[:80]))
                continue
            if r.get("ok"):
                sent += 1
            results.append({"sn": it.get("sn"), "name": it.get("name", ""),
                            "ok": r.get("ok"), "mode": r.get("mode"),
                            "error": r.get("error", "")})
        return jsonify({"ok": True, "sent": sent, "total": len(results),
                        "dry": dry, "results": results})

    return True

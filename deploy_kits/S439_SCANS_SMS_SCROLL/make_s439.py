#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s439.py -- builds the patched live files of kit S439_SCANS_SMS_SCROLL from the LIVE bytes by anchored edits. Every anchor must
occur exactly once and every source must be at its FROM pin, or the build stops with nothing written.

  purchase_app.py                   F-661: the scan matcher reads what OCR writes. The S439 block (purchase_block_s439.py, beside this
                                    file) is appended verbatim: bill tails, the vendor resolved by similarity, the six rules, the pass that
                                    keeps stored links and marks a second scan instead of linking it, the reason of every open scan, the
                                    cron / install entry "purchase_app.py rematch". Four anchored edits in page_scans show the reason
                                    beside every unmatched scan and the probable scan beside a bill with none.
  bank_sms.py                       F-660: the door reads the SMS from any of seven field names (JSON, form or query, any case), from the
                                    raw body, or from the bare query string (how the phone really posts); a refused post keeps the field
                                    names it carried; the storing is take(), apart from the HTTP request, so the web log can be replayed.
  finance_ui/finance_approvals.html PARENT'S, ONE anchored change: approve() calls daysStay() instead of load() -- the Days section keeps
                                    its place.

Usage: make_s439.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "purchase_app.py": "9c40d13ed222addeadf97d3f352f359a",
    "bank_sms.py": "a70d6d96e700380d08b8e379ea0720e5",
    "finance_ui/finance_approvals.html": "9d1eddc8f96856674e1dc3638490bbeb",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def sub(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for '%s' occurs %d times, not once" % (what, n))
    return text.replace(old, new)


def span(text, first, last, new, what):
    """Replace everything from the anchor `first` to the anchor `last` (both included, each exactly once, in that order)."""
    for a in (first, last):
        if text.count(a) != 1:
            sys.exit("REFUSED: span anchor for '%s' occurs %d times, not once" % (what, text.count(a)))
    i, j = text.index(first), text.index(last)
    if j < i:
        sys.exit("REFUSED: span anchors for '%s' are out of order" % what)
    return text[:i] + new + text[j + len(last):]


# ----------------------------------------------------------------------------- purchase_app.py
def patch_purchase_app(s):
    s = sub(s, '    un_b = [b for b in bills if b["id"] not in linked_bills]\n'
               '    btn = (\'<button class="p noprint" onclick="rematch()">Re-match now</button>\'\n',
            '    un_b = [b for b in bills if b["id"] not in linked_bills]\n'
            '    why = _scan_state_s439(con)                                # S439 (F-661): why each unmatched scan has no link\n'
            '    hint = {}                                                  # S439: bill id -> the open scan that is probably this bill\n'
            '    for _sid in sorted(why):\n'
            '        if why[_sid].get("hint_bill") and _sid not in linked:\n'
            '            hint.setdefault(why[_sid]["hint_bill"], _sid)\n'
            '    btn = (\'<button class="p noprint" onclick="rematch()">Re-match now</button>\'\n', "page_scans: read the reasons")
    s = sub(s, '                 \'<td>%s</td><td class="n">%s</td><td class="muted">%s / %s</td></tr>\'\n',
            '                 \'<td>%s</td><td class="n">%s</td><td class="muted">%s / %s</td><td>%s</td></tr>\'\n', "page_scans: the scan row")
    s = sub(s, '                    _esc(s["status"]), _esc(s["ocr_status"])) for s in un_s)\n',
            '                    _esc(s["status"]), _esc(s["ocr_status"]),\n'
            '                    _esc((why.get(s["id"]) or {}).get("detail") or "not checked yet \\u2014 the next match says why")) for s in un_s)\n',
            "page_scans: the reason cell")
    s = sub(s, '    t2 = "".join(\'<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td><a href="%s/page/month/%s">%s</a></td></tr>\'\n',
            '    t2 = "".join(\'<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td><a href="%s/page/month/%s">%s</a></td><td>%s</td></tr>\'\n',
            "page_scans: the bill row")
    s = sub(s, '                    prefix, b["month"], _esc(_month_name(b["month"] or ""))) for b in un_b)\n',
            '                    prefix, b["month"], _esc(_month_name(b["month"] or "")),\n'
            '                    (\'<a href="%s/bills/%d" target="_blank">scan #%d</a> <span class="muted">is probably this bill \\u2014 read differently, '
            'do not scan again</span>\'\n'
            '                     % (_assets_url, hint[b["id"]], hint[b["id"]])) if b["id"] in hint else "") for b in un_b)\n',
            "page_scans: the probable scan cell")
    s = sub(s, "            'bills. EXACT = vendor, bill number and amount all agree; PROBABLE = bill number and amount, '\n"
               "            'or vendor, date and amount.</div><div class=\"card\"><div class=\"row spread\"><div>'\n",
            "            'bills. EXACT = vendor, bill number (its last digits) and amount agree; PROBABLE = bill number and amount, or vendor '\n"
            "            'and bill number, or vendor, date (within 3 days) and amount. A second scan of a bill is marked, never linked twice; '\n"
            "            'every scan still open says why (S439).</div><div class=\"card\"><div class=\"row spread\"><div>'\n",
            "page_scans: the words")
    s = sub(s, "            '<th>Vendor</th><th>Bill no</th><th>Date</th><th class=\"n\">Amount</th><th>Status / OCR</th></tr>%s</table></div></div>'\n",
            "            '<th>Vendor</th><th>Bill no</th><th>Date</th><th class=\"n\">Amount</th><th>Status / OCR</th><th>Why it is not linked</th></tr>%s</table></div></div>'\n",
            "page_scans: the scans head")
    s = sub(s, "            '<th>Supplier</th><th>Bill no</th><th class=\"n\">Amount</th><th>Month</th></tr>%s</table></div></div>'\n",
            "            '<th>Supplier</th><th>Bill no</th><th class=\"n\">Amount</th><th>Month</th><th>A scan already here?</th></tr>%s</table></div></div>'\n",
            "page_scans: the bills head")
    s = sub(s, "               t1 or '<tr><td colspan=\"6\" class=\"muted\">none</td></tr>', len(un_b),\n"
               "               t2 or '<tr><td colspan=\"5\" class=\"muted\">none</td></tr>'))\n",
            "               t1 or '<tr><td colspan=\"7\" class=\"muted\">none</td></tr>', len(un_b),\n"
            "               t2 or '<tr><td colspan=\"6\" class=\"muted\">none</td></tr>'))\n", "page_scans: the empty rows")
    tail = '    return _page("Bank pack \\u2014 %s" % _month_name(month), body, js)\n'
    if not s.endswith(tail) or s.count(tail) != 1:
        sys.exit("REFUSED: purchase_app.py does not end where the S439 block is appended")
    block = io.open(os.path.join(HERE, "purchase_block_s439.py"), "r", encoding="utf-8", newline="").read()
    if "\r" in block or not block.startswith("\n\n# =====") or not block.endswith("_sys_s439.exit(_cli_s439(_sys_s439.argv))\n"):
        sys.exit("REFUSED: purchase_block_s439.py is not the kit's block")
    return s + block


# ----------------------------------------------------------------------------- bank_sms.py
BANK_DOC = (
    "The 200/ignored answer to the phone is unchanged. The key and the phone's address are never printed anywhere.\n"
    "\n"
    "S439 (30-Sep-2026, F-660) -- THE DOOR READS WHAT THE PHONE REALLY SENDS. Seven posts after S405 were refused as 'not a bank\n"
    "SMS' with an EMPTY text: the macro sends the SMS as the bare query string of the address ('?<the SMS>=<the SMS>': the text is\n"
    "its own field name), and the door read only a field called 'text'. Now read_post() takes the SMS from any of text / message / msg / body / sms / content /\n"
    "v1 and the sender from sender / from / number / address / v2 (JSON, form or query, any letter case), else from the raw body,\n"
    "else from the bare query string -- the first of these that reads as a bank SMS wins. A refused post keeps the FIELD NAMES it\n"
    "carried (bank_sms_ignored.fields, e.g. 'message,from,ts' or '(bare query, no field name)') beside its masked text, so the\n"
    "next refusal can be read. The key is never stored: it is cut out of anything kept. The reading and storing is take(), apart\n"
    "from the HTTP request, so the web server's own log of the earlier posts can be replayed through the same code (replay_s439).\n"
)

BANK_TAKE = r'''    text, sender, fields = read_post(request, key)     # S439 (F-660): whatever shape the macro gave the post
    con = _db()
    _ensure(con)
    out, code = take(con, text, sender, _now().strftime("%Y-%m-%d %H:%M:%S"), fields)
    return jsonify(**out), code


def _lower_keys(d):
    return {str(k).strip().lower(): v for k, v in d.items()}


def _reads(text):
    """True when the door can read this text as a bank SMS (ICICI settlement or Yes Bank debit / credit)."""
    if parse(text) is not None:
        return True
    return bool(YES_RE.search(text or "")) and parse_yes(text)[0] is not None


def read_post(req, key=""):
    """S439 (F-660): the SMS text, the sender and the field names of a post, however the macro shaped it.
    Named fields first (TEXT_KEYS / SENDER_KEYS; JSON, form or query; any letter case); then the raw body (a broken JSON,
    'message=...' sent as plain text, or the SMS itself); then the bare query string. The first candidate that reads as a
    bank SMS wins, else the first non-empty one is kept for the refused note. -> (text, sender, fields)."""
    try:
        raw = req.get_data(cache=True, as_text=True) or ""
    except Exception:                            # noqa: BLE001
        raw = ""
    pools, names, notes = [], [], []
    js = req.get_json(force=True, silent=True) if raw.strip()[:1] == "{" else None
    if isinstance(js, dict):
        pools.append(_lower_keys(js))
    try:
        if req.form:
            pools.append(_lower_keys(req.form))
    except Exception:                            # noqa: BLE001
        pass
    qs = req.query_string.decode("utf-8", "replace") if req.query_string else ""
    qpairs = [(k, v) for k, v in parse_qsl(qs, keep_blank_values=True) if k.strip().lower() != "key"]
    named_query = any(k.strip().lower() in TEXT_KEYS + SENDER_KEYS for k, _v in qpairs)
    if named_query:
        pools.append(_lower_keys(dict(qpairs)))
    body = raw.strip()
    plain = {}
    if body and not isinstance(js, dict) and "=" in body[:40]:
        plain = _lower_keys(dict(parse_qsl(body, keep_blank_values=True)))     # 'message=...&from=...' sent as plain text
        if any(k in plain for k in TEXT_KEYS + SENDER_KEYS):
            pools.append(plain)
        else:
            plain = {}

    def pick(keys):
        for p in pools:
            for k in keys:
                v = p.get(k)
                if isinstance(v, (list, tuple)):
                    v = v[0] if v else ""
                if v is not None and str(v).strip():
                    return str(v)
        return ""
    for p in pools:
        for k in p:
            if k != "key" and FIELD_RE.match(k) and k not in names:
                names.append(k)
    cands = [pick(TEXT_KEYS)]
    if body and not isinstance(js, dict) and not plain:
        m = BROKEN_JSON_RE.search(body)
        cands.append(m.group("v") if m else "")
        cands.append(body)
        notes.append("raw body, %s" % (req.mimetype or "no content type"))
    if qpairs and not named_query:
        if len(qpairs) == 1 and qpairs[0][1] in ("", qpairs[0][0]):
            cands.append(qpairs[0][0])           # '?<the SMS>' or '?<the SMS>=<the SMS>' -- the phone's own shape: one copy is kept
        else:
            cands.append("&".join(k if v == "" else "%s=%s" % (k, v) for k, v in qpairs))
        notes.append("bare query, no field name")
    cands = [(c.replace(key, "[key]") if key else c) for c in cands if c and c.strip()]      # the key is never stored
    text = next((c for c in cands if _reads(c)), cands[0] if cands else "")
    fields = ",".join(names)
    if notes:
        fields = (fields + " " if fields else "") + "(" + "; ".join(notes) + ")"
    return text[:600], pick(SENDER_KEYS)[:40], (fields or "(empty post)")[:160]


def take(con, text, sender, stamp, fields=""):
    """S439: the door's reading and storing, apart from the HTTP request -- the replay of the web server's log
    (replay_s439.py) runs this same code. -> (the answer as a dict, the HTTP code)."""
    text, sender = (text or "")[:600], (sender or "")[:40]
    p = parse(text)
    if p is None:
        # S405 (F-634): nothing is silent. A Yes Bank text is read into bank_sms_yes; anything else lands in the
        # ignored table, masked, with a reason. The phone still hears 200/ignored.
        if YES_RE.search(text):
            y, why = parse_yes(text)
            if y is not None:
                con.execute(
                    "INSERT INTO bank_sms_yes (kind, sms_date, amount_p, acct_tail, ref, balance_p, masked_text, phone_sender, received_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(kind, sms_date, amount_p, ref) DO UPDATE SET seen = seen + 1",
                    (y["kind"], y["sms_date"], y["amount_p"], y["acct_tail"], y["ref"], y["balance_p"], mask(text), sender, stamp))
                row = con.execute("SELECT id, seen FROM bank_sms_yes WHERE kind=? AND sms_date=? AND amount_p=? AND ref=?",
                                  (y["kind"], y["sms_date"], y["amount_p"], y["ref"])).fetchone()
                month = None
                if row and int(row[1]) == 1 and y["kind"] == "neft_debit":
                    month = _try_provisional(con, y, int(row[0]), stamp)
                con.commit()
                return dict(ok=True, stored=True, bank="YESBANK", kind=y["kind"], sms_date=y["sms_date"],
                            amount=y["amount_p"] // 100, matched_month=month), 200
            _ignore(con, stamp, sender, text, why, fields)
            con.commit()
            return dict(ok=True, stored=False, ignored=True), 200
        if not text.strip():
            why = "an empty post -- no SMS text in a field, the body or the address"
        else:
            why = icici_reason(text) if "icici" in text.lower() else "not a bank SMS this door reads"
        _ignore(con, stamp, sender, text, why, fields)
        con.commit()
        return dict(ok=True, stored=False, ignored=True), 200
    unit = unit_for_mid(con, p["mid_tail"])
    if unit is None:
        _ignore(con, stamp, sender, text, "unknown merchant (id ending %s)" % p["mid_tail"][-4:], fields)
        con.commit()
        return dict(ok=True, stored=False, ignored=True, why="unknown merchant"), 200
    con.execute(
        "INSERT INTO bank_sms_settlement (unit, credit_date, business_date, amount_p, balance_p, acct_tail, ref, "
        "sms_text, phone_sender, received_at, parse_grade) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(unit, credit_date, amount_p, ref) DO UPDATE SET seen = seen + 1",
        (unit, p["credit_date"], p["business_date"], p["amount_p"], p["balance_p"], p["acct_tail"], p["ref"],
         text.strip(), sender, stamp, p["parse_grade"]))
    con.commit()
    return dict(ok=True, stored=True, unit=unit, business_date=p["business_date"],
                amount=p["amount_p"] // 100, parse_grade=p["parse_grade"]), 200
'''


def patch_bank_sms(s):
    s = sub(s, "The 200/ignored answer to the phone is unchanged. The key and the phone's address are never printed anywhere.\n", BANK_DOC, "docstring")
    s = sub(s, "import time\n\nfrom flask import Blueprint, jsonify, request\n",
            "import time\nfrom urllib.parse import parse_qsl          # S439\n\nfrom flask import Blueprint, jsonify, request\n", "imports")
    s = sub(s, "RATE_PER_HOUR = 60\n",
            "RATE_PER_HOUR = 60\n"
            "# S439 (F-660): the field names the door reads, in this order, whatever their letter case\n"
            "S439_REV = \"S439-DOOR-1\"\n"
            "TEXT_KEYS = (\"text\", \"message\", \"msg\", \"body\", \"sms\", \"content\", \"v1\")\n"
            "SENDER_KEYS = (\"sender\", \"from\", \"number\", \"address\", \"v2\")\n"
            "FIELD_RE = re.compile(r\"^[a-z_][a-z0-9_.\\-\\[\\]]{0,30}$\")          # what may be kept as a field NAME (never a sentence)\n"
            "BROKEN_JSON_RE = re.compile(r'\"(?:text|message|msg|body|sms|content|v1)\"\\s*:\\s*\"(?P<v>.*?)\"\\s*(?:,\\s*\"|\\}\\s*$)', re.I | re.S)\n",
            "constants")
    s = sub(s, "        con.execute(\"ALTER TABLE bank_sms_settlement ADD COLUMN parse_grade TEXT NOT NULL DEFAULT 'strict'\")\n",
            "        con.execute(\"ALTER TABLE bank_sms_settlement ADD COLUMN parse_grade TEXT NOT NULL DEFAULT 'strict'\")\n"
            "    if \"fields\" not in {r[1] for r in con.execute(\"PRAGMA table_info(bank_sms_ignored)\")}:      # S439: the field names a refused post carried\n"
            "        con.execute(\"ALTER TABLE bank_sms_ignored ADD COLUMN fields TEXT NOT NULL DEFAULT ''\")\n", "_ensure: the fields column")
    s = sub(s, "def _ignore(con, stamp, sender, text, reason):\n"
               "    con.execute(\"INSERT INTO bank_sms_ignored (received_at, phone_sender, bank_guess, reason, masked_text) VALUES (?,?,?,?,?)\",\n"
               "                (stamp, sender, _guess_bank(text), reason, mask(text)))\n",
            "def _ignore(con, stamp, sender, text, reason, fields=\"\"):\n"
            "    con.execute(\"INSERT INTO bank_sms_ignored (received_at, phone_sender, bank_guess, reason, masked_text, fields) VALUES (?,?,?,?,?,?)\",\n"
            "                (stamp, sender, _guess_bank(text), reason, mask(text), fields or \"\"))       # S439: + the field names it carried\n", "_ignore")
    s = span(s, "    js = request.get_json(silent=True) or {}          # MacroDroid may send form, query or JSON\n",
             "                   amount=p[\"amount_p\"] // 100, parse_grade=p[\"parse_grade\"]), 200\n", BANK_TAKE, "post_sms: read_post + take")
    s = sub(s, "    ign = con.execute(\"SELECT received_at, bank_guess, reason, masked_text FROM bank_sms_ignored WHERE received_at>=? \"\n",
            "    ign = con.execute(\"SELECT received_at, bank_guess, reason, masked_text, fields FROM bank_sms_ignored WHERE received_at>=? \"   # S439: + fields\n",
            "page: the ignored select")
    s = sub(s, "               % (len(ign), (\"<table class='grid'><thead><tr><th>Received</th><th>Bank</th><th>Why</th><th>Text (masked)</th></tr></thead><tbody>%s</tbody></table>\"\n"
               "                             % \"\".join(\"<tr><td class='d'>%s</td><td>%s</td><td>%s</td><td class='mut'>%s</td></tr>\"\n"
               "                                       % (_esc(r[0]), _esc(r[1]), _esc(r[2]), _esc(r[3])) for r in ign))\n",
            "               % (len(ign), (\"<table class='grid'><thead><tr><th>Received</th><th>Bank</th><th>Why</th><th>Text (masked)</th><th>Fields it carried</th></tr></thead><tbody>%s</tbody></table>\"\n"
            "                             % \"\".join(\"<tr><td class='d'>%s</td><td>%s</td><td>%s</td><td class='mut'>%s</td><td class='mut'>%s</td></tr>\"\n"
            "                                       % (_esc(r[0]), _esc(r[1]), _esc(r[2]), _esc(r[3]), _esc(r[4])) for r in ign))\n", "page: the ignored table")
    s = sub(s, "<li>Body: content type <b>form</b> · field <code>text</code> = <code>[sms_message]</code> · field <code>sender</code> = <code>[sms_number]</code></li>\n",
            "<li>Body: content type <b>form</b> · field <code>text</code> = <code>[sms_message]</code> · field <code>sender</code> = <code>[sms_number]</code></li>\n"
            "<li>The macro does not have to change (S439): the door also reads the SMS from a field named <code>message</code>, <code>msg</code>, <code>body</code>, "
            "<code>sms</code>, <code>content</code> or <code>v1</code> (the sender from <code>from</code>, <code>number</code>, <code>address</code> or <code>v2</code>) "
            "as JSON, form or query, from the raw body, or from the bare address <code>…/bank-sms?{sms_message}={sms_message}</code> — the way the phone sends it today.</li>\n",
            "page: the phone-setup line")
    return s


# ----------------------------------------------------------------------------- finance_ui/finance_approvals.html (PARENT'S: one change)
HTML_OLD = ('      openDays[d]=false; load();\n'
            '    }).catch(function(e){alert("nothing was approved — the server could not be reached at all ("+e+")")});\n'
            '}\n')
HTML_NEW = ('      openDays[d]=false; daysStay();   /* S439: no longer the whole-page reload, which emptied every card and landed the browser at the top */\n'
            '    }).catch(function(e){alert("nothing was approved — the server could not be reached at all ("+e+")")});\n'
            '}\n'
            '/* ---- S439 (30-Sep-2026): an Approve keeps the Days section where it is. Two things threw it back to the top. (1) Each month\'s table\n'
            '   sits in its own scroll box (.tblwrap, 430px tall): every redraw of Days rebuilt the box and its scroll went back to ITS top -- the\n'
            '   day just approved, further down the month, was out of sight. (2) approve() called load(): every card was emptied and redrawn, the\n'
            '   page shrank and the browser landed higher up. Now only Days, the Needs-you strip and the Cash card are read again (and the old\n'
            '   queue, if it was opened), and daysKeep() puts back what the draw loses: the months that were open, each month box\'s own scroll, and\n'
            '   the page\'s offset -- the rules block\'s pattern (poKeepOpen). If the Needs-you strip above then loses a line, the Days card is held\n'
            '   where it was on the screen. ---- */\n'
            'function daysMonKey(el){ var s=el.querySelector("summary"); return (s&&s.firstChild)?String(s.firstChild.nodeValue||"").trim():"" }\n'
            'function daysHold(fn){ var e=document.documentElement, b=e.style.scrollBehavior; e.style.scrollBehavior="auto"; fn(); e.style.scrollBehavior=b }   /* this page scrolls smoothly by its stylesheet; a position put back must not glide */\n'
            'function daysKeep(fn){\n'
            '  var y=window.pageYOffset||document.documentElement.scrollTop||0, keep={}, i, k, w, ms=document.querySelectorAll("#days details.mon");\n'
            '  for(i=0;i<ms.length;i++){ w=ms[i].querySelector(".tblwrap"); keep[daysMonKey(ms[i])]={open:ms[i].open, top:w?w.scrollTop:0, left:w?w.scrollLeft:0} }\n'
            '  fn();\n'
            '  ms=document.querySelectorAll("#days details.mon");\n'
            '  for(i=0;i<ms.length;i++){ k=keep[daysMonKey(ms[i])]; if(!k) continue; if(k.open) ms[i].open=true; w=ms[i].querySelector(".tblwrap"); if(w){ w.scrollTop=k.top; w.scrollLeft=k.left } }\n'
            '  daysHold(function(){ window.scrollTo(0,y) });\n'
            '}\n'
            'function daysStay(){\n'
            '  loadNeeds(); loadCashPos(); if(A) loadOld();\n'
            '  fetch("/finance/sanjeevni/api/days?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){\n'
            '    var j=x.j||{}; if(!j.ok){ loadDays(); return }\n'
            '    daysKeep(function(){ DAYS=j; renderDays() });\n'
            '    var card=$("daysCard"), top=card?card.getBoundingClientRect().top:0, at=window.pageYOffset||0;\n'
            '    [350,1100].forEach(function(ms2){ setTimeout(function(){\n'
            '      if(!card||Math.abs((window.pageYOffset||0)-at)>2) return;             /* he has scrolled since: leave him there */\n'
            '      var d=card.getBoundingClientRect().top-top; if(Math.abs(d)>=2){ daysHold(function(){ window.scrollBy(0,d) }); at=window.pageYOffset||0 }\n'
            '    },ms2) });\n'
            '  }).catch(function(){ loadDays() });\n'
            '}\n')


def patch_approvals(s):
    return sub(s, HTML_OLD, HTML_NEW, "approve(): the Days section keeps its place")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, fn in (("purchase_app.py", patch_purchase_app), ("bank_sms.py", patch_bank_sms), ("finance_ui/finance_approvals.html", patch_approvals)):
        src = load(os.path.join(a.finance, name), name)
        raw = fn(src).encode("utf-8")
        open(os.path.join(a.out, os.path.basename(name)), "wb").write(raw)
        print("%s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()

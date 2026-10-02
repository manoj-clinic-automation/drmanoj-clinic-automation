#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s452.py -- kit S452_AMIR_PANEL_FIXES: builds the six live files from the LIVE bytes (CLAUDE.md rule 2).

Each live file is checked against its FROM pin (S446's TO / the 02-Oct bundle, read live) and every edit is anchored -- its anchor must
occur EXACTLY once, else the build stops and writes nothing. The blocks the kit appends, and the board's line edits
(board_edits_s452.txt: @@@ OLD / @@@ NEW / @@@ END), live beside this file. packs.py is the PARENT's: ONE anchored edit, Amir's NEFT route.

    make_s452.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "purchase_app.py": "176fc6eac35c7a3e7d052cba96ca873e",
    "amir_day.py": "cd8f4659cb828c09e9455d1b7543cfbd",
    "supplier_msg.py": "02b4a9edc4ff6bc42ed896e7f260be72",
    "stock_app.py": "ec6b1ce80d46b808d034b23cab032dc9",
    "stock_amir.html": "1ec8663dbbad397fe46f093966352e0a",
    "packs.py": "6a1cf6ceec4a58260df7352e48cdefe5",
}
E = {}


def edit(f, old, new):
    E.setdefault(f, []).append((old, new))


# ------------------------------------------------------------------ supplier_msg.py (F-687 · NEFT for Amir)
edit("supplier_msg.py", "import hmac\nimport re\nimport secrets\n", "import hmac\nimport os\nimport re\nimport secrets\n")
edit("supplier_msg.py",
     'def api_next():\n    con = _db()\n    if not _token_ok(con):\n        return jsonify(ok=False, error="bad_token"), 401\n    ensure(con)\n',
     'def api_next():\n    con = _db()\n    if not _token_ok(con):\n'
     '        _s452_phone_seen(con, 401)                       # S452: the setup page says when the phone last asked, and the answer\n'
     '        return jsonify(ok=False, error="bad_token"), 401\n    _s452_phone_seen(con, 200)\n    ensure(con)\n')
edit("supplier_msg.py",
     'def api_done():\n    con = _db()\n    if not _token_ok(con):\n        return jsonify(ok=False, error="bad_token"), 401\n    ensure(con)\n',
     'def api_done():\n    con = _db()\n    if not _token_ok(con):\n'
     '        _s452_phone_seen(con, 401)                       # S452\n'
     '        return jsonify(ok=False, error="bad_token"), 401\n    _s452_phone_seen(con, 200)\n    ensure(con)\n')
edit("supplier_msg.py",
     "        h.append('<div class=\"muted\">%d told · %d waiting · %d not sent · <a href=\"%s/page/phone-setup\">the reception phone\\'s setup</a></div>'\n"
     "                 % (st[\"counts\"][\"sent\"], st[\"counts\"][\"queued\"], st[\"counts\"][\"skipped\"], prefix))\n"
     "    if not owner:\n"
     "        h.append('<div class=\"muted\" style=\"margin-top:6px\"><a href=\"%s/page/phone-setup\">Reception phone ka setup (MacroDroid)</a></div>' % prefix)\n",
     "        h.append('<div class=\"muted\">%d told · %d waiting · %d not sent%s</div>'\n"
     "                 % (st[\"counts\"][\"sent\"], st[\"counts\"][\"queued\"], st[\"counts\"][\"skipped\"],\n"
     "                    (' · <a href=\"%s/page/phone-setup\">the reception phone\\'s setup</a>' % prefix) if owner else \"\"))   # S452 (F-687): the setup page is the owner's\n")
edit("supplier_msg.py",
     'def amir_card(con):\n'
     '    """\'NEFT <Month>: bheja <date> — bank se confirm baaki / ho gaya\' + the suppliers told (bata diya). Events of the last 45 days."""\n'
     '    ensure(con)\n',
     'def amir_card(con):\n'
     '    """S452 (the owner, 02-Oct): one line per month whose NEFT is confirmed, and the paid sheet as a PDF -- nothing before that, no\n'
     '    supplier names, no \'baaki\'. Shavez\'s and the owner\'s pages keep the list (pay_card)."""\n'
     '    return s452_amir_card(con)\n\n\n'
     'def _amir_card_s407(con):\n'
     '    """S407\'s card -- \'NEFT <Month>: bheja <date> — bank se confirm baaki / ho gaya\' + the suppliers told (bata diya). Kept for the\n'
     '    record; Amir no longer sees it (S452)."""\n'
     '    ensure(con)\n')
edit("supplier_msg.py",
     '    u, err = _person("checker", "maker", "viewer")\n    if err:\n        return err\n    con = _db()\n    ensure(con)\n    owner = _is_owner(u)\n'
     '    shown = _setting(con, "supplier_msg.token_shown", "")\n    tok = _setting(con, "supplier_msg.phone_token", "")\n'
     '    show = bool(tok) and (not shown or owner)\n    if show and not shown:\n'
     '        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (\'supplier_msg.token_shown\', ?, \'S407 -- the setup page showed the token once\')", (_iso(),))\n'
     '        con.commit()\n'
     '    key_html = (\'<p class="key">%s</p>\' % _esc(tok)) if show else (\n'
     '        \'<div class="warn">Token ek baar dikha diya gaya tha (%s). Dobara chahiye to doctor sahab apne login se yeh page kholein.</div>\' % _esc(shown[:16]))\n'
     '    body = """<h1>Reception phone — supplier message ka setup (MacroDroid)</h1>\n',
     '    u, err = _person("checker")                          # S452 (F-687): the owner and a checker -- a maker / viewer gets the gate\'s refusal\n'
     '    if err:\n        return err\n    con = _db()\n    ensure(con)\n'
     '    tok = _setting(con, "supplier_msg.phone_token", "")\n'
     '    key_html = (\'<p class="key">%s</p>\' % _esc(tok)) if tok else \'<div class="warn">Token abhi bana nahi.</div>\'\n'
     '    if tok:\n'
     '        _s452_token_shown(con, u)                         # S452: every showing audited (who, when); "shown once" retired\n'
     '    body = _s452_phone_state_line(con) + """<h1>Reception phone — supplier message ka setup (MacroDroid)</h1>\n')

# ------------------------------------------------------------------ packs.py (the PARENT's: ONE edit, Amir's NEFT route)
edit("packs.py",
     '    con = _db()\n    p = amir_pack(con, month)\n    if not p["ready"]:\n        return "pack abhi tayyar nahi (dono statement shelf par nahi)", 404\n'
     '    if what == "neft":\n        try:\n            b = build_neft_paid_sheet(con, month)\n'
     '        except Exception as ex:                          # noqa: BLE001\n'
     '            return "sheet nahi ban saki: %s" % _esc(str(ex)[:80]), 500\n'
     '        return send_file(io.BytesIO(b), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="NEFT_paid_%s.xlsx" % month)\n',
     '    con = _db()\n'
     '    if what == "neft":                                   # S452 (the owner, 02-Oct): a PDF, and only once the month\'s NEFT is confirmed\n'
     '        import supplier_msg                              # noqa: PLC0415 -- Sanjeevni\'s rule decides (the bank SMS read, or the owner\'s entry)\n'
     '        return supplier_msg.s452_amir_neft_pdf(con, month)\n'
     '    p = amir_pack(con, month)\n    if not p["ready"]:\n        return "pack abhi tayyar nahi (dono statement shelf par nahi)", 404\n')

# ------------------------------------------------------------------ purchase_app.py (F-686)
edit("purchase_app.py",
     '        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")\n    got = _s446_file_bytes(sid)\n    if got is None:\n'
     '        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404\n'
     '    from flask import Response                                 # noqa: PLC0415\n'
     '    return Response(got[1], mimetype="application/pdf",\n'
     '                    headers={"Content-Disposition": \'attachment; filename="%s"\' % got[0], "Cache-Control": "no-store"})\n',
     '        return _refuse("Yeh file sirf Amir aur doctor sahab ke liye hai.")\n'
     '    kind, item = _s452_lookup(con, sid)                        # S452 (F-686): only a bill Marg does not have, and not one held for reception\n'
     '    if kind in ("linked", "held"):\n        return _s452_small_page(kind)\n'
     '    got = _s446_file_bytes(sid) if kind == "list" else None\n    if got is None:\n'
     '        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404\n'
     '    from flask import Response                                 # noqa: PLC0415\n'
     '    return Response(got[1], mimetype="application/pdf",\n'
     '                    headers={"Content-Disposition": \'attachment; filename="%s"\' % item["name"], "Cache-Control": "no-store"})\n')
edit("purchase_app.py",
     '        for s in scans_to_enter(con):\n            if not s["today"]:\n                continue\n            got = _s446_file_bytes(s["id"])\n'
     '            if got is None:\n                continue\n            n = got[0]\n',
     '        for s in scans_for_amir(con)["list"]:                  # S452 (F-686): the same rule as the list\n            if not s["today"]:\n                continue\n'
     '            got = _s446_file_bytes(s["id"])\n            if got is None:\n                continue\n            n = s["name"]\n')
edit("purchase_app.py",
     "    return bar + _s446_sarvam_card(con) + body + up      # S446 (D650): Sarvam against Marg, one line\n",
     "    return bar + _s446_sarvam_card(con) + _s452_amir_list_line(con) + body + up      # S446 (D650): Sarvam, one line · S452: Amir's list\n")
edit("purchase_app.py",
     '    blob, total, missing = _advice_xlsx_s267(con, month)\n    _audit(con, _who(u), "pay_advice_xlsx", month, {"total": total, "left_out": missing})\n',
     '    if not _s452_may_advice(con, u):                           # S452: the bank file carries full account numbers -- the owner and the senders\n'
     '        return _refuse("Yeh file sirf doctor sahab aur Shavez ke liye hai.")\n'
     '    blob, total, missing = _advice_xlsx_s267(con, month)\n    _audit(con, _who(u), "pay_advice_xlsx", month, {"total": total, "left_out": missing})\n')

# ------------------------------------------------------------------ amir_day.py
edit("amir_day.py",
     "    bills = []\n    try:\n        import purchase_app                                    # noqa: PLC0415\n"
     "        bills = purchase_app.scans_to_enter(cx)\n    except Exception:                                          # noqa: BLE001\n"
     "        bills = []\n    return dict(stage=st, packs=_s446_packs(cx), watch=_s446_watch(cx), bills=bills)\n",
     "    return dict(stage=st, packs=_s446_packs(cx), watch=_s446_watch(cx),\n"
     "                **_s452_state(cx))                             # S452: bills (only those Marg does not have) + held, rates, NEFT confirmed\n")
edit("amir_day.py",
     "    body = _s446_bills_list(w) + body                    # S446 (D650): the scanned bills to put into Marg, first\n",
     "    body = _s452_bills_list(w) + body                    # S446 (D650) · S452 (F-686): only the bills Marg does not have, first\n")
edit("amir_day.py",
     '    if not _ready_to_close(w):\n        body = "<div class=card><h2>Abhi kuch baaki hai</h2><ul>"\n        for item in _left(w):\n'
     '            body += "<li>%s</li>" % _esc(item)\n        body += ("</ul><p class=sub>Aaj ka din khula rehta hai. Jo ho gaya hai wo "\n',
     '    if not _ready_to_close(w):\n'
     '        gate, extra = _s452_left_hi(w)                       # S452: Roman Hindi; what never holds the day stands apart\n'
     '        body = "<div class=card><h2>Abhi kuch baaki hai</h2><ul>"\n        for item in gate or ["Kuch step abhi baaki hain"]:\n'
     '            body += "<li>%s</li>" % _esc(item)\n'
     '        body += "</ul>" + "".join("<p>%s <span class=sub>(din band karne se nahi rukta)</span></p>" % _esc(x) for x in extra)\n'
     '        body += ("<p class=sub>Aaj ka din khula rehta hai. Jo ho gaya hai wo "\n')
edit("amir_day.py",
     '            if C.get("today"):\n'
     '                lines.append("<div class=line><a class=btn href=\'%s\'>Dawa voucher: aaj ke %d (baaki %d) &mdash; kholiye</a></div>"\n'
     '                             % (_esc(_s446_board(st, "vouchers")), len(C["today"]), int(C.get("unreleased") or 0)))\n',
     '            if C.get("open"):                                  # S452: what is open on his board now (12 a visit, more on request)\n'
     '                lines.append("<div class=line><a class=btn href=\'%s\'>Dawa voucher: aaj ke %d (baaki %d) &mdash; kholiye</a></div>"\n'
     '                             % (_esc(_s446_board(st, "vouchers")), int(C["open"]), int(C.get("unreleased") or 0)))\n')
edit("amir_day.py",
     '    for m in s.get("packs") or []:\n'
     '        lines.append("<div class=line><span class=big>Mahine ka pack &mdash; %s</span>"\n'
     '                     "<p><a class=\'btn plain\' href=\'/finance/amir/pack/%s/neft\'>Paid NEFT sheet (Excel)</a></p>"\n'
     '                     "<p><a class=\'btn plain\' href=\'/finance/amir/pack/%s/yes\'>Yes Bank Sanjeevni statement (PDF)</a></p>"\n'
     '                     "<p><a class=\'btn plain\' href=\'/finance/amir/pack/%s/icici\'>ICICI Sanjeevni statement (PDF)</a></p>"\n'
     '                     "<form method=post action=\'/finance/amir/pack/%s/seen\'><button class=btn name=go value=1>Dekh liya</button></form></div>"\n'
     '                     % (_esc(_s446_month_name(m)), m, m, m, m))\n',
     '    if s.get("rates"):                                         # S452: (b) Rate daalo on his card while due\n'
     '        lines.append("<div class=line><a class=\'btn plain\' href=\'%s\'>%d item ka rate Marg mein daalna hai &mdash; kholiye</a></div>"\n'
     '                     % (_esc(_s446_board(st, "rates")), len(s["rates"])))\n'
     '    for m in s.get("packs") or []:\n'
     '        lines.append("<div class=line><span class=big>Mahine ka pack &mdash; %s</span>%s"      # S452: the paid NEFT sheet only once confirmed, a PDF\n'
     '                     "<p><a class=\'btn plain\' href=\'/finance/amir/pack/%s/yes\'>Yes Bank Sanjeevni statement (PDF)</a></p>"\n'
     '                     "<p><a class=\'btn plain\' href=\'/finance/amir/pack/%s/icici\'>ICICI Sanjeevni statement (PDF)</a></p>"\n'
     '                     "<form method=post action=\'/finance/amir/pack/%s/seen\'><button class=btn name=go value=1>Dekh liya</button></form></div>"\n'
     '                     % (_esc(_s446_month_name(m)),\n'
     '                        ("<p><a class=\'btn plain\' href=\'/finance/amir/pack/%s/neft\'>Paid NEFT sheet (PDF)</a></p>" % m) if (s.get("neft_ok") or {}).get(m) else "",\n'
     '                        m, m, m))\n')
edit("amir_day.py",
     '    if not lines:\n        return ""\n'
     '    return ("<div class=card id=s444duty style=\'border:2px solid var(--bad)\'><h2 class=bad>%s</h2>%s</div>"\n'
     '            % ("Marg sudhar &mdash; abhi baaki" if top else "Marg sudhar", "".join(lines)))\n\n\ndef _s446_left(w):\n',
     '    if not lines:\n        return ""\n'
     '    return ("<div class=card id=s444duty style=\'border:2px solid var(--bad)\'>%s%s</div>"      # S452: on step 6 the page\'s own heading is enough\n'
     '            % ("<h2 class=bad>Marg sudhar &mdash; abhi baaki</h2>" if top else "", "".join(lines)))\n\n\ndef _s446_left(w):\n')
edit("amir_day.py",
     '            t = "Stage C (medicine vouchers) %d/%d entered, %d released and open" % (C.get("entered", 0), C.get("total", 0), C.get("open", 0))\n',
     '            t = "Stage C (medicine vouchers) %d/%d entered · %d released · %d verified" % (C.get("entered", 0), C.get("total", 0),\n'
     '                                                                                       C.get("released", 0), C.get("verified", 0))   # S452\n')

# ------------------------------------------------------------------ stock_app.py
edit("stock_app.py",
     'hi=("Marg में हो गया" if marg_done else ("टिक किया, Marg की लिस्ट में अभी नहीं" if r[4] else "करना है"))',
     'hi=("Marg mein ho gaya" if marg_done else ("Tick kiya, Marg ki list mein abhi nahi" if r[4] else "Karna hai"))')
edit("stock_app.py",
     'hi="Marg में selling rate डालें"))\n        elif STOCK_STATEMENT_OK:\n',
     'hi="Marg mein selling rate daaliye"))\n        elif STOCK_STATEMENT_OK:\n')
edit("stock_app.py",
     'hi="Marg में selling rate डालें"))\n        out["rate_tasks"].sort(key=lambda r: r["item"])\n',
     'hi="Marg mein selling rate daaliye"))\n'
     '        out["rate_tasks"] = _s452_rates_open(con, out["rate_tasks"])     # S452: a rate Marg now carries leaves the list (sorted)\n')
edit("stock_app.py", '"नाम बदलना — बाद में, जब Marg और shelf मिल जाएँ"', '"Naam badalna — baad mein, jab Marg aur shelf mil jaayein"')
edit("stock_app.py", '"अभी बाकी — पहले वाउचर Marg में डालें"', '"Abhi baaki — pehle voucher Marg mein daaliye"')
edit("stock_app.py", '"अभी बाकी — वाउचर डल गए, Marg का अगला closing stock export आने दें"',
     '"Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye"')
edit("stock_app.py", 'out["proof_hi"] = "अभी बाकी"\n', 'out["proof_hi"] = "Abhi baaki"\n')
edit("stock_app.py", 'title_hi="%s — वाउचर %d" % (VOUCHER_HI[kind], seq),', 'title_hi="%s — voucher %d" % (VOUCHER_HI[kind], seq),')
edit("stock_app.py", 'v["title_hi"] = "%s — वाउचर %d" % (VOUCHER_HI.get(v["kind"], v["kind"]), v["seq"])',
     'v["title_hi"] = "%s — voucher %d" % (VOUCHER_HI.get(v["kind"], v["kind"]), v["seq"])')
edit("stock_app.py", 'b["renames_wait_hi"] = "नाम बदलना — orthotic voucher Marg में सही होने के बाद"',
     'b["renames_wait_hi"] = "Naam badalna — orthotic voucher Marg mein sahi hone ke baad"')
edit("stock_app.py",
     '    b["stage"] = dict(stage=st["stage"], count_id=st["count_id"])\n',
     '    b["stage"] = dict(stage=st["stage"], count_id=st["count_id"], more=int((st.get("C") or {}).get("unreleased") or 0),\n'
     '                      per=int((st.get("C") or {}).get("per") or 0))   # S452: "Aur voucher kholiye" while some are left\n')
edit("stock_app.py",
     '    per = max(1, _s446_setting(con, "amir.vouchers_per_visit", 5))\n',
     '    per = max(1, _s446_setting(con, "amir.vouchers_per_visit", 12))   # S452: 12 a visit (the owner, 02-Oct)\n')
edit("stock_app.py",
     '    for l in lots:\n'
     '        l["proof"] = _s446_proof(con, root, l["keys"], ent, batches) if all(k in ent for k in l["keys"]) else dict(state="wait", rows=[])\n'
     '        l["verified"] = l["proof"]["state"] == "done"\n',
     '    for l in lots:\n'
     '        ek = [k for k in l["keys"] if k in ent]               # S452: every export checks whatever he has entered so far\n'
     '        l["proof"] = _s446_proof(con, root, ek, ent, batches) if ek else dict(state="wait", rows=[])\n'
     '        l["verified"] = len(ek) == len(l["keys"]) and l["proof"]["state"] == "done"\n')
edit("stock_app.py",
     '    if cur and (cur["verified"] or len(_s446_visits_since(con, cur["at"])) >= 2):\n',
     '    if cur and (cur["verified"] or len(_s446_visits_since(con, cur["at"])) >= 1):   # S452: the next visit opens the next lot, proved or not\n')
edit("stock_app.py",
     '             lot_at=(lots[-1]["at"] if lots else None), lots=len(lots))\n',
     '             lot_at=(lots[-1]["at"] if lots else None), lots=len(lots),\n'
     '             released=len([k for k in med if k in released]), verified=sum(len(l["keys"]) for l in lots if l["verified"]))   # S452\n')
edit("stock_app.py",
     '    b = _s446_board_filter(con, b, u)                     # S446 (D649): a login that is not the checker sees its stage only\n'
     '    return jsonify(ok=True, **b)\n',
     '    b = _s446_board_filter(con, b, u)                     # S446 (D649): a login that is not the checker sees its stage only\n'
     '    b = _s452_board_roman(b)                              # S452: Roman Hindi; block (a) without the lines Marg already shows\n'
     '    return jsonify(ok=True, **b)\n')

APPEND = {"amir_day.py": "amir_block_s452.py", "stock_app.py": "stock_block_s452.py", "supplier_msg.py": "supplier_block_s452.py"}
INSERT_BEFORE = {"purchase_app.py": ('\n\nif __name__ == "__main__":\n    import sys as _sys_s439\n', "purchase_block_s452.py")}
LINE_EDITS = {"stock_amir.html": "board_edits_s452.txt"}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def line_edits(name):
    """The board's edits: whole live lines, each anchor exactly once."""
    txt = io.open(os.path.join(HERE, name), encoding="utf-8", newline="").read()
    out = []
    for blk in re.findall(r"@@@ OLD\n(.*?)\n@@@ NEW\n(.*?)\n@@@ END\n", txt, re.S):
        out.append((blk[0] + "\n", blk[1] + "\n"))
    if not out:
        raise SystemExit("STOP: %s holds no edits" % name)
    return out


def build(finance, out, check_pins=True):
    os.makedirs(out, exist_ok=True)
    for f in FROM:
        raw = open(os.path.join(finance, f), "rb").read()
        if check_pins and md5b(raw) != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- someone changed it since the brief; nothing written" % (f, md5b(raw), FROM[f]))
        txt = raw.decode("utf-8")
        edits = list(E.get(f, [])) + (line_edits(LINE_EDITS[f]) if f in LINE_EDITS else [])
        for old, new in edits:
            n = txt.count(old)
            if n != 1:
                raise SystemExit("STOP: %s -- an anchor occurs %d times (must be exactly once): %r" % (f, n, old[:90]))
            txt = txt.replace(old, new, 1)
        if f in APPEND:
            txt = txt.rstrip("\n") + "\n\n\n" + open(os.path.join(HERE, APPEND[f]), "rb").read().decode("utf-8").strip("\n") + "\n"
        if f in INSERT_BEFORE:
            anchor, blk = INSERT_BEFORE[f]
            if txt.count(anchor) != 1:
                raise SystemExit("STOP: %s -- the insertion anchor occurs %d times" % (f, txt.count(anchor)))
            txt = txt.replace(anchor, "\n\n\n" + open(os.path.join(HERE, blk), "rb").read().decode("utf-8").strip("\n") + "\n" + anchor, 1)
        if f.endswith(".html") and re.search("[ऀ-ॿ]", txt):
            raise SystemExit("STOP: %s -- Devanagari is left on the page after the edits" % f)
        b = txt.encode("utf-8")
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("built %-17s %s -> %s  (%d edits%s)" % (f, FROM[f][:8], md5b(b), len(edits), ", block added" if (f in APPEND or f in INSERT_BEFORE) else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-pins", action="store_true")
    a = ap.parse_args()
    build(a.finance, a.out, check_pins=not a.no_pins)

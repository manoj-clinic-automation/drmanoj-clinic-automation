#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s444.py -- kit S444_STAFF_SAFE: builds the nine live files from the LIVE bytes (CLAUDE.md rule 2).

Every edit is anchored: its anchor must occur EXACTLY once in the live file, else the build stops and writes nothing.
Each live file is first checked against its FROM pin (rule 1). The blocks the kit appends live beside this file
(amir_block_s444.py, stock_block_s444.py). tile_grants.json is edited as text (its bytes and its formatting kept) and
then read back as JSON to prove the result.

    make_s444.py --portal /root/portal --finance /root/finance --out DIR
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

FROM = {
    "clinic_sso.py": "2bc6ba15e52512d3f866536e758079ed",
    "portal.py": "626838cdf624446f90ac3061a79b6523",
    "tile_grants.json": "acc9cc1bad61b3f9a77f6f4f56b15476",
    "amir_day.py": "068a3988e296f6579e2e780b2e4f623b",
    "amir_salts.py": "8d6ef482573e56ae8676712a82a2a563",
    "reports_tile.py": "2798436712be69eb3c4486a0913e38f4",
    "sanjeevni_approvals.py": "3999c4ced7aaf098eeeb00d696014cab",
    "stock_app.py": "4f2625c0a88e450c88e0b23d499d6fa8",
    "porders.py": "af4a6f57b6c7522784fdb53d6233d50b",
}
WHERE = {"clinic_sso.py": "portal", "portal.py": "portal", "tile_grants.json": "portal"}

E = {}      # file -> [(old, new)]


def edit(f, old, new):
    E.setdefault(f, []).append((old, new))


# ------------------------------------------------------------------ clinic_sso.py (PARENT'S, declared): one sign-in name
edit("clinic_sso.py",
     "# Pure standard library. No Flask, no third-party deps -> the VPS venv needs nothing new.\n",
     "# Pure standard library. No Flask, no third-party deps -> the VPS venv needs nothing new.\n"
     "# S444 (01-Oct-2026, F-669 / D647): the name a token carries and returns is the store's own -- small letters, no spaces\n"
     "#   around it (norm_user). 'Amir', 'AMIR', ' amir ' sign in as 'amir'; a token issued earlier as 'Amir' reads as 'amir'.\n")
edit("clinic_sso.py",
     "def get_secret(env=SECRET_ENV):\n",
     "def norm_user(user):\n"
     "    \"\"\"S444 (F-669): ONE sign-in name whatever was typed. clinic_users already looks a user up by strip().lower(); the token\n"
     "    now carries -- and returns -- that same name, so every app keys grants, masks and roles by the name the store holds.\n"
     "    A value that is not text passes through unchanged.\"\"\"\n"
     "    return user.strip().lower() if isinstance(user, str) else user\n"
     "\n"
     "\n"
     "def get_secret(env=SECRET_ENV):\n")
edit("clinic_sso.py",
     '    payload = {"u": user, "r": role, "e": int(epoch), "iat": int(now), "exp": int(now) + int(ttl)}\n',
     '    payload = {"u": norm_user(user), "r": role, "e": int(epoch), "iat": int(now), "exp": int(now) + int(ttl)}   # S444: the store\'s name\n')
edit("clinic_sso.py",
     '    return {"user": payload.get("u"), "role": payload.get("r"),\n',
     '    return {"user": norm_user(payload.get("u")), "role": payload.get("r"),          # S444: an old "Amir" token reads as amir\n')
edit("clinic_sso.py",
     '    ok(d["user"] == "manoj", "user preserved")\n',
     '    ok(d["user"] == "manoj", "user preserved")\n'
     '    # S444: one sign-in name\n'
     '    ok(verify_token(make_token(" Amir ", "staff", 3, S, ttl=100, now=now), S, now=now)["user"] == "amir", "S444: a typed \' Amir \' is signed as amir")\n'
     '    _old = _b64u_encode(json.dumps({"u": "AMIR", "r": "staff", "e": 3, "iat": now, "exp": now + 100}, separators=(",", ":"), sort_keys=True).encode("utf-8"))\n'
     '    ok(verify_token(_old + "." + _sign(_old, S), S, now=now)["user"] == "amir", "S444: a token minted before S444 as \'AMIR\' reads as amir")\n')

# ------------------------------------------------------------------ portal.py (PARENT'S, declared): the login, the home
edit("portal.py",
     "                token = clinic_sso.make_token(user, role,\n",
     "                token = clinic_sso.make_token(user.strip().lower(), role,     # S444 (F-669): the store's own name, whatever was typed\n")
edit("portal.py",
     '    role = who["role"] if who else "doctor"\n'
     "    pc = _is_clinic_pc(request)\n"
     "    return render_template_string(PORTAL_HTML,\n"
     '                                  sections=_visible_sections(role, pc, who["user"] if who else ""),\n'
     "                                  sso=_sso_ready(), who=who, role=role,\n"
     "                                  pc=pc)\n",
     '    role = who["role"] if who else "doctor"\n'
     "    pc = _is_clinic_pc(request)\n"
     '    sections = _visible_sections(role, pc, who["user"] if who else "")\n'
     "    s444 = _s444_home(who, role, sections)              # S444 (D647): a one-job login opens on its job; a login with no work is told so\n"
     '    if s444.get("redirect") is not None:\n'
     '        return s444["redirect"]\n'
     "    return render_template_string(PORTAL_HTML,\n"
     '                                  sections=s444.get("sections", sections),\n'
     "                                  sso=_sso_ready(), who=who, role=role,\n"
     '                                  pc=pc, s444_nowork=s444.get("nowork", False))\n')
edit("portal.py",
     "  {% endif %}\n"
     "  {% for label, items in sections %}\n"
     '  <div class="kick">{{ label }}</div>\n',
     "  {% endif %}\n"
     "  {% if s444_nowork %}\n"
     '  <div id="s444nowork" style="margin:0 0 14px;padding:16px;border:2px solid #a50e0e;border-radius:12px;background:#fff4f4;color:#1b1b1b">\n'
     '    <div style="font-size:19px;font-weight:700;color:#a50e0e;margin:0 0 6px">Is naam par koi kaam set nahi hai &mdash; sahi naam se sign in kijiye</div>\n'
     '    <div style="font-size:15px;margin:0 0 12px">Abhi aap <b>{{ who.user }}</b> naam se sign in hain.</div>\n'
     '    <a href="/portal/logout" style="display:block;text-align:center;padding:14px;border-radius:10px;background:#a50e0e;color:#fff;font-size:18px;font-weight:700;text-decoration:none">Sign out</a>\n'
     "  </div>\n"
     "  {% endif %}\n"
     "  {% for label, items in sections %}\n"
     '  <div class="kick">{{ label }}</div>\n')
edit("portal.py",
     '@app.route("/portal")\n'
     '@app.route("/portal/")\n'
     "def home():\n",
     "# ---- S444_STAFF_SAFE (01-Oct-2026, D647 / F-669): the home of a one-job login, and of a login with no work --------------------\n"
     "# users.<name>.home in tile_grants.json (a path inside this site) sends that login there on the FIRST /portal of a sign-in\n"
     "# (remembered per sign-in -- the token's iat -- in a cookie of its own); /portal?all=1 shows the tiles as before. A staff login\n"
     "# shown nothing but the tiles every staff login gets by role sees, in Hindi, that no work is set on this name, and a big Sign\n"
     "# out; its own punch page (Meri attendance) stays.\n"
     'S444_HOME_COOKIE = "clinic_portal_home"\n'
     'S444_OWN_TILES = ("Meri attendance",)\n'
     "\n"
     "\n"
     "def _s444_home_target(user):\n"
     "    try:\n"
     '        h = (((_tile_grants() or {}).get("users") or {}).get(user) or {}).get("home")\n'
     "    except Exception:\n"
     "        return None\n"
     '    if isinstance(h, str) and h.startswith("/") and not h.startswith("//") and len(h) <= 200 \\\n'
     '            and not any(c in h for c in "\\\\\\r\\n\\"\'<> "):\n'
     "        return h\n"
     "    return None\n"
     "\n"
     "\n"
     "def _s444_home(who, role, sections):\n"
     "    out = {}\n"
     "    if not who:\n"
     "        return out\n"
     '    user = who.get("user") or ""\n'
     "    target = _s444_home_target(user)\n"
     '    if target and request.args.get("all") != "1":\n'
     '        mark = "%s:%s" % (user, who.get("iat") or "")\n'
     "        if request.cookies.get(S444_HOME_COOKIE) != mark:\n"
     "            resp = make_response(redirect(target, code=302))\n"
     "            resp.set_cookie(S444_HOME_COOKIE, mark, max_age=31 * 24 * 3600, secure=True, httponly=True,\n"
     '                            samesite="Lax", path="/portal")\n'
     '            out["redirect"] = resp\n'
     "            return out\n"
     '    if role == "staff":\n'
     "        try:\n"
     "            _mask, extra, _order = _grants_for(user, role)\n"
     "        except Exception:\n"
     "            extra = set()\n"
     "        shown = [t for _g, items in sections for t in items]\n"
     '        if not any(t["name"] in extra and role not in t["roles"] for t in shown):\n'
     '            keep = [(g, [t for t in items if t["name"] in S444_OWN_TILES]) for g, items in sections]\n'
     '            out["sections"] = [(g, items) for g, items in keep if items]\n'
     '            out["nowork"] = True\n'
     "    return out\n"
     "# ---- S444_STAFF_SAFE end --------------------------------------------------------------------------------------------------------\n"
     "\n"
     "\n"
     '@app.route("/portal")\n'
     '@app.route("/portal/")\n'
     "def home():\n")

# ------------------------------------------------------------------ tile_grants.json (PARENT'S, declared): v31, amir's home
edit("tile_grants.json",
     "porders.senders. Nothing else in this file moves.\",\n",
     "porders.senders. Nothing else in this file moves. | v31 (S444, 01-Oct-2026, D647): amir gains 'home': /finance/amir -- his "
     "first /portal of a sign-in opens Amir ka kaam; /portal?all=1 (the 'Sab tiles' link on his pages) shows his tiles as before. "
     "Nobody else has a home. Nothing else in this file moves.\",\n")
edit("tile_grants.json", '  "version": 30,\n', '  "version": 31,\n')
edit("tile_grants.json", '    "amir": {\n      "extra": [\n', '    "amir": {\n      "home": "/finance/amir",\n      "extra": [\n')

# ------------------------------------------------------------------ amir_day.py (Sanjeevni)
edit("amir_day.py",
     'REASONS = (\n    ("ok",        "Theek hai"),\n    ("short",     "Kam maal aaya"),\n',
     'REASONS = (\n    ("ok",        "Theek hai"),\n'
     '    ("self",      "Meri entry galat thi — Marg mein theek kar di"),    # S444 (F-670): his own slip -- no claim; clears itself\n'
     '    ("short",     "Kam maal aaya"),\n')
edit("amir_day.py", '    (6, "Salt/naam"),\n',
     '    (6, "Marg sudhar"),                                  # S444 (F-672): every Marg fix he owes, in one place\n')
edit("amir_day.py",
     "    exports = _export_state(cx, day, wait_since)\n"
     "    today_bills, carry_bills, flagged_bills = _bills(cx, day)\n",
     "    exports = _export_state(cx, day, wait_since)\n"
     "    _s444_self_clear(cx)                                 # S444: his own corrections clear themselves once Marg shows the paper's amount\n"
     "    today_bills, carry_bills, flagged_bills = _bills(cx, day)\n"
     "    _s444_enrich(cx, today_bills + carry_bills + flagged_bills)   # S444: Marg's amount beside the paper's, on every bill\n")
edit("amir_day.py",
     '        "salt_list": _salt_list_state(cx, day),           # S243: a prompt, not a gate\n',
     '        "salt_list": _salt_list_state(cx, day),           # S243: a prompt, not a gate\n'
     '        "s444": _s444_state(cx, day),                     # S444: the vouchers, the renames, the salt list owed -- never a gate\n')
edit("amir_day.py",
     '        out.append("salt and name list not ticked")\n    return out\n',
     '        out.append("salt and name list not ticked")\n'
     "    out.extend(_s444_left(w))                            # S444: words only -- GATE_STEPS unchanged\n"
     "    return out\n")
edit("amir_day.py",
     '    return _shell("Amir -- kaam", _banner(step, w) + head + body + _neft_card_s407() + _packs_card_s408() +\n'
     '                  "<p class=foot>Step %d of 7</p>" % step, head_extra)\n',
     '    return _shell("Amir -- kaam", _s444_who_line() + _banner(step, w) + (_s444_card(w, top=True) if step != 6 else "") + head + body\n'
     "                  + _neft_card_s407() + _packs_card_s408() +\n"
     "                  \"<p class=foot>Step %d of 7 &middot; <a href='/portal?all=1'>Sab tiles</a></p>\" % step, head_extra)\n")
edit("amir_day.py",
     '            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s"\n',
     '            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s%s"\n')
edit("amir_day.py",
     "               was, i, _esc(key), i, _esc(ok_label), why))\n",
     "               _s444_paper_line(b), was, i, _esc(key), i, _esc(ok_label), why))\n")
edit("amir_day.py",
     '        written += 1\n        if reason == "ok":\n',
     '        written += 1\n'
     '        if reason == "self":\n'
     "            s444_mark_self(cx, supplier_norm, bill_no, bill_date, user)   # S444 (F-670): no claim; waits for Marg's next export\n"
     '        if reason == "ok":\n')
edit("amir_day.py",
     "def _step6(w):\n"
     "    body = (_export_band(w) +\n"
     '            "<div class=card><h2>Salt, naye item aur naam</h2>"\n',
     "def _step6(w):\n"
     "    # S444 (F-672): 'Marg sudhar' -- (a) the count's stock vouchers, orthotic first; (b) the renames once the proof is green;\n"
     "    # (c) the salt work as before, with the SALT WISE ITEM LIST card while it is owed. Each goes when done; none holds the day.\n"
     "    body = (_export_band(w) + _s444_card(w) + _s444_salt_card(w) +\n"
     '            "<div class=card><h2>Salt, naye item aur naam</h2>"\n')
edit("amir_day.py",
     '    return _page(6, w, "Salt / naam", body)\n',
     '    return _page(6, w, "Marg sudhar", body)\n')
edit("amir_day.py",
     "                 \"<p><a class=btn href='/finance/amir'>Jahan chhoda tha wahan se</a></p>\")\n"
     '        return _page(7, w, "Abhi baaki", body)\n',
     "                 \"<p><a class=btn href='/finance/amir'>Jahan chhoda tha wahan se</a></p>\")\n"
     "        body += _s444_salt_card(w, close=True)               # S444: the salt list, also while the day is not ready\n"
     '        return _page(7, w, "Abhi baaki", body)\n')
edit("amir_day.py",
     "    if prompt:\n"
     "        rows.append(prompt)\n"
     '    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>" % "".join(rows)\n',
     "    if prompt:\n"
     "        rows.append(prompt)\n"
     "    rows.extend(_s444_summary_rows(w))                  # S444: the vouchers / renames he still owes -- never a gate\n"
     '    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>%s" % ("".join(rows), _s444_salt_card(w, close=True))\n')

# ------------------------------------------------------------------ amir_salts.py (Sanjeevni)
edit("amir_salts.py",
     '    return _shell("Salt ka kaam", "".join(body))\n',
     '    return _shell("Salt ka kaam", _s444_top(cx) + "".join(body))     # S444: who is signed in; the salt list owed\n')

# ------------------------------------------------------------------ reports_tile.py (Sanjeevni): Shavez's salt row
edit("reports_tile.py",
     '              hint="salt ka kaam hua hai -- nayi list chahiye" if due else "aaj aayi")\n    return st\n',
     '              hint="salt ka kaam hua hai -- nayi list chahiye" if due else "aaj aayi")\n'
     '    if due:                                                   # S444 (F-671): owed (a tick is newer than the last list, even one of\n'
     "        try:                                                  # this morning) -- the days it has been owed; it stays red\n"
     "            since = (last_ok or newest_tick)[:10]\n"
     '            st["state"] = "due"\n'
     '            st["owed_days"] = max(0, (date.fromisoformat(today_iso) - date.fromisoformat(since)).days)\n'
     '            st["hint"] = "salt ka kaam hua hai -- nayi list chahiye (Excel) · %d din se baaki" % st["owed_days"]\n'
     "        except ValueError:\n"
     "            pass\n"
     "    return st\n")
edit("reports_tile.py",
     "    else:\n        state = \"<span class='state due'>&#9675; baaki</span>\"\n",
     '    elif r.get("owed_days") is not None:                        # S444: owed, red, with its days\n'
     "        state = \"<span class='state bad'>&#9675; %d din se baaki</span>\" % int(r[\"owed_days\"])\n"
     "    else:\n        state = \"<span class='state due'>&#9675; baaki</span>\"\n")
edit("reports_tile.py",
     '    body = head\n    b = s.get("banner")\n',
     "    body = head + ((\"<p class=small style='text-align:right;margin:-8px 0 8px'>Signed in: %s</p>\" % _esc(s[\"you\"])) if s.get(\"you\") else \"\")   # S444\n"
     '    b = s.get("banner")\n')
edit("reports_tile.py",
     "    cx = _db()\n    return render(status(cx, _today()))\n",
     "    cx = _db()\n"
     "    s = status(cx, _today())\n"
     '    s["you"] = str((u or {}).get("user") or "")                # S444 (D647): who is signed in, one quiet line\n'
     "    return render(s)\n")
edit("reports_tile.py",
     "    cx = _db()\n    return render(status(cx, d), picked_date=(d != _today()))\n",
     "    cx = _db()\n"
     "    s = status(cx, d)\n"
     '    s["you"] = str((u or {}).get("user") or "")                # S444\n'
     "    return render(s, picked_date=(d != _today()))\n")

# ------------------------------------------------------------------ sanjeevni_approvals.py (Sanjeevni): the Needs-you hook
edit("sanjeevni_approvals.py",
     "    # 7 · the statement's age (a word, not a fault)\n    info = []\n",
     "    # 15 · S444 (D647): Amir's slips as the owner's lines -- the salt list owed, his own correction unseen in Marg, Darpan's claims\n"
     "    #      open, the count vouchers untouched, the duty map's orphan duties, a report refused today (fail-soft).\n"
     "    #      NEEDS_YOU_WITHOUT_S444=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it.\n"
     '    if os.environ.get("NEEDS_YOU_WITHOUT_S444") != "1":\n'
     "        try:\n"
     "            import amir_day  # noqa: PLC0415\n"
     "            lines.extend(amir_day.needs_you_lines(con))\n"
     "        except Exception:  # noqa: BLE001\n"
     "            pass\n"
     "    # 7 · the statement's age (a word, not a fault)\n    info = []\n")

# ------------------------------------------------------------------ stock_app.py (Sanjeevni): the board's BACK, the board's visits
edit("stock_app.py",
     '    boot = json.dumps(dict(count_id=int(cid), user=(u or {}).get("user") or "", checker=_may_decide(u)))\n'
     '    return Response(html.replace("/*__BOOT__*/", "window.BOOT=" + boot + ";"), mimetype="text/html")\n'
     "\n\n"
     '@bp.route("/page/report")\n',
     '    boot = json.dumps(dict(count_id=int(cid), user=(u or {}).get("user") or "", checker=_may_decide(u)))\n'
     "    _s444_board_opened(con, int(cid), u)                  # S444 (F-672): his visit to the board is remembered (the owner's line d)\n"
     '    html = _s444_board_html(html, (u or {}).get("user") or "")   # S444: BACK to "Amir ka kaam", and who is signed in\n'
     '    return Response(html.replace("/*__BOOT__*/", "window.BOOT=" + boot + ";"), mimetype="text/html")\n'
     "\n\n"
     '@bp.route("/page/report")\n')

# ------------------------------------------------------------------ porders.py (Sanjeevni): "Signed in" in the S440 BACK bar only
edit("porders.py",
     '    login = str(u.get("login") or u.get("user") or "").lower()\n'
     '    if S441 is not None and S441.is_shared_login(login):          # S441: "Kaun kaam kar raha hai?" -- once per sitting\n'
     '        with open(PAGE, encoding="utf-8") as fh:\n'
     "            html = fh.read()\n"
     '        return html.replace("</body>", S441.who_script(login) + "</body>", 1), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}\n'
     "    return send_file(PAGE)\n",
     '    login = str(u.get("login") or u.get("user") or "").lower()\n'
     '    with open(PAGE, encoding="utf-8") as fh:\n'
     "        html = fh.read()\n"
     '    html = html.replace(\'<span id="ttl">Purchase orders</span></div>\',                     # S444 (D647): who is signed in, one quiet\n'
     '                        \'<span id="ttl">Purchase orders</span><span id="s444who" style="margin-left:10px;font-size:12px;\'   # line,\n'
     '                        \'opacity:.85;white-space:nowrap">Signed in: %s</span></div>\'                   # in the S440 BACK bar only\n'
     '                        % login.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), 1)\n'
     '    if S441 is not None and S441.is_shared_login(login):          # S441: "Kaun kaam kar raha hai?" -- once per sitting\n'
     '        return html.replace("</body>", S441.who_script(login) + "</body>", 1), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}\n'
     '    return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}\n')

APPEND = {"amir_day.py": "amir_block_s444.py", "stock_app.py": "stock_block_s444.py"}
SALTS_TAIL = (
    "\n\n"
    "# ---- S444_STAFF_SAFE (01-Oct-2026, D647 / F-671): who is signed in, and the salt list owed -- the same red card as his step 6 ----\n"
    "def _s444_top(cx):\n"
    '    out = ""\n'
    "    try:\n"
    "        u, err = _require(*_roles, unit=_unit)\n"
    '        who = "" if err else str((u or {}).get("user") or (u or {}).get("username") or "")\n'
    "        if who:\n"
    "            out += \"<p class=sub style='text-align:right;margin:0 0 6px'>Signed in: %s</p>\" % _esc(who)\n"
    "    except Exception:  # noqa: BLE001\n"
    "        pass\n"
    "    try:\n"
    "        import amir_day  # noqa: PLC0415\n"
    '        out += amir_day._s444_salt_card({"s444": {"salt": amir_day._s444_salt(cx)}})\n'
    "    except Exception:  # noqa: BLE001\n"
    "        pass\n"
    "    return out\n"
    "# ---- S444_STAFF_SAFE end ----\n")


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(portal, finance, out, check_pins=True):
    os.makedirs(out, exist_ok=True)
    built = {}
    for f in FROM:
        src = os.path.join(portal if WHERE.get(f) == "portal" else finance, f)
        raw = open(src, "rb").read()
        if check_pins and md5b(raw) != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- someone changed it since the brief; nothing written" % (src, md5b(raw), FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in E.get(f, []):
            n = txt.count(old)
            if n != 1:
                raise SystemExit("STOP: %s -- an anchor occurs %d times (must be exactly once): %r" % (f, n, old[:90]))
            txt = txt.replace(old, new, 1)
        if f in APPEND:
            blk = open(os.path.join(HERE, APPEND[f]), "rb").read().decode("utf-8")
            txt = txt.rstrip("\n") + "\n\n\n" + blk.strip("\n") + "\n"
        if f == "amir_salts.py":
            txt = txt.rstrip("\n") + "\n" + SALTS_TAIL
        built[f] = txt.encode("utf-8")
    g = json.loads(built["tile_grants.json"].decode("utf-8"))
    assert g["version"] == 31 and g["users"]["amir"]["home"] == "/finance/amir", "tile_grants.json did not come out as v31 with amir's home"
    assert sum(1 for u in g["users"].values() if "home" in u) == 1, "a home other than amir's"
    for f, b in built.items():
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("built %-24s %s -> %s  (%d edits%s)" % (f, FROM[f][:8], md5b(b), len(E.get(f, [])),
                                                       ", block appended" if f in APPEND or f == "amir_salts.py" else ""))
    return built


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-pins", action="store_true", help="build without the FROM check (never used by the installer)")
    a = ap.parse_args()
    build(a.portal, a.finance, a.out, check_pins=not a.no_pins)

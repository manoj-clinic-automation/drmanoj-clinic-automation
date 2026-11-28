#!/usr/bin/env python3
"""make_s978.py -- kit S978_STAFF_TAPS (the parent, S545, 28-Nov-2026; D1100, K2b). Remakes the four TO files from the FROM bytes.
Usage: make_s978.py FROM_DIR OUT_DIR   (FROM_DIR holds day_check.py register_push.py clinic_register.py tile_grants.json)
Every anchor must occur exactly once; anything else refuses (exit 1). No patient name or number in this file."""
import hashlib, json, os, sys

FROM = {"day_check.py": "5843d3d579c1571d058bd6e25d8585d4", "register_push.py": "2ba0d63b5c277113cbcfa9f40e2c1d3f",
        "clinic_register.py": "ba56418d46e029391a70556949c4e363", "tile_grants.json": "8a3cff12f66f5ad1ef73627b49091599"}
HERE = os.path.dirname(os.path.abspath(__file__))


def rep(txt, old, new, name):
    n = txt.count(old)
    if n != 1:
        sys.exit("REFUSED: %s anchor found %d times: %r" % (name, n, old[:80]))
    return txt.replace(old, new, 1)


def part(name):
    return open(os.path.join(HERE, name), encoding="utf-8").read()


def make_dc(t):
    n = "day_check.py"
    t = rep(t, 'DAYCHK_REVENUE=0 puts the S970 morning back exactly as it was.\n"""', part("s978_doc.txt") + '"""', n)
    t = rep(t, 'cards.append(_card("notfound", "nf:%s:%d" % (sec, left), left, d, who="docterz", tender=t, section=sec, cands=cands,',
            'cards.append(_card("notfound", "nf:%s:%d" % (sec, left), left, d, who="docterz", tender=t, section=sec, cands=cands,\n'
            '                           cell=((sec, t) if sdelta.get((sec, t), 0) == left else None),   # S978: the register one-tap', n)
    t = rep(t, 'cards.append(_card("less", "less:%s:%d" % (sec, g), g, d, who="docterz", section=sec, cands=cands,',
            'cards.append(_card("less", "less:%s:%d" % (sec, g), g, d, who="docterz", section=sec, cands=cands,\n'
            '                               cell=_s978_lcell(sdelta, sec, g),   # S978: the register one-tap', n)
    t = rep(t, '\n\ndef breakdown(chk, english=False):\n', '\n\n' + part("s978_block1.txt") + part("s978_block2.txt"), n)
    old = ('what_en="consultation (OPD parchi %d)" % s["slip_no"], what_hi="consultation (OPD parchi %d)" % s["slip_no"]))\n'
           '\n    # --- 2 · the money')
    new = ('what_en="consultation (OPD parchi %d)" % s["slip_no"], what_hi="consultation (OPD parchi %d)" % s["slip_no"]))\n'
           '        elif rev and _late978:                          # S978 (K2.2): the late parchi of a patient Docterz holds at Rs 0\n'
           '            ls = [s for s in ss if s["id"] in _late978]\n'
           '            if ls and not any(ln["section"] == "consult" and ln["amount_p"] > 0 and (ln["section"], ln["sn"]) not in held\n'
           '                              for ln in by_cid.get(cid, [])):\n'
           '                s = ls[0]\n'
           '                want.append(dict(amount=fee or 0, tick="", section="consult", cid=cid, name=_name(con, cid, lines, s), slip=s,\n'
           '                                 item=None, key="addopd:%d" % s["id"], opd=True,\n'
           '                                 what_en="consultation (OPD parchi %d, made late)" % s["slip_no"],\n'
           '                                 what_hi="consultation (OPD parchi %d, baad mein bani)" % s["slip_no"]))\n'
           '\n    # --- 2 · the money')
    t = rep(t, old, new, n)
    t = rep(t, '    for cid, ss in opd_ids.items():\n        if not by_cid.get(cid):',
            '    _late978 = _s978_late_ids(con, d) if rev else set()   # S978: parchis made from the nf: card\n'
            '    for cid, ss in opd_ids.items():\n        if not by_cid.get(cid):', n)
    t = rep(t, '"found": ("Found", "Mil gaya"), "regmistake": ("Register mistake", "Register ki galti")}',
            '"found": ("Found", "Mil gaya"), "regmistake": ("Register mistake", "Register ki galti"),\n'
            '                "dunno": ("Don\'t know — sent to Dr Manoj", "Pata nahi — Dr sahab ko bheja"),   # S978\n'
            '                "regfix": ("Register corrected", "Register theek kiya"), "lateslip": ("Parchi made", "Parchi bani")}', n)
    t = rep(t, '            "waits for the Docterz export" if english and c["who"] == "docterz" else\n'
               '            ("Docterz export ka intezaar" if c["who"] == "docterz" else ("waits for the parchi" if english else "parchi ka intezaar")))',
            '            (("Dr Manoj decides" if english else "Dr sahab dekhenge") if t["act"] == DUNNO_ACT else   # S978\n'
            '             "waits for the Docterz export" if english and c["who"] == "docterz" else\n'
            '             ("Docterz export ka intezaar" if c["who"] == "docterz" else ("waits for the parchi" if english else "parchi ka intezaar"))))', n)
    t = rep(t, '        elif c["kind"] == "less":                        # S977 (K2.3): register wrong, or who did not pay\n'
               '            btns.append("<a class=\'tb\' href=\'/finance/clinic/register/%s\'>%s</a>" % (\n'
               '                d, "The register was wrong" if english else "Register galat tha"))\n',
            '        elif c["kind"] == "less":                        # S977 (K2.3): register wrong, or who did not pay\n'
            '            _rb = _s978_regbtn(con, c, d, english) if taps_on() else ""   # S978 (K2.4): the register one-tap\n'
            '            btns.append(_rb or "<a class=\'tb\' href=\'/finance/clinic/register/%s\'>%s</a>" % (\n'
            '                d, "The register was wrong" if english else "Register galat tha"))\n', n)
    t = rep(t, '                btns.append(_btn(d, c["key"], "lessnp", "Did not pay" if english else "Paise nahi diye", "x",\n'
               '                                 "<select name=\'pick\' class=\'rs\'>%s</select>" % sel))\n',
            '                btns.append(_btn(d, c["key"], "lessnp", "Did not pay" if english else "Paise nahi diye", "x",\n'
            '                                 "<select name=\'pick\' class=\'rs\'>%s</select>" % sel))\n'
            '                if taps_on():                            # S978 (F-1733): a refund, always paid back in cash\n'
            '                    btns.append(_btn(d, c["key"], "lessref", "It was a refund (cash)" if english else "Refund tha (cash)", "x",\n'
            '                                     "<select name=\'pick\' class=\'rs\'>%s</select>" % sel))\n'
            '            if taps_on():\n'
            '                btns.append(_btn(d, c["key"], "dunno", "Don\'t know" if english else "Pata nahi", "x"))\n', n)
    t = rep(t, '        elif c["kind"] == "notfound":\n            opts = _day_people(con, d)',
            '        elif c["kind"] == "notfound" and taps_on() and str(c["key"]).count(":") == 2:   # S978 (K2.2): the three taps\n'
            '            btns.extend(_s978_nf_btns(con, c, u, english, d))\n'
            '        elif c["kind"] == "notfound":\n            opts = _day_people(con, d)', n)
    t = rep(t, '        out.append("<h3 class=\'grp\'>%s</h3>" % _esc(en if english else hi))\n        for c in cs:\n',
            '        out.append("<h3 class=\'grp\'>%s</h3>" % _esc(en if english else hi))\n'
            '        if g == "docterz" and taps_on() and can_docterz(u) and _s978_open_plain(chk):   # S978: the per-card ticks, one tap\n'
            '            _pk = [x["key"] for x in _s978_open_plain(chk)]\n'
            '            out.append(_btn(d, "", "saball", ("All done (%d)" if english else "Sab ho gaya (%d)") % len(_pk), "",\n'
            '                            "<input type=\'hidden\' name=\'keys\' value=\'%s\'>" % _esc(",".join(_pk))))\n'
            '        for c in cs:\n', n)
    t = rep(t, '    out.append(_bank_html(con, d, u, english))           # S641: the bank part, as Morning match shows it\n',
            '    if taps_on():\n'
            '        out.append(_s978_made_html(con, d, u, english))  # S978: late parchis and register fixes, with their Undo\n'
            '    out.append(_bank_html(con, d, u, english))           # S641: the bank part, as Morning match shows it\n', n)
    t = rep(t, '    if a == "undo":\n        undo_tick(con, date, key, who)\n',
            '    if a in ("undolate", "undoreg", "saball") and taps_on():   # S978: rows with no card of their own\n'
            '        try:\n'
            '            if a == "saball":\n'
            '                if not can_docterz(u):\n'
            '                    return done(er="Not permitted." if english else "Aapke liye nahi.")\n'
            '                n = _s978_saball(con, date, chk, who, set(k for k in (f.get("keys") or "").split(",") if k))\n'
            '                return done(("%d line(s) ticked." % n) if english else ("%d line tick ki." % n))\n'
            '            return done(*_s978_undo(con, date, a, int(f.get("tid") or 0), u, who, english))\n'
            '        except Exception as ex:                          # noqa: BLE001\n'
            '            try:\n'
            '                con.rollback()\n'
            '            except Exception:                            # noqa: BLE001\n'
            '                pass\n'
            '            return done(er=str(ex)[:200])\n'
            '    if a == "undo":\n        undo_tick(con, date, key, who)\n', n)
    t = rep(t, '            return done(*_s977_lessnp(con, date, card, (f.get("pick") or "")[:12], who, english))\n',
            '            return done(*_s977_lessnp(con, date, card, (f.get("pick") or "")[:12], who, english))\n'
            '        if a == "lessref" and card.get("kind") == "less" and can_docterz(u) and taps_on():   # S978 (F-1733)\n'
            '            return done(*_s977_lessnp(con, date, card, (f.get("pick") or "")[:12], who, english, how="returned"))\n'
            '        if a == "lateslip" and card.get("kind") == "notfound" and can_docterz(u) and taps_on():   # S978 (K2.2)\n'
            '            return done(*_s978_late(con, date, card, f, who, english))\n'
            '        if a == "regfix" and card.get("kind") in ("notfound", "less") and can_docterz(u) and taps_on():   # S978 (K2.4)\n'
            '            return done(*_s978_regfix(con, date, card, f, who, english))\n'
            '        if (a == "dunno" and card["who"] == "docterz" and card.get("kind") in ("notfound", "less") and can_docterz(u)\n'
            '                and taps_on()):                          # S978: the line goes to his push\n'
            '            add_tick(con, date, key, DUNNO_ACT, who)\n'
            '            _s978_push(con, date)\n'
            '            return done("Sent to Dr Manoj." if english else "Dr sahab ko bheja.")\n', n)
    t = rep(t, 'def _s977_lessnp(con, d, card, pick, who, english):', 'def _s977_lessnp(con, d, card, pick, who, english, how="never_taken"):', n)
    t = rep(t, 'cid=pick, how="never_taken", tender="",', 'cid=pick, how=how, tender=("cash" if how == "returned" else ""),', n)
    t = rep(t, '        sa.add_cancel(con, who, int(hit[0]["id"]), pick, "never_taken", note="day check S977")\n',
            '        sa.add_cancel(con, who, int(hit[0]["id"]), pick, how, note=("day check S978 refund" if how == "returned" else "day check S977"),\n'
            '                      tender=("cash" if how == "returned" else ""))   # S978: a refund is always paid back in cash (D1109)\n', n)
    t = rep(t, '    return ("Sent for approval — the day matches once it is in." if english else "Manzoori ke liye gaya — din mil jayega."), ""\n',
            '    if how == "returned":                                # S978\n'
            '        _s978_push(con, d)\n'
            '        return ("Refund noted (cash) — sent for approval; the day matches once it is in." if english else\n'
            '                "Refund likh liya (cash) — manzoori ke liye gaya; din mil jayega."), ""\n'
            '    return ("Sent for approval — the day matches once it is in." if english else "Manzoori ke liye gaya — din mil jayega."), ""\n', n)
    t = rep(t, 'details.s962m{margin:0 0 12px}details.s962m summary{font-size:17px;color:#2c6e2f;cursor:pointer}\n</style>"""\n',
            part("s978_style.txt"), n)
    # review S3: a section whose money was placed into a GUESSED tender offers no one-cell register fix
    t = rep(t, '    backdate, nid_placed = [], 0\n', '    backdate, nid_placed = [], 0\n    _guess978 = set()                                    # S978 (review S3)\n', n)
    t = rep(t, '            t = w["tick"] if w["tick"] in TENDERS else max(TENDERS, key=lambda x: delta[x])\n',
            '            t = w["tick"] if w["tick"] in TENDERS else max(TENDERS, key=lambda x: delta[x])\n'
            '            if w["tick"] not in TENDERS:\n'
            '                _guess978.add(w["section"])\n', n)
    t = rep(t, '        out["s977_left"] = _s977_left(con, d, cards, delta, sdelta, paid_lines, lines)\n',
            '        out["s977_left"] = _s977_left(con, d, cards, delta, sdelta, paid_lines, lines)\n'
            '        for _c in cards:                                 # S978 (review S3): no fix on a guessed tender\n'
            '            if _c.get("cell") and _c["cell"][0] in _guess978:\n'
            '                _c["cell"] = None\n', n)
    t = rep(t, '    out["top"], out["backdate"], out["refunds"] = top, backdate, refunds\n',
            '    out["top"], out["backdate"], out["refunds"] = top, backdate, refunds\n'
            '    out["s978_fixes"] = _s978_fixes(con, d)               # S978 (review S6): his push names every register fix\n', n)
    return t


def make_rp(t):
    n = "register_push.py"
    t = rep(t, 'VERSION = "S977 1"', 'VERSION = "S978 1"', n)
    t = rep(t, '        if c.get("who") == "hand" and k.startswith(OWNER_KEYS) and not c.get("tick"):\n'
               '            out[k] = (c.get("en") or c.get("hi") or "", int(c.get("amount") or 0))\n',
            '        if c.get("who") == "hand" and k.startswith(OWNER_KEYS) and not c.get("tick"):\n'
            '            out[k] = (c.get("en") or c.get("hi") or "", int(c.get("amount") or 0))\n'
            '        elif (c.get("tick") or {}).get("act") == "dunno" and c.get("who") == "docterz":   # S978: the staff said \'Pata nahi\'\n'
            '            out["pn:" + _norm(k)] = ("Staff don\'t know: " + (c.get("en") or c.get("hi") or ""), int(c.get("amount") or 0))\n'
            '    for fx in chk.get("s978_fixes") or []:                  # S978 (review S6): a register figure set from the day check\n'
            '        _k = "rf:%s:%d>%d%s" % (fx["field"], fx["was"], fx["now"], ":undone" if fx.get("undone") else "")   # one line per fix\n'
            '        out[_k] = ("Register %s from the day check by %s: %s Rs %s -> Rs %s" % (\n'
            '            "fix UNDONE" if fx.get("undone") else "corrected", fx["who"].title(), fx["field"].replace("_p", "").replace("_", " "),\n'
            '            "{:,}".format(fx["was"] // 100), "{:,}".format(fx["now"] // 100)), abs(fx["now"] - fx["was"]))\n', n)
    t = rep(t, '    amt = sum(lines[k][1] for k in new)\n',
            '    amt = sum(lines[k][1] for k in new if not k.startswith("rf:"))   # S978 (second look S3): a fix is no gap\n', n)
    t = rep(t, '    title = "%s: Rs %s not explained" % (dm(day), "{:,}".format(int(round(amt / 100.0))))\n',
            '    title = "%s: Rs %s not explained" % (dm(day), "{:,}".format(int(round(amt / 100.0))))\n'
            '    if all(k.startswith("rf:") for k in new):            # S978: a register fix is news, not a gap\n'
            '        title = "%s: the register was corrected from the day check" % dm(day)\n', n)
    return t


def make_cr(t):
    n = "clinic_register.py"
    t = rep(t, '\ndef _s636_check(con, d, u):\n', '\n' + part("s978_crset.txt"), n)
    t = rep(t, '    todo = [d for d in days if d not in done]\n    if todo:\n',
            '    todo = [d for d in days if d not in done]\n'
            '    _t = _s978_today()                                 # S978 (K2b; his 15:09 27-Nov "morning for register work"): in the\n'
            '    _pv = next((d for d in days if d < _t), None)       # morning, before the last working day is saved, it opens on THAT day\n'
            '    if _pv and _pv in todo and _s978_hour() < S978_MORNING_UNTIL:   # review S5: the evening opens today, as before\n'
            '        return redirect("/finance/clinic/register/%s" % _pv)\n'
            '    if todo:\n', n)
    return t


def make_tg(t):
    n = "tile_grants.json"
    j = json.loads(t)
    if j.get("version") != 49:
        sys.exit("REFUSED: tile_grants.json version %r, not 49" % j.get("version"))
    t = rep(t, '"version": 49', '"version": 50', n)
    for who in ("shavez", "shivani", "alisha"):
        ex = j["users"][who]["extra"]
        if "Day check" in ex or "Morning match" not in ex:
            sys.exit("REFUSED: %s's extra list is not as expected" % who)
    out, cur, done = [], None, set()
    for ln in t.split("\n"):
        s = ln.strip()
        if ln.startswith('  "') and not ln.startswith('   ') and s.endswith('": {'):
            cur = s[1:].split('"')[0]
        out.append(ln)
        if cur in ("shavez", "shivani", "alisha") and s in ('"Morning match",', '"Morning match"') and cur not in done:
            ind = ln[:len(ln) - len(ln.lstrip())]
            if s.endswith(","):
                out.append(ind + '"Day check",')
            else:
                out[-1] = ln + ","
                out.append(ind + '"Day check"')
            done.add(cur)
    if done != {"shavez", "shivani", "alisha"}:
        sys.exit("REFUSED: tile_grants.json -- 'Day check' placed for %s only" % sorted(done))
    t = "\n".join(out)
    j2 = json.loads(t)
    for who in j["users"]:
        if who in ("shavez", "shivani", "alisha"):
            if j2["users"][who]["extra"] != j["users"][who]["extra"][:j["users"][who]["extra"].index("Morning match") + 1] + \
                    ["Day check"] + j["users"][who]["extra"][j["users"][who]["extra"].index("Morning match") + 1:]:
                sys.exit("REFUSED: tile_grants.json -- %s's list came out wrong" % who)
            if {k: v for k, v in j2["users"][who].items() if k != "extra"} != {k: v for k, v in j["users"][who].items() if k != "extra"}:
                sys.exit("REFUSED: tile_grants.json -- %s changed beyond the one line" % who)
        elif j2["users"][who] != j["users"][who]:
            sys.exit("REFUSED: tile_grants.json -- %s changed" % who)
    if {k: v for k, v in j2.items() if k not in ("users", "version")} != {k: v for k, v in j.items() if k not in ("users", "version")}:
        sys.exit("REFUSED: tile_grants.json -- more than the users and the version changed")
    return t


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    for name, want in FROM.items():
        b = open(os.path.join(src, name), "rb").read()
        if hashlib.md5(b).hexdigest() != want:
            sys.exit("REFUSED: %s is %s, not %s" % (name, hashlib.md5(b).hexdigest()[:8], want[:8]))
    fn = {"day_check.py": make_dc, "register_push.py": make_rp, "clinic_register.py": make_cr, "tile_grants.json": make_tg}
    for name in FROM:
        t = open(os.path.join(src, name), encoding="utf-8").read()
        t2 = fn[name](t)
        with open(os.path.join(dst, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t2)
        print("MADE %s %s" % (name, hashlib.md5(t2.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()

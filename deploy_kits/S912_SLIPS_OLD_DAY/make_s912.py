"""make_s912.py -- kit S912_SLIPS_OLD_DAY (the parent, S496, 21-Nov-2026). Anchored patches on the live bytes.
usage: python make_s912.py <dir with slip_log.py + parchi_desk.py at their FROM pins> <out dir>
  slip_log.py   c2cf351a -> TO : WRITING a missed parchi reaches 31 days back (edits / removals / radd stay at 7);
                                 an old day's form opens with the number box EMPTY (not today's next number);
                                 a number Shavez marked Radd on that OLD day (his ask still pending) can be written as the parchi it was,
                                 the ask set aside; the 'already written' message names the slip's day and patient;
                                 the Din list shows 15 days, plus the day opened if it is older.
  parchi_desk.py 548d68ca -> TO: on an old day the desk's number boxes start empty ('us din ka number').
"""
import hashlib, os, sys

FROM = {"slip_log.py": "c2cf351a74b983e883be6bed1e5d918b", "parchi_desk.py": "548d68ca9776ab5a97b6590dbdea3fdd"}

P = {"slip_log.py": [
("LATE_DAYS = 7             # S401: a missed parchi can be written up to this many days after its day\n",
 "LATE_DAYS = 7             # S401: a missed parchi can be written up to this many days after its day\n"
 "ENTRY_DAYS = 31           # S912 (21-Nov-2026): WRITING a missed parchi reaches a month back; edits, removals, radd stay at LATE_DAYS\n"
 "DAY_LIST = 14             # S912: the Din list shows today and the last 14 days (+ the day opened, if older)\n"),
("def _day_word(iso):\n",
 "def _entry_day(v):\n"
 "    \"\"\"S912: as _late_day, for WRITING a missed parchi only -- up to ENTRY_DAYS back. Blank is today; else None (refused).\"\"\"\n"
 "    t = _now().date()\n    if not (v or \"\").strip():\n        return t.isoformat()\n"
 "    try:\n        d = dt.date.fromisoformat(v.strip()[:10])\n    except ValueError:\n        return None\n"
 "    return d.isoformat() if t - dt.timedelta(days=ENTRY_DAYS) <= d <= t else None\n\n\n"
 "def _day_word(iso):\n"),
("    day = _late_day(f.get(\"day\"))                        # S401\n    if day is None:\n"
 "        return _form_err(\"Din sahi chunein — aaj se %d din pehle tak.\" % LATE_DAYS)\n",
 "    day = _entry_day(f.get(\"day\"))                       # S401; S912: a month back\n    if day is None:\n"
 "        return _form_err(\"Din sahi chunein — aaj se %d din pehle tak.\" % ENTRY_DAYS)\n"),
("    want_day = _late_day(request.args.get(\"day\")) or _today()\n",
 "    want_day = _entry_day(request.args.get(\"day\")) or _today()     # S912: a month back\n"),
("                   + head2 + _patient_block(opd if (_late_day(request.args.get(\"day\")) or today) == today else\n"
 "                                            [x for x in day_slips(con, _late_day(request.args.get(\"day\"))) if x[\"series\"] == \"opd\"], True) +\n",
 "                   + head2 + _patient_block(opd if (_entry_day(request.args.get(\"day\")) or today) == today else\n"
 "                                            [x for x in day_slips(con, _entry_day(request.args.get(\"day\"))) if x[\"series\"] == \"opd\"], True) +\n"),
("    t = _now().date()\n    o = []\n    for i in range(LATE_DAYS + 1):\n        d = (t - dt.timedelta(days=i)).isoformat()\n"
 "        o.append('<option value=\"%s\"%s>%s</option>' % (d, \" selected\" if d == sel else \"\",\n",
 "    t = _now().date()\n    o = []\n    _days = [(t - dt.timedelta(days=i)).isoformat() for i in range(DAY_LIST + 1)]\n"
 "    if sel and sel not in _days and _entry_day(sel) == sel:                  # S912: the day opened, if older than the list\n"
 "        _days.append(sel)\n    for i, d in enumerate(_days):\n"
 "        o.append('<option value=\"%s\"%s>%s</option>' % (d, \" selected\" if d == sel else \"\",\n"),
("    return nx, head + ('<div class=\"row\"><label>Parchi no.<input name=\"slip_no\" inputmode=\"numeric\" class=\"no\" '\n"
 "                       'value=\"%d\" required></label><span class=\"sm\">book %d–%d</span></div>'\n"
 "                       % (want_no or nx, b[\"first_no\"], b[\"last_no\"])) + _day_select(want_day)\n",
 "    old = want_day != _today()                          # S912: an old day's number is that day's paper, never today's next\n"
 "    val = str(want_no) if want_no else (\"\" if old else str(nx))\n"
 "    ph = ' placeholder=\"us din ki parchi ka number\"' if (old and not want_no) else \"\"\n"
 "    return nx, head + ('<div class=\"row\"><label>Parchi no.<input name=\"slip_no\" inputmode=\"numeric\" class=\"no\" '\n"
 "                       'value=\"%s\"%s required></label><span class=\"sm\">book %d–%d</span></div>'\n"
 "                       % (val, ph, b[\"first_no\"], b[\"last_no\"])) + _day_select(want_day)\n"),
("    cur = _live(con, series, slip_no)\n    if cur is not None and cur[\"state\"] != \"missing\":\n"
 "        raise SlipError(\"Parchi %d pehle se likhi hai (%s, %s). Galat ho to 'Aaj ki list' se hatayein.\"\n"
 "                        % (slip_no, cur[\"logged_by\"] or \"?\", (cur[\"logged_at\"] or \"\")[11:16]))\n",
 "    cur = _live(con, series, slip_no)\n    _s912_radd = []\n"
 "    if cur is not None and cur[\"state\"] == \"cancelled\" and cur[\"day\"] == (day or _today()) and (day or _today()) != _today():\n"
 "        _s912_radd = _s912_radd_asks(con, cur[\"id\"])        # S912: a number marked Radd on an OLD day, its ask still pending\n"
 "        if _s912_radd is None:\n"
 "            raise SlipError(\"Parchi %d: radd ki jaankari abhi padh nahi paaye -- thodi der baad Save karein.\" % slip_no)\n"
 "        if any(a[\"state\"] == \"approved\" for a in _s912_radd):\n"
 "            raise SlipError(\"Parchi %d ka radd Sir ne manzoor kar diya hai -- yeh number nahi likh sakte. Sir se kahein.\" % slip_no)\n"
 "        if not any(a[\"state\"] == \"pending\" for a in _s912_radd):\n"
 "            _s912_radd = []\n"
 "    if cur is not None and cur[\"state\"] != \"missing\" and not _s912_radd:\n"
 "        raise SlipError(\"Parchi %d pehle se likhi hai -- %s ki%s (%s, %s). Galat ho to us din ki list se hatayein.\"\n"
 "                        % (slip_no, _dmy(cur[\"day\"])[:6] if cur[\"day\"] else \"?\",\n"
 "                           (\", ID %s\" % cur[\"clinic_id\"]) if (cur[\"clinic_id\"] and cur[\"state\"] == \"ok\") else\n"
 "                           (\", %s\" % {\"cancelled\": \"radd\", \"spoilt\": \"kharab\"}.get(cur[\"state\"], cur[\"state\"])),\n"
 "                           cur[\"logged_by\"] or \"?\", (cur[\"logged_at\"] or \"\")[11:16]))\n"),
("    if cur is not None:                                   # a number that was left as missing, now filled\n",
 "    if _s912_radd:                                        # S912: its pending radd ask is set aside -- the number is a parchi after all\n"
 "        for a in _s912_radd:\n"
 "            if a[\"state\"] == \"pending\":\n"
 "                con.execute(\"UPDATE slip_adjust SET state='replaced', checked_by=?, checked_at=?, check_note=? WHERE id=? AND state='pending'\",\n"
 "                            (who, now, \"S912: the number written as a parchi\", a[\"id\"]))\n"
 "        _audit_safe(con, cur[\"id\"], \"slip_radd_written_s912\", json.dumps({\"state\": cur[\"state\"], \"clinic_id\": cur[\"clinic_id\"]}),\n"
 "                    json.dumps({\"state\": \"ok\", \"clinic_id\": clinic_id}), who)\n"
 "    if cur is not None:                                   # a number that was left as missing, now filled\n"),
("    note = \"\"\n    if gap:\n",
 "    note = (\"Yeh number pehle radd likha tha -- ab parchi hai; radd ki arzi hata di.\" if _s912_radd else \"\")   # S912\n"
 "    if gap:\n"),
("def items_from_form(con, form):\n",
 "def _s912_radd_asks(con, slip_id):\n"
 "    \"\"\"S912: the radd asks (slip_adjust kind 'cancel') on one slip, pending or approved; None when they cannot be read.\"\"\"\n"
 "    try:\n"
 "        return [dict(r) for r in con.execute(\"SELECT id, state FROM slip_adjust WHERE slip_id=? AND kind='cancel' \"\n"
 "                                             \"AND state IN ('pending','approved')\", (slip_id,))]\n"
 "    except Exception:                                    # noqa: BLE001 -- unreadable: the write is refused\n"
 "        return None\n\n\n"
 "def items_from_form(con, form):\n"),
], "parchi_desk.py": [
(" if(!$('opd_no')._typed)$('opd_no').value=st.nx_opd||'';if(!$('xp_no')._typed)$('xp_no').value=st.nx_xp||'';\n",
 " var oldDay=(st.day!==st.today);   /* S912: an old day's number is that day's paper, never today's next */\n"
 " if(!$('opd_no')._typed)$('opd_no').value=oldDay?'':(st.nx_opd||'');if(!$('xp_no')._typed)$('xp_no').value=oldDay?'':(st.nx_xp||'');\n"
 " $('opd_no').placeholder=$('xp_no').placeholder=oldDay?(EN?'that day slip no.':'us din ka number'):'';\n"),
]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for name, edits in P.items():
        raw = open(os.path.join(src, name), "rb").read()
        if md5(raw) != FROM[name]:
            sys.exit("FAIL %s is %s, not its FROM %s" % (name, md5(raw)[:8], FROM[name][:8]))
        t = raw.decode("utf-8")
        for a, b in edits:
            n = t.count(a)
            if n != 1:
                sys.exit("FAIL %s: anchor found %d times: %r" % (name, n, a[:80]))
            t = t.replace(a, b, 1)
        new = t.encode("utf-8")
        open(os.path.join(out, name), "wb").write(new)
        print("%s %s -> %s" % (name, FROM[name][:8], md5(new)[:8]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

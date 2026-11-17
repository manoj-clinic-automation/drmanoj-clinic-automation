#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s846.py -- kit S846_SLIPS_NOT_IN_DOCTERZ (S471, 16-Nov-2026; the cold review fixes at S474, 17-Nov-2026). Builds the four patched files from the LIVE bytes.

    python make_s846.py <live_dir> <out_dir>

<live_dir> holds the live day_check.py, clinic_money.py, owner_console.py, parchi_desk.py (read from the newest bundle,
parchi_desk.py from S844's kit = its live pin 32f08523). Every anchor must occur exactly once or the build STOPS and
writes nothing. No patient name, no number, no secret (F-185).
"""
import hashlib
import os
import sys

FROM = {"day_check.py": "c23e3f2f", "clinic_money.py": "f8a64266", "owner_console.py": "72da1da8", "parchi_desk.py": "32f08523"}

P = {}

# ------------------------------------------------------------------ day_check.py
P["day_check.py"] = [
    ("    app.register_blueprint(bp)\n    return bp\n",
     "    app.register_blueprint(bp)\n"
     "    try:                                                  # S846: his 'Slips not in Docterz' page, beside this file\n"
     "        import not_in_docterz as _s846_nid                # noqa: PLC0415\n"
     "        _s846_nid.init(app, db_getter, require_fn, audit_fn)\n"
     "    except Exception as _ex_s846:                         # noqa: BLE001 -- the day check works without it\n"
     "        import sys as _sys                                # noqa: PLC0415\n"
     "        print(\"not_in_docterz NOT mounted: %s\" % _ex_s846, file=_sys.stderr)\n"
     "    return bp\n"),
    ("def check_day(con, d):\n",
     "S846_WORDS = {\"entered\": (\"entered in Docterz back-dated by Dr Manoj (not in this day's export yet)\",\n"
     "                          \"Dr Manoj ne Docterz mein purani tareekh se daal diya\"),\n"
     "              \"outside\": (\"kept outside Docterz by Dr Manoj\", \"Dr Manoj: Docterz ke bahar\"),\n"
     "              \"free\": (\"free / staff / home (Dr Manoj)\", \"free / staff / ghar (Dr Manoj)\"),\n"
     "              \"wrong\": (\"wrong slip (Dr Manoj)\", \"galat parchi (Dr Manoj)\")}\n"
     "\n"
     "\n"
     "def _s846_marks(con, d):\n"
     "    \"\"\"S846 (the owner, 16-Nov-2026): his answers on 'Slips not in Docterz' -- {(slip_id, kind): act}. {} when absent.\"\"\"\n"
     "    try:\n"
     "        import not_in_docterz                         # noqa: PLC0415\n"
     "        return not_in_docterz.marks_for_day(con, d)\n"
     "    except Exception:                                    # noqa: BLE001 -- the day check stands without it\n"
     "        return {}\n"
     "\n"
     "\n"
     "def _s846_act(marks, w):\n"
     "    s = w.get(\"slip\") or {}\n"
     "    if not marks or not s.get(\"id\") or w.get(\"partial\"):          # S474 review: a part-billed line is never his\n"
     "        return None\n"
     "    return marks.get((s[\"id\"], \"opd\" if w.get(\"opd\") else w.get(\"section\")))\n"
     "\n"
     "\n"
     "def _s846_note(w, act):\n"
     "    en, hi = S846_WORDS.get(act, (act, act))\n"
     "    return (\"%s %s · %s — %s\" % (rs(w[\"amount\"]), w[\"what_en\"], _who_en(w[\"name\"], w[\"cid\"]), en),\n"
     "            \"%s %s · %s — %s\" % (rs(w[\"amount\"]), w[\"what_hi\"], _who_en(w[\"name\"], w[\"cid\"]), hi))\n"
     "\n"
     "\n"
     "def check_day(con, d):\n"),
    ("    want.sort(key=lambda w: (0 if w[\"tick\"] else 1, -w[\"amount\"]))\n    for w in want:\n"
     "        if w[\"amount\"] > 0 and room >= w[\"amount\"]:\n",
     "    want.sort(key=lambda w: (0 if w[\"tick\"] else 1, -w[\"amount\"]))\n"
     "    _s846 = _s846_marks(con, d)                           # S846: his answers on his 'Slips not in Docterz' page\n"
     "    for w in want:\n"
     "        _sa = _s846_act(_s846, w)\n"
     "        if _sa in (\"free\", \"wrong\"):                 # nothing collected: nothing for the staff to do\n"
     "            out[\"notes\"].append(_s846_note(w, _sa))\n"
     "            continue\n"
     "        if w[\"amount\"] > 0 and room >= w[\"amount\"]:\n"),
    ("            room -= w[\"amount\"]\n            cards.append(_card(\"missing\"",
     "            room -= w[\"amount\"]\n"
     "            if _sa:                                       # S846: entered back-dated / kept outside -- the money is placed, no card\n"
     "                out[\"notes\"].append(_s846_note(w, _sa))\n"
     "                continue\n"
     "            cards.append(_card(\"missing\""),
]

# ------------------------------------------------------------------ clinic_money.py
P["clinic_money.py"] = [
    ("def match_day(con, d, now=None):\n",
     "def _s846_explained(con, d):\n"
     "    \"\"\"S846 (the owner, 16-Nov-2026): the day's slips he answered 'Entered in Docterz' (back-dated, not in this day's\n"
     "    export yet) or 'Not entering in Docterz' -- [(amount_p, act)]. [] when absent or unreadable (the match stands as before).\"\"\"\n"
     "    try:\n"
     "        import not_in_docterz                             # noqa: PLC0415\n"
     "        return not_in_docterz.explained_for_day(con, d)\n"
     "    except Exception:                                    # noqa: BLE001\n"
     "        return []\n"
     "\n"
     "\n"
     "def _s846_upi(con, d):\n"
     "    \"\"\"S846 (S474 review): the answered slips not marked as paid in cash -- the only ones a stray bank UPI may be. [] on a fault.\"\"\"\n"
     "    try:\n"
     "        import not_in_docterz                             # noqa: PLC0415\n"
     "        return not_in_docterz.upi_for_day(con, d)\n"
     "    except Exception:                                    # noqa: BLE001\n"
     "        return []\n"
     "\n"
     "\n"
     "def match_day(con, d, now=None):\n"),
    ("    if diff1 == 0:\n",
     "    _s846_x = _s846_explained(con, d)                    # S846: his answered slips explain counter > Docterz exactly\n"
     "    _s846_sum = sum(a for a, _k in _s846_x)\n"
     "    if _s846_sum and diff1 == _s846_sum:\n"
     "        _ent = sum(a for a, k in _s846_x if k == \"entered\")\n"
     "        expl(\"slips_not_in_docterz\", _s846_sum, \"The counter sheet has ₹%s more than Docterz's export — %s. Same money.\"\n"
     "             % (_r(_s846_sum), \"; \".join(w for w in (\n"
     "                 (\"₹%s entered in Docterz back-dated by Dr Manoj, not in this day's export yet\" % _r(_ent)) if _ent else \"\",\n"
     "                 (\"₹%s on slips Dr Manoj keeps outside Docterz\" % _r(_s846_sum - _ent)) if _s846_sum - _ent else \"\") if w)))\n"
     "    elif diff1 == 0:\n"),
    ("        for b in still_bank:\n            flag(",
     "        _s846_left = _s846_upi(con, d) if _s846_x else []\n"
     "        _s846_cap = max(0, r_t[\"upi\"] - d_t[\"upi\"])          # never more than the counter's UPI over Docterz's\n"
     "        for b in still_bank:\n"
     "            if b[\"amount_p\"] in _s846_left and b[\"amount_p\"] <= _s846_cap:   # S846: UPI for a slip he answered\n"
     "                _s846_left.remove(b[\"amount_p\"])\n"
     "                _s846_cap -= b[\"amount_p\"]\n"
     "                expl(\"slip_not_in_docterz_upi\", b[\"amount_p\"], \"₹%s reached the bank at %s (UPI ref …%s) — a slip Dr Manoj \"\n"
     "                     \"answered on 'Slips not in Docterz'. Not a gap.\" % (_r(b[\"amount_p\"]), b.get(\"txn_time\") or \"—\",\n"
     "                                                                     (b.get(\"rrn\") or \"\")[-4:]))\n"
     "                continue\n"
     "            flag("),
]

# ------------------------------------------------------------------ owner_console.py
P["owner_console.py"] = [
    ("def _sec_needs_map(con, cx):",
     "def _s846_nid_line(con):\n"
     "    \"\"\"S846 (the owner, 16-Nov-2026): slips whose patient is not in Docterz -- his to enter back-dated. None when none.\"\"\"\n"
     "    try:\n"
     "        import not_in_docterz as NID                     # noqa: PLC0415\n"
     "        n, _o = NID.counts(con)\n"
     "    except Exception:                                    # noqa: BLE001 -- the section stands without it\n"
     "        return None\n"
     "    if not n:\n"
     "        return None\n"
     "    return L(\"w\", \"%d slip%s not in Docterz -- yours to enter back-dated\" % (n, \"\" if n == 1 else \"s\"),\n"
     "             href=NID.PAGE_URL, link=\"Slips not in Docterz\")\n"
     "\n"
     "\n"
     "def _sec_needs_map(con, cx):"),
    ("    if bl:\n        lines.append(bl)\n",
     "    if bl:\n        lines.append(bl)\n"
     "    nl = _s846_nid_line(con)                                           # S846: slips not in Docterz, his to enter\n"
     "    if nl:\n        lines.append(nl)\n"),
    ("n, late = len(mine) + (1 if xl else 0) + (1 if bl else 0), sum(1 for i in mine if i[\"late\"])",
     "n, late = len(mine) + (1 if xl else 0) + (1 if bl else 0) + (1 if nl else 0), sum(1 for i in mine if i[\"late\"])"),
    ("        T.update(clinic=inr(amt) if amt is not None else \"–\", clinic_word=",
     "        try:                                                           # S846: his 'Not entering in Docterz' slips of the day\n"
     "            import not_in_docterz as NID                             # noqa: PLC0415\n"
     "            xo = NID.outside_for_day(con, D)\n"
     "            if xo:\n"
     "                out.append(L(\"n\", \"Slips outside Docterz (your answer): %d · %s — they explain the counter's extra over Docterz\"\n"
     "                             % (len(xo), inr(sum(xo))), href=NID.PAGE_URL, link=\"Slips not in Docterz\", sub=True))\n"
     "        except Exception:                                              # noqa: BLE001 -- the line stands without it\n"
     "            pass\n"
     "        T.update(clinic=inr(amt) if amt is not None else \"–\", clinic_word="),
]

# ------------------------------------------------------------------ parchi_desk.py (S844's live 32f08523)
P["parchi_desk.py"] = [
    ("        return _j(ok=True, known=True, name=p[0], new=new, far=False)\n",
     "        return _j(ok=True, known=True, name=p[0], new=new, far=False, old=_s846_old(con, cid, day))\n"),
    ("    return _j(ok=True, known=False, name=\"\", new=new, far=far, highest=hi)\n",
     "    return _j(ok=True, known=False, name=\"\", new=new, far=far, highest=hi, old=_s846_old(con, cid, day))\n"
     "\n"
     "\n"
     "def _s846_old(con, cid, day):\n"
     "    \"\"\"S846 (the owner, 16-Nov-2026): the patient's earlier slips still not in Docterz -- [{day, kind}] (up to 3). [] on any fault.\"\"\"\n"
     "    try:\n"
     "        import not_in_docterz                             # noqa: PLC0415\n"
     "        return [dict(day=o[\"day\"], kind=o[\"kind\"]) for o in not_in_docterz.open_for_patient(con, cid, day)][:3]\n"
     "    except Exception:                                    # noqa: BLE001\n"
     "        return []\n"),
    ("  cb&&cb(r);});}\n",
     "  if(r.old&&r.old.length){var K={opd:'OPD',xray:'X-ray',proc:'procedure'},o=r.old[0],dd=o.day.slice(8,10)+'/'+o.day.slice(5,7);   /* S846 */\n"
     "   out.textContent+=' — '+(EN?'earlier slip ('+dd+' · '+(K[o.kind]||o.kind)+') is not in Docterz — enter this visit in Docterz today'\n"
     "    :'pichhli parchi ('+dd+' · '+(K[o.kind]||o.kind)+') Docterz mein nahi thi — aaj ki visit Docterz mein zaroor darj karein');out.className='name far';}\n"
     "  cb&&cb(r);});}\n"),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, out = argv[1], argv[2]
    built = {}
    for fn, edits in P.items():
        b = open(os.path.join(src, fn), "rb").read()
        if FROM.get(fn) and not md5(b).startswith(FROM[fn]):
            print("STOP: %s is %s, not the live %s -- read the newest bytes first" % (fn, md5(b)[:8], FROM[fn]))
            return 1
        t = b.decode("utf-8")
        for old, new in edits:
            n = t.count(old)
            if n != 1:
                print("STOP: %s: an anchor occurs %d times: %r" % (fn, n, old[:70]))
                return 1
            t = t.replace(old, new, 1)
        built[fn] = t.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    for fn, b in built.items():
        with open(os.path.join(out, fn), "wb") as fh:
            fh.write(b)
        print("%s %s -> %s" % (fn, FROM[fn], md5(b)[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

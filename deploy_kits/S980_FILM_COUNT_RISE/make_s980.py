#!/usr/bin/env python3
"""make_s980.py -- kit S980_FILM_COUNT_RISE (the parent, S545, 28-Nov-2026; his ask 18:15: the film log stuck since 09-Nov).
Remakes /root/finance/xray_film.py from its FROM bytes. Usage: make_s980.py FROM_DIR OUT_DIR. No patient name or number here."""
import hashlib, os, sys
FROM = {"xray_film.py": "5e3a2bd1a8fa63b5142c2c46a8fc5191"}


def rep(t, old, new):
    if t.count(old) != 1:
        sys.exit("REFUSED: anchor found %d times: %r" % (t.count(old), old[:80]))
    return t.replace(old, new, 1)


def make(t):
    t = rep(t, "     The count is to be taken before the first X-ray of the morning (the page says so).\n",
            "     The count is to be taken before the first X-ray of the morning (the page says so).\n"
            "     S980 (28-Nov-2026; his ask 18:15 -- no count saved since 09-Nov: the 8x10 box ran down to 21, a new box went in, and every\n"
            "     staff save since was refused because 21 is above load.max_left 20, with no way through). A rise is now a box load for\n"
            "     staff WITH the tick whatever the last count was -- unless the last count was above load.max_left AND the rise is\n"
            "     RISE_MIN films or fewer (a typo one film up still never becomes a box load). The tick is always offered once a count\n"
            "     exists. A rise saved by staff from a last count above load.max_left is told to him once (his phone, his devices only).\n")
    t = rep(t, 'BASE = "/finance/slips/film"\n',
            'BASE = "/finance/slips/film"\n'
            'RISE_MIN = 20                                                      # S980: a rise of this many films or fewer from above\n'
            '                                                                   # load.max_left is still a typo, never a box load\n')
    t = rep(t, "                if prev > lm:\n                    return None, \"risen\", k\n",
            "                if prev > lm and vals[k] <= prev + RISE_MIN and _s980_recent(con, k, day):   # S980: a small rise on\n"
            "                    return None, \"risen\", k                         # consecutive counts only\n")
    t = rep(t, "        if not own and (form.get(\"sure_%s\" % k) or \"\") != \"1\" and needs_sure(con, k, day, vals[k]):\n",
            "        if prev is not None and vals[k] <= prev and (form.get(\"newbox_%s\" % k) or \"\") == \"1\":   # S980 (review M2): a box\n"
            "            return None, \"boxlow\", k                                # the figures cannot show -- his correction form\n"
            "        if not own and (form.get(\"sure_%s\" % k) or \"\") != \"1\" and needs_sure(con, k, day, vals[k]):\n")
    t = rep(t, '                        "A figure higher than the last count means a new box: tick it (last count 20 or less) or type a note."),\n',
            '                        "A figure higher than the last count means a new box: tick it, or type a note."),\n'
            '           "boxlow": ("Naya box tick hai, par film pichhli ginti se kam hain. Naya box nahi laga to tick hata kar Save kijiye. "\n'
            '                      "Laga tha (ek se zyada box use hue) to bhi tick hata kar Save kijiye aur Dr Manoj ko batayein.",\n'
            '                      "A new box is ticked but the figure is not above the last count. If no new box went in, untick and Save. "\n'
            '                      "If one did (more than a box used since), untick, Save and add a note -- the films used will read a box short."),\n')
    t = rep(t, '        if msg == "sure":                                              # the typed figures (films left: 3 digits at most) come back\n',
            '        if msg in ("sure", "boxlow"):                                  # the typed figures (films left: 3 digits at most) come back\n')
    t = rep(t, '                keep += ("&nb_%s=1" % k) if request.form.get("newbox_" + k) == "1" else ""\n',
            '                keep += ("&nb_%s=1" % k) if (request.form.get("newbox_" + k) == "1" and msg != "boxlow") else ""   # S980: unticked\n')
    t = rep(t, '    pre = {k: (request.args.get("v_" + k) or "") for k in SIZE_KEYS} if mk_ == "sure" else {}\n',
            '    pre = {k: (request.args.get("v_" + k) or "") for k in SIZE_KEYS} if mk_ in ("sure", "boxlow") else {}   # S980\n')
    t = rep(t, '        if own or (prev and prev[-1]["left"] <= _num_setting(con, "load.max_left")):\n',
            '        if own or prev:                                                  # S980: the new-box tick is always offered\n')
    t = rep(t, '    _audit_safe(con, "xf_save", sid, "film_count", None, dict(day=today.isoformat(), left=vals, note=note), who)\n',
            '    _audit_safe(con, "xf_save", sid, "film_count", None, dict(day=today.isoformat(), left=vals, note=note), who)\n'
            '    if not own:                                                        # S980: a box load the old rule refused, told to him\n'
            '        _s980_tell(con, today.isoformat(), vals, who)\n')
    t = rep(t, "def _figures(con, own, day, form):\n",
            "def _s980_tell(con, day, vals, who):\n"
            "    \"\"\"S980: his phone, once per day, when staff saved a rise from a last count above load.max_left (a box load the old rule\n"
            "    refused). Never a reason for the save to fail.\"\"\"\n"
            "    try:\n"
            "        lm = _num_setting(con, \"load.max_left\")\n"
            "        bits = []\n"
            "        for k in SIZE_KEYS:\n"
            "            p = last_before(con, k, day)\n"
            "            if p is not None and p > lm and vals[k] > p:\n"
            "                bits.append(\"%s %d -> %d\" % (SIZE_LABEL[k], p, vals[k]))\n"
            "        if not bits:\n"
            "            return False\n"
            "        import day_check as _dc                                        # noqa: PLC0415 -- the one push road to his devices\n"
            "        s, _why = _dc._s962_push(con, (\"manoj\",), \"X-ray film: a new box marked by %s\" % str(who).title(),\n"
            "                                 \"; \".join(bits) + \" (the last count was above %d)\" % int(lm), BASE + \"/log\", \"film-rise-\" + day)\n"
            "        return bool(s)\n"
            "    except Exception:                                                  # noqa: BLE001\n"
            "        return False\n"
            "\n"
            "\n"
            "def _s980_recent(con, size, day):\n"
            "    \"\"\"S980 (review M1): True when the last count before `day` is CHECK_GAP_DAYS days old or less -- only then is a small rise a\n"
            "    typo; across a longer gap a real new box can show any figure.\"\"\"\n"
            "    prev = [r for r in readings(con, size, day) if r[\"day\"] < str(day)]\n"
            "    if not prev:\n"
            "        return False\n"
            "    try:\n"
            "        return (dt.date.fromisoformat(str(day)[:10]) - dt.date.fromisoformat(str(prev[-1][\"day\"])[:10])).days <= CHECK_GAP_DAYS\n"
            "    except ValueError:\n"
            "        return True\n"
            "\n"
            "\n"
            "def _figures(con, own, day, form):\n")
    t = rep(t, "                if not (note or (prev <= lm and tick)):\n",
            "                if not (note or (tick and (prev <= lm or vals[k] > prev + RISE_MIN or not _s980_recent(con, k, day)))):   # S980\n")
    t = rep(t, "    (never refused). The owner may save either: above 150 with a note; a higher figure with the tick (last count 20 or less) or\n    a note.\"\"\"\n",
            "    (never refused). The owner may save either: above 150 with a note; a higher figure with the tick (last count 20 or less) or\n    a note.\n"
            "    S980 SUPERSEDES the rise rule above: a higher figure with the tick is a box load whatever the last count; only a rise of\n"
            "    RISE_MIN or fewer from above load.max_left on counts CHECK_GAP_DAYS apart or less is refused; a ticked box whose figure is\n"
            "    not above the last count is refused ('boxlow': his correction form).\"\"\"\n")
    t = rep(t, "     the last count unless that count was 20 or less (setting load.max_left) and \"Haan, naya box lagaya gaya\" is ticked -- a\n",
            "     the last count unless that count was 20 or less (setting load.max_left) and \"Haan, naya box lagaya gaya\" is ticked [S980 below\n"
            "     replaces this rule] -- a\n")
    return t


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    for n, want in FROM.items():
        b = open(os.path.join(src, n), "rb").read()
        if hashlib.md5(b).hexdigest() != want:
            sys.exit("REFUSED: %s is %s, not %s" % (n, hashlib.md5(b).hexdigest()[:8], want[:8]))
        t2 = make(b.decode("utf-8"))
        open(os.path.join(dst, n), "w", encoding="utf-8", newline="\n").write(t2)
        print("MADE %s %s" % (n, hashlib.md5(t2.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()

"""make_s913.py -- kit S913_PROCROOM_NEXT_DAY (the parent building on the Scan App's file, S496, 21-Nov-2026). Anchored patches.
usage: python make_s913.py <dir with procroom.py at its FROM pin> <out dir>
  procroom.py 38c5bbaa -> TO : Kal ke procedures (Shavez's morning screen)
    * opened with no day, it opens the OLDEST day still waiting (was always yesterday, even when yesterday was done);
    * after a Save that leaves the day complete, it goes on to the next day still waiting and says so in the message
      ('... Ab 13-11 ke procedures bharein.'), or 'Sab din poore ho gaye.' when nothing waits -- before, the same day came back
      looking unchanged, which read as 'nothing happened'.
  The save itself (save_morning) is not touched.
"""
import hashlib, os, sys

FROM = {"procroom.py": "38c5bbaa79c8b05ac3394a412f74851d"}

P = {"procroom.py": [
("    db = AR.get_db()\n    v = morning_view(db, _day_arg(request.args.get(\"day\")))\n",
 "    db = AR.get_db()\n    v = morning_view(db, _day_arg(request.args.get(\"day\") or _s913_first_open(db)))   # S913: the oldest waiting day\n"),
("    try:\n        msg = save_morning(db, day, request.form)\n        db.commit()\n    except ValueError as e:\n"
 "        db.rollback()\n        msg = str(e) + \" Kuch save nahi hua.\"\n    flash(msg)\n"
 "    return redirect(url_for(\"s637_morning\", day=day))\n",
 "    go = day\n    try:\n        msg = save_morning(db, day, request.form)\n        db.commit()\n"
 "        go, tail = _s913_next(db, day)                    # S913: a finished day goes on to the next one still waiting\n"
 "        msg += tail\n    except ValueError as e:\n"
 "        db.rollback()\n        msg = str(e) + \" Kuch save nahi hua.\"\n    flash(msg)\n"
 "    return redirect(url_for(\"s637_morning\", day=go))\n\n\n"
 "def _s913_first_open(db):\n"
 "    \"\"\"S913: the oldest day Kal ke procedures still waits on, or None (then the screen opens yesterday, as before).\"\"\"\n"
 "    try:\n        od = open_days(db)\n    except Exception:                                            # noqa: BLE001\n        od = None\n"
 "    return od[0][\"day\"] if od else None\n\n\n"
 "def _s913_next(db, day):\n"
 "    \"\"\"S913: after a Save -- (the day to show, the words to add). The same day while it still has slips waiting; else the\n"
 "    oldest other day waiting; else the same day with 'Sab din poore'. An unreadable list keeps the same day and adds nothing.\"\"\"\n"
 "    try:\n        od = open_days(db)\n    except Exception:                                            # noqa: BLE001\n        od = None\n"
 "    if od is None:\n        return day, \"\"\n"
 "    if any(o[\"day\"] == day for o in od):\n        return day, \"\"\n"
 "    if od:\n        n = sum(o[\"n\"] for o in od)\n"
 "        return od[0][\"day\"], \" Yeh din poora. Ab %s ke procedures bharein (%d baaki).\" % (_dmy(od[0][\"day\"])[:5], n)\n"
 "    return day, \" Yeh din poora -- sab din poore ho gaye.\"\n"),
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

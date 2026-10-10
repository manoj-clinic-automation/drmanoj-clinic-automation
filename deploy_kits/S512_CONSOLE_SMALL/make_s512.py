"""make_s512.py -- S512_CONSOLE_SMALL. Builds owner_console.py from the live bytes by exact edits.
    python3 make_s512.py <live dir> <out dir>"""
import hashlib
import os
import sys

PIN = "4819eceb527e"


def rep(s, a, b, what):
    n = s.count(a)
    assert n == 1, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    b = open(os.path.join(live, "owner_console.py"), "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(PIN), "owner_console.py: FROM pin differs"
    s = b.decode("utf-8")
    s = rep(s, '''VERSION = "S487 1.1"''', '''VERSION = "S512 1.2"
# S512 (10-Oct-2026, the owner's list item 8 -- the console's small kit): F-779 the work section follows HIS PANEL -- each person's
# list exactly as they see it (his switches, his own lines, the green 'done' rows) and their tasks with the answers; F-774 the
# System line says how old the freshness reading is and never calls feeds fresh on a reading older than a day; F-795 the flag
# codes in words (pos_diff, mpr_missing, mpr_rejected).''', "version")
    s = rep(s, '''              "not_in_bank": "a Docterz online payment has not reached the bank"}''',
            '''              "not_in_bank": "a Docterz online payment has not reached the bank",
              "pos_diff": "the POS machine's UPI total differs from the bank's",                     # S512 (F-795)
              "mpr_missing": "the bank's daily statement (MPR) has not come",
              "mpr_rejected": "the bank's daily statement (MPR) could not be read"}''', "flag words")
    s = rep(s, '''        legs = [x for x in (f.get("legs") or []) if str(x.get("verdict") or "").upper() not in ("OK", "PARKED")]
        st["stale"] = len(legs)
        T.update(sys_word="%d of %d feeds fresh" % (int(c.get("ok") or 0), int(c.get("total") or 0)), sys_cls="w" if legs else "g")
        out = [L("w" if legs else "g", "%d of %d feeds fresh (read %s)" % (int(c.get("ok") or 0), int(c.get("total") or 0),
                                                                          when(f.get("generated_iso"), cx["today"])),
                 href="/finance/freshness", link="freshness")]''', '''        legs = [x for x in (f.get("legs") or []) if str(x.get("verdict") or "").upper() not in ("OK", "PARKED")]
        st["stale"] = len(legs)
        try:                                                           # S512 (F-774): a reading has an age
            gen = dt.datetime.fromisoformat(str(f.get("generated_iso") or "")[:19])
            hours = (cx["now"] - gen).total_seconds() / 3600.0
        except ValueError:
            hours = None
        if hours is None or hours > 26:
            st["stale"] = max(st["stale"], 1)
            T.update(sys_word="the freshness check has not run since %s" % when(f.get("generated_iso"), cx["today"]), sys_cls="w")
            return [L("w", "The freshness check last ran %s — its %d of %d is too old to call anything fresh" % (
                when(f.get("generated_iso"), cx["today"]), int(c.get("ok") or 0), int(c.get("total") or 0)), href="/finance/freshness", link="freshness")]
        T.update(sys_word="%d of %d feeds fresh" % (int(c.get("ok") or 0), int(c.get("total") or 0)), sys_cls="w" if legs else "g")
        out = [L("w" if legs else "g", "%d of %d feeds fresh (as of %s, %d hour%s ago)" % (int(c.get("ok") or 0), int(c.get("total") or 0),
                                                                                      when(f.get("generated_iso"), cx["today"]), int(hours),
                                                                                      "" if int(hours) == 1 else "s"),
                 href="/finance/freshness", link="freshness")]''', "freshness age")
    s = rep(s, '''            cx["aaj"] = aaj_kaam.build_all(copy, now)''', '''            cx["aaj"] = aaj_kaam.build_all(copy, now)
            try:                                                       # S512 (F-779): the lists as his panel cuts them
                cx["panel"] = read_panel(aaj_kaam, copy, now)
            except Exception as e:                                     # noqa: BLE001 -- 1.1's reading stands in
                cx["panel"], cx["panel_err"] = None, "%s: %s" % (type(e).__name__, str(e)[:100])''', "build panel")
    s = rep(s, '''def sec_work(con, cx):''', '''def read_panel(K, copy, now):
    """S512 (F-779): every person on his panel, their list as they see it (person_list in the owner's view) and their tasks."""
    rd = K.Reader(copy, now)
    try:
        out = []
        for key, doc in rd.people.items():
            if key == "manoj":
                continue
            lst = K.person_list(rd, doc, True)
            en = {ln["id"]: (ln.get("en") or ln.get("hi") or ln["id"]) for ln in doc["lines"]}
            rows = [dict(r, en=en.get(r["id"], r.get("text") or r["id"])) for sec in lst["sections"].values() for r in sec]
            out.append(dict(key=key, name=doc.get("name") or key, on=bool(doc.get("on")), list_on=bool(rd.on), rows=rows,
                            unread=lst.get("unread", 0), tasks=K.tasks_of_person(rd, key),
                            as_login=((K.SEED.VIEW_AS.get(key) if getattr(K, "SEED", None) is not None else None) or key)))
        return out
    finally:
        rd.close()


def _work_people_panel(lines, cx):
    """S512 (F-779): list by list, as his panel cuts them -- the open lines in his English, what waits to be tapped, what
    was tapped and by whom, the green 'done' rows, and each person's tasks with their answers."""
    open_n, today = 0, cx["today"]
    for p in cx["panel"]:
        if not p["on"] or not p["list_on"]:
            lines.append(L("n", "%s: the list is switched off" % p["name"], href="/finance/aaj?as=%s" % p["as_login"], link="the list"))
            continue
        job = [r for r in p["rows"] if r["kind"] == "job"]
        topen = [r for r in p["rows"] if r["kind"] == "tick" and not r.get("done") and not r.get("later")]
        tdone = [r for r in p["rows"] if r["kind"] == "tick" and r.get("done")]
        green = [r for r in p["rows"] if r["kind"] == "done"]
        fetch = [r for r in p["rows"] if r["kind"] == "fetch"]
        tasks = p["tasks"]
        t_open = [t for t in tasks if t["state"] == "open"]
        t_ans = [t for t in tasks if t["state"] in ("done", "cant")]
        n = len(job) + len(topen) + len(t_open)
        open_n += n
        lines.append(L("w" if n else "g", "", b=p["name"], who=("%d open" % n if n else "nothing open") + (" · %d task%s answered" % (len(t_ans), "" if len(t_ans) == 1 else "s") if t_ans else ""),
                       href="/finance/aaj?as=%s" % p["as_login"], link="%s's list" % p["name"]))
        for r in job:
            lines.append(L("w", r["en"], href=r.get("door"), link=r.get("tile") or "open", sub=True))
        for r in topen:
            lines.append(L("w", "To be tapped: %s" % r["en"], sub=True))
        for r in fetch:
            lines.append(L("n", "Shown only when something waits behind its page: %s" % r["en"], sub=True))
        for r in tdone:
            d = r["done"]
            lines.append(L("g", "Tapped done: %s — %s %s" % (r["en"], d.get("by_name") or d.get("by") or "?", when(d.get("at"), today)), sub=True))
        for r in green:
            lines.append(L("g", "Done: %s" % r["en"], sub=True))
        for t in t_open:
            lines.append(L("w", "Task: %s — given by %s %s" % (t["text"], t.get("by_name") or t.get("by_whom"), when(t.get("at"), today)), sub=True))
        for t in t_ans:
            last = (t.get("notes") or [{}])[-1]
            lines.append(L("g" if t["state"] == "done" else "b", "Task %s: %s — %s %s%s" % (
                "done" if t["state"] == "done" else "could not be done", t["text"], last.get("by_name") or t.get("state_by") or "?",
                when(t.get("state_at"), today), (": " + last["note"]) if last.get("note") else ""), href="/finance/aaj", link="close it", sub=True))
        if p.get("unread"):
            lines.append(L("n", "%d of %s's lines could not be read just now." % (p["unread"], p["name"]), sub=True))
    return 0, open_n


def sec_work(con, cx):''', "panel functions")
    s = rep(s, '''    late_n, open_n = _work_people_aaj(lines, cx, aaj) if aaj else _work_people_map(lines, cx)''',
            '''    late_n, open_n = (_work_people_panel(lines, cx) if cx.get("panel") else                      # S512 (F-779)
                      _work_people_aaj(lines, cx, aaj) if aaj else _work_people_map(lines, cx))''', "sec_work")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "owner_console.py"), "wb") as fh:
        fh.write(s.encode("utf-8"))
    print("built owner_console.py %s" % hashlib.md5(s.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])

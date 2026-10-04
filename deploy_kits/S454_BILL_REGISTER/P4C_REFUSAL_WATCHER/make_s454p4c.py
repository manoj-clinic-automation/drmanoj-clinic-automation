#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""make_s454p4c.py -- kit S454_BILL_REGISTER, part 4 -- the medical PC, corrected (S454 section 20; P4B is not delivered).
CLAUDE.md rule 2: built from P4B's own bytes (marg_watch.py 20ec1602, in the kit's P4B_REFUSAL_WATCHER folder), every anchor exactly once.

  marg_watch.py (S454 P4C)
    20.1  * a note is DONE only when the server has answered for it: that fact is a marker <stem>.note beside the kept text
          * a note that could not be sent (a dead line, the off switch, no key, 401/403/404) WAITS -- no marker -- and is tried again at
            every start (after the retry of the refused texts) and at every census; one attempt at a time for a text
          * what ends a note: sent (2xx) . refused by the server (400, 413) . taken later (the reader took the text at a start) .
            overtaken (a text of the same kind was taken after it) . expired (older than CENSUS_DAYS, logged)
          * the first start on a PC marks every text already in refused as kept before S454 and announces none of them
            (sentinel _captured_txt\S454_NOTES_STARTED.flag, written before the first sweep, even when refused is empty)
          * the marker is copied to Drive's FromMedical\refused_text beside the text and its reason (share_refused: 18 files, six texts)
    20.2  * the note never carries a line of the file: "(it begins: ...)" is cut, and a reader's refusal is told as
            "the reader refused it (line N)" / "the reader refused it"; the .why.txt and the PC's log keep every reason whole

    make_s454p4c.py --watch <marg_watch.py of P4B> --out DIR
"""
import argparse
import hashlib
import os

FROM = "20ec1602174cea5e2726d87797fa8e88"

# (old, new): old occurs exactly once.   (start, end, new): both occur exactly once, start before end; the span start..end is replaced.
EDITS = [
    # ---- the head: what P4C is
    (r'''OFF SWITCH (S259)
    D:\\SendToClinic\\_off\\MARG_WATCH_OFF.txt stops capture.''',
     r'''S454 P4C (04-Oct-2026, the brief's section 20): a note is DONE only when the server has answered for it, and that fact is a marker
    <stem>.note beside the kept text. A note that could not be sent -- a dead line, the off switch, no key, a key the server does not
    know -- WAITS, and is tried again at every start and at every census, until it is sent, the server refuses it (400, 413), the reader
    takes the text after all, a text of the same kind is taken after it, or it is older than CENSUS_DAYS. The first start on a PC marks
    what is already in refused as kept before S454 and announces none of it (sentinel _captured_txt\\S454_NOTES_STARTED.flag).
    The note never quotes the file: "(it begins: ...)" is cut and a reader's refusal leaves as "the reader refused it (line N)".

OFF SWITCH (S259)
    D:\\SendToClinic\\_off\\MARG_WATCH_OFF.txt stops capture.'''),
    # ---- the moment a text is kept: its note is tried; if it cannot go, it waits
    (r'''        send_note(note_of(path, tmd5, raw, why), out)          # S454: the owner is told (once: a file kept once returns above)
''',
     r'''        notes_try(spool, out, only=stem)                       # S454 P4C: the owner is told; a note that cannot go WAITS (no marker)
'''),
    # ---- the note, its marker, the waiting notes
    (r'''def note_of(path, tmd5, raw, why):''',
     r'''        out("  note: %s -- the refusal of %s stays on this PC" % (ex.__class__.__name__, note.get("name")))
''',
     r'''NOTE_SENTINEL = "S454_NOTES_STARTED.flag"  # in _captured_txt, outside refused: this PC's watcher has started with notes once
NOTE_FINAL = (400, 413)                    # the server's answers a retry cannot change; every other failure WAITS
NOTE_TRYING = set()                        # stems whose note is being tried now -- one attempt at a time for a text
NOTE_LOCK = threading.Lock()
NOTE_SAID = {"last": None}                 # (why, how many) last written to the log about waiting notes


def _ref_dir(spool):
    return os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")


def _note_reason(why):
    """What of a reason may leave the PC -- never a line of the file (S454 20.2). The .why.txt and the log keep the reason whole."""
    w = " ".join(str(why or "").split())
    if w.startswith("the reader refused it"):
        m = re.match(r"the reader refused it: line (\d+)\b", w)
        w = ("the reader refused it (line %s)" % m.group(1)) if m else "the reader refused it"
    elif " (it begins:" in w:
        w = w[:w.index(" (it begins:")]
    return re.sub(r"\d{6,}", "#", w)[:240]


def note_of(path, tmd5, raw, why):
    """The note: name, md5, kind, reason -- nothing of the file's content (_note_reason); a run of 6+ digits in the reason is masked."""
    name = re.split(r"[\\/]", str(path))[-1][:120]
    return {"name": name, "md5": tmd5, "kind": _kind_of(raw), "reason": _note_reason(why)}


def _note_mark(ref, stem, what, out=None):
    """The marker <stem>.note: this text's note is finished, and how. Never a .txt, so the reader is never offered it."""
    try:
        with open(os.path.join(ref, stem + ".note"), "w", encoding="utf-8") as fh:
            fh.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), what))
        return True
    except OSError as ex:
        if out:
            out("  note: the marker of %s could not be written (%s)" % (stem, ex))
        return False


def notes_waiting(spool):
    """The kept texts of refused with no marker, as stems (the name its .txt, .why.txt and .note share)."""
    ref = _ref_dir(spool)
    try:
        names = os.listdir(ref)
    except OSError:
        return []
    have = set(names)
    return sorted(n[:-4] for n in names
                  if n.lower().endswith(".txt") and not n.lower().endswith(".why.txt") and (n[:-4] + ".note") not in have)


def notes_first_start(spool, out):
    """Once on a PC, before the first sweep: what is already in refused was kept before S454 -- marked, never announced."""
    try:
        keep = os.path.dirname(_ref_dir(spool))
        flag = os.path.join(keep, NOTE_SENTINEL)
        if os.path.exists(flag):
            return None
        os.makedirs(keep, exist_ok=True)
        ref, n = _ref_dir(spool), 0
        for stem in notes_waiting(spool):
            if _note_mark(ref, stem, "kept before S454 -- no note sent", out):
                n += 1
        if notes_waiting(spool):
            out("  notes: an old refused text could not be marked -- the sentinel is not written, and no waiting note is sent until it is")
            return None
        with open(flag, "w", encoding="utf-8") as fh:
            fh.write("%s  marg_watch S454 P4C started here with refusal notes; %d kept before it, none announced\n"
                     % (time.strftime("%Y-%m-%d %H:%M:%S"), n))
        out("  notes: the first start with refusal notes on this PC -- %d text(s) already in refused marked as kept before S454, "
            "none announced; sentinel %s written" % (n, NOTE_SENTINEL))
        return n
    except Exception as ex:                                     # noqa: BLE001 -- capture never fails for a note
        out("  notes: the first-start sentinel could not be written (%s) -- no waiting note is sent until it is" % ex)
        return None


def _taken_after(spool, kind, when):
    """Was a text of this kind TAKEN (its copy is kept in _captured_txt) after WHEN? Then the staff have exported again."""
    keep = os.path.dirname(_ref_dir(spool))
    try:
        names = os.listdir(keep)
    except OSError:
        return False
    for n in names:
        if not n.lower().endswith(".txt"):
            continue
        p = os.path.join(keep, n)
        try:
            if not os.path.isfile(p) or os.path.getmtime(p) <= when:
                continue
            with open(p, "rb") as fh:
                if _kind_of(fh.read(4000)) == kind:
                    return True
        except OSError:
            continue
    return False


def _why_read(ref, stem):
    """(the file's own name, the whole reason) from the .why.txt kept beside a refused text."""
    parts = stem.split("__")
    name = ("__".join(parts[1:-1]) if len(parts) >= 3 else stem) + ".txt"
    why = ""
    try:
        with open(os.path.join(ref, stem + ".why.txt"), encoding="utf-8", errors="replace") as fh:
            t = fh.read()
    except OSError:
        t = ""
    m = re.search(r"^from: (.+)$", t, re.M)
    if m and m.group(1).strip():
        name = re.split(r"[\\/]", m.group(1).strip())[-1] or name
    m = re.search(r"^why:\s*(.*)", t, re.M | re.S)
    if m:
        why = m.group(1).strip()
    return name, (why or "kept as refused (its reason was not kept)")


def _send_note(note, out):
    """ONE attempt (NOTE_TRIES tries, NOTE_GAP_S apart). Answers ("sent", status), ("refused", "HTTP n") or ("wait", why)."""
    try:
        import marg_push as MP
    except Exception as ex:                                     # noqa: BLE001
        return "wait", "marg_push.py is not here (%s)" % ex.__class__.__name__
    try:
        off = MP.off_marker()
        if off:
            return "wait", "sending is OFF (%s)" % os.path.basename(off)
        tok = MP.token()
        if not tok:
            return "wait", "no key in token.txt"
        body = json.dumps(note).encode("utf-8")
        last = "the server could not be reached"
        for i in range(NOTE_TRIES):
            req = urllib.request.Request(MP.URL, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Finance-Marg", tok)
            req.add_header("X-Marg-Note", "refused")
            try:
                with urllib.request.urlopen(req, timeout=30, context=MP._ctx()) as r:
                    txt = r.read().decode("utf-8", "replace")
                try:
                    js = json.loads(txt or "{}")
                except ValueError:
                    js = None
                if isinstance(js, dict):
                    return "sent", str(js.get("status"))
                last = "the answer was not the server's own (not JSON)"
            except urllib.error.HTTPError as e:
                if e.code in NOTE_FINAL:
                    return "refused", "HTTP %s" % e.code
                last = "the server answered HTTP %s" % e.code
                if e.code in (401, 403, 404):
                    break                                       # a minute cannot change these; the next start or census asks again
            except Exception:                                   # noqa: BLE001 -- a dead line: try again shortly
                last = "the server could not be reached"
            if i + 1 < NOTE_TRIES:
                time.sleep(NOTE_GAP_S)
        return "wait", last
    except Exception as ex:                                     # noqa: BLE001
        return "wait", ex.__class__.__name__


def _note_one(spool, ref, stem, out, send=True):
    """One waiting note. None when it is finished (marked) or cannot be judged; else the reason it still waits."""
    p = os.path.join(ref, stem + ".txt")
    try:
        kept = os.path.getmtime(p)
        with open(p, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if time.time() - kept > CENSUS_DAYS * 86400:
        _note_mark(ref, stem, "expired -- older than %d days and never sent" % CENSUS_DAYS, out)
        out("  note: EXPIRED, never sent -- the refusal of %s is older than %d days" % (stem, CENSUS_DAYS))
        return None
    kind = _kind_of(raw)
    if kind and _taken_after(spool, kind, kept):
        _note_mark(ref, stem, "overtaken -- a %s text was taken after it; no note sent" % kind, out)
        out("  note: not sent -- a %s text was taken after %s was kept (overtaken)" % (kind, stem))
        return None
    if not send:
        return "not tried in this pass"
    name, why = _why_read(ref, stem)
    note = note_of(name, hashlib.md5(raw).hexdigest(), raw, why)
    if NOTE_SINK is not None:
        NOTE_SINK.append(dict(note))
        _note_mark(ref, stem, "sent -- collected by the selftest, nothing left the PC")
        return None
    what, how = _send_note(note, out)
    if what == "sent":
        _note_mark(ref, stem, "sent -- the server answered %s" % how, out)
        out("  note: the server has the refusal of %s (%s)" % (note["name"], how))
        return None
    if what == "refused":
        _note_mark(ref, stem, "refused by the server (%s) -- not tried again" % how, out)
        out("  note: the server would not take the refusal of %s (%s) -- not tried again" % (note["name"], how))
        return None
    return how


def _notes_run(spool, stems, out):
    ref = _ref_dir(spool)
    stop = None                                                 # the line, the switch or the key said: not now
    for stem in stems:
        try:
            why = _note_one(spool, ref, stem, out, send=stop is None)
            if why and stop is None:
                stop = why
        except Exception as ex:                                 # noqa: BLE001 -- capture never fails for a note
            out("  note: %s -- the note of %s waits" % (ex.__class__.__name__, stem))
        finally:
            with NOTE_LOCK:
                NOTE_TRYING.discard(stem)
    said = (stop, len(notes_waiting(spool))) if stop else None
    if said and said != NOTE_SAID.get("last"):                  # said once, not at every census: the log's tail is read on Drive
        out("  note: %s -- %d note(s) wait on this PC; tried again at the next start and at every census" % said)
    NOTE_SAID["last"] = said


def notes_try(spool, out, only=None):
    """Try the waiting notes -- every kept text with no marker, or ONLY the one just kept. One attempt at a time for a text."""
    try:
        ref = _ref_dir(spool)
        if only is None and NOTE_SINK is None and not os.path.exists(os.path.join(os.path.dirname(ref), NOTE_SENTINEL)):
            return 0                                            # the past is not marked yet: nothing old is announced
        todo = []
        with NOTE_LOCK:
            for stem in ([only] if only else notes_waiting(spool)):
                if stem not in NOTE_TRYING and not os.path.exists(os.path.join(ref, stem + ".note")):
                    NOTE_TRYING.add(stem)
                    todo.append(stem)
        if not todo:
            return 0
        if NOTE_SINK is not None:
            _notes_run(spool, todo, out)
            return len(todo)
        try:
            threading.Thread(target=_notes_run, args=(spool, todo, out), daemon=True, name="refusal_note").start()
        except Exception as ex:                                 # noqa: BLE001
            with NOTE_LOCK:
                NOTE_TRYING.difference_update(todo)
            out("  note: could not start (%s) -- %d note(s) wait" % (ex.__class__.__name__, len(todo)))
            return 0
        return len(todo)
    except Exception as ex:                                     # noqa: BLE001 -- capture never fails for a note
        out("  note: %s -- the notes wait" % ex.__class__.__name__)
        return 0
'''),
    # ---- Drive's copy of refused carries the marker too (the text, its reason, its marker: six texts)
    (r'''    text and its reason), only the last CENSUS_DAYS, at most 12 files; a copy of the same size is
    not written again."""''',
     r'''    text and its reason), only the last CENSUS_DAYS, at most 18 files; a copy of the same size is
    not written again. S454 P4C: a text's note marker (<stem>.note) is copied with it, so the list on Drive
    still agrees with refused and shows which notes are done -- hence 18 files for the same six texts."""'''),
    (r'''    for name in sorted(os.listdir(src), reverse=True)[:12]:''',
     r'''    for name in sorted(os.listdir(src), reverse=True)[:18]:'''),
    # ---- a text the reader takes at the start's retry is not a refusal any more
    (r'''        if capture_text(p, spool, captured, out):
            took += 1
            out("  + a text refused earlier is taken now: %s" % name)
    return took''',
     r'''        got = capture_text(p, spool, captured, out)
        if got:
            took += 1
            out("  + a text refused earlier is taken now: %s" % name)
        if got or str(TXT_VERDICT.get(p, (0, ""))[1]).startswith(("TAKEN", "already taken", "HELD")):
            stem = name[:-4]                                    # S454 P4C: not a refusal any more -- no note for it
            if not os.path.exists(os.path.join(src, stem + ".note")):
                _note_mark(src, stem, "taken later -- the reader took it at a start; no note sent", out)
    return took'''),
    # ---- the start: the past is marked before the first sweep; the waiting notes go after the retry
    (r'''    new = 0 if watch_off() else sweep()  # always start from a known state
    if not watch_off():
        new += retry_refused(spool, captured, out)      # S397
''',
     r'''    notes_first_start(spool, out)       # S454 P4C: before the first sweep -- what is already in refused is never announced
    new = 0 if watch_off() else sweep()  # always start from a known state
    if not watch_off():
        new += retry_refused(spool, captured, out)      # S397
    notes_try(spool, out)               # S454 P4C: every waiting note, at every start, after the retry
'''),
    # ---- every census
    (r'''        if time.time() - last_census >= CENSUS_EVERY_S:           # S396
            publish_diagnostics(roots, out, spool)
''',
     r'''        if time.time() - last_census >= CENSUS_EVERY_S:           # S396
            notes_try(spool, out)                                 # S454 P4C: every waiting note, at every census
            publish_diagnostics(roots, out, spool)
'''),
    # ---- the selftest: three more checks; every check of P4B's stays as it is
    (r'''        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))''',
     r'''        # S454 P4C: the marker, the reasons that may leave the PC, a text taken later
        ck("P4C: every note that left has its marker beside the kept text (<stem>.note) and nothing waits",
           any(f == "%s.note" % os.path.splitext(w)[0][:-4] for w in whys for f in os.listdir(refd)) and notes_waiting(sp2) == [])
        ck("P4C: the reason that leaves the PC never quotes the file ('(it begins: ...)' cut; a reader's refusal is '(line N)' only)",
           _note_reason("not a bill-wise sales statement (it begins: 'SOME SHOP NAME')") == "not a bill-wise sales statement"
           and _note_reason("the reader refused it: line 52: a line of a kind this reader does not know: '4 *** AN ITEM 1*1'")
           == "the reader refused it (line 52)"
           and _note_reason("the reader refused it: no GRAND TOTAL line") == "the reader refused it")
        ck("P4C: a text the reader takes at a start is marked 'taken later' and sends no note",
           os.path.exists(old[:-4] + ".note") and "taken later" in open(old[:-4] + ".note", encoding="utf-8").read()
           and not any(n["md5"] == hashlib.md5(STK).hexdigest() for n in NOTE_SINK))
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))'''),
    # ---- the start line says which watcher this is
    (r'''    out("marg_watch S454 starting -- text reader %s, text route %s, refusal notes on" % (_mt, "LIVE" if txt_live() else "ON HOLD"))''',
     r'''    out("marg_watch S454 P4C starting -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again)"
        % (_mt, "LIVE" if txt_live() else "ON HOLD"))'''),
]


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = open(a.watch, "rb").read()
    if md5b(raw) != FROM:
        raise SystemExit("STOP: the watcher is %s, not its FROM pin %s -- nothing built" % (md5b(raw), FROM))
    txt = raw.decode("utf-8")
    for ed in EDITS:
        for anchor in ed[:-1]:
            c = txt.count(anchor)
            if c != 1:
                raise SystemExit("STOP: an anchor occurs %d times -- nothing built: %r" % (c, anchor[:90]))
        if len(ed) == 2:
            txt = txt.replace(ed[0], ed[1], 1)
        else:
            i, j = txt.index(ed[0]), txt.index(ed[1]) + len(ed[1])
            if i >= j:
                raise SystemExit("STOP: a span's end is before its start -- nothing built: %r" % ed[0][:90])
            txt = txt[:i] + ed[2] + txt[j:]
    os.makedirs(a.out, exist_ok=True)
    out = txt.encode("utf-8")
    with open(os.path.join(a.out, "marg_watch.py"), "wb") as fh:
        fh.write(out)
    print("built marg_watch.py %s -> %s  (%d edits)" % (FROM[:8], md5b(out), len(EDITS)))


if __name__ == "__main__":
    main()

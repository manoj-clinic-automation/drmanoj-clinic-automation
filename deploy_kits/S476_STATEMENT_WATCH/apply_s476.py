#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s476.py -- S476_STATEMENT_WATCH (session 294, 04-Oct-2026; F-723, F-725, F-243). Exact-anchor edits on four files,
built from their real bytes: the 04-Oct 01:35 bundle with S471 ... S475's own applies on top (each reproduces its S293 pin)
-- packs.py 6099b525 · packs.html 1349b37b · finance_app.py 56eb421b · clinic_state_backup.py 3bf7caea.
Every anchor must be found exactly once; all four files are verified before any is written.

WHAT.
 1. THE STATEMENT ROAD IS WATCHED BY WHAT IT PRODUCES (F-723). The relay that files the banks' statements into Drive runs under
    the owner's personal Google authorisation; on 1-Oct-2026 that lapsed, its failure mail reached his personal inbox only, and
    the shelf simply saw nothing. packs.statement_road(): from the 3rd of a month, AMBER while no bank statement has reached
    the shelf this month and last month's cells are still empty or partial -- it stays amber until one arrives; from the 3rd to
    the 10th a grey note when some came and then none for three days while a cell is still empty; quiet otherwise. The packs
    page prints it above the summary card; /finance/health carries it as one row
    ('Bank statements reaching Drive') through one guarded call in finance_app's _health_state, beside the Reception PC row.
 2. ONE DOOR, THE OWNER'S ONLY (F-725): GET /finance/packs/api/text/<id> answers the text the readers see of one shelf file --
    pdftotext -layout of the unlocked copy when the shelf opened it. A third Yes Bank layout (the bank's monthly e-mailed
    statement) is known to neither reader; its reader is built from that text, never from a file name. Read-only; no-store.
 3. THE ENCRYPTED NIGHTLY TAKES THREE MORE THINGS (clinic_state_backup.py): /root/portal/clinic_users.json as a file (F-243,
    open since S209: every login, in no backup at all); the hand-over photos of S472 and the spine's order snapshots (the
    Sanjeevni chat's word at its S285 close) as TREES -- one source each, so a pruned file never refuses the night.
NOT TOUCHED: the readers, stmt_shelf.py, the tables' shape, the checklist page, every other health row, the backup's walk,
tar, key and slot files.
   usage: apply_s476.py <packs.py> <packs.html> <finance_app.py> <clinic_state_backup.py>
"""
import hashlib
import sys

FROM = {"packs.py": "6099b5255374fc0bd0d27555cc009054", "packs.html": "1349b37b2a952ee4566376a577541e31",
        "finance_app.py": "56eb421b8d57a846e969b362e25b2c94", "clinic_state_backup.py": "3bf7caea3828c4e2a58227e161feec36"}

# ------------------------------------------------------------------------------------------------------------ packs.py
PACKS_DOC = '''
S476 (F-723, F-725, 04-Oct-2026): the statement road is WATCHED BY WHAT IT PRODUCES. The relay that files the banks' statements into
Drive runs under the owner's personal Google authorisation; when that lapsed (1-Oct-2026) its failure mail reached his personal inbox
only and nothing here knew. statement_road(): from the 3rd of a month, amber while NO bank statement has reached the shelf this month
and last month's cells are still empty or partial (it stays amber until one arrives); from the 3rd to the 10th a grey note when some
came and then none for three days while a cell is still empty; quiet otherwise (settings packs.road_from_day / packs.road_to_day /
packs.road_quiet_days). The packs page prints the line above the summary card and
/finance/health carries it as 'Bank statements reaching Drive' (statement_road_row -- one guarded call from finance_app). And one
door, the owner's only: /finance/packs/api/text/<id> answers the text the readers see of one shelf file (pdftotext -layout of the
unlocked copy when the shelf opened it) -- a statement is read in its own bytes before its reader is judged (F-720). Nothing stored.
'''

PACKS_SETTINGS = '''    "packs.road_from_day": ("3", "S476 F-723 -- the statement road is judged from this day of the month (amber while nothing has come this month)"),
    "packs.road_to_day": ("10", "S476 F-723 -- the grey 'quiet for N days' note is said from road_from_day to this day only"),
    "packs.road_quiet_days": ("3", "S476 F-723 -- inside that window, this many days without a new bank file is said out loud (a grey note)"),
'''

PACKS_ROAD = '''# ---------------------------------------------------------------- S476 (F-723): the statement road, watched by what it produces
def _int_setting(con, key):
    try:
        return int(str(_setting(con, key, SETTINGS[key][0]) or SETTINGS[key][0]).strip())
    except (TypeError, ValueError):
        return int(SETTINGS[key][0])


def statement_road(con, today=None):
    """S476 (F-723): is the relay still filing the banks' statements into Drive? It runs under the owner's personal Google
    authorisation and its failure mail reaches his personal inbox only, so this looks at what it PRODUCES: the newest bank file the
    shelf fetched. Returns dict(state, text, hint, last, this_month, missing, waiting, month). 'warn' from road_from_day of a month
    on, while no bank statement has reached the shelf this month and last month's cells are still empty or partial (it stays
    until one arrives); 'info' from road_from_day to road_to_day when some came and then none for road_quiet_days while a cell is
    still empty; 'ok' otherwise. A partial cell alone is never a grey note: a cycle statement's second half is due after the 10th.
    Never raises."""
    try:
        ensure(con)
        t = today or _today()
        d_from, d_to, quiet = _int_setting(con, "packs.road_from_day"), _int_setting(con, "packs.road_to_day"), _int_setting(con, "packs.road_quiet_days")
        r = con.execute("SELECT MAX(fetched_at), SUM(CASE WHEN fetched_at>=? THEN 1 ELSE 0 END) FROM stmt_file WHERE folder='bank'",
                        (t.replace(day=1).isoformat(),)).fetchone()
        last, n_month = str(r[0] or "")[:10], int(r[1] or 0)
        quiet = max(1, quiet)
        m = _prev_month(t.strftime("%Y-%m"))
        bank_cells = [c for c in cells(con, m) if c["kind"] != "card"]
        empty = [c["label"].split(" (")[0] for c in bank_cells if c["state"] == "empty"]
        waiting = [c for c in bank_cells if c["state"] in ("empty", "partial")]
        out = dict(state="ok", text="", hint="", last=last, this_month=n_month, missing=len(empty), waiting=len(waiting), month=m)
        if not last:
            out.update(state="info", text="No bank statement has reached the shelf yet.")
            return out
        age = (t - dt.date.fromisoformat(last)).days
        when = "%s (%s)" % (_dmy(last), "today" if age <= 0 else ("yesterday" if age == 1 else "%d days ago" % age))
        in_window = d_from <= t.day <= d_to
        if t.day >= d_from and waiting and n_month == 0:
            out.update(state="warn",
                       text="No bank statement has reached Drive this month -- the last one came on %s; %d of %s's statements are still awaited."
                            % (when, len(waiting), _month_name(m)),
                       hint="By now the banks have mailed them. If they are sitting in your personal inbox, the relay's Google "
                            "authorisation has lapsed: open the Janitor script, run it once and allow it. The shelf picks the "
                            "files up at its next fetch (05:40 and 07:30).")
        elif in_window and empty and age >= quiet:
            out.update(state="info",
                       text="No bank statement has reached Drive for %d days (the last on %s); %d of %s's statements are still missing: %s."
                            % (age, _dmy(last), len(empty), _month_name(m), ", ".join(empty[:4]) + (" ..." if len(empty) > 4 else "")),
                       hint="Usual while a bank's own copy is late or a statement password is not set. If the statements are "
                            "sitting in your personal inbox, the relay needs allowing again.")
        else:
            out.update(text="The last bank statement reached the shelf on %s -- %d this month." % (when, n_month))
        return out
    except Exception as ex:                              # noqa: BLE001
        return dict(state="info", text="the statement road could not be read (%s)" % str(ex)[:120], hint="", last="", this_month=0,
                    missing=0, waiting=0, month="")


def statement_road_row(add, con):
    """S476 (F-723): one row on /finance/health, called by finance_app's _health_state. Never raises."""
    r = statement_road(con)
    add("stmtroad", "Bank statements reaching Drive", r["state"], r["text"], r.get("hint") or "")


'''

PACKS_TEXT_DOOR = '''@bp.route("/finance/packs/api/text/<int:fid>")
def api_text(fid):
    """S476 (F-725): the text the readers see of one shelf file -- pdftotext -layout of the unlocked copy when the shelf opened
    it, else of the file as fetched -- to the owner only. A statement is read in its own bytes before its reader is judged
    (F-720). Read-only: nothing is stored, and the answer is never cached."""
    u, err = _owner()
    if err:
        return err
    r = _db().execute("SELECT id, name, folder, local_path, unlocked_path, locked, read_status, period_from, period_to FROM stmt_file WHERE id=?",
                      (fid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_on_shelf"), 404
    lp = r[4] or r[3] or ""
    text, still_locked = _file_text(lp)
    resp = jsonify(ok=True, id=r[0], name=r[1], folder=r[2], source=("the unlocked copy" if r[4] else "the file as fetched"),
                   on_disk=bool(lp and os.path.exists(lp)), locked=bool(r[5]), still_locked=bool(still_locked), read_status=r[6],
                   period_from=r[7], period_to=r[8], chars=len(text), lines=text.count("\\n"), text=text)
    resp.headers["Cache-Control"] = "no-store"
    return resp


'''

A_DOC = '"""\nimport datetime as dt\nimport glob\n'
A_SET = '    "packs.digest_drop_words": ("OTP,SECURE LINK,'
A_ROUTES = "# " + "-" * 64 + " routes\ndef _owner():\n"
A_STATE = '                   inbox_dir=INBOX, today=_today().isoformat(), secrets=secret_state(con))\n'
A_PREVIEW = '@bp.route("/finance/packs/preview/<key>")\ndef page_preview(key):\n'
PACKS_EDITS = [
    (A_DOC, PACKS_DOC + A_DOC),
    (A_SET, PACKS_SETTINGS + A_SET),
    (A_ROUTES, PACKS_ROAD + A_ROUTES),
    (A_STATE, '                   inbox_dir=INBOX, today=_today().isoformat(), secrets=secret_state(con), road=statement_road(con))   # S476\n'),
    (A_PREVIEW, PACKS_TEXT_DOOR + A_PREVIEW),
]

# ---------------------------------------------------------------------------------------------------------- packs.html
H_HEAD = '<html lang="en"><head>'
H_FLASH = '<div id="flash"></div>\n'
H_LOAD = '    S=j; $("mn").textContent=j.month_name;\n'
H_TAIL = 'remember();\nload();\n</script>'
HTML_ROAD_FN = '''/* S476 (F-723): the statement road -- amber when no bank statement has reached the shelf this month, a grey note when it is quiet */
function roadLine(r){var e=$("road"); if(!e)return; if(!r||!r.text||r.state==="ok"){e.innerHTML="";return}
  var w=(r.state==="warn"); e.innerHTML='<div class="top" style="border-left-color:'+(w?"#8a6100":"#8a8f98")+'"><span class="'+(w?"warn":"mut")+'">'+esc(r.text)+'</span>'+(r.hint?'<div class="mut">'+esc(r.hint)+'</div>':'')+'</div>';}
'''
HTML_EDITS = [
    (H_HEAD, '<!-- S476 (F-723): one line above the summary card when the statement road is quiet -- amber while no bank statement has reached\n'
             '     the shelf this month (the relay\'s Google authorisation may have lapsed), a grey note when none came for three days. -->\n' + H_HEAD),
    (H_FLASH, H_FLASH + '<div id="road"></div>\n'),
    (H_LOAD, H_LOAD + '    roadLine(j.road);\n'),
    (H_TAIL, HTML_ROAD_FN + H_TAIL),
]

# ------------------------------------------------------------------------------------------------------ finance_app.py
A_RECEPTION = '''    try:
        sys.modules["reception_door"].health_row(add, setting, con)
    except Exception as ex:                                       # noqa: BLE001
        add("reception", "Reception PC", "info", "could not be read (%s)" % ex)
'''
APP_ROAD = '''
    # ---- S476 (F-723): THE STATEMENT ROAD -------------------------------------
    # The relay that files the banks' statements into Drive runs under the owner's personal Google authorisation; when
    # that lapses its failure mail reaches his personal inbox only. So the road is watched by what it produces
    # (packs.statement_road): amber from the 3rd of a month while no bank statement has reached the shelf this month.
    try:
        sys.modules["packs"].statement_road_row(add, con)
    except Exception as ex:                                       # noqa: BLE001
        add("stmtroad", "Bank statements reaching Drive", "info", "could not be read (%s)" % ex)
'''
APP_EDITS = [(A_RECEPTION, A_RECEPTION + APP_ROAD)]

# ---------------------------------------------------------------------------------------------- clinic_state_backup.py
A_RING = '    "/root/portal/ring_outcomes.db",\n]\n'
A_TREES = 'SRC_TREES = [\n    "/root/wa/casepack",\n    "/root/wa/vitals",\n]\n'
BACKUP_EDITS = [
    (A_RING, '    "/root/portal/ring_outcomes.db",\n'
             '    # S476 (F-243, open since S209), 04-Oct-2026: the login store -- every clinic login and its roles, one small\n'
             '    # JSON file that was in no backup at all. Not a secret by this file\'s own patterns; it travels inside the\n'
             '    # encrypted bundle like every other store here. A plain copy.\n'
             '    "/root/portal/clinic_users.json",\n]\n'),
    (A_TREES, 'SRC_TREES = [\n    "/root/wa/casepack",\n    "/root/wa/vitals",\n'
              '    # S476, 04-Oct-2026: the hand-over photos Shavez saves on his month-end checklist (S472) -- on the box only until now.\n'
              '    "/root/finance/statements/packs/handover",\n'
              '    # S476, at the Sanjeevni chat\'s word (its S285 close): the order snapshots under the spine (S470 writes there\n'
              '    # nightly). As a TREE it is ONE source, so a snapshot a later kit prunes never refuses the night -- the reason\n'
              '    # SRC_DIRS left orders/ out at S347.\n'
              '    "/root/finance/spine/orders",\n]\n'),
]

PLAN = [("packs.py", PACKS_EDITS), ("packs.html", HTML_EDITS), ("finance_app.py", APP_EDITS), ("clinic_state_backup.py", BACKUP_EDITS)]


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(name, src, edits):
    if md5(src.encode("utf-8")) != FROM[name]:
        raise SystemExit("%s is %s, not the %s this kit was built on -- nothing written" % (name, md5(src.encode("utf-8")), FROM[name]))
    for i, (a, b) in enumerate(edits, 1):
        n = src.count(a)
        if n != 1:
            raise SystemExit("%s: anchor %d found %d times (must be exactly once) -- nothing written" % (name, i, n))
        src = src.replace(a, b)
    return src


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: apply_s476.py <packs.py> <packs.html> <finance_app.py> <clinic_state_backup.py>")
    out = []
    for path, (name, edits) in zip(argv[1:], PLAN):
        with open(path, encoding="utf-8", newline="") as fh:
            src = fh.read()
        out.append((path, name, edit(name, src, edits)))
    for path, name, new in out:                       # every file verified before the first is written
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        print("%s  %s  (%d edits)" % (md5(new.encode("utf-8")), name, len(dict(PLAN)[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

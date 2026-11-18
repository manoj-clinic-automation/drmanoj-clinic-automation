"""S834 walk: the due rule in four places, on a COPY of the live database with made-up patients (ZZ9xxx, days in Jan-2027).
usage: python3 -I walk_s834.py <code_dir> <duty_map.json> <db_copy>   (code_dir holds xray_photo_nudge.py, slip_log.py, records.py)
Exit 0 = all green. Run on the OLD files it must go red (the CONTROL)."""
import importlib.util, json, os, shutil, sqlite3, sys
CODE, MAP, DB0 = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.environ.get('S834_PYLIB', '/tmp/pylib'))   # flask in the device VM; the server's venv has it
DB = os.path.join(os.environ.get('TMPDIR', '/tmp'), 's834_walk.db')
shutil.copy(DB0, DB)
os.environ['FINANCE_DB'] = DB
ok = bad = 0
def check(name, got, want):
    global ok, bad
    if got == want:
        ok += 1
    else:
        bad += 1
        print('RED  %s\n     got  %s\n     want %s' % (name, got, want))

con = sqlite3.connect(DB)
CASES = {  # tag: (slip day, logged_at, docterz lines, photo days, filing day, mark)
 'A': ('2027-01-20', '2027-01-20 12:10:00', [('xray', 'Morning')], [], None, None),
 'B': ('2027-01-19', '2027-01-19 19:30:00', [('xray', 'Evening')], [], None, None),
 'C': ('2027-01-20', '2027-01-20 11:00:00', [], [], None, None),
 'D': ('2027-01-20', '2027-01-20 19:00:00', [], [], None, None),
 'E': ('2027-01-18', '2027-01-19 10:00:00', [], [], None, None),
 'F': ('2027-01-18', '2027-01-18 12:00:00', [('xray', 'Morning')], ['2027-01-19'], None, None),
 'G': ('2027-01-15', '2027-01-15 12:00:00', [('xray', 'Morning')], ['2027-01-18'], None, None),
 'H': ('2027-01-11', '2027-01-11 12:00:00', [('xray', 'Morning')], [], None, None),
 'I': ('2027-01-20', '2027-01-20 19:10:00', [('xray', 'Morning'), ('consult', 'Evening')], [], None, None),
 'J': ('2027-01-19', '2027-01-19 12:00:00', [('consult', 'Evening')], [], None, None),
 'K': (None, None, [('xray', 'Morning')], [], None, None),            # Docterz only, day 2027-01-20
 'L': ('2027-01-19', '2027-01-19 12:00:00', [('xray', 'Morning')], [], None, 'not_done'),
 'M': ('2027-01-19', '2027-01-19 12:00:00', [('xray', 'Morning'), ('xray', 'Evening')], [], None, None),
 'N': ('2027-01-18', '2027-01-18 19:00:00', [('xray', 'Evening')], [], '2027-01-19', None),
 'P': ('2027-01-20', '2027-01-20 19:00:00', [('xray', ''), ('consult', 'Morning')], [], None, None),   # blank X-ray shift: any line's
 'Q': (None, None, [('xray', ''), ('consult', 'Morning')], [], None, None),                         # Docterz only, blank X-ray shift
 'R': ('2027-01-19', '2027-01-19 12:00:00', [('xray', 'Morning')], [], None, 'rc_not_done'),        # Check karein's 'not done' answer
 'S': ('2027-01-20', ['2027-01-20 19:00:00', '2027-01-20 11:00:00'], [], [], None, None),          # two slips: the earliest due wins
}
ID = {t: 'ZZ90%02d' % (i + 1) for i, t in enumerate(sorted(CASES))}
TAG = {v: k for k, v in ID.items()}
sn = 990000
for t, (day, logged, lines, photos, filing, mark) in sorted(CASES.items()):
    cid = ID[t]
    lday = day or '2027-01-20'
    for sec, sh in lines:
        sn += 1
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, shift) VALUES (?,?,?,?,?,?)",
                    (lday, sec, sn, 'MADE UP %s' % t, cid, sh))
    for lg in ([] if not day else (logged if isinstance(logged, list) else [logged])):
        sn += 1
        cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, logged_at) VALUES ('xp',?,?,?,'ok',?)", (sn, day, cid, lg))
        con.execute("INSERT INTO slip_item (slip_id, kind, name) VALUES (?, 'xray', 'MADE UP VIEW')", (cur.lastrowid,))
    for p in photos:
        con.execute("INSERT INTO record_file (clinic_id, kind, day, source, source_ref) VALUES (?, 'xray', ?, 'walk', ?)", (cid, p, 'w' + cid + p))
    if filing:
        con.execute("INSERT INTO xray_filing (src_id, clinic_id, day, state) VALUES (?,?,?, 'planned')", ('walk' + cid, cid, filing))
    if mark == 'rc_not_done':
        con.execute("INSERT INTO record_check (key, kind, clinic_id, answer) VALUES (?, 'xray', ?, 'not_done')", ('xm:%s:%s' % (day, cid), cid))
    elif mark:
        con.execute("INSERT INTO pend_mark (key, kind, clinic_id, day, act) VALUES (?, 'xray', ?, ?, ?)", ('xm:%s:%s' % (day, cid), cid, day, mark))
con.commit()

def load(name):
    spec = importlib.util.spec_from_file_location(name + '_w', os.path.join(CODE, name + '.py'))
    m = importlib.util.module_from_spec(spec); sys.path.insert(0, CODE); spec.loader.exec_module(m); return m

NOWS = ['2027-01-20 14:59:00', '2027-01-20 15:00:00', '2027-01-20 18:00:00', '2027-01-21 15:00:00', '2027-01-21 16:00:00']
due = {'A': '2027-01-20 15:00:00', 'B': '2027-01-20 15:00:00', 'C': '2027-01-20 15:00:00', 'D': '2027-01-21 15:00:00',
       'E': '2027-01-19 15:00:00', 'G': '2027-01-15 15:00:00', 'H': '2027-01-11 15:00:00', 'I': '2027-01-20 15:00:00',
       'J': '2027-01-20 15:00:00', 'K': '2027-01-20 15:00:00', 'M': '2027-01-20 15:00:00', 'N': '2027-01-19 15:00:00',
       'L': '2027-01-19 15:00:00', 'P': '2027-01-20 15:00:00', 'Q': '2027-01-20 15:00:00', 'R': '2027-01-19 15:00:00', 'S': '2027-01-20 15:00:00'}
def want(now, excl, seven=False):
    """What should be pending at `now`, minus the place's own exclusions."""
    import datetime as dt
    out = set()
    since = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=7)).isoformat()
    for t, d in due.items():
        if d > now or t in excl:
            continue
        if seven and (CASES[t][0] or '2027-01-20') < since:
            continue
        out.add(t)
    return out
NOSLIP = {'K', 'Q'}
EX_NOTICE = NOSLIP | {'N', 'L', 'R'}     # in the folder; X-ray not done (both marks)
EX_DUTY = NOSLIP | {'L', 'R'}           # the duty map counts a picture in the folder until filed (as before)
EX_SLIPLOG = NOSLIP | {'L'}             # Report baaki honours pend_mark only (as before); N shows as 'mailed'
EX_RECORDS = {'N', 'R'}                 # Check karein honours its own answers only (as before)

# 1 -- the notice
nz = load('xray_photo_nudge')
for now in NOWS:
    c2 = sqlite3.connect(DB)
    today = now[:10]
    import datetime as dt
    if nz.SQL.count('?') == 3:
        rows = c2.execute(nz.SQL, ((dt.date.fromisoformat(today) - dt.timedelta(days=7)).isoformat(), today, now)).fetchall()
    else:
        rows = c2.execute(nz.SQL, (getattr(nz, 'FROM_DAY', '2026-09-23'), today)).fetchall()
    got = {TAG[r[1]] for r in rows if r[1] in TAG}
    check('notice %s' % now, sorted(got), sorted(want(now, EX_NOTICE, seven=True)))
    check('notice %s: no real patient counted' % now, len([r for r in rows if r[1] not in TAG]), 0)
    if hasattr(nz, 'counts'):
        try:
            t_, o_, tot = nz.counts(c2, today, now)
        except TypeError:
            t_, o_, tot = nz.counts(c2, today)
        w = want(now, EX_NOTICE, seven=True)
        check('notice counts %s' % now, (t_, o_), (len([x for x in w if (CASES[x][0] or '') == today]), len([x for x in w if (CASES[x][0] or '') != today])))
# 2 -- the duty map
m = json.load(open(MAP, encoding='utf-8'))
sql = [d for d in m['duties'] if d['id'] == 'alisha.xray_photo'][0]['due_sql']
for now in NOWS:
    q = (sql.replace("date('now','localtime','-7 day')", "date('%s','-7 day')" % now[:10])
            .replace("datetime('now','localtime')", "'%s'" % now).replace("date('now','localtime')", "'%s'" % now[:10]))
    c2 = sqlite3.connect(DB)
    n, since = c2.execute(q).fetchone()
    w = want(now, EX_DUTY, seven=True)
    check('duty %s' % now, (n, since), (len(w), min(CASES[x][0] for x in w) if w else None))
# 3 -- Report baaki (slip_log.xray_pending)
sl = load('slip_log')
for now in NOWS:
    os.environ['SLIP_NOW'] = now.replace(' ', 'T')
    c2 = sqlite3.connect(DB); c2.row_factory = sqlite3.Row
    rows = sl.xray_pending(c2)
    got = {TAG[o['clinic_id']]: o['st'] for o in rows if o['clinic_id'] in TAG}
    check('Report baaki %s' % now, sorted(got), sorted(want(now, EX_SLIPLOG)))
    if now == '2027-01-20 18:00:00':
        check('Report baaki words %s' % now, (got.get('N'), got.get('E'), got.get('G'), got.get('A')), ('mailed', 'late', 'late', 'wait'))
    if now == '2027-01-21 16:00:00':
        check('Report baaki: two slips, late from the earliest due %s' % now, (got.get('S'), got.get('D')), ('late', 'wait'))
# 4 -- Check karein (records.xray_items)
rc = load('records')
for now in NOWS:
    os.environ['RECORDS_NOW'] = now.replace(' ', 'T')
    c2 = sqlite3.connect(DB); c2.row_factory = sqlite3.Row
    rows = [i for i in rc.xray_items(c2) if i.get('kind') == 'xray_missing']
    got = {TAG[i['clinic_id']] for i in rows if i['clinic_id'] in TAG}
    check('Check karein %s' % now, sorted(got), sorted(want(now, EX_RECORDS)))
# 5 -- one rule, four copies
pieces = [(nz.__dict__.get('XRAY_DUE'), nz.__dict__.get('XRAY_FILED')), (sl.__dict__.get('XRAY_DUE'), sl.__dict__.get('XRAY_FILED')),
          (rc.__dict__.get('XRAY_DUE'), rc.__dict__.get('XRAY_FILED'))]
check('the rule byte-equal in three files', len(set(pieces)) == 1 and pieces[0][0] is not None, True)
check('the duty map carries the same rule', bool(pieces[0][0]) and pieces[0][0] in sql and pieces[0][1] in sql, True)
print('S834 walk: %d green, %d red' % (ok, bad))
sys.exit(1 if bad else 0)

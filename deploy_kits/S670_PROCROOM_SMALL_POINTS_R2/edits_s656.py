#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""edits_s656.py -- the build record of S656_PROCROOM_SMALL_POINTS: the exact, counted edits that turn procroom.py f6578535
(S648's TO, confirmed by the 26-Oct bundle) into the kit's whole procroom.py. Each old text must occur exactly once.
    python3 -B edits_s656.py <procroom.py FROM> <procroom.py TO>
"""
import hashlib
import sys

FROM_PIN = "f6578535ba3d85dd9c7561df0798a443"

E = []

# E1 -- the version
E.append(('VERSION = "S648"\n', 'VERSION = "S656"\n'))

# E2 -- the header says what S656 changes
E.append(("""    01-10-2026), not one week; the door, Baaki din and his page's line are one computation (open_days).
\"\"\"
""", """    01-10-2026), not one week; the door, Baaki din and his page's line are one computation (open_days).
    S656 (the reviews' small points): a column a later kit added (proc_use.lkey) is added to a table made before it; a photo's lines
    are pre-matched for the month end's comparisons by ONE rule -- the products in use or rarely used, and a retired one only where
    that scan already holds it (photo_lines_for: the match, fits(), the quantities, the rates and the rate words); and the month end
    keeps the rates he typed when he changes Its scan.
\"\"\"
"""))

# E3 -- ensure(): the add-column step (a table made before a column was added)
E.append(("""def ensure(db):
    \"\"\"Additive and idempotent. Two gunicorn workers start at once: 'already exists' from the second is normal.\"\"\"
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    db.commit()
""", """# S656: a column a later kit added to a table that may have been made before it -- added once, never changed after
ADD_COLS = (("proc_use", "lkey", "TEXT NOT NULL DEFAULT ''"),)


def ensure(db):
    \"\"\"Additive and idempotent. Two gunicorn workers start at once: 'already exists' / 'duplicate column' from the second is normal.\"\"\"
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    for t, c, spec in ADD_COLS:
        have = {r[1] for r in db.execute("PRAGMA table_info(%s)" % t)}
        if have and c not in have:
            try:
                db.execute("ALTER TABLE %s ADD COLUMN %s %s" % (t, c, spec))
            except sqlite3.OperationalError as ex:
                if "duplicate column" not in str(ex).lower():
                    raise
    db.commit()
"""))

# E4 -- the one pre-match rule for comparisons with a scan
E.append(("""def delivery_papers(db):
""", """def photo_lines_for(rd, items, slines):
    \"\"\"S656: a photo's lines pre-matched for a comparison with ONE scan, by the desk's own rule: the products in use or rarely used,
    and a retired one only where that scan already holds it -- so fits(), the quantities, the rates and the match agree.\"\"\"
    held = {l["item_id"] for l in (slines or []) if l.get("item_id")}
    return photo_lines(rd, [i for i in items if i["state"] in ("active", "rare") or i["id"] in held])


def delivery_papers(db):
"""))

# E5 -- match_paper: fits() and the ranking, per scan, by that rule
E.append(("""    if any(taken.get(c["id"]) not in (None, p.get("id")) for c in same):
        pl = photo_lines(rd, list(byid.values()))
        same = [c for c in same if taken.get(c["id"]) in (None, p.get("id")) or fits(pl, saved_lines(db, c))]
""", """    if any(taken.get(c["id"]) not in (None, p.get("id")) for c in same):
        same = [c for c in same if taken.get(c["id"]) in (None, p.get("id"))
                or fits(photo_lines_for(rd, list(byid.values()), saved_lines(db, c)), saved_lines(db, c))]
"""))
E.append(("""    pk = {_qkey(l) for l in photo_lines(rd, list(byid.values()))}
    return max(same, key=lambda c: (len(pk & {_qkey(l) for l in saved_lines(db, c)}), -c["id"]))
""", """    return max(same, key=lambda c: (len({_qkey(l) for l in photo_lines_for(rd, list(byid.values()), saved_lines(db, c))}
                                        & {_qkey(l) for l in saved_lines(db, c)}), -c["id"]))
"""))

# E6 -- month_view: the quantities and the fits flag by that rule
E.append(("""        pl = photo_lines(rd, usable)
        r = role_of(db, c) if c else None
""", """        pl = photo_lines(rd, usable)
        plc = photo_lines_for(rd, items, saved_lines(db, c)) if c else pl     # S656: compared with its scan by the one rule
        r = role_of(db, c) if c else None
"""))
E.append(("""            qw = qty_diffs(pl, saved_lines(db, c), byid) if (c and rd) else []
""", """            qw = qty_diffs(plc, saved_lines(db, c), byid) if (c and rd) else []
"""))
E.append(("""                     "count": True, "same_as": "", "fits": bool(c and rd and fits(pl, saved_lines(db, c)))})
""", """                     "count": True, "same_as": "", "fits": bool(c and rd and fits(plc, saved_lines(db, c)))})
"""))

# E7 -- photo_editor: the photo's rates and quantities beside the scan's lines, by that rule
E.append(("""    if c is not None and saved_lines(db, c):
        prate = {}
        pqty = {}
        for l in pl:
""", """    if c is not None and saved_lines(db, c):
        prate = {}
        pqty = {}
        pl = photo_lines_for(rd, items, saved_lines(db, c))          # S656: the one rule (a retired product the scan holds is kept)
        for l in pl:
"""))

# E8 -- check_photo: the quantity words kept at his Save, by that rule
E.append(("""        qd = qty_diffs(photo_lines(rd, list(byid.values())), old, byid) if rd else []
""", """        qd = qty_diffs(photo_lines_for(rd, items, old), old, byid) if rd else []
"""))

# E9 -- the month end keeps the rates he typed when he changes Its scan: each typed rate per line's product (two lines of one product
# keep their own), restored once and only on the page that change opened (its scan), within 2 minutes; never stored on the server
E.append(("""{% if e %}<script>(function(){var s=document.getElementById('s635scan');if(s){s.addEventListener('change',function(){location.href=s.getAttribute('data-base')+'&scan='+encodeURIComponent(s.value)+'#s635edit';});}})();</script>{% endif %}\"\"\"
""", """{% if e %}<script>(function(){var s=document.getElementById('s635scan');if(!s){return;}var K='s656rates{{e.p.id}}';
function q(n){return document.querySelector('[name="'+n+'"]');}
function key(k){var i=q('i'+k),n=q('n'+k),iv=i?i.value:'';if(iv&&iv!=='ask'){return 'i'+iv;}var t=n?n.value.trim().toLowerCase():'';return t?'n'+t:'';}
var cur='';try{cur=new URLSearchParams(location.search).get('scan')||'';}catch(x){cur='';}
var m=null;try{m=JSON.parse(sessionStorage.getItem(K)||'null');sessionStorage.removeItem(K);}catch(x){m=null;}
if(m&&m.t&&(Date.now()-m.t)<120000&&m.r&&m.s===cur){var c=0;document.querySelectorAll('#s635edit input.rt').forEach(function(r){var kk=key(r.name.slice(1));
var a=(kk&&Object.prototype.hasOwnProperty.call(m.r,kk))?m.r[kk]:null;if(a&&a.length){r.value=a.shift();c++;}});
if(c){var p=document.createElement('p');p.className='muted';p.id='s656kept';p.style.margin='4px 0';p.textContent='Your typed rates are kept on the lines of the same product ('+c+').';s.parentNode.parentNode.insertBefore(p,s.parentNode.nextSibling);}}
s.addEventListener('change',function(){var r={},n=0;document.querySelectorAll('#s635edit input.rt').forEach(function(x){if(x.value!==x.defaultValue&&x.value.trim()!==''){var kk=key(x.name.slice(1));if(kk){(r[kk]=r[kk]||[]).push(x.value.trim());n++;}}});
if(n){try{sessionStorage.setItem(K,JSON.stringify({t:Date.now(),s:s.value,r:r}));}catch(x){}}
location.href=s.getAttribute('data-base')+'&scan='+encodeURIComponent(s.value)+'#s635edit';});})();</script>{% endif %}\"\"\"
"""))

# E10 -- month_view: the rate words of an unchecked photo by the same one rule (a retired product the scan holds keeps its history)
E.append(("""            rw = rate_words(allrows, pl, day, key, byid) if rd else []
""", """            rw = rate_words(allrows, plc, day, key, byid) if rd else []
"""))

def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    raw = open(src, "rb").read()
    if md5(raw) != FROM_PIN:
        out("FROM is %s, not the pin %s -- STOP" % (md5(raw)[:8], FROM_PIN[:8]))
        return 1
    t = raw.decode("utf-8")
    for n, (a, b) in enumerate(E, 1):
        k = t.count(a)
        if k != 1:
            out("E%d: its old text occurs %d times, not once -- STOP" % (n, k))
            return 1
        t = t.replace(a, b)
    open(dst, "wb").write(t.encode("utf-8"))
    out("procroom.py: %d counted edits, FROM %s -> TO %s" % (len(E), FROM_PIN[:8], md5(t.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))

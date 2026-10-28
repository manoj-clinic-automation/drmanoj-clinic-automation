"""make_s676.py -- kit S676_SECTIONS_BY_FAMILY (Sanjeevni session S362, 28-Oct-2026). F-1035's residue, the owner's "All three" (12:37 IST):
  (1) a name Marg prints for the first time had NO section row until somebody re-ran the seed (seeded once, 18-Sep; 24 names of the 26-Oct
      closing have none) -- now section_map.on_closing runs from stock_app.api_snapshot the moment a closing lands (fail-soft);
  (2) the S268 word rule filed CREPE / CAST SHOE names as consumables, and the owner's correction of ONE size (D795, S669, S671) said nothing
      about its sisters (CAST SHOE L TYNOR, CAST SHOE L UM, CAST SHOE M TYNOR were still Consumables on the 27-Oct copy) -- now the FAMILY
      rule: a name's family is the name up to its first size / number word; a family the owner has ruled (source 'owner', one section)
      decides every sister, at seeding, at his tap (set_section) and in a one-time sweep (the installer's data step).
  /root/finance/section_map.py  abef2baf -> TO   family(), owner_families(), rule_of(), on_closing(), sweep_families(); seed() and
                                                 set_section() use them; LIST_VERSION bumped. The S268 lists are not touched.
  /root/finance/stock_app.py    8413ee55 -> TO   ONE counted edit in api_snapshot: section_map.on_closing after the feed commit, fail-soft.
Usage: python make_s676.py <live root, e.g. /root> <out dir>"""
import hashlib, os, sys

FROM = {"finance/section_map.py": "abef2baf91ccb00288e2960b071ba0d1",
        "finance/stock_app.py": "8413ee5577cc7dac0f0897fbe5a6231d"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s (it is %s)" % (r, h[:8], hashlib.md5(b).hexdigest()[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


S = "finance/section_map.py"
rep(S, '''LIST_VERSION = "S268 (copied from stock_app.py of the 18-Sep-2026 bundle); S662: DYNA a whole word in both"
''', '''LIST_VERSION = ("S268 (copied from stock_app.py of the 18-Sep-2026 bundle); S662: DYNA a whole word in both; "
                "S676: the owner's ruling on one size decides its sisters (family), and every closing seeds its new names")

# --- S676 THE FAMILY RULE (28-Oct-2026, F-1035's residue) -------------------------------------------------------------
# The owner rules a SECTION on one printed name (CAST SHOE S TYNOR -> Orthotics, D-twins of D795; LEUKOCREPE 6 CM -> Medicines, D795).
# Marg prints the same product in other sizes, packs and brands, and adds new ones. The word rule would file a new CREPE size as a
# consumable again; his ruling must reach the sisters by itself. A name's FAMILY is the name up to its first size / number word
# (after a product word of three letters or more): CAST SHOE L UM -> CAST SHOE; LEUKOCREPE 10CM*4IN -> LEUKOCREPE; L S BELT XL CONT GRAY UNIS -> L S BELT;
# a name with no such word is its own family. A family the owner has ruled, in ONE section, decides every sister; two sections in one
# family = no ruling (the word rule stands). Only source='owner' rows rule -- a seed row never teaches another seed row.
_SIZE_WORDS = frozenset(("XS", "S", "M", "L", "XL", "XXL", "XXXL", "SM", "MED", "LG", "SMALL", "MEDIUM", "LARGE",
                         "UNIVERSAL", "UNIV", "FREE", "CHILD", "KID", "KIDS", "ADULT", "JUNIOR", "SENIOR"))
_NUM_RE = re.compile(r"^\\d")


def family(name):
    """The family key of a name: norm_key(name) cut at its first size or number word that comes after a product word (a word of
    three letters or more) -- so L S BELT XL ... is L S BELT and G DRESS 10 is G DRESS, never L or G."""
    toks = norm_key(name).split()
    seen = False
    for i, t in enumerate(toks):
        if seen and (t in _SIZE_WORDS or _NUM_RE.match(t)):
            return " ".join(toks[:i])
        if len(t) >= 3:
            seen = True
    return " ".join(toks)


def owner_families(con):
    """family -> section for every family the owner has ruled in ONE section (a family with two sections rules nothing).
    Also family -> the owner's row item that teaches it (the first by name), for the record line."""
    ensure(con)
    secs, who = {}, {}
    for it, sec in con.execute("SELECT item, section FROM stock_item_section WHERE source='owner' ORDER BY item"):
        f = family(it)
        if not f:
            continue
        secs.setdefault(f, set()).add(str(sec))
        who.setdefault(f, str(it))
    return {f: s.pop() for f, s in secs.items() if len(s) == 1}, who


def rule_of(name, fams):
    """The owner's family ruling for a name, or None."""
    return fams.get(family(name))


def sweep_families(con, by_user="S676", ts=None, fams=None, who=None):
    """Every seed / rename / family row whose family the owner has ruled, and whose section differs, moves to his section
    (source 'family', seeded_as kept, by_user names the teaching row). Owner rows never move. Returns the moves [(item, from, to, by)]."""
    ensure(con)
    ts = ts or now_iso()
    if fams is None:
        fams, who = owner_families(con)
    moves = []
    for k, it, sec, srcx in con.execute("SELECT item_key, item, section, source FROM stock_item_section "
                                        "WHERE source <> 'owner' ORDER BY item").fetchall():
        want = rule_of(it, fams)
        if want and want != str(sec):
            teacher = (who or {}).get(family(it), "")
            con.execute("UPDATE stock_item_section SET section=?, source='family', by_user=?, at=? WHERE item_key=? AND source <> 'owner'",
                        (want, "%s (family of %s)" % (by_user, teacher), ts, k))
            moves.append((str(it), str(sec), want, teacher))
    return moves


def on_closing(con, items, by_user="closing", ts=None):
    """Called by stock_app.api_snapshot after a Marg closing lands: every name it prints has a row by tonight (seed -- never
    overwrites), and the family sweep. Returns (added, moved)."""
    added, _kept = seed(con, items, by_user=by_user, ts=ts)
    return added, len(sweep_families(con, by_user=by_user, ts=ts))

''')
rep(S, '''    extra = extra_consumable_words(con)
    have = {r[0] for r in con.execute("SELECT item_key FROM stock_item_section")}
    added = kept = 0
    for it in items:
        k = norm_key(it)
        if not k:
            continue
        if k in have:
            kept += 1
            continue
        sec = classify(it, extra)
        con.execute("INSERT INTO stock_item_section (item_key, item, section, source, "
                    "seeded_as, by_user, at) VALUES (?,?,?,'seed',?,?,?)",
                    (k, str(it), sec, sec, by_user, ts))
''', '''    extra = extra_consumable_words(con)
    fams, who = owner_families(con)                           # S676: his ruling on one size decides the sisters
    have = {r[0] for r in con.execute("SELECT item_key FROM stock_item_section")}
    added = kept = 0
    for it in items:
        k = norm_key(it)
        if not k:
            continue
        if k in have:
            kept += 1
            continue
        word = classify(it, extra)
        ruled = rule_of(it, fams)
        sec, srcx, by = (ruled, "family", "%s (family of %s)" % (by_user, who.get(family(it), ""))) if ruled else (word, "seed", by_user)
        con.execute("INSERT INTO stock_item_section (item_key, item, section, source, "
                    "seeded_as, by_user, at) VALUES (?,?,?,?,?,?,?)",
                    (k, str(it), sec, srcx, word, by, ts))
''')
rep(S, '''    else:
        con.execute("UPDATE stock_item_section SET item=?, section=?, source='owner', "
                    "by_user=?, at=? WHERE item_key=?", (str(item), section, by_user, ts, k))
    return True, "set to %s" % section
''', '''    else:
        con.execute("UPDATE stock_item_section SET item=?, section=?, source='owner', "
                    "by_user=?, at=? WHERE item_key=?", (str(item), section, by_user, ts, k))
    moved = sweep_families(con, by_user=(by_user or "owner"), ts=ts)      # S676: the sisters follow his word at once
    return True, ("set to %s" % section) + ("; %d sister name(s) followed" % len(moved) if moved else "")
''')

A = "finance/stock_app.py"
rep(A, '''    con.commit()
    # S528 (D709, charter 6): the rename memory is no longer told here. A push carries no capture moment; marg_take._rename_verify
''', '''    con.commit()
    # S676: every name this closing prints has its section row by tonight (section_map.on_closing: a new name takes the owner's ruling on
    # its sisters first, the S268 word rule second; his word is never overwritten). Fail-soft: the closing stands whatever this does.
    try:
        if SECTION_MAP_OK and _kind != "expected":
            _sm.on_closing(con, [(it.get("item") or "").strip() for it in items if (it.get("item") or "").strip()],
                           by_user="closing %s" % as_on)
            con.commit()
    except Exception:                                          # noqa: BLE001
        con.rollback()
    # S528 (D709, charter 6): the rename memory is no longer told here. A push carries no capture moment; marg_take._rename_verify
''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))

# -*- coding: utf-8 -*-
# Snippets for patients_page.py (S862). Read by make_s862.py.
DOC_OLD = '''Mounted by owner_console.init (S851). READ-ONLY on finance.db (mode=ro): it writes only its own reading file
patients_reading.dat beside this file (*.dat is in none of the nightly bundle's lists) and its lock.
'''
DOC_NEW = '''Mounted by owner_console.init (S851). The reading is READ-ONLY on finance.db (mode=ro): it writes only its own reading file
patients_reading.dat beside this file (*.dat is in none of the nightly bundle's lists) and its lock.
S862 (S480, 18-Nov-2026; his "go" 07:59): the diagnosis words, one tap. Two POST doors, his login alone, JSON only:
  /finance/console/api/patients/place     a word (with the spellings and sides he left ticked) -> one standard diagnosis of
                                          his taxonomy, written to dx_term_map (dx_feed.py's own table); then
                                          dx_feed.reclassify() re-reads every visit and the reading is built afresh.
  /finance/console/api/patients/unplace   takes a word back out of dx_term_map, the same way.
  These two doors are the ONLY writes of this file to finance.db, and only to dx_term_map (+ dx_feed's own re-read of dx_visit).
'''

WORDS_OLD = '''    # ------------------------------------------------------------------ diagnosis words the taxonomy does not know
    words = []
    try:
        import dx_feed                                                 # noqa: PLC0415 -- the constant only; nothing is written
        un = getattr(dx_feed, "UNCLASSIFIED", "Unclassified")
        words = [dict(word=str(w or "").strip(), n=int(n)) for w, n in q(
            "SELECT diagnosis_raw, COUNT(*) FROM dx_visit WHERE std_dx=? AND TRIM(COALESCE(diagnosis_raw,''))<>'' "
            "GROUP BY UPPER(TRIM(diagnosis_raw)) ORDER BY COUNT(*) DESC, diagnosis_raw LIMIT 200", un)]
    except Exception:                                                  # noqa: BLE001 -- the block says it could not be read
        words = None
'''
WORDS_NEW = '''    # ------------------------------------------------------------------ diagnosis words the taxonomy does not know
    words = []
    wrows, wchoices, placed = [], [], []
    try:
        import dx_feed                                                 # noqa: PLC0415 -- the constant only; nothing is written
        un = getattr(dx_feed, "UNCLASSIFIED", "Unclassified")
        words = [dict(word=str(w or "").strip(), n=int(n)) for w, n in q(
            "SELECT diagnosis_raw, COUNT(*) FROM dx_visit WHERE std_dx=? AND TRIM(COALESCE(diagnosis_raw,''))<>'' "
            "GROUP BY UPPER(TRIM(diagnosis_raw)) ORDER BY COUNT(*) DESC, diagnosis_raw LIMIT 200", un)]
        try:                                                           # S862: the one-tap rows -- never at the list's cost
            wrows, wchoices = words_for_page(words)
        except Exception:                                              # noqa: BLE001 -- the card shows the list without the taps
            wrows, wchoices = [], []
        if _has(con, "dx_term_map"):
            placed = [dict(term=str(t or ""), std=str(s or ""), at=str(a or "")[:16]) for t, s, a in q(
                "SELECT term, std_dx, set_at FROM dx_term_map ORDER BY set_at DESC, term LIMIT 300")]
    except Exception:                                                  # noqa: BLE001 -- the block says it could not be read
        words = None
'''

READING_OLD = '''                   words=(dict(n=len(words), visits=sum(w["n"] for w in words), top=words[:8]) if words is not None else None),'''
READING_NEW = '''                   words=(dict(n=len(words), visits=sum(w["n"] for w in words), top=words[:8], rows=wrows, choices=wchoices,
                               placed=placed) if words is not None else None),'''

HELPERS_ANCHOR = '''# =================================================================================================== building and serving
'''
HELPERS = '''# =================================================================================================== S862: the diagnosis words, one tap
# The page suggests one standard diagnosis of his taxonomy for each word it did not recognise; "Place" writes his choice to
# dx_term_map (dx_feed.py's own table: a word -> a standard diagnosis) and dx_feed.reclassify() re-reads every visit through the
# taxonomy and the map. A word's spelling slips and its other sides (the same word with LEFT / RIGHT / BOTH, a note in brackets,
# "U/O", "?") are drawn with it, each ticked, so he can leave one out. Undo takes a word out of the map and re-reads the same way.
# Only a word unrecognised at that moment can be placed; only a standard diagnosis of the taxonomy can be chosen.
_SIDES = {"RIGHT", "LEFT", "RT", "LT", "BOTH", "B/L", "BL", "BILATERAL", "U/O", "CAUSE", "OLD", "OF", "IN", "THE", "AND", "WITH"}
_HINTS = (                                                              # first match wins; a suggestion only -- he chooses
    (r"NAILING|PLATING|INTERLOCK|\\bORIF\\b|\\bTKR\\b|\\bTHR\\b|ARTHROPLAST|POST[ -]?OP|IMPLANT", "Post-Operative Follow-Up"),
    (r"CELLULITIS|ABSCESS|OSTEOMY|NON[ -]?HEALING|WOUND|INFECT|COLLECTION|DISCHARG|TUBERCUL|\\bPUS\\b", "Infection / Osteomyelitis"),
    (r"FRACT|INJUR|TRAUMA|DISLOCAT|CRUSH|SPRAIN", "Trauma / Fracture"),
    (r"BAKER", "Knee Osteoarthritis"),
    (r"LYTIC|TUMOU?R|NODULE|\\bMASS\\b|GROWTH|NEOPLAS", "Tumor / Suspected Tumor"),
    (r"OSGOOD|PERTHES|CTEV|CLUB ?FOOT|RICKETS", "Pediatric Orthopedic Disorder"),
    (r"HYPOCALC|VITAMIN|OSTEOPEN|OSTEOPOR", "Osteoporosis / Metabolic Bone Disease"),
    (r"GOUT|URIC", "Gouty Arthritis"),
    (r"\\bDISC\\b|PIVD|BULGE|PROLAPS", "Lumbar Degenerative Disease"),
    (r"BURSITIS|SYNOVITIS|TENDIN|TENOSYN", "General Musculoskeletal Pain"),
    (r"THUMB|WRIST|\\bHAND\\b|FINGER|\\bCMC\\b|\\bCMP\\b", "Hand / Wrist Disorder"),
    (r"ELBOW", "Elbow Soft Tissue Disorder"),
    (r"FOOT|HEEL|ANKLE|\\bMTP\\b|\\bTOES?\\b", "Foot / Heel Pain Syndrome"),
    (r"SHOULDER", "Shoulder Degenerative Disorder"),
    (r"\\bHIPS?\\b", "Hip Degenerative Disease"),
    (r"LUMBAR|SACR|COCCY|\\bBACK\\b", "Lumbar Mechanical Pain Syndrome"),
    (r"CERVICAL|\\bNECK\\b", "Cervical Mechanical Pain Syndrome"),
    (r"\\bKNEES?\\b|PATELL", "Knee Osteoarthritis"),
    (r"\\bPAIN\\b|ACHE|SWELLING", "General Musculoskeletal Pain"),
)


def _core(word):
    """The word without its sides, brackets and marks, its parts in order -- 'PAIN LEFT THUMB U/O' = 'RIGHT THUMB PAIN'."""
    t = re.sub(r"\\([^)]*\\)", " ", str(word or "").upper())
    t = re.sub(r"[^A-Z0-9/]+", " ", t)
    return " ".join(sorted({x for x in t.split() if x not in _SIDES}))


def _vocab(dn):
    v = set()
    for kw, _s in list(getattr(dn, "TAXONOMY", []) or []) + list(getattr(dn, "_ABBREV", []) or []):
        for t in re.split(r"[^A-Z]+", str(kw).upper()):
            if len(t) >= 5:
                v.add(t)
    return v


def _suggest(word, dn, vocab, vlist):
    """(standard diagnosis, why) or ('', ''). A spelling slip read through his own taxonomy first, then the hints."""
    import difflib                                                     # noqa: PLC0415
    up = str(word or "").upper()
    parts, slips = re.split(r"([^A-Z]+)", up), []
    for i, t in enumerate(parts):
        if len(t) >= 5 and t.isalpha() and t not in vocab:
            m = difflib.get_close_matches(t, vlist, n=1, cutoff=0.85)
            if m:
                slips.append((t, m[0]))
                parts[i] = m[0]
    if slips:
        try:
            s = dn.normalise_diagnosis("".join(parts)).get("Standardized_Diagnosis") or ""
            if s in dn.CATEGORY:
                return s, "the spelling " + ", ".join("%s = %s" % x for x in slips)
        except Exception:                                              # noqa: BLE001 -- fall back to the hints
            pass
    for pat, s in _HINTS:
        m = re.search(pat, up)
        if m and s in dn.CATEGORY:
            a = re.search(r"[A-Z0-9/]*$", up[:m.start()]).group(0)
            b = re.search(r"^[A-Z0-9/]*", up[m.end():]).group(0)
            return s, "the word %s" % (a + m.group(0) + b).strip()
    return "", ""


def _clusters(words):
    """Index groups: one word with its spelling slips and other sides (same core, or cores 90% alike)."""
    import difflib                                                     # noqa: PLC0415
    n = len(words)
    par = list(range(n))

    def top(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    cores = [_core(w["word"]) for w in words]
    for i in range(n):
        for j in range(i + 1, n):
            a, b = cores[i], cores[j]
            if a and b and (a == b or (min(len(a), len(b)) >= 6 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.9)):
                par[top(j)] = top(i)
    g = defaultdict(list)
    for i in range(n):
        g[top(i)].append(i)
    return [sorted(x, key=lambda i: (-words[i]["n"], words[i]["word"])) for x in g.values()]


def words_for_page(words):
    """(rows, choices). rows: one per word with its slips and sides -- word, n (visits of all), words [{word, n}], sug, why.
    choices: every standard diagnosis of his taxonomy with its group, for the page's list."""
    import dx_feed                                                     # noqa: PLC0415
    dn = dx_feed._normaliser()
    choices = [dict(std=s, cat=c) for s, c in sorted(dn.CATEGORY.items(), key=lambda x: (x[1], x[0]))]
    vocab = _vocab(dn)
    vlist = sorted(vocab)
    rows = []
    for g in _clusters(words):
        ws = [dict(word=words[i]["word"], n=words[i]["n"]) for i in g]
        sug, why = "", ""
        for w in ws:
            sug, why = _suggest(w["word"], dn, vocab, vlist)
            if sug:
                break
        rows.append(dict(word=ws[0]["word"], n=sum(w["n"] for w in ws), words=ws, sug=sug, why=why))
    rows.sort(key=lambda r: (-r["n"], r["word"]))
    return rows, choices


class PlaceError(Exception):
    pass


def place_words(con, words, std, who):
    """His tap: each word (still unrecognised now) -> std in dx_term_map; every visit re-read; the reading built afresh."""
    import dx_feed                                                     # noqa: PLC0415
    dn = dx_feed._normaliser()
    std = str(std or "").strip()
    if std not in dn.CATEGORY:
        raise PlaceError("Choose a group from the list first.")
    if not isinstance(words, list) or not words or len(words) > 50:
        raise PlaceError("No word was chosen.")
    dx_feed.ensure(con)
    open_ = {dx_feed.term_key(r[0]) for r in con.execute(
        "SELECT diagnosis_raw FROM dx_visit WHERE std_dx=? AND TRIM(COALESCE(diagnosis_raw,''))<>''", (dx_feed.UNCLASSIFIED,)).fetchall()}
    keys = []
    for w in words:
        k = dx_feed.term_key(w if isinstance(w, str) else "")
        if k and k in open_ and k not in keys:
            keys.append(k)
    if not keys:
        raise PlaceError("These words are placed already -- the page is reading afresh.")
    ts = dx_feed.now()
    prev = {k: con.execute("SELECT term, std_dx, set_by, set_at FROM dx_term_map WHERE term=?", (k,)).fetchone() for k in keys}
    for k in keys:
        con.execute("INSERT OR REPLACE INTO dx_term_map (term, std_dx, set_by, set_at) VALUES (?,?,?,?)", (k, std, str(who or "")[:40], ts))
    con.commit()
    try:
        moved = dx_feed.reclassify(con)
    except Exception as e:                                             # noqa: BLE001 -- review 1: the tap is taken back whole
        _put_back(con, prev)
        raise PlaceError("Not done -- the visits could not be re-read just now (%s); nothing changed. Try again in a minute." % type(e).__name__)
    return dict(placed=len(keys), moved=moved, std=std, cat=dn.CATEGORY.get(std, ""), rebuilt=rebuild_now(con))


def _put_back(con, prev):
    """Review 1: a re-read that failed half way is rolled back and the map rows are put back as they were."""
    try:
        con.rollback()
    except Exception:                                                  # noqa: BLE001
        pass
    for k, row in prev.items():
        con.execute("DELETE FROM dx_term_map WHERE term=?", (k,))
        if row is not None:
            con.execute("INSERT INTO dx_term_map (term, std_dx, set_by, set_at) VALUES (?,?,?,?)", tuple(row))
    con.commit()


def unplace_word(con, term):
    """Undo: the word out of dx_term_map; every visit re-read (the word is back among the words to place)."""
    import dx_feed                                                     # noqa: PLC0415
    dx_feed.ensure(con)
    k = dx_feed.term_key(term if isinstance(term, str) else "")
    row = con.execute("SELECT term, std_dx, set_by, set_at FROM dx_term_map WHERE term=?", (k,)).fetchone() if k else None
    if row is None:
        raise PlaceError("That word is not in the placed list -- the page is reading afresh.")
    con.execute("DELETE FROM dx_term_map WHERE term=?", (k,))
    con.commit()
    try:
        moved = dx_feed.reclassify(con)
    except Exception as e:                                             # noqa: BLE001 -- review 1
        _put_back(con, {k: row})
        raise PlaceError("Not done -- the visits could not be re-read just now (%s); nothing changed. Try again in a minute." % type(e).__name__)
    return dict(removed=1, moved=moved, rebuilt=rebuild_now(con))


'''

REBUILD_ANCHOR = '''def _names(con, cids):
'''
REBUILD = '''def _expire():
    """Review 2: when the reading could not be built at once, the stored one is marked old so the page's next open builds it
    (and says so if that fails too) -- never shown as current after his tap."""
    try:
        s, _age = _load()
        if s is None:
            return
        s["built_epoch"] = 0
        tmp = "%s.tmp%d" % (READING, os.getpid())
        fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(s, fh, ensure_ascii=False)
        os.replace(tmp, READING)
    except Exception:                                                  # noqa: BLE001
        pass


def rebuild_now(con):
    """S862: after his tap the reading is built at once (the hourly age rule waits for nothing). True when built."""
    p = _db_path(con)
    if not p:
        return False
    for _i in range(40):
        if _take_lock():
            break
        time.sleep(0.25)
    else:
        _expire()
        return False
    try:
        build(p)
        return True
    except Exception:                                                  # noqa: BLE001 -- the older reading stands, marked old
        _expire()
        return False
    finally:
        try:
            with open(LOCK) as fh:
                mine = fh.read().strip() == str(os.getpid())
            if mine:
                os.unlink(LOCK)
        except OSError:
            pass


'''

ROUTES_ANCHOR = '''    app.register_blueprint(bp)
    return bp
'''
ROUTES = '''    def _post_body():
        """JSON only (a plain form from another site cannot send it); the console's gate first."""
        if not request.is_json:
            return None
        b = request.get_json(silent=True)
        return b if isinstance(b, dict) else None

    @bp.route("/finance/console/api/patients/place", methods=["POST"])
    def patients_place():
        u, err = _gate()
        if err:
            return err
        b = _post_body()
        if b is None:
            return jsonify(ok=False, why="Not understood."), 400
        try:
            res = place_words(_db(), b.get("words"), b.get("std"), str((u or {}).get("user", "") or ""))
        except PlaceError as e:
            return jsonify(ok=False, why=str(e)), 400
        except Exception as e:                                         # noqa: BLE001 -- review 1: a JSON answer, never a bare 500 page
            return jsonify(ok=False, why="Not done (%s) -- try again in a minute." % type(e).__name__), 500
        r = jsonify(ok=True, **res)
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/console/api/patients/unplace", methods=["POST"])
    def patients_unplace():
        _u, err = _gate()
        if err:
            return err
        b = _post_body()
        if b is None:
            return jsonify(ok=False, why="Not understood."), 400
        try:
            res = unplace_word(_db(), b.get("term"))
        except PlaceError as e:
            return jsonify(ok=False, why=str(e)), 400
        except Exception as e:                                         # noqa: BLE001 -- review 1: a JSON answer, never a bare 500 page
            return jsonify(ok=False, why="Not done (%s) -- try again in a minute." % type(e).__name__), 500
        r = jsonify(ok=True, **res)
        r.headers["Cache-Control"] = "no-store"
        return r

'''

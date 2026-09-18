"""S313_SECTION_MAP -- one stored answer to "which section is this item in".

WHY THIS EXISTS (F-528).  Measured on the box, 18-Sep-2026, over the newest
snapshot of 373 items, the estate holds FOUR separate rules for the same
question and none of them is stored:

    _is_ortho()        37 words, stock_app   -> 93 items   (drives the pricing
                                                 margin, 0.30 vs 0.20, and the
                                                 'dead' lane)
    _is_consumable()   31 words + a setting  -> 25 items
    _is_orthotic()     34 words, not consum. -> 68 items
    orthotics.vocab    13 phrases, a SETTING -> 51 items   (read by darpan_app
                                                 only -- the counter's screen)

They disagree.  PRIME PAD 4" and 6" are ortho for pricing and neither orthotic
nor consumable for anything else, so they fall in no section at all.  SKIN
TRACTION HOPE is an orthotic that is not ortho; TAPEASE NS SPRAY is a consumable
that is not ortho.  And of the 51 items the COUNTER calls orthotics, 2 are not
ortho at all, while 44 of the stock lane's 93 are not in the counter's
vocabulary -- the two screens disagree about half the section.

That is tolerable while every count is a whole-shop count, because the answer
never has to be given.  It stops being tolerable the moment a round is scoped:
a monthly orthotics count is a PROMISE that these lines were counted and those
were not, and the estate cannot say which lines those are without first being
asked which of four rules to use.

SO: one table, one authority, seeded once, corrected by the owner on a screen,
and read by everything that later needs a scope.

WHAT THIS MODULE DELIBERATELY DOES NOT DO.  It changes nothing.  The four word
lists stay exactly where they are and keep doing their own jobs -- pricing,
lanes, the counter's vocabulary -- and nothing in the estate reads this table
yet.  It is the foundation rung of the count-#2-by-section plan and it is built
first precisely so that the seed can be wrong for a while without costing
anything: no screen, no figure and no decision depends on it until the rung
above it is built.

THE SEED RULE is stock_app._voucher_section()'s own, reduced to the item name:
consumable first, then orthotic, else medicine.  It was chosen because it is
already the rule that prints the section heading on a Marg voucher in front of
Amir -- seeding from any other would make the paper and the screen disagree on
day one.

An owner's word is never overwritten by a re-seed.  source tells them apart.
"""

import datetime as dt
import re

SECTIONS = ("Medicines", "Orthotics", "Consumables")

# --- the three word lists, copied VERBATIM from stock_app.py at S268 ---------
# Copied, not imported, on purpose: this table is a RECORD of a decision taken
# on a given day, and it must not silently re-classify itself because somebody
# added a word to a pricing list months later.  If the lists move, the seed is
# re-run deliberately and the difference is visible.
_CONSUMABLE_WORDS = ("GLOVE", "SYRINGE", "COTTON", "BLADE", "CREPE", "BANDAGE", "GAUZE", "DRESS", "CAST",
                     "FIBER", "FIBRE", "POP ", "PLASTER", "NEEDLE", "CANNULA", "IV SET", "SPIRIT", "BETADINE",
                     "SUTURE", "DRAPE", "MASK", "CATHETER", "SCALP VEIN", "ADHESIVE", "TAPE", "LEUKO", "NIPRO",
                     "MICROPORE", "SWAB", "ROLL", "GLOVES")
_ORTHOTIC_WORDS = ("BELT", "BINDER", "BRACE", "COLLAR", "SPLINT", "SUPPORT", "KNEE", "WRIST", "IMMOBIL", "SLING",
                   "SHOE", "WALKER", "FINGER COT", "ELBOW", "ANKLE", "CERVICAL", "LUMBAR", "STICK", "CRUTCH",
                   "BODY AID", "TRACTION", "PILLOW", "HEEL", "INSOLE", "ARCH", "CORSET", "TYNOR", "UNISON",
                   "HOSPIK", "FLAMINGO", "REMEDE", "VISSCO", "DYNA", "BAMBOO")
_ORTHO_WORDS = ("BELT", "BINDER", "BRACE", "COLLAR", "CAST", "PAD ", "SPLINT", "SUPPORT", "KNEE", "WRIST",
                "GLOVE", "SYRINGE", "COTTON", "BLADE", "CREPE", "BANDAGE", "TYNOR", "UNISON", "HOSPIK",
                "IMMOBIL", "SLING", "SHOE", "WALKER", "FINGER COT", "DRESS", "GAUZE", "ELBOW", "ANKLE",
                "CERVICAL", "LUMBAR", "STICK", "CRUTCH", "BODY AID", "FLAMINGO", "REMEDE", "LEUKO", "NIPRO")

LIST_VERSION = "S268 (copied from stock_app.py of the 18-Sep-2026 bundle)"


def norm_key(name):
    """finance_returns.norm_item(), verbatim -- the same key the sale lines and
    the claim queue use, so one item is one row however Marg spells it."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\s+", " ", s).strip()


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _pad(item):
    return " " + str(item or "").upper() + " "


def is_consumable(item, extra_words=()):
    u = _pad(item)
    return any(w in u for w in tuple(_CONSUMABLE_WORDS) + tuple(extra_words))


def is_orthotic(item, extra_words=()):
    u = _pad(item)
    return (not is_consumable(item, extra_words)) and any(w in u for w in _ORTHOTIC_WORDS)


def is_ortho_priced(item):
    """The PRICING sense -- what decides the 0.30 margin. Not a section."""
    u = _pad(item)
    return any(w in u for w in _ORTHO_WORDS)


def classify(item, extra_words=()):
    """THE SEED RULE: stock_app._voucher_section() reduced to the item name.
    Consumable first, then orthotic, else medicine."""
    if is_consumable(item, extra_words):
        return "Consumables"
    if is_orthotic(item, extra_words):
        return "Orthotics"
    return "Medicines"


# ------------------------------------------------------------------ the table

def ensure(con):
    con.execute("""
      CREATE TABLE IF NOT EXISTS stock_item_section (
        item_key  TEXT PRIMARY KEY,          -- norm_key(item)
        item      TEXT NOT NULL,             -- as Marg last printed it
        section   TEXT NOT NULL,             -- one of SECTIONS
        source    TEXT NOT NULL,             -- 'seed' | 'owner'
        seeded_as TEXT,                      -- what the seed rule said, kept even
                                             -- after the owner moves it, so the
                                             -- disagreement stays visible
        by_user   TEXT,
        at        TEXT NOT NULL
      )""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_item_section ON stock_item_section(section)")


def _setting(con, key):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]) if r and r[0] is not None else ""
    except Exception:
        return ""


def extra_consumable_words(con):
    v = _setting(con, "stock.consumable_words")
    return tuple(w.strip().upper() for w in v.split(",") if w.strip())


def counter_vocab(con):
    """The COUNTER's orthotics vocabulary -- a setting the owner edits, read
    today by darpan_app alone. Not an input to the seed; shown beside it so the
    disagreement between the two screens is a fact on a page, not a surprise."""
    v = _setting(con, "orthotics.vocab")
    return tuple(w.strip().upper() for w in v.split(",") if w.strip())


def in_counter_vocab(item, vocab):
    u = _pad(item)
    return any(w in u for w in vocab)


def snapshot_items(con):
    """Every item of the newest Marg closing snapshot, by its own dd-mm-yyyy key."""
    rows = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not rows:
        return []
    as_on = max(rows, key=lambda d: (str(d)[6:], str(d)[3:5], str(d)[:2]))
    return as_on, [r[0] for r in con.execute(
        "SELECT item FROM stock_snapshot WHERE as_on=? ORDER BY item", (as_on,))]


def seed(con, items=None, by_user="seed", ts=None):
    """Insert a row for every item that has none. NEVER overwrites, and in
    particular never overwrites source='owner'. Returns (added, kept, moved_none)."""
    ensure(con)
    ts = ts or now_iso()
    if items is None:
        got = snapshot_items(con)
        items = got[1] if got else []
    extra = extra_consumable_words(con)
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
        have.add(k)
        added += 1
    return added, kept


def set_section(con, item, section, by_user="", ts=None):
    """The owner's tap. Returns (ok, message)."""
    ensure(con)
    ts = ts or now_iso()
    if section not in SECTIONS:
        return False, "that is not one of the three sections"
    k = norm_key(item)
    if not k:
        return False, "no item"
    row = con.execute("SELECT seeded_as FROM stock_item_section WHERE item_key=?", (k,)).fetchone()
    if row is None:
        con.execute("INSERT INTO stock_item_section (item_key, item, section, source, "
                    "seeded_as, by_user, at) VALUES (?,?,?,'owner',NULL,?,?)",
                    (k, str(item), section, by_user, ts))
    else:
        con.execute("UPDATE stock_item_section SET item=?, section=?, source='owner', "
                    "by_user=?, at=? WHERE item_key=?", (str(item), section, by_user, ts, k))
    return True, "set to %s" % section


def summary(con):
    ensure(con)
    out = dict(total=0, by_section={s: 0 for s in SECTIONS}, owner_set=0, moved=0)
    for r in con.execute("SELECT section, source, seeded_as FROM stock_item_section"):
        out["total"] += 1
        out["by_section"][str(r[0])] = out["by_section"].get(str(r[0]), 0) + 1
        if str(r[1]) == "owner":
            out["owner_set"] += 1
            if r[2] and str(r[2]) != str(r[0]):
                out["moved"] += 1
    return out


def rows(con, only_disputed=False, limit=500):
    """Every item with its stored section AND what each of the four rules says.

    `disputed` is the whole point of this page: it is True when the four rules
    do not tell one story about the item -- the pricing list calls it ortho but
    no section list claims it, or the counter's screen and the stock lane put it
    on different sides. Those are the rows worth a tap; the rest are agreed and
    need no attention.
    """
    ensure(con)
    extra = extra_consumable_words(con)
    vocab = counter_vocab(con)
    out = []
    for r in con.execute("SELECT item_key, item, section, source, seeded_as, by_user, at "
                         "FROM stock_item_section ORDER BY item"):
        item = str(r[1])
        cons = is_consumable(item, extra)
        orth = is_orthotic(item, extra)
        opr = is_ortho_priced(item)
        cv = in_counter_vocab(item, vocab) if vocab else None
        # the four disagreements, each named
        why = []
        if opr and not cons and not orth:
            why.append("priced as an orthotic but in no section list")
        if orth and not opr:
            why.append("an orthotic the pricing list does not call ortho")
        if cons and not opr:
            why.append("a consumable the pricing list does not call ortho")
        if cv is True and not opr:
            why.append("the counter calls it an orthotic; the pricing list does not")
        if cv is False and opr:
            why.append("the pricing list calls it ortho; the counter's list does not")
        d = dict(item_key=str(r[0]), item=item, section=str(r[2]), source=str(r[3]),
                 seeded_as=(r[4] or ""), by_user=(r[5] or ""), at=str(r[6] or ""),
                 consumable=cons, orthotic=orth, ortho_priced=opr,
                 counter_vocab=cv, disputed=bool(why), why=why,
                 moved=bool(r[4] and str(r[4]) != str(r[2])))
        if only_disputed and not d["disputed"]:
            continue
        out.append(d)
    out.sort(key=lambda x: (0 if x["disputed"] else 1, x["item"]))
    return out[:int(limit)]


def items_in(con, section):
    """THE WHOLE POINT, once the rungs above this one are built: the list of
    items a section-scoped round would carry. Nothing calls it yet."""
    ensure(con)
    return [str(r[0]) for r in con.execute(
        "SELECT item FROM stock_item_section WHERE section=? ORDER BY item", (section,))]

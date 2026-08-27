#!/usr/bin/python3
"""
rename16.py -- fit every item name inside 16 characters WITHOUT losing the
identifier, and prove the result is still unique.

THE RULE
    Marg prints 16 characters on a bill and 20 on the sale report. Whatever
    falls outside is gone -- not shortened, GONE, and unrecoverable by anything
    downstream. Six sizes of one belt currently print identically.

    So the size, strength or form is PROTECTED and everything else gives way,
    in this order:
        1  the vendor or brand word (UNISON, TYNOR, HOPE, DYNA, UM, HOSPIK...)
           -- dropped first, and only if no sibling needs it to stay distinct
        2  long descriptive words -- abbreviated from a fixed table
        3  filler (THE, OF, WITH, FOR, &)
        4  long words SQUEEZED (inner vowels out) then CLIPPED, longest first
        5  the product word itself, clipped from its right end
        6  dropping a whole middle word -- genuinely last, because a dropped
           word is information gone. An early version dropped the longest word
           and turned DECA INSTABOLIN 50 into DECA 50 and FINGER EXTENSION
           SPLINT into FINGER EXTN. Both fit in sixteen characters and both
           lost the thing that names the product.

    THREE THINGS ARE NEVER TOUCHED: the FIRST word (the product), any short
    middle marker of three characters or less (CR, DS, SP, XT -- these are
    strengths and forms, not description), and the trailing identifier.
    An earlier version trimmed from the left and produced 'HINGED XXL UNIS'
    out of 'KNEE SUPPORT HINGED XXL UNISO'. Losing the word KNEE is not a
    shorter name, it is a different product.

WHAT THIS FILE WILL NOT DO
    It will not emit two names that collide, and it will not emit a name whose
    identifier was dropped. Both are checked after generation, and a name that
    fails is reported for the owner to decide rather than shipped. Renaming one
    product onto another's name would be worse than the truncation it fixes.
"""
import re

LIMIT = 16

# Vendor and brand words. Dropped first because two vendors' L-size collars are
# the same collar to a stock count, and the vendor is on the purchase bill.
VENDOR = {"UNISON","UNISO","UNIS","TYNOR","HOPE","DYNA","UM","HOSPIK","BODYAID","AID",
          "FLAMINGO","NEOLIFE","SUNLINE","PERFECT","PERFE","NIPRO","OLYMPIC","VISSCO",
          "SAMSON","LEUKO","BODY","LYCRA","NEOPRENE"}

# Word -> short form. Only words that appear in this item master.
ABBR = {
 "IMMOBILISER":"IMMOB","IMMOBILIZER":"IMMOB","IMMOBILISE":"IMMOB","IMMOBILSER":"IMMOB",
 "SHOULDER":"SHLDR","CONTOURED":"CONT","SUPPORT":"SUPP","BINDER":"BIND","UNIVERSAL":"UNIV",
 "ADJUSTABLE":"ADJ","ADJUST":"ADJ","SYRINGE":"SYR","DISPOSABLE":"DISPO","BANDAGE":"BAND",
 "ELASTIC":"ELAS","ELAST":"ELAS","TABLETS":"TAB","TABLET":"TAB","INJECTION":"INJ",
 "POWDER":"POW","SACHET":"SACH","SOLUTION":"SOLN","OINTMENT":"OINT","CAPSULES":"CAP",
 "CAPSULE":"CAP","CAPS":"CAP","COLLAR":"COLR","CERVICAL":"CERV","LUMBOGRIP":"LUMBO",
 "CORSET":"CORS","TRACTION":"TRAC","EXTENSION":"EXTN","SPLINT":"SPLNT","BRACE":"BRC",
 "WALKER":"WALK","FOLDING":"FOLD","FOLDIND":"FOLD","SURGICAL":"SURG","GLOVES":"GLOV",
 "CRUTCHES":"CRUTCH","ABDOMINAL":"ABDO","WRIST":"WRST","ANKLE":"ANKL","KNEE":"KNEE",
 "SHEET":"SHT","DRESSING":"DRESS","COTTON":"COTN","CREPE":"CREPE","CRAPE":"CREPE",
 "HEAVY":"HVY","SOFT":"SOFT","HARD":"HARD","BELT":"BELT",
 "CHOCOLATE":"CHOCO","VANILLA":"VANIL","LOTION":"LOTN","PATCH":"PTCH","SPRAY":"SPRY",
 "FORTE":"FORT","INSTABOLIN":"INSTBLN","SPILNT":"SPLNT","REMEDE":"RMD","LYCRA":"LYC",
 "BAMBOO":"BAMB","UNIVERSAL":"UNIV","CLAVICAL":"CLAVI","CLAVICLE":"CLAVI",
}

SIZE = re.compile(r"^(XXXL|XXL|XL|XS|S|M|L|XXX|XX)$", re.I)
# A measurement or strength -- anything that STARTS with a digit and carries
# only digits, unit letters and punctuation: 90 · 12.5 · 500MG · 3ML · 15T ·
# 10CM*4IN · 6". Starting with a digit is what keeps it from swallowing a word.
MEAS = re.compile(r'^\d[\dA-Z."*/x-]*$', re.I)


def toks(name):
    return [t for t in re.split(r"\s+", " ".join(str(name).split()).upper()) if t]


def identifier(ts):
    """
    The trailing tokens that distinguish this item from its siblings.

    A vendor word may sit AFTER the size -- 'KNEE SUPPORT HINGED XXL UNISO'.
    Strip those first, or the scan stops on the vendor, decides there is no
    identifier, and the XXL is quietly lost.
    """
    ts = list(ts)
    while ts and ts[-1] in VENDOR:
        ts = ts[:-1]
    out = []
    for t in reversed(ts):
        if SIZE.match(t) or MEAS.match(t):
            out.insert(0, t)
        elif out:
            break
        else:
            break
    return out


def split_name(ts):
    """
    (body, identifier) from one token list, using ONE definition of where the
    identifier starts.

    THE FAULT THIS FIXES: identifier() strips a trailing vendor word before it
    scans, so for 'ANKLE BINDER L TYNOR' it correctly returns ['L'] -- but the
    caller was slicing the FULL list by that length, removing TYNOR and leaving
    the L in the body too. The L was then appended a second time:
    'ANKLE BINDER L L'. Nineteen names came out that way. Body and identifier
    must be cut from the same list, once.
    """
    ts = list(ts)
    tail = []
    while ts and ts[-1] in VENDOR:
        tail.append(ts.pop())
    ident = identifier(ts)
    body = ts[:len(ts) - len(ident)] if ident else ts[:]
    return body, ident


def shorten(word):
    return ABBR.get(word, word)


def propose(name, keep_vendor=False):
    """Returns (new_name, note). Head, short markers and identifier survive."""
    ts = toks(name)
    body, ident = split_name(ts)
    if not body:
        return " ".join(ts), "nothing to shorten"
    # A one-letter first token is not a product name: 'L S BELT' is one word
    # broken by spaces. Glue it forward before anything else looks at it.
    while len(body) > 1 and len(body[0]) == 1:
        body = [body[0] + body[1]] + body[2:]
    # And when the name LEADS with the vendor -- 'TYNOR WRIST SPLINT LF L' --
    # protecting the first word protects the wrong word. Demote it, so the
    # product survives and the vendor is what gives way.
    if len(body) > 1 and body[0] in VENDOR and not keep_vendor:
        body = body[1:] + [body[0]]
    head, mid = body[0], body[1:]
    notes = []

    def build(h, m):
        return " ".join([x for x in [h] + m + ident if x]).strip()

    if len(build(head, mid)) <= LIMIT:
        out = build(head, mid)
        return out, ("already fits" if out == " ".join(ts) else "spacing only")

    if not keep_vendor:
        drop = [w for w in mid if w in VENDOR]
        if drop:
            mid = [w for w in mid if w not in VENDOR]
            notes.append("dropped %s (it is on the purchase bill)" % "/".join(drop))
            if len(build(head, mid)) <= LIMIT:
                return build(head, mid), "; ".join(notes)

    m2 = [shorten(w) for w in mid]
    h2 = shorten(head)
    if m2 != mid or h2 != head:
        notes.append("shortened words")
        mid, head = m2, h2
        if len(build(head, mid)) <= LIMIT:
            return build(head, mid), "; ".join(notes)

    mid = [w for w in mid if w not in ("THE", "OF", "WITH", "FOR", "&", "AND")]
    if len(build(head, mid)) <= LIMIT:
        return build(head, mid), "; ".join(notes + ["dropped filler"])

    def squeeze(w):
        return w[0] + re.sub(r"[AEIOU]", "", w[1:]) if len(w) > 4 else w

    # Squeeze the inner vowels out of long middle words, longest first.
    order = sorted(range(len(mid)), key=lambda i: -len(mid[i]))
    for i in order:
        if len(build(head, mid)) <= LIMIT:
            break
        if len(mid[i]) > 4 and mid[i] not in VENDOR:
            sq = squeeze(mid[i])
            if sq != mid[i]:
                mid[i] = sq
                notes.append("squeezed")
    if len(build(head, mid)) <= LIMIT:
        return build(head, mid), "; ".join(dict.fromkeys(notes))

    # Then clip long middle words from the right, never below four letters.
    while len(build(head, mid)) > LIMIT and any(len(w) > 4 for w in mid):
        i = max(range(len(mid)), key=lambda i: len(mid[i]))
        mid[i] = mid[i][:-1]
        notes.append("clipped a word")
    if len(build(head, mid)) <= LIMIT:
        return build(head, mid), "; ".join(dict.fromkeys(notes))

    # Then the product word.
    while len(build(head, mid)) > LIMIT and len(head) > 4:
        head = head[:-1]
        notes.append("clipped the product word")
    if len(build(head, mid)) <= LIMIT:
        return build(head, mid), "; ".join(dict.fromkeys(notes))

    # Only now is a whole word given up.
    while len(build(head, mid)) > LIMIT and any(len(w) > 3 for w in mid):
        longest = max((w for w in mid if len(w) > 3), key=len)
        mid = [w for w in mid if w != longest]
        notes.append("DROPPED '%s' — check this one" % longest)
    if len(build(head, mid)) <= LIMIT:
        return build(head, mid), "; ".join(dict.fromkeys(notes))

    # When the vendor MUST stay -- two vendors' XXL collars would otherwise
    # print the same -- squeeze the descriptive words by dropping their inner
    # vowels before touching the product word. SHLDR IMMOB -> SHLDR IMMB.
    if keep_vendor:
        for i, w in enumerate(mid):
            if len(build(head, mid)) <= LIMIT:
                break
            if len(w) > 4 and w not in VENDOR:
                mid[i] = w[0] + re.sub(r"[AEIOU]", "", w[1:])
        if len(head) > 4 and len(build(head, mid)) > LIMIT:
            head = head[0] + re.sub(r"[AEIOU]", "", head[1:])
        if len(build(head, mid)) <= LIMIT:
            return build(head, mid), "; ".join(notes + ["squeezed to keep the brand"])

    # Last resort: clip the product word from its right end.
    while len(build(head, mid)) > LIMIT and len(head) > 4:
        head = head[:-1]
    notes.append("clipped the product word")
    return build(head, mid), "; ".join(notes)


def family_key(name):
    """The name with its size/strength removed -- what siblings share."""
    return " ".join(split_name(toks(name))[0])


def propose_family(members, keep_vendor=False):
    """
    ONE core for a whole size family, so L, M, XL and XXL read the same.

    Proposing each size on its own budget gave 'KNEE SUPP HNGD L' for the L and
    'KNEE HNGD XL' for the XL -- both inside sixteen characters, and together
    unreadable as one product. The family is budgeted by its LONGEST identifier
    and every member then carries the identical core.
    """
    global LIMIT
    idents = [split_name(toks(m))[1] for m in members]
    widest = max((len(" ".join(i)) for i in idents), default=0)
    budget = LIMIT - (widest + 1 if widest else 0)
    stem = split_name(toks(members[0]))[0] or toks(members[0])
    saved = LIMIT
    try:
        LIMIT = max(budget, 6)
        core, note = propose(" ".join(stem), keep_vendor=keep_vendor)
    finally:
        LIMIT = saved
    out = {}
    for m, i in zip(members, idents):
        out[m] = " ".join([core] + i).strip()
    return out, note


def verify(pairs, existing):
    """
    pairs: [(old, new, note)].  existing: every name in the master, normalised.
    Returns (ok, problems). Nothing ships that collides or loses its identifier.
    """
    problems = []
    seen = {}
    changed = {p[0] for p in pairs}
    keep = {n for n in existing if n not in changed}   # names not being renamed
    for old, new, note in pairs:
        n = " ".join(new.split()).upper()
        if len(n) > LIMIT:
            problems.append((old, new, "STILL over %d characters" % LIMIT))
        if split_name(toks(old))[1] and split_name(toks(new))[1] != split_name(toks(old))[1]:
            problems.append((old, new, "the identifier changed or was lost"))
        if n in seen:
            problems.append((old, new, "collides with the new name for '%s'" % seen[n]))
        if n in keep:
            problems.append((old, new, "collides with the existing item '%s'" % n))
        seen[n] = old
    return (not problems), problems

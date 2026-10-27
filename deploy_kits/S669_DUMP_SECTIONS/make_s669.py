"""make_s669.py -- kit S669_DUMP_SECTIONS (Sanjeevni session S359, 28-Oct-2026). The owner, 05:09 IST: orthotics listed under "Medicines and
others" in the expiry watch's dump. Two slips, both ours (not Marg's, not the spine's):
  (1) his own section rulings are keyed on the name as the CLOSING STOCK prints it (stock_item_section.item_key); the BATCH STOCK prints
      names two to four letters longer or shorter (BLING ELASTIC SHOULDER IMMOB S vs ... IMMOB; L S BELT XL CONT GRAY UNIS vs ... UNISON),
      so the exact lookup in expiry_watch.ortho_of misses and the word list has the last word.
  (2) the S268 seed rule filed CAST SHOE S TYNOR and PRIME CAST SHOE S as Consumables (CAST is a consumable word, checked first) -- a data
      step, done by the installer, not here.
  /root/finance/expiry_watch.py  7ba3b0bc -> TO  1 edit in ortho_of: when the exact key misses, a table key that is a Marg-width twin of
        the name (one a prefix of the other, the shorter at least 12 letters, exactly one such key) stands for it. Nothing else moves.
Usage: python make_s669.py <live root, e.g. /root> <out dir>   (writes <out>/finance/expiry_watch.py)"""
import hashlib, os, sys

FROM = {"finance/expiry_watch.py": "7ba3b0bcc0131cb7258ef0dd63afb5b5"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


E = "finance/expiry_watch.py"
rep(E, '''        s = sec.get(nkey(name))
        if s:
            return s == "Orthotics"
''', '''        s = sec.get(nkey(name)) or _twin(sec, nkey(name))     # S669: the owner's word survives Marg's report widths
        if s:
            return s == "Orthotics"
''')
rep(E, '''def nkey(name):''', '''TWIN_MIN = 12


def _twin(sec, k):
    """S669 (28-Oct-2026): Marg's reports print an item's name at different widths (the closing stock 28 letters, the Batch Stock 30, a
    voucher 26), so the owner's section rulings -- keyed on one width -- must be found from another. The section of the ONE table key that is
    a prefix of k or that k is a prefix of, the shorter at least TWIN_MIN letters; None when none or more than one."""
    if not k or len(k) < TWIN_MIN:
        return None
    hits = [t for t in sec if t != k and len(t) >= TWIN_MIN and (k.startswith(t) or t.startswith(k))]
    return sec[hits[0]] if len(hits) == 1 else None


def nkey(name):''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))

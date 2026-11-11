#!/usr/bin/python3
# make_s788.py -- kit S788_XRAY_NAME_DECIDES (S428, 11-Nov-2026, the parent; the owner 09:14 IST: "For such cases, the name should be the
# deciding factor where all other parameters match and the ID is only slightly off"). Usage: make_s788.py <live check_screens.py> <out dir>
# Exact replacements on the live bytes (check_screens.py 597dd8c9 -- S787); every anchor must occur once.
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("597dd8c9"), "not the live check_screens.py (597dd8c9)"
C = b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:80]
    return t.replace(a, b)

C = rp(C, 'VERSION = "S787 1"', 'VERSION = "S788 1"')
C = rp(C, '''def s787_auto(con):''', '''S788_BY = {"user": "system · S788: the name is this patient's, the number on the photo one digit off"}


def _s788_j(s):
    """A name with its spaces taken out, as it sounds: 'sundarwati' = 'Sunder Wati'."""
    return R._s782_ph("".join(R._s752_tokens(s)))


def _s788_alike(toks, stem, name):
    """The picture's name is this patient's: word by word (records._s782_alike), or with the spaces taken out -- the same sound, or
    (six letters or more, the same first letter) one vowel apart inside."""
    if R._s782_alike(toks, R._s752_tokens(name)):
        return True
    a, b = _s788_j(stem), _s788_j(name)
    return bool(a and b) and (a == b or (len(a) >= 6 and len(b) >= 6 and a[0] == b[0] and R._s782_lev1(a, b)))


def _s788_name_decides(con, toks, stem, own, how, fr, d0, d1, cache):
    """S788 (the owner 09:14 IST 11-Nov): "the name should be the deciding factor where all other parameters match and the ID is only
    slightly off" (SUNDARWATI, 24-Oct: the film read 8344 -- another X-ray patient of the day -- her ID 8343). The clinic ID when the
    picture's name (spaces ignored, the usual spelling) is that of exactly ONE patient who came on the film's day +-1 (so nobody else
    who came has a name like it), he had an X-ray (slip or Docterz) those days, and there IS a number -- read on the film or written in
    the file name -- every one of which is his ID or one digit off it, even when it is another patient's. Else ''."""
    nums = {x for x in (fr[1] if fr else []) if x}
    if how == "one" and own:
        nums.add(own)
    if not nums or len("".join(toks)) < 4:
        return ""
    ppl = _people(con, d0, d1, cache)
    alike = [c for c, p in ppl.items() if any(_s788_alike(toks, stem, nm) for nm in p["names"])]
    if len(alike) != 1:
        return ""
    cid = alike[0]
    if not ppl[cid]["xdays"]:
        return ""
    if not all(x == cid or R._s752_one_off(x, cid) for x in nums):
        return ""
    return cid


def s787_auto(con):''')
C = rp(C, '''        d0, d1 = _d(day, -1), _d(day, 1)

        def alike(names):''', '''        d0, d1 = _d(day, -1), _d(day, 1)
        nid = _s788_name_decides(con, toks, stem, own, how, fr, d0, d1, cache)   # S788: the name decides, the number one digit off
        if nid:
            _write(con, "xf:" + r["src_id"], "xray_file", r["clinic_id"] or "", "id_fixed", nid, S788_BY)
            n += 1
            continue

        def alike(names):''')
C = rp(C, '''    if how == "none":
        return "Photo par clinic ID nahi likha", "No clinic ID on the photo"''', '''    fr = R._s772_film(con, row["src_id"])                 # S788: say what the film itself reads, not only the file's name
    film = [x for x in (fr[1] if fr else []) if x]
    if how == "none" and film:
        who = ", ".join("%s (%s)" % (x, _name_of(con, x) or "not a known ID") for x in film[:2])
        return ("File ke naam mein ID nahi; film par ID %s likha hai" % who, "No ID in the file name; the film reads %s" % who)
    if how == "none":
        return ("File ke naam mein clinic ID nahi" + (" (film abhi padhi nahi gayi)" if fr is None else "; film par bhi ID nahi padha"),
                "No clinic ID in the file name" + (" (the film not read yet)" if fr is None else "; none read on the film"))''')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "check_screens.py"), "wb").write(C.encode("utf-8"))
print("written check_screens.py", hashlib.md5(C.encode("utf-8")).hexdigest()[:8])

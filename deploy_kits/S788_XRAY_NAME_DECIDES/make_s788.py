#!/usr/bin/python3
# make_s788.py -- kit S788_XRAY_NAME_DECIDES (+ the lab list, b) (S428, 11-Nov-2026, the parent; the owner 09:14 IST: "For such cases, the name should be the
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
    """A name with its spaces taken out, as it sounds: 'RAMRATI' = 'Ram Rati' (a made-up example)."""
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
    slightly off" (a 24-Oct photo: the film read another X-ray patient's ID of that day, one digit off hers). The clinic ID when the
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
# ---- S788 (b), the owner 09:22 IST: "Lab report came, no blood slip ... How about filing these reports automatically and not holding
# them just because there was no blood slip and only a mention that for these patients no blood slip was generated." Every such report
# is ALREADY filed in the patient's record (record_file, from the lab's mail); the list only asked about the slip. Now: nothing to do
# for them -- off Shavez's queue and his Aaj ka kaam count; on the owner's page a list for information (the report, no buttons). Only a
# report that looks like the WRONG ID (the lab's name is another visitor's) still asks, as before.
C = rp(C, """        items += lab_items(con) + xbill_items(con)""",
          """        items += [i for i in lab_items(con) if i["wrong"]] + xbill_items(con)   # S788: only a likely wrong ID asks""")
C = rp(C, """    l = len(lab_items(con)) if lab else 0""",
          """    l = len([i for i in lab_items(con) if i["wrong"]]) if lab else 0   # S788: the rest are filed, for information only""")
C = rp(C, """['lab','Lab report came, no blood slip','also on Shavez’s list','#1D4ED8']""",
          """['lab','Lab report filed, no blood slip','in the record already · for your information','#1D4ED8']""")
C = rp(C, """lab:['Lab report came, no blood slip','matched by the report’s clinic ID against the slips and Docterz · Shavez answers these too — whoever answers first closes it for both']""",
          """lab:['Lab report filed, no blood slip','each report is already in the patient’s record · no blood slip was made for it — nothing to do · only a report that looks like the wrong ID asks you (and Shavez)']""")
C = rp(C, """  if(TAB==='lab')acts='<button class="'+(on?'b2':'b1 bbl')+'" data-o="1">'+(on?'Close':'See report &amp; answer')+'</button>';""",
          """  if(TAB==='lab')acts='<button class="'+(on||!i.wrong?'b2':'b1 bbl')+'" data-o="1">'+(on?'Close':(i.wrong?'See report &amp; answer':'See report'))+'</button>';""")
C = rp(C, """'A blood slip was not made for this test. Has it been made now?'""",
          """'Filed in the patient’s record. No blood slip was made for this test — nothing to do.'""")
C = rp(C, """'<a class="b1 bbl" style="display:inline-flex;align-items:center;text-decoration:none" href="'+esc(i.desk)+'">Make the blood slip (Parchi desk) →</a><button class="b2" data-a="direct_lab">Went straight to the lab</button>'""",
          """''""")
C = rp(C, """'</div><span class="f">The same buttons Shavez has — whoever answers first closes it for both.</span></div>';}""",
          """'</div>'+(i.wrong?'<span class="f">The same buttons Shavez has — whoever answers first closes it for both.</span>':'')+'</div>';}""")

os.makedirs(out, exist_ok=True)
open(os.path.join(out, "check_screens.py"), "wb").write(C.encode("utf-8"))
print("written check_screens.py", hashlib.md5(C.encode("utf-8")).hexdigest()[:8])

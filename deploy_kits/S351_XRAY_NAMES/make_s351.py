#!/usr/bin/env python3
"""make_s351.py -- builds the S351 records.py from the S346 file (8cdd334f), two anchored edits, both
checked to occur exactly once. Run offline; the kit ships the RESULT as a full file (D202: one authored
source), this script is evidence of how it was made.
"""
import hashlib
import sys

SRC, DST = sys.argv[1], sys.argv[2]
s = open(SRC, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "8cdd334f2f1329899afd8fc09df145fd", "not the S346 file"

OLD1 = '''IMG = re.compile(r"\\.(jpe?g|png|bmp|tiff?|dcm)$", re.I)
_LEAD = re.compile(r"^\\s*(\\d{1,8})(?!\\d)")
'''
NEW1 = '''IMG = re.compile(r"\\.(jpe?g|png|bmp|tiff?|dcm)$", re.I)
_LEAD = re.compile(r"^\\s*(\\d{1,8})(?!\\d)")
# S351: the staff write the clinic ID at the END of the name -- "NAME 1234.jpg", a second view as
# "NAME 1234 ..jpg" -- and sometimes leave it off the second file altogether. The ID is therefore the ONE
# standalone run of 1-8 digits anywhere in the name (start or end); two such runs is an ambiguity, not a
# guess; a file with no number takes the ID of a same-day sister file with the same name stem, and says so.
_NUM = re.compile(r"(?<!\\d)(\\d{1,8})(?!\\d)")


def xray_id(name):
    """(clinic ID or '', how) -- how is 'one' / 'none' / 'many'. The extension never counts."""
    stem = IMG.sub("", name or "")
    nums = _NUM.findall(stem)
    if len(nums) == 1:
        return nums[0], "one"
    return "", ("none" if not nums else "many")


def xray_stem(name):
    """The name with its numbers, dots and extension gone, for the sister rule: 'PHOOL WATI ..jpg' and
    'PHOOL WATI 3527.jpg' share the stem 'PHOOL WATI'."""
    stem = IMG.sub("", name or "")
    stem = _NUM.sub(" ", stem)
    return re.sub(r"[\\s._\\-]+", " ", stem).strip().upper()
'''
assert s.count(OLD1) == 1, "anchor 1"
s = s.replace(OLD1, NEW1)

OLD2 = '''        t, src = file_time(f)
        row["time"], row["src"] = t, src
        m = _LEAD.match(name)
        if not m:
            row.update(verdict="no clinic ID in the file name \\u2192 check folder", kind="check")
            continue
        row["cid"] = m.group(1)
        if not t:
            row.update(verdict="the file has no time \\u2192 check folder", kind="check")
            continue
        groups.setdefault((t.date().isoformat(), row["cid"]), []).append(row)
    for (day, cid), grp in groups.items():
'''
NEW2 = '''        t, src = file_time(f)
        row["time"], row["src"] = t, src
        cid, how = xray_id(name)
        if how == "many":
            row.update(verdict="two numbers in the file name \\u2014 which is the clinic ID? \\u2192 check folder", kind="check")
            continue
        if not t:
            row.update(verdict="the file has no time \\u2192 check folder", kind="check")
            continue
        row["cid"] = cid
        if not cid:
            row["_sister"] = True          # S351: decided below, once every sister is known
            continue
        groups.setdefault((t.date().isoformat(), row["cid"]), []).append(row)
    # S351: a file with no number takes the ID of a same-day sister with the same name stem -- exactly one.
    for r in rows:
        if not r.pop("_sister", False):
            continue
        day = r["time"].date().isoformat()
        st = xray_stem(r["orig"])
        sis = sorted({g["cid"] for g in rows if g is not r and g["cid"] and g["time"] and st
                      and g["time"].date().isoformat() == day and xray_stem(g["orig"]) == st})
        if len(sis) != 1:
            r.update(verdict="no clinic ID in the file name \\u2192 check folder", kind="check")
            continue
        r["cid"] = sis[0]
        r["sister"] = next(g["orig"] for g in rows if g is not r and g["cid"] == sis[0] and g["time"]
                           and g["time"].date().isoformat() == day and xray_stem(g["orig"]) == st)
        groups.setdefault((day, r["cid"]), []).append(r)
    for (day, cid), grp in groups.items():
'''
assert s.count(OLD2) == 1, "anchor 2"
s = s.replace(OLD2, NEW2)

OLD3 = '''            if same:
                r.update(verdict="matched (%s)" % ("slip %s" % studies[i]["slip"] if studies[i]["slip"] else "Docterz"),
                         kind="ok")
            else:
                r.update(verdict="%d file(s), %d X-ray(s) on the %s \\u2014 numbered, not guessed" % (len(grp), len(studies), how),
                         kind="differ")
'''
NEW3 = '''            if same:
                r.update(verdict="matched (%s)" % ("slip %s" % studies[i]["slip"] if studies[i]["slip"] else "Docterz"),
                         kind="ok")
            else:
                r.update(verdict="%d file(s), %d X-ray(s) on the %s \\u2014 numbered, not guessed" % (len(grp), len(studies), how),
                         kind="differ")
            if r.get("sister"):
                r["verdict"] += " \\u00b7 ID %s taken from the sister file %s" % (cid, r["sister"])
'''
assert s.count(OLD3) == 1, "anchor 3"
s = s.replace(OLD3, NEW3)

open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("written", DST, hashlib.md5(s.encode("utf-8")).hexdigest())

# set_base_s712.py -- kit S712 (session 389, the parent, 06-Nov-2026), D834.
# Arjun (machine number 20) -- base pay 3200 -> 3500 in staff_master.csv, from November.
# ONE cell changes. Every other byte of the file is proved identical. Backup first, atomic replace.
#   python set_base_s712.py <staff_master.csv> [--dry]
# rc 0 = changed (or already 3500, nothing written) . rc 2 = STOPPED, nothing written.
import io, os, shutil, sys, time

UID, NAME, FROM, TO = "20", "Arjun", "3200", "3500"
path = sys.argv[1]
dry = "--dry" in sys.argv[2:]


def stop(why):
    print("STOPPED: %s. Nothing was written." % why)
    sys.exit(2)


if not os.path.isfile(path):
    stop("%s is not there" % path)
raw = io.open(path, "rb").read()
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError:
    stop("the file is not UTF-8")
bom = text.startswith("﻿")
body = text[1:] if bom else text
nl = "\r\n" if "\r\n" in body else "\n"
lines = body.split(nl)
head = lines[0].split(",")
for col in ("user_id", "name", "base_salary", "allowed_offs", "minutes_exempt", "wd_start", "sun_start"):
    if col not in head:
        stop("the header has no %s column" % col)
ix = {c: head.index(c) for c in head}
hits = [i for i, ln in enumerate(lines[1:], 1) if ln.split(",")[:1] == [UID]]
if len(hits) != 1:
    stop("machine number %s is on %d lines, not 1" % (UID, len(hits)))
i = hits[0]
ln = lines[i]
if '"' in ln:
    stop("his line carries quotes -- not the plain line this kit was built for")
f = ln.split(",")
if len(f) != len(head):
    stop("his line has %d fields, the header %d" % (len(f), len(head)))
if f[ix["name"]].strip() != NAME:
    stop("number %s is '%s', not %s" % (UID, f[ix["name"]], NAME))
# what the owner's terms (D834) already rely on -- measured 06-Nov 08:1x IST on the live list
if f[ix["allowed_offs"]].strip() != "4" or f[ix["minutes_exempt"]].strip().upper() != "Y" \
        or not f[ix["wd_start"]].strip() or not f[ix["sun_start"]].strip():
    stop("his offs / late-minutes / duty hours are not as read on 06-Nov (offs 4, minutes exempt, every day a duty day)")
cur = f[ix["base_salary"]].strip()
if cur == TO:
    print("ALREADY: %s's base pay is %s. Nothing written." % (NAME, TO))
    sys.exit(0)
if cur != FROM:
    stop("%s's base pay is %s, not %s as read on 06-Nov" % (NAME, cur, FROM))
f[ix["base_salary"]] = TO
new_lines = lines[:i] + [",".join(f)] + lines[i + 1:]
new = ("﻿" if bom else "") + nl.join(new_lines)
nb = new.encode("utf-8")
# proof: the same file except that one cell
a, b = raw.decode("utf-8").split(nl), new.split(nl)
diff = [k for k in range(max(len(a), len(b))) if (a[k] if k < len(a) else None) != (b[k] if k < len(b) else None)]
if diff != [i]:
    stop("the change would touch lines %s, not only his" % diff)
fa, fb = a[i].split(","), b[i].split(",")
if [k for k in range(len(fa)) if fa[k] != fb[k]] != [ix["base_salary"]]:
    stop("the change would touch more than his base pay")
if len(nb) != len(raw):
    stop("the size would change (%d -> %d)" % (len(raw), len(nb)))
print("%s (number %s): base pay %s -> %s; offs 4, late minutes not counted, every day a duty day -- unchanged."
      % (NAME, UID, FROM, TO))
if dry:
    print("DRY: nothing written.")
    sys.exit(0)
bak = "%s.bak_S712_%s" % (path, time.strftime("%Y%m%d-%H%M%S"))
shutil.copy2(path, bak)
tmp = path + ".tmp_S712"
with io.open(tmp, "wb") as fh:
    fh.write(nb)
st = os.stat(path)
os.chmod(tmp, st.st_mode & 0o777)
try:
    os.chown(tmp, st.st_uid, st.st_gid)
except (AttributeError, PermissionError):
    pass
os.replace(tmp, path)
if io.open(path, "rb").read() != nb:
    shutil.copy2(bak, path)
    stop("read-back did not match -- the old file was put back")
print("written; read back; backup %s" % os.path.basename(bak))

#!/usr/bin/python3
# fix_punch_clock.py -- kit S792_PUNCH_CLOCK (S430, 11-Nov-2026, the parent). Run by the installer only, with the listener stopped.
# Usage: fix_punch_clock.py <punches.csv> <day YYYY-MM-DD> [--apply]
# The owner, 12:10 IST 11-Nov: "correct today's punches also". On that day the machine's clock ran 1 h 39 min to 2 h 57 min behind;
# the server received each punch at the true time. A row of <day> is corrected -- 'datetime' becomes its received_at, the machine's
# time goes to the last column 'machine_time' -- only when (1) its machine time is more than 5 minutes off its received time and
# (2) it ARRIVED ALONE: no other punch was received within a minute of it (a burst is a backlog sent after the machine was offline,
# whose machine times are right). Every other row is left byte-identical; the header gains 'machine_time'. Idempotent: a row that
# already has a machine_time is not touched again. Without --apply it only prints what it would change (counts and minutes).
import datetime as D, os, sys

path, day = sys.argv[1], sys.argv[2]
APPLY = "--apply" in sys.argv
FIX_MIN, ALONE_S = 5, 60
P = lambda s: D.datetime.strptime(s.strip()[:19], "%Y-%m-%d %H:%M:%S")
raw = open(path, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw.split("\n", 1)[0] + "\n" else "\n"
lines = raw.split(nl)
head = lines[0]
if not head.startswith("user_id,datetime,io_mode,verify_mode,received_at"):
    sys.exit("STOP: the header is not the listener's")
recs = []
for i, ln in enumerate(lines[1:], 1):
    parts = ln.split(",")
    if len(parts) >= 5:
        try:
            recs.append((i, parts, P(parts[4])))
        except ValueError:
            pass
out, changed = list(lines), []
for i, parts, rec in recs:
    if not parts[1].startswith(day) and not parts[4].startswith(day):
        continue
    if len(parts) >= 6 and parts[5].strip():
        continue                                         # already corrected
    try:
        m = P(parts[1])
    except ValueError:
        continue
    off = (rec - m).total_seconds() / 60
    if abs(off) <= FIX_MIN:
        continue
    near = [r for j, q, r in recs if j != i and abs((r - rec).total_seconds()) <= ALONE_S and (q[0], q[1]) != (parts[0], parts[1])]
    if near:
        continue                                         # a burst: a backlog -- the machine's time stands
    new = [parts[0], parts[4][:19], parts[2], parts[3], parts[4]] + ([parts[5]] if len(parts) >= 6 else [""])
    new[5] = parts[1]
    out[i] = ",".join(new[:6] + parts[6:])
    changed.append((parts[0], round(off)))
if not head.rstrip().endswith(",machine_time"):
    out[0] = head + ",machine_time"
print("rows on %s corrected: %d %s" % (day, len(changed), " ".join("id%s:+%dmin" % c for c in changed)))
if APPLY:
    tmp = path + ".s792tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(out))
    st = os.stat(path)
    os.chmod(tmp, st.st_mode & 0o7777)
    try:
        os.chown(tmp, st.st_uid, st.st_gid)
    except OSError:
        pass
    os.replace(tmp, path)
    print("APPLIED")

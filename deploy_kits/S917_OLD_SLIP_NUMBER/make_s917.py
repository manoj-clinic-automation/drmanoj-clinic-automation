"""make_s917.py -- S917 (the parent, S498, 21-Nov-2026): slip_log.py 5cfaf728 -> TO. One anchored block in log_slip:
an OLD day's parchi whose number is HIGHER than a saved parchi of a LATER day (same series, same book) asks 'Haan, yahi number'
(the existing gap confirmation) before it is saved -- 14-Nov's paper 1546 had been saved on 15-Nov as a 9-Nov slip."""
import hashlib, sys
FROM = "5cfaf728ffa65cbe7f65522863744238"
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != FROM:
    sys.exit("FROM pin mismatch: %s" % hashlib.md5(b).hexdigest())
t = b.decode("utf-8")
A = "    exp = next_no(con, series)\n    gap = []\n"
assert t.count(A) == 1, "anchor A"
NEW = ("    _s917_later_check(con, series, slip_no, day, confirm_gap)   # S917: an old day's number past a later day's parchi asks first\n"
       + A)
t = t.replace(A, NEW)
B = "def _s912_radd_asks(con, slip_id):\n"
assert t.count(B) == 1, "anchor B"
FN = '''def _s917_later_check(con, series, slip_no, day, confirm_gap):
    """S917 (21-Nov-2026, the owner: a 14-Nov X-ray paper, 1546, was saved on 15-Nov as another patient's 9-Nov slip). A parchi
    written for an OLD day whose number is higher than a parchi already saved for a LATER day (same series, same book) is
    almost surely another day's paper: refused until 'Haan, yahi number' is ticked (the gap confirmation, both pages)."""
    d = day or _today()
    if confirm_gap or d == _today():
        return
    b = book(con, series)
    lo, hi = (None, None)
    if b and b["first_no"] <= slip_no <= b["last_no"]:
        lo, hi = b["first_no"], b["last_no"]
    elif b and _in_prev_book(b, slip_no):
        lo, hi = _prev_range(b)
    if lo is None:
        return
    r = con.execute("SELECT day, slip_no FROM slip WHERE series=? AND state='ok' AND day>? AND slip_no<? AND slip_no BETWEEN ? AND ? "
                    "ORDER BY slip_no DESC LIMIT 1", (series, d, slip_no, lo, hi)).fetchone()
    if r:
        raise SlipError("Parchi %d %s ki parchi %d ke baad ka number hai -- yeh %s ki parchi nahi lagti. Kaagaz par number aur din "
                        "dobara dekhein; sahi ho to 'Haan, yahi number' chun kar Save karein."
                        % (slip_no, _dmy(r["day"])[:6], r["slip_no"], _dmy(d)[:6]))


'''
t = t.replace(B, FN + B)
open(dst, "w", encoding="utf-8", newline="").write(t)
print(hashlib.md5(t.encode("utf-8")).hexdigest())

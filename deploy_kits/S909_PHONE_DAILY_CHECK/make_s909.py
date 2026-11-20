#!/usr/bin/env python3
# make_s909.py -- kit S909_PHONE_DAILY_CHECK: builds the two changed files from their LIVE bytes by exact anchors (each must occur once).
#   python3 make_s909.py <dir holding supplier_msg.py (407d2b1d) and porders_s454.py (06966a0f)> <out dir>
import hashlib, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"supplier_msg.py": "407d2b1d4cf7bda3bb28263bd55e0aa9", "porders_s454.py": "06966a0f9262b1f87c1b608129d11848"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def once(text, old, new, name):
    n = text.count(old)
    if n != 1:
        sys.exit("make_s909: anchor in %s found %d times: %r" % (name, n, old[:80]))
    return text.replace(old, new)


SM_TAIL = '''


# ==========================================================================================================================================
# S909_PHONE_DAILY_CHECK (20-Nov-2026, Sanjeevni session 494; D1026). The reception phone's daily delivery check (phone_check.py) puts ONE
# message of kind 'check' on this road each morning. Here: a check message is handed to the phone once and never retried (the failed-retry
# rule leaves it out), it is never on the stuck list nor counted by the silent-phone line (phone_check says its own result), and the
# check's own Needs-you line joins this file's lines. Every other reader here reads named kinds only.
# ==========================================================================================================================================
_needs_you_lines_before_s909 = needs_you_lines


def needs_you_lines(con):                                      # noqa: F811 -- S909: + the daily phone check's line (fail-soft)
    lines = _needs_you_lines_before_s909(con)
    try:
        import phone_check                                     # noqa: PLC0415
        lines.extend(phone_check.needs_you_lines(con))
    except Exception:                                          # noqa: BLE001 -- the Hub never waits on the check
        pass
    return lines
# ---- S909 end ---------------------------------------------------------------------------------------------------------------------------
'''

PO_TAIL = '''


# ==========================================================================================================================================
# S909_PHONE_DAILY_CHECK (20-Nov-2026, Sanjeevni session 494; D1026): the owner's Reception phone card shows the daily delivery check --
# its last result, the clinic's WhatsApp number (masked), Save, Check now. No dialog. Two owner-only doors:
#    POST /finance/porders/api/s909/clinic_number {number}     the number never reaches a log or the audit
#    POST /finance/porders/api/s909/check_now                  one check now (none running)
# ==========================================================================================================================================
_phone_card_before_s909 = phone_card


def phone_card(con, st):                                       # noqa: F811 -- S909: + the daily check (fail-soft)
    h = _phone_card_before_s909(con, st)
    try:
        import phone_check                                     # noqa: PLC0415
        h = h[:h.rindex("</div>")] + phone_check.card_block(con) + "</div>"
    except Exception:                                          # noqa: BLE001 -- the card never waits on its new part
        pass
    return h


@bp.route(P + "/api/s909/clinic_number", methods=["POST"])
def api_s909_clinic_number():
    u, con, err = _owner_api()
    if err:
        return err
    import phone_check                                         # noqa: PLC0415
    ok, msg = phone_check.save_to(con, who(u), str(_body().get("number") or "")[:30])
    return jsonify(ok=ok, message=msg), (200 if ok else 400)


@bp.route(P + "/api/s909/check_now", methods=["POST"])
def api_s909_check_now():
    u, con, err = _owner_api()
    if err:
        return err
    import phone_check                                         # noqa: PLC0415
    ok, v = phone_check.start_run(con, manual=True, who=who(u))
    return (jsonify(ok=True, run=v), 200) if ok else (jsonify(ok=False, message=v), 409)
# ---- S909 end ---------------------------------------------------------------------------------------------------------------------------
'''

out = {}
for name in FROM:
    b = open(os.path.join(SRC, name), "rb").read()
    if md5(b) != FROM[name]:
        sys.exit("make_s909: %s is %s, expected %s -- nothing built" % (name, md5(b)[:8], FROM[name][:8]))
    out[name] = b.decode("utf-8")

t = out["supplier_msg.py"]
t = once(t, "\"(status='failed' AND kind NOT IN ('order','test') AND (handed_at IS NULL OR handed_at<=?)",
         "\"(status='failed' AND kind NOT IN ('order','test','check') AND (handed_at IS NULL OR handed_at<=?)", "supplier_msg.py")
t = once(t, "\"AND status IN ('queued','failed') AND kind NOT IN ('order','test') AND to_number IS NOT NULL AND attempts<? \"",
         "\"AND status IN ('queued','failed') AND kind NOT IN ('order','test','check') AND to_number IS NOT NULL AND attempts<? \"", "supplier_msg.py")
t = once(t, "FROM supplier_msg WHERE handed_at>=? AND handed_at<=? AND status<>'sent'\",",
         "FROM supplier_msg WHERE handed_at>=? AND handed_at<=? AND status<>'sent' AND kind<>'check'\",", "supplier_msg.py")
out["supplier_msg.py"] = t.rstrip("\n") + "\n" + SM_TAIL

out["porders_s454.py"] = out["porders_s454.py"].rstrip("\n") + "\n" + PO_TAIL

os.makedirs(OUT, exist_ok=True)
for name, text in out.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("make_s909: %s %s -> %s" % (name, FROM[name][:8], md5(text.encode("utf-8"))[:8]))

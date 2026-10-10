#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s521.py -- the builder of kit S521_AMIR_BOARD_STAGE_PROOF (11-Oct-2026, F-838).

    python3 -B make_s521.py --finance /root/finance --out DIR

Reads ONE live file, stock_app.py, refuses anything but its FROM pin (1f43f47e, S520's TO), makes THREE anchored edits (each anchor must
occur exactly once, else it stops), compiles the result and refuses anything but its TO pin.  Nothing else in the file moves.

  1  api_pad_amir_board: one line after `b = _s446_board_filter(con, b, u)` -- `b = _s521_stage_proof(con, b)`, for EVERY login.
  2  _s444_renames: ONLY the line `ready = (_proof_state(con, d).get("state") == "done")` -- ready is now what amir_stage says
     (stage B, C or done; None or a raise -> False, as before).  Its 10-minute cache and its n_open count are unchanged.
  3  a new S521 block at the end of the file: _s521_stage_proof(con, b) and its two helpers -- the board's proof line (section 2) and
     its renames gate (section 3c) are the stage's, as on his card.

WHY (F-838): after S520 Amir's card said "Orthotic: sab sahi" while his board (section 2, from _proof_state through _s436_board_extra)
still said "Marg = shelf: 26 of 28 · 2 to correct: ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST" -- two judgments of one fact
(charter rule 2); following the board would have spoiled two items that are right in Marg.  _proof_state itself, the owner's hub (step 5)
and every other page are not changed.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import os
import sys

PINS = {"stock_app.py": ("1f43f47ea288c8bba3750b78ba4cef9b", "c0f0623f7d540bbdedb4369aa459405a")}


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


# ---- 1: the call, for every login ------------------------------------------------------------------------------------------------------
A1 = "    b = _s446_board_filter(con, b, u)                     # S446 (D649): a login that is not the checker sees its stage only\n"
N1 = A1 + "    b = _s521_stage_proof(con, b)                          # S521 (F-838): the board's proof line and renames gate are the stage's, as on his card\n"

# ---- 2: his step-6 rename duty asks the stage, not _proof_state ----------------------------------------------------------------------
A2 = "            ready = (_proof_state(con, d).get(\"state\") == \"done\")\n"
N2 = "            ready = ((amir_stage(con, cid) or {}).get(\"stage\") in (\"B\", \"C\", \"done\"))   # S521 (F-838): the board's proof line and renames gate are the stage's, as on his card\n"

# ---- 3: the new block, at the end of the file ------------------------------------------------------------------------------------------
A3 = "# ---- S488_DATES_AND_WAITS end ---------------------------------------------------------------------------------------------------------\n"
N3 = A3 + '''

# ==========================================================================================================================================
# S521_AMIR_BOARD_STAGE_PROOF (11-Oct-2026, F-838): the board's proof line and renames gate are the stage's, as on his card.
#   Section 2 of Amir's board ("Marg = shelf?") came from _proof_state -- the whole count's proof on the FIRST closing after the vouchers,
#   through _s436_board_extra -- while his card reads amir_stage / _s446_proof (S520: proven on the first OR the newest closing).  Two
#   judgments of one fact (charter rule 2): after S520 the card said "Orthotic: sab sahi" and the board still named two items to correct
#   that are right in Marg.  Now api_pad_amir_board asks the stage, for EVERY login, so the owner's board says the same as Amir's; and
#   _s444_renames (his step-6 rename duty) asks the stage too.  _proof_state itself, the owner's hub (step 5) and every other page are
#   not changed.  The extra amir_stage call on an owner read is accepted: its writes are the once-only stage events his own card causes.
# ==========================================================================================================================================
S521_KIT = "S521_AMIR_BOARD_STAGE_PROOF"
S521_RENAMES_WAIT_HI = "Naam badalna \\u2014 orthotic voucher Marg mein sahi hone ke baad"           # _s446_board_filter's own wording
S521_EXPORT_HI = "Abhi baaki \\u2014 voucher daal diye, Marg ka agla closing stock export aane dijiye"   # when S488's reason tail is empty


def _s521_wrong_hi(rows):
    """'Marg = shelf: N theek karna hai -- names' from the proof's not-ok rows: the same rows his card lists (12 names at most)."""
    names = []
    for r in rows or []:
        it = (r or {}).get("item")
        if it and it not in names:
            names.append(it)
    return "Marg = shelf: %d theek karna hai \\u2014 %s" % (len(names), ", ".join(names[:12]) + (" \\u2026" if len(names) > 12 else ""))


def _s521_export_hi(st):
    """'Abhi baaki -- ' + S488's reason (F-753) for the stage's waiting proof; today's words when the tail is empty or cannot be had."""
    try:
        tail = _s488_tail_hi(_s488_stage_proof(st))
    except Exception:                                          # noqa: BLE001
        tail = ""
    return ("Abhi baaki \\u2014 " + tail) if tail else S521_EXPORT_HI


def _s521_stage_proof(con, b):
    """S521 (F-838): the board's proof line and renames gate are the stage's, as on his card.  For every login.  The new values are built
    in local variables and assigned to b only at the end: when the stage cannot be had (None) or anything raises, b is returned as it came.
        A, vouchers open       wait    Abhi baaki -- pehle orthotic voucher Marg mein daaliye
        A, proof export        export  Abhi baaki -- <S488 reason tail>  (today's words when the tail is empty)
        A, proof wrong         wrong   Marg = shelf: N theek karna hai -- names   (the page's chip reads "Aa gaya")
        B, or done             done    Orthotic: sab sahi (the card's own words)
        C, a wrong lot         wrong   Marg = shelf: N theek karna hai -- names
        C, a lot waiting       export  Abhi baaki -- <S488 reason tail>
        C, else                done    Ab tak ke voucher Marg mein sahi
    renames_ready: False in stage A (with _s446_board_filter's wording), True in B, C or done (and renames_wait_hi emptied)."""
    try:
        st = amir_stage(con, b.get("count_id"))
        if not st:
            return b
        stage = st.get("stage")
        A, C = st.get("A") or {}, st.get("C") or {}
        AP = A.get("proof") or {}                              # None while vouchers are open
        state = hi = None
        if stage == "A":
            if int(A.get("open") or 0) > 0:
                state, hi = "wait", "Abhi baaki \\u2014 pehle orthotic voucher Marg mein daaliye"
            elif AP.get("state") == "export":
                state, hi = "export", _s521_export_hi(st)
            elif AP.get("state") == "wrong":
                state, hi = "wrong", _s521_wrong_hi(AP.get("rows"))
        elif stage in ("B", "done"):
            state, hi = "done", "Orthotic: sab sahi \\u2713"
        elif stage == "C":
            if C.get("wrong"):
                state, hi = "wrong", _s521_wrong_hi(C.get("wrong"))
            elif C.get("waiting_export"):
                state, hi = "export", _s521_export_hi(st)
            else:
                state, hi = "done", "Ab tak ke voucher Marg mein sahi \\u2713"
        ready = stage in ("B", "C", "done")
        wait_hi = "" if ready else S521_RENAMES_WAIT_HI
    except Exception:                                          # noqa: BLE001 -- the board never waits for its own line: b as it came
        return b
    if state is not None:
        b["proof_state"], b["proof_hi"] = state, hi
    b["renames_ready"], b["renames_wait_hi"] = ready, wait_hi
    return b
# ---- S521_AMIR_BOARD_STAGE_PROOF end -----------------------------------------------------------------------------------------------------
'''


def build(t):
    for n, (a, new) in enumerate(((A1, N1), (A2, N2), (A3, N3)), 1):
        if t.count(a) != 1:
            raise Stop("anchor %d occurs %d times (must be exactly 1)" % (n, t.count(a)))
    if not t.endswith(A3):
        raise Stop("the S488 end line is not the last line of the file this builder was written on")
    if "_s521_" in t:
        raise Stop("the file already carries an S521 edit")
    for a, new in ((A1, N1), (A2, N2), (A3, N3)):
        t = t.replace(a, new, 1)
    return t


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true", help="print the built md5 and accept it (packing the kit)")
    a = ap.parse_args(argv)
    name = "stock_app.py"
    frm, to = PINS[name]
    try:
        raw = open(os.path.join(a.finance, name), "rb").read()
        if md5(raw) != frm:
            raise Stop("%s is %s, not the FROM pin %s -- someone changed it since the brief" % (name, md5(raw), frm))
        if b"\r" in raw:
            raise Stop("%s carries carriage returns" % name)
        new = build(raw.decode("utf-8")).encode("utf-8")
        compile(new, name, "exec")
        if md5(new) != to and not a.print_to:
            raise Stop("%s built to %s, not the TO pin %s" % (name, md5(new), to))
    except Stop as e:
        print("STOP: %s" % e)
        return 2
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, name), "wb") as fh:
        fh.write(new)
    print("%s  %s -> %s  (%+d lines)" % (name, frm[:8], md5(new)[:8], new.count(b"\n") - raw.count(b"\n")))
    if a.print_to:
        print("   TO %s = %s" % (name, md5(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

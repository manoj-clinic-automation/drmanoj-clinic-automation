#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s536.py -- the builder of kit S536_AMIR_BOARD_D712 (12-Oct-2026; D712, D708; F-864).

    python3 -B make_s536.py --finance DIR --out DIR [--print-to]

Reads the LIVE files at their FROM pins (anything else: stop), makes anchored edits (each anchor must occur exactly once, else it
stops), compiles every python result, and writes the results into --out (nothing else is written).
With --print-to the built md5s are printed and accepted (packing the kit); without it every result must equal its TO pin (PINS.sh).

  stock_app.py     2.1: _amir_board_light's two `rest = dict(...)` lose the arrival key (D712: the arrival is the owner's Needs-you line,
                   one place); a comment line says so.
  stock_amir.html  2.2: restCard's arrival row removed whole; the header comment's section 4 no longer lists it.
  amir_day.py      2.3: needs_you_lines' "ordering can start" line only at stage C or done, dated by the root's first stage-C release
                   (else B's verification), in its own try.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import os
import sys

PINS = {
    "stock_app.py": "c626a46acf371b3a767756dc35743d57",
    "stock_amir.html": "8dd65e64aa2315da6c74909fe50c31c7",
    "amir_day.py": "262b0b814ec2b840012cd1988e420097",
}
TO_FILE = "PINS.sh"


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def rep(t, a, new, what):
    n = t.count(a)
    if n != 1:
        raise Stop("%s: anchor occurs %d times (must be exactly 1): %r" % (what, n, a[:120]))
    return t.replace(a, new, 1)


# ============================================================================================================== stock_app.py (2.1)
SA_EMPTY_OLD = "    rest = dict(plan=None, bill_pending=[], fixes=[])\n"
SA_EMPTY_NEW = ("    # S536 (D712): a reception arrival tap is the owner's Needs-you line (amir_day), never a row of this board -- the board sends\n"
                "    # the Sunday and the fixes only.\n"
                "    rest = dict(plan=None, fixes=[])\n")
SA_FULL_OLD = ('            rest = dict(plan=W.get("plan"), bill_pending=[dict(item=x.get("item"), text_hi=x.get("text_hi") or "") for x in (W.get("bill_pending") or [])],\n'
               '                        fixes=[dict(item=x.get("item"), fix=x.get("fix"), at_text=x.get("at_text") or "") for x in (W.get("fixes") or [])])\n')
SA_FULL_NEW = ('            rest = dict(plan=W.get("plan"),\n'
               '                        fixes=[dict(item=x.get("item"), fix=x.get("fix"), at_text=x.get("at_text") or "") for x in (W.get("fixes") or [])])\n')


def build_stock_app(t):
    t = rep(t, SA_EMPTY_OLD, SA_EMPTY_NEW, "stock_app: the empty rest of _amir_board_light")
    t = rep(t, SA_FULL_OLD, SA_FULL_NEW, "stock_app: the rest from amir_view (two lines)")
    return t


# ============================================================================================================== stock_amir.html (2.2)
HT_ROW_OLD = ("  (W.bill_pending||[]).forEach(x=>{ n++; h+='<div class=\"row\"><div><div class=\"it\">'+esc(x.item)+'</div><div class=\"q\">'+esc(x.text_hi)"
              "+' — maal aa gaya, Marg mein bill abhi nahi</div></div><div class=\"r\"><span class=\"chip warn\">bill entry</span></div></div>'; });\n")
HT_HEAD_OLD = "     4  Baaki kaam                          the Sunday, bill entry baaki, the traces' fixes\n"
HT_HEAD_NEW = ("     4  Baaki kaam                          the Sunday, the traces' fixes (S536, D712: a reception arrival tap is the owner's\n"
               "                                            line, never a row here)\n")


def build_html(t):
    t = rep(t, HT_ROW_OLD, "", "stock_amir.html: restCard's arrival row")
    t = rep(t, HT_HEAD_OLD, HT_HEAD_NEW, "stock_amir.html: the header comment's section 4")
    return t


# ============================================================================================================== amir_day.py (2.3)
AD_OLD = ('            bat = (st.get("B") or {}).get("verified_at")\n'
          '            if bat and _days_since(bat) is not None and _days_since(bat) <= 2:\n'
          '                out.append(dict(cls="warn", target="stock", text="Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (st["count_id"], _dm_hm(bat, time=False))))\n')
AD_NEW = ('            # S536: only once the count has passed the orthotic stages (C or done). The moment is the root\'s FIRST stage-C release --\n'
          '            # amir_stage releases the first medicine lot on the read that first finds A and B passed, and state() has just called it on\n'
          '            # this connection -- else B\'s verification (a count with no medicine batch goes straight to done). Its own try: a fault here\n'
          '            # drops this one line only. Read-only (amir_day writes no stage event).\n'
          '            try:\n'
          '                if st.get("stage") in ("C", "done"):\n'
          '                    r = con.execute("SELECT MIN(at) FROM stock_stage_event WHERE count_id=? AND stage=\'C\' AND event=\'release\'",\n'
          '                                    (int(st["count_id"]),)).fetchone()\n'
          '                    mom = (r[0] if r else None) or (st.get("B") or {}).get("verified_at")\n'
          '                    dd = _days_since(mom) if mom else None\n'
          '                    if dd is not None and dd <= 2:\n'
          '                        out.append(dict(cls="warn", target="stock", text="Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)"\n'
          '                                        % (st["count_id"], _dm_hm(mom, time=False))))\n'
          '            except Exception:                              # noqa: BLE001\n'
          '                pass\n')


def build_amir_day(t):
    return rep(t, AD_OLD, AD_NEW, "amir_day: needs_you_lines' ordering line")


def read_to(kit_dir):
    p = os.path.join(kit_dir, TO_FILE)
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith("TO[") and "]=" in line:
                k, v = line[3:].split("]=", 1)
                out[k] = v.strip()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true")
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    to = read_to(here)
    os.makedirs(a.out, exist_ok=True)
    builders = {"stock_app.py": build_stock_app, "stock_amir.html": build_html, "amir_day.py": build_amir_day}
    rc = 0
    for name, fn in builders.items():
        src = os.path.join(a.finance, name)
        raw = open(src, "rb").read()
        m0 = md5(raw)
        if m0 != PINS[name]:
            print("!! %s is %s, not its FROM pin %s -- stopped" % (src, m0, PINS[name]))
            return 2
        try:
            new = fn(raw.decode("utf-8"))
        except Stop as e:
            print("!! %s: %s" % (name, e))
            return 2
        if name.endswith(".py"):
            try:
                compile(new, name, "exec")
            except SyntaxError as e:
                print("!! %s does not compile after the edits: %s" % (name, e))
                return 2
        nb = new.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(nb)
        m = md5(nb)
        want = to.get(name)
        print("   %-15s %s -> %s  (%+d lines)%s" % (name, PINS[name][:8], m, new.count("\n") - raw.decode("utf-8").count("\n"),
                                                    "" if (a.print_to or want == m) else "   !! not the kit's TO pin %s" % want))
        if not a.print_to and want != m:
            rc = 3
    return rc


if __name__ == "__main__":
    sys.exit(main())

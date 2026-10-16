#!/usr/bin/env python3
"""lines_s566.py -- a frozen earlier walk, re-run on the S566 files, with exactly the lines S566's TO pins force in their new form.

    python3 lines_s566.py s563|s559 <the frozen walk_s563.py / the S563-adapted walk_s559 copy> <out: a /tmp copy>

The earlier kits are never edited (a published kit is frozen); the copy is written to /tmp. Each line below must be found
exactly once, or this refuses (exit 1) and the installer stops.
  s563 F4 -- S566 item 1 (S563-K1-N5): the blank fix's Restore of a paper with the same supplier, number and amount as an
             accepted one is now refused BEFORE anything is written ('This looks like Z-2031-RFN0 — open it instead.'): the
             paper stays set aside, nothing cleared, no restore audited -- and still never two accepted copies.
  s559 O3 -- S566 item 8: the grey line on /desk?open= now says why -- a pharmacy paper: _visible's reason ('... is a pharmacy
             paper ...'); an unknown id: 'No paper <typed>'.
  s559 O4 -- S566 item 8: a manager's Personal paper: _visible's reason ('Personal papers are the owner's alone.').
(s559 is applied to the copy lines_s563.py s559 already wrote: S563's J1 / J3 lines stay in S563's form.)"""
import sys

LINES = {
    "s563": (
        ("lambda: c_fx == 200 and r_fx[\"status\"] == \"draft\" and r_fx[\"approved_by\"] is None and r_fx[\"approved_at\"] is None\n"
         "       and aud(f_bl2, \"desk_blank_restored\") and row(f_bl2)[\"status\"] != \"approved\",",
         "lambda: c_fx == 400 and (j_fx.get(\"error\") or \"\").endswith(\"— open it instead.\") and r_fx[\"status\"] == \"rejected\"\n"
         "       and r_fx[\"approved_by\"] == \"Walk Blank\" and not aud(f_bl2, \"desk_blank_restored\") and row(f_bl2)[\"status\"] != \"approved\","),
    ),
    "s559": (
        ("\"That paper can't be opened here\" in d_ph and cfg_of(d_unk).get(\"open\") == 0\n"
         "       and \"That paper can't be opened here\" in d_unk",
         "\"s559cant\" in d_ph and \"is a pharmacy paper\" in d_ph and cfg_of(d_unk).get(\"open\") == 0\n"
         "       and \"No paper 999999999\" in d_unk"),
        ("\"That paper can't be opened here\" in d_pe_m",
         "\"s559cant\" in d_pe_m and \"Personal papers are the owner\" in d_pe_m"),
    ),
}


def main():
    which, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    s = open(src, encoding="utf-8").read()
    for old, new in LINES[which]:
        n = s.count(old)
        if n != 1:
            sys.exit("REFUSED: the %s walk line %r was found %d times, not once" % (which, old[:60], n))
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(s)
    print("%s walk copied to %s with its %d line%s in S566's form" % (which.upper(), out, len(LINES[which]), "" if len(LINES[which]) == 1 else "s"))


if __name__ == "__main__":
    main()

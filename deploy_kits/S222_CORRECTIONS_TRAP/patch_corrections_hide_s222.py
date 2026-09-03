#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_corrections_hide_s222.py -- S222 star-1-2 part A: stop drawing Amir a trap.

THE OWNER, at the S221 close: hide the ledger-check and transfer controls the corrections
page still draws for a viewer -- "they refuse him safely; a control that refuses is a trap".

He is right, and it is the same shape as F-296. S221 gave Amir `viewer` so he could work the
corrections desk. The BOTTOM half of that page is the owner's: a ledger check for one date,
and the control that records an owner transfer. Both are checker-only on the server and were
re-verified as such at S221 -- so nothing is exposed. What is wrong is that a purchase man is
shown two controls, in his own workplace, that exist to tell him no.

WHAT THIS DOES, AND WHAT IT DELIBERATELY DOES NOT

It hides the block, and it hides it by ASKING THE SERVER, not by being told a role. The page
already calls `/finance/darpan/api/ledger-check`; that route is checker-only and S221's own
patcher verified it still is. So the page asks it once on load: a 403 means "not yours" and the
block stays hidden; anything else shows it.

  * The block is hidden IN THE MARKUP and revealed afterwards, so a viewer never sees a flash
    of controls he must not use.
  * A NETWORK ERROR SHOWS THE BLOCK. That is deliberate. The server is the real gate and is
    unchanged by this kit, so failing open cannot expose anything -- while failing closed
    would silently rob the owner of his own control on a bad connection. This page-level hide
    is about not drawing a trap, never about permission.
  * NO server file is touched. No route changes. No role is read client-side, because this
    page has no honest way to learn one: it carries no `data-user`, and reading one would have
    meant editing `darpan_app.py`, whose live bytes no store holds (see the S222 paper on the
    `darpan_corrections.html` pin conflict). Guessing at a file nobody can reproduce is how
    this session already produced one false RED. Not twice.

COST, stated plainly: one extra GET per page load, for the owner only. For a viewer the route
refuses at its guard before doing any work.

Target: /root/finance/darpan_corrections.html   (live pin f2f6f60ed57681c9fde7ddbbc4dc90d7,
        read from the box at the S222 open -- and NOT the b3cfd86f... the Register's pin table
        still names. That row is stale and is corrected at this close.)

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_corrections_hide_s222.py
Offline:         DC_PATH=./darpan_corrections.html python3 -B patch_corrections_hide_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('DC_PATH', '/root/finance/darpan_corrections.html')
MARK = "S222 star-1-2"
EXPECT_FROM = "f2f6f60ed57681c9fde7ddbbc4dc90d7"


A_OLD = '''<div class="sec">
<h1>Ledger check and owner transfer</h1>
'''

A_NEW = '''<!-- S222 star-1-2 -- hidden until the server says this login may use it.
     Revealed by the script at the foot of this page. Both controls inside are
     checker-only on the server; this only stops a viewer being SHOWN them. -->
<div class="sec" id="ownerOnly" hidden style="display:none">
<h1>Ledger check and owner transfer</h1>
'''


B_OLD = '''fillParties();
</script>
'''

B_NEW = '''fillParties();

/* S222 star-1-2 -- "a control that refuses is a trap" (the owner, S221 close).
   Ask the server one question instead of guessing at a role: may this login run
   the ledger check? That route is checker-only and S221's patcher verified it
   still is. 403 -> the block stays hidden. Anything else -> show it.
   AN ERROR SHOWS IT. Deliberate: the server is the real gate and is untouched by
   this kit, so failing open exposes nothing, while failing closed would rob the
   owner of his own control on a bad connection. */
(function(){
  var el = document.getElementById("ownerOnly");
  if (!el) return;
  function show(){ el.hidden = false; el.style.display = ""; }
  try {
    fetch("/finance/darpan/api/ledger-check", {cache:"no-store"})
      .then(function(r){ if (r.status !== 403) show(); })
      .catch(function(){ show(); });
  } catch (e) { show(); }
})();
</script>
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0

    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit(
            "REFUSED: this file is %s, not the %s this kit was built against. NOTHING was "
            "changed. Send me that hash -- the anchors are written for the bytes I have."
            % (before, EXPECT_FROM))

    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_trap_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)

    # the page must not come out with unbalanced script tags -- the S221 page
    # patcher's own guard, kept
    if out.count("<script") != src.count("<script") or \
            out.count("</script>") != src.count("</script>"):
        raise SystemExit("REFUSED: the script tags came out unbalanced. NOTHING was written.")

    open(TARGET, "w", encoding="utf-8").write(out)
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    print("next     hard-reload the page as yourself; the block must still be there")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_cp11_contrast.py - CP-1.1 step 2: the dropdown contrast (S216)
======================================================================
Base = the S216 step-1 page (guard live, pin 1e4d25d4...).
Five ANCHORED patches, each must match EXACTLY ONCE. CSS only.
No script, no wording, no consent logic is touched.

WHY:
  The page is dark (--bg:#263433, --ink:#E7EEEC near-white) and selects are
  styled color:var(--ink). The word `color-scheme` appears ZERO times in the
  file and there is NO option{} rule at all, so Chrome paints the NATIVE popup
  list on the OS default WHITE while keeping the near-white option text -
  invisible until the highlight bar paints behind a row. Every dropdown on the
  page is affected. Textareas (.docbox) had no background or colour either.

PRINTING IS PROTECTED: color-scheme reverts to light inside @media print and on
.consent-out, so the consent still prints black on white.
"""
import sys, hashlib

BASE_MD5 = "1e4d25d4ac6fa41729653527616b6299"

A_ROOT = (":root{--bg:#263433;--card:#2F3E3D;--ink:#E7EEEC;--muted:#9DB0AC;--blue:#4E88B8;"
          "--green:#74C295;--accent:#E0966B;--line:#3D4F4D;--shadow:0 1px 2px rgba(0,0,0,.25),"
          "0 6px 18px rgba(0,0,0,.30);--warn:#E0B36A;--warnbg:rgba(224,179,106,.14);"
          "--lowbg:rgba(227,154,150,.14);--low:#E39A96;--wa:#25D366}")

A_SELECT = "select{border:none;background:transparent;font-size:14px;font-weight:600;color:var(--ink)}"

A_DOCBOX = (".docbox{width:100%;min-height:230px;padding:10px 12px;border:1px solid var(--line);"
            "border-radius:10px;font-size:14px;font-family:inherit;line-height:1.5;resize:vertical}")

A_CONSENTOUT = (".consent-out{background:#fff;border:1px solid var(--line);border-radius:8px;"
                "padding:16px 18px;margin-top:10px;font-size:14px;line-height:1.6}")

A_PRINT = "@media print{\n  body{background:#fff}"

N_ROOT = A_ROOT + """
/* ---- CP-1.1 step 2 (S216): native controls follow the dark theme --------
   Without color-scheme the browser paints select popups, date pickers,
   checkboxes and scrollbars on the OS default WHITE, so near-white option
   text was unreadable until highlighted. */
html{color-scheme:dark}
:root{--line2:#5A706E}   /* mid-strength edge: 2.12:1 on --card, 2.45:1 on --bg */
select,option,optgroup{background-color:var(--card);color:var(--ink)}
textarea,input{color-scheme:dark}
/* No option:checked override: measured white-on-var(--blue) at only 3.79:1.
   color-scheme:dark makes the browser draw its own contrast-tested highlight. */"""

N_SELECT = ("select{border:none;background:transparent;font-size:14px;font-weight:600;"
            "color:var(--ink)}\n"
            "select option{background-color:var(--card);color:var(--ink);font-weight:500}")

N_DOCBOX = (".docbox{width:100%;min-height:230px;padding:10px 12px;border:1px solid var(--line2);"
            "border-radius:10px;font-size:14px;font-family:inherit;line-height:1.5;"
            "resize:vertical;background:var(--bg);color:var(--ink)}")
# --bg, not --card: on --card the box is the SAME fill as the panel behind it
# and its 1px --line border sits at 1.29:1, so the field loses its edge.
# --bg is the inset step the page already uses; text lands at 11:1.

N_CONSENTOUT = (".consent-out{background:#fff;border:1px solid var(--line);border-radius:8px;"
                "padding:16px 18px;margin-top:10px;font-size:14px;line-height:1.6;"
                "color-scheme:light}")

N_PRINT = "@media print{\n  :root,html,body{color-scheme:light}\n  body{background:#fff}"


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)

    n = [0]; ref = [src]
    def patch(old, new, label):
        c = ref[0].count(old)
        assert c == 1, "ANCHOR FAIL (%s): found %d, expected 1" % (label, c)
        ref[0] = ref[0].replace(old, new); n[0] += 1

    patch(A_ROOT,       N_ROOT,       "C1 color-scheme + option colours")
    patch(A_SELECT,     N_SELECT,     "C2 select option belt-and-braces")
    patch(A_DOCBOX,     N_DOCBOX,     "C3 template boxes themed")
    patch(A_CONSENTOUT, N_CONSENTOUT, "C4 consent paper stays light")
    patch(A_PRINT,      N_PRINT,      "C5 print reverts to light")

    out = ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())
    print("bytes: %d -> %d" % (len(src.encode()), len(out.encode())))

if __name__ == "__main__":
    main()

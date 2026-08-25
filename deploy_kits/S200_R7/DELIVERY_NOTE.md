# S200_R7 — the month-end flow made intuitive (owner's UX rulings, all of them)

| file | was | now |
|---|---|---|
| `/root/staff_register/salary_policy.py` | `9b14c340…` (R6) | `c9dd846ef5bc971b905ac33e2ad6eded` (v1.5) |
| `/root/staff_register/staff_register.py` | `40efbac3…` (R5) | `f85a4b0663ee0028c967cefec716bd12` (v0.12) |
| `manual_advances_2026-07.json` | — | **NOT in this kit** — salary data never enters the repo (D320/F-31, the publish guard caught it). Placed on the box by paste. |

## What each complaint became

- **"option to approve on the pages itself"** → Sheet 1 and Sheet 2 each carry an APPROVE strip
  at the top: reviewed-and-correct? one press, confirm, and you return to the SAME page with the
  strip now showing who approved and when, plus a Lock-desk door. The lock desk shows both
  sheets with "open & approve" doors AND direct approve buttons (confirm warns you're approving
  without opening). The sign-off itself stays a deliberate human press — D337 unbowed; it just
  stopped needing a page hop.
- **"salary sheets… marked as finalised or not, clearly"** → the preview (Sheets 3+4) now opens
  under a strip: 🔒 FINALISED — locked by … / ⚠️ NOT FINAL — working preview, with a Lock-desk
  door; plus a Print/save-as-PDF button (the export).
- **"scenario is very confusing"** → button renamed **What-if**, and the page opens with a plain
  sandbox explanation: re-runs the month's REAL punches under trial numbers, saves nothing,
  touches no pay; live rules live in Settings.
- **"sheet 1 — fix absents link to stand out"** → a proper orange button: 🔧 FIX ABSENTS — the
  whole month on one page.
- **"fix-absents… staff days make expandable"** → every staff block is a collapsible card
  (first one open), header carrying absent/corrected/still-absent; same for the undo section.
- **"sheet 2 — july advances populated… as provided in the google sheet"** → a new Sheet-2
  table, "Advances settled OUTSIDE the ledger (owner's record)", fed from
  `manual_advances_<ym>.json`. July's eight rows go to the box by PASTE (the publish guard rightly refused them in git) (Shivani noted 2,800 with her
  parked 3,000; Surendra noted with the held Rs 516 question). Display-only — already deducted
  when paid, never touches NET. Future months: drop a file of the same shape, or better, use
  the ledger so it flows itself.
- **"darpan page mentions only one tranche"** → REAL BUG FIXED: the open-loans table filtered to
  interest-bearing rows only, hiding every non-interest tranche. ALL open advances now list
  (interest ones tagged), and his page carries doors: 📜 Complete ledger statement · 💵 Advances
  page (where PENDING items like the unsigned ₹20,000 SPECIAL live) · 🎁 Perks.
- **"all small fonts should go"** → sheet tables 13.5→15px, desk 15→16px, notes/date-links up,
  early-big page padded and enlarged.
- **Early-big count**: the desk button already shows only UNRULED events — refresh after saving
  rulings and the number goes.

## Proof offline
Hash-gated bases; every anchor exactly once; py_compile + pyflakes clean; register selftest
full-suite GREEN; policy selftest PASS; and a render harness proved: approve strips appear on
screen and never in print, the manual-advances table renders on the main page only, BOTH Darpan
tranches list with the interest tag exactly once, the statement/advances/perks doors present,
FINAL vs NOT-FINAL strips render, and the fix-absents cards keep every form field the selftest
watches.

## Install
    cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R7/INSTALL_S200_R7.sh

Then the July run-through: desk → Sheet 1 (read, APPROVE on-page) → Sheet 2 (read July's
advances there, APPROVE on-page) → desk turns Ready → LOCK.

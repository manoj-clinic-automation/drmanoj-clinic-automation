# S216_AYUSH_NAMES — readable Ayushman package names

**Page only, display only.** `casepack_portal.py` unchanged and NOT installed.

## The fault, measured

The card headline was `a.name || a.proc` — **the sub-option alone**, with the
parent package name never shown. Across `BUNDLE.ayush` (**138 rows, 73 parent
procedures**):

| | |
|---|---|
| headlines that are a bare body part or qualifier, meaningless alone | **28** |
| headlines of 12 characters or fewer | **59 of 138** |

Cards read *"Upper Limbs"*, *"Spikas"*, *"Long bone"*, *"Without plaster"*.
The parent name was in the data all along.

## What changed

- The parent package is shown as a small kicker line above the variant.
- Where the parent already ends with the variant **and the package has no
  sibling variants**, the parent is shown alone instead. The sibling guard is
  what keeps *Spikas* and *Jackets* — same parent, different rates — apart;
  a naive join collapsed them to one string.
- `w/` expands to `with` in the display text only.
- The filed name appears as a small **"Filed as:"** line **only when it
  actually differs** from what he is reading. **97 of 138 packages say the same
  thing twice**, so the line is hidden on those; it survives where it matters,
  e.g. the government's plural *"Skeletal Tractions"* and its typo
  *"Duputryen's"*, which the screen label spells correctly.
- The price column is anchored so it does not shift on cards that gained a
  kicker.

## What is NOT touched — the money path

`ayushBlock()` still prints the government's own `hpkg` / `hproc` **verbatim**,
typos included. Copy details, WhatsApp and the record detail are byte-unchanged.
`ayushKey()` is unchanged, so existing tray selections keep their identity.
**Prettifying the claim identity would be a money fault, not a cosmetic one.**

## Cost, measured

Card height before: uniform 190px. After: 188px (folded), 196px (kicker only),
221px (kicker + a genuinely different filed name). Because the duplicate line
is suppressed on 97 of 138 packages, the typical card grows by **6px**, not 31.
Price offset from card top is now a steady 15px on every card.

## Proof

| gate | result |
|---|---|
| `selftest_casepack.py` | **32/32** unchanged |
| `RENDER_TEST_casepack.py` | **17/17** unchanged |
| `GUARD_WALK_cp11.py` | **19/19** unchanged |
| `CONTRAST_TEST_cp11.py` | **9/9** unchanged |
| `AYUSH_NAME_WALK.py` (new) | **14/14** |

The naming walk asserts the reading path improved AND that the claim path did
not move — including that the government typo is still printed and that Spikas
and Jackets remain two cards with their own rates.

## Install

    cd /root/deploy/repo && git pull && bash deploy_kits/S216_AYUSH_NAMES/install_ayush.sh

Base `3cac3904…` → new `af850a87…`.

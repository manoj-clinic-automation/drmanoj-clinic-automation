# S216_CP11_CONTRAST — CP-1.1 step 2: the dropdown contrast

**Page only, CSS only.** No script, no wording, no consent logic is touched.
`casepack_portal.py` is unchanged and NOT installed.

## The fault, measured

The page is dark (`--bg:#263433`, `--ink:#E7EEEC` near-white) and selects are
styled `color:var(--ink)`. The word **`color-scheme` appeared ZERO times** in
the file and there was **no `option{}` rule at all**, so Chrome painted the
native popup list on the OS default **white** while keeping the near-white
option text — invisible until the highlight bar painted behind a row. Every
dropdown on the page was affected. The three template textareas had no
background or colour set either, so they rendered as bright white slabs in a
dark page.

Reverse proof: `CONTRAST_TEST_cp11.py` scores **3 of 9** on the live page and
reports `color-scheme: normal`.

## What changed — five anchored CSS patches

1. `html{color-scheme:dark}` — native popups, date pickers, checkboxes and
   scrollbars now follow the theme.
2. `select,option,optgroup` given explicit theme colours.
3. `.docbox` (the three template boxes) themed as an **inset well**:
   `--bg` fill, text at **11:1**, with a new `--line2:#5A706E` edge.
4. `.consent-out` pinned to `color-scheme:light` — the consent paper stays a
   white document.
5. `@media print` reverts the root to light, so printing is unaffected.

## Two faults found during the build, both by measurement, both fixed

- The first draft set `option:checked` to white on `var(--blue)` — **measured
  at 3.79:1**, below the 4.5 minimum. The override was removed entirely;
  `color-scheme:dark` lets the browser draw its own contrast-tested highlight.
  Every dropdown now measures **9.50:1**.
- The themed textarea was first given `var(--card)` — the **same fill as the
  panel behind it**, leaving a 1.29:1 hairline to carry the whole boundary, so
  the field lost its edge. Changed to the darker `--bg` with a stronger
  `--line2` border. Caught by reading the rendered screen, not by a check.

## Proof

| gate | result |
|---|---|
| `selftest_casepack.py` | **32/32** unchanged |
| `RENDER_TEST_casepack.py` | **17/17** unchanged |
| `GUARD_WALK_cp11.py` (step 1) | **19/19** unchanged |
| `CONTRAST_TEST_cp11.py` (new) | **9/9** — measures real ratios, not strings |
| same test on the live page | **3/9** |

`CONTRAST_TEST_cp11.py` computes WCAG contrast ratios from computed styles in a
real browser and asserts ≥4.5:1, checks the consent paper still measures 21:1
black-on-white, and emulates print media to prove printing stays light.

Playwright is on neither the clinic PC nor the VPS; the browser scripts exit 2
(SKIP) there and the gate treats SKIP as not-a-FAIL.

## Install

    cd /root/deploy/repo && git pull && bash deploy_kits/S216_CP11_CONTRAST/install_contrast.sh

Base `1e4d25d4…` → new `3cac3904…`.

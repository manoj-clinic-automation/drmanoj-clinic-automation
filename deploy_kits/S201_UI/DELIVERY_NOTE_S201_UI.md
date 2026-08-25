# S201_UI — the health page, redesigned + a real rendering fault fixed

**One file: `finance_app.py`. Smoke +3 exactly, fail set byte-identical.**

## 1. The fault (found in the owner's own saved copy of the live page)

The **Correction checklist** row rendered broken. Cause: the row is wrapped in
`<a class=row>` *and* its hint carried `Open the checklist` as a second `<a>`.
**Nested `<a>` is invalid HTML.** Every browser un-nests it — the outer anchor
is closed where the inner one opens, so the status dot was orphaned into its
own clickable strip and `.body` fell outside the row entirely.

Fix: a row that is itself a link strips anchors out of its hint — the row
already goes where the inner link went, so the tags are redundant. The words
are kept. **Asserted on the served bytes**, because an eye cannot police this
and a test can: no row anchor may contain another anchor.

## 2. The redesign — Clinic Design Language v1

The page was on pre-v1 styling (teal bar, 13px body, no kickers, no tabular
numerals). `Clinic_Design_Language_v1.md` says existing pages migrate
*"whenever a kit already touches them"* — `S201_HEALTH` just did.

- Warm-paper tokens verbatim from the doc; the ONE accent for links.
- **A status is never colour alone** — every row carries ✓ ⚠ ✗ ⓘ beside it.
- 15px/1.6 type, `tabular-nums`, 11px uppercase kickers.
- Sticky branded header (40px mark, clinic line) + section tabs with counts.
- **Three sections instead of one flat list**: *What needs you* (bad+warn) ·
  *Worth knowing* (info) · *Running normally* (ok). The eye lands on the job.
  An empty section is omitted, never an empty box.
- Prose folded into `<details class="help">` — the density valve.
- 46px floating back-to-top; 38px minimum tap targets.

## 3. It is now registered, so it cannot revert silently

`/finance/health` is added to the **F-130 `_DESIGN_V1_PAGES`** table as `True`.
That table asserts pre-v1 pages *negatively* on purpose: a page cannot change
design class without coming here and flipping its flag.

## 4. Verification

- Offline differential **+3 exactly**, fail set **byte-identical** (109 → 109,
  the known harness gap; both runs all-green on the live server's data).
- Rendered against the owner's real 19:52 rows: 11 rows, 9 clickable,
  **0 nested anchors**, all four v1 markers present, de-linked hint keeps
  its words and drops its tag.
- `py_compile` clean · `bash -n` on the whole installer (standing rule, F-126).

## 5. Not changed

Every check, threshold, state and link target is untouched. This kit changes
**how the page is drawn**, not what it says or what it decides.

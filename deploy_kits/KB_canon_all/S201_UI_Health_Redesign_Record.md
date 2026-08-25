# S201_UI — the health page: a rendering fault, and the design migration

**Kit `S201_UI` · `finance_app.py` `024399775bfd14844f299b3dfac4bb47` →
`3f72e9ad16d915fe5ced45c4e28a2248` · smoke **+3 exactly**, fail set byte-identical.
Built and delivered; install state recorded at the close.**

---

## 1. How it was found

The owner uploaded his own saved copy of the live `/finance/health` page (2026-08-25
19:52) while asking for a redesign. Reading the **served bytes** — not the generator —
showed the **Correction checklist** row rendering broken.

This is the second time in S201 that the owner's own uploaded HTML has surfaced a fault
invisible from the source side (S187 P2a found a doubled `</tbody>` the same way).
**Reading what the server actually sent is a distinct check from reading what builds it.**

## 2. The fault — nested `<a>`

Every mapped health row is wrapped in `<a class=row>`. The `corrlist` row's *hint* also
carried a link:

```html
<a class=row href="/finance/marg-worklist">        <-- outer
   ...<div class=hint><a href="/finance/marg-worklist">Open the checklist</a> ...
```

**Nested `<a>` is invalid HTML.** No browser renders it as written: the parser closes the
outer anchor at the point the inner one opens. The result in the live DOM was an orphaned
status dot as its own clickable strip, with `.body` falling *outside* the row:

```html
<a class="row" href="..."><div class="dot" style="background:#9a6a00"></div></a>
<div class="body">…</div><div class="go">→</div>
```

**Why it survived:** the row was rendered, the link worked, the text was present. The
S198 selftest counted rows and counted clickable rows — both counts were still right. The
only symptom was the *shape* of one row, which no assertion described.

**Fix.** A row that is itself a link strips anchors out of its hint — the row already goes
where the inner link went, so the tags are redundant; the words are kept:

```python
def _delink(txt):
    return re.sub(r"</?a\b[^>]*>", "", txt or "")
```

**And it is now asserted on the served bytes**, because an eye cannot police this and a
test can:

```python
check("S201: no row anchor contains another anchor …", not _nested_anchor(_ht))
check("S201: a de-linked hint keeps its text", ("Open the checklist" in _ht))
```

## 3. The redesign — Clinic Design Language v1

The page was still pre-v1: teal bar, 13px body, no kickers, no tabular numerals.
`Clinic_Design_Language_v1.md` §5 says existing pages migrate *"whenever a kit already
touches them, never as gratuitous rebuilds"* — `S201_HEALTH` had just touched it, so this
is the sanctioned moment, not a gratuitous rebuild.

| v1 requirement | Applied |
|---|---|
| Tokens verbatim, warm paper, ONE accent | `:root` copied from the doc |
| **Status never colour alone** | every row carries ✓ ⚠ ✗ ⓘ beside its mark |
| 15px/1.6, tabular numerals, 11px uppercase kickers | yes |
| Sticky branded header + section tabs | 40px mark, clinic line, tabs with counts |
| Folded `<details class="help">` | the page's prose moved inside it |
| 46px floating back-to-top | `id="toTop"`, appears after 500px |
| Buttons ≥38px | Hub button and `<summary>` both 38px |

**The one structural change:** a single flat list became **three sections** —
*What needs you* (bad+warn) · *Worth knowing* (info) · *Running normally* (ok). An empty
section is omitted rather than drawn as an empty box. The page's job is "is anything wrong
right now"; the eye should land on the answer, not scan eleven equal rows for it.

This also completes what `S201_HEALTH` began: that kit stopped the review queue driving
the tile; this one stops it *looking* like the failures above it.

## 4. Registered, so it cannot revert silently

`/finance/health` is added to the **F-130 `_DESIGN_V1_PAGES`** table as `True`:

```python
("/finance/approvals", "checker", True),   # S187_H1b / H1c
("/finance/health",    "checker", True),   # S201_UI -- migrated
```

That table asserts pre-v1 pages **negatively** on purpose — a page cannot change design
class without coming here and flipping its flag. Before this kit `/finance/health` was not
in the table at all: it was neither protected nor recorded, which is how it sat on pre-v1
styling for fourteen sessions without anything noticing.

## 5. Verification

- Offline differential **+3 exactly** (689 → 692 offline); fail set **byte-identical**
  (109 → 109 — the known harness-data gap; the live server runs all-green).
- Rendered against the owner's **real 19:52 rows**: 11 rows, 9 clickable,
  **0 nested anchors**, all four v1 markers present, de-linked hint keeps its words and
  drops its tag.
- `py_compile` clean · `bash -n` on the whole installer (standing rule after F-126).

## 6. Not changed

Every check, threshold, state, hint and link target is untouched. This kit changes **how
the page is drawn**, not what it says or what it decides.

---
*S201 · companion to `S201_HEALTH` · design authority: `Clinic_Design_Language_v1.md`*

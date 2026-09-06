# S226_SAFESTORE — the count made hard to lose

The owner put the counting page on hold and asked for a verified check before
anyone types into it again. This is that check, and what it found.

## 1 · The bug that caused the hold — mine, and the worst this page has had

An entry made by pressing **OK** stored the total and nothing else. From
`S226_REVISIT` an already-counted item opened *filled in* when it was searched
for — and with no strips/loose to fill from, it opened with **two empty boxes**.
`calc()` then read those empty boxes, computed **0**, and saved it.

**Searching for an item you had already counted destroyed it.** `358` became
`0`, in silence, while the row on screen still showed 358 from the render
before. Every item counted before that install was exposed, because none of them
carried a breakdown. It was live for about twenty minutes of a real count.

Two changes, either of which alone would have prevented it:

* **A figure on record is never opened as a blank.** When the breakdown is
  missing it is derived from the total that *is* there.
* **Opening a row may not write.** `calc()` now takes a `typed` flag; the call
  that fires when a box is opened draws the total and saves nothing. Only a
  keystroke saves.

## 2 · Then the audit — every path that writes or deletes a counted figure

Four write sites, all now correct. Two structural silences remained, both the
same family — *a failure nobody is told about*:

**`save()` swallowed everything.** It was `try{...}catch(e){}`. If the browser
refused the write — storage full, private mode, a locked-down profile — every
entry was quietly dropped and nobody found out until a reload showed an empty
list. It now **reads the value back** to prove the write landed, keeps a good
copy beside it, and puts a red line across the top of the page that does not go
away: *"THIS BROWSER IS NOT SAVING YOUR ENTRIES. Stop counting and tell the
doctor now. Do not reload this page."*

**`load()` started a blank count on any parse error.** A truncated or corrupted
record meant an empty screen — and the next save wrote over the very bytes that
might have been recovered. It now sets the unreadable bytes aside under their own
key **before anything else is written**, restores from the backup copy when it
can, and says which happened. It never starts blank in silence.

## 3 · What the walk caught in the fix itself

Twice, which is the whole argument for driving a page instead of reading it.

**The rescue path killed the page.** The three state flags were declared with
`let`, *below* the line that calls `load()`. Function declarations hoist so
`load()` ran fine; `let` does not. The moment `load()` took its recovery path it
threw *"Cannot access 'LOAD_LOST' before initialization"* and the whole page
died. The happy path returned before ever touching those variables — so
everything looked perfect, and **the one path the code exists for was the only
one broken.**

**The warning was in the wrong place.** It painted into the counting screen. But
when the record cannot be read the counter lands on the **gate** — a blank form —
with the warning inside a hidden section, and would simply fill it in and count
straight over the top. It now sits at the top of the page, on whatever screen
they land on.

## 4 · Proof — 77 checks, all driven in a real browser at phone width

| walk | what it covers | result |
|---|---|---|
| `WALK_count_search_s226.py` | the search, revisiting a counted item, adjusting it when more stock turns up, and **the destroyer: an old entry is not damaged by looking at it** | **34 / 34** |
| `WALK_submit_flow_s226.py` | report, send, the ledger rows read back, the sealed finding, the frozen horizon, and a reload after sending | **30 / 30** |
| `WALK_safestore_s226.py` | a browser that refuses to save; a damaged record recovered from the backup; nothing readable anywhere | **13 / 13** |

## 5 · What is still true, and worth saying plainly

**The count still lives in one browser.** Everything above makes losing it loud
instead of silent, and recoverable instead of final — but it does not move the
record off that machine. The durable answer is saving each entry to the server as
it is typed, which is built next and is a bigger change than a page swap.

Until then the honest position is: this page will now tell you when something is
wrong, and it will not destroy an entry by being looked at.

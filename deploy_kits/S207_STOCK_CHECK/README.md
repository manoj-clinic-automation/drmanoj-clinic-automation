# S207_STOCK_CHECK — the staff stock count, generated from the archive

**Staged, not installed.** Reads `MargArchive`, writes one self-contained HTML file into
`D:\Downloads\margsync\_analysis\STOCK_CHECK.html`. Nothing live is touched, nothing is sent.

```
python3 build_stock_check.py             # rebuild from the newest exports
python3 build_stock_check.py --selftest  # 14 checks, needs no data
```

## Why a generator and not a page

The owner asked for it to *"keep this updated with latest data"*. A page edited by hand goes stale
the day after it is written and **nothing about it looks stale**. This reads whatever is in the
archive today, so refreshing the count sheet after a new stock export is one command.

## The rules built into it

**Marg's unit label is not trusted.** 27 orthotics — arm slings, clavicle braces — are labelled
`TAB.` in the item master. **The pack size decides** whether a thing is counted in strips or in
pieces. Same rule as `units.py` and the reconciliation.

**The F-235 guard.** A category-filtered export (orthotics, 81 rows) carries the same store name,
the same as-on date and a byte-identical header to the full 377-row one — Marg records no category
marker anywhere. So the universe is the **largest** export for the newest date, never the latest
file; the filtered one only marks which items are orthotic.

**An unknown expiry sorts last.** Batches are offered oldest-expiry-first for FEFO. A batch whose
expiry could not be parsed must never be presented as the one to sell next.

**No per-batch expected figure is invented.** Marg holds no per-batch shelf quantity. The page says
so on screen and asks only what was found.

## What the dummy run found — every one of these is fixed and re-tested

The page was driven end to end in a real browser at phone width, as staff, twice.

| found | fix |
|---|---|
| typing `-1` strips gave **"Counted −5"** — `min="0"` does not stop a typed value | every quantity clamps at zero |
| batch quantities summing to 33 sat beside a total of 23 and **nothing said a word** | the batch sum is checked against the count and the disagreement is shown |
| no way to reconcile that sum — stock bought before 1-Apr has no batch on record | a **"not on this list"** box |
| tapping **Not OK** twice **hid the boxes** a counter had just filled | Not OK always opens, never toggles |
| the report listed **all 368** uncounted item names | a count, and how many of them hold stock |
| the report ran to **66 characters** and scrolled off the right of a phone, taking the diff column with it | every line under 40, two lines per item, `pre-wrap` as the net |

**None of these would have been found by reading the code.** They were found by operating it.

## Two people, not one

The gate asks **who counted the stock** and **who is entering it here**, separately, because on the
floor one person often calls the shelf out while another types. **"Same person" is one tap**, since
that is the common case.

People: **Darpan · Shavez · Amir · Alisha**, plus **Someone else** with a free-text name for whoever
is actually there that day.

**Every entry carries both names**, and tapping the names in the top bar returns to the gate with
every count kept — a shift can change halfway through 376 items and the next stretch is attributed
to whoever is holding the phone. A difference counted by someone other than the current counter says
so on its own line in the report.

## The shared record — how the back end actually works

There is no server. The page **is** the record: it publishes a new version of itself carrying the
counts, using the artifact runtime capability (`capabilities: {artifact: {}}`).

**Counts live in two places, deliberately.** `localStorage` is the counter's own working copy and is
never lost — not to a reload, not to a conflict, not to a flat battery. The shared copy is what
everyone else sees, and it only changes when somebody taps **Share**. The button carries the gap:
`Share 12` means twelve counts on this phone that nobody else can see yet.

**Merging is by timestamp, newest wins, per item.** Two people counting the same item is not a clash
to resolve cleverly — the later count is taken and the report says who made it.

**The page carries its own source**, base64'd, with two holes: one for the shared counts and one for
the source itself. Filling the second hole with the same string reproduces the carrier exactly, so
version 40 can still publish version 41. Proven across three generations below.

**The four failure paths are each handled, and each was tested:**

| | |
|---|---|
| no capability (the file opened offline, or over WhatsApp) | button reads **"On this phone only"** and is disabled; counting works exactly as before |
| **conflict** — somebody shared first | routine, never retried. Every view reloads to the winner; this phone's counts are in `localStorage` and merge again on the way back |
| **not_writer / not_granted** — a view-only link | the viewer is told the view is read-only and pointed at Copy report, not shown a failure |
| anything else | the button offers another try |

### Proven end to end, three generations, three people

```
GEN 1  Darpan opens it, counts 3, shares   -> 3 shared
GEN 2  Alisha opens what Darpan published  -> sees "3 / 376" already done
       counts 2, shares                    -> 5 shared, Darpan's 3 intact
GEN 3  Amir opens that                     -> 6 shared, all three named
       376 items still embedded, no decay in size or data
```

## What it is not, yet

**Sharing is a tap, not automatic.** A counter has to press Share for the others to see their work.
Automatic publishing on every tick would mean a publish per item, a conflict storm, and dropped
edits — the tap is the batching.

**No live Marg feed.** Expected quantities come from the export the page was built against, stamped
at the top. A new stock export means re-running this builder and republishing.

*S207_STOCK_CHECK · staged 28-Aug-2026 · nothing live touched.*

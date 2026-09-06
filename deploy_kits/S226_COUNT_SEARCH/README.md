# S226_COUNT_SEARCH — the search box, and the crash it uncovered

## 1 · The crash. This is the important half.

The owner asked for a search box. Driving the page to prove the search, the walk
tapped the **Differences** chip and the list went blank with
*"Maximum call stack size exceeded"*. It did the same on the page that was
**already live**, so this was not the new code — it was there while Darpan and
Amir were counting.

**The mechanism.** `render()` empties the list, builds every row into a
`DocumentFragment`, and appends it only at the end — so all through a render
`list.children.length` is `0`. A row carrying a difference is rendered with its
entry box already open, and that path runs
`openEntry() → calc() → bump()`. The last line of `bump()` was:

```js
if(!list.children.length) render();
```

During a render that is always true. `render()` empties the list again, and it
recurses until the stack blows.

**Every filter that can show a differing item did this** — Differences, All, Has
stock, Nil. Only **To do** escaped, because it removes the counted row instead
of re-rendering. So the crash was invisible until the moment a counter marked
his first item *Not OK* and then looked at any other chip — which is exactly
what a person does before submitting. The owner's fear, in his own words, was
that staff would *"find flaws in it and reject it outright on the very first
one."* This was that flaw, and it was one tap away.

**The fix** is a re-entry guard: `render()` sets a flag, `bump()` will not call
`render()` while one is running. `bump()`'s auto-render is kept — it exists so
the "To do" list refills when it empties — it simply can no longer recurse.

*Found by driving the page during a live count, not by reading it.* That is the
second time this file has hidden a defect from a green gate.

## 2 · The search box

> *"It is not very practical for them to count the items in the same
> chronological order as it is mentioned in the page."* — the owner, mid-count

Of course it is not: the shelf has its own order and it is not ours. So the page
stops asking anyone to follow a list. Darpan calls a name, Amir types three or
four letters, the item is on screen.

Three decisions that make it work on a real counter:

* **A search looks at every item, whatever chip is selected.** Searching inside
  *To do* would hide an item the moment it was counted — which is precisely when
  someone wants to find it again to correct it.
* **The match ignores spaces, dots, quotes and case.** `primecast5` finds
  `PRIME CAST 5"`. Five people type that name five ways.
* **After OK, the box clears itself and keeps focus.** Otherwise the counter
  reaches up and clears it by hand between every single item.

The box sits in the sticky bar, so it stays on screen while the list scrolls.
It says what it is showing (*"Showing 1 item matching 'd3' — every item, counted
or not"*), and `Esc` or the × clears it.

## 3 · Proof — the page driven at phone width, mid-count

`WALK_count_search_s226.py` — **24 / 24**. It does the one thing that mattered
today: it seeds `localStorage` with a **half-finished count**, reloads the new
page over it, and checks nothing was lost — then drives the search the way a
counter would.

* the half-done count survives the swap; progress reads 2 / 6
* three letters find the item, and only that item
* `primecast5` finds `PRIME CAST 5"`
* an already-counted item is still findable
* OK saves, the box clears, progress moves
* Not OK opens the entry box; the typed figure is saved against the right item
* **all four chips render instead of blanking**; Differences shows both mismatches
* no JavaScript error anywhere in that

## 4 · Installing during a count

The count lives in `localStorage` on Amir's browser under
`sanj-stock-live-v1`. Replacing the page does not touch it — proven above by
reloading over a seeded half-count. **Amir reloads the page once and carries on
where he was.**

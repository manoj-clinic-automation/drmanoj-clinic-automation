# S189_E1a — the expense menu: free text is a choice, not a default

**Your words: "this free text entry will become the rogue spoiler." The survey
agreed, and found something worse underneath.**

## F-139 — the dropdown that pointed at nothing

The old page's staff selector was hardcoded: `value="1" Darpan · value="2"
Someone else` — ids into a `staff_ref` table that has been **empty since S179**
and that nothing in the app ever read or wrote. *"Someone else"* was a fake
staff member with id 2. Surveyed on the box before building: **zero expense
rows ever carried a staff_id** — the loaded gun was never fired, so F-139 is a
finding with no damage. From this kit, the **server resolves the identity** (the
F-84 rule: the client doesn't get to name who money attributes to), creating the
one real Darpan row lazily and ignoring any client-sent id.

## The menu

Per your ruling — Darpan draws only *his own* salary advance from the medical
cash — there is **no staff selector at all**:

| choice | what gets written |
|---|---|
| Medicine purchase (stock) | canonical label, verbatim |
| Shop expense (tea, cleaning, stationery) | canonical label |
| Transport / courier | canonical label |
| **My salary advance** | `salary_advance` + server-resolved staff row + `Salary advance - Darpan` — **the exact string the three S184 rows already carry**, so the whole history stays one queryable value |
| Other (write details) | his own words — **details required, refused blank** |

A skipped choice is **refused by the server**, never quietly written as an
uncategorised row. The menu lives in ONE place (the app); the selftest holds the
served page to every label, so the two copies cannot drift apart silently.
Checker pages untouched; an old cached page keeps working, its staff ids ignored.

## Projection, written before measuring

| | before | after |
|---|---|---|
| offline, unmigrated store | 486/488 | **507/509** |
| offline, custody-migrated store | 486/488 | **507/509** |
| your box | 488/488 | **509/509** |

Both offline runs measured **507/509 — held exactly**, same two seed artefacts,
21 new checks all green and all delta-disciplined (F-138 is one day old; not
committing it twice).

## Two hazards named, deliberately NOT fixed here (scope)

1. **A re-saved draft silently drops its earlier expenses.** `loadDay` never
   repopulates expense/movement/bill rows into the form, and the save is
   full-replacement. Pre-existing since S179; matters for the 14/15 Aug drafts
   if they carry expenses. Belongs on the backlog with its own number if you
   want one.
2. **When the D3 bridge lands, it must reconcile `PENDING_LEDGER_WIRING` rows
   against manually-entered ledger rows.** The ₹20,000 you'll enter in the
   Staff Ledger by hand will ALSO exist as a pending-wiring finance row —
   the bridge posting it again would be the double-count. Written down now,
   per F-137's lesson: read the consequence before the build, not after.

## Install

```
bash /root/deploy/repo/deploy_kits/S189_E1a/install_e1a.sh
```

Built on live `41788368…` (app) + `d3844bb9…` (page); ships
`7d6a87aa850df6c6678dc322d074de36` + `1c7d2dc3179f29e9de0b9fb0d77c6fe1`.

**Then the ₹30,000 walkthrough uses the menu:** ₹20,000 → *My salary advance* ·
₹10,000 → *Other* → "Salary July settled in cash (doctor's instruction)".

---

## E1b — why there are two kits with one page

**E1a refused itself at its own gate on your box — the projection said +21 and
the staged run went red on six checks.** Its selftest hunted a rehearsal day
forward from 1 April and landed on your store's first hole: a Sunday in early
April (Sundays are optional days, D322, so the legacy import never filed them),
**135 days back — beyond the 120-day backfill window** — where every save
answers `too_old` before the expense parse even runs. My offline store was
continuous, so the finder landed on 14 August there and everything passed:
**right data, wrong shape.**

Reproduced offline before fixing (the W1b discipline): a copy given a
beyond-window gap produced **exactly your six FAILs**; a mid-window gap
produced the partial set. The fix searches **backward from today** — the
direction the D2/F-129 blocks already use — and every check now prints the
server's actual error when it fails, so a future red says why instead of
making us derive it.

Rehearsed green on **four** store shapes: continuous · mid-window gap ·
beyond-window gap · custody-migrated — 507/509 each, same two seed artefacts.

The page is **byte-identical** to E1a's (`1c7d2dc3…`); only the selftest
changed. Ships app `5cb73ff83b591535053c7911026ecd8b`. Check count unchanged
at 509, so the installer still requires **+21 exactly**.

```
bash /root/deploy/repo/deploy_kits/S189_E1b/install_e1b.sh
```

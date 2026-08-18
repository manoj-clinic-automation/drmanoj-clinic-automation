# S189_W1b — F-138: a check measures its own delta, not the store

**App only, selftest only. The red you saw was the installer doing its job —
your books were restored untouched, and the migration itself was proven perfect
before the suite refused it.**

## What actually failed yesterday

Not the migration. `verify GREEN — location recorded, not one paisa moved` had
already printed. The red came from three checks **I wrote earlier this same
session**, which asserted the store's absolute state:

```
"parked with Dr Manoj must be Rs 0.00"
"custody inside this year must be exactly Rs 12,345.00"
```

True on a store with no custody rows. **False the moment C1a legitimately
recorded the real position** — you genuinely hold ₹18,963 now, and
18,963 + 12,345 is not 12,345. The F-106/F-125 family, again.

The part that earns it its own number: **one of the four F-137 checks had
already been converted to a delta for exactly this reason, citing F-106 in its
own comment — and its three neighbours were left absolute.** A discipline
applied to the line under the cursor and not to the pattern. That is **F-138**.

## The fix

The three checks now measure the delta their own inserts produce, against
whatever position the store already holds. Rehearsed offline on **both** store
states: green before C1a, green after C1a, and the old app red on a migrated
copy with exactly the box's three FAIL lines.

## How a count-equal kit proves itself

488 → 488 — checks corrected, not added — so a check *count* cannot see this
change (the F-130 problem). The installer therefore **reproduces the failure
instead**: it applies the C1a migration to a throwaway copy of your live store
and requires, before any swap:

| run | store | required result |
|---|---|---|
| current app | live | GREEN 488/488 |
| current app | migrated copy | **RED, every FAIL naming F-137** — your exact red, recreated |
| new app | migrated copy | GREEN 488/488 |
| new app | live | GREEN 488/488 |

If the reproduction doesn't reproduce, nothing is installed.

Built on live `583092c015c37d97fc240d09637b5ea7`, ships
`41788368ec815b804d276df63c796575`.

```
bash /root/deploy/repo/deploy_kits/S189_W1b/install_w1b.sh
bash /root/deploy/repo/deploy_kits/S189_C1a/install_c1a.sh   # then re-run this
```

The C1a kit's installer is updated in the same push to expect the W1b build;
its migration SQL and gate are **byte-identical** to yesterday's — the thing
that was wrong was never in them.

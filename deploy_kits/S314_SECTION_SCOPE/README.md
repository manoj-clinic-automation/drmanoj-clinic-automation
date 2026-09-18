# S314_SECTION_SCOPE — a stock count can cover one section

**Project:** Sanjeevni — Pharmacy & Marg · **Session:** S268 · **18-Sep-2026**
**Rungs 2 and 3 of** `S268_COUNT2_BY_SECTION_PLAN.md`. **Requires S313_SECTION_MAP live.**

## The one line

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S314_SECTION_SCOPE/install_S314_SECTION_SCOPE.sh
```

## How to do an orthotics-only count, once this is live

Download the ordinary count pad as always, fill in **only the orthotic rows**, and upload it. That
is the whole method — there is no new screen and no setting to remember. The blank rows have always
meant *not counted*, never *counted zero*, so the sheet already says what it covers; the server now
reads that and holds the round answerable for the orthotics alone.

The round will say so in its own words: *"Orthotics only — 69 of the shop's 373 items"*.

If you would rather say it in advance than have it read off the sheet — which also lets your staff
close the round rather than only you — one call declares it:

```
POST https://followup.dr-manoj.in/finance/stock/api/pad/section/2
{"section": "Orthotics"}
```

## What does not change

Nothing on the 06-Sep count. The walk holds that round against the current live code and **every
figure, and the entire hub payload, must come back identical** before this kit will install itself.
The hub, the desk, Amir's board, the report and the loss board all still open the 06-Sep count and
not a new sectioned one — a sectioned round is opened by `?count=N`.

## Files

| file | what |
|---|---|
| `patch_scope_s314.py` | the six anchored edits |
| `selftest_s314.py` | 22 checks with negative controls, synthetic databases |
| `walk_s314.py` | on a scratch copy of the live database: **the whole-shop round is identical** |
| `install_S314_SECTION_SCOPE.sh` | 7 gates; refuses if S313 is not live, walks, places, reads back, restores |

# S328 BUILD BRIEF — the Sanjeevni chat, 18 → 19-Oct-2026 (20:30 IST 18-Oct → 09:24 IST 19-Oct)

*The one paper for the next Sanjeevni session and for Dr Manoj. Also in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S328\` and on the SSD (`F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`). The next chat's entry is `START_HERE_SESSION_330.md`.*

## For Dr Manoj — what this session did

1. **The buying model, re-read against today's live code** before anything was built. Finding: the ordering engine had not changed since 11-Oct, and since orders still come from Marg's sheet (your word of 5-Oct), the engine reaches nobody — so the new model can be built and scored silently for a few weeks before it touches a staff screen. Two kits, not three.
2. **Your "Yes" (21:21) to the Yuvika mock-up → D743 → kit S593, live 08:03 this morning.** The engine now reads every item's stock from the one stock function and the one "goods arrived" rule; suppliers' buying rhythm from the spine; Marg's "billed" mark on order lines works again (it had matched nothing for weeks — 7 old lines caught up at once). Reception's order page: Yuvika's one card, and done lines from earlier days now carry their date. Nothing changed in what reception orders.
3. **The nightly side-by-side watch is in (kit S594, 08:27)** — your question at 01:40 ("can you do it yourself?") was right: the schedule is the clinic project's *record*, not a bar; the kit says what it touched. From tonight at 23:58 the stock figure writes its comparison file every night; seven explained nights, then the old stock figures are retired (step 3 of the plan).
4. **The orthotic-sizes confusion (F-942), read to its cause:** Yuvika's bill of 28-09 carried knee supports in M and L only, yet the XL order line was credited with it — orders and bills printed before the 11-Oct renames still share one name key per item. **Kit S598 is briefed and published** (checked independently, two blockers fixed): each bill line answers only its own size; the wrong XL mark is undone (that order shows XL open again; XL leaves the shortage card, 4 → 3); your Needs-you lines name the bill that carried the other sizes. **Its paste line was given at 09:2x — if you have not run it yet, it is the first thing the next chat asks.**
5. **The plan corrected:** the "22 renames" in step 7 were done on 11-Oct (Amir keyed them; 23 of 23 verified). Step 7 is: count #1 closes → the stock-check screens onto the spine → count #2 by section.
6. Two small faults logged, neither urgent: F-942 (above, S598) and F-943 (one harmless warning line in the nightly witness log while a morning closing is pending).

## What needs you

- **The publish of this close** — your double-click, as always:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

- **S598, if not yet run** — paste into Claude Code on manojz, in `D:\dr-manoj-git\drmanoj-clinic-automation`:

```
Build, install, verify and publish the kit in claude_code_briefs/S598_ARRIVALS_BY_LINE.md (v2). Read CLAUDE.md, the charter and the brief first.
```

- Nothing else. Still yours from before, not urgent: bank details for Agarwal Surgicals and Medicals; the first cheque (Shavez can log it); a photo of Marg's purchase-import screen; BASS's number.

## The staff's (on their own screens)

- **Reception:** the order page as before — one card per supplier; a done line from an earlier day shows its date. After S598, the Yuvika order of 28-09 shows KNEE SUPPORT HINGED XL open again (it never came on that bill).
- **Amir:** nothing new; his next export covers the 18-10 09:37 closing.
- **Darpan:** the spot count of ANKLE BINDER L BAMBOO; his order tab stays unused until the model is scored.
- **Morning staff:** the two reports, as every day.

## For the next chat

- **First:** S598's report, its live read and its board line (or the paste line again); the 19-Oct bundle (S327's 17 pins) and the 20-Oct bundle (S593's six, the crontab line); the first witness file (night 1 of 7); the 09:37 capture's verdict.
- **Then, by the plan:** 4 · Kit II — the levels model, scored in shadow, a mock-up of Darpan's one header line first · 3 · 4b-2 after seven explained nights · 5 · rung 4c, Amir's Kit 3, F-943 · 6 · rungs 4d, 4e · 7 · count #1 → 4f → count #2 · 8 · rung 5 → P4/P5.
- **Numbers:** D743; F-942, F-943; kits S593 (live), S594 (live), S598 (published, not run); session 330 reserved.

*S328 build brief · 19-Oct-2026.*

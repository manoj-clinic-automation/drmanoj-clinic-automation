# HANDOFF RUNBOOK — v191 — written at the S269 close, 19-Sep-2026 (the parent project)

## §0 · WHAT HAPPENED

Eight kits, five of them live on the VPS and one on manojz, across two sittings on 18–19 September.

| kit | in one line |
|---|---|
| **S316_SHEETS_SEEDED** | his two owner sheets arrive already written — 19 X-ray studies, 17 procedures |
| **S317_UNIT_STATE** | the nightly bundle records **whether each scheduled job is switched on** (F-496 closed) |
| **S318_UNIT_GAP** | seven more unit files carried (20 → 27), and the gap now **names itself** every morning |
| **S319_WITNESS_INFO** | the never-fired health card reads **five**, not seven |
| **S320_CANON_CURRENT** | manojz's nightly canon gate watches for duplicate **CURRENT** rows — no owner step |
| **S321_XRAY_VIEWS** | **the page's buttons made to work** (F-544), X-rays named with views and priced |
| **S322_PROC_SIDE** | ten plaster sites → twenty fibre cast / fibre slab lines; the Side column |
| **S323_PROC_ONLY** | X-rays off the page, no turn-off on an asked side, consumables read-only, shorthand-first names |

**The session's own shape is the lesson:** the machine gates were green throughout, and three of the
kits existed only because the owner tapped a button and told us what he saw. F-544 (every form on
his page posted one directory up) and F-545 (a safety rule that silently did nothing and printed a
bare `0`) are both of that kind.

## §1 · MENTAL MODELS TO CARRY

1. **The nightly bundle is 01:35 evidence and nothing later.** F-539: I told him a published kit had
   never been installed on the strength of a snapshot taken before he installed it. Ask the live
   surface — most kits print a read-only `--check` that costs him nothing.
2. **A page's buttons are not tested until they are resolved the way a browser resolves them.**
   S316's walk was 33/33 green and could not see the 404 he hit. The walks in S321–S323 render the
   page through Flask, read every `<form action>`, resolve it against the page URL and its `<base>`
   tag, and POST to what comes out.
3. **A safety rule that can do nothing must say what it skipped.** S322 protected the rows he had
   already approved — correctly — and so flagged none of them, printing `X-rays that now ask a side:
   0` with no reason beside it.
4. **Side is a marker, not two more rows.** A left and a right knee cast are one line at one charge;
   which side it was belongs to the visit. The chamber screen asks R / L for the lines that carry it.
5. **An owner page carries only the work in hand** (D553). The X-ray list came off the page the hour
   he finished with it.
6. **A URL is a live route or it is not printed** (F-540).

## §2 · THE LIVE BACKLOG

**First item next session, his own instruction:** *confirmation on how slips get logged* — then the
chamber screen can be built on it.

Then, in order:

1. **His approvals** on the X-ray and procedure lists at `https://followup.dr-manoj.in/finance/clinic/sheets` — and the procedure prices, which were deliberately left empty.
2. **The phonebook work** from the two contact exports he handed over on 19-Sep (7,418 contacts in the bocbareilly export, 2,972 in the clinic account; 49 and 53 columns). They hold patient numbers: they stay out of the repository under F-185 and are read into `finance.db` or `_config` only.
3. **The freshness page** (F-540) — a small owner-gated route serving the collector's own HTML, which also makes S310's printed link true.
4. **The `watcher` ruling as a kit** (D554 / F-547): red during clinic hours when the heartbeat is stale, info outside them.
5. **The last four units into the bundle** (D555): `fitlog`, `gutlog`, `rxguard`, `email-agent.timer`.
6. **The fault-injection kit** for `backup` and `outbox` — closes D525 for good.
7. **The daily report has said “Attendance report not received” for a week** while the attendance mails arrive beside it. Named on four unattended nights; no close has picked it up.
8. **The bank-SMS feed stays PARKED** until he says otherwise (his words, 18-Sep).

## §3 · INSTALL DISCIPLINE — what this session added to it

- **Run the repository's own gate before naming a publish:** `deploy_kits/NO_PHONE_NUMBERS.py` over the new kit folders, in the cloud workspace. Two refusals in two days were knowable before his double-click (F-542).
- **A kit carrying a blanket-ignored file type needs its exact-path allow line in the same breath** — `!deploy_kits/S###_NAME/file.json`.
- **Claim the kit number on the board before the scratch folder is named** (F-515).
- **A data kit dumps the table it will change** to a `.sql` beside the database before the first row moves, and only ever changes rows still marked as the seed's own — a name he typed himself is never overwritten.
- **The four numbers, measured at this close:** drift 3 (`owner_sheets.py`) · dead 1 · folders 86/9/7 loose · stale 0.

## §4 · THE BOUNDARY WITH THE SANJEEVNI CHAT

The other project owns the stock check, the Marg lane, suppliers, and the Amir / Darpan screens. It
took Session **270** and wrote its own entry point; this parent's handoff is **271**, and the next
free session number is **272**. Canon is shared: **list `KB_canon_all\` immediately before writing
anything into it** (F-534) — at this close the folder already held Register v5.110, Archive v1.107,
Fault v2.95 and Runbook v190 from the other chat's S268, and this close appended onto those.

## §5 · WHAT NEEDS HIM, AND IT IS SHORT

1. **One double-click on manojz:** `D:\Downloads\_kbtools\NIGHTLY.bat` — the 03:10 nightly fired as a
   catch-up at ~04:03 IST on 19-Sep and died inside the SSD mirror step, leaving
   `KB_mirror_ClaudeCowork_nightly_2026-09-19.zip.new` and three reports still dated 18-Sep (F-546).
   The newest complete mirror is 18-Sep, 3,616 files, every CRC tested — nothing is lost.
2. **The publish** — his double-click, as always:
   `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
3. **The slip-logging confirmation**, which is the next session's first question.

*v191 · 19-Sep-2026 · S269 close · supersedes v190 (the Sanjeevni chat's S268 close). Canon at this
close: Register **v5.111** · Archive **v1.108** · Fault **v2.96** · routine
**END_OF_SESSION_PROMPT_v16** · entry point **START_HERE_SESSION_271** · pins
**live_pins_S269close.txt**.*

# S815_MARG_WATCH_DARPAN_REPORTS — Darpan's own Ask line; reports on need (13-Nov-2026, Sanjeevni sessions 446–448)

**What it does (the owner's "looks right" of 11:33 IST on the mock-up, artifact 1M6DeQmpxFqfXXGFpYnFkJ — D960; D959 'Both, clubbed'):**
(a) **Darpan's own Ask line** — on the Marg watch, *Put on Darpan* sends a row's question to Darpan's own page, Kal ka hisaab, where it is drawn
FIRST as *Doctor sahab ka sawaal*: one tap of the answers offered, an optional short line, no take-back; only his (staff) login may answer
(door `POST /finance/darpan/kal/api/mw-ask-answer`). The answer comes back to the row; only the owner closes the row, and closing it withdraws
the question. Unanswered two days → the owner's Needs-you (duty `darpan.mw_ask`, raise, 2 days).
(b) **Reports on need** — a sale report (Detail) asked again: by him from a section A row, or by the Marg watch itself when **3 or more** items
rise on one closing with no record (his figure on the page, `mwr.cluster`; 1 = never by itself; only moves found after the install, `mwr.since`).
It shows as a card on Shavez's *Aaj ki reports* (read only; the day's counts unchanged) and closes itself when VERIFIED sale (Detail) files
**received after the ask** cover every day of it that had a sale (owner_notice's five-minute tick; it sends nothing new). New table `marg_watch_report`.

**Files** (all five rebuilt on the box from the live bytes, checked against `TO_PINS.md5`):
| file | from | to |
|---|---|---|
| `/root/finance/marg_billwatch.py` | a36d8265 (S814) | 960b5309 |
| `/root/finance/darpan_kal.py` | a64353c0 | d27ed062 |
| `/root/finance/darpan_kal.html` | b89ca3ad | b7d2d61e |
| `/root/finance/reports_tile.py` | a96bcad5 (S810) | 163a869a |
| `/root/finance/owner_notice.py` | 8bbfb9ef (S814) | 471859b3 |
`claude_code_briefs/DUTY_MAP.json` v23 → v24 (shared with the parent): two duties ADDED — `darpan.mw_ask`, `shavez.mw_report`; no existing
duty or `due_sql` changed (no `aaj_seed.REWRITE` piece touched, F-1024); it rides the publish and the installer stops unless the repository's
copy carries both. `darpan_app.py` is not touched.

**Proof (device VM; the database copy never left it):** the 13-Nov 03:15 bundle and database copy; S810, S812, S813, S814 made on top from the
bundle bytes; the spine rebuilt from manojz's MargArchive (394 readings). `walk_s815.py` 61/61 (with the base-page check and the review's fixes), control on the live
files red; `walk_s814` 44/44, `walk_s812` 61/61, `walk_s803` GREEN, `reports_tile --selftest` 55/55 on the built files; owner_console's
`read_duties` on the v24 map: 60 duties, no error. The three pages in Chromium at 1366 / 884 / 360 px — 42/42: no script error; the strip, the
row button and *Put on Darpan* on the Marg watch; Darpan's question FIRST on his page, three answers, Enter in his line box sends nothing, one
tap sends once with his line; Shavez's card above the steps card; nothing off-screen. `rehearse_s815.sh` 13/13 on a stand-in root (on the round-1 bytes; the installer is unchanged since — the device shell stopped before
the re-run on the final bytes; the installer's own gates walk the final bytes on the box before anything is placed).

**Cold review by a second reader (S448): SAFE TO INSTALL, no must-fix.** Should-fixes built and walked: (S1) a closing's sale days are asked at
most once — an ask, open or closed, that already covers them stops the cluster rule asking again (it had asked Shavez for days she had just sent);
(S3) Darpan's door: a busy database answers 503 with a Hindi line, rolled back, never a 500; every message plain Hindi; a question the owner
withdrew says so; (S4) Shavez's card stands above the day's *kaam poora* / count line, never below it. Nit built: a rise under one unit counts.
Left, said so: (S2) the card's duty line closes on the five-minute tick — with the phone notices switched off it closes when he opens the Marg
watch; (S5) the duty map rides the publish — run the server line straight after the publish (until then the owner's console reads
`shavez.mw_report` as *not read just now*). The whole review: `03_WORKING_PAPERS\S448\S815_COLD_REVIEW.md`.

**Install:** the owner's publish, then the one server line in the installer's header. **Undo:** the line printed at [6/7] (it also withdraws
an open question on Darpan's page and an open report ask — the old page knows neither).

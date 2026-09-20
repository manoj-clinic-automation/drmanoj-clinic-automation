# HANDOFF RUNBOOK — v192 — written at the S271 close, 20-Sep-2026 (the parent project)

## §0 · WHAT HAPPENED

His first task from S269 — *how slips get logged* — answered by him and built the same day: **seven kits,
S324 → S330, all live**, each corrected by what he saw on the live screen. Then, with no code, the
**360° patient-record plan** was designed with him end to end. Full detail: `S271_BUILD_BRIEF.md`.

| kit | in one line |
|---|---|
| **S324_SLIP_LOG** | the slip tile, unit `slips`, room ticks, night report beside the old one |
| **S325_SLIP_OLD_ID** | an old ID missing from the master is not NAYA |
| **S326_SLIP_NEW_FRONTIER** | NEW = above the highest ID issued before the day |
| **S327_SLIP_ROOM_BOOK** | "X-ray room work", amount read-only, "Start new book", pre-1137 numbers voided once |
| **S328_EMR_UPLOAD** | reception's Docterz upload list |
| **S329_SLIP_MENU** | the tile opens a menu; one tap per X-ray; upload tile withdrawn |
| **S330_BLOOD_TEST** | blood orders, lab e-mail by clinic ID, outcome only at upload time |

## §1 · MENTAL MODELS TO CARRY

1. **Take a maximum over events, not over a register** (F-551). The master's highest row was a stray.
2. **A walk compares before/after of what it did not touch** — never a count that depends on his data (F-552).
3. **On a live page, change data through the page's own form found by content, never by pixel** (F-553).
4. **No `__pycache__` under a kit before the publish** — compile and rehearse from copies (F-554).
5. **A rule he states is not relaxed to cure a one-off** (F-555, D557).
6. **Nothing is asked of staff during patient flow** — questions wait for the quiet hour (D559).
7. **He wants the record, not the upload** (D560): the 360° view is the destination; Docterz is the fallback.

## §2 · THE LIVE BACKLOG

**First, in one go, his accepted order (D563):**
1. Blood PDFs into the clinic Drive + the 360° page (visits, procedures, pharmacy bills & returns, reports).
2. The X-ray inbox — **read-only test run first**, then live, then the old-X-ray import.
3. "Check karein" + his one collapsed line.
4. Reports patients send on WhatsApp (confirm first that MyOperator passes attachments).
5. Outside MRI/CT scans + hospital/surgery events.
6. Sending reports to patients on WhatsApp — once sending is cleared (F-82).

Settle before (1): Drive space on the clinic account; the reception PC's Drive folder path.

Then the carried list: rate-page approvals + procedure prices · phonebook from the two exports · freshness
page (F-540) · `watcher` (D554) · last four units into the bundle (D555) · fault injection (D525) ·
"Attendance report not received" · Bhati's petty-book layout (offered) · bank-SMS PARKED.

## §3 · INSTALL DISCIPLINE — added this session

- A kit that follows a same-day kit accepts **every earlier build of the same file** as its FROM (S327–S330
  did), so an uninstalled middle kit never blocks the next.
- Installers drop the slip tables in the **scratch copy** before walking, so the walk sees first use.
- The walk's own cron token is set inside the walk; the box's real token is never read.

## §4 · THE BOUNDARY WITH THE SANJEEVNI CHAT

Unchanged: stock, Marg, suppliers, Amir/Darpan are theirs. The records plan reads Sanjeevni bills and
returns **read-only** for the 360° page. List `KB_canon_all\` before writing (F-534). The parent's next session is **273** (`START_HERE_SESSION_273.md`) — 272 is the Sanjeevni chat's, open beside this close, holding kit S331. Next free after it: **D564 · F-556 · kit S332 · Session 274**.

## §5 · WHAT NEEDS HIM

1. **The publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (this close's canon).
2. Nothing else. The records build starts in the next chat on his word.

# START HERE — SESSION 461 — the Scan App chat (papers & bills)

*Written at the S410 close (14-Nov-2026, 16:1x IST, full EOS) by the Scan App chat. Session **461 is RESERVED for this project** on the board (`board/_numbers`): take it there as the FIRST act (NUMBERS_PROTOCOL_v1) with a SHORT line (under 400 characters). The project's custom instructions govern every reply.*

## A · The open (OPEN_ROUTINE_v1)

1. **Connections:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup`. The device shell; never `git` in it. The device VM's `/sessions` disk is full (F-1326): scratch in `/tmp`, re-made when wiped (the VM restarts wipe it).
2. **The number:** 461 by a pinned write; the clock from the clock tool. Read the counters from the newest close's END line; read `_numbers` whole only to write it (F-1405).
3. **The board:** unread messages to `scanapp`; the packs reminder.
4. **The day's checks:** `D:\Downloads\_kbtools\DAY_OPEN_LATEST.txt` — run `day_open.py` only when it is not today's or a publish / bundle came since.
5. **The pins:** S826's two — `/root/shared/scan_checks_s441.py` 5c934bdb, `/root/assetapp/asset_register.py` 63eba920 — CONFIRMED by a bundle newer than 14-Nov 09:07 IST.

## B · The work — in this order

1. **THE PROCEDURE ROOM PAGE (D982; his "Final" 14:40 IST 14-Nov).** The mock-up IS the specification: artifact "Procedure Room — simplified page (mock-up)" v4, `https://claude.ai/artifact/WFkBPm1Twt7NVM6gTuiUoM`; the written spec `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S410\S410_PROCROOM_SPEC.md` (read it first). Build on the newest bundle's `/root/assetapp/procroom.py` (e51c00a1 at S410 — hash it), read WHOLE first (2,912 lines). Take a kit number before the scratch folder. The parts:
   - the tiles (each a link; the Fibrecast tile lists 5" / 4" / 3" / 2" with rolls in stock, red under the reorder level);
   - the Start-here strip (count · dealer challans waiting · morning screen);
   - Expenses and revenue — the financial year in the X-ray page's way (`xray_costs.py` S633): per month bought Rs, procedures, ILI revenue, other procedures' revenue, revenue less bought; NO per-procedure column; each month opens to (a) what was bought (dealer challans, items, qty, rates) and (b) procedures done, one row per PATIENT slip with its fee and its items, editable (+ add), saved through the morning screen's own save (a slip's old record voided, kept);
   - revenue read from the parent's slip book (`finance.db` slip / slip_item, READ ONLY, as `fin_day` reads it) — the fee field to be read from the live schema, never assumed (F-472);
   - Stock now with the reorder level editable in the table; GLOVES IN PAIRS, never a decimal (`proc.gloves_box` = 50 pairs, set live);
   - "dealer challan" for Yuvika's papers everywhere on this page — "slip" means the patient slip only;
   - the rest folded; a fixed "↑ Top".
   Owner page only: no staff screen changes. Walk on the real app with a made-up database + a control; cold review; installed by his publish and one line.
2. **F-1404 — a stopped reader told to him at once** (small kit on `claude_reader.py` / the admin card's words: "expired" when it is). Read `claude_reader.py` live first: it is 1c9e952e now (another chat's S783 `_post` override) — PLANNED line if that chat still holds it.
3. **F-1194, F-1174** as S409 left them.

## C · What this project is now (S410)

- **S826 live (09:07 IST):** no twin question when two scans' read amounts differ by more than 2%; an open one on such a pair is settled 'different' by the next pass (not when a scan is already set aside); a 'same' answer on such a pair keeps both. The owner's **Restore — not a duplicate** (`/bills/<id>/restore_s826`, owner only, pharmacy lane, set aside as a duplicate, not a page): captured, dup_of cleared, stamp kept, `bill_audit restore_s826`; the partner `dup_flag='no'`; the pair a 'different' twin row. Undo: the kit's README line.
- **The reader:** `read.claude` ON with the new key (never expires); Sarvam OFF (his). The bulk re-read tool `claude_reread.py --ids a,b` re-reads given papers (his server line).
- **Known, accepted:** a true double whose total the reader misread by more than 2% is kept twice (the pharmacy side shows the extra scan unpaired).

## D · Pins

`/root/shared/scan_checks_s441.py` 5c934bdb (S826, DECLARED-PENDING) · `/root/assetapp/asset_register.py` 63eba920 (S826, DECLARED-PENDING) · `procroom.py` e51c00a1 · `claude_reader.py` 1c9e952e · `sorting_desk.py` baa7c6aa (drift 5) · `clinic_papers.py` 89a3cd0a · `xray_costs.py` 5823bae2.

## E · Lessons of S410 (into §2C's NEVER list)

- An API key with an expiry date stops the reader in silence — keys for the estate are made never-expiring, and a stopped reader must be told (F-1404).
- A walk check that the pass skips anyway proves nothing — make the pass judge afresh (S826 review).
- A Restore of one of a pair must also settle the other half, or the partner's own re-read sets IT aside (S826 review).
- The board's numbers page has a size cap: keep lines short; never read it whole to learn one number (F-1405, F-1406).

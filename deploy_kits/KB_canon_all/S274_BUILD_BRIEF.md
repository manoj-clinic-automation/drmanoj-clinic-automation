# S274 BUILD BRIEF — the Sanjeevni close of 20-Sep-2026, and the mandate for S275

*Written 20-Sep-2026 at the close (10:0x IST, clock read). S274 opened 08:18 IST on `START_HERE_SESSION_274` §0 (D567). Next Sanjeevni session: **S275** (reserved on the board; the parent's next is 276). Model: the session ran on the model the owner set.*

## 0 · WHERE THE WEEK STANDS — the mandate for S275

**D567 is done: six of the seven items live on 20-Sep, the seventh (the Book) is v1.6.** What runs now without anyone: the spine every 10 min 08–23 (gate **13/13** nightly — D572), the compare 23:55, near-expiry 23:57, the order rehearsal 23:58, the quarantine rescan 06:25 when signatures change, Shavez's page every morning. **The clock that matters is D566/D572 — seven consecutive nights of `gate 13/13` from 20-Sep** (`/root/finance/spine/spine_state.json`, or the health page's *Marg spine gate* row). Until then and his word: no screen onto the spine; the stock-check screens untouched until count #1 closes.

S275 does, in order, none of it his: **(1)** read the first real morning on Shavez's tile — the tick's lag behind the door (`walk_s334.py` prints it); a one-line proposal if it is hours (the door running the reader at take time — a kit, his call); **(2)** read the three nightly files beside the spine (`orders/`, `expiry/` — F-576's 27 batches, `spine_compare_latest.txt`); **(3)** the category-list signature to the VPS `signatures.json` (`b2dcb211` → manojz's `a987a08e`) — one data edit, the first real rescue for S336's rescan; **(4)** the rung-4 paper, ordering onto the spine, for the day the seven nights are up and he has ruled on `order_rules.json`.

## 1 · WHAT S274 DID

| item | kit | live | what |
|---|---|---|---|
| Phase 0 | — | — | session 274 from `_numbers` (v1→v2); reports REBUILT / WARN (folder counts) / FIXED at 03:11; clone `02c3e39`, gate 693/693; pins 43 match · 0 drift · 7 spine files absent by rule; knowledge 199,236 B |
| 1 + 2 | `S334` → **`S337_SHAVEZ_MORNING_2`** | ~09:0x | `reports_tile.py 78afc54b → 2798436712`: due day, Marg path, tick = the spine's certificate (D568), 10:00 / 21:00 banner, monthly rows, the owner's overdue line. S334 restored itself at its own login-gated probe (F-573) |
| 3 | **`S336_QUARANTINE`** | 09:02 | `marg_take.py 4bcf0243 → 75b8056c` + `phi_scan.py` + `marg_rescan.py` (manojz's, byte-identical) + `marg_rescan_vps.py`; cron 06:25. D569; F-575 measured 98/98 · 44/44 · 7 of 8. Book 3d DONE |
| 4 | **`S338_SPINE_HEALTH`** | 09:06 | `spine_build.py f5907fd4 → 1378c87d` writes `spine_state.json`; `freshness_legs.json 0e56aa9e → 9dfbef9c` (the parent's, two legs, declared); gate is 13 (D572, F-577) |
| 5 | **`S341_ORDER_REHEARSAL`** | 09:44 | `order_rehearsal.py` + `order_rules.json`; cron 23:58; 47 lines · Rs 88,541 · 33 CONFIRM, identical on PC and box (D570) |
| 6 | **`S343_NEAR_EXPIRY`** | 09:38 | `near_expiry.py`; cron 23:57; 7 batches NEAR, ASTOFEN R −38 in Marg vs 44 in the spine; 27 sold batches not in the export (F-576, open) (D571) |
| 7 | Book | — | `SANJEEVNI_SYSTEM_BOOK_v1_6_S274.md` (v1.5 whole + six *Added at v1.6* blocks, §9.4, §13.y, §14.0) |

**Live pins (read back from the box):** `reports_tile.py 2798436712be69eb3c4486a0913e38f4` · `marg_take.py 75b8056cc43ad6f3034ea1fa819ed7a8` · `phi_scan.py 45ca44aad0311657091e4364c4d81e37` · `marg_rescan.py c6a28fc62e3048c0ebbfb0c98679da8c` · `marg_rescan_vps.py 0bbd8a56aaf3ef52b68b1d8ed7d21bd3` · `spine_build.py 1378c87de2f8d4b3796cd92c7ca50d8d` · `freshness_legs.json 9dfbef9c395fdc0049ac007d605d79ca` · `order_rehearsal.py 02582fbea29f51606a6ba8bb8694d3fc` · `order_rules.json b76a610825ecc1dddb0d467d4619aeb4` · `near_expiry.py 627a3915727fce3595c2fdfb11b8f01a`. Crontab: three lines (`# S336_QUARANTINE` · `# S341_ORDER_REHEARSAL` · `# S343_NEAR_EXPIRY`).

## 2 · STANDING RULES CARRIED, AND THE NEW ONES

His rules of the S272 brief §3 unchanged (the stock check untouched until completed; seven clean nights before a lane moves — now `13/13`), plus this session's: **a placed module is proven by importing it, never by curling its own login-gated route (F-573)** · **compile on copies; the `__pycache__` find runs before the copy into `deploy_kits\` (F-574)** · **a PHI scan of a Marg export exempts exactly the shop's `Phone :` line and Marg's footer (F-575)** · **the count the code runs beats the count a decision remembers (F-577)** · **a canon file corrected after its row is written is a new row (F-578)** · the one counter: every number from `board/_numbers`, re-read on a failed pin.

## 3 · NUMBERS

Taken from `board/_numbers` this session: session 274 · kits S334, S336, S337, S338, S341, S343 · D568 … D572 · F-573 … F-578 · session **275** reserved for the next Sanjeevni chat. Mirror at this close: **D573 · F-579 · A-D25 · Session 275 (Sanjeevni) / 276 (parent)**; kit numbers from the board only.

## 4 · OWED TO THE PARENT (one line each)

- `code_bundle.py`: carry `root/finance/spine` (`*.py`, `*.json`, `spine_compare_latest.txt`) — and `spine.db` + `readings/` into the state backup (owed since S272).
- Three root crontab lines (`# S336_QUARANTINE` 06:25 · `# S341_ORDER_REHEARSAL` 23:58 · `# S343_NEAR_EXPIRY` 23:57).
- `freshness_legs.json` moved `0e56aa9e → 9dfbef9c` (two legs appended, backup `.bak_S338_0e56aa9e`) — the parent's pin check expects `9dfbef9c`.
- `clinic-finance` restarted twice (~09:0x, 09:02).

## 5 · WHERE THINGS ARE

Working papers `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S274\` (`kit_build\` the scratch builds, `close\` the close's authored texts, this brief, the close report) · kits `02_SESSION_KITS\S274\` (six) · canon snapshot `00_CANON_SNAPSHOT_S274\` · project knowledge: `claude/S274_BUILD_BRIEF.md`, `claude/SANJEEVNI_SYSTEM_BOOK_v1_6_S274.md` (v1.5 removed there, the canon copy proven) · the board keys `kit_S33x` / `kit_S34x`, `session_S274` · this close's canon in `KB_canon_all\` (Register v5.114 · Archive v1.111 · Fault v2.99 · Runbook v194 · `START_HERE_SESSION_275` · Book v1.6 · `live_pins_S274close.txt`).

---
*S274_BUILD_BRIEF · close 20-Sep-2026 · the mandate is §0.*

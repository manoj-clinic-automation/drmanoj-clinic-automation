# S281 BUILD BRIEF — the Sanjeevni project · the handover to the next Sanjeevni chat (Session 283)

*Written at the S281 close, 25-Sep-2026. This is the ONE document the next Sanjeevni chat reads instead of the session's papers. It lives in three places: this project's knowledge, `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S281\`, and `F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`; a copy sits in `deploy_kits\KB_canon_all\`. The owner's words at the close: "do complete EOS here with a full context to a fresh chat in this project where we will proceed with the build."*

---

## 0 · THE MANDATE FOR SESSION 283, IN ORDER

1. **Ask the owner for his OK to install S397, in one line** — and nothing else first (the Phase 0 ritual runs, but he is not asked anything before this). He said "Go" to the build on 25-Sep; installing switches the closing stock onto the text route, which is live, so it waits for his word (D615, his standing rule: nothing live without his OK).
2. **On his OK, install S397 through Drive, in two steps** (§2). Then **confirm the 24-Sep closing stock reached the server.**
3. **Then the carried list** (§4), in that order, unless he names something else.

## 1 · WHAT IS TRUE AT THE CLOSE

- **The medical PC** (the counter machine, "SET" and the staff account "user"; Office broken, the vendor was due 25-Sep): the agent runs under whichever account is signed in (`agent_guard.py`, S387/S388). The watcher `D:\SendToClinic\marg_watch.py` is **S396.1 `ce64bb31`**, the text reader `marg_txt.py` is **S389.2 `76b5eb5d`** (bill-wise sale only), and the text route is **LIVE** (`MARG_TXT_LIVE.txt`).
- **Sale:** Marg's bill-wise sale travels as text. 22-Sep (parity proof), 23-Sep and 24-Sep are on the server. **It must be exported with item detail (each bill followed by its medicines) — the SUMMARY layout is refused, and that is correct** (it has no item lines, and the server needs them).
- **Stock:** the 24-Sep closing stock was exported as text at 07:36 IST 25-Sep and **refused by today's reader, by design** — kept in `D:\SendToClinic\_captured_txt\refused\` and in Drive `Clinic Data Archive\FromMedical\refused_text\` (`20260925-073658__report__6da7cfb8….txt`). **S397 takes it.**
- **What the medical PC tells Drive every ten minutes** (`Clinic Data Archive\FromMedical\`): `heartbeat.txt` (from the agent), `marg_text_census.txt` (every recent `.txt` where an export could land, with its verdict and title — never a patient's name), `marg_watch_log.txt` (the watcher log's tail), `refused_text\` (anything refused, with a `.why.txt`). **Read these first whenever an export "has not come"** — they work with manojz's link down.
- **The VPS:** seven S281 kits live (S367, S368, S371, S375, S377, S378, S380) — pins in Register v5.122 §S281. Nothing installed on the VPS since 23-Sep 15:40 IST.

## 2 · INSTALLING S397 — exactly

The kit: `deploy_kits\S397_STOCK_TEXT\` in the repository (and staged in Drive, below). Files: `marg_txt.py` **`38d85298f1627ab22b59c9f3459d8764`**, `marg_watch.py` **`81145aa7d7c8e9f7e23072cfab1ee620`**, `KIT_MANIFEST.txt` **`8230562e3dc08d5b07b458198086c68d`**; proof `PROVE_S397_RESULT.txt` (GREEN 14/14).

**Pre-staged at this close** in Drive `Clinic Data Archive\ToMedical\_kit\S397_STAGED\` (a subfolder — the agent installs only files at the `_kit` top level by name, so a subfolder is inert). Each staged file's md5 is re-read before use.

- `_kit` folder id `18bHTgwmY2osQRYc8bkHfKy0G5DajilAM` · `FromMedical` folder id `1cRqkgX5CVaO9yxcWkr9lOZ57oggpKIBp` · `heartbeat.txt` id `12pSKOTfeeGXtdu6-m2IXFDM-3f8Lkt3x`.
- The live `_kit` files at the close: `marg_watch.py` id `1OR5hkOo-Tt2p1-eLbiLlDYRouKaGg2p8` (`ce64bb31`) · `marg_txt.py` id `1umM-WcHmAHY6hS9EWvqAJ-cxhcXmLjZT` (`76b5eb5d`) · `KIT_MANIFEST.txt` id `1ydc30hiF7r9XJ-f7gvaf5jqZeyJTcNwf` (`8c8ac555`).

**Step 1 — the reader and the manifest.** With the Google Drive connector (`update_file` changes only title and parent): rename the live `marg_txt.py` → `marg_txt_S390.py.superseded` and the live `KIT_MANIFEST.txt` → `KIT_MANIFEST_S390.txt.superseded`; move the staged `marg_txt.py` and `KIT_MANIFEST.txt` from `S397_STAGED` into `_kit` (parent → `18bHTgwm…`), keeping their names. Download each back and check the md5 first. Wait for the heartbeat (every few minutes) to show **`marg_txt.py up to date (38d85298)`**.

**Step 2 — the watcher.** Only after step 1 shows in the heartbeat: rename the live `marg_watch.py` → `marg_watch_S396_1.py.superseded`, move the staged `marg_watch.py` in. The agent restarts the watcher; at its start it offers every refused text of the last three days to the new reader (`retry_refused`). Expect in `marg_watch_log.txt`: `marg_watch S397 starting -- text reader S397, text route LIVE`, then `+ CAPTURED 20260925-073658__report__6da7cfb8….txt (text)` and `+ a text refused earlier is taken now`, then the pusher's `TAKEN … -> STOCK_CLOSING VERIFIED`. The 24-Sep SUMMARY sale is refused again, quietly — correct.

**If the manojz link is up,** the same can be done by committing files into `H:\My Drive\Clinic Data Archive\ToMedical\_kit\` (a connected folder) — the Drive letter on manojz is `H:`, on the medical PC `G:`.

**Confirm:** the server's `mi_file` row for STOCK_CLOSING dated 2026-09-24, verdict VERIFIED — read by the owner's one VPS line if needed, or from the watcher log's `TAKEN` line. Then tell him in one line: stock can be exported as text from now on.

**If anything goes wrong:** put the `.superseded` files back under their real names; the agent reinstalls them by md5. Nothing on the VPS or manojz is touched by S397.

## 3 · THE DECISIONS OF S281 (full text: Archive v1.119 §S281)

D602 (04-Sep is Marg's 18 bills; a machine-filed day follows Marg until approved) · D603 (the approvals page is one tree) · D604 (two bank accounts, a transfer is never income, the bulk NEFT next month by its third week) · D605 (the payment pack: letter, annexure, sheet, signature blocks) · **D615 (Marg's exports travel as text; sale live, stock after S397 on his OK; Excel the fallback; the bill-wise sale always with item detail).**

## 4 · THE CARRIED LIST, IN ORDER

1. **The Sanjeevni Book v1.9** — owed: the text route, the agent guard, the census, the approvals tree, the two accounts.
2. **The vendor-ledger reconciliation** once the Yes Bank statement shows August's bulk NEFT.
3. **The ICICI statement reader and the statement shelf** — a drop box, identified by content, one place per account per month.
4. **The monthly pack for Amir** — the NEFT sheet and both statements.
5. **The spine's seven clean nights (27-Sep)** and the Sanjeevni doors switched to it; **Shavez's first real morning** on his tile (sale + closing stock, now both text once S397 is in).
6. Small: F-612 (his Yes Bank CSV); the category signature `b2dcb211 → a987a08e`; the rung-4 paper; an F-number for the `__pycache__` lesson; the `MD5SUMS_ALL` backup row; retire the parent's S377 handover draft.

**His own items (deferred — name only if urgent):** update Gunina Pharmaceuticals' new bank account on the phone book page, then reprint August's bank pack and re-download the NEFT file if it has not gone to the bank — https://followup.dr-manoj.in/finance/purchase/page/book . For the vendor's visit: keep the SET and `user` accounts, `D:\SendToClinic` and `D:\MARGERP` intact.

## 5 · NUMBERS AND RULES

Numbers at the close (board `_numbers` v90): **session 283 reserved for this chat** — take it by a version-pinned write as the first act; **next free D616 · F-632 · kit S399 · session 284**. The parent's S282 is open beside it. Claim every kit number before its scratch folder is named (F-515). No git in the PC shell (F-511). A clock time is read, never estimated (F-510). No phone or account numbers in the repository (F-185).

*S281_BUILD_BRIEF · 25-Sep-2026 · the Sanjeevni project.*

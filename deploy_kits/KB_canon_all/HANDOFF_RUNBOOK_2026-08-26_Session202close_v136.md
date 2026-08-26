# HANDOFF RUNBOOK — v136 (Session 202 · THE DAY THE FEED WENT DARK · 26 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 202 — FULL build EOS)

Opened as canon housekeeping. Became an incident.

1. **The pharmacy revenue feed was dark for 8h40m and nothing said so.** From 23:08 IST on 25-Aug the
   Marg pull failed every ten minutes. Found at 07:33 — **only because the owner asked why a report
   had not arrived.** Every component was healthy: the medical PC on with him in an RDP session,
   Tailscale `active; direct`, the agent running, the watcher capturing, Drive syncing. The single
   failure was Windows on manojz applying its default block on **unauthenticated guest access** to the
   share. Fixed by AUTHENTICATING (`cmdkey /add:100.119.151.40 /user:MEDICAL\SET /pass`) — the forums'
   remedy of re-enabling guest access on a PC holding patient records was declined and recorded as
   declined. The 07:40 pull ran `-- ok`.

2. **F-187 — the Rs 20,000 that existed only as prose.** `cash_count.explanation` had itemised the
   17-Aug drawer clearing in words since S186. Two of the three amounts became entries; the 20,000 did
   not. Settled by **PHYSICAL COUNT** — books 63,903, drawer 43,903, difference 20,000 exactly — after
   a plausible wrong theory (*20,003, with 3 written off*) was **disproved first**.

3. **The owner overruled the assistant, and was right.** Told to press Apply on the 12-June report, he
   asked why he should risk disturbing financial data. Reading the live ingest code proved him
   correct: Apply supersedes, and would have DELETED 26 attributed and 26 RESOLVED review rows on a
   closed month to arrive at the identical number. The assistant had read that behaviour hours earlier
   and had not connected it.

4. **D349 minted and both halves built** — one rule in one place. Proven twice within hours:
   `/ledger/statement` announcing full recovery of a scheduled advance (the close takes 8,000), and
   `/finance/approvals` still saying *variance* after S201 renamed it on the health page. The
   exceptions card is now the owner's inline reconciliation table, with **five harmless rows no longer
   hiding four real ones**.

5. **D350 written and scoped by the owner** — he took the contract's own §8 counter-argument:
   verification, visibility, documents, reinstall kit; **no second transport**. Drive fallback PARKED.

6. **Seven kits live**, every pin recorded as it moved: `S202_DARPAN20K` · `S202_D349B` (294→301) ·
   `S202_D349A` v2 (693→701) · `S202_B2A` (→713) · `S202_B2C` (→719) · `S202_B2B` · `S202_PICTURE`
   (49→53). **F-184 repaired** — twelve absent canonical documents filed, and the canon folder's own
   verification command exits 0 for the first time. **F-190** — `.gitattributes` pinned `*.md`.

7. **F-185 CORRECTED. The assistant's claim that patient diagnoses were public was FALSE.**
   `.gitignore` had always excluded them; the scanner asked the filesystem instead of asking git.

**Six of the nine findings this session are the assistant's own.** F-189 gates that do not gate ·
F-191 monitors born dead · F-192 a stale reading read as live · F-193 error messages naming the wrong
cause · F-188 a test asserting a data state · and F-185's false claim.

**Verdict at close: GREEN, match 47, drift 0.**

---

## §1 — MENTAL MODELS (added this session)

- **A monitor is proven against the thing it monitors, running, in its real state — never a fixture.**
  Three faults surfaced only from live data: the outbox count, the served statement page, the
  heartbeat's age.
- **Configured but never confirmed producing output is not configured — it is decoration.**
  `E:\auto` has been empty for eleven months.
- **A false GREEN is worse than a false red.** A dead machine's last words still say ALIVE.
- **A false alarm every ten minutes is how a file stops being read.** 56 phantom missing days would
  have killed `MARG_PICTURE.txt` as a health signal within a week.
- **A gate is written by asking what it must PROVE**, never by copying a previous kit's shape. And a
  gate's refusal is never redirected to `/dev/null`.
- **An error must not list only the causes it cannot tell apart.**
- **A count is evidence; a theory that fits two digits is not.**
- **To make a claim about what is public, ask the thing that publishes.**
- **The person building the guard is not exempt from the thing the guard is for.** The never-fired
  witness was built, and then wired past, the same morning.

---

## §2 — THE LIVE BACKLOG

> **The maintained copy is `OWNER_TODO_LIVE.md`** (project knowledge, un-manifested by design,
> refreshed at every close as step A10). This is the close-time snapshot.

**⭐0 — owner actions:**

- **TOKEN ROTATION** (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`) — aging since 21-Aug, still the
  oldest and highest-severity item. Three copies of the Marg token.
- **Copy the pin list**: `cp /root/deploy/repo/deploy_kits/KB_canon_all/live_pins_S202close.txt
  /root/deploy/live_pins.txt` then run the checker.
- **Pravesh exits 31-Aug** · July cash top-ups Rs 4,519 · Surendra Rs 516 · Arjun's actual-paid ·
  Shivani's two August items · AF-3's duplicate-advance scan **before the August close**.
- **F-173** — the April-2025 NEFT advice file's shifted account column. Money may have gone to wrong
  accounts. Still the only item where money may already have left for the wrong party.
- **Generate 25-Aug's Marg sale report** — the picture now correctly reports it missing.
- **F-191(c)** — ask Marg support why the automatic backup has produced nothing since Oct-2025.
- **F-185** — the repo's visibility ruling is his, on the corrected figures.

**⭐1 — builder queue, in the owner's stated order:**

1. **The pen-drive backup and D350's Marg transport work — FIRST, and largely autonomous** (his
   instruction at the close: *"max on yr own"*).
2. The expectations file — what report is due, by when, for every type. Useful whether Marg is
   automated or a human clicks.
3. D350 §2/§3 completion: the medical agent reporting Tailscale, power and session state.
4. D350 §4: the reinstall kits — **Marg and its data first**, the pipeline second.
5. F-183 · identifier capture on the health page · B3–B7 · the ledger kit · F-178 · Staff Console
   Phase 0 · Purchase Portal (D335).

**⭐2 — the August close** remains the first fully live enforced run.

**⭐3 — blocked:** the no-clinic-ID bills → Docterz migration · Lab PC/Labmate · AF-1 armed on the
medical sender.

---

## §3 — INSTALL DISCIPLINE (updated)

Unchanged, plus three earned today:

- **Exact-count smoke gates.** `701/701`, not a pattern that might match. Two kits' gates were wrong
  this session; the exact one caught what the loose one had passed.
- **Publish BEFORE pull, always.** An unpublished kit makes the VPS run a silent no-op.
- **Reproduce the red offline before changing anything.** F-188 was diagnosed by applying the
  migration to a throwaway copy and watching the unpatched app drop 645 → 642.

---

## §4 — THE EOS AUTOMATION BOUNDARY (held)

Unchanged. The assistant writes documents and kits; the owner installs, and holds every credential.
`cmdkey` was run by him, and the password never entered this session.

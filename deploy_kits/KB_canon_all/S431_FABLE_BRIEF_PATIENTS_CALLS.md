# FABLE BRIEF — three builds for analysis and refinement (written at S431, the parent, 11-Nov-2026 21:3x IST)

**The owner, 21:21 IST 11-Nov:** *"I want to give this 3 to Fable for analysis and any refinements. So you set it up for this because I will give it to Fable in next fresh session."*

**What the session is for:** study the three items below against the live code and the real data, find what the plans miss or get wrong, refine them, and bring each back to him as something he can SEE (a mock-up or a worked example on real counts) — with the decision made, not offered as options. **Build only after his word on each** ("build"). He judges screens, wording, flow and priority; never put a technical choice to him.

**Run the session in the usual way:** `OPEN_ROUTINE_v1` from the clone · the common custom instructions · the numbers from `board/_numbers` · patient rows stay in the device VM (D656), counts and initials only come out · read a screen's own code first · a gate on a live answer is written from a read of that answer (F-1265) · a walk that could pass on zero cases counts them.

---

## 1 · THE PATIENTS SECTION, PART 2 — his console section (D884, D894)

**What he asked (D884, 10-Nov; D894, 10-Nov 18:39 / 19:23 IST):** a Patients section on his command console, as mocked up and approved in principle:
```
https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA
```
(v4) — new vs repeat patients, grouped by **his diagnosis taxonomy**, the return pattern (8–30-day review, follow-up kept, called), revenue by taxonomy group (his earlier ask, `areas/call-console` memory, 02-Nov). **June's data is unreliable — use Aug–Oct and allow for festival weeks** (D884 (4)). Plus a **one-tap list for diagnosis words the system does not recognise**, so he maps them once.

**Where the data is now (S779, live since 10-Nov 19:23 IST, confirmed by the 11-Nov bundle):**
- `/root/finance/docterz_pickup.py` a26c1467 learns the Docterz *Clinical data report*; `/root/finance/dx_feed.py` f18c5652 + `/root/finance/diagnosis_normalizer.py` daef69da (his taxonomy, from the PC tracker) fill a per-visit diagnosis table (`dx_visit` in `finance.db`). The 01-Jul..09-Nov export went in at S780 (from his Downloads, by itself).
- The taxonomy master: project file `Orthopedic_Diagnosis_Taxonomy_Master.xlsx`.
- The return-pattern analysis already done: `deploy_kits/KB_canon_all/S421_RETURN_PATTERN_ANALYSIS.md` (counts only) — and its two corrections F-1228 / F-1229 (October's 30-day return 43% so far; on-time follow-ups by patient ID 53 / 48 / 46% Aug / Sep / Oct).
- His console: `/root/finance/owner_console.py` **ba977832** (S791 payment-gap line, S792 clock line; DECLARED-PENDING until the 12-Nov bundle — read its section code first) and `/root/finance/owner_console.html` 1662c51a.

**What to analyse first:** how many visits in Aug–Oct carry a diagnosis after S779 (F-1225 said 735 of 1,305 patients and 905 of 2,121 follow-ups had none before it); how many distinct diagnosis words fail the normaliser (that is the size of his one-tap list); whether the mock-up's figures can be reproduced exactly from `dx_visit` + the visits; revenue per taxonomy group — which revenue source and whether pharmacy/X-ray belong in it.

## 2 · THE PATIENTS SECTION, PART 3 — reception's third evening export

**What it is:** the same data kept current every day. Reception already exports two Docterz reports every evening after 9 p.m. (the consultation report and the follow-up log; `areas/reception-entry-workflows` memory, 10-Nov). Part 3 adds the **Clinical data report** as the third — so `dx_visit` stays fresh without him exporting by hand (today it arrives only when he exports it into `D:\Downloads` on manojz; S780 sends it on).

**What to analyse:** the export's date range per evening (one day, or a rolling window that overlaps safely); what the server does with an overlap or a missed evening (S779's reader — insert-only or replace?); whether reception's existing pickup route (the PC tracker's `docterz_fetch.py` 83aa8d90 / `DOCTERZ_PICKUP.bat` on manojz, and the server road since S457) already carries a third file; the staff instruction in Hindi, and how a missed export shows (on whose list). **No extra burden on reception during patient flow** (his standing rule).

## 3 · THE CALL CONSOLE — the older follow-ups (D899)

**What he asked (D899, 11-Nov 06:47 IST; memory `areas/call-console`):** for older follow-ups (grace period onwards) each patient shows **when last called successfully**, and from there **the outcome, the call recording and the transcript — all on his page**; **the staff page gets the recording, not the transcript** (standing rule, 07-Nov: staff never see transcripts), so a caller knows when the patient was last reached and what was said. **A mock-up first.**

**Where things are:** `/root/portal/calls_console.py` 45b03731 and `/root/portal/ring_common.py` ce428b2c; the follow-up sections come from the Callback Tracker / the PC follow-up tracker (`processor.py` f1c02736 on manojz, S777 — the calling list's rules D893: a visit from half the advised period before the due date closes a follow-up; one visit closes every open follow-up of the same patient). The console's history: kits S698 … S762 (`deploy_kits/S698_CALLS_R1` … `S762_STAFF_CARDS_R2`), `claude/S377_CALL_CONSOLE_PLAN.md`, `Call_Console_Evolution_Spec_v2_4.md`, D819. His look rules for this page (memory `areas/call-console`): larger darker small text, sections collapsed with a one-line summary whose colour says "open me", a progress bar while a recording plays, the clinic ID beside every patient, full mobile numbers, little scrolling.

**What to analyse:** how "successful call" is decided (answered + a minimum duration? the AI verdict?) and on how many older follow-ups it exists; matching calls to a follow-up by number when the patient called from another mobile; what the staff page shows today and where the recording fits there; what D884 (5) adds — the calling sections show only patients who have NOT visited (staff were told "already visited").

---

## Not in this brief (stays with the parent's backlog)
- **The reception mobile (D908):** the shared/backup reception phone used only with each staff member's own login, and Ranjit (Ranjeet, no portal login yet) added as its backup person. Not small: the shared `reception` login is named in 20 server files (pushes, duties, tiles). A future session, on his word.

*S431_FABLE_BRIEF_PATIENTS_CALLS — written at S431 (the parent), 11-Nov-2026. A paper of this project: placed into canon at the S431 close; the next START_HERE points here.*

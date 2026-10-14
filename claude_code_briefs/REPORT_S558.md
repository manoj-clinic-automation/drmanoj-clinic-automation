# REPORT S558_RING_LIST_LINK_CALL — installed 14-Oct-2026 12:29 IST (read from the installer's output)

On the after-call list, staff can now link a no-show who came in under a different mobile. The list then shows that patient as came, and the next call from that number shows the patient as known.
Each no-show line also gets an **IVR call** button. The staff member's own phone rings first, then MyOperator joins the patient, exactly as in the Callback Tracker.

**Both are installed switched OFF, as the brief says.** Nothing has changed yet for the staff. On `https://followup.dr-manoj.in/portal/ring/list` your own box now has two new switches, **Doosre number se link** and **IVR call button**, both OFF. Turn each one on when you are ready. Everything was tested on a copy first and works.

---

## For the chat — the proof

**Decision D726 · finding F-896 · kit S558** (numbers as given in the brief). Run by Claude Code from the brief (f3deb4b5), not by run_build.py.

### Pins (each read live before touching it, then read back on the box after placing)
| file | FROM (pin = live, 12:10 IST) | TO (read back 12:29) |
|---|---|---|
| `/root/portal/ring_outcome.py` | `7cb60aad2df80f87fdc4a674ebe7ee45` | `25a169bfe280e16b4b39585d827cc36e` |
| `/root/portal/ring_common.py` | `4344b59277d94b2d11d8d7cc23328677` | `ce428b2c52582d4a30d460612a6da968` |
| `/root/wa/call_api.py` (read only) | `930b42c49e8c03ecc46d5e53e1e8d386` | unchanged, read again after the restart |
| `/root/portal/portal.py` (read only) | `f8b059f61fa8b885f024f4f4ce73e4f2` | unchanged (no route was needed there; the acts go through `ring_list_act` inside `ring_outcome.install`) |

The programs were built on the box by `make_s558.py`: 24 counted anchored edits on the live bytes, each found exactly once (4 in ring_common, 20 in ring_outcome), checked in memory, then compared byte for byte with the kit (`--check`). They compile under `/usr/bin/python3` and the venv python (both 3.9.25).
Functions changed in `ring_outcome.py`: `init_db, _ids_on_call, list_data, _row_noshow, _row_due, _row_came, _owner_box, render_list, install`. 23 functions were added. In `ring_common.py` only `lookup_caller` changed, and `_linked_ids` was added. THE RULE (`appt_state`, `can_judge`, `first_visit`) is byte for byte the live code, and so are the tap, the mirror, the sweeper, the floor and the card (checked by the walk).

### Walk (`walk_s558.py`, run on the box under both pythons, on a made-up root dated March 2027)
- **WALK_S558 GREEN 129 checks**, under each python. It covers: G installed OFF (every login's home has the tile; nothing new is drawn; all four acts return 403); (a) suggestions; (e) search; (b) link; (d) the number remembered; (c) undo; (f) IVR call; (g) switches off again; (h) S497's walk; R real-store copies.
- **(a)** The patient registered 2 days after the booking is suggested, newest first. These are **not** suggested: one registered 10 days after the window, one already matched by another line, one under the caller's own fingerprint, and an old patient seen again.
- **(b)** A link moves the line to Aa gaye with *doosre number se aaye · Sunita Walk · ID W5801 · linked by Alisha Walk*. It writes an `appt_link` row and an `appt_event` `link`. A second link is refused (409). A clinic ID with no visit since the booking is refused (400). The outcome table is untouched, so nothing goes to the mirror.
- **(c)** Staff can undo on the same day, and the line returns to Nahi aaye. The next day staff are refused (403) and the button is gone from their page. The owner can still undo (allowed). The row is never deleted; a re-link re-uses it.
- **(d)** `lookup_caller` shows the linked patient (`linked`, with last visit and count), so the next call is *known*. It still works without a fingerprint. After undo the patient is absent, and with `link_on=0` absent too.
- **(e)** Search finds a clinic ID (exact) and a part of a name (case-blind), only among patients with a visit since the booking day.
- **(f)** Tested against a stand-in for call_api:
  - accepted;
  - refused, with its reason shown (a long digit run in it is cut to its last 4);
  - call_api's own 400 "unknown agent" is shown as *Aapka phone IVR mein nahi juda*;
  - server down;
  - no key in .env: refused, and call_api is not reached.
  - Reception, who has no MyOperator entry, sees the button greyed, and the press is refused (400).
  - The stand-in received `X-Call-Key` = the walk's key from .env, the line's **stored** number (a number sent from the page was ignored), `RL<id>` and a 30 s timeout.
  - No page contains the key, and nothing printed contains the number or the key.
  - A second press within 60 s is refused (429).
  - Each press is kept as `appt_event` `ivr_call`: accepted / refused / refused / error, with no number in it.
- **(g)** With both switches off: no fold, button or link words for any login; all acts return 403, even for the owner; links are not read. finance.db stays byte-identical, and nothing tried to reach the network.
- **(h)** S497's own `walk_s497.py`, re-run on this kit's programs: **183 checks, 1 red**. The red one is its file-identity check (`make_s497` rebuilds S497's bytes, and the file is now S558's). Every check of THE RULE, the tap, the card, the clock and Docterz is green.
- **R** (copies of the real stores, counts only): `appt_link` is made and the four old tables are unchanged. The list reads with the switches off. With link on (copy only), 7 new-number lines get the fold, with 48 suggestions in all. This walk never reads the clinic's real salt, so its Nahi aaye count (6) is higher than the live page's.
- **Negative control** (the same walk on the old files): **WALK_S558 RED 56 failed of 101**, under both pythons. Red per part: (a) 10 · (e) 5 · (b) 5 · (d) 3 · (c) 2 · (f) 12 · S 5 · G 8 · (g) 6. So the old files fail (a) through (f).
- **Rehearsal** (`rehearse_s558.sh`, made-up root under /tmp): **REHEARSAL GREEN**. A fresh install was green, a second run said ALREADY INSTALLED, and each of these restored the FROM bytes: a forced red after placing, the list answering 200 to a stranger, and a red after the look as manoj.

### Install (12:28:19 → 12:29:09 IST, read from `date` on the box)
- Gates → pins → compile → rebuild = kit → walk + control → backups → place → read-back → table and keys → restart → health → look as manoj: **all green, exit 0**.
- **Backups:**
  - `/root/portal/ring_outcome.py.bak_S558_7cb60aad`
  - `/root/portal/ring_common.py.bak_S558_4344b592`
  - `/root/portal/ring_outcomes.db.bak_S558_20261014_122900`
  - `/root/finance/finance.db.bak_S558_20261014_122900`
  - The databases were copied with the sqlite backup API and integrity-checked. finance.db is never written by this kit; it was backed up because the rulebook says so.
- **Data step:**
  - the table `appt_link` was made, with 0 rows;
  - `kv link_on=0` and `call_on=0` were written (INSERT OR IGNORE).
- **Restarted: ring-hook and clinic-portal only.** Afterwards:
  - both services are active;
  - `/portal/health` and the ring-hook health answer ok;
  - `/finance/healthz` answers 200;
  - the list and its POST doors answer 302 to a caller with no login;
  - the journal has no errors since the restart.
- **Read as manoj** (the placed program rendering the live store read-only, both switches off):
  - 3 Nahi aaye · 2 Aane baaki · 4 Aa gaye;
  - nothing new on any line;
  - his box carries the two toggles, both OFF.
- The build lock `/root/deploy/.claude_code_build.lock` was held from 12:28 until this report was written. The installer took a lock inside it.

**Undo (one line on the box):** `\cp -p /root/portal/ring_outcome.py.bak_S558_7cb60aad /root/portal/ring_outcome.py && \cp -p /root/portal/ring_common.py.bak_S558_4344b592 /root/portal/ring_common.py && systemctl restart ring-hook clinic-portal && md5sum /root/portal/ring_outcome.py /root/portal/ring_common.py`. The md5 sums must read `7cb60aad…` and `4344b592…`. The empty table and the OFF keys may stay.

### Decisions made where the brief was silent (also in the kit README)
1. A stored link counts only while `link_on` is on. Switching it off takes the whole feature off; the rows are kept.
2. `outcome_id UNIQUE` plus "never delete": after an undo, a new link on that line re-uses its row. The earlier ID is kept in the `appt_event` `link` row's old value.
3. "The owner" who may undo on any day means the doctor role (manoj).
4. `linked_by` / `linked_name` hold the presser's login and display name, as in `appt_event`.
5. The fold sits in the *Mareez* cell, because Aane baaki has no action column. The call button sits beside S497's two buttons.
6. Search does not hide patients linked elsewhere. The brief's exclusions apply only to the suggestions.
7. A linked line in Aa gaye follows the span like every Aa gaye line, so one booked more than 7 days ago shows under *30 din*.
8. The pop-up card's words are **not** changed. *"(doosra number)"* was optional, and `caller_card` is outside the brief's `lookup_caller`-only edit. A linked patient simply shows on the card as a known patient.

### Not done, and noticed
- **Not switched on** (brief §6). The chat shows the owner, and he turns them on.
- **Board `_numbers`:** not reachable from Claude Code (it is a claude.ai artifact). **The chat should append S558's DONE line:** ring_outcome.py 25a169bf, ring_common.py ce428b2c, live 14-Oct 12:29 IST.
- **No staff duty was added, moved or removed** (these are tools on an existing page), so DUTY_MAP.md / .json are unchanged. The *Nahi aaye* list itself still has no DUTY_MAP line, as S497 noted. That is outside this brief.
- **PUBLISH_ALL published 16 files in commit 726b6b2:** this kit's 9, plus 7 that were already pending in the repository from other work. This kit did not touch them.
- **Live call not placed:** the IVR button was tested against a stand-in, not by ringing a real phone. The first real press, after the owner turns it on, is the live proof. call_api's own journal logs only the last 4 digits.
- **The rehearsal's look** showed "0 Nahi aaye" because its made-up root has no fingerprint salt. On the live box the look correctly read 3.
- **Cost:** about US$6.5 of the US$40 budget for this run.

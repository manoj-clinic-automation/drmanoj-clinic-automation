# S419_RING_OUTCOME — the caller card made operational (D590 steps 2–3) · session 284 · 27-Sep-2026

**What it does, in the owner's words (D630, 26-Sep):** *"caller card … make it operational first."* At hang-up the staff phone that answered is asked **"क्या हुआ?"**; one tap files the outcome; ten minutes without one brings **one** reminder; the doctor sees **per-person counts**.

## The flow
1. `call.dial_begin` → the S366 ring card, as today. NEW: the call is recorded in `/root/portal/ring_outcomes.db` (0600).
2. `call.answered` → the others see *"ने उठा लिया"*, as today. NEW: who answered is recorded.
3. `call.end`, bridged → NEW: the phone that answered gets **"क्या हुआ? · <name>"** (tag `call-<session>`, so it replaces the ring card). The other phones' cards close as today. If no `call.answered` reached us, every dialled phone is asked. **Missed** → the ❌ card as today, no question.
4. The tap opens **`/portal/ring/outcome?s=<session>`** (signed-in portal; Hindi): the caller card on top, then the buttons —
   - **known patient:** अपॉइंटमेंट बुक हो गया (first — owner, 21/22-Sep) · मरीज़ आ रहे हैं · नहीं आएँगे · बात हुई — फिर call करना · बात नहीं हो पाई · डॉक्टर को दिखाना है (the tracker's own one-tap set, its own order and codes: `k_coming` · `k_not_coming` · `k_call_again` · `no_answer` · `problem`);
   - **new number:** अपॉइंटमेंट बुक हो गया · सोच कर बताएँगे · जानकारी दे दी · फिर call करना है · 🚨 डॉक्टर — surgery / urgent · काम का नहीं (the D225 lead set: `in_appointment_booked` · `in_will_come` · `in_enquiry_only` · `in_needs_callback` · `in_escalated` · `in_no_action`), and the 7th — *पुराने मरीज़, नया नंबर* — is a link into the Call Tracker's own link form.
   One outcome per call; a second tap is refused (changes go in the tracker, as today).
5. **Stored on the VPS first, mirrored into the Google tracker within the minute:** `Followup_Outcomes` gets a row of exactly the 18-column shape `saveIncomingOutcome` / `saveKOutcome` write (Source `ring`, or `K` for the one-tap codes); an escalation also appends the 13-column `Followup_Escalations` row with the tracker's own reason text; the Doctor/urgent path also fires the same ntfy buzz the tracker fires (`NTFY_TOPIC` from `/root/wa/.env`). `Handled By` = the staff name from `ring_agents.json`, `Agent Ext` from the tracker's `Agents` tab. The mirror uses the venv's `gspread` and the same service-account key `push_followups_vps.py` uses (found by content, never named). **A failed mirror is retried every 30 s, never lost**; the page says *tracker में थोड़ी देर में* until it lands.
6. **Ten minutes** after an answered call with no outcome: one push *"Outcome बाकी — <name / …last4>"*, same tag; never a second. An outcome typed in the tracker itself for `IN_<phone>_<day>` at or after the call ended closes the reminder first. Restart-safe: due times live in the db, the sweeper runs in the ring-hook process.
7. **Counts** (doctor only, numbers only): `https://followup.dr-manoj.in/portal/ring/counts` — per login per day: rang · answered · outcome · missing · appointments; `?day=YYYYMMDD` for another day; `&json=1` for the machine. *The Gist line waits for the tiles pass — the Gist template lives inside `portal.py`, untouched by this kit on purpose (drift 7 → read whole this session, re-pinned 912a1d82).*

## Files
| file | from | to | note |
|---|---|---|---|
| `/root/portal/ring_outcome.py` | — | NEW | db, page, mirror, reminder, counts |
| `/root/portal/ring_hook.py` | `a3cd0466` (S366) | full file | records the call; the outcome card at `call.end`; starts the sweeper |
| `/root/portal/portal_push.py` | `576ae269` (S370) | full file | `install()` also mounts `ring_outcome`'s three routes |
| `/root/portal/portal.py` | `912a1d82` | **untouched** | |
| `/root/portal/ring_common.py`, `portal_sw.js` | `4344b592`, `ab728b08` | untouched | the SW already opens `data.url` on tap |

Restarts `ring-hook` and `clinic-portal`. Backups `ring_hook.py.bak_S419_a3cd0466`, `portal_push.py.bak_S419_576ae269`. RED after placing → restored, `ring_outcome.py` removed.

## Proof
`walk_s419.py` — 46 checks on a scratch copy, no network (fake push, fake sheet, fake ntfy): the card routing, the page order, the tap, the refusal of a second tap, the 18/13-column rows, the buzz, the reminder (once, and closed by a tracker-typed outcome), the counts, the S366 gate. The installer runs it again on the box with the venv, then a **read-only** look at the real sheet (key found, id read, header = the 18 names, Agents tab readable) before anything is placed; after placing, health + route probes (302 without login, F-621) + the journal since its own restart (F-622).

## Install — one line on the VPS
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S419_RING_OUTCOME/install_S419_RING_OUTCOME.sh
```

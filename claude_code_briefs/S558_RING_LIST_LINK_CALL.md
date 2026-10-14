# S558_RING_LIST_LINK_CALL — brief for the build runner (Agent SDK, the API credits)

*Written 14-Oct-2026 by the parent (session 313) at its close. Kit **S558** is claimed on the board `_numbers` with its PLANNED line, in the S313 close's one write. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S558_RING_LIST_LINK_CALL`. It is the first job of the next parent chat (session 317). Decision **D726**; finding **F-896**.*

## 0 · For the owner (2 plain lines on top of the report)
On the after-call list, staff can now link a no-show who came in under a different mobile. The list then shows that patient as came, and the next call from that number shows the patient as known.
Each no-show line also gets an **IVR call** button. The staff member's own phone rings first, then MyOperator joins the patient, exactly as in the Callback Tracker.

## 1 · The owner's word
- 14-Oct 08:5x IST, on `https://followup.dr-manoj.in/portal/ring/list`: *"This feature is working well. The only issue is coming that the patients, they call from a different number. The new ones. And then they register themselves with a different number. So, that functionality is missing and needs to be built. Secondly, there should be a click to call link to IVR number as the callback tracker does. For the no shows, so that they can be called seamlessly. Either from here or through a dedicated section in the callback tracker itself."*
- After the chat's plan, 09:02 IST: **"1 any staff · 2 yes"**. That means:
  - any staff member who has the list may confirm a link;
  - the second number is remembered for future calls.
- Placement (the chat's decision, inside D726): the call button goes **on this list**, not in the Google tracker.

## 2 · What was read (14-Oct, the 01:35 bundle and the live page, read only)
- **The live list (30 din):**
  - Nahi aaye 3 rows, **all three "Naya number — Docterz mein abhi koi record nahi"**;
  - Aane baaki 0 rows;
  - Aa gaye 4 rows (3 *"call ke samay naya number tha"*);
  - the mobile cell is a plain `tel:` link, and nothing on the page places an IVR call;
  - visits reach the server up to 13-Oct.
- **`/root/portal/ring_outcome.py` `7cb60aad2df80f87fdc4a674ebe7ee45`** (S419 + S497, D693), 1,761 lines:
  - `list_data()` → `first_visit(row, booked, visits, fp)` looks for a visit by the clinic IDs on the call card (`_ids_on_call`), then by the caller's mobile fingerprint (`_mobile_fp` → `visits_since` reads `patient_visit` read-only);
  - `appt_state()` is THE RULE (came / closed / noshow / due); `can_judge()`;
  - the store `ring_outcomes.db` holds the tables `call`, `outcome` (+ S497 columns), `kv` and `appt_event` (`_appt_event`);
  - the list's POST route `ring_list_act()` handles `recall` and close;
  - the page HTML and JS are inside this file (`s497post`);
  - access: `list_access(who)` (tile *Call ke baad*, `tile_grants.json`).
- **The gap (F-896):** a new caller has no clinic ID on the card and no name, because the pop-up captures none for a new number. If they register in Docterz under another mobile, neither key finds the visit, so they stand in Nahi aaye for ever, or until a person presses *Ab nahi aayenge*.
- **`/root/portal/ring_common.py` `4344b59277d94b2d11d8d7cc23328677`:**
  - `lookup_caller(phone)` reads `patient_ref` by `mobile_fp` (salted, `finance_patient_match`), plus `patient_visit`;
  - `ring_hook.py` and `choices_for()` treat a card with patients as *known*;
  - `load_agents()` reads `ring_agents.json` as `{phone: {user: <login>, name: <MyOperator name>}}`. Seven logins are there: manoj, shavez, shivani, bhati, alisha, darpan, reception.
- **`patient_ref`** (finance.db, written by `finance_patient_sync.py`) has these columns: `clinic_id, name, patient_uid, mobile_fp, first_seen, last_seen, merged_into`. **`patient_visit`** has `visit_date, clinic_id, patient_uid, mobile_fp, had_procedure`.
- **`/root/wa/call_api.py` `930b42c49e8c03ecc46d5e53e1e8d386`** (service `call-api`, `127.0.0.1:8097`, proxied at `https://followup.dr-manoj.in/call`):
  - `POST /call` needs the header `X-Call-Key` = `CALL_API_SECRET` from `/root/wa/.env`;
  - its JSON is `{agent | user_id, patient_number, reference_id}`, and `agent` resolves by extension or MyOperator name (`resolve_agent`);
  - it replies `{ok, accepted, reason, …}` and logs only the last 4 digits.
  - **It is not edited.**

## 3 · Pins — read each live file, check its md5 = the pin, a different byte = STOP that file and report
- `/root/portal/ring_outcome.py` `7cb60aad2df80f87fdc4a674ebe7ee45` — edited.
- `/root/portal/ring_common.py` `4344b59277d94b2d11d8d7cc23328677` — edited (`lookup_caller` only).
- Read-only, must be unchanged at install: `/root/wa/call_api.py` `930b42c4…`, `/root/portal/portal.py` `f8b059f6…` (if a route must be registered in `portal.py` instead of inside `ring_outcome.py`, say why in the report and pin it the same way).
- Find which service serves `/portal/ring/list` and which imports `ring_common` (the portal app; `ring_hook`). Restart only those.

## 4 · The change
**A · Link a different number (any staff who can open the list — D726 (1)).**
1. A new table in `ring_outcomes.db`, made the way S497's columns are made (on a page request or the installer, never inside a read):
   - the table: `appt_link(id, outcome_id UNIQUE, clinic_id, mobile, linked_by, linked_name, linked_at, undone_by, undone_at)`;
   - `mobile` is the call's own 10-digit number, as `outcome.mobile` already holds it;
   - every link and undo is also written as an `appt_event` (`link` / `unlink`).
2. **Suggestions** on every Nahi aaye and Aane baaki line whose call card had no clinic ID (a new number) — a small *"Shayad yeh aaye?"* fold:
   - the candidates are the patients whose **first-ever visit** (the earliest `patient_visit.visit_date` for that `clinic_id`, or `patient_ref.first_seen`) falls from the booking day to the promised day (or booking day + `wait_days`) **+ 3 days**, and up to today;
   - not a patient already linked to, or matched by, another ring line;
   - not a patient whose `mobile_fp` is this caller's;
   - shown newest first, at most 8, as name · clinic ID · *"pehli visit dd-mm"*;
   - one button each: **"Haan, yahi hai"**.
3. **Search** in the same fold: a clinic ID (exact) or a name (contains, case-blind), over patients with a visit from the booking day to today, up to 8 results, with the same button.
4. **On "Haan, yahi hai"** (POST through `ring_list_act`, a new act `link`; the server re-checks access, that the line is still Nahi aaye or Aane baaki, and that the clinic ID has a visit on or after the booking day):
   - the link is stored;
   - `list_data` treats the linked clinic ID as an ID on the call, so the line becomes **Aa gaye** with *"doosre number se aaye · <name> · <clinic ID> · linked by <person>"*.
5. **Undo:** on that Aa gaye line, **"Galat link — hatao"** by any staff on the same IST day as the link, and by the owner any day. It writes `undone_*`, never deletes, and the line goes back to where THE RULE puts it.
6. **THE RULE (`appt_state`) is not changed.** A link only supplies the visit.

**B · Remember the second number (D726 (2)).** In `ring_common.lookup_caller(phone)`:
- after the `patient_ref` read, also read `ring_outcomes.db` (read-only, its own path constant, any error → ignored) for live links whose `mobile` equals this caller's 10 digits;
- add each linked patient (name, clinic ID, last visit and visit count from `patient_ref` / `patient_visit` by clinic ID) once, with `"linked": True`;
- the next call from that number then shows the patient on the pop-up, and `choices_for` offers the *known* list;
- the card text may add *"(doosra number)"*;
- an undone link is not read;
- a number whose fingerprint cannot be made still reads the links (they are by the 10 digits).

**C · The IVR call button (D726 (3)).** On each **Nahi aaye** line, a button **"IVR se call karein"**:
- POST through `ring_list_act`, act `call`, the outcome id only — never a number from the page;
- the server takes the login from the session and finds that login's MyOperator name in `ring_agents.json` (`load_agents()`, the entry whose `user` = login);
- it POSTs to `http://127.0.0.1:8097/call` with `X-Call-Key` read fresh from `/root/wa/.env` and `{agent: <name>, patient_number: <the line's stored mobile>, reference_id: "RL<outcome id>"}`, with a 30 s timeout;
- it returns plain Hinglish:
  - accepted → *"Aapka phone baj raha hai — uthaiye, patient se jod diya jayega"*;
  - refused → *"Call nahi lagi: <call_api's reason, short>"*;
  - the login has no MyOperator entry, or `resolve_agent` refuses it → the button shows greyed with *"Aapka phone IVR mein nahi juda — owner se kahein"* (decide this on the page render from `ring_agents.json`; still handle the 400 at click time);
- one call per line per 60 seconds;
- an `appt_event` `ivr_call` with who, when and accepted (no number in it beyond what `outcome` already holds);
- the `tel:` link stays as it is (the manual fallback).
- **The secret never reaches the page, a log line or the report. No phone number in any log line beyond the last 4.**

**D · Switches (installed OFF — the parent's rule 19).**
- `kv` keys `link_on` and `call_on`, both default `0`.
- The owner's box on the list (where `list_on` and the wait days are set) gets two toggles: *Doosre number se link* and *IVR call button*.
- While a switch is off, its buttons and fold do not render and its act is refused.
- B (remember) follows `link_on`: with it off, `lookup_caller` reads no links.

**E · Not changed:**
- THE RULE;
- the Google tracker mirror (`mirror_one` and the `Followup_Outcomes` tab — a link is not mirrored);
- `call_api.py`;
- the WhatsApp room;
- the floor and the spans;
- `finance.db` (opened read-only only).

## 5 · Walk (`BUILD_NORM_v1.md`) — a made-up root, made-up `ring_outcomes.db` and `finance.db`
**Every phone number in the walk is a run-time join (`P("98765","43210")`) — the number gate (F-185).**
Checks:
- **(a)** a new-number booking, and a new patient registered two days later under another mobile → the patient is in the suggestions; one registered 10 days after the window is not; one already matched to another line is not; one with the caller's own fingerprint is not.
- **(b)** link → the line is Aa gaye with *doosre number se*; `appt_link` and `appt_event` rows are written; a second link on the same line is refused.
- **(c)** undo the same day by staff → back to Nahi aaye; undo the next day by staff → refused, and by `manoj` → allowed.
- **(d)** `lookup_caller` for the caller's number → the linked patient is present, with `linked`; after undo → absent; with `link_on=0` → absent.
- **(e)** search by clinic ID and by part of a name.
- **(f)** the call act, with the HTTP post replaced by a stub:
  - accepted;
  - refused, with its reason shown;
  - a login with no agent → greyed and refused;
  - the stub receives `X-Call-Key` and the stored number, and the page HTML never contains the key;
  - 60-second guard.
- **(g)** switches off → nothing renders, and the acts are refused.
- **(h)** THE RULE's existing walk cases still pass (re-run S497's own checks if its kit has a walk).
- **Negative control:** the old files fail (a)–(f).
- **Installer:**
  - order: gates → pins → compile → rebuild by counted anchored edits on the live bytes (`make_s558.py`, in memory first) → walk → DRY → backups `.bak_S558_<from8>` → place → table and keys made → restart only the services found in §3 → health → read as `manoj`;
  - rehearsed on a made-up root (green · ALREADY INSTALLED · red-after-placing restores);
  - `SUMS.md5`; no `.json` in the kit (or `.json.kit` with its exact `.gitignore` line);
  - the number gate as PUBLISH runs it: `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> <repo>`.

## 6 · Install, publish, report
- After the install, read the live page as `manoj` with both switches **off** (nothing new shows), then report.
- **Do not switch them on.** The chat shows the owner, and he switches them on.
- Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (CLAUDE.md).
- Write `claude_code_briefs/REPORT_S558.md`: 2 plain lines on top, then the proof — pins FROM → TO with full md5s, the walk counts, the old-file red count, the services restarted, the undo line, and the cost.
- Append the install line to the board's `_numbers` claims if it is reachable; otherwise say so in the report.

**NEVER:**
- print, log or report a phone number (last 4 only) or any `.env` value;
- write to `finance.db`;
- edit `call_api.py`;
- mirror a link to Google;
- switch the new features on;
- touch a file another chat's PLANNED line names.

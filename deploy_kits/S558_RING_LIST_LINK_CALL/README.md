# S558_RING_LIST_LINK_CALL — the after-call list: link a different number · remember it · the IVR call

Session 317, 14-Oct-2026. **D726**, mends **F-896**. Brief: `claude_code_briefs/S558_RING_LIST_LINK_CALL.md`.
The owner, 14-Oct, on `/portal/ring/list`: *"This feature is working well. The only issue is coming that the patients, they
call from a different number. The new ones. And then they register themselves with a different number … Secondly, there
should be a click to call link to IVR number as the callback tracker does. For the no shows"*; then *"1 any staff · 2 yes"*.

## What it does (installed OFF — nothing changes for anyone until the owner turns a switch on)

| switch (his box on the list) | who | what |
|---|---|---|
| **Doosre number se link** (`kv link_on`) | any staff member who holds the tile *Call ke baad* (alisha, shivani, shavez, reception) and the doctor | On every *Nahi aaye* and *Aane baaki* line whose call card had no clinic ID (a new number): a fold **Shayad yeh aaye?** — the patients whose **first-ever visit** (earliest `patient_visit` date, or `patient_ref.first_seen`, whichever is earlier) falls from the booking day to the promised day (or booking day + `wait_days`) **+ 3 days**, and not after today; not a patient linked to or matched by another ring line; not one whose fingerprint is the caller's; newest first, at most 8, as *name · ID · pehli visit dd-mm*, one button **Haan, yahi hai** each. Below them a search — a clinic ID (exact) or a part of a name (case-blind) over the patients with a visit from the booking day to today, up to 8. On **Haan, yahi hai** the line becomes **Aa gaye** with *doosre number se aaye · <name> · ID <clinic ID> · linked by <person>*. **Galat link — hatao** on that line: any staff the same India day, the doctor any day. |
| (the same switch) | the ring pop-up | `ring_common.lookup_caller` also reads the live links: the next call from that number shows the linked patient (`"linked": True`) and offers the *known* list. |
| **IVR call button** (`kv call_on`) | the same | On each *Nahi aaye* line, **IVR se call karein**: the staff member's own phone rings first, then MyOperator joins the patient (`call_api.py`, as the Callback Tracker). A login with no MyOperator entry in `ring_agents.json` sees the button greyed: *Aapka phone IVR mein nahi juda — owner se kahein*. One call per line per 60 seconds. The `tel:` link stays. |

- **THE RULE (`appt_state`) is not changed.** A link only supplies the visit: the linked clinic ID is treated as an ID on the
  call (`_ids_on_call`), so `first_visit` finds its visit on or after the booking day.
- **The server re-checks every press:** access (`list_access`), the switch, that the line stands in *Nahi aaye* or *Aane
  baaki* this minute, and that Docterz shows a visit for that clinic ID on or after the booking day. One live link per line
  (`outcome_id UNIQUE`); a second link on the same line is refused (409).
- **The call** posts `{agent: <the login's MyOperator name>, patient_number: <the line's STORED mobile>, reference_id:
  "RL<outcome id>"}` to `http://127.0.0.1:8097/call` with `X-Call-Key` read fresh from `/root/wa/.env`, 30 s timeout.
  The page sends only the line's id — never a number. The key never reaches a page, a log line or a report; S558 prints
  nothing. call_api's own refusal is shown short (*Call nahi lagi: …*, any long digit run cut to its last 4).
- **Never deleted:** an undo writes `undone_by`/`undone_at`; a later link on the same line re-uses its row. Every link,
  undo and call is also an `appt_event` (`link` / `unlink` / `ivr_call` with accepted / refused / error — no number).
- **Switch off** = its fold, buttons and linked words do not render, its acts are refused (403), and `lookup_caller`
  reads no link. A stored link is kept; it counts again when the switch is turned on again.

## Files

| file | on the box | from → to |
|---|---|---|
| `ring_outcome.py` | `/root/portal/ring_outcome.py` | `7cb60aad2df80f87fdc4a674ebe7ee45` → `25a169bfe280e16b4b39585d827cc36e` |
| `ring_common.py` | `/root/portal/ring_common.py` | `4344b59277d94b2d11d8d7cc23328677` → `ce428b2c52582d4a30d460612a6da968` |
| *(read only, pinned)* | `/root/wa/call_api.py` | `930b42c49e8c03ecc46d5e53e1e8d386` — not edited |
| *(read only, pinned)* | `/root/portal/portal.py` | `f8b059f61fa8b885f024f4f4ce73e4f2` — not edited (the routes live in `ring_outcome.install`) |
| `make_s558.py` | not placed | rebuilds both programs from the live bytes by 24 counted anchored edits (each exactly once), compiles them, checks the TO pins; `--check` rebuilds in memory and compares; `--pins` |
| `walk_s558.py` | not placed | the walk (below); `--control` is the same walk on the live files and must end RED |
| `install_S558_RING_LIST_LINK_CALL.sh` | not placed | gates → pins → compile (both pythons) → rebuild = kit bytes → walk + S497's walk + control → `DRY=1` stop → backups → place → md5 read-back → table and keys → restart ring-hook + clinic-portal → health → the page read as manoj → undo line; red after placing restores |
| `rehearse_s558.sh` | not placed | the installer on a made-up root under `/tmp/s558dev/root`: green · ALREADY INSTALLED · forced red restores · list answering 200 restores · red after the look restores |

In `ring_outcome.py` only `init_db`, `_ids_on_call`, `list_data`, `_row_noshow`, `_row_due`, `_row_came`, `_owner_box`,
`render_list` and `install` change; 23 functions are added. In `ring_common.py` only `lookup_caller` changes; `_linked_ids` is
added. THE RULE, the tap (`file_outcome`), the mirror into the Google tracker, the sweeper, the floor, the spans, the card and
the counts are byte for byte the live ones (walked).

**The store:** `ring_outcomes.db` gains `appt_link(id, outcome_id UNIQUE, clinic_id, mobile, linked_by, linked_name,
linked_at, undone_by, undone_at)` (+ an index on `mobile`) and the keys `link_on = 0`, `call_on = 0` (made by the installer
and by `init_db` on a page request — never inside a read). Nothing that is there is changed. `linked_by`/`linked_name` are
the login and the display name of the person who pressed (as `appt_event.by_login`/`by_name`); `mobile` is `outcome.mobile`.
**finance.db** is only ever opened read-only (`file:…?mode=ro`); it is backed up by rule before placing.
**Restarts:** `ring-hook` and `clinic-portal` only (both import `ring_outcome` and `ring_common`).
**Backups:** `ring_outcome.py.bak_S558_7cb60aad`, `ring_common.py.bak_S558_4344b592` (in `/root/portal/`),
`ring_outcomes.db.bak_S558_<stamp>`, `/root/finance/finance.db.bak_S558_<stamp>` (sqlite backup API).

## The walk (`walk_s558.py`)

Made-up root, made-up `ring_outcomes.db` and `finance.db` (March 2027), the walk's own user store, signing secret, salt and
call key; every phone number made at run time; the HTTP post to call_api answered by a stand-in. The real live `portal.py`
with the kit's two programs, through Flask's test client, signed in as alisha, shivani, shavez, reception, manoj (and darpan,
refused). Parts: S the files · G installed OFF · A (a) suggestions · E (e) search · B (b) link · D (d) remembered · C (c) undo ·
F (f) IVR call · O (g) switches off · H (h) S497's own walk re-run on this kit's programs (only its file-identity check may be
red) · R copies of the real stores, counts only. **No staff duty is added, moved or removed** (these are tools on an existing
page), so `DUTY_MAP.md/json` are unchanged.

## Install (the VPS; one line)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S558_RING_LIST_LINK_CALL/install_S558_RING_LIST_LINK_CALL.sh

`DRY=1 ` before `bash` = every gate and the walk, nothing placed. Already installed → it says so and changes nothing.

## Undo

    \cp -p /root/portal/ring_outcome.py.bak_S558_7cb60aad /root/portal/ring_outcome.py && \cp -p /root/portal/ring_common.py.bak_S558_4344b592 /root/portal/ring_common.py && systemctl restart ring-hook clinic-portal && md5sum /root/portal/ring_outcome.py /root/portal/ring_common.py

The md5s must read `7cb60aad…` and `4344b592…`; `/portal/health` 200. The table `appt_link` and the two keys may stay — the old
program never reads them. The store's backup is needed only if the links themselves must be taken back.

## The assistant's decisions where the brief was silent

1. **A stored link counts only while `link_on` is on** (the list and the pop-up alike), so turning the switch off takes the
   whole feature off at once; the rows are kept and count again when it is turned on.
2. **`outcome_id UNIQUE` and "never delete" together:** after an undo, a new link on the same line re-uses its row (the
   earlier clinic ID is kept in `appt_event` as the `link` event's old value).
3. **"The owner" for the any-day undo is the doctor's role** (manoj).
4. **The fold is drawn in the *Mareez* cell** (Aane baaki has no action column); the call button sits with the two S497
   buttons in *Ab kya karna hai*.
5. **Search does not hide patients already linked elsewhere** (the brief's exclusions are for the suggestions); the server
   re-checks only what the brief lists.
6. **The pop-up card's text is not changed** (`caller_card` is outside the brief's edit to `ring_common.py`): a linked
   patient shows on the card like any known patient; the *"(doosra number)"* words were optional and are not added.
7. **A linked line in *Aa gaye* follows the span** like every *Aa gaye* line (S497's rule): booked more than 7 days ago it
   shows under *30 din*.
8. **Call answers:** accepted 200; call_api refused 502 (its reason shown); no MyOperator entry 400; within 60 s 429; switch
   off 403; the line not in *Nahi aaye* 409.

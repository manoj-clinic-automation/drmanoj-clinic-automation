# S366_RING_POPUP — the caller's name on the staff phone as it rings (D590, step 1)

**Owner's GO:** 21-Sep-2026 evening. Rulings folded in: *Appointment booked* tops the known-patient outcome list and
the 10-minute second pop-up is wanted (both are **step 2**, the outcome buttons at hangup — not in this kit); **full
mobile numbers** to staff and owner everywhere (21-Sep, general rule); the doctor's phone is not in the MyOperator
call flow, so he never gets the pop-up.

**What staff see.** The phone MyOperator is ringing shows a Clinic-app notification within a few seconds of the ring:
`📞 RAM KUMAR · 98xxxxxxxx` — `ID 1201 · आखिरी visit 12 Aug 2026 (procedure) · कुल 5 visit`. A family phone lists every
name on it; an unknown number reads `📞 नया नंबर · <number>`. When someone else picks up, the others' pop-up becomes
`<name> ने उठा लिया`; when the call ends it closes on every phone; a missed call stays as `❌ Missed …` until tapped.
Tapping opens the Call Tracker already signed in (S364). It is a normal Chrome notification — nothing installed,
nothing touching the dialer or the call.

**One-time per staff phone (about a minute):** open the Clinic app (home-screen icon), sign in as yourself, tap
**सूचना चालू करें** on the card at the top, tap *Allow*. A test pop-up arrives at once. The card shows only to a login
that owns a ringing phone.

**How.** MyOperator's *second* webhook entry (`call.dial_begin`, `call.answered`, `call.end`) posts to
`https://followup.dr-manoj.in/ring-hook?key=…` → new `ring-hook.service` (`/root/portal/ring_hook.py`, 127.0.0.1:8110,
OLS context `/ring-hook`) → which login owns the ringing phone (`ring_agents.json`, built from MyOperator's user list by
name; numbers only in that 0600 file) → who is calling (`finance.db` by the clinic's own salted fingerprint —
**finding: `patient_ref.mobile` is empty on the VPS, `mobile_fp` is what is there**) → one Web Push (VAPID, pywebpush) to
that login's phones. The portal serves `/portal/sw.js` and stores subscriptions per login (`push_subs.json`, 0600).
Replies to MyOperator are immediate; pushes go on a background thread; every event body and push timing lands in
`/root/portal/ring_state/YYYY-MM-DD.jsonl` — that file measures the first real call's delay. The live `call-hook`
(:8098) is not touched.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S366_RING_POPUP/install_S366_RING_POPUP.sh
```

**Pins.** `portal.py` `62b223cd…` (S364) → `7bddc17cd7e65c75303b0046a86a08db` (full file; `make_s366.py` = four anchored
edits) · NEW `ring_hook.py` `a3cd0466…` · `ring_common.py` `4344b592…` · `portal_push.py` `6fa0a56a…` · `portal_sw.js`
`ab728b08…` · `ring_agents_build.py` `7c3a2081…` · `ring_setup.py` `03ff5891…` · checked unchanged: `tracker_pass.py`
`97ac975a`, `clinic_sso.py` `2bc6ba15`, `clinic_users.py` `2e85a7c8`, `/root/finance/finance_patient_match.py` `0700768a`.

**Proof before the paste.** `walk_s366.py` 49/49 (scratch finance.db with the real fingerprint code and a test salt, a
fake push service; ring → hunt → answered → end, missed, unknown, family, unmapped phone, the gate, the test push, the
six portal routes, the service worker, the card; the live portal.py as negative control: routes +6 none lost, every tile
identical) · the real `pywebpush` path proven against a local push server (VAPID header, aes128gcm, TTL, Urgency) · the
installer rehearsed end to end against a running copy (once red on a check of its own, restored byte-identically, then
green; re-run = "already installed"). Restarts `clinic-portal` and starts `ring-hook`. Touches no Sanjeevni file, not
`finance_app.py`, not `call_hook_capture.py`.

**After the paste, the owner's two GUI steps** (nobody else can): the webhook line printed at the end goes into the
MyOperator panel (*APIs & Webhooks → Webhooks v2 → Add New Webhook*, events `call.dial_begin`, `call.answered`,
`call.end`); each staff phone taps *सूचना चालू करें* once. Then one real call, and the assistant reads the delay from
`ring_state`.

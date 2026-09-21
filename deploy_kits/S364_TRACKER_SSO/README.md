# S364_TRACKER_SSO — the Callback Tracker opened from the Clinic app, already signed in

**The owner's order** (S278 close, D589; his ruling at the S279 open, 21-Sep-2026): *build ONLY the Callback
Tracker's single sign-in through the Clinic app, and take it live.*

**What staff see.** They tap **Call Tracker** in the Clinic app and the Tracker opens already signed in as them —
no key to type, nobody fetching a password from the Apps Script project. Typing a key still works exactly as
before (the fallback never goes away). Tapping the tile again after *Sign out* in the Tracker signs them in again —
a tap in the Clinic app is a real sign-in.

**How** (one line each):
- `/root/portal/portal.py` — the tile now opens `/portal/go/call-tracker`; a signed-in person who is *shown* that
  tile is sent on to the Tracker with a **120-second, one-use pass**; everyone else, and every failure, gets the plain
  Tracker address. `/portal/sso/tracker-redeem` (POST) answers the Tracker's server who a pass belongs to — only an
  active user, with their current role.
- `/root/portal/tracker_pass.py` (new) — the pass, signed with a key *derived* from the portal's existing
  `CLINIC_SSO_SECRET`. **No new secret**: the portal alone checks its own passes, so nothing is copied into Google.
  A pass is not a login cookie and a cookie is not a pass. *Sign out everywhere* kills every pass.
- Apps Script *Clinic Callback Tracker* (`gas/`) — `ssoExchange(pass)` asks the portal, maps the portal user to
  the agent extension (`manoj 10 · shavez 11 · shivani 12 · bhati 13 · alisha 14 · darpan 15`; the Script
  Property `SSO_USER_EXT` overrides) and returns that person's own key; the page signs in with it. A pass is refused
  the second time (remembered 10 minutes). Placed by the assistant in the owner's browser (D577); `GAS_CURRENT` updated
  in the same breath (D583).

**Design note (decided, recorded).** The S278 brief sketched a secret shared with the Tracker's Script
Properties. Built instead: the Tracker hands the pass back to the portal to check — the same short signed pass and
the same fallback, but no secret ever has to travel to Google or pass through anyone's hands.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S364_TRACKER_SSO/install_S364_TRACKER_SSO.sh
```

**Pins.** `portal.py` `d9a9dc40…` → `62b223cd4086d673f550e5eccf3380e0` (full file; `make_s364.py` = three anchored
edits on the live bytes from the 21-Sep 01:35 bundle) · `tracker_pass.py` new `97ac975ad842247b5bcdce2f5b1432f2` ·
checked, unchanged: `clinic_sso.py` `2bc6ba15`, `clinic_users.py` `2e85a7c8`, `tile_grants.json` (read only).
Apps Script: `WebApp.gs` sha256 `989b7de9…` → `10621ed7…`, `Dashboard.html` `440ca0b0…` → `64f07ba9…`
(`make_gas_s364.py`, two anchored edits on the photograph taken from the live editor, every file sha256-matched).

**Proof before the owner's paste.** `tracker_pass` selftest 19/19 · `walk_s364.py` 42/42 (scratch store, test
secret, the real `tile_grants.json` read only, the live `portal.py` as negative control: route table +2 none lost,
every other tile identical) · `gas_harness.js` 21/21 · `page_harness.js` 9/9 (the old key paths unchanged) · the
installer rehearsed end to end against a running copy of the portal, including its restore path (it went red on a
rehearsal fault, restored byte-identically, then green). Restarts `clinic-portal` only. Touches no Sanjeevni file,
not `finance_app.py`, not `call_hook_capture.py`.

# HANDOFF RUNBOOK — 2026-08-08 · Session 159 · v97 (Tier 0)

**Dr. Manoj Agarwal Clinic · Bareilly.** Supersedes v96. §0 = what just happened · §1 = mental models · §2 = the live backlog.

---

## §0 — WHAT HAPPENED THIS SESSION (S159)

A build session on the **doctor portal** (backlog item 3). Phase 0 verified all 26 canonical rows by md5 — **zero mismatches**; the long-pending S150–S158 install had landed. Owner directed: item 1 **done**, start item 3, fold item 7 into EOS.

- **`portal.py` → `679a00874c039ecabc533f9ddd0f5e67`** (was `c52ab1fd…`, 516→634 lines), live at `/root/portal/`, service **`clinic-portal`** (:8099). Delivery gate: `py_compile` + Jinja render smoke-test (doctor-on-PC / off-PC / manager) — all green.
- **Group C (report-Sheet views) found ALREADY wired** in the live portal — not duplicated.
- **Group D — 4 Clinic-PC-only tiles** (Follow-up 5000 · Vitals 5057 · Case Pack 5058 · CC→Tally 5059): plain links, doctor-only, shown only on a browser marked via **`/portal/mark-pc`** (undo: `/portal/unmark-pc`). No probing → immune to Chrome's localhost tightening (**D267**).
- **2 personal tiles** (CC Statement Saver, Inbox Janitor): URLs read from git-ignored `portal_config.py` (`CC_SAVER_URL` confirmed live; `INBOX_JANITOR_URL` optional) (**D268**).
- **GMB Review Assist → VPS-hosted** at `/portal/gmb` behind login, read per-request from `/root/portal/gmb.html`, works on any device (**D269**). `gmb_serve.py` was built then **retired** same session.
- **CC→Tally VPS-hosting requested → DECLINED** (owner-only finance + feeds PC Tally; D262/D269).

**New fault codes:** **F-59** (Chrome ERR_UNSAFE_PORT on 5060/5061 SIP), **F-60** (VPS case-sensitivity `GMB.html`≠`gmb.html`), **F-61** (code-fence label pasted into config breaks it). **No SOP/surveillance-scope change. No incident.** Two stale doc headers fixed in passing (Archive header v1.9→v1.11; Fault end-marker v2.3→v2.5).

**Decisions D267–D269 · Findings F-59–F-61 minted. Next free: D270 · F-62 · Session 160.**

---

## §1 — MENTAL MODELS (carry these)

- **Phase 0 first, every session** — hash-verify every manifest row before any work (D172/D188/D201). A filename is not provenance.
- **Build from the md5-verified live file**, full-file replacements only, `py_compile` on the **VPS Python path** discipline (F-53), owner installs. String replacement with count assertions, never sed (D202: canonical docs are full files, never deltas).
- **One writer per table; append-only ledger; maker-checker for money.** F-31: salary/finance data never in public repos or shared drives.
- **Portal = SSO broker.** `portal.py` (:8099, `clinic-portal`) issues the `clinic_sso` cookie on `.dr-manoj.in`; attendance/ledger/asset each verify it with their own login as fallback, **inert if the secret is unreadable** (D264). SSO proves WHO; each app's own store decides WHAT (D265); manager can never resolve to a ledger checker.
- **Local vs remote (D262, reaffirmed S159):** localhost apps that touch finance/PHI (5057/5058/5059) **stay on the PC** — never VPS-hosted. GMB is the one exception (static HTML, no data). Capability/secret URLs live only in `portal_config.py`, never the repo (D268/D176).
- **Browser reality:** Chrome 142+ blocks HTTPS→localhost probes (PNA) and refuses SIP ports 5060/5061 (F-59). Prefer server-side gating (a marker cookie) over client-side probing.
- **Secrets:** never displayed by a procedure (D176), masked in commands, git-ignored config only. Coordinate WABA token rotation with Lokesh (D120).

---

## §2 — LIVE BACKLOG (the authoritative open list)

1. **GitHub commits + the item-1 verify.** (a) Commit **`portal.py` `679a0087…`** → `launcher/portal.py` (S159). (b) **External md5 re-check** that the six S158 files landed (`launcher/portal.py`+`clinic_sso.py`+`clinic_users.py`, `attendance/att_dashboard.py`, `assetapp/asset_register.py`, `staff_ledger/staff_ledger.py`) — owner said done; needs the **repo-owner path** to verify via raw CDN. `gmb_serve.py` = retired (commit optional, mark superseded). Older owed: staff_ledger/watchdog mirror, canonical-docs mirror.
2. **Ledger fine-tuning tasks** — owner to detail (carried from S158).
3. 🆕 **Local PC apps — confirm + reliably launch.** Vitals 5057 · Case Pack 5058 · CC→Tally 5059: a **hands-on PC session** to confirm each app actually starts, then a reliable launcher. **NOT VPS** (D262/D269). Owner ruled Task Scheduler *and* NSSM services unreliable → likely a manual one-click launcher, decided live at the PC. Follow-up Tracker 5000 already runs.
4. **Config fill / optional migration** — paste `INBOX_JANITOR_URL` into `portal_config.py` when ready (tile shows MANUAL until then). Optional: migrate the existing hardcoded clinic Sheet tile URLs into config too (D268 scope-B, deferred).
5. **July salary reconciliation** — rupee-by-rupee vs actually-paid (owner carry; July had no APPROVE).
6. 🔴 **Rotate the Google service-account key** (F-56 — rode through an upload; overdue) + **CALLHOOK Steps 3–4** (Lokesh).
7. **August salary run** (~Sep 01–09) — first real **APPROVE & LOCK**.
8. **Parked / small (item 7 family):** Notion — push S159 D267–D269 + F-59–F-61 + portal status; the S158 parked items still open (4 VPS-state flags to verify + D194 duplicate-row deletion). Tidy the stale **`:8090` dev-line** comment in `portal.py` (bundle with the next portal change, not a standalone install). Migrate **`wa_approve`** from nohup → systemd. **WABA sends blocked** vendor-side (D120, Lokesh).

*Backlog pointer for next session: this §2. Next free D270 · F-62 · Session 160.*

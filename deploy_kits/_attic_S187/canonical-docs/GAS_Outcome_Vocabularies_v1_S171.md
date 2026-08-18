# GAS OUTCOME VOCABULARIES — VERBATIM — v1 (S171)

> Tier 1 reference. Extracted **verbatim from live repo code** (S171, 12-Aug-2026):
> `dashboard/Dashboard.html` (L1801, L1904, L1455, L1262, L1276, L1285) ·
> `dashboard/Callconsole.gs` (L989 K_CODE_MAP). Filenames + line numbers are provenance (D188).
> These lists seed the VPS `console_options` store and the Hindi coaching-report label map.
> The doc-summary in Frontend_Dashboard_Documentation v4 §4 under-counts two lists
> (FU has 11 incl. `cant_communicate`; IN_RESOLUTIONS has 6) — **this file wins** (D172).

## 1 · K-set — one-tap, outgoing follow-up + known-patient incoming, connected (K_LABELS/K_ORDER · D214/D227)

| # | Button (exact) | kcode | Sheet code | settle |
|---|---|---|---|---|
| 1 | मरीज़ आ रहे हैं | K_COMING | `k_coming` | settle |
| 2 | नहीं आएँगे | K_NOT_COMING | `k_not_coming` | settle |
| 3 | बात हुई — फिर call करना | K_CALL_AGAIN | `k_call_again` | retry |
| 4 | बात नहीं हो पाई | K_NO_CONTACT | `no_answer` | retry · cross-day miss counter (D220) |
| 5 | डॉक्टर को दिखाना है | K_TO_DOCTOR | → `problem` via saveFollowupOutcome | escalation |

## 2 · Legacy follow-up dropdown (FU_OUTCOMES, 11)

| code | label |
|---|---|
| `coming` | Coming / will visit *(needs date)* |
| `out_of_town` | Out of town *(needs date)* |
| `on_medication` | On medication *(asks source/days)* |
| `cant_communicate` | Connected but couldn't communicate *(only code that stays on the worklist)* |
| `dikha_chuke` | Already visited (dikha chuke) |
| `problem` | Problem / needs attention |
| `close_followup` | Close follow-up · treatment complete |
| `not_interested` | Not interested |
| `treatment_elsewhere` | Treatment elsewhere |
| `wrong_number` | Wrong number |
| `asked_not_to_call` | Asked not to call |

Routing: settle = coming, out_of_town, on_medication (+unreach_*) · escalate = dikha_chuke, problem,
close_followup, not_interested, treatment_elsewhere, wrong_number, asked_not_to_call · else retry.
`wrong_number` / `asked_not_to_call` / deceased → `Do_Not_Call` (D194).

## 3 · Incoming, known patient (IN_REASONS 10 × IN_RESOLUTIONS 6)

**Reasons:** `appointment` Appointment — book / reschedule / cancel · `reports` Reports — ready? ·
`pharmacy` Pharmacy / medicines · `xray` X-ray — availability · `billing` Billing / payment ·
`post_op` Post-op / recovery concern \* · `new_symptom` New symptom / problem \* ·
`info` Directions / timings / info · `wants_doctor` Wants to speak to doctor \* · `other` Other
(\* auto-escalates).

**Resolutions:** `resolved_on_call` Resolved on call · `appointment_booked` Appointment booked ·
`info_given_will_act` Info given, will act · `needs_callback` Needs callback (stays on list) ·
`escalated` Escalate to doctor · `cant_communicate` Couldn't communicate (stays).

## 4 · Incoming, unknown caller — lead set (L_LABELS/L_ORDER · D225) + IN_NEW_OUTCOMES (same codes)

| Button (exact) | code |
|---|---|
| Appointment booked | `appointment_booked` |
| सोच कर बताएँगे | `will_come` |
| जानकारी दे दी | `enquiry_only` *(NOT terminal — lead stays alive, D226)* |
| फिर call करना है | `needs_callback` |
| 🚨 डॉक्टर — surgery / urgent | `escalated` *(instant doctor push)* |
| काम का नहीं | `no_action` |

7th tile slot: **पुराने मरीज़ — नया नंबर** → opens the link-patient form (`inIdentity('existing_new_number')`);
writes no outcome code. Channels: `gmb` Google/GMB · `referral` · `hoarding` · `app` Clinic app · … .
Missed incoming calls keep the old "Log outcome ▾" dropdown (K/L sets are connected-call only).

## 5 · Coaching-report Hindi map (S171 — correct-outcome shown in the staff's own button words)

AI/review verdict → staff wording: `coming`/`will_come`/`k_coming` → **मरीज़ आ रहे हैं** ·
`not_coming`/`k_not_coming` → **नहीं आएँगे** · `call_again`/`k_call_again`/`needs_callback` →
**बात हुई — फिर call करना** · `no_answer`/`no_contact` → **बात नहीं हो पाई** ·
`problem`/`escalated`/`to_doctor` → **डॉक्टर को दिखाना है** · `appointment_booked` → **Appointment booked** ·
`enquiry_only`/`info_given_will_act` → **जानकारी दे दी** · `no_action` → **काम का नहीं** ·
unmapped codes render as-is.

*File enters CANONICAL_MANIFEST at S171 EOS. Owner installs to project knowledge + `canonical-docs/` in git.*

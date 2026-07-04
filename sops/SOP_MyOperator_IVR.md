# SOP — MyOperator IVR & Telephony
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · API Quick Reference Card. KB wins on any conflict.**

> **What this SOP is.** The operational guide for the clinic's phone system — the MyOperator
> IVR (the numbers patients call and staff dial through), the agent extensions, the
> click-to-call dialer, and the call webhooks. Use it when calls don't route, an extension
> is wrong, the dialer fails, or call data stops arriving.

---

## 1. The phone setup at a glance

| Item | Value |
|---|---|
| MyOperator Company ID | `68384350414b9847` |
| Public inbound number | ends in **"93"** — the number patients call |
| Outbound DID (IVR / OBD) | `8065293652` |
| WABA ID | `2101222617483538` |
| Phone Number ID | `1090067637530949` |

**All staff call exclusively through the MyOperator IVR** — there is no personal-mobile
bypass (audit finding D56). This matters: it means call data is complete and the archive can
be trusted as ground truth.

---

## 2. Agent extensions (the roster)

| Ext | Agent |
|---|---|
| 11 | Shavez Ahmed |
| 12 | Shivani Srivastava |
| 13 | Manoj Bhati |
| 14 | Alisha Khan  *(AKEY_14 flagged for rotation)* |
| 15 | Darpan Robert |
| 16 | Reception Mobile |

Extensions map staff to the IVR. If a call reaches the wrong person or "Agent shows as
Staff" on the dashboard, the roster mapping (`Agents` tab / panel extensions) is where to look.

---

## 3. The four telephony pieces (and which SOP/reference owns each)

| Piece | System | Lives | Notes |
|---|---|---|---|
| Call / Logs (history) | A | `developers.myoperator.co/search` | Dashboard reads this live each page load. Low regen risk. |
| Click-to-call (OBD) | OBD | VPS `call_api.py` :8097 | The dialer. E.164 numbers, unique `reference_id` per call. |
| Call webhooks (ended/summary) | C-call | VPS `call-hook.service` :8098 | Writes PHI-clean durations to `Call_Durations`. |
| WhatsApp after-call/missed | B | Panel-native automations | `new_post_call_message`, `eng_missedaftercall`. |

Deep API detail is in `API_QUICK_REFERENCE_CARD.md` and `MyOperator_Call_API_Master_Reference`.
This SOP is the operational layer, not the API spec.

---

## 4. Caller-ID recognition SOP (D93 — the no-code fix)

Older patients don't answer numbers they don't recognise. The fix is a workflow, not code:

1. At the clinic, staff ask the patient to **call the "93" number**.
2. That triggers the post-call WABA template containing the `save.dr-manoj.in` vCard link.
3. Staff **help the patient tap the link** → the outbound DID lands in the patient's contacts.
4. Now future clinic calls show a recognised name → answer rates rise.

(WABA cannot send a native contact card — confirmed three ways — hence the vCard-link route.)

---

## 5. What "healthy" looks like

- Patients calling "93" route correctly and reach an agent / the right IVR flow.
- Staff can place click-to-call calls from the dashboard (agent phone rings, then patient bridges).
- Call history shows in the dashboard (System A live read working).
- `Call_Durations` gets rows for OBD calls (webhook `call-hook.service` up).
- After-call / missed-call WhatsApp messages fire automatically.

---

## 6. Known failure modes & fix paths

### Click-to-call (OBD) fails
- **`403` on placing a call:** almost always a **reused `reference_id`** within ~2 days
  (must be unique per call), OR someone enabled Anonymous Dialer (disabled on this plan —
  use User Dialer).
- **Call never bridges:** OBD is queued, not instant, and 2-leg — the agent's phone rings
  first, then the patient. If the agent doesn't pick up, the patient is never dialled.
- **Number rejected:** `number` must be **E.164** (`+91` + 10 digits). Bare 10-digit or
  12-digit-without-`+` both fail.
- Check the dialer service is up: `systemctl is-active call-api` (:8097) — see `SOP_VPS_Services.md`.

### Call durations stop arriving in `Call_Durations`
- `call-hook.service` (:8098) is down, or the webhook was edited. Confirm the service is up.
- The join key is `client_ref_id` (our OBD `reference_id`) — **not** `ref_id`. Only OBD
  calls carry it; incoming calls are correctly skipped.
- The "reached patient" signal is the **customer leg**: `result == "answered"` + `talk_duration`.
  Do not use top-level `duration` (includes ring + agent pickup).

### Call history not showing in dashboard
- System A (Call/Logs) read is failing. The dashboard reads it live per page load. Check the
  token hasn't changed and the API is responding.

### Wrong agent / "Agent shows as Staff"
- Check the extension roster mapping (§2) and the `Agents` tab. Known display bug, owner
  indicated resolved; verify + close is a standing item.

---

## 7. The two webhooks (do not confuse or cross-edit)

MyOperator panel → APIs & Webhooks → **Webhooks v2** has **two separate** webhook entries:

1. **Message Received** (WhatsApp inbound) → `https://followup.dr-manoj.in/wa-webhook?key=…`
   → `wa-receiver.service` :8095.
2. **Call Ended + Call Summary** → `https://followup.dr-manoj.in/mo-callhook?key=…`
   → `call-hook.service` :8098.

They are separate entries. **Editing one must never touch the other.** Both use a self-chosen
`?key=` gate (not a MyOperator token) — no WABA rotation, no Lokesh coordination needed to
adjust the call webhook.

---

## 8. Manual fallback (dialer / webhooks down)

- Staff dial patients **directly in the MyOperator panel** — the dialer relay is a
  convenience layer, not the only way to call.
- Call history is still viewable in the panel even if the dashboard's live read fails.
- Duration-gate features degrade gracefully; outcomes can still be recorded.

---

## 9. Emergency contacts

| For | Who |
|---|---|
| IVR routing, extensions, panel settings | Lokesh Kumar VB (MyOperator engineer) |
| OBD / webhook behaviour | Lokesh |
| VPS dialer / hook services | Owner (with Claude) — `SOP_VPS_Services.md` |

---

*Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update in the same session
any extension, number, webhook, or dialer rule changes (KB discipline).*

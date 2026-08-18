# S187 — Daily Flow v2, Design Addendum: Returns · 360 · Orthotics · Hub · Remote Access

**Extends `S187_Daily_Flow_v2_Target_Design.md` (D326). Owner directive of 18 Aug 2026.
DESIGN — becomes contract on sign-off; the owner's four decisions are in §8.**

---

## 1. Stage D-R — Returns booked at RECEPTION (the owner's rules, verbatim contract)

The counter flow, as directed:

1. Reception handles the patient: enters available patient details → the system finds
   **related sales** (from `sale_item`/`sale_line_item` + `patient_ref`, and by phone/name
   via the follow-up tracker's Patient_Master when the pharmacy record is anonymous).
2. Staff selects the **drugs to be returned, with quantities**, against the original sale's
   lines (batch, expiry, discount all on record since S183).
3. **Reason for return from a dropdown** (configurable vocabulary; free-text note optional).
4. The form **verifies the return against its initial sale** — `finance_returns`' graded
   matching (D315), surfaced live instead of after the fact.
5. **Eligibility rules, applied automatically and shown as legends:**
   - product **expired** → **INELIGIBLE**;
   - return **more than 2 months after sale** → **FLAGGED** (allowed, marked);
   - **sold ≥ 1 month ago AND now < 1 month expiry remaining** → **DISQUALIFIED**;
   - within limits → eligible, clean.
6. Output: an on-screen verdict with all legends + a **print-formatted return slip** —
   complete enough to conclude the counter transaction independently.
7. **Darpan then books the return in Marg** (the CN bill). When that CN arrives via the
   export, it **reconciles against the reception-logged return** — matched = closed loop;
   a CN with no logged return, or a logged return with no CN after N days, each becomes a
   visible exception. Two independent records again, by construction.
8. The return (and the sale) land in the patient's **360 view** (§3).

**Cash effect:** the refund is cash out of the drawer same-day. The logged return posts a
drawer movement (refund, with the slip number) so Darpan's closing math carries it the day
it happens — not the day the export arrives.

**Data reality (all satisfied):** expiry per line ✓ (`expiry_ym`), sale date ✓, discounts ✓,
quantities ✓, batch ✓. Eligibility is computable exactly as specified.

## 2. Stage D2 (confirmed by the owner): Darpan's mirror

His entry page gains, for the day he is filing: **ICICI settled UPI** (total + count,
match/gap vs his declared) and **the Marg export summary** for that day (present/absent,
total, bill count). Save-then-see with the D326 `edited_after_reveal` badge. Scoped to his
own day; no month views, no cash position.

## 3. The 360 wiring — closing the Console's deferred placeholder

The Console spec (v2.4 §4.4) reserved "last medicine refill" for "the not-yet-built pharmacy
system." It is built. Wiring (read-only, fail-soft, the `clinic_holidays()` pattern —
finance.db opened `mode=ro` from the console side, absence degrades to the old placeholder):

- Patient lookup gains a **Sanjeevni strip**: last refill date, items, amount; full sale
  history expandable; returns with their reasons and verdicts.
- **Refill-skipper intelligence (the owner's "rich data"):** patients whose pharmacy refills
  continue while follow-up visits lapse — refill date present, no follow-up outcome within
  the window. Surfaces as a Console list ("refilling, not following up"), highest-value
  call targets. Read-only analytics; no new writer.

## 4. Orthotics — tracking honest to what the data can support

**What we HAVE:** every orthotics **sale**, item-wise, daily (filter `sale_line_item` by an
orthotics item vocabulary — same mechanism as B4's home-medicine list).
**What we DO NOT have and cannot read:** Marg's **stock levels and purchase records** — the
live tables are encrypted DBFs (S180 recon, settled). Any screen claiming "current stock"
would be a guess wearing a number.

**Design:** an Orthotics section (reception + owner): sales velocity per item (7/30-day),
days-since-last-sold, and a **reorder signal** = velocity × configurable per-item threshold.
Two options for the stock side (§8 Q2): reception logs stock counts / received orders in a
small register (real, human-counted), or velocity-only with no stock claim. Either way the
reorder nudge stops depending on Darpan remembering the Marg purchase screen.

## 5. The owner's one-click Sanjeevni Hub

One portal tile → `/finance/hub`: a strip of section cards — Approvals · Workbench ·
Month · Day Page search · Returns · Orthotics · 360 refill-skippers — each opening in
place or one click deep. The existing pages stay (nothing rebuilt); the hub is the
uncluttered front door. Portal tile count for the owner DROPS (the hub replaces several).

## 6. Reception's authority (new, needs the owner's blessing — §8 Q1)

Returns + orthotics + 360 lookup require reception to have a **screen with identity** —
the stage-only sender token cannot carry a UI. Proposal: a **`counter` role** on the
medical unit (portal login, e.g. user `vinay`): can look up patients, log returns, view
orthotics; **cannot** see cash position, day totals, approvals, or anything checker-side;
every action attributed by name. This extends the S179 role model deliberately and gets
recorded as a decision.

## 7. Remote access — reaching the clinic PCs from yours (separate infra track)

Requirement: your PC → medical PC, same network or different; then lab, reception, manager.

**Recommended: Tailscale + RustDesk.**
- **Tailscale** (free tier, 100 devices): a private mesh between your PCs — each machine
  gets a stable private address reachable from anywhere, NO port-forwarding, NO public
  exposure, encrypted end-to-end, each device approved by you in one admin panel. Works
  identically on the same network and across networks.
- **RustDesk** on top for the screen itself: open-source remote desktop, connects over the
  Tailscale addresses, unattended access with a per-machine password you set. (Windows'
  built-in RDP is the alternative where the PC edition supports it.)
- **Why not simpler tools:** AnyDesk/TeamViewer free tiers throttle commercial use;
  Chrome Remote Desktop ties every PC to a Google login and gives no file-level control;
  raw RDP over the internet is the classic clinic-ransomware door — never without the mesh.
- **PHI note (F-31):** remote access to the medical PC is access to Marg and patient data.
  Device list stays minimal, each PC named, your Tailscale account under your email with
  2FA. The VPS can optionally join the mesh later (SSH without the public port).
- Rollout: your PC + medical PC first (15 minutes each, I guide step-by-step); lab /
  reception / manager PCs after the pattern is proven.

## 8. The owner's four decisions — ANSWERED 18 Aug 2026 (contract from here)

1. **Reception identity: the scoped `counter` role.** A portal login (e.g. `vinay`) that can
   look up patients, log returns, and view orthotics — no cash position, no day totals, no
   approvals; every action attributed by name. Decision-candidate D327 at the close.
2. **Orthotics stock: PURCHASE BILLS SCANNED THROUGH THE ASSET APP** (owner's own answer,
   better than both options offered). The Scan Purchase pipeline already exists — scanner
   widget + shared Sarvam OCR + the portal tile (masked from Darpan since S179). Orthotics
   stock = scanned purchase quantities − Marg-line sales, **both sides real records**. The
   reorder signal compares that stock to sales velocity. Build note: read the asset app's
   scan-purchase data model (Tier-1 Asset Register docs) before wiring; the orthotics item
   vocabulary maps purchase lines to sale lines.
3. **Remote access: Tailscale + RustDesk, approved.** Rollout is guided configuration, not a
   kit — owner's PC + medical PC first, then lab / reception / manager. Runs parallel to any
   build stage, whenever the owner has 30 minutes at both machines.
4. **Build order: PAUSED by the owner.** Three kits are live from this session; the owner
   reviews both design documents first. **The next build starts at the S188 open, on this
   signed contract** — proposed order there: D-R (returns) → D2 (mirror) → 360 wiring →
   Hub → Orthotics.

---
*S187 addendum · contract on sign-off · Register v5.15 current · next free D327 · F-125.*

## 9. ADDED 18 Aug (owner ideation, parked as a stage-D6 candidate): CONTEXTUAL INSTRUCTIONS

Owner: *"generated instructions to use can also populate the portals, contextual to the users —
think about it as a later add-on feature."* Shape when built: a per-role, per-page guidance layer —
the same `<details class="help">` slots the Design Language already reserves, but populated from a
maintained instruction set per seat (Darpan sees his filing steps in Hindi; reception sees the
returns walk-through; the checker sees approval rules), served from settings so wording changes
without code kits. Pairs naturally with the Hindi-labels sign-off and the D2/D-R builds, where the
first user-facing walkthroughs are needed anyway. NOT scheduled; revisit at the S188 contract.

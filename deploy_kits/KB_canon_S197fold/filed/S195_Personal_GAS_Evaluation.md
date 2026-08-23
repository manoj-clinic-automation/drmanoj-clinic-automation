# S195 — Evaluation of the two personal-account GAS projects (22-Aug)

Fresh project exports supplied by the owner; both compared against the repo canon and
audited. **Repo integrity: PASS** — both live projects are byte-identical (normalised) to
their repo copies (`c5c0c7101dae69642db5762f34d32a11` CC saver,
`d730b48d47f9116b98916c4eec102f5b` janitor v2.2). The repo-is-canonical rule is holding.

## CC Statement Saver — CLEAN

Domain-proof by design (matches sender *usernames*, so the 2026 `icicibank.com →
icici.bank.in` and `hdfcbank.net → hdfcbank.bank.in` migrations cannot break it), filename
dedupe per card folder, done-label bookkeeping. No changes needed. Minor note only: a
thread is marked done even when no PDF was attached — harmless.

## Inbox Janitor v2.2 — ONE CONFIRMED BUG → v2.3 shipped

**`RULE_REPORTS` went blind to the merchant statements.** Its query pins the OLD domain
(`MERCHANTSOLUTIONS@icicibank.com`); the mails now come from
`merchantsolutions@icici.bank.in`. The CC saver in the *same account* was explicitly built
domain-proof for this exact migration; this rule was not.

**Primary evidence (this session, not inference):** of 141 sampled MerchantStatement
mails, **132 sat in INBOX, 69 unread** — precisely the signature of the label/markRead/
archive-after-2d rule no longer matching. ~5 mails/day piling up since the migration.

**Fix — v2.3** (`gmail-automation/gas/inbox_janitor_v2.3.gs`, **final md5
`3be9bb77f5ec7a9d26e498da438c0a79`**): username-only `from:(merchantsolutions OR …)`,
version header bumped, full-file paste over the project. All other rules checked: they
already use the new domain or username-only forms — this was the only stale literal.

**This is the two-copies-of-a-rule fault class again**, cross-account this time: the
domain-proofing rule existed in one script and not its sibling. Flagged to the Auditor
(slice 5, the perimeter).

## The janitor also *answered* an open question

Its bank-alerts rule lists sender `corp.stmnts` — almost certainly the **YES BANK account
statement** sender (Amir's needed statements). Bank_Statement_Relay.gs's survey query now
includes `corp.stmnts` and `estatement` as **candidates** (still survey-first; the survey
must confirm before anything relays). Relay updated in `deploy_kits/S195_STMT/`
(`fe3fb672…`). Interaction checked: the janitor archives these mails after 7 days, but the
relay searches all mail, not `in:inbox` — no conflict.

## The renewals questions — ANSWERED by the owner, array updated in v2.3

1. **`dr-manoj.in`: renewed, AUTO-RENEW is ON, and the GoDaddy login is the CLINIC
   Google account** (drmka.ortho — worth remembering: domain recovery goes through the
   clinic account, not the personal one). The RENEWALS entry now points at **2027-08-29**
   with its job changed from "renew" to "**verify the auto-renewal actually charged**" —
   an auto-renewal that silently fails on an expired card is the same outage one year
   deferred, and the entire VPS estate rides on this domain.
2. **`drmanojagarwal.in` is being RETIRED, not transferred** (owner decision, pre-dating
   today). Both its entries — the past-dated JustDial→Hostinger ACTION and the 2027-06-01
   renewal — are **withdrawn from the array** with a comment saying why. Note: if
   `syncRenewalReminders()` ever created a calendar event for the 2027 renewal, removing
   the array row does not delete the event — dismiss it if it surfaces next June.
3. `Bhawna DL` renewal date still `TODO` in the array (nagged by the digest — working as
   designed).

## To deploy (both personal-account, ~2 min)

1. Paste `inbox_janitor_v2.3.gs` (`3be9bb77…`) over the Janitor project's file, save.
   Optionally run `sweepBacklogOnce()` twice to clear the MerchantStatement backlog.
2. The relay/filer setup is unchanged from `S195_Monthly_Cycle_Discovery.md` — survey
   first, fill senders, then triggers.

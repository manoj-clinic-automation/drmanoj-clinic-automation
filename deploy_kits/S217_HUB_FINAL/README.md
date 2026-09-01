# S217_HUB_FINAL — the final run on the hub page (owner's batch order, 01-Sep)

Base bytes verified against live pins before anything is replaced:
finance_approvals.html 71522939 · darpan_card.html 29f30ba8 · VPS_Push_UPI.gs
fac84c5b. The install paste REFUSES if the live files have drifted.

**What changes, item by item (his list):**
1. **Alert bar** at the very top, never collapsed — a weekday not filed ("अभी
   FILE नहीं हुआ"), a filed day whose bank statement has not arrived ("drawer
   will read INFLATED until it lands"), "Docterz report upload pending for
   <date>", and a Latest-filed line (who, when, approved when). Server-composed
   by the new read-only route `/finance/api/statement-health` (maker+checker).
2. **Chips expand their card** (a collapsed card no longer swallows the jump)
   and a "**Needs you, by name**" list under the tiles names each item with
   its section — days awaiting approval, unexplained rows, bank-vs-entered
   rows, returns needing a decision.
3. **Returns is its own card** at the top of the Marg area with a **month
   picker** (August is one click back) — same sump API, ?month= existed since
   S213 — expandable to bill and drug-line level as before.
4. **Declared vs bank** now names the likely cause when bills declare more
   digital than the bank settled ("cash sale marked UPI at the till"), opens
   that day's bills in place, and links the corrections page.
5. **Parked "awaiting patient names" rows expand to their own bills** (the
   day-gaps rows, same server rule) with masked phone last-4; the Docterz
   pending banner sits inside the section too.
6. **Darpan's card**: a Hindi notice whenever the bank's UPI report has not
   arrived — "दिन में बाद में दोबारा देखें — तब तक दराज़ की रक़म बढ़ी हुई दिख
   सकती है" (fail-soft if the route is unreachable).
7. **legacy_sweep.py** closes every pre-17-Aug open difference under the
   owner's delegated ruling (rows kept, resolution recorded; the live-era
   28-Aug ₹5,688 flag STAYS).
8. **VPS_Push_UPI.gs v3** (paste into the clinic-Gmail Apps Script): hourly
   pushes instead of one 09:30 run, plus a 15:00 shout when today's statement
   mails have not arrived at all (skipped when the business day was Sunday —
   a warning that cries wolf is worse than none).
9. Look: nav wraps instead of clipping; no doubled carets; alert styling in
   the Clinic Design Language tokens.

**Walked offline in a real browser (see EVIDENCE_walk_01Sep.txt), route
rehearsed against the real backup, sweep rehearsed on a copy.** The real
LIVE-SHAPE walk is the owner reloading the page after the paste.

**Rollback:** the paste writes `.bak_S217` beside both HTML files; the
finance_app patch writes its own timestamped backup; the sweep only flips
status (rows and history kept); GAS keeps v2 in version history.

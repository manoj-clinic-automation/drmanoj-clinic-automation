# Claude Code brief — S439_SCANS_SMS_SCROLL (the scan matcher made to match what OCR actually reads; the bank-SMS door made to accept the phone's posts; the approvals Days section keeps its place)

Written 30-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S439 · faults F-660, F-661** (claimed on the System Board).
Runs AFTER S437 (live 28-Sep 23:09 IST). **S438_COUNT_BOOK is HELD by the owner — do not build it.** Touches `purchase_app.py` (the S403
matcher), `bank_sms.py` (the S405 door), and ONE anchored change in `finance_ui/finance_approvals.html` (the parent's file, declared).
The asset app (`/root/assetapp`, the parent's) is READ ONLY here. Restart `clinic-finance` only.

## 1 · The owner's words (30-Sep)
"Yesterday reception scanned all medical bills of September (101), but the system is showing very few — check." "SMS from MacroDroid
doesn't appear on the Sanjeevni page; only the bank statement is seen." "My Sanjeevni page — the Days section scrolls back to the top on
any Approve; make it stay there."

## 2 · What the chat read on the box (30-Sep, read-only; REPORT the same facts first, then fix)
- **Scans (F-661).** `assets.db bills`: 86 rows since 28-Sep (80 captured, 4 draft, 2 rejected); 79 on the pharmacy lane; `purchase_scan_link`
  holds 26 for September; **51 pharmacy scans unlinked** although ~30 have their bill on the server. OCR reads the bill, the S403 matcher
  (`purchase_app` — grades EXACT vendor+bill+amount · PROBABLE bill+amount~2% · vendor+date+amount) does not forgive its form:
  bill numbers with prefixes / leading zeros (scan "A000166" vs Marg "166" KEDAR; "GPPL-26-64906" vs "64906" GUNINA ×6; "NOT015521" vs
  "15521" JUBILEE; "SF 003051" vs "3051" SHIVAAZ; "A007234" vs "7234" ESS KAY; "G-4430" vs "4430"; "T005620" vs "5620"; "A000601" vs "601"
  DEEPAM); OCR years off ("2024-09-14", "2028-09-09", "2036-09-14", "2018-09-25", "2025-09-09"); the buyer read as the vendor ("SANJEEVNI
  MEDICOS" / "M/S SANJEEVINI MEDICOSE" on 7 scans); vendor misspelt ("KEDAR PHAMACEUTICAL", "KEEDAR", "SUNINA / CUNINA / QUNINA
  PHARMACEUTICALS", "SHIVAZ"); one true digit error (L.K. "KT-078347" vs 78354). 12 scans are bills of 25–29 Sep not yet in Marg (Amir
  enters twice a week; last bill on the server 25-Sep). 13 September bills on the server have no scan at all (1–3 Sep: DEEPAM 545,
  JANTA 18108, KEDAR 160/162, L.K. 75707/75904, YOGENDRA 14928, SHIVAAZ 2888; DRUG DEAL 5207, RAVI 7617, SAISUN IP006767 …).
  Matching runs only at intake (S403/S409); a bill entered in Marg after its scan is never re-tried.
- **SMS (F-660).** `bank_sms_ignored`: 5 posts (28-Sep 01:19 ×2, 09:18; 29-Sep 07:01, 17:14 — bank-SMS times), every one
  "not a bank SMS this door reads" with `phone_sender` and `masked_text` EMPTY; `bank_sms_settlement` and `bank_sms_yes` have 0 rows ever.
  `bank_sms.py` ~447: `text = request.values.get("text") or js.get("text")`, `sender = …("sender")` — the macro posts different field names
  (or the text in the raw body); the refused note keeps no field names, so nobody can see what arrived.
- **Scroll.** `finance_approvals.html` `approve()` → `load()` (the whole page) → every section's innerHTML is emptied and rebuilt → the page
  shrinks and the browser lands at the top. The rules block already does it right (line ~1008: remembers `pageYOffset`, restores after render).

## 3 · The build

### 3.1 The matcher (`purchase_app.py`, the S403 match; F-661)
- **Bill-number normalisation** on both sides: keep the trailing digit run (strip letters, dashes, spaces, leading zeros): "GPPL-26-64906"
  → 64906; "A000166" → 166; "NOT015521" → 15521; "SF 003051" → 3051; "18112 (NOT015878)" → the LAST digit run 15878 wins, the first kept as
  a second candidate. Grades gain **`bill_tail + amount ≤ 2%`** (PROBABLE) and **`bill_tail + vendor` (EXACT when the amount is also within
  2%)**.
- **Vendor by similarity**: normalise (upper, letters only, drop PVT/LTD/M/S/BAREILLY/EXTN), then token-set similarity ≥ 0.7 against
  `purchase_vendor_alias` + the supplier list; a match learns the OCR spelling into `purchase_vendor_alias` (audited "S439 learned from scan
  <id>"). **Buyer as vendor**: any vendor text matching SANJEEV*/MEDICOS* → vendor UNKNOWN; the scan matches on bill_tail + amount (+ date
  month) only.
- **Dates**: an OCR bill_date whose year is not this or last financial year is ignored (never blocks; the month from the digits may still
  narrow); `vendor+date+amount` uses ±3 days.
- **Re-match**: a `rematch(count)` pass over every captured, unlinked pharmacy scan runs (a) at every Marg purchase export (the push door
  of S26x — hook after `purchase_bill` rows land), (b) nightly at 23:59 (one root cron line, declared) and (c) once at install. Every link
  written is audited with its grade and the rule that made it. A scan matched to a bill that already has a scan → `dup_cand` on the scan,
  never a second link.
- **The owner's view**: the porders / purchase "without scan" list (S403) shows, per unmatched scan, WHY (no bill on server yet · vendor
  unknown · amount differs · no digits read) so reception is never asked to re-scan what is already there. Say in the report how many of the
  51 the rule links at install (expected ≈ 30), and list the ones still open with their reason.
- **The 15 scans that never arrived**: read the asset app's intake log / journal for 29-Sep 12:30–14:00 IST (read-only) and say what
  happened (refused uploads, duplicates folded by the guard, phone-side failures). If the cause is in the asset app, name it for the parent
  and change nothing there.

### 3.2 The SMS door (`bank_sms.py`, S405; F-660)
- Read the text from ANY of: `text`, `message`, `msg`, `body`, `sms`, `content`, `v1`; the sender from `sender`, `from`, `number`, `address`,
  `v2`; JSON, form or query alike; and if none is present, the **raw request body** (up to 600 chars) as the text. Case-insensitive keys.
- A refused post keeps the **field names it carried** (`fields` column: e.g. "message,from,ts") and a masked 60-char sample, so the next
  refusal is readable. Never store the key.
- Re-run the door's parser over the 5 refused posts at install if their raw bodies are retrievable (they are not — say so); otherwise the
  first real SMS after install proves it: the report names the first accepted row (masked) or, if none arrived by report time, the
  test the walk ran with a crafted MacroDroid-shaped post (field names `message`/`from`).
- The phone-setup page (S407) gains one line naming the accepted field names, so the macro never has to change.

### 3.3 The Days section keeps its place (`finance_ui/finance_approvals.html`, PARENT'S — one anchored change, declared)
`approve()` success path: instead of `load()`, remember `window.pageYOffset`, call `loadDays()` (and the Needs-you strip refresh only),
and restore the offset after `renderDays()` — the same pattern the rules block uses. The month `<details>` that was open stays open
(`openDays`). Nothing else on the page changes.

## 4 · Pins — read live: purchase_app.py (S437's TO — read live), bank_sms.py (S405's TO — read live), finance_ui/finance_approvals.html
(the parent's; S428's TO 9d1eddc8 unless moved — read live, anchored), the S407 phone-setup page file (one line). READ ONLY: /root/assetapp/*,
assets.db, the asset intake log. One root cron line (23:59 rematch), declared. Restart `clinic-finance` only.

## 5 · Walk (scratch copies of finance.db and assets.db; rows keyed W439*)
Matcher: the seven real OCR forms above (crafted copies) each link to their bill by the named rule; "18112 (NOT015878)" links by its last
run; a year-off date does not block; "SANJEEVNI MEDICOS" as vendor links by tail+amount; a misspelt vendor links and the alias is learned
once; a bill already linked is never double-linked (dup_cand set); the rematch pass is idempotent (second run links 0); the WHY list
shows the four reasons · SMS door: posts with `message`/`from`, with `body`/`number`, with a raw body and no fields, all accepted when the
text is an ICICI/Yes Bank SMS; a non-bank post refused with its field names kept; the key never stored · Scroll: after a crafted approve
the Days section re-renders, the open month stays open, and the recorded offset is restored (assert the function calls, no browser) ·
negative control (old files: the seven forms fail, the door drops the fields, approve calls load()) · dates computed from today · S403
52/52 and S405's walk re-run green (assertions adjusted only where this brief changes behaviour, named).

## 6 · Done means
Kit `deploy_kits\S439_SCANS_SMS_SCROLL\` · installed · published · `claude_code_briefs\REPORT_S439.md` — owner lines first: how many of
the 51 scans are now linked and the list still open with the reason each; what happened to the 15 that never arrived; whether an SMS has
been accepted yet; the Days section fix in one line; ending with `https://followup.dr-manoj.in/finance/approvals` and the purchase
"without scan" page's full address.

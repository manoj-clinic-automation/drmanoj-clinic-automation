# Claude Code brief — S436_STAFF_PAGES_CLEAN (Darpan's orthotic answers made one-option, Amir's board reduced to his work, the wrong-salt pairs, the renames card gated)

Written 28-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S436 · decision D638** (claimed on the System Board; S433–S435 are
the parent's). Runs AFTER S432 (live 28-Sep 07:52 IST). **Staff-facing pages stay Hindi; owner-facing English. Sanjeevni-owned** (stockmatch.py/html,
stock_amir.html + its routes in stock_app.py, section/pair logic of S404/S228, the orthotic round of S404, purchase_salt_task). No parent file.
Restart `clinic-finance` only. Count #1's medicines are closed (S427); the orthotic section is OPEN — this kit closes it by rule.

## 1 · The owner's words (28-Sep 09:5x IST, on the live pages)
Salts: "PARI CR 12.5, LINVIZ and LACTOVAX have wrong salts in Marg, so the pairs can't be matched — Pari is paroxetine, Lactovax is a laxative
syrup, Linviz is linezolid 600." Darpan's Stock milaan, orthotics: "for the orthotics found less than Marg he writes 'does not know' — it should
be 'sold without bill'; 'went out never came back' is irrelevant — remove; 'does not know' — replace with sold without bill; 'broken or damaged'
is not part of this flow — remove; in Darpan's milaan 'toota kharab', 'vaapas nahi aaya', 'pata nahi' need removal, only the left option stays;
then we compute the orthotic loss for the deficient items; Darpan's responses on deficient items go to the 'bill nahi' option automatically for
those he has entered." Amir's board: "renames should appear only when our flow is ready; 1 'Reports the server still needs from Marg' — its
contents need scrutiny and improvement; 2 'Waiting to go on a voucher (48)' is of no use — he gets only the vouchers he needs to make; the
Round-2 Excel — no need for Amir, remove; 'What is behind them' (the three Excel lists) — he is only for doing entries in Marg, remove; he does
the vouchers, uploads the suitable report, gets confirmation, any remaining work and any corrections; 3 'Type Darpan's answers' and 5 'Orthotics
by family' — irrelevant, remove; 6 'Naam badlo (23)' — only when the system is ready." "I need a proper clean build."

## 2 · What exists (read live; the owner's saved copy of Stock milaan and the round-2 workbook are in the chat's uploads, not needed)
`stockmatch.py` df5501ea (S432's TO — read live) / `stockmatch.html`: cards *Aaj ki ginti* (S428), the staff block (S427), *Dobara ginna hai*,
*Stock batao*, *Kuchh gadbad hai?*, **Orthotics** — *Adla-badli?* (9 pairs, answered) and *Kam kyun?* with four reasons per short line
(Galti se bill nahi bana · Toota / kharab · Vaapas nahi aaya · Pata nahi) and two per extra line; `stock_diff.cause` vocabulary (S221:
`sold, no bill was made`, `broken or damaged`, `went out, never came back`, `does not know`, `billed, not handed over` …); the hub's orthotic
block "your one-tap change" and **Make the orthotic round (18)** (S404); the same-salt pairs (S228 matcher on `purchase_salt_marg`);
`stock_amir.html` + routes: sections 1 Reports needed (S221 ledger questions from the OLD tables), 2 Vouchers (waiting list 48 + rounds +
Excel links + "What is behind them"), 3 Type Darpan's answers (S227, retired path), 4 Files, 5 Orthotics by family (S235), 6 Naam badlo (23,
D620 rename memory), the salt tasks (`purchase_salt_task`, S243). The statement (S431/S432) and the Loss desk read the orthotic outcome.

## 3 · The build (D638)

### 3.1 Darpan's Stock milaan — orthotics, one answer
- *Kam kyun?*: a **short** line offers ONE button, **"Galti se bill nahi bana"** (cause `sold, no bill was made`); an **extra** line offers ONE,
  **"Bill bana, diya nahi"** (cause `billed, not handed over`). The buttons *Toota / kharab*, *Vaapas nahi aaya*, *Pata nahi* are gone from the
  page (the cause values stay in the vocabulary for old rows; the diffs page chips for medicines are untouched).
- **By rule at install (seed, audited "rule D638, 28-Sep"):** every orthotic short line Darpan answered `does not know` (10 lines) becomes
  `sold, no bill was made`; the two he has not answered (FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S) get the same by default, marked
  "default — Darpan ne nahi likha", and stay tappable for him. The extra lines with `does not know` (CERVICAL COLLAR SOFT HOPE L — Marg
  negative, a book correction; SHOULDER IMMOBILISE UNISON M) become `billed, not handed over`. The owner's "one-tap change" on the hub stays
  for any line he wants to overrule.
- The 22 renames: nothing on Darpan's page.

### 3.2 The orthotic loss, computed; the round made by rule
When no orthotic line is open (after 3.1 that is now), the section closes by itself: each short line = **orthotic loss at selling price**
(the statement's price rule, S431) recorded as `stock_writeoff_run` group `ortho_loss` ("Orthotic loss — sold without bill"), each extra line a
book correction, and **the orthotic round is made without a tap** (S404's round maker, ≤ 6 lines a voucher) on Amir's board; the hub's orthotic
block shows CLOSED with the totals; one Needs-you line to the owner: "Orthotics closed: N lines short, Rs X at selling price; round of 18 on
Amir's board." The statement's Orthotics section reads the outcome ("orthotic loss · on voucher round N"). The Loss desk's staff block gains
one line at its foot: "Orthotics — Rs X (N lines, bina bill)" — orthotics stay separate, never merged into the medicine figures.

### 3.3 The wrong-salt pairs
Same-salt pairs whose salt is wrong in Marg are **not swaps**: ETOZOX 90 ↔ PARI CR 12.5 (unanswered on the hub) → "No — not a swap, salt
wrong in Marg", audited; LACTOVAX ↔ LINVIZ 600 and LACTOVAX ↔ FEBUTAL are already "No" — leave them, add the same note. The matcher must not
propose a pair whose salt is on the salt-fix list (3.4) until the fix is seen in a later salt export.

### 3.4 Amir's board — only his work (Hindi, one screen)
Sections, in this order, nothing else:
1. **वाउचर — Marg में डालने हैं**: the rounds only, each round a card with its Marg vouchers (≤ 6 lines each), the lines readable inline (item ·
   ISSUE/RECEIVE · Marg से → तक · कितना), one tap **"Marg में डाल दिया"** per voucher with Marg's voucher number typed; a round's card
   collapses when every voucher is entered. Order: round 2 (medicines, 20 vouchers) · round 1 (owner's use, 1) · the orthotic round (from
   3.2). **Removed:** "Waiting to go on a voucher", every Excel link, "What is behind them".
2. **वाउचर के बाद — Marg से closing stock निकालें**: one instruction line (the whole-stores closing stock export, the usual way — it travels
   by itself), and the confirmation the proof gives when the next export lands: "Marg = shelf: 371 of 373 · 2 to correct: …" (the hub's step 5,
   read here in Hindi); until then "अभी बाकी". The file-upload box of old section 4 stays here only as the fallback ("रिपोर्ट यहाँ भी भेज
   सकते हैं").
3. **सुधार — Marg में ठीक करना है**: (a) **Salt theek karo**: JARDIANCE 25 (ETOROCOXIB 90 → EMPAGLIFLOZIN 25), PARI CR 12.5 (→ PAROXETINE CR
   12.5), LACTOVAX SYP (→ the laxative — take the salt Marg's own item master gives for it; if none, "LAXATIVE (LACTULOSE)" and say so in the
   report), LINVIZ 600 (→ LINEZOLID 600) — seeded into `purchase_salt_task` with the owner as the source; each clears itself when the next salt
   export shows it; (b) **Rate daalo**: the two orthotic items without a selling rate (FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S);
   (c) **Naam badlo (23)** — shown ONLY when the orthotic round exists and every earlier round is entered (the flow "ready"); until then a
   one-line note "नाम बदलना — बाद में, जब वाउचर हो जाएँ". Each rename ticks itself from the next export (D620).
4. **बाकी काम** — anything the system still needs from him, one line each (today: none).
**Removed from the page:** section 1 "Reports the server still needs from Marg" (the S221 ledger questions were built from the old tables;
the spine answers most of them and the rest are the owner's traces, not Amir's — they leave Amir's board; the route may stay for the
owner's reading, say where), section 3 "Type Darpan's answers", section 5 "Orthotics by family". The purchase-side cards of Amir's day
(S241 amir_day) are not on this page and are untouched.

### 3.5 Settings — none new.

## 4 · Pins — read live after S432: stockmatch.py, stockmatch.html, stock_amir.html, stock_app.py 02ad3d6a (the amir routes, the orthotic
round maker, the pair vocabulary), stock_hub.html 38e0537c (the orthotic block's CLOSED state), stock_statement.py 05c63235 (the ortho_loss
outcome), loss_piles.py 2501b55a (the staff-block foot line), stock_watch.py 5114e01f (the Needs-you line via its existing hook — or
sanjeevni_approvals.py 3999c4ce, say which). Spine read-only. No parent file. Restart `clinic-finance` only.

## 5 · Walk (scratch copy of the live database; rows keyed W436*)
Darpan's page: a short orthotic line shows exactly one button, an extra line exactly one; the removed words appear nowhere on the rendered
page; the seed converted the 10 + 2 + 2 lines with the audit; the owner's one-tap change still overrules · the section closes by rule, the
ortho_loss run has one row per short line at selling price, the round exists with ≤ 6 lines a voucher, the hub says CLOSED, Needs you has the
line, the statement reads "orthotic loss", the staff block has the foot line and the medicine figures are unchanged · ETOZOX/PARI is "No"
with the note; the matcher proposes no pair on a salt-fix item · Amir's board: only the four sections; no waiting list, no Excel link, no
"behind them", no section 1/3/5 text; "Marg में डाल दिया" records the voucher number and collapses a finished round; the salt tasks seeded;
Naam badlo hidden until the orthotic round exists and earlier rounds are entered, then shown · bhati/darpan/shavez gates as before · S427
82/82, S428 73/73, S430 42/42, S431 56/56, S432 68/68, S404 65/65 re-run green (assertions on the removed reasons and the orthotic open
count adjusted, each named; dates computed from today — never hardcoded) · negative control.

## 6 · Done means
Kit `deploy_kits\S436_STAFF_PAGES_CLEAN\` · installed · published · `claude_code_briefs\REPORT_S436.md` — owner lines first: the orthotic
loss (lines, Rs at selling price, the items), the round on Amir's board, what Amir's board now shows in four lines, the four salt tasks;
ending with `https://followup.dr-manoj.in/finance/stockmatch`, `https://followup.dr-manoj.in/finance/stock/page/amir?count=1` and
`https://followup.dr-manoj.in/finance/stock/page/hub?count=1`.

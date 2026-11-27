# S969_STOCKCHECK_DESK_WRITES — the Stock check desk's buttons (kit A2 of S534_FINAL_BUILD_PLAN; built at Sanjeevni session 536, 27-Nov-2026)

**What he asked (D1090, D1092):** on the one Stock check page (kit A1, S967), his own call on every short: **Write off** (a Stock Issue on
Amir's card) or **Pursue** (a recount on Darpan's next list first), the allowance group written off in one go — two taps, no pop-up (his
18-Nov rule). His "ok" 09:25 IST 27-Nov on mock-up v9 (`https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF`); his "build" 12:10 IST 27-Nov.
With it F-1712: the old counts whose "count again" reached no list, and a phone alert for every morning list.

## The desk — `stock_check.py` 5f1b239e → v1.7, `stock_check.html` a9f7b682
`POST /finance/stockcheck/api/desk/act` (the owner only — role checker) `{act, item, items}`. The desk is built afresh first; a button acts
only on a row the desk offers it on — a double tap, a stale page or a row that moved meanwhile writes nothing (409).
* **Write off** (box 1 rows judged a fresh loss): one line per item on Amir's card — `amir_job` kind `tap`, key `S969:wo:<day>:<card>:<item>`,
  the S957 words `"<ITEM> — Marg mein STOCK ISSUE kijiye: 6 patte"` (quantity words from `qty_words`, as Darpan's). **The day's write-offs
  ride ONE card** (one voucher, one *Kar diya*); **a card Amir has tapped done never grows** — the next write-off opens the day's next card.
  An item already written off and not done is never written twice. The batch is only SUGGESTED (sub-line, Hindi): Marg's newest Batch Stock
  report, nearest expiry first, until the quantity is covered (two at most) — "Marg mein jis batch mein maal ho, wahi lijiye". Its own row in
  `stock_desk_action` (pack, units, the count it acts on, the batch suggested, by).
* **Pursue** (box 1): `stock_watch.ask(mode=None)` — a new ask at the head of Darpan's next morning list; an open ask is never moved. The row
  stays in box 1 tagged *Pursue — on Darpan's list*, no buttons. **End rule:** the recount agrees with Marg → the row closes by itself under
  Settled ("a count error"); still short → back in box 1 with BOTH counts in its path and both buttons again; counted but the stock of record
  not yet built on it → *recounted — the record catches up*, no buttons.
* **Within the allowance**: one group button, *Write off both / all N*, onto the same day's card.
* **Count first — an old count differs from Marg** (F-1712): every item whose shelf figure is only an old count carried forward (`old_base`)
  and differs from Marg, not already shown in boxes 3–4: **Next list** per row, and *All N on Darpan's next list*. Never a write-off.
* No button on an evening count still waiting for its sales; *about a delivery* rows get Pursue only.
The table is made by the installer (and by the first write); nothing is written until his tap. Buttons are drawn only for him.

## Amir's card — `amir_day.py` 1cf0f13f
The day's write-off lines are drawn as ONE card: "STOCK ISSUE · dd-mm — Ek STOCK ISSUE voucher banaiye — in sab ka:" with each item, its
quantity and the batch line, and one *Kar diya* (`tapg:<day>:<card>`) that marks every line of that card done. His other one-time jobs keep
their own lines and buttons.

## The judge — `voucher_judge.py` aea43633 → v1.2
A desk Write off's pack and units come from `stock_desk_action` (never read from the Hindi words with a guessed pack). Still read only.

## The morning list — `stock_watch.py` e205f889 → v1.15
F-1712: every morning list written reaches Darpan's phone (one push naming the items) — before, only a list with the owner's asks did.
Once a day (the list is written once). Setting `count.push_every_list` (1; 0 keeps it quiet).

## Proof
* `walk_s969.py` **49/49** on made-up data (S967's fixture with three items added), twice on one layout; the control on the live files red at its
  first line (no desk writes). `walk_s967.py` on the new files 40/41 and `walk_s965_regress.py` 31/32 — only their version lines.
* **Live shape** — the 27-Nov database copy, device VM only: box 1 six (NORTIMER TAB, MEG QCS, CROCAL, TRAMATEE P TAB 15T, PANTAVIN 40,
  ZUPRINOR 5 — each Write off + Pursue), the allowance two (PRETOL-4, TYRO BR), Count first 19. On a COPY: NORTIMER TAB written off → Amir's
  card "NORTIMER TAB — Marg mein STOCK ISSUE kijiye: 6 patte", batch 24006 suggested; the voucher judge reads 60 units. The installer
  repeats this on a copy of the live database.
* Rehearsal on a made-up root (`rehearse_s969.sh`) **12/12**: dry · red@4 · red@5 · the old mount in the log · install (only the empty
  table) · again · undo · install again · wrong FROM · a read pin moved · the lock · a corrupt kit.

## Reviews
**Cold review** (a separate agent): NOT SAFE — 3 MUST, all built in: **M1** the mount opened the database outside a request (the live
getter needs Flask's context) — the install would have rolled itself back; the table is now made by the installer and the first write.
**M2** Amir's one *Kar diya* marked a line added after his page was drawn — the button now carries the highest line it showed
(`tapg:<day>:<card>:<id>`); a later line stays open and comes back as its own card. **M3** a count could be written off twice when the judge
failed — every write is refused while the judge cannot run, and one write-off per count, ever. SHOULD built in: a Pursue is answered only by
the FIRST count after it; a withdrawn ask gives the buttons back; no key clash; the 5-second arm timer cleared.
**Second look** (a separate agent): NOT SAFE — 1 MUST built in: **M1** a new count of an item whose desk write-off Amir tapped done (not yet in
Marg) was offered again (allowance) — such an ask now always holds the item in box 2. SHOULD built in: Darpan's same-day correction of the
pursued count is not its recount; an S936-held recount never answers a Pursue; a written-off row in Marg's report waits in box 2, no button;
the buttons drawn for the owner only (`can_write`).
**Re-look** (a separate agent): SAFE. Built in: a written-off row whose Marg line is not as asked says so; a later count that agrees with Marg
while his write-off is still unkeyed shows RED in box 2 ("not to be keyed"), never quietly Settled.
**Noted for kit B:** withdrawing a desk write-off Amir never keyed; a concurrent second tab could open a duplicate ask (the old
`stock_watch.ask` race); after an undo the old judge reads S969 lines with a guessed pack.

## Install
His publish, then one server line (in the installer's head). Five files placed after backups `*.bak_S969_*`, the table made, clinic-finance
restarted, the doors and the modules checked, the mount proved from the service log ("S930 stock_check mounted v1.7"), the desk read once
on the live database. **Undo:** `bash /root/deploy/repo/deploy_kits/S969_STOCKCHECK_DESK_WRITES/undo_s969.sh` (the five files back; the
table stays, unread).

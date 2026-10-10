# S504_CARD_SPENDS — the card spends, read and named (Club B, part 1)

Session 304 (parent), 10-Oct-2026. The owner, 10-Oct: the card sheet *"is too crude, the explanation of the spend needs a
look for being properly categorised for me and accountant use … like COCO is the main petrol pump where fuel is filled"*.

## What it does
- **Every card statement is read on the server, line by line** — HDFC Business Regalia (its 2025 layout and the present one),
  ICICI Amazon Pay and ICICI Coral — by a new program, `/root/finance/card_lines.py`. The old PC script's one pattern read
  only 5 of 15 HDFC statements; this reads all of them.
- **Each statement is proved**: the debits read must equal the *Purchases* the statement prints, and the credits its
  *Payments / Credits*. On the session's copies: **38 statements, 38 proved, 391 lines**. A statement that does not add up
  is shown in red on the page and is never sent to the accountants as if whole.
- **Each line gets two words**: what it is for him (*Fuel (petrol / diesel)*) and the ledger the accountants post it to
  (*Fuel Expenses*). Kinds are told apart by the statement's own words: card repayments (*Card Payment (Contra)*), fuel
  surcharges and their waivers (netted into fuel), EMI principal (the merchant's category), interest / GST / DCC mark-up
  (*Bank Charges & Interest*), refunds.
- **Known merchants are named already** (COCO Bareilly, Indian Oil, Shakti, Evergreen, Bharat Petroleum = fuel; UPPCL =
  electricity; Central UP Gas = cooking gas; Airtel = phone; Anthropic, Canva, ClickUp, Sarvam, GoDaddy = software; Apple,
  Google Play = apps; IT CC = income tax; ICICI Lombard, National Insurance = insurance; Dr Lal = medical; Blinkit, Amazon
  grocery = groceries …). **The rest — about twenty — wait for him once**, on the packs page under *Name these merchants*:
  he picks what it is, and every line of that merchant, past and future, follows.
- **The accountant pack** gets *Card spends by ledger — <month>.xlsx* (By ledger · Every line · Statements with their
  proof) **when every card's statement of the month is read and proved**; until then the running All_Transactions.xlsx goes
  as before (the manual fallback stays).
- The electricity bill a card pays is looked for in these lines first.

## On the page — https://followup.dr-manoj.in/finance/packs
A new folded section, **Card spends — <month>**: each card's statement and its proof · the month by what it is (his word,
the ledger, spent, credits, net) · *Name these merchants* · every line (folded).

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S504_CARD_SPENDS/install_S504_CARD_SPENDS.sh

## Undo (one line; the two files back, the reader moved aside, the finance app restarted; the card tables stay, unused)
    cd /root/finance && \cp -p packs.py.bak_S504_484dce36 packs.py && \cp -p packs.html.bak_S504_c857718c packs.html && mv -f card_lines.py card_lines.py.off_S504 && systemctl restart clinic-finance

## Files
`card_lines.py` (new) · `packs.py` `packs.html` (as placed) · `make_packs.py` `make_packs_html.py` (each builds its file from
the live bytes by exact, counted edits; the installer rebuilds both on the box) · `walk_s504.py` (`--control` = the
negative control) · `install_S504_CARD_SPENDS.sh` (`DRY=1` places nothing).

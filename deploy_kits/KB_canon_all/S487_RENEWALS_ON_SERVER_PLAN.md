# S487 — RENEWALS: ONE LIST ON THE SERVER, THE JANITOR AS ITS MAIL FEEDER (kit S890) — plan v2, 18-Nov-2026 22:0x IST

**His word (21:56):** the renewals section lives wholly on the server; the Google Sheet is not used for renewals; the Janitor (personal Apps Script) is the back support that reads Gmail and keeps adding to the server list (renewals and any new item); the Scan App's present renewals integration is to be studied, refined and corrected. **Approved earlier (21:37, 21:54):** mock-up v2 (the page with days left, + Add renewal, Mark renewed) and the folder tile with three equally bold lines (Month-end packs · Month checklist · Renewals, the red count on Renewals only). Arms licence: 45 days. **His word 22:35:** he reviews this plan and the mock-ups in a fresh session before any build.

## 1 · What exists today (studied 18-Nov, bundle of 18-Nov 01:35 + the Janitor read live)

| piece | where | what it does | fault |
|---|---|---|---|
| typed list `RENEWALS` (24 rows) + `ANNUAL_RENEWALS` (6) | Janitor `Code.gs` (personal account) | the only real list of licences, documents, insurances, subscriptions | typed by hand; nothing updates it when a renewal is done (the Marg nag after its 08-Nov renewal) |
| `nagRenewals` 08:42 daily | Janitor `Renewal_Nag.gs` v4 | mail to the personal Gmail: 45 d (passport 365 d), weekly → 3-daily → daily, 45 d past | vehicle rulings (insurance 30, PUC 7, RC 45) not applied; a row without a date skipped silently; full document numbers in subjects |
| push to `/finance/api/renewals-push` | Janitor → `finance_app.py` | rows inside 50 d to `renewals_state.json`; the health page's Renewals row | names only, nothing shown on the Renewals tile |
| `syncRenewalReminders` (calendar) | Janitor | calendar events for all rows + the 6 yearly items | **no trigger — never runs**; the 6 yearly items (TVS insurance 05-Dec) reach nobody |
| `monthlyPaymentDigest` | Janitor | 1st of month | **never run** (not renewals; left alone, noted) |
| Sheets *Renewals Master v2*, *Personal Documents* | personal Drive | written once by a one-off; **read by nothing** | out of date (Vento RC differs) |
| `/scanapp/renewals` | `/root/assetapp/asset_register.py` (the Scan App's) | asset warranties / AMCs (`expiries`, entity `asset`), the D664 warranty card, batteries (S571), consumables (owner) | see §2 |

Data fix already made in place (21:5x, `S487_RENEWALS_DATA_FIX.md`): Marg 141167 next renewal 03-Dec-2027; Bhawna DL expiry 09-Jan-2030 (Code.gs fa5cb667 → e68cf3b5).

## 2 · The Scan App's renewals — what is wrong and the correction

1. **Staff document expiries never reach the Renewals page.** `expiries` holds `staff` rows (the staff record's document + due date) and the scan app's dashboard shows them, but `/renewals` joins `assets` only. → a **Staff documents** section on the page.
2. **Default warning 60 days** (`THRESHOLD_DEFAULT = 60`) against his ruling "45 days for every renewal but passports". → new rows default to 45; an asset row with its own threshold keeps it.
3. **Nothing is ever mailed for an asset or staff expiry** — the page is the only place it shows. → they join the one morning mail (§3).
4. **No way to say "renewed"** on an asset row other than editing the asset. → the same **Mark renewed** (new date) on every row of the page; the old row is closed (`resolved=1`) and a new one opened with the new date — history kept.
5. **The health page's Renewals row** reads the push file (`renewals_state.json`), a second copy of a subset. → it reads the one list; the push door stays one week in parallel, then is retired.
6. Batteries and consumables keep their own flows and stay on the page as they are; they do not enter the mail.

## 3 · The design (decided — not for the owner)

- **One table on the server:** `renewal_item` in `/root/assetapp/assets.db` (the Scan App's database, beside `expiries`): what · group (Clinic · NK Pathology · Personal · Vehicle · Civic) · expires on · remind days before · every (1/2/5/10 years, once) · note · renewed on · source (typed / mail / seeded) · open/closed. **Document numbers stored as last 4 only**; full numbers stay in his own papers.
- **Seeded once** from the Janitor's 24 + 6 rows (numbers cut to last 4, the alert dates converted to real expiries; the six yearly items become yearly rows).
- **The page** `/scanapp/renewals` shows, in order: *Found in your mail* (only when there is something) · Licences, documents and subscriptions · Assets (warranties / AMCs) · Staff documents · Batteries · Consumables. **+ Add renewal** and **Mark renewed** write straight to the server; the change shows at once. Owner-only for Personal and Vehicle rows.
- **The morning mail stays where he reads it:** at 08:42 the Janitor asks the server for *today's due list* (one token-gated read; the server computes every lead time and cadence — passports 365, vehicle insurance 30, PUC 7, RC 45, everything else 45, arms licence 45) and sends it from his personal Gmail as today. The script no longer holds any list. Subjects carry last-4 only.
- **The Janitor as the feeder (his word):** each morning it looks in the personal Gmail (last 2 days) for renewal-type mails — *renewed*, *renewal*, *policy issued/schedule*, *licence*, *subscription*, *domain*, *valid till / expiry* — and posts each (sender, subject, date, any date it can read, the item it seems to match) to the server. The page's **Found in your mail** box shows each with one tap: **Apply** (the matched item, the new date pre-filled from the mail or one year on) · **Add as new** · **Not a renewal**. A date is never changed without that tap — a wrong silent change would hide a real renewal. Mails it has posted are remembered; nothing is posted twice.
- **The yearly calendar sync is retired** (it never ran); the server list carries the yearly items into the mail instead. The two old Google Sheets are left untouched and no longer used.
- **The tile:** the *Accounts and month-end* folder tile draws its three tiles as three equally bold lines; the red count on Renewals reads the server list (due within its lead time or overdue). Every folder tile of his home is drawn the same way (one bold line per inside tile).

## 4 · The pieces and their owners

| piece | owner | change |
|---|---|---|
| NEW `/root/assetapp/renewals_one.py` (table, seed, page section, Add / Mark renewed / Found-in-mail, the due-list and mail-intake doors) | the Scan App's folder, the parent building it (PLANNED line on the board at v1810) | new file, mounted from `asset_register.py` by a short guarded block (the S557 pattern) |
| `/root/assetapp/asset_register.py` `/renewals` | the Scan App | the page renders the new sections; staff section; default 45 |
| `/root/portal/portal.py` + `tile_grants.json` | the parent | folder tiles as bold lines; Renewals count |
| `/root/finance/finance_app.py` health row | the parent | reads the one list; the push door kept 7 days then retired |
| Janitor `Code.gs` / `Renewal_Nag.gs` (personal account) | the parent | the typed lists removed after the seed is proven; `nagRenewals` mails the server's due list; NEW `feedRenewalMail_` |

## 5 · Order of work

1. Read the live bytes whole (the 19-Nov bundle): `asset_register.py`, `asset_machine.py`, `portal.py`, `finance_app.py` (renewals parts); a read-only count on the box of `expiries` by entity/state (counts only).
2. Build `renewals_one.py` + the page + the tile on a made-up root; walk with a CONTROL that goes red (a renewed item still mailed; a number longer than 4 stored; a mail applied without a tap; a staff expiry missing from the page).
3. Rehearse the seed on a copy; mock the 08:42 mail from the server's due list and compare with today's mail (every row accounted for).
4. Cold review; his publish (`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`) and one server line.
5. The Janitor changed in place (before/after hash, undo) only after the server list is live and read back; one morning in parallel, then the typed lists go.
6. The Scan App chat told at the close (its page, its database).

## 6 · The mock-ups shown in the S487 chat (for his review)

v1 — the page with the new section (days left, numbers last 4) · v2 — the home tile, the page with + Add renewal / Mark renewed, the Add form, the Drive sheet (the sheet part superseded by D1017) · the folder tile with three equally bold lines (approved 21:56) · v3 — the page wholly on the server: *Found in your mail* (Apply / Add as new / Not a renewal), the main list, assets, staff documents (new here), batteries and consumables as today. The *National Insurance* row in v3 is a made-up example.

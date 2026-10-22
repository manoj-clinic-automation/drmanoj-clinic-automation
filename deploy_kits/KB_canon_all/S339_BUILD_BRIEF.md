# S339 BUILD BRIEF — the Sanjeevni chat · 22-Oct-2026 17:16 IST → 19:46 IST

*The one paper for the next chat (session 340) and for you. Plain words; the detail is in the Archive §S339 and the Book §15V.*

## What you asked

1. The open, then: is reading September's purchase bills — and if needed older ones — useful or crucial for the earliest product mapping?
2. "What will this build do?" → **"Start"** — the combined build (D761), in the chat itself.
3. "Did you check the live pages — what happens to the rejected pharmacy scans already present?"
4. LINVIZ 600: the strip arithmetic, why Marg mismatched, the rates if the packing is changed, the stable long-term fix for our system and for Marg, and a message for Darpan and Amir.

## What we found

- **September: yes, free.** 69 of September's 88 Marg bills were already linked to their scans and read by Claude, so the name list learnt from them at the first pass (69 sure spellings). **April–August: no** — about 460 papers never scanned, for 33 medicines that learn themselves when next bought. **Not crucial:** the four false shorts came from Marg's own two names, two lines on one bill and another dealer's bill; old bills fix none of those (**D762**).
- **The independent read of the build** found five blockers before anything was placed (stock counts would have moved; B-0159's set-aside belongs to the Scan App chat; THIO's price check; bandage sizes merging; LINVIZ being undone). All fixed; the stock figure of all 1,045 items stayed byte-identical.
- **Set-aside scans (F-999):** after the first install the order list offered *Send back* on B-0159 (set aside as B-0157's copy; the server refuses it) and named it in *the same paper twice*. Fixed by S631.
- **LINVIZ 600:** you ordered 10 strips of 10 (100 tablets); Kedar sent 6 strips of 6 (36). 64 tablets are owed, which the list carries as **7 strips of 10**. Marg has three items: the old `LINVIZ 600` (1×10, 30 tablets in stock on 21-10), `ZZLINVIZ 600` (1×6, retired in September) and Amir's new `LINVIZ 600 6T` (1×6, 36 in stock). The order came from Marg's sheet for the 1×10 item (**F-1000**, open).

## What is done

- **Live since 18:58 (S629):** the one name list (Marg's two names for one medicine; each dealer's printed spellings). THIO Q AP came 12, ZUPRINOR 5 came 6, POWERGESIC 100 PATCH *came from Janta (bill 23672)* — their wrong carries dropped. LINVIZ 600 short 7. *Send back* on every scan on an order card; *Change dealer* on B-0161 / B-0167; *the same paper twice* named; "came X of Y" the right way; English only on your pages.
- **Live since S631 (published 19:17:56, installed after it — the owner pasted its DONE line):** *Send back* is never offered on a set-aside scan (the tied scan instead); a set-aside scan is never named in *the same paper twice*. Read live: Send back on 37 scans, none set aside; B-0150 / B-0154 the only pair.
- **D763 — Marg pack changes:** a new item for a new pack; the old item sold first, then retired with ZZ; never change the strip size of an item that still has stock. Messages drafted for Darpan (sell the old LINVIZ 600 first) and Amir.
- Two kits (S628, S630) were refused on the box by their own controls — nothing harmful placed; each was rebuilt (S629, S631) with walks on their own rows (**F-998**).

## What the next chat builds — on your yes only

**F-1000, the pack-change build** (asked at 19:27, not answered): every shortfall and carry counted in tablets; the strip size taken from the dealer's latest bill; one *do this* line on Amir's page when a medicine's pack changes (new item, old item's re-order to zero, retire with ZZ when sold out). Size: **small–medium** — `stock_figure.py`, `order_track.py`, `amir_day.py`. Staff screens: only Amir's gets the one line.

## Yours

1. The publish (this close's record): `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
2. Send the two LINVIZ messages (Darpan, Amir).
3. *Change dealer* on B-0161 and B-0167 on your track page, if the paper's dealer is right.
4. Yes or no on the F-1000 build.

## Still open

- Your note, points 1–4: Marg's monthly reports in Shavez's and Amir's flow — a plan and a mock-up first.
- Kit II — the buying model (shadow first).
- F-987; the purchase page's `staff_send`; `order.lead_days`; the S335 small list. Flacort 6 / Flemcort 6 still on Kedar's card until your word to the vendor.

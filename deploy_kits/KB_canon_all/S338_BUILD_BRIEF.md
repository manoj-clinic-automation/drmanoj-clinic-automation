# S338 BUILD BRIEF — the Sanjeevni chat · 22-Oct-2026 15:21 IST → 16:33 IST

*The one paper for the next chat (session 339) and for you. Plain words; the detail is in the Archive §S338 and the Book §15U.*

## What you asked

1. "start" — the open, then the last close's first fix: **Amir's bank statements vanished from his app** (your note, point 5).
2. A rescan of B-0180 got a new number, B-0205 — why?
3. The order tracker (`/finance/porders/s454/track`): medicines marked "not sent" that are on the bills (Thioq AP, Zuprinor, the patch); no way to send B-0181 and B-0188 back; a bill showing only its total; a scan from another dealer with no way to correct it. "Analyse this page deeply and report all errors and what I am missing."
4. Is a name-mapping in place, or should one be? Then: what exactly is to be built, and how big; the API credits left.
5. B-0176 and B-0157: where to see them, how to change B-0176's lane, which bill B-0157 is.

## What we found

- **Amir's statements (F-988):** his page showed a month's pack only while he had not tapped *Dekh liya*. He tapped September's on 8 Oct at 09:25, so it vanished.
- **The rescan number:** S618 gives every rescan its own new number and marks the old one "rescanned as B-0xxx". The record is right; only the paper gets a second number. **You ruled: leave it; write the new number on the rescanned paper (D759).**
- **The tracker, read whole (the live page by a helper, the code rebuilt byte-exact from the three kits of the morning, the 22-Oct database copies):**
  - **Four medicines falsely "did not come" — and each was put back on that dealer's next order by itself:**
    - **THIO Q AP** (Deepam 12-10) — on Marg's bill A000678 as "THIO Q AP TAB", 10 + 2 free. Marg's order sheet and its purchase report print two names for one medicine (**F-989**).
    - **LINVIZ 600** (Kedar 16-10) — Marg's bill 216 prints "LINVIZ 600 6T", 6 came. Only 4 are short, not 10 (**F-989**).
    - **ZUPRINOR 5** (Janta 12-10) — two lines on bill JP23217, 2 + 4 = all 6; only the first was counted (**F-990**).
    - **POWERGESIC 100 PATCH** (Deepam 16-10) — came on **Janta's** bill 23672 (scan B-0169). Another dealer's bill counts for stock only, so it stayed short at Deepam (**F-991**).
  - Of the seven carried lines, only **C2CALZ (2 strips)** and **XGESIC LA** are truly short. **FLACORT 6 (20 strips): Kedar sent FLEMCORT 6 instead** (the bill says Flemcort; you are asking the vendor).
  - **The duplicate check kept the worst scan (F-992):** Kedar A000211 was scanned three times on 13-10 by Alisha — B-0157 (11:22, only the bottom total) kept; **B-0159 (18:13, the whole bill: Astofen R 10, C2CALZ 18, Flemcort 6 20)** and B-0160 set aside as its duplicates. The paper carries 160. Also B-0150 and B-0154 are two scans of A000678, neither set aside.
  - **The rescan flow (F-993):** the track page counts 4 scans to redo (B-0176, B-0155, B-0157, B-0199) with no button; the scans page shows only the two you had already sent (B-0157, B-0176) with *Withdraw*; B-0155 and B-0199 cannot be sent from anywhere; **a scan the check passed (B-0181, B-0188) can never be sent back.** My S335 board line told you to send those two from a page that cannot (**F-994**, the assistant's).
  - **Wrong dealer:** B-0161 (a Kedar bill saved under Shivaaz — so Toltris Plus reads "not seen") and B-0167 (a second copy of Mannat's B-0173, saved under Yogendra): only *Open the scan*, no correction door (the open item from S335).
  - **Your page's wording (F-995):** counts read backwards ("2 of 1 came"); Hindi "Doctor sahab ne bheja" on your English page; Verma Bros and Bass show *Arrived* though their one line did not come (tapped 22-10 12:29).
  - **The scan note's spelling match (F-996)** is too strict: pack numbers ("TAB ORICOX-P 10*10"), extra words ("NASO B12 NASAL SPRY") or one letter ("ASTUFEN-SP") and it says "not seen on the scanned bill".
- **The mapping:** three pieces exist and do not talk to each other — the ticked renames and the count's accepted spellings; 69 scan spellings learnt per dealer (learnt only after an exact match); Marg's item key, which refuses two items sharing a start. Nothing joins Marg's order-sheet name to its purchase-report name.
- **B-0176** is a Eureka supply for the procedure room in the pharmacy lane (your word). **B-0157** = Kedar A000211 (the paper says 160).
- **API credits:** the runner has spent **$324.31** in 41 runs since 14-Oct ($126.28 since 18-Oct); **$57 remain** (your read of the Billing page). The build was estimated at $50–70.

## What is done

- **S626_AMIR_PACK_STAYS (live 15:40, built in the chat, no API credit):** the newest month whose two statements are on the shelf stays on Amir's page, seen or not, until the next month's pack is ready; a seen month keeps its links without the *Dekh liya* button. `/root/finance/amir_day.py` 1169a3d6 → 2c99c29e. Walk 12/0 on the new file, red on the old; one independent review (no blocker, two installer corrections applied); rehearsed (dry, live, again, a foreign lock, a switch already on, a red restore).
- **D759** — a rescan keeps its own number; the new number is written on the paper.
- **D760** — for the time being an accepted substitute **never closes a line by itself**; it is shown to you.
- **D761** — the combined build, approved ("if all can be clubbed together, then we should do it that way"; "go"), **to be built in a fresh chat in this project, in the chat itself — not the API runner** ($57 left against $50–70).

## What the next chat builds — ONE combined build (D761), in stages, each walked on copies of the live data

1. **One name list for every medicine** — every spelling (Marg's item list, its order sheet, its purchase report, the scanned bills, the count) mapped to one Marg item. It learns only when sure (same dealer, same bill, quantity and rate agree; a name that differs only by TAB / CAP / 6T / 10*10); **strengths and sizes never merged** (the S598 sibling rule kept); unsure → one line on your page, *"THIO Q AP TAB on Deepam's bill = THIO Q AP? Yes / No"*, asked once; **a substitute is only shown, never closes the line (D760)**. Every reader uses it: `stock_figure.carried` / `_line_forms`, `order_track.forms_of`, the carry pass, Amir's bill line, stock. (F-989, F-996)
2. **Marg's matching:** two lines of one item on one bill summed (F-990 — read `_purchase_lines_of` on `spine.db` first: the two ZUPRINOR lines are two batches); a medicine billed by another dealer on or after the order shows *"came from Janta"*, not short, and is not carried (F-991).
3. **The wrong carries go by themselves** once the lines read right (`carry_pass` drops a line no longer short as `came`); LINVIZ 600 carries 4, not 10. Proven on the copy before placing.
4. **Duplicates:** the clearer scan is kept (one with items over one with none); B-0159 takes B-0157's place and its order tie; the B-0150 / B-0154 pair named (F-992). Your open ask for B-0157 may be done by reception before — then the rescan already replaced it.
5. **Send back for rescan on every pharmacy scan** — on the track page's rows and the scans page, including scans the check passed (B-0181, B-0188); B-0155 and B-0199 listed with the button (F-993).
6. **Wrong dealer:** one tap *"Change dealer to the one on the paper"* on the *Saved under another dealer* rows (B-0161, B-0167), the scan's order tie moved with it; the owner and Shavez only.
7. **Your page's words (F-995):** "came X of Y" the right way round; English only on your pages; a card whose lines all did not come shows *"arrived — nothing on it came"*.

**Staff screens do not change.** Size: **large** — about ten files (stock_figure.py, order_track.py, porders.py detect_supplies, order_sheet.py's tie pass, porders_s454.py, asset_register.py's duplicate guard and a dealer door, the owner's track and scans pages). **`/root/assetapp/asset_register.py` moved again at 16:20 IST 22-Oct (the Scan App chat's S627)** — read the board's newest lines and its pin before touching it.

## Yours

1. The publish (this close's record): `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
2. B-0176 out of the pharmacy lane: on its page choose *Clinic bill — asset or consumable* → *move* (it then waits as a clinic draft, where the supplier can be corrected to Eureka), and *Withdraw* its rescan ask on the scans page.
3. When you like: a fresh chat in this project for the combined build.
4. Flacort 6 / Flemcort 6 — your word to the vendor; until then Flacort 6 (20 strips) stays on Kedar's next order card (reception can remove it with *Abhi nahi chahiye*).

## Still open, after the combined build

- Your note, points 1–4: Marg's monthly reports (expiry, near expiry, dump, item list, salt list, the Tally export) in Shavez's and Amir's flow — a plan and a mock-up first.
- Kit II — the buying model (shadow first).
- F-987 (a WRONG Marg bill on *Bill scan karna hai*); the purchase page's `staff_send`; the small list of S335.

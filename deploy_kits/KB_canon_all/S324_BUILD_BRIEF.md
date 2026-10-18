# S324 BUILD BRIEF — the Sanjeevni chat, 18-Oct-2026 (09:46 → 13:41 IST)

*The one paper for the next Sanjeevni session and for Dr Manoj. Also in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S324\` and loose on the SSD (`F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`). The next chat's entry is `START_HERE_SESSION_327.md`.*

## For Dr Manoj — what this session did

1. **Stock is worked out in one place now (kit S577, live 12:14 IST).**
   - One module gives every item two figures — Marg's, and the shelf's (the 6-Sep count carried forward) — each on the closing it stands on.
   - The voucher check for Amir, Darpan's spot counts, the shelf-gap flags, "bill entry baaki" and your *stock now* / *drift* pages all ask it.
   - A renamed item is now recognised under both names.
   - A voucher can no longer take Marg past the shelf figure.
   - Opening the Loss desk no longer changes the count.
   - Checked live on your pages after the install. Two small display faults of its own go into the next small kit: the word "null" on the drift page, and two dates on the stock-now page.
2. **The extra stock on some items was found (probe S580).** When reception scans a supplier's bill, the whole order counted as "arrived", even items that never came. Examples: TOLTRIS PLUS, 50 strips from Shivaaz (14-10); FLACORT 6, 20 strips from Kedar (13-10); THIO Q AP; LINVIZ 600.
3. **The repair (kit S583) was building when you closed.**
   - Each arrival counts until Marg shows the item.
   - If Marg's purchases still don't show it a few days later, it stops counting and becomes one line for you.
   - Ordering and staff screens are unchanged.
   - Its result is the next chat's first read.
4. **Your morning flow (D737).** You told me Shavez's closing is always taken before any sale, and that Amir's purchase export came before Shavez's reports. I found six such problems (`claude/S324_MORNING_FLOW_FINDINGS.md`):
   - The time fix (a closing's time is when Marg made it) is live in S577.
   - The rest is one kit after this one:
     - Shavez's closing is used whichever date he prints — this needs **one ruling from you**, because it changes a written rule;
     - Amir's export of a visit covers until his next visit;
     - a correct voucher is called right at once;
     - your hub says "Amir marked it done" instead of "wrong";
     - Amir's page gets the export step last — **a mock-up for you first**.

## What needs you

- **The publish of this close** — your double-click, as always:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

- Paste S583's result into a fresh chat in this project (you said you would).
- Later, when the morning-flow kit comes: one ruling and one mock-up to look at.

## The staff's (on their own screens)

- **Amir:** nothing new. His four corrections of 18-Oct are recorded; the stock check judges them on the first closing after them that the rule accepts.
- **Darpan:** the spot count of ANKLE BINDER L BAMBOO is still open.
- **Morning staff:** the two reports, as every day.

## For the next chat

- **First:** S583's result (`REPORT_S583.md`), read live.
- **Then:**
  1. the small kit (F-931, F-932, F-913 … F-916, F-875, F-881, the settings, E);
  2. the morning-flow kit (the mock-up and the ruling first);
  3. S486 A and B;
  4. 4b-2 after the witness week (the parent adds the crontab line).
- **Numbers:** D737; F-925 … F-934; kits S577 (live), S580 (probe), S583 (building); session 327 reserved (326 the parent's, reserved at its S325 close before this one).

*S324 build brief · 18-Oct-2026.*

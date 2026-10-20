# S332 BUILD BRIEF — the Sanjeevni chat · 19-Oct-2026 (13:44 → 20:04 IST)

*The one paper for the next chat (session 333) and for you. Plain words; the detail is in the Archive §S332 and the Book §15Q.*

## What is done

- **Claude now reads the pharmacy bills (S601, live 17:29 IST).** It fills supplier, bill number, date, total and the item lines, handwritten challans too. **Sarvam is switched off** by your switch on the scan-app Admin page (card *"Reading the scans — Sarvam"*); its code is kept. Each bill is now paid for once, not twice. If Claude cannot read a paper, the app tries again by itself three times over two hours.
- **Darpan's order tab has the cut-off line (S602, live 19:56 IST):** *"Marg में खरीद 18-10 के बिल तक चढ़ी है — उसके बाद आया माल इस सूची के स्टॉक में नहीं है"* — the date moves by itself with Amir's purchase export. The tab is not in use while ordering stays on Marg's sheet.
- **The nightly stock check no longer complains** (F-943): it runs read-only from tonight.
- **The bill dates:** you spoke to Amir; he corrects them in Marg. The system takes the corrected date by itself from his next purchase export — nothing to build.

## What we found

- **What a scanned pharmacy bill is used for:** only its top part (supplier, number, total) — to link it to Marg's bill for Amir's page, vendor payments and the packs. Darpan's ordering uses nothing from a scan. The item lines matter only for the day Marg imports a scanned bill by itself (your photo of Marg's import screen decides that).
- **S601's build left its "build in progress" lock on the server** — Claude Code's own permissions refused to remove it; you removed it with one line (F-950). S602 removed its own lock. The next chat writes the right command into Claude Code's rulebook.

## What comes next (your word, 18:09: "Darpan, amir and f 943 now, and remaining build from Sunday")

1. **Amir's calendar-safety kit** — so his page handles no-sale days and the 1st of the month by the bill chain, not the calendar, and his "bill pending" line comes from the scanned bill. **Must be live before 1 November.** The next chat analyses, briefs, and brings you one paste line.
2. **From Sunday 25-Oct:** the buying model (Kit II), then the plan's remaining steps.

## Your one action now

The publish of this record — one double-click on your PC:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

*S332 · 19-Oct-2026 · the Sanjeevni chat.*

# S380_PAY_PACK — the month's bank pack (Sanjeevni, session 281, 23-Sep-2026) · F-616 · D605

**The owner, 23-Sep:** "I just finalized and printed the payment sheets for the month of August. Only the vendor payment sheet came out, remaining five pages were blank. The check letter did not get printed and in the payment details sheet in the lower part, my signature line, name, etc. part is also missing."

## What was wrong (read in the code and in his own 6-page PDF)
1. The pay page's print rule (ADVICE_CSS_S265) hid everything but the annexure with `visibility:hidden` — which paints nothing but keeps the layout, so the page still filled six sheets. Five blank by construction.
2. The covering letter (cheque number, authority to debit) printed only from its own page `/page/pay/<month>/letter`.
3. No signature block anywhere: the bank's own workbook has none (his "NEFT ADVICE AUGUST 2026.xlsx", sent 23-Sep, confirms: rows after the total are empty).
4. `purchase_pay_letter` was empty and `api/pay-letter` refused every write after FINAL — the cheque number could not be typed once August was locked.

## What this kit does
- `/finance/purchase/page/pay/<month>/pack` — three papers, one per sheet: covering letter (portrait) · annexure (landscape) · payment sheet (portrait). `?print=1` opens the print dialog. Buttons on the payment sheet (top card, advice card, letter card).
- Annexure and payment sheet end with **For SANJEEVNI MEDICOS / rule / Authorized Signatory (Checked and authorised on the sheet) / name**; name = `purchase_pay_config.signatory_name`, typed once beside the cheque number.
- The pay page's own print = the annexure alone, one landscape sheet (display:none collapse).
- Letter date, cheque number and signatory name typable after FINAL; audited (`pay_letter`, `pay_signatory`). No figure door opens: `api/pay-line` still refuses with FINAL.
- One renderer for the annexure (`_advice_paper_s380`) — pay page and pack are byte-identical in the annexure.
- The email workbook keeps its exact sheet bytes; its **file name** is the month it is PAID in: August's purchases → `NEFT ADVICE SEPTEMBER 2026.xlsx`. Evidence: his August file carries July's purchases (20 of 21 amounts equal this server's July advice to the rupee; the 21st, Kedar, differs by ₹310).

## Proof (build time, scratch copy of the live database of 23-Sep 04:30)
- walk_s380.py 14/14 GREEN.
- Headless Chromium 141 printed the pack to PDF: **3 pages — portrait, landscape, portrait**, each paper on one sheet, zero script errors; the pay page printed to **1 landscape page**.

## Files
`/root/finance/purchase_app.py` 8788962a (rev 13, S371) → 9ad50878 (rev 14). clinic-finance restarted (declared). No parent file, no table row at install.

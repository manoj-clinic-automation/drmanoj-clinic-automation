# S224_DAY_REVENUE_PDF — the day sheet as a PDF, shared to WhatsApp from the phone

**The owner (04-Sep-2026):** *"give me option to share PDF of Day Revenue from my Android phone
through my WhatsApp."*

## What it is

The S223 Day Revenue screen prints; a phone cannot hand a printed page to WhatsApp. This kit
adds one module, `clinic_day_pdf.py`, that renders the **same day** — the same `clinic_day_revenue`
row, the same `clinic_day_line` rows in the same five sections and order, the same split legs —
into a real A4 PDF file, and a small phone page that hands that file to Android's share sheet.

| route | what |
|---|---|
| `GET /finance/clinic/share` | **the one bookmark.** No date → redirects to *yesterday's* share page. `?d=yyyy-mm-dd` → that day's. |
| `GET /finance/clinic/day/<yyyy-mm-dd>/share` | the phone page: the day's total and heads, **Share PDF on WhatsApp**, **Download PDF**, a date picker. |
| `GET /finance/clinic/day/<yyyy-mm-dd>/pdf` | the PDF, inline. `?dl=1` → `Content-Disposition: attachment`. Filename `Docterz_Revenue_<date>.pdf`. |
| `GET /finance/clinic/day/<yyyy-mm-dd>.pdf` | the same file by its filename (proven not to collide with S223's `/day/<date>`). |

The owner bookmarks: **`https://followup.dr-manoj.in/finance/clinic/share`**

**Who.** `require("checker", unit="clinic")` — the doctors. A maker sees the A4 page as before; the
file that leaves the building through a phone is the checker's to send. A maker or a viewer gets
403, in words on the share page, as JSON on the PDF, and no figure in either refusal.

**The A4 page is not touched.** `finance_clinic_day.py`'s live pin is DECLARED-PENDING (never read
back), so nothing pending is patched. The three SELECTs are copied verbatim from that file as
built at S223_DAY_PAGE_EDITS (`dceb79a06e71f7e35150c69e1f5dd175`): the day row (line 166), the
lines (line 174), the split legs (line 200); sections, shift order and the people count are the
same code (lines 52–63, 246). D367 stands: the sheet's own summary figures are read from nowhere.

## How the WhatsApp share works on Android

The share page fetches the PDF once (with the session cookie) the moment it opens, so the button
is instant. Tapping **Share PDF on WhatsApp** wraps the bytes in a `File` and calls the **Web Share
API**: `navigator.canShare({files:[f]})` then `navigator.share({files:[f], title, text})`. Chrome
on Android opens the system share sheet with the PDF attached; WhatsApp is one tap, then the
contact or group. Nothing is sent by the server; nothing leaves except through the owner's own
WhatsApp, by his own tap.

If the browser cannot share files (an old Chrome, or a desktop), the page says so and shows two
routes that always work: **Download PDF** (then the paper-clip in WhatsApp), and a `wa.me` link
carrying a one-line summary of the numbers — no name, no ID, no number of anyone's.

## The PDF writer

Gunicorn runs the finance app under `/usr/bin/python3`, which has no reportlab and no weasyprint,
so the writer is in the module: about a hundred lines, PDF 1.4, Helvetica / Helvetica-Bold core
fonts with real AFM widths for alignment and trimming, rules, shaded header rows, page breaks with
the table header repeated, *Page n of N*, uncompressed streams (searchable, testable). The core
fonts have no rupee glyph, so amounts read **Rs 1,23,456** in Indian grouping. `qpdf --check` clean;
`pypdf` reads it; rendered to PNG and looked at.

## Proven

* `EVIDENCE_selftest_s224.txt` — **63/63 GREEN.** The real blueprint on a real Flask app over a temp
  db seeded with an invented day (every name and ID synthetic — the S223 kits seeded from real
  workbooks the repository cannot hold, F-185): `%PDF-1.4`, page count, exact xref offsets, the date
  and the total as text, all five sections in order, every line, the tender line, the split legs,
  D367 (the differing sheet total is nowhere), no rupee sign, **no 10-digit run in the text**, no UID
  shape; `?dl=1`; the `.pdf` alias; maker and viewer 403 with no figure; bad/missing dates 404 not 500;
  the share page (buttons, `navigator.share` with files, `canShare` first, same-origin fetch, `wa.me`
  fallback with the numbers, picker, no patient name on it); the bookmark redirects; a day with totals
  but no lines; no table at all; Indian grouping edges; 139 lines paginating onto 3 pages.
* `EVIDENCE_walk_gate_s224.txt` — **19/19.** The REAL patched `finance_app.py`, its REAL front gate,
  the REAL S223 day page mounted beside it, on a COPY of the db: signed-out 302, no-role refused,
  maker 403, checker gets the PDF with the invented lines, `.pdf` reaches this module and `/day/<date>`
  still reaches S223's page, healthz and the purchase healthz still answer. The patcher refused the
  wrong pin, applied on the right one, and said ALREADY PATCHED the second time.

## Files

`clinic_day_pdf.py` (the module) · `patch_finance_app_daypdf_s224.py` (one anchor, FROM-pin as
argument, backup, compile-or-restore, idempotent) · `walk_daypdf_gate_s224.py` ·
`selftest_clinic_day_pdf.py` · the two EVIDENCE files · `INSTALL.txt` (one paste, self-rollback) ·
`PREDICTED_PINS.txt` · `KIT_ID.txt` · `SUMS.md5`.

## Named, not glossed

* **The phone must be signed in to the portal in the same browser** (the PDF is fetched with the
  session cookie). The F-242 trusted-device loop, if it bites, bites here too.
* The PDF carries patient names and clinic IDs, exactly as the A4 page does (the owner's own ruling:
  clinic ID + NAME, no mobile). Once shared it is in WhatsApp; that is the point, and his choice.
* `/finance/clinic/share` uses the server's *yesterday*. A day whose sheet has not reached Drive shows
  "No day was read" with a link to the newest day stored — nothing is hidden.

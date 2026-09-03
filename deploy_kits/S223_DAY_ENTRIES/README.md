# S223_DAY_ENTRIES — the per-patient table, every section, composed for A4

**The owner, the same night the month view went live:** *"per patient entry table, daily, section
wise for consult, xray and proc, with amt name and clinic id, this is print format also"* ·
*"include free etc all patients"* · *"all composed for A4 sheet"*.

## What changes

Every date on the month view becomes a link. It opens **that day's own page**: every entry on the
day's Docterz sheet, section by section — **PAID CONSULTATIONS · X-RAY · PROCEDURES · FREE
REVISITS · FREE / CONCESSION CASES** — each with the patient, the clinic ID, the amount, the mode
and the shift, and a subtotal. Sections with no entries that day are not shown at all rather than
printed empty.

The header says **how many PEOPLE were seen**, not only how many entries: a person billed for both
a consultation and an X-ray is two entries and one person, and the page says so in those words so
nobody has to work it out.

**Composed for A4.** `@page size:A4 portrait`, 12mm/10mm margins, 10.5pt body, black on white,
hairline rules. Table headers **repeat on every printed page**, no row is ever split across a page
break, and the navigation disappears. Ctrl-P, or the button, then Save as PDF.

## Identity, and why it is allowed here

The reader originally stored no patient name and no clinic ID at all. This kit adds them, because
that is the owner's own recorded ruling for this screen: **clinic ID + NAME on the view, no
mobile** (`DOCTERZ_REVENUE_PHASE1_WORKING_PAPER`, owner rulings #2).

**There is no mobile number in the Day Revenue sheet** and none is derived. The names live in
`finance.db` on the box, behind the same clinic-role gate as the month view and the same SSO as
every other screen that already names a patient. **F-185 still governs the repository absolutely:**
no identity in a kit file, a test fixture or an evidence file — and the evidence file in this kit
was scanned for mobile-shaped and UID-shaped strings before it was committed. Both zero.

## Proven — 39/39 GREEN

`EVIDENCE_entries_s223.txt`. The real blueprint on a real Flask app, a real database filled by the
real ingester, pages fetched over HTTP, assertions on the delivered bytes. Among them:

- every stored line appears on its day's page, matched by clinic ID
- **the billed lines sum to the day's stored total** — the detail and the summary cannot drift
- each section's subtotal is on the page; a section with no entries is absent, not empty
- the free revisits and concession cases are listed too
- a non-clinic login is refused **with no patient name anywhere in the refusal**
- a date with no day says so and offers the way back; a malformed date is refused, not crashed on
- `@page size:A4 portrait` is declared, headers repeat, rows do not split
- still **no `<script>` tag at all**, and no mobile-shaped number on any page

## Still not solved, and named rather than glossed

**A `Split Payment` line has no breakup on this page, because the Day Revenue sheet does not carry
one.** The sheet records a line's Mode; the legs (`1100 (Wallet: 600, Online Payment: 500)`) exist
only in the raw Docterz export. Those exports ARE retained — **80 of them, in the tracker's own
`uploads/` folder** — and the tracker's `outputs/` folder is the very folder that syncs to Drive.
So the route is clear and needs no new transport: a PC-side pass over the retained exports, with
the seven-token parser already proven offline, writing a tender file into `outputs/`. That is the
next kit, not this one.

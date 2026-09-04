# S225_LOANS_VIEW — the Loans view (D371)

**The owner's words (04-Sep-2026):** *"staff advance ledger has all entries and it's confusing, so the data should clearly
display actual loans — tranches with details and instalments due — and the ledger should be clear of the extra entries,
as we don't cancel any; then only we can plan which view to share with staff on their PWA."*

**What this kit adds to `staff_ledger.py` (v3.4 → v3.5, full-file replacement, the close untouched):**

- **`/ledger/loans`** — one table per person. For every advance actually issued (a *tranche*): taken · amount · kind
  (advance / interest loan / SPECIAL) · **how it recovers** (from `advance_lane`, the one D349 rule: agreed schedule,
  against-salary, loan, or waterfall) · recovered · balance · **next collection** (month and rupees, months left) ·
  status (open / recovered by …; deferred months named). Per person: **outstanding** and **falling due this month**
  (the per-lane instalments, before the close's salary-capacity check — the page says so). Pending advances are
  counted, not listed as loans. A reversed advance (a correction — we never cancel, we contra) is counted out, not shown.
  System rows, interest lines and contras never appear as lines; they are inside the figures.
  The doctor sees everyone, or one person, for any month. A staff login linked to a name sees **My loans** — own only.
  *This is the view from which the staff-facing PWA view is planned, as he asked.*
- **The agreed-schedule box on the New-entry form** — `make_entry` has accepted a repayment schedule since D332 §4, but
  the form never sent one, so a scheduled advance could only be created by the migration tool. Now: one step per line,
  `2026-09:5000`, refused unless the steps add up to the advance exactly. This is how Surendra's ₹13,000 August advance
  is entered with its instalment plan.
- Nav: **Loans** / **My loans**.

**Proof:** the module's own selftest is unchanged at **301/301**; `selftest_loans_view_s225.py` — **35/35** — builds a
synthetic ledger (an interest loan with a recovered instalment, a waiting interest-free advance, a Surendra-shaped
₹13,000 schedule, a reversed pair, a pending maker advance, a defer, a fully recovered tranche) and reads the page
through the real app as checker, linked maker and unlinked maker; the form round-trip saves a schedule and refuses one
that does not add up. The install script re-runs both on the box in isolation and walks the live route before GREEN.

**Not in this kit:** entering the August advances (Surendra ₹13,000 with plan; Darpan ₹15,000) — those are the doctor's
entries on the New-entry page, the ledger's own maker-checker path · Parvesh's exit (the register's last-working date; the
ledger has no final-settlement concept — recorded as owed design) · the staff PWA view (after he has seen this one).

**Rev 3 — D374 (owner, 04-Sep 15:05):** *"make it optional for me, I can add it later."* A SPECIAL advance can now be approved on Pending before its signed application is uploaded; it carries **application owed** on Advances and Loans (with an attach link) until the PDF is attached, which clears the mark. D331's evidence rule stands; its timing moved.

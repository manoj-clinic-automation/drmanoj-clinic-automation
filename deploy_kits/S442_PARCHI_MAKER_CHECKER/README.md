# S442_PARCHI_MAKER_CHECKER — discount and free with a checker, radd after billing, the late parchi

**Session 287 (parent), 01-Oct-2026 · D644 · F-663 · F-664 · F-668 · plan `S286_NEXT_BUILD_PLAN.md` §B.**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S442_PARCHI_MAKER_CHECKER/install_S442_PARCHI_MAKER_CHECKER.sh

- **Chhoot / Free** on any X-ray or procedure line (at logging, in the picker, or later from *Aaj ki list*), with a reason pick.
  The line carries it at once; it waits for **Shavez, the owner or Dr Bhawna** (`slips.approvers`); nobody approves their own;
  a reject needs a reason and goes to the night report. Shavez sees *Chhoot / Radd manzoori* in his menu; the doctors see it at
  the top of the report.
- **Night check** (the slip report): Docterz below the rate with no chhoot written → *discount not written*, naming who logged
  the parchi; it also comes back to that person's tile the next day.
- **Radd after billing**: clinic ID + *paise lauta diye / liye hi nahi*; approved → the parchi reads cancelled, the Docterz line
  leaves the expected money in `clinic_money` (explained, not flagged) and shows under *Cancelled after billing*. A parchi already
  radd with no ID (29-Sep, ₹600) shows on *Chhooti parchi* and takes its ID there — never guessed.
- **Late parchi**: the form proposes the day (the ID in the last Docterz day without a parchi there; a number below today's first);
  one tap accepts.
- **Owner's page**: `/finance/slips/discounts` (and one line on `/finance/clinic/money`).
- **Data**: OPD 19493–19509 → 28-Sep, audited, only if exactly those 17 are still on 29-Sep.

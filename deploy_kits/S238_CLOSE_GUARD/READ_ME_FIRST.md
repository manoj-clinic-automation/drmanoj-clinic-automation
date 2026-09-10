# S238_CLOSE_GUARD — the monthly close is yours, and only after the month is over

**staff_ledger.py v3.6 → v3.7 · built 10-Sep-2026 (S238) on the owner's ruling D447:**
*"the close should be after the calendar month is over and only when I manually do it, because
corrections have to be done in the attendance and other things also."*

## WHAT WAS HAPPENING

Nothing on the server has ever closed a month by itself. The Salary page's **step 5** carried a
**"Run monthly close"** button that was live on **any day of the month**, including the month still
running. August's close was one press of it, at 00:19 on 20 August, eleven days before the month ended.
A close can never be repeated, so everything entered after it fell into the next month.

## WHAT CHANGES

1. **The close button appears only from the 1st of the following month.** Until then step 5 says
   when it opens. The page, the route behind it, and the command line all refuse an earlier close.
   It still never runs by itself.
2. **The close refuses while an entry for that month is still PENDING.** It names the entries. Tick
   *"close anyway"* only if you want them in the next month. August's ₹20,000 was pending at its close,
   which is why August collected nothing on it.
3. **After the close, it tells you what it did not collect, by name.** Held because the salary couldn't
   bear it, waiting behind the loan, a schedule left behind, entries left pending. This shows on the
   Salary page and is saved beside the ledger.
4. **Duplicate warning.** The same person, category, date and amount as an entry already in the
   ledger is refused, with a one-click *"Yes — save it as a separate entry"* for a genuine second one.
5. **A SPECIAL advance needs a narration.**

**The close's arithmetic (`close_month`) is not changed by one line.**

## INSTALL — after the publish, one line on the VPS

```
bash /root/deploy/vps_deploy.sh S238_CLOSE_GUARD
```

It refuses unless the running file is the pinned v3.6. It runs the new file's selftest (323) and a probe
against a **copy** of the real ledger that renders every page you use, all before it replaces anything.
It backs up, installs, restarts, and checks that the live service reports v3.7. On any failure it puts
the old file back.

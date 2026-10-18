# S318 — Scan App: what changed, and what comes next (15 → 18-Oct-2026)

*For Dr Manoj. Short; the detail is in the canon.*

## Live now

<details open><summary><b>1 · Batteries</b> (live 16-Oct 14:19; your rulings and mock-up)</summary>

- **One Batteries page** with your 15 places in four groups:
  - Online UPS: digital X-ray, NK Pathology, DTH lab;
  - Small UPS;
  - Generator and inverters;
  - Vehicles: Carnival, Wagon R, Vento, Scooty, Bike.
- **New battery fitted:**
  - a B.L. battery shows *bill awaited* until its bill is linked;
  - a Jasoria battery takes the price, the old-battery amount and the warranty from the card.
- **The bill link:** when a B.L. or Jasoria bill reaches the sorting desk, it asks *"this bill?"*. One tap links it; the paper itself is never moved.
- **Reminders** (warranty ending, battery due, water top-up, UPS check) sit as one *Batteries* card on Renewals.
- **Who sees what:** reception is untouched. Home and vehicles are yours only. Shavez sees nothing until you switch him on.
</details>

<details><summary><b>2 · Stationery & packaging</b> (live 16-Oct 12:15)</summary>

- **An item list** of general stationery with rates. You can add items to it any time.
- **Stock** comes in from the bills and challans on the desk (once, never twice). Issues are entered on the staff screen *Stationery diya* (Kya diya / Kitne / Kisko). That screen is built to your mock-up and is **off** until you switch it on.
- **Aumni Crafts invoices:** *Add a paper from a file* on the desk files them as a Sanjeevni pharmacy expense, paid by your card.
- **Only bills and invoices now go to the accountants.** Estimates and paid-on-challan papers stay internal.
</details>

<details><summary><b>3 · Tidy-ups</b> (15–16 Oct)</summary>

- A paper set aside by mistake can be restored on the desk.
- Every waiting paper now reaches the desk; B-0009 (construction, waiting since 11-Sep) was not.
- The counts that disagreed now agree: *Bills awaited* and the home page's month total.
- A half-read date is never stored, and *None* is never shown as a contract.
</details>

## Next — waiting for your one line

**Battery first setup**, as you asked this morning:
- an **old battery with only a date** is recorded as *"Old battery — no bill"*, so no false *bill awaited* reminder;
- **older bills** can be found and linked (*Show older papers*, or *Find by stamp*);
- each online UPS asks **how many batteries** it has;
- a **First setup** list lets you do all the places in one sitting.

The brief is checked and ready. Run it when the Sanjeevni build has finished:

```
python D:\Downloads\_kbtools\agent_build\run_build.py S575_BATTERY_SETUP
```

## Yours

- **The publish of this close (papers only):**

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

- **When you want Shavez on them,** switch these on in the *Switches* card of the scan app's home page: *Sorting desk*, *Machine pages* and *Batteries* for Shavez, and *Stationery diya* for the managers.

```
https://followup.dr-manoj.in/scanapp/
```

- **Your API credit:** USD 185.48 left, valid to 18-Nov. It pays for both the builds and Claude's reading of the scans.
- **Later, your word (no hurry):** the stop-gap fix to your renewal email.

# S323 — Scan App: what changed, and what comes next (18 → 22-Oct-2026)

*For Dr Manoj. Short; the detail is in the canon.*

## Live now

<details open><summary><b>1 · Batteries — first setup</b> (live 18-Oct morning)</summary>

- An **old battery with only a date** is recorded as *"Old battery — no bill"* — no false *bill awaited*.
- **Older bills** can be found and linked (*Show older papers*, or *Find by stamp*).
- Each online UPS asks **how many batteries** it has.
- The **First setup** list let you do all the places in one sitting. You fitted 14 of 16; the Vento and the DTH lab are still open.
- Added: *X-ray detector (FDR) battery*. Renamed: *Medical PC*, *Lab PC*.
</details>

<details><summary><b>2 · X-ray costs</b> (live 18-Oct afternoon; your ruling of 13:03)</summary>

- A new page, only for you, right after Batteries in the menu.
- Month by month it adds: the X-ray films, the papers you mark for X-ray, the service and AMC of the machines you tick, and the batteries of the X-ray places. **Each rupee is counted once.**
- A paper stays in its own group; marking it for X-ray only adds it here.

```
https://followup.dr-manoj.in/scanapp/xray
```
</details>

<details><summary><b>3 · Stationery</b> (live 18-Oct evening; your rulings of 14:41–15:10)</summary>

- **Your opening count** of 18-Oct is the starting stock (nine items).
- **Many items on one screen** for staff, as in your mock-up. It is **off** until you switch it on.
- **X-ray** is now a place on *Kisko diya*.
- You can **Void** a wrong issue; the line stays, struck through.
- **Shavez's sheet** is in as past issues, in its own fold.
</details>

<details><summary><b>4 · Entered at your word</b> (19–22 Oct)</summary>

- The FDR AMC on the X-ray detector, with its paper (B-0203, July) and the FDR battery's tax invoice (B-0204, August).
- The email to Shail / Fujifilm asking for the AMC's tax invoice went from your Gmail.
</details>

## Next — waiting for your one line

**The Variety challans as past stock-in**, as you asked this morning: the six challans entered on their own dates, before your opening count, with your item rulings. The brief is checked and ready. Run it in the next fresh chat of this project:

```
python D:\Downloads\_kbtools\agent_build\run_build.py S623_STATIONERY_CHALLAN_HISTORY
```

## Yours

- **The publish of this close (papers only):**

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

- **When you are happy with it:** switch on *Many items on one screen* — the card at the top of your Stationery page:

```
https://followup.dr-manoj.in/scanapp/stationery
```

- **When you have them:** the Vento's and the DTH lab's battery dates, under *First setup*:

```
https://followup.dr-manoj.in/scanapp/batteries
```

- **When it comes:** scan Fujifilm's tax invoice for the AMC.

## Seen, for the next round (I will build these when you say)

- Editing a machine resets its purchase day to the 1st.
- A battery past its warranty still shows OK.
- A machine's AMC cannot be linked to its paper after it is added.
- The stationery match did not look at the pack size (the token line — fixed in the data by the next build).
- A back-dated bill counts in the month it was scanned until its month is set by hand.

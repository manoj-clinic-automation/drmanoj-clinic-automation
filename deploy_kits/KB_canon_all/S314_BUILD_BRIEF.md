# S314 — Scan App: what changed, and what comes next (13 → 14-Oct-2026)

*For Dr Manoj. Short; the detail is in the canon.*

## Live now

<details open><summary><b>1 · Reception only captures</b> (live 13-Oct; switched on by you)</summary>

- Reception sees four big buttons: **Clinic · Pharmacy · NK Pathology · Other document**, and the **Challan** button.
- **Personal expense** is for you and Shavez only. Each paper asks **Dr MK / Dr Bhawna**; with no choice it counts as Dr MK.
- *Medical Equipment* is now **Dr MK Clinic Equipment**, and every machine in it moved.
- A paper in your **Personal** section no longer opens for a manager anywhere.
</details>

<details><summary><b>2 · The scanner finds the paper</b> (live 13-Oct)</summary>

- On a busy table, a light table or with the page filling the frame, the phone now crops to the paper.
- It turns a sideways page upright.
- Reception's real scans since then are checked once more today.
</details>

<details><summary><b>3 · Dr Bhawna's own file in the accountants' pack</b> (live 13-Oct; your D721)</summary>

- Her personal expenses are item **8.3**; yours stay in 8.2.
</details>

<details><summary><b>4 · Claude reads every scan</b> (live 14-Oct 05:10; your API credit)</summary>

- **What it reads:** every new scan is read by Claude first (printed, handwritten estimate slips, challans). It fills only what is empty; Sarvam reads when Claude can't.
- **The older papers:** they are being read once in the background.
- **What it never does:** it never keeps a person's name, never writes on pharmacy papers, and never sends resumes or your Personal papers.
- **When it stops:** by itself if the key or the credit stops, and Sarvam carries on.
- **Your switch** is on the admin page, which also shows today's count and the older papers' progress:

```
https://followup.dr-manoj.in/scanapp/admin
```
</details>

## Next

<details open><summary><b>The sorting desk — your final mock-up is the plan</b></summary>

- **How it gets built:** through the parent project's SDK path on your API credits (to 17-Oct). This project writes the work order and checks the result before you publish.
- **What it is:** one laptop page, side by side — the waiting papers, the scan large, what was read (editable), the paper's kind, where it goes, Save & next.
- **Where a paper goes:**
  - Clinic consumables (Procedure room · X-ray small · X-ray 11 × 14 · Others);
  - Implant stock, Clinic equipment, Construction work;
  - Personal expense (Dr MK / Dr Bhawna), Personal;
  - Pharmacy, NK Pathology;
  - Resumes, Miscellaneous;
  - *A patient's paper* (set aside for the surgical case pack).
- **Challans by supplier:** Gaurav Traders monthly, Variety Stationers now and then, Elegans paid on the challan.
- **Pages beside the desk:** an implant stock ledger per supplier, and one month page by section.
- **The switches** move onto the scan app's own pages.
</details>

<details><summary><b>After the desk</b></summary>

- The machine pages: parts, warranty/AMC history, repairs, each with its bill.
- Then your family's documents and renewals in their own Google project.
</details>

## Yours

- **The publish of this close (papers only):**

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

- **Later, your word (no hurry):** the stop-gap fix to your renewal email.

# S681_IPD_PAPERS_BILL — IPD cases, kits 2 + 3: papers, implants, assistants · the hospital bill and the share

The parent · session S370 · 30-Oct-2026 · D804 · the owner 13:47 IST ("do kits 2 and 3 first") and 13:52 IST ("keep both methods of
computation"). Built on S680_IPD_CASES_RECORD (live since 13:33 IST, surgery_cases.py ed91e2af). One file changes.

**What Dr Manoj and Shavez will see on an opened case** (the screens were rendered with made-up patients first, read by a reviewer twice)
1. **Section 2 — surgery, implant, assistants.** Each implant has its own payment step (not raised · bill raised · cheque received ·
   paid to the vendor · vendor confirmed); the case's implant payment follows the least advanced one (and the list's filter with it).
   A step set for the whole case moves its implants with it. **Assistants:** the technician and the assisting doctor are written on
   the case (Shavez may write the names); what they were paid is optional and seen and written only by Dr Manoj.
2. **Section 3 — papers as thumbnails.** A photo shows small, a PDF as a PDF tile; each opens large; **Delete** asks a tapped reason
   (wrong patient · wrong paper · unclear / blurred · scanned twice) and the paper is kept in the record with it. Missing papers show
   as dashed tiles that open the scanner. **New kinds:** police FIR copy, the previous hospital's papers, LAMA, DOPR.
3. **Section 4 — the hospital bill**, typed field by field (blank = not on the bill): bill no. and date; the four heads **as the
   hospital's statement prints them** (Prof. visit, Misc, Bed charges, Surgery); then the fields of **your formula** for the payer —
   cash (bill total, discount, admission and nursing prefilled, other doctors, X-ray / pathology, misc), package (package, admission,
   medicines, anaesthesia, implant prefilled, investigations, assistants — yours only) or credit (billed, sanctioned, received,
   anaesthesia, medicines, pathology, X-ray, CT, MRI, other doctors; the implant paid comes from the implants).
4. **Section 5 — your share, both ways, side by side:** the hospital's way (the four heads × the statement's %, 50 as on September's
   statement — Settings) and your formula (× your %; not worked until you set it); the difference said; *Use ₹… as the amount due*
   (yours only). On a credit case your formula's line uses the implant's actual cost, so only you see it.
5. **Settings** gains *The hospital statement's doctor's share (%)* (50).

How the hospital fills the credit cases' heads is to be explained by the hospital (the owner, 13:51); the form takes them as printed.
Kit 4 (the implant bills desk and the vendors' ledger — the old cases' implants included) goes to a fresh chat on Claude Fable; kit 5
(the monthly statement) is designed on the September statement's shape; kit 6 (after discharge) after.

**Data** — additive only: column `surg_implant.pay_status`, tables `surg_assistant`, `surg_bill` (one live row per case; a new save
keeps the old row voided "replaced"), setting `ipd.hospital_share_pct`. No phone number in any address, as S680.

## Install (on the server, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s681kit && cp -rp /root/deploy/repo/deploy_kits/S681_IPD_PAPERS_BILL /tmp/s681kit && bash /tmp/s681kit/install_S681_IPD_PAPERS_BILL.sh
```
Gates → the pin (surgery_cases.py ed91e2af, S680) → compile on both pythons → **the walk** (S680's 205 carried — one rewritten, the
paper kinds 10 → 14 — and section K for kits 2 + 3) on a made-up database and on a copy of the live one, and its control on the live
module → **the probe** through the real finance app as manoj, shavez, bhawna, darpan (S680's 15 + the bill and an assistant through
the real app), and its control → health → the backup and the database copy → place and read back → restart clinic-finance → health
→ the probe on the placed file. A red after placing puts the file back. A second run says ALREADY INSTALLED.

## Undo
```
cp -p /root/finance/surgery_cases.py.bak_S681_ed91e2af /root/finance/surgery_cases.py && systemctl restart clinic-finance
```
(The added column and tables are harmless to the S680 file.)

"""
CC STATEMENT PROCESSOR - decrypt + Tally-ready transaction extraction
Dr. Manoj Agarwal | 23-Jul-2026

WHAT IT DOES
1. Walks your synced "Credit Card Statements" folder (per-card subfolders
   created by the Gmail script).
2. Removes PDF password protection -> saves open copies to Decrypted/
   (mirrored per-card structure; originals untouched).
3. Extracts every transaction row -> one consolidated Excel workbook
   (sheet per card) + a single tally_entries.csv with columns:
   Date | Card | Narration | Amount | Dr/Cr | Suggested Ledger
   The accountant can key Tally entries straight off this file.

SETUP (once)
  pip install pikepdf pdfplumber pandas openpyxl
  Fill CARD_PASSWORDS below (bank PDF passwords - typically a
  name+DOB combination as per each bank's statement email footer).

RUN
  python process_statements.py
  Point INPUT_DIR at the Google Drive for Desktop path of the
  "Credit Card Statements" folder (or a downloaded copy).
"""

from pathlib import Path
import csv
import re

import pikepdf
import pdfplumber
import pandas as pd

# ====================== CONFIG ======================
INPUT_DIR  = Path(r"G:/My Drive/Credit Card Statements")   # adjust
OUTPUT_DIR = INPUT_DIR / "Decrypted"
EXCEL_OUT  = INPUT_DIR / "All_Transactions.xlsx"
TALLY_OUT  = INPUT_DIR / "tally_entries.csv"

# Folder name -> PDF password (fill these yourself; never share this file)
CARD_PASSWORDS = {
    "HDFC Business Regalia": "FILL_ME",
    "ICICI Amazon Pay":      "FILL_ME",
    "ICICI Card 5007":       "FILL_ME",
}

# Keyword -> Tally ledger suggestion (edit freely; first match wins)
LEDGER_MAP = [
    (r"amazon|flipkart|myntra",        "Online Purchases"),
    (r"swiggy|zomato|restaurant|hotel","Food & Entertainment"),
    (r"petrol|fuel|hpcl|bpcl|ioc",     "Fuel & Conveyance"),
    (r"pharma|medic|chemist|apollo",   "Medical Expenses"),
    (r"hostinger|godaddy|razorpay|anthropic|openai|google|microsoft|myoperator",
                                        "Software & Subscriptions"),
    (r"airtel|jio|vodafone|bsnl",      "Telephone & Internet"),
    (r"insurance|premium",             "Insurance"),
    (r"payment received|neft|upi|autopay|ach|credit received",
                                        "Card Payment (Contra)"),
    (r"fee|charge|gst|tax|interest",   "Bank Charges & Interest"),
]
DEFAULT_LEDGER = "Sundry Expenses (Review)"

# Transaction line: date  narration  amount [Cr]
TXN_RE = re.compile(
    r"^(\d{2}[/-]\d{2}[/-]\d{2,4})\s+(.*?)\s+([\d,]+\.\d{2})\s*(Cr|CR)?\s*$"
)
# ====================================================


def decrypt_all():
    OUTPUT_DIR.mkdir(exist_ok=True)
    done, failed = 0, []
    for card, pwd in CARD_PASSWORDS.items():
        src = INPUT_DIR / card
        if not src.is_dir():
            continue
        dst = OUTPUT_DIR / card
        dst.mkdir(exist_ok=True)
        for pdf in sorted(src.glob("*.pdf")):
            out = dst / pdf.name
            if out.exists():
                continue
            try:
                with pikepdf.open(pdf, password=pwd) as doc:
                    doc.save(out)
                done += 1
            except pikepdf.PasswordError:
                failed.append(f"{card}/{pdf.name}  (wrong password)")
            except Exception as e:
                failed.append(f"{card}/{pdf.name}  ({e})")
    print(f"Decrypted {done} new file(s).")
    for f in failed:
        print("  FAILED:", f)


def suggest_ledger(narration: str) -> str:
    low = narration.lower()
    for pattern, ledger in LEDGER_MAP:
        if re.search(pattern, low):
            return ledger
    return DEFAULT_LEDGER


def extract_all():
    rows = []
    for card_dir in sorted(OUTPUT_DIR.iterdir()):
        if not card_dir.is_dir():
            continue
        for pdf in sorted(card_dir.glob("*.pdf")):
            try:
                with pdfplumber.open(pdf) as doc:
                    text = "\n".join(
                        (p.extract_text() or "") for p in doc.pages)
            except Exception as e:
                print("  READ FAILED:", pdf.name, e)
                continue
            for line in text.splitlines():
                m = TXN_RE.match(line.strip())
                if not m:
                    continue
                date, narr, amount, cr = m.groups()
                narr = re.sub(r"\s{2,}", " ", narr).strip()
                if len(narr) < 3:
                    continue
                rows.append({
                    "Date": date,
                    "Card": card_dir.name,
                    "Narration": narr,
                    "Amount": float(amount.replace(",", "")),
                    "Dr/Cr": "Cr" if cr else "Dr",
                    "Suggested Ledger": suggest_ledger(narr),
                    "Source PDF": pdf.name,
                })
    if not rows:
        print("No transactions parsed - send me one decrypted PDF layout "
              "and I will tune TXN_RE for that bank's format.")
        return

    df = pd.DataFrame(rows)
    with pd.ExcelWriter(EXCEL_OUT, engine="openpyxl") as xl:
        for card, part in df.groupby("Card"):
            part.drop(columns=["Card"]).to_excel(
                xl, sheet_name=card[:31], index=False)
        df.to_excel(xl, sheet_name="ALL", index=False)

    df.to_csv(TALLY_OUT, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Extracted {len(df)} transactions "
          f"-> {EXCEL_OUT.name} and {TALLY_OUT.name}")


if __name__ == "__main__":
    decrypt_all()
    extract_all()
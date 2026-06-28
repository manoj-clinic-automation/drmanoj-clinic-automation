"""
revenue_ingest.py — Periodic external-revenue ingest for the Follow-Up Tracker.
Dr. Manoj Agarwal Clinic, Bareilly

WHAT THIS ADDS (sits beside revenue.py; reuses its ledger + helpers)
  The clinic's pharmacy (Marg / Sanjeevni) and pathology (Labmate / NK Pathology)
  bills are NOT in Docterz. This module ingests those external files, attributes
  each bill to the right patient, and folds the result into the SAME
  revenue_ledger.csv that /finance already reads.

OWNER POLICY (locked 28 Jun 2026)
  • Only CONFIDENTLY-MATCHED bills are written to the live ledger (so /finance
    counts them immediately).
  • REVIEW (ambiguous) + UNCLASSIFIED (no patient) bills are HELD in a separate
    file — revenue_pending_review.csv — and are NOT counted by /finance until the
    doctor manually checks them and PROMOTES them. No doubtful rupee lands on a
    patient automatically; no rupee is lost either (held money is visible + promotable).
  • Preview first, then confirm: the web route shows the buckets + ₹ before
    anything is written.

WHY A SEPARATE HOLDING FILE (not tagged rows in the ledger)
  revenue.finance_summary / totals_for_period count EVERY row in the ledger,
  regardless of Source or tag. So a "held" row left in the ledger would be counted
  at once — violating the policy. Keeping held bills out of the ledger entirely is
  the only way to keep them invisible to /finance until promoted.

MATCHING LADDER (per bill, first hit wins) — same as the proven reconciler
  1. Clinic ID exact  2. mobile exact  3. name + visit within ±WINDOW days
  4. name unambiguous in master  → MATCHED
  5. 2+ candidates → REVIEW (held)   6. no candidate → UNCLASSIFIED (held)

DE-DUP: re-uploading the same file is safe. Matched rows de-dupe against the
ledger on (Source, Date, Invoice_No, Net, Origin-file). Held rows de-dupe on the
same key within the holding file.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd

# Reuse the tracker's own helpers + ledger so behaviour is identical.
from processor import (
    DATA_DIR, clean_mobile, parse_date, date_to_str, load_master, load_visits,
)
import revenue


# ── config ────────────────────────────────────────────────────────────────────
DATE_WINDOW_DAYS = 3                       # bill-date ↔ visit-date tolerance
PENDING_FILE = DATA_DIR / "revenue_pending_review.csv"
META_FILE    = DATA_DIR / "revenue_source_meta.json"
STALE_DAYS   = 45                          # banner turns amber past this

SOURCE_LAB          = "Lab"
SOURCE_PHARMACY     = "Pharmacy"
SOURCE_UNCLASSIFIED = "Unclassified"

HONORIFICS = {
    "mr", "mrs", "ms", "miss", "master", "mast", "smt", "sh", "shri", "sri",
    "km", "kumari", "dr", "baby", "bo", "wo", "so", "do", "co",
}

# Held-file columns: the full ledger row (so a promote is a straight copy) PLUS
# the candidate info needed to resolve it.
PENDING_COLS = revenue.REVENUE_COLS + [
    "Match_Status", "Match_By", "Candidate_Count", "Source_File",
    "Bill_Name", "Bill_Mobile", "Bill_Clinic_Id",
    "Cand_UIDs", "Cand_Clinic_Ids", "Cand_Names",   # ; -joined candidate lists
]


# ── name normalisation (honorific-stripped token set) ─────────────────────────
def _nameset(raw) -> frozenset:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return frozenset()
    s = re.sub(r"[^a-z\s]", " ", str(raw).lower())
    return frozenset(t for t in s.split() if t and t not in HONORIFICS and len(t) > 1)


def _num(x) -> float:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 0.0
    s = str(x).replace(",", "").strip()
    if s in ("", "nan", "None", "#VALUE!", "-"):
        return 0.0
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _bill_date(val):
    """Parse a date from the formats in these files (incl. 'DD-MM-YYYY hh:mm AM/PM')."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%d-%m-%Y %I:%M %p", "%d/%m/%Y %I:%M %p"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return parse_date(s)


# ── visit-date spine (master visits + any consultation reports present) ───────
def _build_visit_spine() -> pd.DataFrame:
    """Per-visit table to match bill dates against: Patient_UID, Clinic_Specific_Id,
    Patient_Name, Mobile_Clean, Visit_Date(date), _nameset.

    Sources, unioned + de-duped on (UID, date):
      • the tracker's own visit_ledger (load_visits)
      • every uploads/consultation_report_*.csv present (extends coverage to the
        whole exported history — that's where April/May visit dates live)
    """
    frames = []

    vis = load_visits()
    if vis is not None and len(vis):
        a = pd.DataFrame({
            "Patient_UID":        vis["Patient_UID"].astype(str).str.strip(),
            "Clinic_Specific_Id": vis["Clinic_Specific_Id"].astype(str).str.strip(),
            "Patient_Name":       vis["Patient_Name"].astype(str).str.strip(),
            "Mobile_Clean":       vis["Mobile_Clean"].map(clean_mobile),
            "Visit_Date":         vis["Visit_Date"].map(parse_date),
        })
        frames.append(a)

    up = DATA_DIR.parent / "uploads"
    for f in sorted(up.glob("consultation_report*.csv")):
        try:
            cr = pd.read_csv(f, dtype=str, engine="python", on_bad_lines="skip").fillna("")
        except Exception:
            continue
        if "Patient UID" not in cr.columns:
            continue
        cr = cr[~cr["Patient UID"].astype(str).str.strip().isin(["", "nan"])]
        cr = cr[cr["Patient Name"].astype(str).str.strip().str.lower() != "total"]
        b = pd.DataFrame({
            "Patient_UID":        cr["Patient UID"].astype(str).str.strip(),
            "Clinic_Specific_Id": cr.get("Clinic Specific Id", "").astype(str).str.strip(),
            "Patient_Name":       cr["Patient Name"].astype(str).str.strip(),
            "Mobile_Clean":       cr["Mobile"].map(clean_mobile),
            "Visit_Date":         cr["Consultation Date"].map(_bill_date),
        })
        frames.append(b)

    if not frames:
        return pd.DataFrame(columns=["Patient_UID", "Clinic_Specific_Id",
                                     "Patient_Name", "Mobile_Clean", "Visit_Date", "_nameset"])
    spine = pd.concat(frames, ignore_index=True)
    spine = spine[spine["Visit_Date"].notna()].copy()
    spine["_dk"] = spine["Patient_UID"] + "|" + spine["Visit_Date"].astype(str)
    spine = spine.drop_duplicates("_dk").drop(columns="_dk").reset_index(drop=True)
    spine["_nameset"] = spine["Patient_Name"].map(_nameset)
    return spine


# ── file readers → list of normalised bills ───────────────────────────────────
def _read_labmate(path: Path) -> list[dict]:
    raw = _read_any_excel(path, sheet_name=0, header=None)
    hdr = [str(h).strip() for h in raw.iloc[2].tolist()]
    df = raw.iloc[3:].copy()
    df.columns = hdr
    out = []
    for _, r in df.iterrows():
        d = _bill_date(r.get("Date"))
        if d is None:
            continue
        out.append({
            "Date": d, "Name": str(r.get("Name") or "").strip(),
            "Mobile": "", "Clinic_Id": "",
            "Gross": _num(r.get("Charge")), "Discount": _num(r.get("Disc")),
            "Net": _num(r.get("Net")), "Invoice_No": str(r.get("Sr.") or "").strip(),
        })
    return out


def _read_marg(path: Path) -> list[dict]:
    full = _read_any_excel(path, sheet_name=0, header=None)
    hdr_row = None
    for i in range(min(12, len(full))):
        if str(full.iloc[i, 0]).strip().upper().startswith("BILL"):
            hdr_row = i
            break
    if hdr_row is None:
        return []
    body = full.iloc[hdr_row + 1:].copy()
    body.columns = (["BILL_NO", "DESC", "VAL"] + list(body.columns))[:body.shape[1]]
    cur_date, out = None, []
    for _, r in body.iterrows():
        bno = str(r.get("BILL_NO") or "").strip()
        desc = str(r.get("DESC") or "").strip()
        val = _num(r.get("VAL"))
        d = _bill_date(bno)
        if d is not None and not desc:
            cur_date = d
            continue
        if not re.match(r"^[A-Z]?\d{3,}", bno):
            continue
        mob = ""
        m = re.match(r"^\s*(\d{10})\b", desc)
        if m:
            mob = clean_mobile(m.group(1))
            rest = desc[m.end():].strip()
        else:
            rest = desc
        cids = re.findall(r"\b(\d{4})\b", rest)
        clinic_id = cids[-1] if cids else ""
        name = re.sub(r"\b\d{2,}\b", " ", rest)
        name = re.sub(r"[^A-Za-z\s]", " ", name).strip()
        out.append({
            "Date": cur_date, "Name": name, "Mobile": mob, "Clinic_Id": clinic_id,
            "Gross": val, "Discount": 0.0, "Net": val, "Invoice_No": bno,
        })
    return out


def _read_any_excel(path: Path, **kw):
    """Open .xlsx, true old .xls, or HTML-masquerading-as-.xls. Tries engines in order."""
    last = None
    for eng in ("openpyxl", "xlrd", None):      # None lets pandas auto-pick
        try:
            return pd.read_excel(path, engine=eng, **kw) if eng else pd.read_excel(path, **kw)
        except Exception as e:
            last = e
            continue
    # final fallback: some Labmate/Marg .xls are actually HTML tables
    try:
        tables = pd.read_html(path)
        if tables:
            return tables[0]
    except Exception as e:
        last = e
    raise last


def detect_kind(path: Path) -> str:
    """'lab' (Labmate) or 'pharmacy' (Marg). Filename keywords win FIRST,
    then content sniff, and the file extension is only the last resort."""
    name = path.name.lower()
    # 1) filename keywords are the strongest signal (a file named LABMATE is lab,
    #    even if its extension is .xls)
    if "labmate" in name or "patho" in name or "patient" in name and "report" in name:
        return "lab"
    if "marg" in name or "sanjeev" in name or "sanjeevni" in name:
        return "pharmacy"
    # 2) content sniff
    try:
        head = _read_any_excel(path, sheet_name=0, header=None, nrows=8)
        flat = " ".join(str(x) for x in head.values.flatten()).upper()
        if "BILL NO" in flat or "MARG" in flat or "SANJEEVNI" in flat:
            return "pharmacy"
        if "CHARGE" in flat and "NET" in flat:
            return "lab"
    except Exception:
        pass
    # 3) extension last resort
    if path.suffix.lower() == ".xls":
        return "pharmacy"
    return "lab"


def read_bills(path: Path, kind: str) -> list[dict]:
    return _read_marg(path) if kind == "pharmacy" else _read_labmate(path)


# ── matcher ───────────────────────────────────────────────────────────────────
class _Matcher:
    def __init__(self, master, spine, window_days=DATE_WINDOW_DAYS):
        self.window = window_days
        self.by_cid, self.by_mob, self.by_ns = {}, {}, {}
        for _, r in master.iterrows():
            cid = str(r["Clinic_Specific_Id"]).strip()
            mob = clean_mobile(r.get("Mobile_Clean", r.get("Mobile", "")))
            ns = _nameset(r["Patient_Name"])
            ident = {"uid": str(r["Patient_UID"]).strip(), "clinic_id": cid,
                     "name": str(r["Patient_Name"]).strip(), "mobile": mob}
            if cid: self.by_cid.setdefault(cid, []).append(ident)
            if mob: self.by_mob.setdefault(mob, []).append(ident)
            if ns:  self.by_ns.setdefault(ns, []).append(ident)
        self.visits_by_ns = {}
        for _, v in spine.iterrows():
            ns = v["_nameset"]
            if ns:
                self.visits_by_ns.setdefault(ns, []).append(v)

    def match(self, bill) -> dict:
        cid = str(bill.get("Clinic_Id") or "").strip()
        if cid and cid in self.by_cid and len(self.by_cid[cid]) == 1:
            return _ok(self.by_cid[cid][0], "clinic_id")
        mob = clean_mobile(bill.get("Mobile"))
        if mob and mob in self.by_mob:
            rows = self.by_mob[mob]
            if len(rows) == 1:
                return _ok(rows[0], "mobile")
            ns = _nameset(bill.get("Name"))
            nar = [r for r in rows if _nameset(r["name"]) & ns] if ns else rows
            if len(nar) == 1:
                return _ok(nar[0], "mobile+name")
            return _review(rows, "mobile_shared")
        ns = _nameset(bill.get("Name"))
        if not ns:
            return _unclassified()
        bdate = bill.get("Date")
        if bdate is not None:
            hits, seen = [], set()
            for cand_ns, visits in self.visits_by_ns.items():
                if not (cand_ns & ns):
                    continue
                if not (ns.issubset(cand_ns) or cand_ns.issubset(ns)):
                    continue
                for v in visits:
                    dd = v["Visit_Date"]
                    if dd and abs((dd - bdate).days) <= self.window:
                        u = str(v["Patient_UID"]).strip()
                        if u not in seen:
                            seen.add(u)
                            hits.append({"uid": u,
                                         "clinic_id": str(v["Clinic_Specific_Id"]).strip(),
                                         "name": str(v["Patient_Name"]).strip(),
                                         "mobile": clean_mobile(v.get("Mobile_Clean", ""))})
            if len(hits) == 1:
                return _ok(hits[0], "name_date")
            if len(hits) > 1:
                return _review(hits, "name_date_multi")
        exact = self.by_ns.get(ns, [])
        if len(exact) == 1:
            return _ok(exact[0], "name_only")
        if len(exact) > 1:
            return _review(exact, "name_multi")
        loose, seen = [], set()
        for cand_ns, rows in self.by_ns.items():
            if ns.issubset(cand_ns) or cand_ns.issubset(ns):
                for r in rows:
                    if r["uid"] not in seen:
                        seen.add(r["uid"])
                        loose.append(r)
        if len(loose) == 1:
            return _ok(loose[0], "name_loose")
        if len(loose) > 1:
            return _review(loose, "name_loose_multi")
        return _unclassified()


def _ok(ident, by):     return {"status": "matched", "by": by, "candidates": [ident], "chosen": ident}
def _review(idents, by): return {"status": "review", "by": by, "candidates": idents, "chosen": None}
def _unclassified():    return {"status": "unclassified", "by": "none", "candidates": [], "chosen": None}


# ── build a ledger row from a bill + match ────────────────────────────────────
def _ledger_row(bill, res, source_tag, source_file, processed_on) -> dict:
    chosen = res["chosen"] or {}
    src = SOURCE_UNCLASSIFIED if res["status"] == "unclassified" else source_tag
    return {
        "Revenue_ID": "X" + uuid.uuid4().hex[:10].upper(),
        "Date": bill["Date"].strftime("%Y-%m-%d") if bill.get("Date") else "",
        "Patient_UID": chosen.get("uid", ""),
        "Clinic_Specific_Id": chosen.get("clinic_id", "") or bill.get("Clinic_Id", ""),
        "Patient_Name": chosen.get("name", "") or bill.get("Name", ""),
        "Mobile_Clean": chosen.get("mobile", "") or clean_mobile(bill.get("Mobile")),
        "Source": src,
        "Gross": bill["Gross"], "Discount": bill["Discount"], "Net": bill["Net"],
        "Mode_Of_Payment": "", "Cash": "", "Online": "", "Pending": "",
        "Shift": "", "Purpose_Of_Visit": "Pathology" if source_tag == SOURCE_LAB else "Pharmacy",
        "Invoice_No": bill.get("Invoice_No", ""),
        "Origin": f"reconciler:{source_file}",
        "Entered_By": "Reconciler (auto)",
        "Processed_On": processed_on,
    }


def _dedup_key(row) -> tuple:
    return (str(row.get("Source", "")), str(row.get("Date", "")),
            str(row.get("Invoice_No", "")), str(row.get("Net", "")),
            str(row.get("Origin", "")))


# ── PREVIEW (no writes) ───────────────────────────────────────────────────────
def preview(filepath: str, kind: str | None = None,
            window_days: int = DATE_WINDOW_DAYS) -> dict:
    """Run the match and return a summary dict — writes NOTHING. Powers the
    confirm screen. Buckets, ₹ totals, and the rows (held back for the writer)."""
    path = Path(filepath)
    kind = kind or detect_kind(path)
    source_tag = SOURCE_PHARMACY if kind == "pharmacy" else SOURCE_LAB
    bills = read_bills(path, kind)
    master = load_master()
    spine = _build_visit_spine()
    matcher = _Matcher(master, spine, window_days)
    processed_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    matched, held = [], []
    bucket = {"matched": [0, 0.0], "review": [0, 0.0], "unclassified": [0, 0.0]}
    by_breakdown = {}
    for b in bills:
        res = matcher.match(b)
        row = _ledger_row(b, res, source_tag, path.name, processed_on)
        bucket[res["status"]][0] += 1
        bucket[res["status"]][1] += b["Net"]
        by_breakdown[res["by"]] = by_breakdown.get(res["by"], [0, 0.0])
        by_breakdown[res["by"]][0] += 1
        by_breakdown[res["by"]][1] += b["Net"]
        if res["status"] == "matched":
            matched.append(row)
        else:
            hr = dict(row)
            hr.update({
                "Match_Status": res["status"], "Match_By": res["by"],
                "Candidate_Count": len(res["candidates"]), "Source_File": path.name,
                "Bill_Name": b.get("Name", ""), "Bill_Mobile": clean_mobile(b.get("Mobile")),
                "Bill_Clinic_Id": b.get("Clinic_Id", ""),
                "Cand_UIDs": ";".join(c["uid"] for c in res["candidates"]),
                "Cand_Clinic_Ids": ";".join(c["clinic_id"] for c in res["candidates"]),
                "Cand_Names": ";".join(c["name"] for c in res["candidates"]),
            })
            held.append(hr)

    in_net = sum(b["Net"] for b in bills)
    # as-of date = latest bill date
    bill_dates = [b["Date"] for b in bills if b.get("Date")]
    as_of = max(bill_dates).strftime("%Y-%m-%d") if bill_dates else ""

    # how much of MATCHED is genuinely new vs already in the ledger (dedup preview)
    existing = {_dedup_key(r) for _, r in revenue.load_revenue().iterrows()}
    new_matched = [r for r in matched if _dedup_key(r) not in existing]

    return {
        "kind": kind, "source_tag": source_tag, "source_file": path.name,
        "as_of": as_of, "window_days": window_days,
        "bills_in": len(bills), "net_in": in_net,
        "buckets": {k: {"count": v[0], "net": v[1]} for k, v in bucket.items()},
        "by_breakdown": {k: {"count": v[0], "net": v[1]} for k, v in by_breakdown.items()},
        "matched_rows": matched, "held_rows": held,
        "new_matched_count": len(new_matched), "new_matched_net": sum(r["Net"] for r in new_matched),
        "already_in_ledger": len(matched) - len(new_matched),
        "processed_on": processed_on,
    }


# ── COMMIT (writes: matched→ledger, held→holding file, + meta) ────────────────
def commit(prev: dict) -> dict:
    """Take a preview() result and write it. Matched rows append to the live ledger
    (de-duped). Held rows append to revenue_pending_review.csv (de-duped). Writes
    the source meta for the banner. Returns counts actually written."""
    # 1. matched → live ledger (de-dup)
    ledger = revenue.load_revenue()
    existing = {_dedup_key(r) for _, r in ledger.iterrows()}
    new_matched = [r for r in prev["matched_rows"] if _dedup_key(r) not in existing]
    if new_matched:
        ledger = pd.concat([ledger, pd.DataFrame(new_matched)[revenue.REVENUE_COLS]],
                           ignore_index=True)
        revenue.save_revenue(ledger)

    # 2. held → holding file (de-dup)
    held_existing = set()
    if PENDING_FILE.exists():
        pend = pd.read_csv(PENDING_FILE, dtype=str).fillna("")
        for c in PENDING_COLS:
            if c not in pend.columns:
                pend[c] = ""
        held_existing = {_dedup_key(r) for _, r in pend.iterrows()}
    else:
        pend = pd.DataFrame(columns=PENDING_COLS)
    new_held = [r for r in prev["held_rows"] if _dedup_key(r) not in held_existing]
    if new_held:
        pend = pd.concat([pend, pd.DataFrame(new_held)[PENDING_COLS]], ignore_index=True)
        pend[PENDING_COLS].to_csv(PENDING_FILE, index=False)

    # 3. meta (powers the last-uploaded banner)
    write_meta(prev, written_matched=len(new_matched), written_held=len(new_held))

    return {
        "matched_written": len(new_matched),
        "matched_skipped_dup": len(prev["matched_rows"]) - len(new_matched),
        "held_written": len(new_held),
        "held_total_pending": len(pend),
    }


# ── holding-file helpers (for the /revenue/review queue + promote) ────────────
def load_pending() -> pd.DataFrame:
    if PENDING_FILE.exists():
        df = pd.read_csv(PENDING_FILE, dtype=str).fillna("")
        for c in PENDING_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[PENDING_COLS]
    return pd.DataFrame(columns=PENDING_COLS)


def promote(revenue_id: str, uid: str, clinic_id: str, name: str, mobile: str) -> dict:
    """Move ONE held bill (by its Revenue_ID) into the live ledger, attributed to
    the chosen patient, and drop it from the holding file. This is the
    'after manual checking' step. Returns {ok, net} or {ok:False, message}."""
    pend = load_pending()
    hit = pend[pend["Revenue_ID"].astype(str) == str(revenue_id)]
    if hit.empty:
        return {"ok": False, "message": "That pending bill was not found (already promoted?)."}
    r = hit.iloc[0].to_dict()
    src = r["Source"]
    if src == SOURCE_UNCLASSIFIED:
        # promoting an unclassified bill → tag it to its real source by purpose
        src = SOURCE_PHARMACY if str(r.get("Purpose_Of_Visit", "")).lower().startswith("pharm") else SOURCE_LAB
    led_row = {c: r.get(c, "") for c in revenue.REVENUE_COLS}
    led_row.update({
        "Revenue_ID": "X" + uuid.uuid4().hex[:10].upper(),
        "Patient_UID": uid, "Clinic_Specific_Id": clinic_id,
        "Patient_Name": name, "Mobile_Clean": clean_mobile(mobile) or mobile,
        "Source": src, "Entered_By": "Reconciler (promoted)",
        "Processed_On": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    ledger = revenue.load_revenue()
    ledger = pd.concat([ledger, pd.DataFrame([led_row])[revenue.REVENUE_COLS]],
                       ignore_index=True)
    revenue.save_revenue(ledger)
    # drop from holding
    pend = pend[pend["Revenue_ID"].astype(str) != str(revenue_id)]
    pend[PENDING_COLS].to_csv(PENDING_FILE, index=False)
    return {"ok": True, "net": _num(led_row["Net"]), "name": name}


# ── meta (the last-uploaded banner) ───────────────────────────────────────────
def write_meta(prev: dict, written_matched: int, written_held: int) -> dict:
    meta = load_meta()
    history = meta.get("history", [])
    entry = {
        "ingested_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_file": prev["source_file"], "kind": prev["kind"],
        "as_of_date": prev.get("as_of", ""),
        "bills_in": prev["bills_in"], "net_in": round(prev["net_in"], 2),
        "matched_net": round(prev["buckets"]["matched"]["net"], 2),
        "held_net": round(prev["buckets"]["review"]["net"] + prev["buckets"]["unclassified"]["net"], 2),
        "matched_written": written_matched, "held_written": written_held,
    }
    history.append(entry)
    meta = {**entry, "history": history[-30:]}
    META_FILE.write_text(json.dumps(meta, indent=2))
    return meta


def load_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text())
        except Exception:
            return {}
    return {}


def meta_status() -> dict:
    """Banner data for the upload page (mirrors _diagnosis_status)."""
    m = load_meta()
    if not m:
        return {}
    asof = (m.get("as_of_date") or "").strip()
    ref = asof or (m.get("ingested_on", "")[:10])
    age_days, stale, as_of_label = None, False, "unknown"
    if ref:
        try:
            age_days = (date.today() - date.fromisoformat(ref)).days
            stale = age_days is not None and age_days > STALE_DAYS
        except Exception:
            age_days = None
    if asof:
        try:
            as_of_label = date.fromisoformat(asof).strftime("%d %b %Y")
        except Exception:
            as_of_label = asof
    else:
        as_of_label = "not in file (using ingest date)"
    pend = load_pending()
    return {
        "as_of_date": asof, "as_of_label": as_of_label,
        "ingested_on": m.get("ingested_on", ""), "source_file": m.get("source_file", "—"),
        "kind": m.get("kind", ""), "bills_in": m.get("bills_in", 0),
        "matched_net": m.get("matched_net", 0.0), "held_net": m.get("held_net", 0.0),
        "matched_written": m.get("matched_written", 0),
        "age_days": age_days, "stale": stale,
        "pending_count": int(len(pend)),
        "pending_net": float(pd.to_numeric(pend["Net"], errors="coerce").fillna(0).sum()) if len(pend) else 0.0,
    }

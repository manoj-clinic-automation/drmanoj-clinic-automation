# S210_MARGTIDY — the Marg push list stops lying, and a ruled-out report can be removed

## What the owner saw (30-Aug-2026) and what each thing actually was

1. **"Clicked Apply on 28/29-Aug, the button is still there."** Apply WORKED and refused
   correctly: those days have no `day_entry` — nothing has FILED them in the books.
   Apply loads bills **into** a filed day; it cannot create the day (F-155 rule: marking
   a report applied while its day is empty was the 17-Aug lie). Not a defect — but the
   page never said so until after the click. The waiting text now explains it.
2. **"A wrong not-filed flag on 27-Aug."** REAL DEFECT (**candidate F-249**): the list
   renders the push-time survey snapshot as if current. 27-Aug was filed later; the badge
   never updated. Fix: the server now answers `filed` from `day_entry` LIVE.
3. **"The June report was ruled out; no remove button exists."** REAL GAP. Fix: a
   **Remove** button on every pending push → owner-only
   `POST /finance/api/marg-push/dismiss` with a mandatory reason. The row and an audit
   entry are KEPT; the replay payload is cleared so it can never apply by accident; the
   list hides dismissed rows. Nothing that ever reached the books is touched.

## The kit

- `patch_finance_app_margtidy.py` — three anchored edits to `/root/finance/finance_app.py`
  (live filed-refresh · dismissed filter · dismiss route). Refuses on missing/ambiguous
  anchors; backup; py_compile with auto-restore. **Selftest 20/20**, dry-run patched +
  compiled against the three newest full finance_app copies in the repo.
- `finance_approvals.html` — S210_ONEMONEY v2 page + Remove button, honest waiting text.
  js_gate PASS; node walk 5/5 (live badge honoured, both buttons, dismiss round-trip).

## Install — VPS, one line at a time (server patch ⇒ restart IS needed)

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_MARGTIDY/patch_finance_app_margtidy.py /root/finance/finance_app.py
```
```
\cp /root/finance/finance_ui/finance_approvals.html /root/finance/finance_ui/finance_approvals.html.bak_S210_MARGTIDY_$(date +%Y%m%d_%H%M%S)
```
```
\cp /root/deploy/repo/deploy_kits/S210_MARGTIDY/finance_approvals.html /root/finance/finance_ui/finance_approvals.html
```
```
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service
```

Walk: reload the approvals page → Marg section: 27-Aug badge gone, Remove beside Apply.
Remove the June report with a one-line reason — it leaves the list, audited.

## What this kit deliberately does NOT do

**28/29-Aug stay "waiting" until their days are FILED** (the entry form creates
`day_entry`; the din-ka-card flow does not). That upstream gap — since the new Darpan flow,
day-filing has no daily owner — is a DESIGN decision for the owner, not a patch:
auto-creating money days from Marg+MPR would set the cash/UPI split from the bank record
alone. Recorded for the session close; nothing here presumes the answer.

*S210 · 30-Aug-2026 · base page S210_ONEMONEY v2 · anchors refused if ambiguous.*

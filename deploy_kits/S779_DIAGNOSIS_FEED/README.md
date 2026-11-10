# S779_DIAGNOSIS_FEED — every visit's diagnosis on the server (the Patients plan, part 1)

**The owner, D884 (10-Nov-2026):** the Patients section starts from each visit's diagnosis. He exported Docterz's *Clinical data
report* for 01-Jul → 09-Nov (10:58 IST 10-Nov) and said so at 18:39.

**Found first (the reason for the reader change):** `/root/finance/docterz_pickup.py` identifies a report by its columns, and a
clinical data report carries the consultation report's own two (Consultation Date, Mode Of Payment). Today it would be taken as
*the consultation report of its latest day* — the 01-Jul → 09-Nov export would have replaced 09-Nov's real report (12 rows) with
2,534 rows (proved on a copy of the 10-Nov nightly database). Both roads — the Drive folder and the reception PC's door — go
through `identify()` / `take()`.

**What changes (nothing visible):**
- `docterz_pickup.py` f8cb978e → a third kind, **clinical** (it carries Diagnosis and Drugs Prescribed): kept by its bytes,
  never replacing or replaced by day (one export may span months); the consultation and follow-up kinds are unchanged.
- NEW `dx_feed.py`: each clinical export, the moment it is taken, into `dx_visit` — one row per patient per visit day: the
  Docterz UID, the clinic ID, the diagnosis as written, the owner's taxonomy (standard diagnosis, category, follow-up
  priority) and the follow-up date advised. No name or mobile. A later export of the same visit wins. `dx_term_map` holds
  the owner's one-tap mappings for terms the taxonomy does not know (the list comes with the Patients section, part 2).
- NEW `diagnosis_normalizer.py`: the owner's taxonomy engine, byte-identical to the follow-up tracker's on his PC (daef69da).

**Proof:** `walk_s779.py` (made-up exports) 17/17; the CONTROL on the live reader red on exactly the misfiling. On the real
catch-up export (device VM, counts only): taken as clinical, 01-Jul → 09-Nov; 09-Nov's consultation report untouched;
2,395 visits of 1,138 patients; 1,695 with a diagnosis, 50 unclassified (29 distinct terms); 1,782 with an advised follow-up date.

**After the install:** the catch-up file goes into the Drive folder *Clinic Records / Docterz exports* (the pickup takes it within
15 minutes); then reception adds the Clinical data report as its third evening export.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s779kit && cp -rp /root/deploy/repo/deploy_kits/S779_DIAGNOSIS_FEED /tmp/s779kit && bash /tmp/s779kit/install_S779_DIAGNOSIS_FEED.sh
```
Undo: `bash /tmp/s779kit/install_S779_DIAGNOSIS_FEED.sh --undo`.

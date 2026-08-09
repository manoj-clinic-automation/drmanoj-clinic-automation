# staff_register/ — commit the LIVE VPS files here (do NOT use a chat copy)

**Discipline: D160 (the live VPS is canonical, not a mirror) + F-52 (a repo copy silently stale vs the VPS is a real trap).**
Do not paste code from the chat transcript into these files — a copy that does not md5-match is exactly the F-52 hazard. Copy the two files straight off the VPS with WinSCP, drop them into this folder, then verify:

```
# on the VPS, or after copying into this folder:
md5sum staff_register.py salary_engine.py
```

Expected (must match exactly before you commit):

| File | Expected md5 | VPS path |
|---|---|---|
| `staff_register.py` | `406a793f96b743bccce53c5c783c1ce3` | `/root/staff_register/staff_register.py` |
| `salary_engine.py`  | `a639f2b4be50b0e0d3e31fa3604ba175` | `/root/staff_register/salary_engine.py` |

**Do NOT commit any of these (F-31 / secrets / generated data):**
- `staff_register.db` (register SQLite — real staff data)
- `register_salary_*.html` (salary previews — rupee figures)
- `salary_inputs_*.csv`, `review_*.csv` (from att_month_report)
- any `*.csv` salary/attendance export
- the document-vault files under the register's storage dir

A `.gitignore` covering `*.db`, `register_salary_*.html`, `*.csv`, and the vault dir should sit in this folder before the first commit (mirrors the F-49 rule).

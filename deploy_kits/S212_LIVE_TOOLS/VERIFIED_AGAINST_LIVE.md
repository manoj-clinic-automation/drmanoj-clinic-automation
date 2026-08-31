# S212_LIVE_TOOLS — verified AGAINST THE LIVE SOURCE, not against itself

**Captured 31-Aug-2026 from the running machines.**

`SUMS.md5` proves a kit is internally intact. It cannot prove the kit matches
the machine — that is F-215, and `S205_LIVE_TOOLS` has verified green while
carrying stale bytes for five sessions. So every row below was measured
**kit against live**, today.

| file | kit md5 | live md5 | live source |
|---|---|---|---|
| `manojz/signatures.json` | `6111889d022e` | `6111889d022e` | `D:\Downloads\margsync\MargPull\signatures.json` |
| `medical/medical_agent.py` | `70d5c4e3c439` | `70d5c4e3c439` | `D:\Downloads\margsync\medical_SendToClinic\medical_agent.py` |
| `medical/SEND_TO_CLINIC.bat` | `fdaf7100893b` | `fdaf7100893b` | `D:\Downloads\margsync\medical_SendToClinic\SEND_TO_CLINIC.bat` |
| `medical/GUARD_AND_SEND.bat` | `957a5f169ce7` | `957a5f169ce7` | `D:\Downloads\margsync\medical_SendToClinic\GUARD_AND_SEND.bat` |
| `medical/marg_export_macro_v3.ahk` | `ab792eb883a6` | `ab792eb883a6` | `D:\Downloads\margsync\medical_SendToClinic\marg_export_macro_v3.ahk` |
| `medical/marg_macro_calib.txt` | `37806b73cf88` | `37806b73cf88` | `D:\Downloads\margsync\medical_SendToClinic\marg_macro_calib.txt` |
| `medical/find_sale_report.ps1` | `5b5e61626010` | `5b5e61626010` | `D:\Downloads\margsync\medical_SendToClinic\find_sale_report.ps1` |
| `manojz/xlrd/` (11 .py) | tree | tree | `D:\Downloads\margsync\MargPull\xlrd\` |
| `medical/xlrd/` (11 .py) | tree | tree | `D:\Downloads\margsync\medical_SendToClinic\xlrd\` |

**All rows match the live source. Verified GREEN.**

**Bytecode (`__pycache__`, `*.pyc`) is deliberately excluded — it is regenerated
on first run and must never sit inside a gate.**

# S204_C1 -- LIVE VPS BYTES, CAPTURED

**Written by `capture_live_to_repo.py` at 2026-08-27 03:35:04 IST. D350 section 4.**

Every file below was read from the running VPS and its md5 matched the pin in
`/root/deploy/live_pins.txt` at the moment of capture. A pin proves identity; these are the bytes.

| live path | md5 | bytes | gate (mob/sec/bearer) |
|---|---|---|---|
| `/root/portal/portal.py` | `24ea2c0b44bad08fbce71908a5019ecc` | 379690 | 0 / 0 / 0 |
| `/root/portal/casepack_portal.py` | `341404d7e6d054b4c49fae09d59ea13b` | 12973 | 0 / 0 / 0 |
| `/root/portal/portal_followups.py` | `98547bc41869360bf224b190fc27cc5d` | 7866 | 0 / 0 / 0 |
| `/root/finance/finance_app.py` | `7948cee0e00494bbee30de1c51d03d74` | 611802 | 0 / 1 / 0 |
| `/root/finance/finance_ui/finance_daily.html` | `20efc5caa664c9b96be23bb66866d21c` | 29864 | 0 / 0 / 0 |
| `/root/deploy/email_agent.py` | `e535c4f8116abd2fe60b7fda334f33ec` | 16021 | 0 / 0 / 0 |
| `/root/finance/finance_ui/finance_entry.html` | `92477b068c67e28661b049b7f3385708` | 71341 | 0 / 0 / 0 |
| `/root/finance/finance_ingest.py` | `6cb83302b022ca3d46a53b32011a7ddd` | 34569 | 0 / 0 / 0 |
| `/root/finance/finance_yesbank.py` | `5dcbdd3a41360c96310929083524fc93` | 22230 | 0 / 0 / 0 |
| `/root/finance/finance_ui/finance_approvals.html` | `89e02711061f473c5e2e118fe50aa1aa` | 62878 | 0 / 0 / 0 |
| `/root/finance/finance_ui/finance_workbench.html` | `420f82c2846bc49d0d12ab5040d8c542` | 18324 | 0 / 0 / 0 |
| `/root/finance/finance_ui/finance_entry_clinic.html` | `d4f7ddaa4c2151935bc81f1bf38c8945` | 38069 | 0 / 0 / 0 |
| `/root/finance/finance_returns.py` | `a46a87e65d951d59baeb9d86c9d8fe59` | 20583 | 0 / 0 / 0 |
| `/root/finance/finance_returns.sql` | `9cec4e317590f845beda87881721cf69` | 3502 | 0 / 0 / 0 |
| `/root/finance/marg_backfill.py` | `fa33ec8a6dfa0ee0b6af5613160f3394` | 13691 | 0 / 0 / 0 |
| `/root/finance/finance_identity.py` | `81092e3ca18c9a85f1de06cc8055d967` | 17266 | 0 / 0 / 0 |
| `/root/finance/finance_import_medical.py` | `7cfde93e1c18a030a031a60ff66795f6` | 24891 | 0 / 0 / 0 |
| `/root/finance/finance_upi.py` | `3f5016f0c64f12b91ab55c18252705c1` | 14446 | 0 / 0 / 0 |
| `/root/finance/finance_schema.sql` | `bef0d8100a1d7da30d049a9cd8eaf365` | 45289 | 0 / 0 / 0 |
| `/root/finance/finance_ui/finance_review.html` | `ddd3d5f61fb2f41950b1a63aa3480650` | 44159 | 0 / 0 / 0 |
| `/root/finance/finance_backup.sh` | `efe6f1b527bffafc21062bc352a063ee` | 3740 | 0 / 0 / 0 |
| `/root/wa/recordings-archive/call_pipeline_worker.py` | `3c8be7f0f6f5960103fb1ed586c48cce` | 11326 | 0 / 0 / 0 |
| `/root/wa/call-hook/callhook_write_probe.py` | `705bd4a1d82068b1ccc74a2567e2ac67` | 9411 | 0 / 0 / 0 |
| `/root/staff_register/salary_engine.py` | `bedd468ee7b89b8f0c130d215a42b6d1` | 56979 | 0 / 0 / 0 |
| `/root/staff_register/salary_policy.py` | `7c0cfb940df2b542d1c4eb849ee3f924` | 51867 | 0 / 0 / 0 |
| `/root/att_scenario.py` | `4dcd19bc02675a07cf0a77fadff6605b` | 27193 | 0 / 0 / 0 |
| `/root/att_month_report.py` | `0184cb139907ee11adcc78c1ecab2daa` | 52559 | 0 / 0 / 0 |
| `/root/wa/clinic_watchdog.py` | `01ca6591a74ec8009bf9748fb7f480c2` | 12391 | 0 / 0 / 0 |
| `/root/assetapp/asset_register.py` | `0cd8fc3bfe8d39322c6162a41124bddf` | 178572 | 0 / 0 / 0 |
| `/root/assetapp/scanner_widget.js` | `4fe8c89386a54ce90786823b53df55bc` | 26279 | 0 / 0 / 0 |
| `/root/shared/sarvam_ocr.py` | `b1cc567b70b5e67c8c021fa22590babf` | 7250 | 0 / 0 / 0 |

**Restore:** copy the flattened file back to its live path, then run
`python3 /root/deploy/verify_live_pins.py` and expect GREEN.

## Gate allowlist entries used

- `/root/finance/finance_app.py` — S204: the only secret-shaped literal is the smoke test's own placeholder CRON_TOKEN at the D204-era Docterz feed check -- a dummy assigned inside selftest(), not a credential. Verified by reading the line at S204.

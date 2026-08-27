# F-216 — per-file disposition for all 85 untracked VPS files

Source census: `D:\\Downloads\\margsync\\_kits\\S205_B2\\_vps_untracked_census.txt`
(85 lines, 6364 bytes, md5 `bbbee3be43f3fe0f7fc6b3a4bf77904e`)

Every row below was decided by **comparing the census md5 against an md5 index of all
2,038 files in the repository working tree** — not by reading a filename.

| code | meaning | count |
|---|---|---|
| **CAP** | capture into the private store; no identical bytes exist in git | **24** |
| **IGN** | IGNORE row in the pin list, with its reason | **23** |
| **PIN** | add a VPS pin row; the bytes are already in git, so it is recoverable today | **38** |
| | **total** | **85** |

---

## CAP — capture privately (24)

| # | VPS path | bytes | md5 | note |
|---|---|---|---|---|
| 1 | `/root/att_config.py` | 1876 | `be5f246beb8e…` | no identical bytes anywhere in the repo |
| 2 | `/root/attlistener_phase1.py` | 4192 | `d926d2c2c085…` | no identical bytes anywhere in the repo |
| 3 | `/root/attlistener_phase15.py` | 4640 | `f65a920d1a00…` | no identical bytes anywhere in the repo |
| 4 | `/root/attlistener_phase16.py` | 4768 | `5c53f966e1a5…` | no identical bytes anywhere in the repo |
| 5 | `/root/attlistener_phase17.py` | 4477 | `36db973850e4…` | no identical bytes anywhere in the repo |
| 6 | `/root/attlistener_phase18.py` | 4475 | `57498adb7cfa…` | no identical bytes anywhere in the repo |
| 7 | `/root/deploy/vps_deploy.sh` | 1697 | `5ec7f06ec0a0…` | no identical bytes anywhere in the repo |
| 8 | `/root/finance/add_finance_tiles.sh` | 5755 | `f506913da411…` | no identical bytes anywhere in the repo |
| 9 | `/root/finance/add_finance_vhost.sh` | 3973 | `772b8ea36117…` | no identical bytes anywhere in the repo |
| 10 | `/root/finance/install_finance_S179.sh` | 4957 | `740afc623150…` | no identical bytes anywhere in the repo |
| 11 | `/root/finance/mask_darpan_tiles.sh` | 3139 | `80baa64920b2…` | no identical bytes anywhere in the repo |
| 12 | `/root/finance/post_install_finance.sh` | 5022 | `be9def7c2614…` | no identical bytes anywhere in the repo |
| 13 | `/root/finance/update_finance_browse.sh` | 3688 | `8a227d43a907…` | no identical bytes anywhere in the repo |
| 14 | `/root/finance/update_finance_epoch.sh` | 3917 | `7fd265b9cf02…` | no identical bytes anywhere in the repo |
| 15 | `/root/finance/update_finance_parked.sh` | 6632 | `6d6987da3775…` | no identical bytes anywhere in the repo |
| 16 | `/root/finance/update_finance_scanner.sh` | 5258 | `45ab77b93dad…` | no identical bytes anywhere in the repo |
| 17 | `/root/finance/update_finance_sso.sh` | 5040 | `cc4fb79039c3…` | no identical bytes anywhere in the repo |
| 18 | `/root/finance/update_finance_ui.sh` | 2499 | `97cf09737114…` | no identical bytes anywhere in the repo |
| 19 | `/root/finance/update_finance_upi.sh` | 5485 | `d50b7137ebda…` | no identical bytes anywhere in the repo |
| 20 | `/root/patch_switcher.py` | 3285 | `c19870c641e9…` | no identical bytes anywhere in the repo |
| 21 | `/root/portal/portal_config.py` | 1042 | `c17886623ff2…` | no identical bytes anywhere in the repo |
| 22 | `/root/wa/staff_ledger.py` | 138215 | `06bf03cb74e8…` | no identical bytes anywhere in the repo |
| 23 | `/root/wa/wa_receiver.py` | 16915 | `9f46279ebc08…` | no identical bytes anywhere in the repo |
| 24 | `/root/watchdog_live_copy.py` | 12279 | `096aba396d28…` | no identical bytes anywhere in the repo |

## IGN — pin-list IGNORE row (23)

| # | VPS path | bytes | md5 | note |
|---|---|---|---|---|
| 1 | `/root/assetapp/asset_register_BACKUP_S158_pre_sso.py` | 67388 | `2f9025dcd5a8…` | superseded snapshot, kept on the box by design |
| 2 | `/root/assetapp/diag_sarvam.py` | 5174 | `b4c6f02846b3…` | one-off diagnostic, never in the live loop |
| 3 | `/root/flow_2026-07_sheet1.html` | 24719 | `d09e65fb9045…` | generated render, re-made by the app that prints it |
| 4 | `/root/flow_2026-07_sheet2.html` | 7102 | `70f327cfac00…` | generated render, re-made by the app that prints it |
| 5 | `/root/flow_2026-07_sheets34.html` | 8794 | `f101fcc337ea…` | generated render, re-made by the app that prints it |
| 6 | `/root/flow_2026-08_sheet1.html` | 19825 | `5a2b2415a65a…` | generated render, re-made by the app that prints it |
| 7 | `/root/flow_2026-08_sheet2.html` | 7312 | `c405cce5ec5c…` | generated render, re-made by the app that prints it |
| 8 | `/root/flow_2026-08_sheets34.html` | 8786 | `f4ee14f047a2…` | generated render, re-made by the app that prints it |
| 9 | `/root/portal/portal_BACKUP_S139_pre_https.py` | 14989 | `04753b02d0ca…` | superseded snapshot, kept on the box by design |
| 10 | `/root/portal/portal_BACKUP_S158_pre_sso.py` | 14994 | `e21241cc9c55…` | superseded snapshot, kept on the box by design |
| 11 | `/root/portal/portal_BACKUP_S159_pre_groupD.py` | 27095 | `e504d2a2826b…` | superseded snapshot, kept on the box by design |
| 12 | `/root/salary_inputs_2026-07.html` | 62553 | `ad3a2e9b0177…` | generated render, re-made by the app that prints it |
| 13 | `/root/salary_inputs_2026-08.html` | 52089 | `40f3dfad5dcd…` | generated render, re-made by the app that prints it |
| 14 | `/root/scenario_2026-07.html` | 10531 | `a47002e8a432…` | generated render, re-made by the app that prints it |
| 15 | `/root/scenario_2026-08.html` | 10455 | `0eefcc5b837a…` | generated render, re-made by the app that prints it |
| 16 | `/root/selftest_grid.html` | 14831 | `b7f7aeb2f303…` | generated render, re-made by the app that prints it |
| 17 | `/root/staff_ledger_BACKUP_S158_pre_sso.py` | 138237 | `8bcf1b2d2967…` | superseded snapshot, kept on the box by design |
| 18 | `/root/staff_register/register_salary_2026-07.html` | 9338 | `c227b11e4a8e…` | generated render, re-made by the app that prints it |
| 19 | `/root/wa/backfill_wa_media.py` | 5351 | `275e85691b67…` | one-off backfill, already run |
| 20 | `/root/wa/check_link.py` | 1648 | `4a8f4fd3ec73…` | one-off diagnostic, never in the live loop |
| 21 | `/root/wa/peek_media.py` | 2961 | `88775560a8da…` | one-off diagnostic, never in the live loop |
| 22 | `/root/wa/recordings-archive/call_verdict_BACKUP_S123_pre_join_redesign.py` | 37246 | `bb17720d4857…` | superseded snapshot, kept on the box by design |
| 23 | `/root/wa/waba_certainty.py` | 2722 | `aa0734986b12…` | one-off diagnostic, never in the live loop |

## PIN — add a Register/pin row (38)

| # | VPS path | bytes | md5 | note |
|---|---|---|---|---|
| 1 | `/root/assetapp/delete_test_assets.py` | 6088 | `24cc30d832d3…` | same bytes in repo: assetapp/delete_test_assets.py |
| 2 | `/root/assetapp/inspect_assets.py` | 1745 | `56771273c651…` | same bytes in repo: assetapp/inspect_assets.py |
| 3 | `/root/att_core.py` | 5090 | `08a815eaa6a0…` | same bytes in repo: attendance/att_core.py |
| 4 | `/root/att_dashboard.py` | 22089 | `ebd8bd85fa97…` | same bytes in repo: attendance/att_dashboard.py |
| 5 | `/root/att_doctor.py` | 14598 | `048257ee5624…` | same bytes in repo: attendance/att_doctor.py |
| 6 | `/root/att_mailer.py` | 6258 | `7d87910df8f7…` | same bytes in repo: attendance/att_mailer.py |
| 7 | `/root/attlistener_v2.py` | 6620 | `94fc58caff28…` | same bytes in repo: attendance/attlistener_v2.py |
| 8 | `/root/deploy/dr_query.py` | 7351 | `c1ed086760c6…` | same bytes in repo: deploy_kits/S193_TOOLS/dr_query.py |
| 9 | `/root/deploy/gen_live_pins.py` | 22786 | `9c402c366e7c…` | same bytes in repo: deploy_kits/S187_V1a/gen_live_pins.py |
| 10 | `/root/finance/finance_migration_S182_c2.sql` | 6753 | `22c67f25b17e…` | same bytes in repo: deploy_kits/S182_C2a/finance_migration_S182_c2.sql |
| 11 | `/root/finance/finance_migration_S182_clinic.sql` | 8064 | `bd2bb0ee5c58…` | same bytes in repo: deploy_kits/S182_C1e/finance_migration_S182_clinic.sql |
| 12 | `/root/portal/gmb.html` | 70745 | `e33aa6125a59…` | same bytes in repo: gmail-automation/clinic-hub/GMB_Review_Assist_DrManojAgarwal.html |
| 13 | `/root/portal/portal_setup.py` | 4052 | `0a9dcf636af4…` | same bytes in repo: launcher/portal_setup.py |
| 14 | `/root/prune_backups.py` | 10688 | `9dce8ea6dd61…` | same bytes in repo: tools/prune_backups.py |
| 15 | `/root/wa/call-hook/backfill_call_durations.py` | 5023 | `974ae54952db…` | same bytes in repo: call-hook/backfill_call_durations.py |
| 16 | `/root/wa/call-hook/callhook_watchdog.py` | 25042 | `665797f8d18d…` | same bytes in repo: call-hook/callhook_watchdog.py |
| 17 | `/root/wa/call-hook/peek_callhook.py` | 2780 | `a9842439e2d3…` | same bytes in repo: call-hook/peek_callhook.py |
| 18 | `/root/wa/call_api.py` | 12608 | `930b42c49e8c…` | same bytes in repo: wa-call/call_api.py |
| 19 | `/root/wa/clinic_health_report.py` | 11654 | `08e1a483ac47…` | same bytes in repo: diagnostics-vps/clinic_health_report.py |
| 20 | `/root/wa/followup_receiver.py` | 2505 | `384e9ed8209a…` | same bytes in repo: followup-vps/followup_receiver.py |
| 21 | `/root/wa/get_users.py` | 3983 | `8aa05229a946…` | same bytes in repo: obd/get_users.py |
| 22 | `/root/wa/insert_call_proxy.py` | 2844 | `056b6663db3e…` | same bytes in repo: wa-call/insert_call_proxy.py |
| 23 | `/root/wa/notifier_wa.py` | 8990 | `feeea7efca7b…` | same bytes in repo: notifier/notifier_wa.py |
| 24 | `/root/wa/obd_test.py` | 3459 | `036e1d942dfa…` | same bytes in repo: obd/obd_test.py |
| 25 | `/root/wa/plan_followups_from_xlsx.py` | 9316 | `8aa736062abe…` | same bytes in repo: wa-approve/plan_followups_from_xlsx.py |
| 26 | `/root/wa/push_followups_vps.py` | 16656 | `8823b3963342…` | same bytes in repo: followup-vps/push_followups_vps.py |
| 27 | `/root/wa/recordings-archive/call_recording_archive.py` | 22564 | `d6b35e0a9386…` | same bytes in repo: recordings-archive/call_recording_archive.py |
| 28 | `/root/wa/recordings-archive/call_transcription.py` | 24148 | `ee8d3e4134ff…` | same bytes in repo: recordings-archive/call_transcription.py |
| 29 | `/root/wa/rotate_callhook.sh` | 6405 | `9e1f7802abaa…` | same bytes in repo: call-hook/rotate_callhook.sh |
| 30 | `/root/wa/wa_approve.py` | 15766 | `c650f4c28ed5…` | same bytes in repo: wa-approve/wa_approve.py |
| 31 | `/root/wa/wa_send.py` | 12478 | `67398d6a438c…` | same bytes in repo: wa-send/wa_send.py |
| 32 | `/root/wa/wa_send_api.py` | 16182 | `a3ed37080aae…` | same bytes in repo: wa-send/wa_send_api.py |
| 33 | `/root/wa/waba.py` | 11013 | `031b46429c08…` | same bytes in repo: wa/waba.py |
| 34 | `/root/wa/waba_diag.py` | 6415 | `b560d12d0385…` | same bytes in repo: wa/waba_diag.py |
| 35 | `/root/wa/waba_probe.sh` | 5758 | `02f9fc34a98d…` | same bytes in repo: wa-diagnostics/waba_probe.sh |
| 36 | `/root/wa/waba_recovery_window.sh` | 5040 | `e1cfa25e8e10…` | same bytes in repo: wa-diagnostics/waba_recovery_window.sh |
| 37 | `/root/wa/waba_template_test.py` | 7102 | `5200a0a80bb4…` | same bytes in repo: wa-diagnostics/waba_template_test.py |
| 38 | `/root/wa/waba_text_probe.py` | 7845 | `f05748f58985…` | same bytes in repo: wa-send/waba_text_probe.py |

---

## The five files with a namesake in the repo but different bytes

| VPS path | repo namesake | same name, different bytes |
|---|---|---|
| `/root/deploy/vps_deploy.sh` | `deploy_kits/S182_C1a/deploy/vps_deploy.sh` | yes |
| `/root/wa/staff_ledger.py` | `deploy_kits/S200_R6/staff_ledger.py` | yes |
| `/root/wa/wa_receiver.py` | `wa-receiver/wa_receiver.py` | yes |
| `/root/wa/check_link.py` | `wa-receiver/check_link.py` | yes |
| `/root/wa/peek_media.py` | `wa-receiver/peek_media.py` | yes |

*Generated from measurement. Do not hand-edit — regenerate.*

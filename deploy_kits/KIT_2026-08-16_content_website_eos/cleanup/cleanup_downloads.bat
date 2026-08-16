@echo off
REM Session cleanup - archive folder includes PROJECT NAME per protocol v2
set SRC=D:\Downloads
set DST=D:\Downloads\_session_archive\Content_Website_Ops\2026-08-16
if not exist "%DST%" mkdir "%DST%"
for %%F in (Blog01_Knee_OA_v3_FINAL.md Blog01_Knee_OA_v4_FINAL.md Blog01_Media_Distribution_Index.md Blog02_Low_Back_Pain_v1.md Blog03_Cervical_Spondylosis_v1.md Blog04_Sciatica_v1.md Batch1_Media_Distribution_Index.md Graphic_Content_Strategy.md links_hub_page.html website_monitor.gs DrManoj_Content_System_Master_Vision_v1.md DrManoj_Content_System_Master_Vision_v2.md DrManoj_Website_Baseline_Audit_2026-08-16.md DrManoj_Website_Ops_SEO_Monitoring_Handoff.md DrManoj_Website_Setup_Runbook.md Step5_WordPress_Edit_Sheet.md Step6_OffSite_NAP_Correction_Pack.md NK_Pathology_Website_Handoff.md Knee_OA_Blog_DrManoj.md Knee_OA_Blog_DrManoj_v2.md push_kit.bat) do (
  if exist "%SRC%\%%F" move /y "%SRC%\%%F" "%DST%\" >nul && echo archived %%F
)
if exist "%SRC%\KIT_2026-08-16_content_website_eos.zip" move /y "%SRC%\KIT_2026-08-16_content_website_eos.zip" "%DST%\" >nul && echo archived kit zip
if exist "%SRC%\EOS_RUN.bat" move /y "%SRC%\EOS_RUN.bat" "%DST%\" >nul && echo archived runner
echo Cleanup done. Archive: %DST%

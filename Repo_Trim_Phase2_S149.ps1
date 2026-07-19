<#
  Repo_Trim_Phase2_S149.ps1  —  Dr. Manoj clinic-automation repo tidy, Phase 2 (Session 149)
  ------------------------------------------------------------------------------------------
  Continues the S148 trim. Moves the remaining *unambiguously historical* documents into
  canonical-docs/archive/ with `git mv` (history preserved). Same safety pattern as
  Repo_Trim_S148.ps1: DRY-RUN by default, explicit file lists (NO wildcards), collision-guarded,
  and it NEVER commits or pushes — you review `git status` and commit yourself.

  WHY EXPLICIT LISTS, NOT A WILDCARD SWEEP:
    A naive "archive everything in docs/" would bury LIVE clinic-facing manuals (Staff Manual,
    Doctor Manual, Wall Cards, the Hinglish Call-Desk Companion) and reference docs of uncertain
    currency. That is the exact trap that nearly buried the Maintenance SOP in S148. So this script
    moves ONLY the 41 files it is certain are superseded, and LEAVES the 12 "hold" files in place
    for you to rule on (listed at the foot; nothing touches them).

  USAGE (from the repo root, GitHub Desktop's git on PATH):
    Dry run (default, shows every planned move, changes nothing):
        powershell -ExecutionPolicy Bypass -File .\Repo_Trim_Phase2_S149.ps1
    Execute the moves:
        powershell -ExecutionPolicy Bypass -File .\Repo_Trim_Phase2_S149.ps1 -Execute
    Then review and commit:
        git status
        git commit -m "S149 Phase-2 repo tidy: archive 41 superseded docs (pure renames)"
        git push
#>

param([switch]$Execute)

$ErrorActionPreference = "Stop"
$RepoRoot   = (Get-Location).Path
$ArchiveDir = "canonical-docs/archive"

# --- sanity: are we at the repo root? ---
if (-not (Test-Path (Join-Path $RepoRoot "canonical-docs"))) {
    Write-Host "ERROR: run this from the repo root (canonical-docs/ not found here)." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $RepoRoot $ArchiveDir))) {
    Write-Host "ERROR: $ArchiveDir does not exist. Run the S148 trim first." -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------------------
#  MOVE LIST — 38 files, each an explicit source path -> canonical-docs/archive/
# ---------------------------------------------------------------------------

# (a) canonical-docs/ stragglers: superseded at the S148 CLOSE, after the S148 trim had already run,
#     so that trim could not have caught them. Their successors are the current Tier-0 loop docs.
$CanonicalStragglers = @(
    "canonical-docs/KB_Register_v2_0_S147.md",           # -> superseded by KB_Register v2.2
    "canonical-docs/KB_Register_v2_1_S148.md",           # -> superseded by KB_Register v2.2 (S149 close)
    "canonical-docs/KB_History_Archive_v1_0_S147.md",    # -> superseded by KB_History_Archive v1.1
    "canonical-docs/START_HERE_SESSION_148.md",          # -> superseded by START_HERE_SESSION_150
    "canonical-docs/START_HERE_SESSION_149.md",          # -> superseded by START_HERE_SESSION_150 (S149 close)
    "canonical-docs/HANDOFF_RUNBOOK_2026-07-19_Session148_v86.md"  # -> superseded by runbook v87 (S149 close)
)

# (b) docs/ — 35 unambiguously historical files (old KB versions, umbrella deltas, old runbooks,
#     superseded specs, session carryovers, commit notes, old callback-dashboard docs).
$DocsHistorical = @(
    # old Master KB versions / deltas (current KB = Register v2.x + Archive v1.x)
    "docs/Clinic_Master_KB_SystemsRegister_v1_7.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_15.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_27.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_28.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_36.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_37_Delta.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_39.md",
    "docs/Clinic_Master_KB_SystemsRegister_v1_41_delta.md",
    # old Umbrella Architecture versions / deltas (current = v1.58)
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1.2_28Jun2026.md",
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1_21_Delta.md",
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1_22_Delta.md",
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1_26_Delta.md",
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1_27_Delta.md",
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1_29.md",
    "docs/Dr_Manoj_Clinic_Umbrella_Architecture_v1_6_30Jun2026.md",
    # old Handoff Runbooks (current = v86)
    "docs/HANDOFF_RUNBOOK_2026-06-27_v9.md",
    "docs/HANDOFF_RUNBOOK_2026-06-28_v12.md",
    "docs/HANDOFF_RUNBOOK_2026-06-30_Session19_v17.md",
    "docs/HANDOFF_RUNBOOK_2026-07-02_Session28_v26.md",
    "docs/HANDOFF_RUNBOOK_2026-07-04_Session59_v39.md",
    "docs/HANDOFF_RUNBOOK_2026-07-04_Session60_v40.md",
    "docs/HANDOFF_RUNBOOK_2026-07-05_Session67_v47.md",
    "docs/HANDOFF_RUNBOOK_2026-07-05_Session73_v48.md",
    "docs/HANDOFF_RUNBOOK_2026-07-05_Session75_v50.md",
    "docs/HANDOFF_RUNBOOK_2026-07-07_Session94_v52.md",
    # superseded specs (current = Call Console v2.4, Diagnostics v2.3)
    "docs/Call_Console_Evolution_Spec_v1_1.md",
    "docs/Diagnostics_Surveillance_System_Spec_v1_1.md",
    # session carryovers / commit notes / old start-here (historical process docs)
    "docs/CARRYOVER_Session9_to_10_27Jun2026.md",
    "docs/CARRYOVER_Session14_to_15_28Jun2026.md",
    "docs/SESSION16_GITHUB_COMMIT_NOTES.md",
    "docs/SESSION125_GITHUB_COMMIT_NOTES.md",
    "docs/START_HERE_Session_13_prompt.md",
    # old callback-dashboard docs (superseded by Frontend Dashboard v4 + Call Console Evolution v2.4)
    "docs/Callback_Dashboard_KB_v1.md",
    "docs/Callback_Dashboard_TROUBLESHOOTER_v1.md",
    "docs/Callback_Dashboard_TROUBLESHOOT_LOG.md"
)

$MoveList = $CanonicalStragglers + $DocsHistorical

Write-Host ""
Write-Host "=== Repo_Trim_Phase2_S149  ($(if($Execute){'EXECUTE'}else{'DRY-RUN'})) ===" -ForegroundColor Cyan
Write-Host "Planned moves: $($MoveList.Count)  ->  $ArchiveDir" -ForegroundColor Cyan
Write-Host ""

$moved = 0; $skipped = 0; $collision = 0
foreach ($src in $MoveList) {
    $leaf = Split-Path $src -Leaf
    $dst  = "$ArchiveDir/$leaf"

    if (-not (Test-Path $src)) {
        Write-Host "  SKIP (not found): $src" -ForegroundColor DarkYellow; $skipped++; continue
    }
    if (Test-Path $dst) {
        Write-Host "  COLLISION (dest exists, left untouched): $dst" -ForegroundColor Red; $collision++; continue
    }
    if ($Execute) {
        git mv -- "$src" "$dst"
        Write-Host "  moved: $src -> $dst" -ForegroundColor Green
    } else {
        Write-Host "  would move: $src -> $dst"
    }
    $moved++
}

Write-Host ""
Write-Host "planned/moved=$moved  skipped(missing)=$skipped  collisions=$collision" -ForegroundColor Cyan
if (-not $Execute) {
    Write-Host "DRY-RUN only. Re-run with -Execute to perform the moves." -ForegroundColor Yellow
} else {
    Write-Host "Done. Review 'git status', then commit + push yourself." -ForegroundColor Yellow
}

<#
  ------------------------------------------------------------------------------------------
  HELD — 12 files this script deliberately does NOT touch. Confirm their status before moving.
  These are potentially LIVE clinic-facing or current reference docs; burying one is the
  documented S148 near-miss. Move them by hand only if you confirm they are superseded.

    LIVE clinic manuals (almost certainly current — probably belong in docs/ or a manuals/ folder):
      docs/01_Troubleshooting_Runbook_DrManojClinic.docx
      docs/02_Staff_Manual_CallConsole_DrManojClinic.docx
      docs/03_Doctor_Manual_DrManojClinic.docx
      docs/A4_Wall_Card_Call_Flows_DrManojClinic.docx
      docs/A4_Wall_Card_Call_Flows_DrManojClinic.pdf
      docs/Call_Desk_Companion_Hinglish_DrManojClinic.docx

    Reference docs of uncertain currency (confirm before archiving):
      docs/Dashboard_Capability_Map_and_Inventory.md
      docs/Google_Workspace_Inventory_v1_0_30Jun2026.md
      docs/TPA_Verification_Ingestion_Brief_v1_0.md
      docs/Voice_Bot_Pipeline_Plan_v1_1.md
      docs/context/FollowupTracker_WABA_Context_Consolidated.md
      docs/context/MyOperator_WABA_Project_Context.md
  ------------------------------------------------------------------------------------------
#>

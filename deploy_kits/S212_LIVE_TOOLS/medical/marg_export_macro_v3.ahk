#Requires AutoHotkey v2.0
#SingleInstance Force
; =============================================================================
;  marg_export_macro_v3.ahk   (S195)   -- generate the day's Marg export, then
;  hand it to GUARD_AND_SEND.bat, which checks it and sends it.
;
;  v3 CHANGES (21-08-2026, after the live 401 incident)
;   * RunGuard is now TRUE - the macro completes the whole job.
;   * It no longer waits for a FIXED filename. Marg names exports by SLOT
;     (REPORT_1.XLS, REPORT_2.XLS, even REPORT_7JJ0J0TR7.XLS) and which one it
;     uses changes. v2 watched D:\MARGERP\users\61376\report\REPORT_2.XLS and
;     would have hung forever the day Marg picked a different slot -- exactly
;     the assumption that broke the sender. v3 watches ALL report folders for
;     ANY REPORT*.XLS and detects whichever one gets written.
;   * It passes NO filename to GUARD_AND_SEND.bat. The wrapper looks INSIDE the
;     files and picks the newest complete BILL WISE SALES report itself, so a
;     stock or purchase export can never be mistaken for the day's sale report.
;
;  Calibrated on the medical PC (maximised Marg), S195.
;  KEYS:  Ctrl+Alt+C capture a position   Ctrl+Alt+G run   Esc quit
; =============================================================================

CoordMode "Mouse", "Screen"
CoordMode "ToolTip", "Screen"
SetTitleMatchMode 2
SetKeyDelay 60, 40

; ======================= CONFIG ==============================================
global MargWinTitle := "MARG ERP 9+"
global GuardBat     := "D:\SendToClinic\GUARD_AND_SEND.bat"
global MargUsers    := "D:\MARGERP\users"
global GuardExpect := "any"          ; the business date the guard demands
global RunGuard     := true                 ; v3: complete the job

; --- calibrated screen positions (maximised Marg, medical PC) ---
global CFG_TILE_X := 1804, CFG_TILE_Y := 941     ; "Daily Sale" tile
global CFG_RTYPE_X := 1132, CFG_RTYPE_Y := 850   ; Report Type dropdown
global CFG_WITEM_X := 984,  CFG_WITEM_Y := 992   ; "With Item Deta." dropdown
global CFG_VIEW_X := 641,  CFG_VIEW_Y := 1414    ; View button
global CFG_EXCEL_X := 1391, CFG_EXCEL_Y := 1254  ; Excel button on the report

global SET_DATE := false                    ; Marg already shows yesterday
global CFG_DATEFROM_X := 0, CFG_DATEFROM_Y := 0
global CFG_DATETO_X := 0,  CFG_DATETO_Y := 0

global Enters_After_View  := 2
global Enters_After_Excel := 4
global WaitDialog_ms := 1500
global WaitReport_ms := 2500
global WaitExcel_ms  := 4000
global WaitFile_ms   := 90000               ; how long to wait for a new export

global CalibFile := A_ScriptDir "\marg_macro_calib.txt"

; ======================= helpers =============================================
; The newest REPORT*.XLS anywhere under users\*\report\ -- name-agnostic.
NewestReport() {
    best := "", bestT := ""
    Loop Files, MargUsers "\*", "D" {
        dir := A_LoopFilePath "\report"
        if !DirExist(dir)
            continue
        Loop Files, dir "\REPORT*.XLS" {
            t := FileGetTime(A_LoopFilePath, "M")
            if (bestT = "" || t > bestT) {
                bestT := t
                best  := A_LoopFilePath
            }
        }
    }
    return Map("path", best, "time", bestT)
}

; ======================= calibration =========================================
CaptureXY() {
    MouseGetPos(&mx, &my)
    FileAppend(FormatTime(A_Now, "HH:mm:ss") "  X=" mx "  Y=" my "`n", CalibFile)
    ToolTip("Captured  X=" mx "  Y=" my)
    SetTimer(() => ToolTip(), -1500)
}
^!c::CaptureXY()
F9::CaptureXY()
^!q::ExitApp()
Esc::ExitApp()

; ======================= run =================================================
RunExport() {
    global
    if !WinExist(MargWinTitle) {
        MsgBox("Open Marg and log in first, then press Ctrl+Alt+G.", "Marg not open", 48)
        return
    }
    WinActivate(MargWinTitle)
    WinWaitActive(MargWinTitle, , 10)
    Sleep 500

    ; remember the newest export BEFORE we start, so we can spot the new one
    before := NewestReport()

    Click(CFG_TILE_X " " CFG_TILE_Y)                 ; Daily Sale tile
    Sleep WaitDialog_ms

    if (SET_DATE) {
        d := FormatTime(DateAdd(A_Now, -1, "Days"), "ddMMyyyy")
        Click(CFG_DATEFROM_X " " CFG_DATEFROM_Y)
    Sleep(250)
    SendText(d)
    Send("{Enter}")
    Sleep(250)
        Click(CFG_DATETO_X " " CFG_DATETO_Y)
    Sleep(250)
    SendText(d)
    Send("{Enter}")
    Sleep(250)
    }

    Click(CFG_RTYPE_X " " CFG_RTYPE_Y)               ; Report Type -> Detail
    Sleep 400
    SendText("Detail")
    Sleep(200)
    Send("{Enter}")
    Sleep(300)

    Click(CFG_WITEM_X " " CFG_WITEM_Y)               ; With Item Deta. -> Yes
    Sleep 400
    SendText("Yes")
    Sleep(200)
    Send("{Enter}")
    Sleep(300)

    Click(CFG_VIEW_X " " CFG_VIEW_Y)                 ; View
    Sleep WaitReport_ms
    Loop Enters_After_View {
        Send("{Enter}")
        Sleep 500
    }
    Sleep WaitReport_ms

    Click(CFG_EXCEL_X " " CFG_EXCEL_Y)               ; Excel
    Sleep WaitExcel_ms
    Loop Enters_After_Excel {
        Send("{Enter}")
        Sleep 700
    }

    ; ---- wait for ANY new/changed REPORT*.XLS, whatever Marg called it ----
    startTick := A_TickCount
    fresh := ""
    Loop {
        Sleep 1000
        now := NewestReport()
        if (now["path"] != "" && (now["path"] != before["path"] || now["time"] != before["time"])) {
            fresh := now["path"]
            break
        }
        if (A_TickCount - startTick > WaitFile_ms) {
            MsgBox("No new Marg export appeared in " Round(WaitFile_ms/1000) "s.`n`n"
                 . "Nothing was sent. Run the export by hand and check Marg.",
                   "Export not detected", 48)
            return
        }
    }
    Sleep 2000                                        ; let Marg finish writing

    try WinClose("REPORT ahk_exe EXCEL.EXE")          ; close Marg's Excel
    Sleep 1000

    if (!RunGuard || !FileExist(GuardBat)) {
        MsgBox("Export finished (guard/send skipped).`n`n" fresh, "Done - export only", 64)
        return
    }
    ; Pass NO filename: GUARD_AND_SEND.bat looks inside the files and picks the
    ; newest COMPLETE SALE report itself. That is the check that matters.
    RunWait(A_ComSpec ' /c ""' GuardBat '" ' GuardExpect ' AUTO"', , "Hide")
    MsgBox("Export + check + send finished.`n`nExport: " fresh
         . "`n`nIf anything was refused it is in guard_alerts.txt, and a copy is "
         . "parked in NEEDS_UPLOAD\ for manual upload.", "Done", 64)
}
^!g::RunExport()
^!r::RunExport()
F10::RunExport()


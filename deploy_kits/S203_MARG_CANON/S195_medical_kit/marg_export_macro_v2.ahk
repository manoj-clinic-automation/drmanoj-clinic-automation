#Requires AutoHotkey v2.0
#SingleInstance Force
; =============================================================================
;  marg_export_macro_v2.ahk   (S195, Method B auto-generation)   AutoHotkey v2
;
;  Reproduces the manual Marg BILL WISE SALES export, then (optionally) hands the
;  file to GUARD_AND_SEND.bat. Written for AutoHotkey v2 (your AutoHotkey_2.0.26).
;
;  YOUR FLOW (as recorded):
;    1. Click the "Daily Sale" tile on the Marg home screen.
;    2. (date is usually already yesterday; optional to set it)
;    3. Report Type dropdown  -> "Detail"
;    4. With Item Deta dropdown -> "Yes"
;    5. Click "View" -> Enter x(1-2) -> report opens
;    6. Click the "Excel" button -> Enter x(few) -> Excel writes REPORT_x.XLS
;    7. Close Excel; then guard-and-send (if enabled).
;
;  KEYS (chosen to need NO Fn key — works on HP laptops):
;    Ctrl+Alt+C  = capture the mouse X,Y  (during calibration)
;    Ctrl+Alt+G  = run the whole export  (G = Go; Ctrl+Alt+R is often taken by
;                  screen recorders, so we use G instead)
;    Ctrl+Alt+Q  or  Esc  = quit the macro
;    (F10 also runs it if your keyboard sends a real F10.)
;
;  CALIBRATE ONCE on the medical PC:
;    * Run this file (drag it onto AutoHotkey64.exe, or right-click -> Open with
;      -> AutoHotkey64.exe).
;    * Maximize Marg. Do the export by hand slowly; at EACH control below hover
;      the mouse and press Ctrl+Alt+C. Each press writes X,Y to
;      marg_macro_calib.txt and shows a tooltip.
;    * Paste those numbers into the CONFIG block (replace the 0s). Save.
;    * Press Ctrl+Alt+G to run the whole thing once, watching. Tune the Sleeps /
;      Enter counts. Press Esc anytime to abort.
; =============================================================================

CoordMode "Mouse", "Screen"
CoordMode "ToolTip", "Screen"
SetTitleMatchMode 2
SetKeyDelay 60, 40

; ======================= CONFIG (fill from calibration) ======================
global MargWinTitle := "MARG ERP 9+"                 ; part of the Marg window title
global GuardBat     := "D:\SendToClinic\GUARD_AND_SEND.bat"
global ReportFile   := "D:\MARGERP\users\61376\report\REPORT_2.XLS"  ; file Marg writes
global GuardExpect  := "yesterday"
global RunGuard     := false      ; keep FALSE while calibrating (export only, no send)

; --- screen positions (X,Y). Captured on the medical PC, S195 (21-Aug-2026). ---
global CFG_TILE_X := 1804, CFG_TILE_Y := 941     ; the "Daily Sale" tile
global CFG_RTYPE_X := 1132, CFG_RTYPE_Y := 850   ; the Report Type dropdown
global CFG_WITEM_X := 984, CFG_WITEM_Y := 992    ; the "With Item Deta." dropdown
global CFG_VIEW_X := 641, CFG_VIEW_Y := 1414     ; the "View" button
global CFG_EXCEL_X := 1391, CFG_EXCEL_Y := 1254  ; the "Excel" button on the report

; --- optional: set the date to yesterday (leave SET_DATE false if Marg already
;     shows yesterday) ---
global SET_DATE := false
global CFG_DATEFROM_X := 0, CFG_DATEFROM_Y := 0
global CFG_DATETO_X := 0, CFG_DATETO_Y := 0

; --- timing / key counts (tune during the test run) ---
global Enters_After_View  := 2
global Enters_After_Excel := 4
global WaitDialog_ms := 1500
global WaitReport_ms := 2500
global WaitExcel_ms  := 4000

global CalibFile := A_ScriptDir "\marg_macro_calib.txt"

; ======================= CALIBRATION HOTKEYS =================================
CaptureXY(*) {
    global CalibFile
    MouseGetPos(&mx, &my)
    FileAppend(FormatTime(A_Now, "HH:mm:ss") "  X=" mx "  Y=" my "`n", CalibFile)
    ToolTip("Captured  X=" mx "  Y=" my "`n(saved to marg_macro_calib.txt)")
    SetTimer(() => ToolTip(), -1500)
}
; Ctrl+Alt+C is the reliable capture key on HP laptops (no Fn needed). F9 too.
^!c::CaptureXY()
F9::CaptureXY()

; Quit
^!q::ExitApp()
Esc::ExitApp()

; ======================= RUN THE MACRO  (Ctrl+Alt+R or F10) ==================
RunExport(*) {
    global
    if (CFG_TILE_X = 0 or CFG_RTYPE_X = 0 or CFG_VIEW_X = 0 or CFG_EXCEL_X = 0) {
        MsgBox("Capture the button positions with F9 and paste them into CONFIG first.", "Not calibrated", 48)
        return
    }
    if !WinExist(MargWinTitle) {
        MsgBox("Open Marg and log in first, then press F10.", "Marg not open", 48)
        return
    }
    WinActivate(MargWinTitle)
    WinWaitActive(MargWinTitle, , 10)
    Sleep 500

    ; 1. open the Daily Sale tile
    Click(CFG_TILE_X " " CFG_TILE_Y)
    Sleep WaitDialog_ms

    ; 2. optional: set date to yesterday
    if (SET_DATE) {
        d := FormatTime(DateAdd(A_Now, -1, "Days"), "ddMMyyyy")
        Click(CFG_DATEFROM_X " " CFG_DATEFROM_Y)
        Sleep 250
        SendText(d)
        Send("{Enter}")
        Sleep 250
        Click(CFG_DATETO_X " " CFG_DATETO_Y)
        Sleep 250
        SendText(d)
        Send("{Enter}")
        Sleep 250
    }

    ; 3. Report Type -> Detail
    Click(CFG_RTYPE_X " " CFG_RTYPE_Y)
    Sleep 400
    SendText("Detail")
    Sleep 200
    Send("{Enter}")
    Sleep 300

    ; 4. With Item Deta. -> Yes
    Click(CFG_WITEM_X " " CFG_WITEM_Y)
    Sleep 400
    SendText("Yes")
    Sleep 200
    Send("{Enter}")
    Sleep 300

    ; remember old file time
    before := FileExist(ReportFile) ? FileGetTime(ReportFile, "M") : ""

    ; 5. View -> Enter(s)
    Click(CFG_VIEW_X " " CFG_VIEW_Y)
    Sleep WaitReport_ms
    Loop Enters_After_View {
        Send("{Enter}")
        Sleep 500
    }
    Sleep WaitReport_ms

    ; 6. Excel button -> Enter(s)
    Click(CFG_EXCEL_X " " CFG_EXCEL_Y)
    Sleep WaitExcel_ms
    Loop Enters_After_Excel {
        Send("{Enter}")
        Sleep 700
    }

    ; 7. wait for the file to be (re)written
    startTick := A_TickCount
    Loop {
        Sleep 1000
        if FileExist(ReportFile) {
            now := FileGetTime(ReportFile, "M")
            if (now != before)
                break
        }
        if (A_TickCount - startTick > 60000) {
            MsgBox("REPORT file was not rewritten in time. Check Marg / Excel by hand.", "No new file", 48)
            return
        }
    }
    Sleep 1500

    ; close the Excel that Marg opened
    try WinClose("REPORT ahk_exe EXCEL.EXE")
    Sleep 1000

    ; 8. validate + send (only if enabled and the guard is present)
    if (RunGuard && FileExist(GuardBat)) {
        RunWait(A_ComSpec ' /c "' GuardBat '" ' GuardExpect ' AUTO', , "Hide")
        MsgBox("Export + guard-and-send finished. Check the summary / guard_alerts.txt.", "Done", 64)
    } else {
        MsgBox("Export finished (guard/send skipped). File: " ReportFile, "Done - export only", 64)
    }
}
^!g::RunExport()      ; primary run key: Ctrl+Alt+G (Go)
^!r::RunExport()      ; alternate (may be grabbed by a screen recorder)
F10::RunExport()

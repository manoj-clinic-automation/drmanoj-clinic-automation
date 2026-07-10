# F-17 — the repo's `WebApp.gs` is the PRE-FIX file wearing the live file's name

Not exploitable (repo code does not execute; deployment v64 has the setters deleted) — but the
filename lies to its next reader, including the next assistant.

    git rm  dashboard/WebApp_v19_D189.gs
    cp  dashboard_F17_fix/WebApp.gs                      dashboard/WebApp.gs
    cp  dashboard_F17_fix/WebApp_PREFIX_ROLLBACK_S129.gs dashboard/WebApp_PREFIX_ROLLBACK_S129.gs
    git mv dashboard/CallField.gs.gs dashboard/CallField.gs
    git mv dashboard/Probe.gs.gs     dashboard/Probe.gs

Verify:  md5sum dashboard/WebApp.gs   -> 5173c3c7a9d58e091fa8a49ee97522c9
A filename is not provenance (D188). Assert the md5.  No live system is touched.

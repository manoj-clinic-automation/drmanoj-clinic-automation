# S198_G1 — the Gist filled (A5; the buildable slice of D241)

Two files:
- `portal_gist.py` `55e111d71e95032c21234ae540a49431` -> `ef3ad196a00c2df44a7770553237a0e6` (the cron builder; console.db read-only)
- `portal.py` `43ec35b1e87075ef942946e918db82f9` -> `ab019dda3ac68e566de017c5ae536a6b` (three new cards)

NEW gist blocks, all 7-day, all fail-loud (null + note, never zero):
- **Judgment funnel**: answered -> transcribed -> judged, unjudged count + top reason
  (closes metric 5, "deferred" since S139 — the verdict store has lived in console.db since S168)
- **Staff vs AI**: verdict rows, filed%, Mismatch count (the Console's own semantics, D172)
- **New leads**: incoming unknown phones — new / answered / never reached (Console lead semantics)

DEFERRED WITH REASONS (in the builder's header, recorded not dropped): conversion (the D246
Followup->Callback seam — the "came" half lives on the clinic PC), reputation (no GMB data
feed exists), ROI (no honest denominator without conversion).

Proof: builder selftest 21 -> 27 (+6, fixture-exact incl. the error-row exclusion and the
known-patient lead exclusion); portal gate 6/6 (cards render, null blocks say "unavailable",
ZERO tile changes); the installer re-runs both on the box AND does a LIVE --dry-run against
the real console.db before anything counts as green.

    cd /root/deploy/repo && git pull
    bash deploy_kits/S198_G1/INSTALL_S198_G1.sh

#!/bin/bash
# =============================================================================
#  install_p1a.sh · kit S182_P1a — PORTAL TILES for the clinic finance module.
#
#  Adds two tiles (Daily Collection -> /finance/clinic/entry, Clinic ->
#  /finance/clinic/review), grants them to the real unit_role rosters, retires
#  the legacy Google-Sheet "Daily Collections" tile (owner ruling, S182), and
#  hydrates both labels from clinic.tile.* via /finance/clinic/api/tile-meta.
#
#  Shape follows D317, with ONE deliberate improvement over the finance kits:
#  the smoke gate runs BEFORE anything live is touched, because a portal change
#  needs no migration and no live DB. So the ordering here is
#     preflight -> SUMS -> KIT_ID currency -> LIVE-FILE CURRENCY -> smoke gate
#     -> backup -> swap -> restart -> health -> green, else HONEST red.
#
#  THE LIVE-FILE CURRENCY GATE (new, S182 / F-97):
#  This kit was built against the live portal.py at md5 34f038a765...  At S182
#  it was discovered that /root/portal/portal.py had drifted from BOTH git and
#  its KB Register pin for two sessions — it carried the S179 finance tiles that
#  existed nowhere else. A full-file replacement built from the stale copy would
#  have silently deleted them. So this installer refuses to run unless the live
#  file is exactly the one the candidate was derived from. A filename is not
#  provenance (D188); neither is a Register pin.
# =============================================================================
set -u

KIT_NAME="S182_P1a"
LIVE=/root/portal
SVC=clinic-portal
PORT=8090
# The portal is served by gunicorn from the wa venv, so the gate must run under
# the SAME interpreter that will import the file in production (F-53 discipline).
PY=/root/wa/venv/bin/python3
EXPECT_LIVE_MD5="34f038a7652024d49479569ed53bbfb9"

for c in systemctl md5sum awk curl cp mv; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing before touching anything"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing before touching anything"; exit 1; }
[ -f "$LIVE/portal.py" ] || { echo "!! preflight: $LIVE/portal.py not found — refusing"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

LIVE_NOW="$(md5sum "$LIVE/portal.py" | awk '{print $1}')"

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum portal.py.new | awk '{print $1}')" ] \
&& { [ "$LIVE_NOW" = "$EXPECT_LIVE_MD5" ] || {
       echo ""
       echo "!! REFUSING — the live portal.py is NOT the file this kit was built against."
       echo "     live now : $LIVE_NOW"
       echo "     expected : $EXPECT_LIVE_MD5"
       echo "   Nothing has been touched. Installing would overwrite whatever changed"
       echo "   since this kit was built. Send the current /root/portal/portal.py back"
       echo "   and the kit will be rebuilt on top of it."
       exit 1; }; } \
&& echo "-- live-file currency OK ($LIVE_NOW)" \
&& echo "-- running the smoke gate BEFORE touching anything live..." \
&& "$PY" smoke_portal_S182.py portal.py.new "$LIVE/portal.py" \
&& "$PY" -m py_compile portal.py.new \
&& echo "-- gate green; installing" \
&& cp portal.py.new "$LIVE/portal.py.new" \
&& cd "$LIVE" \
&& cp portal.py portal.py.bak_S182P1 \
&& touch .S182P1_touched \
&& mv portal.py.new portal.py \
&& systemctl restart "$SVC" \
&& sleep 3 \
&& curl -sf "http://127.0.0.1:$PORT/portal/health" >/dev/null \
&& rm -f .S182P1_touched \
&& echo "" \
&& echo "$KIT_NAME INSTALLED — smoke green, service restarted, health OK" \
&& echo "   backup: $LIVE/portal.py.bak_S182P1" \
&& echo "   tiles : Daily Collection (shavez/alisha/shivani) · Clinic (manoj/bhawna/shavez)" \
&& echo "   retired: the legacy Google-Sheet 'Daily Collections' tile" \
|| { echo ""; \
     echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S182P1_touched" ]; then \
        echo "   live files WERE touched — restoring portal.py from the S182P1 backup:"; \
        cp -f "$LIVE/portal.py.bak_S182P1" "$LIVE/portal.py" && echo "   portal.py restored"; \
        systemctl restart "$SVC" && echo "   $SVC restarted on the restored file"; \
        sleep 2; \
        if curl -sf "http://127.0.0.1:$PORT/portal/health" >/dev/null; then \
          echo "   health OK after restore — the portal is back as it was."; \
        else \
          echo "   !! health STILL failing after restore — check: journalctl -u $SVC -n 40"; \
        fi; \
        rm -f "$LIVE/.S182P1_touched"; \
     else \
        echo "   the gate fired BEFORE anything live was touched — nothing to restore."; \
        echo "   the portal is running exactly as it was."; \
     fi; \
     exit 1; }

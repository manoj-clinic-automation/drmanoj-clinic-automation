#!/bin/bash
# rehearse_s543.sh -- kit S543_ORDER_SHEET_MARG: the installer on a MADE-UP root (/tmp/s543rh), never the live one.
#   A copy of /root/finance (code + a backup-API copy of finance.db), a made-up clone (its DUTY_MAP v12 and .md), a stand-in service
#   (the real finance_app from the made-up root on 127.0.0.1:18543, run by a stand-in systemctl), a stand-in git whose 'pull' brings the
#   kit's v13 map. Three runs: (1) red after placing (a stand-in journal with a Traceback) -> every file back byte-identically, the new file
#   removed; (2) green -> DONE; (3) again -> ALREADY INSTALLED. The live box is only read (the databases by the backup API).
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
R=/tmp/s543rh; rm -rf "$R"; mkdir -p "$R/finance/spine" "$R/finance/finance_ui" "$R/repo/claude_code_briefs" "$R/repo/deploy_kits" "$R/bin"
cp -p /root/finance/*.py "$R/finance/"; cp -p /root/finance/*.html /root/finance/*.json /root/finance/*.sql "$R/finance/" 2>/dev/null
cp -rp /root/finance/finance_ui/. "$R/finance/finance_ui/"; cp -p /root/finance/spine/*.py /root/finance/spine/*.json "$R/finance/spine/" 2>/dev/null
/usr/bin/python3 -c "import sqlite3; s=sqlite3.connect('file:/root/finance/finance.db?mode=ro',uri=True,timeout=60); d=sqlite3.connect('$R/finance/finance.db'); s.backup(d); d.close(); s.close()"
cp -p /root/deploy/repo/claude_code_briefs/DUTY_MAP.json /root/deploy/repo/claude_code_briefs/DUTY_MAP.md "$R/repo/claude_code_briefs/"
cat > "$R/bin/systemctl" <<EOF
#!/bin/bash
PIDF=$R/standin.pid
case "\$1" in
  restart) if [ -f \$PIDF ]; then P=\$(cat \$PIDF); kill -9 \$P 2>/dev/null; for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do kill -0 \$P 2>/dev/null || break; sleep 0.5; done; fi; pkill -9 -f "18543, fa.app" 2>/dev/null; sleep 2
           ( cd $R/finance && FINANCE_DB=$R/finance/finance.db PYTHONDONTWRITEBYTECODE=1 nohup /usr/bin/python3 -B -c "import sys; sys.path.insert(0, '$R/finance'); import finance_app as fa; from werkzeug.serving import run_simple; run_simple('127.0.0.1', 18543, fa.app, use_reloader=False)" >$R/standin.log 2>&1 & echo \$! > \$PIDF ); exit 0;;
  is-active) [ -f \$PIDF ] && kill -0 \$(cat \$PIDF) 2>/dev/null && { [ "\${2:-}" = "--quiet" ] || echo active; exit 0; }; [ "\${2:-}" = "--quiet" ] || echo inactive; exit 3;;
esac
exit 0
EOF
cat > "$R/bin/git" <<EOF
#!/bin/bash
# stand-in: 'git -C <repo> pull --ff-only' brings the kit's v13 map and the kit folder, as the real pull would
[ "\$3" = "pull" ] || exit 1
/usr/bin/python3 -B "$KDIR/make_s543.py" --fin /root/finance --briefs /root/deploy/repo/claude_code_briefs --out $R/pulled --only map >/dev/null || exit 1
cp -p $R/pulled/DUTY_MAP.json $R/repo/claude_code_briefs/DUTY_MAP.json; rm -rf $R/repo/deploy_kits/S543_ORDER_SHEET_MARG; cp -rp "$KDIR" $R/repo/deploy_kits/S543_ORDER_SHEET_MARG
echo "Fast-forward (stand-in)"
EOF
printf '#!/bin/bash\necho "Traceback (most recent call last): (stand-in red)"\n' > "$R/bin/journal_red"
printf '#!/bin/bash\nexit 0\n' > "$R/bin/journal_ok"
chmod +x "$R/bin/"*
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ENVS=(FIN="$R/finance" REPO="$R/repo" LOCK="$R/lock" FIN_PORT=18543 SYSTEMCTL="$R/bin/systemctl" GIT="$R/bin/git" TMPW="$R")
"$R/bin/systemctl" restart x; sleep 4
B0="$(for f in order_sheet.py porders_s454.py order_sheet_pdf.py; do m5 "$R/finance/$f"; done)"
echo "== run 1: red after placing (a stand-in journal with a Traceback)"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_red" bash "$KDIR/install_S543_ORDER_SHEET_MARG.sh" > "$R/run1.out" 2>&1; R1=$?
grep -E "^\[|^!!|^   /tmp|^   after|^   the clone|^   the database" "$R/run1.out" | grep -v "^\[3/12\]" | tail -14
B1="$(for f in order_sheet.py porders_s454.py order_sheet_pdf.py; do m5 "$R/finance/$f"; done)"
[ "$R1" = 1 ] && [ "$B0" = "$B1" ] && [ ! -e "$R/finance/marg_order_pdf.py" ] && echo "REHEARSAL 1 OK: red -> the three files byte-identical to before, marg_order_pdf.py removed (exit $R1)" || echo "REHEARSAL 1 FAILED (exit $R1)"
cp -p /root/deploy/repo/claude_code_briefs/DUTY_MAP.json "$R/repo/claude_code_briefs/DUTY_MAP.json"
echo "== run 2: green"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S543_ORDER_SHEET_MARG.sh" > "$R/run2.out" 2>&1; R2=$?
grep -E "^\[|^!!|^ *  /finance|^PAGE|DONE" "$R/run2.out" | grep -v "^\[3/12\]" | tail -14
[ "$R2" = 0 ] && grep -q "DONE" "$R/run2.out" && echo "REHEARSAL 2 OK: green install on the made-up root" || echo "REHEARSAL 2 FAILED (exit $R2)"
echo "== run 3: again"
env "${ENVS[@]}" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S543_ORDER_SHEET_MARG.sh" > "$R/run3.out" 2>&1; R3=$?
tail -2 "$R/run3.out"
[ "$R3" = 0 ] && grep -q "ALREADY INSTALLED" "$R/run3.out" && echo "REHEARSAL 3 OK: ALREADY INSTALLED" || echo "REHEARSAL 3 FAILED (exit $R3)"
pkill -9 -f "18543, fa.app" 2>/dev/null
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null

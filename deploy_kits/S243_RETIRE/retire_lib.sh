#!/bin/bash
# S243_RETIRE — shared candidate logic. Sourced by retire_dryrun.sh and retire_move.sh.
# Everything here only READS. ROOT is overridable for offline tests.
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"

# --- names that are NEVER candidates (rulings, live, secrets, data) ---
never_touch() {
  case "$1" in
    .acme.sh|crontab.bak_S237|_quarantine_S232_*|finance.db|*.log|*.json|*.env|__pycache__|backups|deploy|wa|portal|staff_register|staff_ledger|staff_ledger_reconcile|state_backup|marg_ingest|assetapp|gutlog|fitlog|rxguard|gutlog_backup_v2|shared|archive|clinic_salary|finance_ui|exports|incoming|scans|vendor|_import|finance_scans|upi_statements|yesbank_statements|logs|backfill_in|patient_fp.env|clinic-finance.service) return 0;;
  esac
  return 1
}

# --- category tests on a BASENAME ---
cat_of() {
  local n="$1"
  never_touch "$n" && { echo ""; return; }
  case "$n" in
    _backup_S*)                                  echo "B_backupdir";;
    *.bak|*.bak.*|*.bak_*|*.bak-*|*.BAK_*|*.BACKUP_*|*_BACKUP_*|*.BACKUP|*.pre-dedup-*|vhosts.BACKUP_S179) echo "A_bakcopy";;
    patch_*.py|selftest_*.py|walk_*.py|WALK_*.py|seed_*.py) echo "C_buildhelper";;
    S180_U*|S195_*)                              echo "D_installresidue";;
    attlistener_phase*.py)                       echo "C_buildhelper";;
    install_finance_S179.sh|post_install_finance.sh|update_finance_*.sh|add_finance_*.sh|mask_darpan_tiles.sh|finance_gitignore_additions.txt|B1_reconciliation.md|finance_migration_S182_*.sql|finance_browse.md5|finance_epoch.md5|finance_parked.md5|finance_scanner.md5|finance_sso.md5|finance_ui.md5|finance_upi.md5|finance.md5) echo "D_installresidue";;
    add_bhawna_desk_s223.py|backfill_lookup_s218.py|close_amir_joiner_s222.py|correct_days_s218.py|crosstab.py|diagnose_identity_text.py|explore_db.py|find_the_june_case.py|fix_f185_fixtures.py|json_keys.py|legacy_sweep.py|rejoin_returns_s220.py|repair_upi_txn.py|research_once.py|returns_keyprobe.py|returns_probe.py|returns_recovery.py|tally_recent.py|validate_visit_rung.py|why_unmatched.py|s218_backfill_effects.csv|patch_switcher.py|watchdog_live_copy.py) echo "E_oneoff";;
    marg_14_15_aug.xls|medical_adjustments.csv|medical_daily_ledger.csv|medical_exceptions.csv|medical_legacy.csv|audit_finance_backup.db) echo "F_legacydata";;
    flow_2026-*.html|salary_inputs_*|scenario_2026-*|review_2026-*.csv|deductions_extras_*.csv|selftest_grid.html) echo "";;  # S243 review: salary inputs/outputs stay in place
    *) echo "";;
  esac
}

# --- reference check: is the basename mentioned by anything live? ---
# Live set = every .py/.sh/.service/.html/.conf under ROOT (excluding candidates' own categories and retired dirs) + crontab + systemd units.
ref_hits() {
  local n="$1" hits
  hits=$( { grep -rlsF --include='*.py' --include='*.sh' --include='*.service' --include='*.timer' --include='*.html' --include='*.conf' --exclude='*.bak*' --exclude='*.BAK*' --exclude='*.BACKUP*' --exclude='patch_*' --exclude='selftest_*' --exclude='walk_*' --exclude='WALK_*' --exclude='seed_*' --exclude-dir='_backup_S*' --exclude-dir='_retired*' --exclude-dir='_quarantine*' --exclude-dir='deploy' --exclude-dir='backups' --exclude-dir='__pycache__' --exclude-dir='S180_U*' -- "$n" "$ROOT" 2>/dev/null; crontab -l 2>/dev/null | grep -F -- "$n" | sed 's/^/crontab: /'; ls /etc/systemd/system/*.service /etc/systemd/system/*.timer 2>/dev/null | xargs grep -lsF -- "$n" 2>/dev/null; } | grep -v -F -- "/$n" | head -3 | tr '\n' ' ')
  # drop hits that are themselves candidates (a residue script mentioning another residue file holds nothing)
  local out="" h
  for h in $hits; do
    case "$h" in crontab:) out="$out $h";; *) [ -z "$(cat_of "$(basename "$h")")" ] && out="$out $h";; esac
  done
  echo "${out# }"
}

# --- enumerate candidates: prints "cat<TAB>relpath<TAB>size<TAB>refs" ---
enumerate() {
  local d rel n c sz refs
  for d in "$ROOT" "$FIN"; do
    [ -d "$d" ] || continue
    while IFS= read -r -d '' p; do
      n=$(basename "$p"); c=$(cat_of "$n"); [ -z "$c" ] && continue
      rel="${p#$ROOT/}"
      sz=$(du -sk "$p" 2>/dev/null | cut -f1)
      refs=$(ref_hits "$n")
      printf '%s\t%s\t%s\t%s\n' "$c" "$rel" "$sz" "$refs"
    done < <(find "$d" -mindepth 1 -maxdepth 1 -print0 | sort -z)
  done
}

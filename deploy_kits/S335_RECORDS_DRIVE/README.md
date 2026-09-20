# S335_RECORDS_DRIVE

Found live at 08:4x IST, 20-Sep: the first blood report opened from the records page answered *"Drive not reachable (ModuleNotFoundError)"*. The finance web app runs under the system python, which has no Google libraries; the box's venv has them. Every Drive read of the records page now goes through `records_drive.py`, run with the venv python (read-only). The installer then proves it on the real Drive: it lists the X-ray test folder and reads one filed report. Walk: 96 checks.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S335_RECORDS_DRIVE/install_S335_RECORDS_DRIVE.sh
```

Pins: `/root/finance/records.py` `f284fd15…` → `dcb49d8cc425b52b2f79d940c2baf7fe` · `/root/finance/records_drive.py` NEW → `83a7171fb2e2bd8022613383641e4821` · `finance_app.py` `3a871f53…` unchanged.

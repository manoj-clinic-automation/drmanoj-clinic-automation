# S904_TRACKER_VENV311 (the parent, S493, 20-Nov-2026) -- see the installer header.

Install (server, one line; builds a Python 3.11 venv, 5-25 min):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s904kit && cp -rp /root/deploy/repo/deploy_kits/S904_TRACKER_VENV311 /tmp/s904kit && bash /tmp/s904kit/install_S904_TRACKER_VENV311.sh
```
Undo: `bash /tmp/s904kit/install_S904_TRACKER_VENV311.sh --undo`.

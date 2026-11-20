# S908_STABLE_TIES (the parent, S493, 20-Nov-2026) -- see the installer header. The PC side: processor.py f1c02736 -> 6929fc15 by the same patcher (the assistant, connected folder); replay1_hash.py in the VM prints the same content hashes.

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s908kit && cp -rp /root/deploy/repo/deploy_kits/S908_STABLE_TIES /tmp/s908kit && bash /tmp/s908kit/install_S908_STABLE_TIES.sh
```
Undo: `bash /tmp/s908kit/install_S908_STABLE_TIES.sh --undo`.

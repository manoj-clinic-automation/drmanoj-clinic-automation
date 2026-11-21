# S918_FREE_XRAY_TAP — a free X-ray closed in one tap

*The parent · S498 · 21-Nov-2026.*

**What happened.** Three September X-ray photos of people registered nowhere (one of them four photos) had no slip, no clinic ID and no Docterz line: the free X-rays. The card offered only "Docterz mein nahi", which moved them to the owner's *Not in Docterz* tile, where a second tap ("Free X-ray") was still needed. They looked impossible to remove.

| file | what changes |
|---|---|
| `finance/check_screens.py` 5d00b2e8 → TO | The card's **"Docterz mein nahi"** button becomes **"Free X-ray"** (Shavez's card; the owner's waiting card: "Free X-ray (not registered)"). One tap writes both answers at once — not in Docterz, explained *free X-ray* — for every photo of that person, so it leaves Check karein, the counts and the *Not in Docterz* open list. His *Not in Docterz* tile still shows it as explained (who, when); it can still be given an ID later. The old answer still works. |

## Proof
- `walk_s918.py` on a copy of the 21-Nov data: **14/14** (a 4-photo group closed together; gone from the waiting list and the open list; kept as explained; a second tap harmless; from the owner's tile too; the words on both pages). Live file **3/14** (red).
- `walk_s854` 31/31 on the new file; `walk_s836` the same on old and new.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s918kit && cp -rp /root/deploy/repo/deploy_kits/S918_FREE_XRAY_TAP /tmp/s918kit && bash /tmp/s918kit/install_S918_FREE_XRAY_TAP.sh
```
`DRY=1` before `bash`: every gate and walk, nothing changed. `--undo`: the file back.

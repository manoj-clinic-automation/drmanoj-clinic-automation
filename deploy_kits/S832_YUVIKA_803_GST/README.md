# S832_YUVIKA_803_GST — Yuvika bill 803's GST, as one job on Amir's card (Sanjeevni, session 459)

Yuvika Surgicals issued two papers under one number, YS/0803/2026-27 of 06-11-2026: scan **B-0262** (XL 2 + XXL 1, ₹1,380) and scan **B-0272** (XL 1 + XXL 2, ₹1,410, the receiver's signature and the firm's stamp — the revised bill). Marg holds XL 1 + XXL 2 (as B-0272) but its XXL line carries no GST: Marg ₹1,364, the paper ₹1,410 (5% on both lines). The owner's word (18:05 IST): correct Marg.

- One tap job on Amir's card (amir_job, kind tap, key `fix:S832:YUVIKA 803`): put 5% GST on the XXL line; the bill should read ₹1,410.
- B-0272 is restored as not a duplicate by the owner's Restore in the Scan App.

Data only; no file changes; no restart. The undo is one line (the installer prints it).

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S832_YUVIKA_803_GST/install_S832_YUVIKA_803_GST.sh

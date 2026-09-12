# S240_MEDICAL_PUSH — the medical PC sends each export to the server by itself

**Delivered through Google Drive, not by hand.** Copy these into
`Clinic Data Archive\ToMedical\_kit` and the medical agent installs them by itself, within
five minutes, md5- and compile-gated. Nothing is run on that machine by a person.

| file | md5 | lands at |
|---|---|---|
| `marg_push.py` | 630fc5efeac89513d5b0d057df9e0639 | `D:\SendToClinic\marg_push.py` |
| `marg_watch.py` | 581ff3a7bc9493602172ef9765af2f2f | `D:\SendToClinic\marg_watch.py` (replaces aa55cdb5; the agent restarts the watcher) |
| `KIT_MANIFEST.txt` | — | stays in `_kit`; it is what lets a NEW file be delivered at all |

**Order:** `marg_push.py` and `KIT_MANIFEST.txt` first — they change nothing on their own.
`marg_watch.py` second, and only on the owner's word: it is the live capture program.

**To undo:** put `marg_watch.py` aa55cdb5 back in `_kit`. The agent reinstalls it and restarts
the watcher; the pusher is then never started and the file it left behind does nothing.

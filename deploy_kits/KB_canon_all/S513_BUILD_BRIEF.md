# S513 BUILD BRIEF — for Dr. Manoj (24-Nov-2026, evening)

**What changed today (session 513):**

1. **A patient's mobile number was hiding in test data — now taken out.** Four of the call-audit programs on the server carried sample phone numbers for their self-checks. One of them was a real patient's mobile (it appears in your Docterz exports; no name was with it). It had been in the live programs and in the public code store since the summer. All four programs now use plainly made-up numbers; their self-checks pass exactly as before. Live since 16:09 (your publish and one server line).
   - Still to weigh: older copies of that number remain in the code store's *history*. Removing history is disruptive, so the next review decides whether and how.
2. **The System Board's notes were trimmed** from 253 KB to 3 KB, so new lines won't be refused. The full old text is kept, checked byte for byte, on your PC.
3. **MyOperator's webhooks checked once in your panel:** only one webhook points to the call hook, so it is not a double subscription. The leftover second key will be retired on the server.
4. **Your word (17:19):** the new Call Console screens will use the **same simple-English words as the Callback Tracker**, which the staff already know.

**What waits on you:** one double-click to publish this session's records —

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

Nothing follows it on the server. Standing reminder: the packs page — the 25 card shops, and the card and ICICI passwords.

**Next session (514, Opus):** first, read tomorrow's checks. Then build the staff Call Console screens in the tracker's words; you'll see one screen before it is built.

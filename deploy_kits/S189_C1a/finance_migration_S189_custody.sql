-- =============================================================================
--  finance_migration_S189_custody.sql  ·  Session 189  ·  F-137
--
--  WHAT THIS RECORDS
--  The physical cash position established by COUNT on 17 Aug 2026 (S186), which
--  until now has existed only as a sentence inside cash_count.explanation:
--
--      "Darpan drawer 0 (cleared) + owner 18,963 + Dr Bhawna 1,56,235"
--
--  S186 created cash_custody_event -- with from_party, to_party and amount_p --
--  in the same session, and then wrote the custody facts into a text column of a
--  different table. No query can reach prose. That is why Darpan's "Where the
--  cash is" card reads zero against roughly 1.75 lakh, and it is the whole of
--  what this migration fixes.
--
--  WHAT IT DELIBERATELY DOES NOT DO -- read this before anything else
--  It does NOT write cash_movement. v_day_cash computes
--      cash_out_p = SUM(cash_movement WHERE direction='out')
--  so EVERY movement row is subtracted from cash in hand, whatever the party.
--  Booking these handovers there would take cash in hand from Rs 2,05,198 to
--  about Rs 30,000 and destroy the agreement the 17 Aug count established.
--  OWNER RULING, S189: cash held by Dr Manoj or Dr Bhawna IS cash in hand,
--  merely located elsewhere. Custody is LOCATION; movement is QUANTITY.
--  No view in the cash ledger reads cash_custody_event, so this migration
--  cannot move a rupee -- and gate_s189.py proves that rather than asserting it.
--
--  THE ARITHMETIC, and where each figure comes from
--    Dr Manoj      18,963   S186 §4, the drawer clearing, itemised to the rupee
--    Dr Bhawna    1,56,235  = 7,309 + 3,926 + 1,45,000
--                    7,309  S186 §4, Vinay -> Dr Bhawna, 6 Aug  (proven by the
--                           drawer arithmetic landing exactly on 48,963)
--                    3,926  S186 §4, Vinay -> Dr Bhawna, 15 Aug (same proof)
--                1,45,000  the balance of her counted position. Its individual
--                           journeys are NOT itemised anywhere in the record, so
--                           it is entered as ONE row that says so. The route is
--                           taken from the documented custody model (S186 §2:
--                           the counter person hands cash direct to Dr Bhawna,
--                           bypassing the drawer), NOT from a per-transaction
--                           record -- and the note on the row states that.
--                           That it comes to a round 1,45,000 is a corroboration,
--                           not the reason: 1,56,235 - 7,309 - 3,926 = 1,45,000.
--    TOTAL        1,75,198  equal, to the paise, to cash_count.counted_p for
--                           2026-08-17. The gate refuses if it is not.
--
--  Darpan's drawer is 0 and therefore has NO row. An empty drawer is the absence
--  of custody, and absence is recorded by writing nothing (F-107's lesson taken
--  the other way: we do not invent a row to say "nothing here").
--
--  ADDITIVE. Four INSERTs into one table, plus one marker. Nothing is read,
--  altered, rebuilt or dropped. Rollback block at the foot; it is lossless.
-- =============================================================================

INSERT INTO cash_custody_event
    (unit, event_date, from_party, to_party, amount_p, counter_person_id,
     day_entry_id, month_end_kind, note, entered_by, entered_at)
VALUES
 ('medical','2026-08-06','counter','dr_bhawna',   730900,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Vinay Saxena'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-06'),
  NULL,
  'S189 (F-137). Vinay handed cash DIRECT to Dr Bhawna, bypassing the drawer. '
  || 'Itemised in S186 section 4 and proven by the drawer clearing landing '
  || 'exactly on Rs 48,963. Location only -- this money never left the books.',
  'manoj','2026-08-18'),

 ('medical','2026-08-15','counter','dr_bhawna',   392600,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Vinay Saxena'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-15'),
  NULL,
  'S189 (F-137). Vinay handed cash DIRECT to Dr Bhawna, bypassing the drawer. '
  || 'Itemised in S186 section 4, same proof. Location only.',
  'manoj','2026-08-18'),

 ('medical','2026-08-17','counter','dr_bhawna', 14500000,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Vinay Saxena'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-17'),
  NULL,
  'S189 (F-137). BALANCING ENTRY to the physical count of 17 Aug 2026. '
  || 'Rs 1,56,235 counted with Dr Bhawna, less the two itemised Vinay '
  || 'handovers (7,309 + 3,926) = Rs 1,45,000. The individual journeys making '
  || 'up this remainder are NOT recorded anywhere; the route shown is the '
  || 'documented custody model (S186 section 2), not a per-transaction record. '
  || 'This row is evidence of POSITION, established by counting notes, and it '
  || 'is deliberately one row rather than an invented history. D323.',
  'manoj','2026-08-18'),

 ('medical','2026-08-17','drawer','dr_manoj',   1896300,
  (SELECT id FROM counter_person WHERE unit='medical' AND name='Darpan'),
  (SELECT id FROM day_entry WHERE unit='medical' AND business_date='2026-08-17'),
  NULL,
  'S189 (F-137). The drawer clearing of 17 Aug 2026, itemised to the rupee in '
  || 'S186 section 4: copy balance 60,198 less the two Vinay handovers = '
  || 'Rs 48,963 physically in the drawer, of which 10,000 settled July salary, '
  || '20,000 was advanced against August salary, and Rs 18,963 was handed to '
  || 'the owner. Drawer left EMPTY, proved to the rupee. Location only.',
  'manoj','2026-08-18');

INSERT OR REPLACE INTO setting (key,value,note) VALUES
 ('migration.S189_custody','applied 2026-08-18',
  'S189 F-137: the 17 Aug 2026 counted custody position written into '
  || 'cash_custody_event, where it had existed only as prose in '
  || 'cash_count.explanation. Dr Manoj 18,963 + Dr Bhawna 1,56,235 = 1,75,198, '
  || 'equal to cash_count.counted_p for that date. Ledger deliberately '
  || 'untouched: custody is location, not quantity.');

-- =============================================================================
--  ROLLBACK -- paste and run only if S189_C1a has to be undone. Lossless:
--  it removes exactly the four rows this file inserted and the marker, and
--  touches no money, because this migration never touched any.
--
--  DELETE FROM cash_custody_event
--   WHERE unit='medical' AND entered_by='manoj' AND entered_at='2026-08-18'
--     AND note LIKE 'S189 (F-137).%';
--  DELETE FROM setting WHERE key='migration.S189_custody';
-- =============================================================================

# Raw dataset guide

## Files
- `competitors.csv`: provider directory and internal IDs.
- `programs.csv`: one row per programme. Blank `fee_amount_inr` means no numeric INR fee was captured from the reviewed page.
- `source_register.csv`: provenance and review notes for each programme row.

## Important fields
- `fee_amount_inr`: numeric fee only; blank if not disclosed/captured.
- `fee_tax_status`: whether GST is included, extra, unspecified, or price varies.
- `fee_display_text`: original human-readable fee statement.
- `duration_months`: numeric duration where the source states months; blank for week-based or unreported durations.
- `duration_display`: source-style duration statement.
- `verification_status`: means the public programme page was reviewed, not that every claim has been independently audited.
- `source_checked_date`: date the page was reviewed for this starter snapshot.
- `research_notes`: caveats and details requiring follow-up.

## Use carefully
Do not compare blank fees as zero. Do not infer a numeric monthly duration from week-based programmes unless a documented conversion rule is applied. Revisit pages before publishing or making decisions; programme terms change.

---
name: affiliate-review
description: Review compact affiliate offer batches produced by this repository without accessing WhatsApp credentials or raw webhook history.
---

# Affiliate Review

Work from the repository root. Never read `.env`, browser profiles, Evolution
credentials, QR codes, or the raw SQLite database.

1. Run `python -m scripts.affiliate_list_pending`.
2. If the output is exactly `EMPTY`, stop without further analysis.
3. Review only the returned compact JSON. Never invent prices, coupons, product
   names, links, or marketplace data.
4. Produce a JSON array with `id`, `decision`, `reason`, and `final_text`.
   Allowed decisions are `approve`, `reject`, and `needs_human`.
5. Prefer `needs_human` whenever product identity, price, coupon, affiliate
   ownership, or link destination is uncertain.
6. Save the JSON in a temporary file and run
   `python -m scripts.affiliate_apply_decisions --file <path>`.
7. Do not call the publication script. Python publishes in a separate,
   controlled step.

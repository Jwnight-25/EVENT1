# Domain layer

Place instrument/contract rules, continuous-series policy, feature definitions, and forecast validation rules here. Keep these independent from FastAPI, storage vendors, and external data providers.

Key rules from the requirements:

- Preserve raw single-contract observations; generate continuous series separately and version its stitching/adjustment method.
- Align every feature to its actual publication/availability time to prevent look-ahead leakage.
- Do not expose probability, interval, or performance fields unless produced by a validated model/statistical method.

# Data connectors

Implement one adapter per source. Each adapter should return normalized observations while preserving raw values and provenance. Keep source-specific parsing, rate limits, retry behavior, publication timestamps, and licensing notes inside the adapter; do not let an adapter write over the raw archive.

No live source is configured yet. An unavailable source should remain unavailable in the API instead of being replaced by invented market values.

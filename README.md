# Innovist Intelligence Studio

Python / Streamlit research dashboard. **Partial research delivery, not a completed consumer-insights study.**

## Run
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
The delivered private research bundle includes the database and cleaned snapshots. No API key is needed to explore it. The app reads versioned JSON exports; SQLite is the relational research mirror. `python sync_database.py` refreshes SQLite and CSV exports after approved changes.

## Security
No GitHub remote or public deployment was created. Source code is locally version-controlled. GitHub integration is not offered in this session. Data, reports, uploads and secrets are gitignored. **Never publish the full research bundle as a public repository.** Review data rights before sharing. The running Arena preview is a session development preview, not a hardened deployment: no application login or role-based controls are implemented. For production, restore CORS/origin restrictions, add authentication, encrypt backups and use a private deployment.

## What is delivered
- Ten working navigation sections, global partial/token search across product names, brand, category, ingredients, description, SKU, variant, communication records and ASIN candidate records.
- 690 original source rows preserved, audit denominators explicit; URL normalisation keeps variants and node parameters.
- 35 direct official product profiles / 35 catalog variants, 3 brands; ingredient text retrieved for 35 and directions for 34.
- Seven investigated Amazon ASINs (four direct listings + three store-context leads). Six exposed rating/count labels; no individual review records retrieved. Review endpoints returned 404. Store-context ASINs are **not** complete store inventories.
- Additional product-link discovery queue. These leads are **not** counted as researched profiles.
- Source-backed product descriptions, formulation sections, usage, suitability and testing claims where extracted; field-level provenance; separate communication hypotheses and research checklist.
- Portfolio comparison and an external competitor evidence framework. No unsupported competitor table.
- Downloadable CSV/JSON/Markdown reports; SQLite mirror; raw page archive.

## Reproducible pipeline
Original CSVs are expected at `../uploads/` with the supplied filenames. The complete originals are delivered separately from the Git-ready source. Cached raw responses are in `data/raw_sources.zip` and selected bootstrap files in `data/raw/`.

Before a full extraction replay, unpack the cache:
```sh
python -m zipfile -e data/raw_sources.zip data/raw
python pipeline.py
python enrich.py
python recover.py
python enrich.py
python finalize_data.py
python sync_database.py
python -m pytest -q
```
The scripts retain source snapshots. `recover.py` uses a sequential delay and stops on HTTP 429. Initial ingestion uses a small worker pool; for sustained research switch it to one worker and enforce Retry-After. No access control bypass, proxy rotation or CAPTCHA solving exists. A single launch never triggers extraction. **A replay may change findings as websites change.** Backup the delivered snapshot first.

`pipeline.py` extracts supplied direct pages. `enrich.py` resolves catalog metadata. `finalize_data.py` pulls structured sections from cached official pages and creates the link discovery backlog. The delivered data includes a reviewed recovery pass. Additional catalog products outside direct CSV product URLs remain discovery leads, not finished profiles.

## Permitted Amazon review imports
Obtain a contractually authorised provider/export. No provider credentials or subscription are present. Do not use search snippets as reviews.
```sh
python -m src.import_reviews authorised_export.csv
python sync_database.py
```
Required columns: `review_id,asin,text,rating,date,url`. Optional: title, verified_purchase, variant, helpful_votes. Unknown ASINs are rejected. The importer deduplicates by review ID and leaves product mapping unconfirmed. It is an ingestion scaffold, not a turnkey Amazon API connector. Review attribution, provider licence, sampling frame and variant mapping must be manually approved before analyses are published. Current UI explicitly withholds review-backed conclusions; update coverage and analysis after approval. Theme analysis uses transparent keyword rules, not validated NLP. Review rating valence is not linguistic sentiment. No fake review fixtures are mixed with live data.

## Evidence policy
Marketing descriptions and clinical percentages are brand claims until their reports are assessed. Ingredient presence does not establish clinical efficacy. Emotional interpretations are hypotheses. A failed extraction is not a negative consumer finding. “Not disclosed” denotes absence from structured retrieved fields; it must not be interpreted as a claim that the live brand page contains no such information. Original ingredient order is retained; no active concentration is inferred. Shipping weight is not product volume. Discount prices are dated catalog snapshots, not checkout guarantees.

## Known limitations / next work
- No collected Amazon review text, confirmed variant matches, review-backed pros/cons or claim-versus-experience verdicts. This blocks the user's full definition of done.
- 404 review responses; no authorised review provider configured. Additional store-discovered ASINs remain uninvestigated leads.
- Some category/brand sources still rate-limited. Direct-product recovery succeeded. Product-level catalog variants may not represent every size/bundle on the live website.
- Communication records are description-based analytical hypotheses. No complete campaign/visual semiotics audit, independent trial appraisal or validated consumer emotional research.
- External competitor data not researched; only framework and internal comparison provided.
- Rules are intentionally conservative. Some technical fields are retained in source text rather than separately parsed. No independent formulation verification.
- SQLite currently mirrors clean snapshots, with historical price/rating snapshot support. Incremental history is not an enterprise migration/versioning system.
- Test coverage includes audit reconciliation, deduplication, URL variants, review denominator arithmetic, provenance and all ten UI pages; not a full browser accessibility/security audit.

## Layout
`app.py`, `src/`, `tests/`, `pages/` (reserved; navigation is centrally rendered), `data/raw/`, `data/clean/`, `data/intelligence.sqlite`, `reports/`. No LLM runtime or hidden generated consumer quotations.

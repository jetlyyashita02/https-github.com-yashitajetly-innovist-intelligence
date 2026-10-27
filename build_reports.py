import json,collections
from pathlib import Path
from src.database import records
D=Path('data/clean');ps=records('products');ms=records('messages');ins=records('insights')
for m in ms:
 p=next(p for p in ps if p['id']==m['product_id']);m['original_message']=p['description'];m['source_url']=p['url'];m['proof']=p.get('testing_claims','No product-specific testing claim extracted')+' — brand-reported, underlying report not assessed'
profiles=[]
for b,slug,position,tone,emotion,weakness,question in [
 ('Bare Anatomy','rosemary-rice-water','Nature-plus-science haircare with outcomes and routine convenience','Outcome-led, ingredient-led and reassuring','Confidence and control over visible hair changes (hypothesis)','The 2.6X volume claim is explicitly attributed to an ingredient study; finished-product equivalence is not established by that attribution. Separate consumer-trial percentages also appear; methods are not assessed.','Does the finished formulation reproduce the ingredient-study endpoint, and do users distinguish growth, fullness and reduced breakage?'),
 ('Chemist at Play','underarm-roll-on','Active-led problem–solution body care','Accessible, playful usage language combined with numerical efficacy claims','Social comfort and confidence (hypothesis)','The 99.99% germ-elimination claim and 96%/98% consumer-study outcomes are distinct endpoints. The page comparison makes broad assertions about unidentified others.','What organisms, contact time and protocol support the germ claim, and what does the consumer expect after one use versus four weeks?'),
 ('SunScoop','5-niacinamide','Daily sun protection combined with sensory and skincare benefits','Protection-led, reassuring, routine-friendly','Reassurance outdoors without a greasy feel (hypothesis)','The description says SPF 50 while the title/comparison uses SPF 50+. The page claims COLIPA certification and consumer tan/hydration outcomes; underlying reports are not assessed.','Verify current packaging SPF designation, test method and report, use quantity, reapplication and consumer expectations around tanning.')]:
 p=next(p for p in ps if slug in p['url']);profiles.append(dict(brand=b,positioning_interpretation=position,tone_interpretation=tone,emotional_hypothesis=emotion,exact_example=p['description'],functional_promise=p.get('benefits',p['description']),source_url=p['url'],observed_evidence=p.get('testing_claims','Not extracted'),communication_concern=weakness,next_research=question,confidence='Moderate for page-level interpretation; not a complete brand/campaign audit',visual_conventions='Not audited; no visual claims made'))
 ins.append(dict(product_id=p['id'],product=p['name'],observation=weakness,evidence=p['url']+' | description, comparison and testing-claim sections',consumer_tension='Do numerical proof cues create expectations beyond the measured endpoint? (hypothesis)',interpretation='Different proof types need clear separation; no consumer misunderstanding has been demonstrated',implication='Review substantiation and copy comprehension before recommending stronger claims',opportunity='Clarify endpoint, population, time frame and evidence type',validation=question,confidence='High that wording appears; underlying efficacy and consumer response unverified',evidence_label='Official brand claim + analytical interpretation'))
for n,d in [('messages',ms),('brand_profiles',profiles),('insights',ins)]: (D/f'{n}.json').write_text(json.dumps(d,indent=2,ensure_ascii=False))
a=records('audit');src=records('inventory');leads=records('discovery_leads');ls=records('listings')
counts=collections.Counter(x['source_type'] for x in src if x['normalized_url']);unique={x['normalized_url']:x for x in src if x['normalized_url']};status=collections.Counter(x['extraction_status'] for x in unique.values())
text='''# Innovist Product Intelligence — Delivery & Coverage Report

**Snapshot: 26 October 2026 · Status: working dashboard, partial research completion.**

The full definition of done is **not yet met**: actual Amazon review text, confirmed marketplace-variant joins, researched external competitors and complete discovery-backlog coverage remain outstanding. No consumer quotations, pros/cons or sentiment statistics have been invented.

## 1. Complete CSV audit

Counts below exclude headers. Every original row is retained in the source inventory.

| File | Rows | Blank URLs | Non-URL rows | Unique original URLs | Duplicate occurrences | Unique normalised URLs | Normalised duplicate occurrences |
|---|---:|---:|---:|---:|---:|---:|---:|
'''
for x in a:text+='| '+x['file']+' | '+' | '.join(str(x[k]) for k in ['rows','blank_urls','non_url_rows','unique_original_urls','duplicate_url_occurrences','unique_normalized_urls','normalized_duplicate_occurrences'])+' |\n'
text+='''
### Columns and meanings
Website file: `#` = input link-inventory ordinal (not a product ID); `Url` = original link target; `Type` = link element type (text/image), not source-page type; `Anchor` = link text or image label, not a verified page title; `No-follow` = exported link attribute; `Status` = input crawler status placeholder; `Check result` = input validation placeholder, not a check performed in this project; `Count` = occurrence count in the original crawl, not product volume; `Backlinks` = input backlink metadata, mostly placeholders.

Amazon file: `Link Chemist at play` = mixed URL/section-heading column spanning multiple brands, despite its header; `Page Title ` (trailing space) = supplied anchor/title metadata, sometimes “Empty anchor”, not a fetched listing title. Two rows are brand-section headings, not URLs.

Original URLs and original anchors are retained. Fetched page titles are recorded when available. Normalisation removes fragments/tracking, canonicalises Amazon product URLs and preserves variant/node identifiers. Raw duplicate rows are never discarded from the inventory. Three website URL spellings collapse during normalisation. A further two direct product-source URLs resolve to one Shopify product ID, leaving 35 product profiles from 36 distinct normalised direct product URLs. No exact website/Amazon URL overlaps exist; semantic matches are candidates only.

### Source-type classification (distinct normalised URLs)
'''
for k,v in sorted(collections.Counter(x['source_type'] for x in unique.values()).items()):text+=f'- {k}: **{v}**\n'
text+='\n### Extraction status (distinct normalised supplied URLs)\n'
for k,v in sorted(status.items()):text+=f'- {k}: **{v}**\n'
text+='''
Classification is URL-pattern based and may require content verification. Utility/account/policy links and non-URL rows are separately preserved in `irrelevant_links.json`; they are not treated as product evidence. Category/store pages are discovery sources, not one product each. HTTP 200 indicates an accessible response, not complete extraction or validated identity.

## 2. Official product database

- **35** stable Shopify-linked product profiles: Bare Anatomy **15**, Chemist at Play **18**, SunScoop **2**.
- **35** catalog variant records. This is not a guarantee of every current size or pack.
- **35/35** profiles contain extracted ingredient text in source order.
- **34/35** contain a structured directions section. Missing extraction is not proof of non-disclosure.
- Original product descriptions, additional information, suitability, key ingredients, testing statements and benefit sections are retained where selectors found them. Warnings, technical fields and concentrations are not inferred; some remain unparsed in source text.
- The initial parallel pass encountered 429s. A delayed sequential recovery pass retrieved the direct-product pages; some category/brand sources remain limited.

'''
text+=f'Additional discovery backlog: **{len({x["url"] for x in leads})} distinct product-link leads** from supplied pages, with parent-source provenance. These may include recommendations, aliases and bundles and are **not counted as researched products**. The full catalogue and store universe is not finished.\n'
text+='''
## 3. Amazon review coverage

Four direct CSV product listings were investigated, plus three ASIN leads found in store query context. A context ASIN does not represent the entire store. Store-linked product discoveries remain a separate queue.

| ASIN | Listing title | Displayed rating | Displayed count label | Actual reviews | Review endpoint | Match |
|---|---|---|---|---:|---|---|
'''
for l in ls:text+=f"| {l['asin']} | {l['title']} | {l['displayed_rating'] or 'Unavailable'} | {l['displayed_review_count'] or 'Unavailable'} | 0 | {l.get('review_page_status','not checked')} | Candidate / unconfirmed |\n"
text+='''
- **0 individual records retrieved / 7 investigated ASINs**. Sampling completeness and date ranges are unavailable.
- Listing responses exposed no individual review bodies. The seven permitted review-page attempts returned HTTP 404, not a collected dataset. No authorised provider, review export or credentials were available.
- Displayed counts are retained verbatim; the labels must not automatically be interpreted as counts of written text reviews.
- No review-backed drawback register, frequency/severity ranking, sentiment trend or consumer-alignment verdict can responsibly be calculated.
- Next legitimate method: contract an authorised review provider or obtain a permitted export including review identifiers, text, dates, variants and provenance. Importer scaffold is supplied; provider integration and licence review are still required.

## 4. Communication intelligence — provisional page-level findings

'''
for b in profiles:
 text+=f"### {b['brand']}\n\n**Positioning interpretation:** {b['positioning_interpretation']}.\n\n**Tone interpretation:** {b['tone_interpretation']}.\n\n**Emotional hypothesis:** {b['emotional_hypothesis']}.\n\n**Exact official message:** {b['exact_example']}\n\n**Why it may be used:** connects a practical concern to an ingredient or numerical proof cue, aiming to reduce choice uncertainty. This is an analytical hypothesis, not a consumer finding.\n\n**Credibility question:** {b['communication_concern']}\n\n**Next validation:** {b['next_research']}\n\nSource: {b['source_url']}\n\n"
text+='''
A 35-record communication-to-emotion map is supplied, separately from source facts. These are conservative description-based interpretations, not a complete campaign/visual guide. No assumption is made that all brands have identical strategy.

## 5. Promise versus reality and opportunities

Four evidence layers remain separate: (1) official claims; (2) documented formulation/specifications; (3) brand-reported testing statements, underlying reports not assessed; (4) consumer evidence, currently unavailable. Ingredient studies, consumer studies and finished-product clinical efficacy are not interchangeable. The dashboard therefore displays evidence gaps rather than an invented alignment score.

The internal portfolio comparison works for selected products. Equivalent external competitor variants, prices, claims and review datasets have not been researched. Opportunities are research hypotheses, not confirmed market gaps.

## 6. Validation and delivery

- Seven automated tests passed, including ten-section Streamlit navigation, partial search and empty results, URL deduplication, variant preservation, source-row reconciliation, stable product IDs, variant foreign-key membership, review-count arithmetic, theme denominators and provenance presence.
- Source links were checked during recorded extraction attempts; inaccessible/irrelevant URLs are not represented as verified content.
- No independent scientific validation, complete manual transcription audit, full browser accessibility audit or security penetration test performed.
- No public GitHub remote or production deployment created. Private session development preview only. The application has no authentication and is not ready for public hosting.

## 7. Prioritised next steps

1. Obtain authorised Amazon review records and document the sampling frame.
2. Confirm product/variant/pack matching before assigning any marketplace review to a formulation.
3. Triage the 404 additional product-link leads and complete the accessible catalogue research incrementally.
4. Revisit remaining rate-limited brand/category sources after cooldown; respect access restrictions.
5. Obtain full trial reports, protocols, sample sizes, endpoints and disclaimers for quantitative claims.
6. Collect equivalent competitor sources and unit sizes before price-per-unit or competitive conclusions.
7. Validate communication hypotheses with interviews and message-comprehension tests.
8. Harden access control and confidentiality arrangements before any deployment outside the session.

## Files

`data/clean/`: source inventory, product master, variants, field evidence, review coverage, communication map, brand profiles, insights, checklists and discovery queue (CSV + JSON). `data/intelligence.sqlite`: unified mirror and snapshots. `data/raw_sources.zip`: lossless raw source responses. `reports/tests.txt`: test result. `README.md`: setup, pipeline, security and limitations. Original input CSVs are retained separately in the private research bundle, never committed.
'''
Path('reports/Delivery_Report.md').write_text(text)

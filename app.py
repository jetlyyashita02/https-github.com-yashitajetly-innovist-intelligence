import streamlit as st
import pandas as pd,json
from src.database import records
from src.product_profiles import profile
from src.review_analysis import analyse
st.set_page_config(page_title='Innovist | Intelligence Studio',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>

.stApp{background:#f7f8fa;color:#192c3b} [data-testid="stSidebar"]{background:#102d32;color:#ebf1ee} [data-testid="stSidebar"] *{color:#ebf1ee} h1,h2,h3{letter-spacing:-.04em} .eyebrow{font-size:11px;letter-spacing:2.4px;color:#518272;font-weight:700;margin-bottom:12px}.hero{background:#123d3c;border-radius:16px;padding:26px 32px;color:#fff;margin:8px 0 25px}.hero h2{color:white;margin:0}.hero p{color:#c1d8d0;margin:8px 0 0}.tag{font-size:11px;border:1px solid #c8dbd3;border-radius:20px;padding:4px 9px;color:#306956}.note{border-left:3px solid #d6a650;background:#fff7e7;padding:12px 16px;font-size:13px;margin:15px 0}.stMetric{background:#fff;border:1px solid #e2e8e5;border-radius:12px;padding:18px}.stButton>button{border-radius:8px} div[data-testid="stExpander"]{background:white;border-radius:12px} .block-container{padding-top:2rem;max-width:1550px}
</style>''',unsafe_allow_html=True)
P=records('products');V=records('variants');S=records('inventory');L=records('listings');M=records('messages');F=records('fields');C=records('checklist');I=records('insights');R=records('reviews');A=records('audit')
PAGES=['Executive Overview','Product Explorer','Specification Library','Brand Communication','Amazon Review Intelligence','Promise vs. Reality','Competitor Comparison','Insights & Opportunities','Research Checklist','Sources & Data Quality']
with st.sidebar:
 st.markdown('## ◈ INNOVIST')
 st.caption('INTELLIGENCE STUDIO')
 st.divider();page=st.radio('WORKSPACE',PAGES,label_visibility='visible');st.divider()
 st.markdown('**Evidence, not assumptions.**');st.caption('Private workspace · Research snapshot\n\n26 October 2026');st.caption('No public deployment or GitHub publication performed.')
left,right=st.columns([5,1]);left.markdown('<div class="eyebrow">RESEARCH WORKSPACE / '+page.upper()+'</div>',unsafe_allow_html=True);right.markdown('<span class="tag">● SOURCE-TRACEABLE</span>',unsafe_allow_html=True)
q=st.text_input('Global product search',placeholder='Search products, ingredients, benefits, brands, SKU or ASIN…',key='global_query')
brands=sorted({p['brand'] for p in P});bcol,ccol=st.columns(2);brand=bcol.multiselect('Brand',brands);categories=sorted({p['category'] for p in P});category=ccol.multiselect('Category',categories)
def search(p):
 variants=[v for v in V if v['product_id']==p['id']];msgs=[m for m in M if m['product_id']==p['id']];ls=[l for l in L if l.get('product_id')==p['id'] or l.get('candidate_product_id')==p['id']]
 hay=json.dumps([p['name'],p['brand'],p['category'],p['description'],p['ingredients'],variants,msgs,ls]).lower()
 return all(term in hay for term in q.lower().split()) and (not brand or p['brand'] in brand) and (not category or p['category'] in category)
filtered=[p for p in P if search(p)];ids={p['id'] for p in filtered}
def frame(data):
 if data:st.dataframe(pd.DataFrame(data),width='stretch',hide_index=True)
 else:st.info('No records in this evidence layer. Unavailable does not mean no issues exist.')
def csv_download(data,label,name):st.download_button(label,pd.DataFrame(data).to_csv(index=False),name,'text/csv')
def choose():
 if not filtered:st.warning('No product matches. Try a shorter search or clear the filters.');st.stop()
 return st.selectbox('Select product',filtered,format_func=lambda p:p['brand']+' · '+p['name'])
def gap():st.warning('Consumer positives and drawbacks are unavailable: 0 individual Amazon reviews collected, 0 confirmed product matches. Do not infer sentiment from displayed ratings.')
def report(p):
 st.download_button('↓ Download product profile (JSON)',profile(p,V,M),p['id']+'.json','application/json')
 md='# '+p['name']+'\n\nBrand: '+p['brand']+'\n\nOfficial source: '+p['url']+'\n\nChecked: '+p['checked']+'\n\n## Official description (brand claim)\n'+p['description']+'\n\n## Ingredients\n'+p['ingredients']+'\n\n## Consumer experience\nUnavailable: no confirmed matched review sample.\n\n## Next research\n'+'\n'.join('- '+c['task'] for c in C if c['product_id']==p['id'])
 st.download_button('↓ Download research report (Markdown)',md,p['id']+'.md','text/markdown')
def show_profile(p):
 st.subheader(p['name']);st.caption(p['brand']+' / '+p['category']+' / '+p['id'])
 st.markdown('**What it is / the brand promise**');st.write(p['description'])
 msg=next((m for m in M if m['product_id']==p['id']),None)
 if msg:st.markdown('**Emotional angle — hypothesis:** '+msg['emotional_territory'])
 gap();st.markdown('**Next:** verify Amazon variant match, collect authorised review records, and inspect product-specific claim substantiation.')
 st.link_button('Official product source ↗',p['url']);report(p)
 with st.expander('01 · Specifications, ingredients & variants',expanded=False):
  st.write('**Ingredients (original order)**');st.write(p['ingredients']);st.write('**Directions**');st.write(p['directions']);st.caption('“Not disclosed” here means not present in the retrieved data; a blocked page may contain it. No concentration is estimated.');frame([v for v in V if v['product_id']==p['id']]);frame([f for f in F if f['product_id']==p['id']])
 with st.expander('02 · Claims & communication analysis'):
  for claim in p['claims']:st.write('• '+claim)
  if msg:frame([msg])
 with st.expander('03 · Amazon listings, review evidence & drawback register'):
  frame([l for l in L if l.get('candidate_product_id')==p['id'] or l.get('product_id')==p['id']]);gap();st.write('Drawback register: unavailable, not “no drawbacks”. No review quotations or frequency estimates are generated.')
 with st.expander('04 · Four evidence layers / promise versus reality'):
  frame([{'Layer':'1 · Brand claim','Evidence':p['description']},{'Layer':'2 · Specification','Evidence':p['ingredients']},{'Layer':'3 · Supporting evidence','Evidence':p.get('testing_claims','No testing claim extracted')+' — brand-reported; underlying report not independently assessed.'},{'Layer':'4 · Consumer experience','Evidence':'Unavailable; no matched actual review sample.'}]);st.caption('No claim alignment verdict is possible without layers 3 and 4.')
 with st.expander('05 · Competitive context & research checklist'):
  st.info('External competitor comparisons pending documented equivalent-variant sources. No market-gap claim is established.');frame([c for c in C if c['product_id']==p['id']])
if page=='Executive Overview':
 st.title('The evidence behind the product.')
 st.markdown('<div class="hero"><h2>One workspace. Four evidence layers.</h2><p>Explore official product facts, decode brand messages and see exactly where consumer evidence is still missing.</p></div>',unsafe_allow_html=True)
 a,b,c,d=st.columns(4);a.metric('Products in scope',len(P));b.metric('Identified brands',len(brands));c.metric('Products with ingredient text',sum(p['ingredients']!='Not disclosed' for p in P));d.metric('Collected Amazon reviews',len(R))
 st.caption('Denominators: products = distinct internal IDs linked to product URLs; brands = distinct official catalog vendor groups; ingredient coverage = retrieved ingredient text / '+str(len(P))+' products; review count = individual records, not displayed ratings.')
 gap();l,r=st.columns([3,2])
 with l:
  st.subheader('Product research coverage');frame([{'Brand':b,'Products':sum(p['brand']==b for p in P),'Descriptions':sum(p['brand']==b and p['description']!='Not disclosed' for p in P),'Review-backed products':0} for b in brands])
 with r:
  st.subheader('Priority research gaps');st.write('01  Obtain permitted review dataset\n\n02  Resolve marketplace variants\n\n03  Recover rate-limited specifications\n\n04  Assess quantified claim substantiation')
 st.subheader('Underlying product records');frame([{k:p[k] for k in ['id','brand','name','status','url']} for p in filtered]);csv_download(P,'Download product master','products.csv')
elif page=='Product Explorer':
 st.title('Product Explorer');st.caption(str(len(filtered))+' matching products · aliases and SKU search available through source metadata');p=choose();show_profile(p)
elif page=='Specification Library':
 st.title('Specification Library');frame([f for f in F if f['product_id'] in ids]);st.subheader('Variant & pricing snapshot');frame([v for v in V if v['product_id'] in ids]);st.caption('INR catalog prices, not checkout quotes. Shipping weight is not net volume. Compare-at price is a brand-listed reference, not verified historical selling price.');csv_download([f for f in F if f['product_id'] in ids],'Export field-level evidence','specifications.csv')
elif page=='Brand Communication':
 st.title('Brand Communication Guide');st.caption('Each brand is analysed independently. Emotional motivations are unvalidated hypotheses, not consumer findings.')
 for b in brands:
  bp=next((x for x in records('brand_profiles') if x['brand']==b),None)
  if bp:
   st.subheader(b);st.markdown('**Positioning — interpretation:** '+bp['positioning_interpretation']);st.markdown('**Tone:** '+bp['tone_interpretation']);st.markdown('**Emotional hypothesis:** '+bp['emotional_hypothesis']);st.info(bp['communication_concern']);st.caption('Validate: '+bp['next_research']);st.link_button('Inspect official example ↗',bp['source_url'])
  ms=[m for m in M if m['brand']==b and m['product_id'] in ids]
  if not ms:continue
  with st.expander(b+' · '+str(len(ms))+' message records',expanded=True):
   st.markdown('**Observed product-level approach:** '+', '.join(sorted({m['technique'] for m in ms})))
   st.write('**Positioning interpretation:** inferred from the descriptions below, not a confirmed brand strategy. Visual identity and campaign consistency require a separate rendered creative audit.');frame(ms)
 csv_download([m for m in M if m['product_id'] in ids],'Export communication-to-emotion map','communication.csv')
elif page=='Amazon Review Intelligence':
 st.title('Amazon Review Intelligence');gap();st.metric('Actual records analysed',len(R));frame(L);st.caption('Store-context ASINs are leads, not products represented by the entire store. Similarity scores are suggestions only. Displayed count labels are retained verbatim because ratings and written reviews are not interchangeable.');csv_download(L,'Download review coverage report','review_coverage.csv')
 st.subheader('Review method & import');st.write('Authorised provider/export required. No credentials are configured. The sample would remain partial unless the provider documents completeness. Rating-based valence: 4–5 positive, 3 mixed, 1–2 negative; this is not text sentiment. Keyword theme tags require human validation. Denominator: all analysed reviews. A review can mention multiple themes.');frame(R)
elif page=='Promise vs. Reality':
 st.title('Product Promise vs. Reality');p=choose();show_profile(p)
elif page=='Competitor Comparison':
 st.title('Comparison workspace');st.info('Internal portfolio comparison is available below. External competitive positioning remains an evidence gap; no unsourced competitor statistics are shown.')
 selected=st.multiselect('Choose up to four products',filtered,format_func=lambda p:p['name'],max_selections=4)
 rows=[]
 for p in selected:
  vs=[v for v in V if v['product_id']==p['id']];rows.append({'Product':p['name'],'Brand':p['brand'],'Category':p['category'],'Official description':p['description'],'Ingredients':p['ingredients'],'Variant prices (INR)':'; '.join(str(v['name'])+': '+str(v['price']) for v in vs),'Price per unit':'Not calculated — confirm equivalent net size','Consumer drawbacks':'Unavailable','Source':p['url']})
 if rows:st.dataframe(pd.DataFrame(rows).set_index('Product').T,width='stretch');csv_download(rows,'Export comparison','comparison.csv')
 st.subheader('External evidence collection template');frame([{'Category':'Equivalent product type','Brand/product':'Pending research','Variant/size':'Verify formula & pack','Source URL':'Required','Price & date':'Required','Unit price':'Same unit basis required','Claims & evidence':'Separate claim from substantiation','Review sample':'Only actual permitted records'}])
elif page=='Insights & Opportunities':
 st.title('Insights & Opportunities');st.caption('Observations, interpretations and opportunities are separate. No unavailable consumer dataset is presented as an insight.');frame([i for i in I if i['product_id'] in ids]);csv_download([i for i in I if i['product_id'] in ids],'Export research opportunities','insights.csv')
elif page=='Research Checklist':
 st.title('Research Checklist');priority=st.multiselect('Priority',[1,2,3],default=[1,2,3]);rows=[c for c in C if c['product_id'] in ids and c['priority'] in priority];frame(rows);csv_download(rows,'Download checklist','research_checklist.csv')
else:
 st.title('Sources & Data Quality');st.subheader('Input reconciliation');frame(A);st.caption('Row counts exclude CSV headers. Duplicate occurrences = valid URL rows minus unique valid URLs. Blank URLs and non-URL headings are counted separately. Normalisation removes tracking but retains variant/node identifiers.')
 status=st.multiselect('Extraction status',sorted({s['extraction_status'] for s in S}));kind=st.multiselect('Source type',sorted({s['source_type'] for s in S}));rows=[s for s in S if (not status or s['extraction_status'] in status) and (not kind or s['source_type'] in kind)];frame(rows);csv_download(rows,'Download source inventory','sources.csv')
 st.subheader('Additional discovered product links — not researched profiles');leads=records('discovery_leads');st.caption(str(len({x['url'] for x in leads}))+' distinct product-link leads; may include unrelated recommendations, aliases or bundles. Verification pending.');frame(leads);csv_download(leads,'Download discovery backlog','discovery_leads.csv');st.subheader('Limitations');st.write('HTTP 429 responses are retained, not bypassed. Utility, policy and account links are preserved separately and not used as product evidence. Catalog descriptions can be available when page extraction fails. Snapshot dates and raw source paths are preserved. External competitor claims and complete brand visual audits remain open.');st.link_button('Official website ↗','https://innovist.com')

import json,re,sqlite3,csv
from pathlib import Path
from bs4 import BeautifulSoup
from src.web_extraction import specs
from src.ingestion import sid
R=Path(__file__).parent;D=R/'data';load=lambda n:json.loads((D/'clean'/f'{n}.json').read_text())
products=load('products');inventory=load('inventory');variants=load('variants');fields=load('fields');listings=load('listings')
catalog=[]
for path in (D/'raw').glob('catalog*.json'):catalog+=json.loads(path.read_text())['products']
byhandle={p['handle']:p for p in catalog}
for obj in products:
 handle=obj['url'].split('/products/')[1].split('?')[0];p=byhandle.get(handle)
 if p:
  old=obj['id'];obj.update(id='shopify-'+str(p['id']),name=p['title'],brand=p.get('vendor') or 'Not disclosed',category=p.get('product_type') or 'Not disclosed')
  for b in ['Bare Anatomy','Chemist at Play','SunScoop']:
   if b.lower().replace(' ','') in obj['brand'].lower().replace(' ',''):obj['brand']=b
  desc=BeautifulSoup(p.get('body_html') or '', 'html.parser').get_text(' ',strip=True)
  if obj['description']=='Not disclosed' and desc:obj['description']=desc;obj['claims']=re.split(r'(?<=[.!?])\s+',desc);obj['description_source']='https://innovist.com/products.json?limit=250&page='+('2' if p in json.loads((D/'raw/catalog-page2.json').read_text())['products'] else '1')
  if not any(v['product_id']==obj['id'] for v in variants):
   for v in p['variants']:variants.append(dict(id=str(v['id']),product_id=obj['id'],name=v['title'],sku=v.get('sku'),price=v.get('price'),compare_at_price=v.get('compare_at_price'),grams=v.get('grams'),available=v.get('available'),url=obj['url']+'?variant='+str(v['id']),checked='2026-10-26'))
  obj['source_note']='Official catalog metadata; page fields limited by HTTP '+obj['status']
 if 'rosemary-rice-water-hair-growth-spray'==handle:
  html=(D/'raw/sample.html').read_text();obj.update(**specs(html));obj['brand']='Bare Anatomy';obj['name']='Rosemary & Rice Water Hair Growth Spray - 200 ml';obj['text']=BeautifulSoup(html,'html.parser').get_text(' ',strip=True);obj['status']='200 (earlier saved response; later 429)';obj['source_note']='Successful initial page response preserved in data/raw/sample.html';obj['claims']=re.split(r'(?<=[.!?])\s+',obj['description'])
  obj['directions']='Use on clean, dry or towel-dried hair, ideally post-wash. Daily use. (Official FAQ)'
 obj['description_source']=obj.get('description_source',obj['url'])
# One stable product with multiple source URLs (same handle with query).
products=list({p['id']:p for p in products}.values());variants=list({v['id']:v for v in variants}.values())
# Deterministic candidate match, never auto-confirm size/variant equivalence.
from rapidfuzz.fuzz import token_set_ratio
for l in listings:
 ranked=sorted([(token_set_ratio(l['title'].lower(),p['name'].lower()),p) for p in products if p['brand']!='Unresolved'],key=lambda a:a[0],reverse=True)
 if ranked and ranked[0][0]>44:
  score,p=ranked[0];l['candidate_product_id']=p['id'];l['match_score']=round(score,1);l['match_status']='candidate only — size, formula and pack require verification'
 l['limitation']='Product response exposes ratings but no individual review records. No authorised review provider/export configured. Completeness unavailable.'
# Product-specific interpretations, grounded only in product description, not navigation.
messages=[];insights=[];checklist=[]
for p in products:
 text=p['description'];low=text.lower();territory='Informed choice / reassurance';tension='Difficulty evaluating product suitability';tech='Benefit-led description'
 if any(k in low for k in ['hair fall','hair growth','thicker']):territory='Confidence / control';tension='Concern about visible thinning or hair loss';tech='Outcome-led and ingredient-led framing'
 elif any(k in low for k in ['odour','pigmentation','bright']):territory='Social confidence / comfort';tension='Concern about odour or uneven appearance';tech='Problem–solution framing'
 elif any(k in low for k in ['spf','sun protection','sunscreen']):territory='Reassurance / freedom outdoors';tension='Balancing protection with everyday wearability';tech='Protection and routine framing'
 if text!='Not disclosed':
  messages.append(dict(product_id=p['id'],brand=p['brand'],product=p['name'],original_message=text,source_url=p['description_source'],functional_promise='Official wording above; efficacy not independently established',emotional_territory=territory,consumer_tension=tension,intended_audience='Users with the stated concern (analytical inference)',desired_perception='Effective and suitable for the stated use (hypothesis)',technique=tech,proof='Description is a brand claim, not independent substantiation',weakness='Testing methods and population need checking before quantified claims are endorsed',validation='Interview relevant users; test message comprehension and expected time-to-result',evidence_label='Analytical interpretation / unverified emotional hypothesis'))
 for priority,task,reason in [(1,'Obtain authorised Amazon review records and verify ASIN/variant mapping','No review-backed consumer conclusion is available'),(1,'Verify full formulation, warnings and directions against an accessible product page or packaging','Missing extraction is not proof of non-disclosure'),(2,'Request product-specific substantiation and trial methodology','Brand claim is not proof of efficacy'),(2,'Compare equivalent sizes and current competitor prices','No validated competitor set yet'),(3,'Validate emotional interpretation with consumer interviews','Emotional benefits are hypotheses')]:checklist.append(dict(product_id=p['id'],product=p['name'],priority=priority,task=task,reason=reason,status='open'))
 insights.append(dict(product_id=p['id'],product=p['name'],observation='No individual Amazon review records collected for a confirmed product match',evidence='data/clean/listings.json; data/clean/reviews.json',consumer_tension='Unknown; not inferable from unavailable review data',interpretation='Consumer agreement with brand promises cannot yet be assessed',implication='Do not recommend product changes based on displayed ratings alone',opportunity='Test claim comprehension and expected results with relevant users',validation='Authorised review sample + product/variant verification + interviews',confidence='High for data gap; consumer hypothesis unvalidated',evidence_label='Research gap'))
fields=[]
for p in products:
 for f in ['description','ingredients','directions','additional_information']:
  fields.append(dict(product_id=p['id'],field=f,value=p.get(f,'Not disclosed'),source_url=p['description_source'] if f=='description' else p['url'],section=f,checked=p['checked'],evidence_label='Official brand claim' if f=='description' else 'Official specification',status='unavailable extraction / not disclosed in retrieved data' if p.get(f,'Not disclosed')=='Not disclosed' else 'retrieved'))
for name,data in [('products',products),('variants',variants),('fields',fields),('listings',listings),('messages',messages),('insights',insights),('checklist',checklist)]:
 (D/'clean'/f'{name}.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
 if data:
  with (D/'clean'/f'{name}.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for row in data for k in row)));w.writeheader();w.writerows(data)
con=sqlite3.connect(D/'intelligence.sqlite');import pandas as pd
for name in ['products','variants','fields','listings','messages','insights','checklist']:
 data=load(name);pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data]).to_sql('field_evidence' if name=='fields' else name,con,if_exists='replace',index=False)
print('Products',len(products),'variants',len(variants),'messages',len(messages))

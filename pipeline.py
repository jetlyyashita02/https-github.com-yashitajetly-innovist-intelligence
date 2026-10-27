import csv,json,re,sqlite3,collections,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from src.ingestion import normalize,classify,sid
from src.web_extraction import fetch,specs
R=Path(__file__).parent; D=R/'data';inventory=[];audits=[]
for name in ['Links - website links.csv','Links - amazon links .csv']:
 rows=list(csv.DictReader(open(R.parent/'uploads'/name,encoding='utf-8-sig')));urls=[];brand='Chemist at Play'
 for i,r in enumerate(rows,2):
  original=r.get('Url',r.get('Link Chemist at play','')).strip();n=normalize(original);urls.append(original)
  if original.startswith('Links '):brand=original[6:]
  title=r.get('Anchor',r.get('Page Title ',''));b=brand if 'amazon' in name else ''
  for token,bn in [('bare-anatomy','Bare Anatomy'),('chemist-at-play','Chemist at Play'),('sunscoop','SunScoop')]:
   if token in original.lower():b=bn
  inventory.append(dict(source_id=sid(name+str(i)),file=name,row=i,original_url=original,normalized_url=n,page_title=title,brand=b,source_type=classify(n),extraction_status='not checked' if n else 'not a URL',last_checked='',error='',extracted_data_location='',asin=(re.search(r'/dp/([A-Z0-9]{10})',n)[1] if re.search(r'/dp/([A-Z0-9]{10})',n) else ''),context_asin=(re.search(r'lp_context_asin=([A-Z0-9]{10})',original)[1] if re.search(r'lp_context_asin=([A-Z0-9]{10})',original) else '')))
 valid=[u for u in urls if normalize(u)];norm=[normalize(u) for u in valid]
 audits.append(dict(file=name,columns=list(rows[0]),rows=len(rows),blank_urls=sum(not u for u in urls),non_url_rows=sum(bool(u) and not normalize(u) for u in urls),unique_original_urls=len(set(valid)),duplicate_url_occurrences=len(valid)-len(set(valid)),unique_normalized_urls=len(set(norm)),normalized_duplicate_occurrences=len(norm)-len(set(norm))))
# Fetch every distinct relevant source, preserve utility links without fetching.
urls=sorted({x['normalized_url'] for x in inventory if x['source_type'] not in ('other / utility','blank or section heading')})
print('Relevant sources',len(urls),flush=True)
with ThreadPoolExecutor(max_workers=5) as pool: pages=dict(zip(urls,pool.map(fetch,urls)))
for x in inventory:
 p=pages.get(x['normalized_url'])
 if p:x.update(extraction_status=p['status'],last_checked=p['checked'],error=p['error'],extracted_data_location='data/raw/'+sid(x['normalized_url'])+'.json')
 else:x['error']='Preserved; utility/irrelevant or non-URL row, not fetched'
products=[];variants=[];fields=[]
catalog=json.loads((D/'raw/catalog.json').read_text())['products'];byhandle={p['handle']:p for p in catalog}
product_urls=sorted({u for u in urls if classify(u)=='official product page'})
# Individual JSON resolves products outside the first catalog page without expanding scope silently.
for j,u in enumerate(product_urls):
 page=pages[u];h=u.split('/products/')[1].split('?')[0];p=byhandle.get(h)
 if not p:
  extra=fetch(u+'.json')
  try:p=json.loads(extra['html']).get('product')
  except Exception:p=None
 if not p:
  products.append(dict(id='unresolved-'+sid(u),name=h.replace('-',' ').title(),brand='Unresolved',category='Not disclosed',url=u,status=page['status'],description='Not disclosed',ingredients='Not disclosed',directions='Not disclosed',text='',checked=page['checked'],claims=[],source_note='URL-derived label only; identity unverified'));continue
 pid='shopify-'+str(p['id']);sp=specs(page['html']);vendor=p.get('vendor','');brand=next((b for b in ['Bare Anatomy','Chemist at Play','SunScoop','Sun Scoop','MuscleBlaze'] if b.lower() in vendor.lower()),vendor or 'Not disclosed')
 if brand=='Sun Scoop':brand='SunScoop'
 body=BeautifulSoup(p.get('body_html') or '', 'html.parser').get_text(' ',strip=True)
 if sp['description']=='Not disclosed' and body:sp['description']=body
 s=BeautifulSoup(page['html'],'html.parser')
 # Product-specific sections; never treat navigation/site boilerplate as product claims.
 claimtext=sp['description'];claims=[v.strip() for v in re.split(r'(?<=[.!?])\s+',claimtext) if v.strip() and v!='Not disclosed']
 obj=dict(id=pid,name=p['title'],brand=brand,category=p.get('product_type') or 'Not disclosed',url=u,status=page['status'],checked=page['checked'],text=page['text'],claims=claims,source_note='Official page + Shopify catalog',**sp)
 products.append(obj)
 for k,v in sp.items():fields.append(dict(product_id=pid,field=k,value=v,source_url=u,section=k,checked=page['checked'],evidence_label='Official specification' if k!='description' else 'Official brand claim'))
 for v in p.get('variants',[]):variants.append(dict(id=str(v['id']),product_id=pid,name=v.get('title'),sku=v.get('sku'),price=v.get('price'),compare_at_price=v.get('compare_at_price'),grams=v.get('grams'),available=v.get('available'),url=u+'?variant='+str(v['id']),checked=page['checked']))
 print(j+1,len(product_urls),p['title'],flush=True)
# Context ASINs are leads, never inferred store products.
asins={x['asin'] for x in inventory if x['asin']}|{x['context_asin'] for x in inventory if x['context_asin']}
listings=[];reviews=[]
for asin in sorted(asins):
 u='https://www.amazon.in/dp/'+asin;p=fetch(u);s=BeautifulSoup(p['html'],'html.parser');title=s.select_one('#productTitle');name=title.get_text(' ',strip=True) if title else ''
 rating=s.select_one('#acrPopover');count=s.select_one('#acrCustomerReviewText')
 record=dict(asin=asin,url=u,title=name,status=p['status'],checked=p['checked'],displayed_rating=rating.get('title') if rating else None,displayed_review_count=count.get_text(' ',strip=True) if count else None,product_id=None,match_status='unmatched; manual variant verification required',sample_status='unavailable',limitation='No authorised API/export configured; only genuinely accessible product-page review records collected')
 for node in s.select('[data-hook="review"]'):
  def tx(sel):
   z=node.select_one(sel);return z.get_text(' ',strip=True) if z else None
  text=tx('[data-hook="review-body"]');rid=node.get('id')
  if not text or not rid:continue
  stars=tx('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]')
  reviews.append(dict(review_id=rid,asin=asin,product_id=None,title=tx('[data-hook="review-title"]'),text=text,rating=float(re.search(r'[\d.]+',stars)[0]) if stars and re.search(r'[\d.]+',stars) else None,date=tx('[data-hook="review-date"]'),verified_purchase=bool(node.select_one('[data-hook="avp-badge"]')),variant=tx('[data-hook="format-strip"]'),helpful_votes=tx('[data-hook="helpful-vote-statement"]'),url='https://www.amazon.in/gp/customer-reviews/'+rid,collected=p['checked']))
 record['analysed_reviews']=sum(r['asin']==asin for r in reviews);record['sample_status']='partial' if record['analysed_reviews'] else 'unavailable';listings.append(record)
# De-duplicate review IDs; preserve original raw source.
reviews=list({r['review_id']:r for r in reviews}.values())
for name,data in [('inventory',inventory),('audit',audits),('products',products),('variants',variants),('fields',fields),('listings',listings),('reviews',reviews)]:
 (D/'clean'/f'{name}.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
 if data:
  with (D/'clean'/f'{name}.csv').open('w') as f:
   w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in data for k in r)));w.writeheader();w.writerows(data)
con=sqlite3.connect(D/'intelligence.sqlite')
for table,data in [('sources',inventory),('products',products),('variants',variants),('field_evidence',fields),('listings',listings),('reviews',reviews)]:
 import pandas as pd
 if data:pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data]).to_sql(table,con,if_exists='replace',index=False)
con.execute('CREATE TABLE IF NOT EXISTS aliases (product_id TEXT, alias TEXT, source_url TEXT, verified INTEGER)');con.execute('CREATE TABLE IF NOT EXISTS review_import_log (file_hash TEXT PRIMARY KEY, imported_at TEXT)');con.commit()
(R/'reports/audit.json').write_text(json.dumps(audits,indent=2));print('DONE',len(products),len(variants),len(reviews),flush=True)

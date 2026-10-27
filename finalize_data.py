import json,re,csv,sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
from src.ingestion import sid,normalize
D=Path('data');load=lambda n:json.loads((D/'clean'/f'{n}.json').read_text())
ps=load('products');sources=load('inventory');fields=[];leads=[]
for p in ps:
 raw=D/'raw'/f"{sid(p['url'])}.json"
 if raw.exists():page=json.loads(raw.read_text())
 else:continue
 if p['name'].startswith('Rosemary & Rice'):html=(D/'raw/sample.html').read_text()
 elif page['status']=='200':html=page['html']
 else:continue
 s=BeautifulSoup(html,'html.parser')
 selectors={'description':'#description','ingredients':'#ingredients','additional_information':'#info','directions':'[id*="product_directions_section"]','benefits':'[id^="benefit-panel-1"]','suitability':'[id^="benefit-panel-2"]','key_ingredients':'.key-ingredients-section, [id*="key_ingredients"]','testing_claims':'[id*="clinical_results"], .clinical-results','certifications_claims':'[id*="reasons_trust"], .reasons-trust','comparison_claims':'#why'}
 for field,sel in selectors.items():
  e=s.select_one(sel)
  if e:
   for t in e(['script','style']):t.decompose()
   val=e.get_text(' ',strip=True)
   if val:p[field]=val
 p['claims']=re.split(r'(?<=[.!?])\s+',p['description']);p['description_source']=p['url'];p['source_note']='Successful official product response; original text in cached raw HTML'
 for f in list(selectors)+['warnings','active_concentrations','format','fragrance','recommended_frequency','complementary_products']:
  # Do not infer specific concentrations from ingredient order or name.
  value=p.get(f,'Not disclosed');fields.append(dict(product_id=p['id'],field=f,value=value,source_url=p['url'],section=selectors.get(f,'Not extracted / not separately disclosed'),checked=p['checked'],evidence_label='Official brand claim' if f in ['description','benefits','testing_claims','certifications_claims','comparison_claims'] else 'Official specification',status='retrieved' if value!='Not disclosed' else 'Unavailable in structured extraction; inspect source'))
for x in sources:
 raw=D/'raw'/f"{sid(x['normalized_url'])}.json"
 if raw.exists():
  p=json.loads(raw.read_text());x.update(extraction_status=p['status'],last_checked=p['checked'],error=p['error'])
  soup=BeautifulSoup(p['html'],'html.parser')
  for a in soup.select('a[href]'):
   u=a['href']
   if u.startswith('/'):u=('https://www.amazon.in' if 'amazon' in x['normalized_url'] else 'https://innovist.com')+u
   if '/products/' in u or re.search('/dp/[A-Z0-9]{10}',u):
    leads.append(dict(url=normalize(u),title=a.get_text(' ',strip=True),discovered_from=x['normalized_url'],status='discovery lead; not necessarily researched',checked=p['checked']))
leads=list({(x['url'],x['discovered_from']):x for x in leads}.values())
for name,rows in [('products',ps),('inventory',sources),('fields',fields),('discovery_leads',leads)]:
 (D/'clean'/f'{name}.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
 if rows:
  with (D/'clean'/f'{name}.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for x in rows for k in x)));w.writeheader();w.writerows(rows)
print('Ingredients',sum(p['ingredients']!='Not disclosed' for p in ps),'directions',sum(p['directions']!='Not disclosed' for p in ps),'discovery links',len({x['url'] for x in leads}))

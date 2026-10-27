"""Single sequential recovery pass after cooldown. Stop on first 429; never bypass."""
import json,time
from pathlib import Path
from src.web_extraction import fetch,specs
D=Path('data');ps=json.loads((D/'clean/products.json').read_text());log=[]
for p in ps:
 if p['status']!='429':continue
 page=fetch(p['url'],refresh=True);log.append({'url':p['url'],'status':page['status'],'checked':page['checked']})
 if page['status']=='429':break
 if page['status']=='200':
  found=specs(page['html'])
  for k,v in found.items():
   if v!='Not disclosed':p[k]=v
  p.update(status='200',text=page['text'],checked=page['checked'])
 time.sleep(1.2)
(D/'clean/products.json').write_text(json.dumps(ps,indent=2,ensure_ascii=False));Path('reports/recovery.json').write_text(json.dumps(log,indent=2));print(log)

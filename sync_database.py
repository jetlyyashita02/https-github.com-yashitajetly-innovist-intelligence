import json,sqlite3,csv
from pathlib import Path
import pandas as pd
from src.database import records,connect
D=Path('data/clean');con=connect()
for path in D.glob('*.json'):
 name=path.stem;data=json.loads(path.read_text())
 if not isinstance(data,list) or not data:continue
 table={'inventory':'sources','fields':'field_evidence'}.get(name,name)
 pd.DataFrame([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data]).to_sql(table,con,if_exists='replace',index=False)
 with path.with_suffix('.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in data for k in r)));w.writeheader();w.writerows(data)
con.execute('CREATE TABLE IF NOT EXISTS snapshots (entity_id TEXT, snapshot_type TEXT, retrieved_at TEXT, payload TEXT, UNIQUE(entity_id,snapshot_type,retrieved_at))')
for name,typ,idkey in [('variants','price','id'),('listings','marketplace','asin')]:
 for r in records(name):con.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?,?,?)',(r[idkey],typ,r['checked'],json.dumps(r)))
con.execute('CREATE TABLE IF NOT EXISTS reviews (review_id TEXT PRIMARY KEY, asin TEXT, product_id TEXT, text TEXT, rating REAL, date TEXT, url TEXT)')
for p in records('products'):con.execute('INSERT INTO aliases SELECT ?,?,?,1 WHERE NOT EXISTS (SELECT 1 FROM aliases WHERE product_id=? AND alias=?)',(p['id'],p['name'],p['url'],p['id'],p['name']))
for idx,table,col in [('product_ids','products','id'),('source_urls','sources','normalized_url'),('variant_product','variants','product_id')]:con.execute(f'CREATE INDEX IF NOT EXISTS {idx} ON {table}({col})')
con.commit();con.close()
con=connect()
con.execute('CREATE TABLE IF NOT EXISTS product_sources (product_id TEXT, source_id TEXT, relation TEXT, PRIMARY KEY(product_id,source_id))')
for s in records('inventory'):
 if s.get('product_id'):con.execute('INSERT OR REPLACE INTO product_sources VALUES (?,?,?)',(s['product_id'],s['source_id'],'official product URL'))
con.commit();con.close()

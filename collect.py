import json,re,os,urllib.request,datetime as dt,zoneinfo
ALIAS={'land':['beauty|美女','baymax|ベイマックス','pooh|プーさん','monsters|モンスターズ','splash|スプラッシュ','big thunder|ビッグサンダー','space mountain|スペース','haunted|ホーンテッド','buzz|バズ','pirates|カリブ'],
'sea':['frozen|アナ','rapunzel|ラプンツェル','peter pan|ピーターパン','soarin|ソアリン','toy story|トイ・ストーリー','tower of terror|タワー','center of the earth|センター','indiana|インディ','raging|レイジング','nemo|ニモ']}
PARKS={'land':274,'sea':275}
KEEP_DAYS=60
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'park-wait-collector'}),timeout=30))
now=dt.datetime.now(zoneinfo.ZoneInfo('Asia/Tokyo'))

def shows():
    JST=zoneinfo.ZoneInfo('Asia/Tokyo')
    d=next(x for x in get('https://api.themeparks.wiki/v1/destinations')['destinations'] if 'tokyo' in x['name'].lower())
    out={'updated':now.isoformat(),'land':[],'sea':[]}
    for p in d['parks']:
        key='sea' if 'sea' in p['name'].lower() else 'land'
        for e in get(f"https://api.themeparks.wiki/v1/entity/{p['id']}/live").get('liveData',[]):
            if e.get('entityType')!='SHOW': continue
            for s in e.get('showtimes') or []:
                try:
                    a=dt.datetime.fromisoformat(s['startTime']).astimezone(JST)
                    b=dt.datetime.fromisoformat(s['endTime']).astimezone(JST) if s.get('endTime') else None
                except Exception: continue
                out[key].append({'n':e['name'],'d':a.date().isoformat(),'s':a.strftime('%H:%M'),'m':int((b-a).total_seconds()//60) if b else 40})
    for k in ('land','sea'): out[k].sort(key=lambda x:(x['d'],x['s']))
    json.dump(out,open('data/shows.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
try: shows()
except Exception as ex: print('shows skipped:',ex)
slot=int((now.hour*60+now.minute+15)//30*30)
if not 540<=slot<=1260: raise SystemExit('time out of range')
date=now.date().isoformat()
slot=int((now.hour*60+now.minute+15)//30*30)
inrange=540<=slot<=1260
try:
    p=get('https://api.open-meteo.com/v1/forecast?latitude=35.633&longitude=139.880&daily=precipitation_sum&timezone=Asia%2FTokyo&forecast_days=1')['daily']['precipitation_sum'][0] or 0
    wc=2 if p>=15 else 1 if p>=3 else 0
except Exception: wc=0
path='data/history.json'
rows=json.load(open(path))['rows'] if os.path.exists(path) else []
new={};rl={}
for pi,pk in enumerate(['land','sea']):
    j=get(f'https://queue-times.com/parks/{PARKS[pk]}/queue_times.json')
    allr=[r for l in j.get('lands',[]) for r in l.get('rides',[])]+j.get('rides',[])
    seen=set();lst=[];pn={}
    for r in allr:
        if r['id'] in seen: continue
        seen.add(r['id'])
        bi=next((k for k,a in enumerate(ALIAS[pk]) if re.search(a,r['name'],re.I)),None)
        lst.append([r['id'],r['name'],bi])
        if r.get('is_open') and isinstance(r.get('wait_time'),(int,float)): pn[(pi,r['id'],date,slot)]=int(r['wait_time'])
    rl[pk]=lst
    if inrange and len(pn)>=3: new.update(pn)
json.dump(rl,open('data/rides.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
cut=(now.date()-dt.timedelta(days=KEEP_DAYS)).isoformat()
rows=[r for r in rows if r[1]>=100 and r[2]>=cut and (r[0],r[1],r[2],r[3]) not in new]
rows+=[[k[0],k[1],k[2],k[3],v,wc] for k,v in new.items()]
rows.sort(key=lambda r:(r[2],r[3],r[0],r[1]))
json.dump({'updated':now.isoformat(),'rows':rows},open(path,'w'),separators=(',',':'))
print(len(new),'rows added,',sum(len(v) for v in rl.values()),'rides listed')


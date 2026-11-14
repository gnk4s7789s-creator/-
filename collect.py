import json,re,os,urllib.request,datetime as dt,zoneinfo
ALIAS={'land':['beauty|美女','baymax|ベイマックス','pooh|プーさん','monsters|モンスターズ','splash|スプラッシュ','big thunder|ビッグサンダー','space mountain|スペース','haunted|ホーンテッド','buzz|バズ','pirates|カリブ'],
'sea':['frozen|アナ','rapunzel|ラプンツェル','peter pan|ピーターパン','soarin|ソアリン','toy story|トイ・ストーリー','tower of terror|タワー','center of the earth|センター','indiana|インディ','raging|レイジング','nemo|ニモ']}
PARKS={'land':274,'sea':275}
KEEP_DAYS=90
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'park-wait-collector'}),timeout=30))
now=dt.datetime.now(zoneinfo.ZoneInfo('Asia/Tokyo'))
slot=int((now.hour*60+now.minute+15)//30*30)
if not 540<=slot<=1260: raise SystemExit('time out of range')
date=now.date().isoformat()
try:
    p=get('https://api.open-meteo.com/v1/forecast?latitude=35.633&longitude=139.880&daily=precipitation_sum&timezone=Asia%2FTokyo&forecast_days=1')['daily']['precipitation_sum'][0] or 0
    wc=2 if p>=15 else 1 if p>=3 else 0
except Exception: wc=0
path='data/history.json'
rows=json.load(open(path))['rows'] if os.path.exists(path) else []
new={}
for pi,pk in enumerate(['land','sea']):
    j=get(f'https://queue-times.com/parks/{PARKS[pk]}/queue_times.json')
    live=[r for l in j.get('lands',[]) for r in l.get('rides',[])]+j.get('rides',[])
    live=[r for r in live if r.get('is_open') and isinstance(r.get('wait_time'),(int,float))]
    if len(live)<3: continue
    for idx,a in enumerate(ALIAS[pk]):
        m=next((r for r in live if re.search(a,r['name'],re.I)),None)
        if m: new[(pi,idx,date,slot)]=int(m['wait_time'])
cut=(now.date()-dt.timedelta(days=KEEP_DAYS)).isoformat()
rows=[r for r in rows if r[2]>=cut and (r[0],r[1],r[2],r[3]) not in new]
rows+=[[k[0],k[1],k[2],k[3],v,wc] for k,v in new.items()]
rows.sort(key=lambda r:(r[2],r[3],r[0],r[1]))
json.dump({'updated':now.isoformat(),'rows':rows},open(path,'w'),separators=(',',':'))
print(len(new),'rows added')

import numpy as np, cv2, json
res=json.load(open('reg.json')); tie=json.load(open('sift.json'))
H={k:np.array(res[k]['H']) for k in ['4071','3054']}
G={k:(np.float32(res[k]['inl'][0]),np.float32(res[k]['inl'][1])) for k in ['4071','3054']}
T53=(np.float32(tie['4053']['P']),np.float32(tie['4053']['Q']))  # 4053 px -> 4071 px
T54=(np.float32(tie['3054']['P']),np.float32(tie['3054']['Q']))  # 3054 px -> 4071 px
pt=lambda Hm,P: cv2.perspectiveTransform(np.float32(P)[None],Hm)[0]
# consistency before
H54via=H['4071']@np.array(tie['3054']['H'])
d=np.linalg.norm(pt(H['3054'],T54[0])-pt(H['4071'],T54[1]),axis=1); print('3054 vs 4071 in overlap before: median m',np.median(d).round(2),'max',d.max().round(1))
for it in range(5):
  # 4071: own GCPs + tie points from 3054 (mapped by current H3054), weight ties lower via subsample
  idx=np.random.default_rng(it).choice(len(T54[0]),min(60,len(T54[0])),replace=False)
  P71=np.vstack([G['4071'][0],T54[1][idx]]); Q71=np.vstack([G['4071'][1],pt(H['3054'],T54[0][idx])])
  H['4071'],_=cv2.findHomography(P71,Q71,0)
  P54=np.vstack([G['3054'][0],T54[0][idx]]); Q54=np.vstack([G['3054'][1],pt(H['4071'],T54[1][idx])])
  H['3054'],_=cv2.findHomography(P54,Q54,0)
d=np.linalg.norm(pt(H['3054'],T54[0])-pt(H['4071'],T54[1]),axis=1); print('3054 vs 4071 overlap after: median m',np.median(d).round(2),'max',d.max().round(1))
for k in ['4071','3054']:
  e=np.linalg.norm(pt(H[k],G[k][0])-G[k][1],axis=1); print(k,'GCP RMSE vs 1953 m',np.sqrt((e**2).mean()).round(2),'n',len(e))
H['4053']=cv2.findHomography(T53[0],pt(H['4071'],T53[1]),0)[0]
# 4053 check vs its own 1953 matches
own=np.float32(res['4053']['inl'][0]),np.float32(res['4053']['inl'][1])
e=np.linalg.norm(pt(H['4053'],own[0])-own[1],axis=1); print('4053 check vs 1953 matches m median',np.median(e).round(1),'n',len(e))
bbs={'4071':(640,480,7380,7230),'4053':(470,520,7230,7140),'3054':(520,420,7230,7180)}
for k in H:
  c=np.float32([[(bbs[k][0]+bbs[k][2])/2,(bbs[k][1]+bbs[k][3])/2]])
  p=pt(H[k],np.vstack([c,c+[100,0],c+[0,100]]))
  print(k,'m/px',np.linalg.norm(p[1]-p[0])/100,np.linalg.norm(p[2]-p[0])/100)
json.dump({k:H[k].tolist() for k in H},open('Hfinal.json','w'))

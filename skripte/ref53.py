import numpy as np, cv2, json
Hf=json.load(open('Hfinal.json')); tie=json.load(open('sift.json'))
H71=np.array(Hf['4071']); Hm=np.array(Hf['4053'])
pt=lambda Hm,P: cv2.perspectiveTransform(np.float32(P)[None],Hm)[0]
TP=np.float32(tie['4053']['P']); TQ=pt(H71,np.float32(tie['4053']['Q']))
ref=cv2.imread('r53.jpg',0); Hh,Ww=ref.shape
cl=cv2.createCLAHE(2.0,(16,16))
def prep(im):
  im=cl.apply(im); g=cv2.GaussianBlur(im,(0,0),1.5)
  gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1)
  return cv2.GaussianBlur(np.sqrt(gx*gx+gy*gy),(0,0),1.0)
R=prep(ref)
fr=cv2.imread('f4053.jpg',0); bb=(470,520,7230,7140); mask=np.zeros_like(fr); mask[bb[1]:bb[3],bb[0]:bb[2]]=255
rng=np.random.default_rng(0)
for it in range(4):
  w=cv2.warpPerspective(fr,Hm,(Ww,Hh),flags=cv2.INTER_AREA); wm=cv2.warpPerspective(mask,Hm,(Ww,Hh),flags=cv2.INTER_NEAREST); W=prep(w)
  win=44;srch=30 if it==0 else 15;S=[];D=[]
  for y in range(srch+win,Hh-srch-win,30):
    for x in range(srch+win,Ww-srch-win,30):
      if wm[y-win-srch:y+win+srch,x-win-srch:x+win+srch].min()==0: continue
      t=W[y-win:y+win,x-win:x+win]
      if t.std()<4: continue
      c=cv2.matchTemplate(R[y-win-srch:y+win+srch,x-win-srch:x+win+srch],t,cv2.TM_CCOEFF_NORMED); _,mx,_,ml=cv2.minMaxLoc(c)
      if mx<0.4: continue
      c2=c.copy(); cv2.circle(c2,ml,8,-1,-1)
      if mx-c2.max()<0.06: continue
      p=np.linalg.inv(Hm)@np.array([x,y,1.]); p/=p[2]; S.append(p[:2]); D.append([x+ml[0]-srch,y+ml[1]-srch])
  S=np.float32(S);D=np.float32(D)
  # RANSAC on 1953 matches alone first
  _,inl=cv2.findHomography(S,D,cv2.RANSAC,5.0,maxIters=30000); inl=inl.ravel().astype(bool)
  idx=rng.choice(len(TP),min(len(TP),max(50,int(inl.sum()))),replace=False)
  Hm,_=cv2.findHomography(np.vstack([S[inl],TP[idx]]),np.vstack([D[inl],TQ[idx]]),0)
  e1=np.linalg.norm(pt(Hm,S[inl])-D[inl],axis=1); e2=np.linalg.norm(pt(Hm,TP)-TQ,axis=1)
  print('it',it,'1953 matches',len(S),'inl',inl.sum(),'RMSE1953',np.sqrt((e1**2).mean()).round(2),'tie-RMSE vs4071',np.sqrt((e2**2).mean()).round(2))
c=np.float32([[3850,3830]]); p=pt(Hm,np.vstack([c,c+[100,0],c+[0,100]])); print('m/px',np.linalg.norm(p[1]-p[0])/100,np.linalg.norm(p[2]-p[0])/100)
Hf['4053']=Hm.tolist(); json.dump(Hf,open('Hfinal.json','w'))

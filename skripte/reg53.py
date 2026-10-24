import numpy as np, cv2, json
res=json.load(open('reg.json'))
Z2R=np.array([[2,0,-2100],[0,2,-1900],[0,0,1.]])
ref53=cv2.imread('r53.jpg',0); Hh,Ww=ref53.shape
cl=cv2.createCLAHE(2.0,(16,16))
def prep(im):
  im=cl.apply(im); g=cv2.GaussianBlur(im,(0,0),1.5)
  gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1)
  return cv2.GaussianBlur(np.sqrt(gx*gx+gy*gy),(0,0),1.0)
f71=cv2.imread('frame_full.jpg',0); m71=np.zeros_like(f71); m71[480:7230,640:7380]=255
H71=np.array(res['4071']['H'])
w71=cv2.warpPerspective(f71,H71,(Ww,Hh),flags=cv2.INTER_AREA); c71=cv2.warpPerspective(m71,H71,(Ww,Hh),flags=cv2.INTER_NEAREST)
R71=prep(w71); R53=prep(ref53)
fr=cv2.imread('f4053.jpg',0); bb=(470,520,7230,7140); mask=np.zeros_like(fr); mask[bb[1]:bb[3],bb[0]:bb[2]]=255
Hm=Z2R@np.vstack([np.load('o53a.jpg.M.npy'),[0,0,1]])
for it in range(4):
  w=cv2.warpPerspective(fr,Hm,(Ww,Hh),flags=cv2.INTER_AREA); wm=cv2.warpPerspective(mask,Hm,(Ww,Hh),flags=cv2.INTER_NEAREST)
  W=prep(w); src=[];dst=[];kind=[]
  win=48; srch=[110,50,20,15][it]
  for y in range(srch+win,Hh-srch-win,36):
    for x in range(srch+win,Ww-srch-win,36):
      if wm[y-win-srch:y+win+srch,x-win-srch:x+win+srch].min()==0: continue
      t=W[y-win:y+win,x-win:x+win]
      if t.std()<4: continue
      use71=c71[y-win-srch:y+win+srch,x-win-srch:x+win+srch].min()>0
      R=R71 if use71 else R53
      s=R[y-win-srch:y+win+srch,x-win-srch:x+win+srch]
      c=cv2.matchTemplate(s,t,cv2.TM_CCOEFF_NORMED); _,mx,_,ml=cv2.minMaxLoc(c)
      if mx<(0.45 if use71 else 0.35): continue
      c2=c.copy(); cv2.circle(c2,ml,8,-1,-1)
      if mx-c2.max()<0.06: continue
      p=np.linalg.inv(Hm)@np.array([x,y,1.]); p/=p[2]
      src.append(p[:2]); dst.append([x+ml[0]-srch,y+ml[1]-srch]); kind.append(use71)
  src=np.float32(src); dst=np.float32(dst); kind=np.array(kind)
  Hn,inl=cv2.findHomography(src,dst,cv2.RANSAC,[10,6,4,4][it],maxIters=30000); inl=inl.ravel().astype(bool)
  pr=cv2.perspectiveTransform(src[inl][None],Hn)[0]; err=np.linalg.norm(pr-dst[inl],axis=1)
  print('it',it,'matches',len(src),'(vs4071',int(kind.sum()),') inliers',inl.sum(),'(vs4071',int(kind[inl].sum()),') RMSE',round(float(np.sqrt((err**2).mean())),2))
  Hm=Hn
c=np.array([3850,3830.]); pts=cv2.perspectiveTransform(np.float32([[c,c+[100,0],c+[0,100]]]),Hm)[0]
print('m/px',np.linalg.norm(pts[1]-pts[0])/100,np.linalg.norm(pts[2]-pts[0])/100)
res['4053']=dict(H=Hm.tolist(),inl=[src[inl].tolist(),dst[inl].tolist()],rmse=float(np.sqrt((err**2).mean())),n=int(inl.sum()))
json.dump(res,open('reg.json','w'))

import numpy as np, cv2, json
A4071=np.array([[7.37221801e-02,-5.67742052e-02,1.78551927e+03],[5.67742052e-02,7.37221801e-02,7.85960850e+02]])
frames={'4071':('frame_full.jpg',A4071,(640,480,7380,7230)),'4053':('f4053.jpg',np.load('o53a.jpg.M.npy'),(470,520,7230,7140)),'3054':('f3054.jpg',np.load('o54a.jpg.M.npy'),(520,420,7230,7180))}
Z2R=np.array([[2,0,-2100],[0,2,-1900],[0,0,1.]])  # z53 px -> r53 px (1 m)
ref=cv2.imread('r53.jpg',0)
cl=cv2.createCLAHE(2.0,(16,16))
def prep(im):
  im=cl.apply(im); g=cv2.GaussianBlur(im,(0,0),1.5)
  gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1)
  return cv2.GaussianBlur(np.sqrt(gx*gx+gy*gy),(0,0),1.0)
R=prep(ref); Hh,Ww=ref.shape
res={}
for name,(fn,M,bb) in frames.items():
  fr=cv2.imread(fn,0)
  mask=np.zeros_like(fr); mask[bb[1]:bb[3],bb[0]:bb[2]]=255
  Hm=Z2R@np.vstack([M,[0,0,1]])   # frame->r53 initial (similarity)
  for it in range(3):
    w=cv2.warpPerspective(fr,Hm,(Ww,Hh),flags=cv2.INTER_AREA)
    wm=cv2.warpPerspective(mask,Hm,(Ww,Hh),flags=cv2.INTER_NEAREST)
    W=prep(w)
    src=[];dst=[];sc=[]
    win=48 if it==0 else 40; srch=60 if it==0 else 20
    for y in range(srch+win,Hh-srch-win,40):
      for x in range(srch+win,Ww-srch-win,40):
        if wm[y-win-srch:y+win+srch,x-win-srch:x+win+srch].min()==0: continue
        t=W[y-win:y+win,x-win:x+win]
        if t.std()<4: continue
        s=R[y-win-srch:y+win+srch,x-win-srch:x+win+srch]
        c=cv2.matchTemplate(s,t,cv2.TM_CCOEFF_NORMED)
        _,mx,_,ml=cv2.minMaxLoc(c)
        if mx<0.35: continue
        # distinctiveness: second peak
        c2=c.copy(); cv2.circle(c2,ml,8,-1,-1); m2=c2.max()
        if mx-m2<0.06: continue
        dx=ml[0]-srch; dy=ml[1]-srch
        p=np.array([x,y,1.]); f=np.linalg.inv(Hm)@p; f/=f[2]
        src.append(f[:2]); dst.append([x+dx,y+dy]); sc.append(mx)
    src=np.float32(src); dst=np.float32(dst)
    Hn,inl=cv2.findHomography(src,dst,cv2.RANSAC,6.0 if it<2 else 4.0,maxIters=20000)
    inl=inl.ravel().astype(bool)
    pr=cv2.perspectiveTransform(src[inl][None],Hn)[0]; err=np.linalg.norm(pr-dst[inl],axis=1)
    print(name,'it',it,'matches',len(src),'inliers',inl.sum(),'RMSE m',round(float(np.sqrt((err**2).mean())),2))
    Hm=Hn
  # scale at frame centre
  c=np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2])
  pts=cv2.perspectiveTransform(np.float32([[c,c+[100,0],c+[0,100]]]),Hm)[0]
  print(name,'m/px x',round(np.linalg.norm(pts[1]-pts[0])/100,4),'y',round(np.linalg.norm(pts[2]-pts[0])/100,4))
  res[name]=dict(H=Hm.tolist(),inl=[src[inl].tolist(),dst[inl].tolist()],rmse=float(np.sqrt((err**2).mean())),n=int(inl.sum()))
json.dump(res,open('reg.json','w'))

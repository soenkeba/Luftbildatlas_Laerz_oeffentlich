import numpy as np, cv2, json, sys
res=json.load(open('reg.json'))
def load(fn,bb):
  im=cv2.imread(fn,0); m=np.zeros_like(im); m[bb[1]:bb[3],bb[0]:bb[2]]=255
  s=0.5; return cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_AREA), cv2.resize(m,None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST), s
sift=cv2.SIFT_create(40000)
def feats(fn,bb):
  im,m,s=load(fn,bb); im=cv2.createCLAHE(2.0,(8,8)).apply(im)
  k,d=sift.detectAndCompute(im,m); return np.float32([p.pt for p in k])/s,d
pairs=[('4053','f4053.jpg',(470,520,7230,7140),'4071','frame_full.jpg',(640,480,7380,7230)),('3054','f3054.jpg',(520,420,7230,7180),'4071','frame_full.jpg',(640,480,7380,7230))]
out={}
for a,fa,ba,b,fb,bbb in pairs:
  ka,da=feats(fa,ba); kb,db=feats(fb,bbb)
  m=cv2.FlannBasedMatcher(dict(algorithm=1,trees=5),dict(checks=64)).knnMatch(da,db,k=2)
  g=[x for x,y in m if x.distance<0.75*y.distance]
  P=ka[[x.queryIdx for x in g]]; Q=kb[[x.trainIdx for x in g]]
  H,inl=cv2.findHomography(P,Q,cv2.RANSAC,8.0,maxIters=50000); inl=inl.ravel().astype(bool)
  e=np.linalg.norm(cv2.perspectiveTransform(P[inl][None],H)[0]-Q[inl],axis=1)
  print(a,'->',b,'good',len(g),'inliers',inl.sum(),'rmse px',e.std().round(2), 'rmse m', round(float(np.sqrt((e**2).mean()))*0.18,2))
  out[a]=dict(H=H.tolist(),n=int(inl.sum()),P=P[inl].tolist(),Q=Q[inl].tolist())
json.dump(out,open('sift.json','w'))

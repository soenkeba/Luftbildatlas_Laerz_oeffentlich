import numpy as np, cv2, json
Hf=json.load(open('Hfinal.json'))
files={'3054':('f3054.jpg',(520,420,7230,7180)),'4071':('frame_full.jpg',(640,480,7380,7230)),'4053':('f4053.jpg',(470,520,7230,7140))}
r=0.5; X0,Y0,X1,Y1=700,800,1700,1700
W,H=int((X1-X0)/r),int((Y1-Y0)/r)
S=np.array([[r,0,X0],[0,r,Y0],[0,0,1.]])
mos=np.zeros((H,W),np.float32); cov=np.zeros((H,W),bool)
for n,(fn,bb) in files.items():
  im=cv2.imread(fn,0)
  m=np.zeros_like(im); m[bb[1]+30:bb[3]-30,bb[0]+30:bb[2]-30]=255
  T=np.linalg.inv(S)@np.array(Hf[n])
  w=cv2.warpPerspective(im,T,(W,H),flags=cv2.INTER_AREA).astype(np.float32)
  mm=cv2.warpPerspective(m,T,(W,H),flags=cv2.INTER_NEAREST)>0
  sel=mm&~cov; mos[sel]=w[sel]; cov|=mm
mos=cv2.createCLAHE(2.5,(8,8)).apply(mos.astype(np.uint8))
cv2.imwrite('mos45.png',mos); np.save('mos45_cov.npy',cov); json.dump(dict(r=r,X0=X0,Y0=Y0),open('mos45.json','w'))
s=cv2.resize(mos,None,fx=0.65,fy=0.65,interpolation=cv2.INTER_AREA); cv2.imwrite('mos45_prev.jpg',s); print(W,H)

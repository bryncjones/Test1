import io, math, urllib.request, numpy as np
from PIL import Image
z=12
def tx(lon): return int((lon+180)/360*2**z)
def ty(lat): r=math.radians(lat); return int((1-math.log(math.tan(r)+1/math.cos(r))/math.pi)/2*2**z)
x0,x1,y0,y1=tx(-4.45),tx(-4.16),ty(51.17),ty(51.06)
rows=[]
for y in range(y0,y1+1):
  row=[]
  for x in range(x0,x1+1):
    b=urllib.request.urlopen(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png").read()
    a=np.asarray(Image.open(io.BytesIO(b)).convert('RGB')).astype(float)
    row.append(a[...,0]*256+a[...,1]+a[...,2]/256-32768)
  rows.append(np.hstack(row))
e=np.vstack(rows); print(e.shape, (x0,x1,y0,y1))
np.save('terrarium.npy',e); 
# sample a west-east profile through middle row
r=e[e.shape[0]//2]; print(np.round(r[::16],1))
v=np.clip((e+40)/80,0,1); Image.fromarray((v*255).astype(np.uint8)).save('terrarium.png')

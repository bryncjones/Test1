import os, re, urllib.request, numpy as np, rasterio, concurrent.futures as cf
from rasterio.windows import from_bounds
from pyproj import Transformer
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CURL_CA_BUNDLE='/root/.ccr/ca-bundle.crt', GDAL_HTTP_MULTIRANGE='YES')
B='https://sentinel-cogs.s3.us-west-2.amazonaws.com'
W,S,E,N=-4.32,51.06,-4.16,51.17
t=Transformer.from_crs(4326,32630,always_xy=True)
xs,ys=zip(*[t.transform(x,y) for x in (W,E) for y in (S,N)])
bb=(min(xs),min(ys),max(xs),max(ys))
scenes=[]
for y in (2023,2024,2025):
  for m in range(4,10):
    xml=urllib.request.urlopen(f"{B}/?list-type=2&prefix=sentinel-s2-l2a-cogs/30/U/VB/{y}/{m}/&delimiter=/").read().decode()
    scenes+=re.findall(r"<Prefix>(sentinel-s2-l2a-cogs/30/U/VB/\d+/\d+/[^<]+/)</Prefix>",xml)
def score(p):
  try:
    with rasterio.open(f"/vsicurl/{B}/{p}SCL.tif") as d:
      a=d.read(1,window=from_bounds(*bb,d.transform))
    if a.size==0: return None
    nod=(a==0).mean(); cl=np.isin(a,[3,8,9,10]).mean()
    return p, round(float(cl),4), round(float(nod),3)
  except Exception as e: return p, 'err', str(e)[:60]
with cf.ThreadPoolExecutor(12) as ex:
  res=[r for r in ex.map(score,scenes) if r]
ok=sorted([r for r in res if r[1]!='err' and r[2]<0.01], key=lambda r:r[1])
print(len(scenes), 'scenes'); [print(r) for r in ok[:10]]
print([r for r in res if r[1]=='err'][:3])

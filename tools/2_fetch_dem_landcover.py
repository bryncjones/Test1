import os, numpy as np, rasterio
from rasterio.windows import from_bounds
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CURL_CA_BUNDLE='/root/.ccr/ca-bundle.crt')
W,S,E,N=-4.33,51.05,-4.15,51.18
u='/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N51_00_W005_00_DEM/Copernicus_DSM_COG_10_N51_00_W005_00_DEM.tif'
with rasterio.open(u) as d:
  win=from_bounds(W,S,E,N,d.transform).round_offsets().round_lengths(); a=d.read(1,window=win); tr=d.window_transform(win)
  print(d.res, a.shape, tr)
np.save('glo30.npy',a); np.save('glo30_tr.npy',np.array(tr)[:6])
# row through Saunton ~51.10
r=int((N-51.10)/abs(tr.e)); print(np.round(a[r, ::6],1))
u2='/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N51W006_Map.tif'
with rasterio.open(u2) as d:
  win=from_bounds(W,S,E,N,d.transform).round_offsets().round_lengths(); c=d.read(1,window=win); tr2=d.window_transform(win)
  print(d.res, c.shape, np.unique(c, return_counts=True))
np.save('wc.npy',c); np.save('wc_tr.npy',np.array(tr2)[:6])

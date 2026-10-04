import os, json, math, numpy as np, rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from scipy import ndimage as ndi
from PIL import Image, ImageFilter
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CURL_CA_BUNDLE='/root/.ccr/ca-bundle.crt')
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'); os.makedirs(OUT, exist_ok=True)
LAT0, LON0 = 51.115, -4.24
M_LAT = 111250.0; M_LON = 111320.0*math.cos(math.radians(LAT0))
W_, E_, S_, N_ = -4.32, -4.16, 51.06, 51.17
CELL = 12.5
x0 = (W_-LON0)*M_LON; x1 = (E_-LON0)*M_LON; z0 = -(N_-LAT0)*M_LAT; z1 = -(S_-LAT0)*M_LAT
GW = int(round((x1-x0)/CELL))+1; GH = int(round((z1-z0)/CELL))+1
xs = x0+np.arange(GW)*CELL; zs = z0+np.arange(GH)*CELL
lon = LON0 + xs/M_LON; lat = LAT0 - zs/M_LAT
LON, LAT = np.meshgrid(lon, lat)
print('grid', GW, GH)

def sample_geo(arr, tr, lons, lats, order=1):
    # tr: affine of a lon/lat raster (pixel corner origin)
    c = (lons - tr[2]) / tr[0] - 0.5; r = (lats - tr[5]) / tr[4] - 0.5
    return ndi.map_coordinates(arr.astype(np.float32), [r, c], order=order, mode='nearest')

g = np.load('glo30.npy'); gt = np.load('glo30_tr.npy')
dem = sample_geo(g, gt, LON, LAT)
# Sentinel-2 bands (UTM 30N) resampled to our grid via lon/lat -> utm
from pyproj import Transformer
T = Transformer.from_crs(4326, 32630, always_xy=True)
UX, UY = T.transform(LON, LAT)
B='/vsicurl/https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/30/U/VB/2023/9/S2A_30UVB_20230904_0_L2A/'
def s2(band, order=1):
    with rasterio.open(B+band+'.tif') as d:
        bb = (UX.min()-200, UY.min()-200, UX.max()+200, UY.max()+200)
        win = from_bounds(*bb, d.transform).round_offsets().round_lengths()
        a = d.read(window=win); t = d.window_transform(win)
    c = (UX - t.c)/t.a - 0.5; r = (UY - t.f)/t.e - 0.5
    return np.stack([ndi.map_coordinates(a[i].astype(np.float32), [r, c], order=order, mode='nearest') for i in range(a.shape[0])])
green = s2('B03')[0]; swir = s2('B11')[0]
mndwi = (green - swir) / np.maximum(green + swir, 1)
water_img = mndwi > 0.15
landD = dem > 0.5
# sea = cells with dem==0 connected to west edge
lab, n = ndi.label(~landD)
seaIds = set(np.unique(lab[:, 0])) - {0}
sea = np.isin(lab, list(seaIds))
# water at image time, only within the sea region; remove small dry islands (foam) not touching land
wimg = water_img & sea
dry = sea & ~wimg
dl, dn = ndi.label(dry)
touch = set(np.unique(dl[ndi.binary_dilation(landD, iterations=1) & dry])) - {0}
dry = np.isin(dl, list(touch))
wimg = sea & ~dry
# imaged waterline tide level (estimate; Sentinel overpass ~11:20 UTC 4 Sep 2023)
L_IMG = -1.8; HW = 3.6
dA = ndi.distance_transform_edt(~landD) * CELL           # distance from dune/cliff edge
dB = ndi.distance_transform_edt(~wimg) * CELL            # distance (on dry) to imaged water
dW = ndi.distance_transform_edt(wimg) * CELL             # distance (in water) from imaged waterline
wc = np.load('wc.npy'); wct = np.load('wc_tr.npy')
cls = sample_geo(wc, wct, LON, LAT, order=0).astype(np.uint8)
sandy = ndi.gaussian_filter(((cls == 60) | dry).astype(np.float32), 25)
sandy = np.clip(sandy*4, 0, 1)
te = np.load('terrarium.npy')
# terrarium z12 grid: tiles x 1997..2000, y 1368..1370
z = 12; n2 = 2**z
def merc_px(lons, lats):
    px = (lons+180)/360*n2*256 - 1997*256
    r = np.radians(lats); py = (1-np.log(np.tan(r)+1/np.cos(r))/np.pi)/2*n2*256 - 1368*256
    return px, py
px, py = merc_px(LON, LAT)
terr = ndi.map_coordinates(ndi.gaussian_filter(te, 4), [py-0.5, px-0.5], order=1, mode='nearest')
bed = dem.copy()
it = dry
bed[it] = L_IMG + (HW - L_IMG) * dB[it] / np.maximum(dA[it] + dB[it], 1)
# subtidal: synthetic shoreface below the imaged waterline, blended into measured depths offshore
d = dW
rng = np.random.default_rng(1)
nz = ndi.gaussian_filter(rng.standard_normal(bed.shape), 30)*8
synth_sand = L_IMG - (6*(1-np.exp(-d/650)) + 0.0035*d) + 0.75*np.exp(-((d-150)/60)**2) + 0.5*np.exp(-((d-380)/100)**2)*(1+0.3*nz)
synth_rock = L_IMG - (12*(1-np.exp(-d/300)) + 0.004*d)
synth = synth_sand*sandy + synth_rock*(1-sandy)
w = np.clip((d-600)/1200, 0, 1); w = w*w*(3-2*w)
deep = np.minimum(terr, L_IMG - 2)
sub = wimg
bed[sub] = (synth*(1-w) + deep*w)[sub]
bed[sub] = np.minimum(bed[sub], L_IMG - 0.05)
# smooth sea part lightly to remove raster steps, keep land untouched
sm = ndi.gaussian_filter(bed, 1.2)
bed[sea] = sm[sea]
print('bed range', bed.min(), bed.max(), 'dry cells', dry.sum(), 'water', wimg.sum())
np.save('bed.npy', bed); np.save('cls.npy', cls)
(np.clip(np.round(bed*10), -32768, 32767).astype('<i2')).tofile(f'{OUT}/terrain.bin')
# ---- imagery at 5 m: true colour, stretched; subtidal water replaced with seabed sand

iw, ih = int(round((x1-x0)/5))+1, int(round((z1-z0)/5))+1
lonI = LON0 + (x0+np.arange(iw)*5)/M_LON; latI = LAT0 - (z0+np.arange(ih)*5)/M_LAT
LONI, LATI = np.meshgrid(lonI, latI)
UXI, UYI = T.transform(LONI, LATI)
with rasterio.open(B+'TCI.tif') as dd:
    bb = (UXI.min()-200, UYI.min()-200, UXI.max()+200, UYI.max()+200)
    win = from_bounds(*bb, dd.transform).round_offsets().round_lengths()
    a = dd.read(window=win).astype(np.float32); t = dd.window_transform(win)
c = (UXI - t.c)/t.a - 0.5; r = (UYI - t.f)/t.e - 0.5
rgb = np.stack([ndi.map_coordinates(a[i], [r, c], order=3, mode='nearest') for i in range(3)], -1)
# masks on image grid
gx = (LONI - lon[0]) / (lon[1]-lon[0]); gy = (LATI - lat[0]) / (lat[1]-lat[0])
subI = ndi.map_coordinates(sub.astype(np.float32), [gy, gx], order=1) > 0.5
bedI = ndi.map_coordinates(bed, [gy, gx], order=1)
landI = ndi.map_coordinates((~sea).astype(np.float32), [gy, gx], order=1) > 0.5
lin = (np.clip(rgb, 0, 255)/255.0)**2.2
# per-channel stretch from land/intertidal percentiles
ref = lin[~subI]
lo = np.percentile(ref, 0.5, axis=0); hi = np.percentile(ref, 99.7, axis=0)
lin = np.clip((lin - lo) / (hi - lo), 0, 1)
out = lin**(1/2.2)
out = np.clip((out - 0.5) * 1.08 + 0.5 + 0.03, 0, 1)
# seabed colour: wet sand from the imaged intertidal, darkening with depth
dryI = ~subI & ~landI
sandcol = np.median(out[dryI], axis=0) if dryI.any() else np.array([0.62, 0.56, 0.44])
print('sand colour', sandcol)
dep = np.clip((L_IMG - bedI)/12, 0, 1)[..., None]
nI = ndi.gaussian_filter(rng.standard_normal(bedI.shape), 3)[..., None]*0.03
seab = sandcol*(1-dep*0.55) + np.array([0.18, 0.22, 0.2])*dep*0.55 + nI
fe = ndi.gaussian_filter(subI.astype(np.float32), 3)[..., None]
out = out*(1-fe) + seab*fe
Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8)).save(f'{OUT}/imagery.jpg', quality=86, optimize=True, progressive=True)
# landcover at 10 m (nearest), as 8-bit codes
lw, lh = int(round((x1-x0)/10))+1, int(round((z1-z0)/10))+1
lonL = LON0 + (x0+np.arange(lw)*10)/M_LON; latL = LAT0 - (z0+np.arange(lh)*10)/M_LAT
LL, LT = np.meshgrid(lonL, latL)
clsL = sample_geo(wc, wct, LL, LT, order=0).astype(np.uint8)
gxL = (LL - lon[0])/(lon[1]-lon[0]); gyL = (LT - lat[0])/(lat[1]-lat[0])
dryL = ndi.map_coordinates(dry.astype(np.float32), [gyL, gxL], order=0) > 0.5
clsL[dryL] = 61   # intertidal sand (own code)
Image.fromarray(clsL).save(f'{OUT}/landcover.png', optimize=True)
meta = dict(lat0=LAT0, lon0=LON0, mPerDegLat=M_LAT, mPerDegLon=M_LON, cell=CELL, W=GW, H=GH,
            xmin=x0, zmin=z0, xmax=x0+(GW-1)*CELL, zmax=z0+(GH-1)*CELL, bounds=dict(west=W_, east=E_, south=S_, north=N_),
            elevation=dict(file='terrain.bin', type='int16le', scale=0.1, units='m above mean sea level'),
            imagery=dict(file='imagery.jpg', width=iw, height=ih, cellM=5, scene='S2A_30UVB_20230904_0_L2A'),
            landcover=dict(file='landcover.png', width=lw, height=lh, cellM=10),
            imagedWaterlineTideM=L_IMG)
json.dump(meta, open(f'{OUT}/meta.json','w'), indent=1)
Image.fromarray((np.clip((bed+30)/80,0,1)*255).astype(np.uint8)).save('bed.png')
print(meta['W'], meta['H'], iw, ih)

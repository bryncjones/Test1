# Saunton Sands 3D

A 3D surf view of Saunton Sands, Croyde, Putsborough and Woolacombe in North Devon. It is built on real elevation, satellite imagery and land-cover data, with a live swell, wind and tide forecast. `index.html` plus the `data/` folder is the whole app, built on three.js with no build step.

## What it shows

- **Real terrain:** Copernicus GLO-30 elevation and Sentinel-2 imagery, with ESA WorldCover land cover adding fine texture close up.
- **Real-ish seabed:** a modelled shoreface (sandbars on sandy coast, steeper off rock) blended into coarse measured depths offshore.
- **Refracted swell:**
  - The main swell bends towards shallow water, shoals and breaks at 0.78 × depth.
  - Headlands cast a shelter shadow over a ±20° directional spread.
  - Broken waves run up the sand.
- **Forecast:**
  - Seven days of hourly data from Open-Meteo (swell, a second swell, wind and sea level including tide).
  - A play-through scrubber and a tide curve with high and low water times.
  - Wind is rated against the direction each beach faces.
- **Breaking height in the model** for each spot, shown in the panel and as map labels. The second swell is added by energy. These numbers are the model's own, not a tuned surf forecast.
- **Light:** the real sun position for the chosen day and hour, plus a sky with clouds that drives the water reflections and haze.
- **Views:** Whole area, Saunton Sands, On the beach, In the line-up, Saunton Down and From above.

## Run it

```sh
python3 -m http.server 8000
# open http://localhost:8000/
```

GitHub Pages also works. Deploy from the branch root.

The page fetches its own `data/` files, so open it through a web server rather than as a file.

The forecast comes straight from Open-Meteo in the browser. It is free for non-commercial use and needs no key. Pages hosted on claude.ai block outside requests, so the forecast only works when the page is self-hosted. Elsewhere the "Try your own swell" sliders still work.

## Sharper imagery (optional)

Sentinel-2 is 10 m per pixel. Under **Sharper imagery** you can paste a Mapbox public token or a MapTiler key to drape 1.5–3 m aerial imagery over the land and beach. The key stays in your browser. Restrict it to your site's URL in the provider's dashboard, and don't commit it.

## Data and credits

| Layer | Source | Notes |
|---|---|---|
| Land elevation | Copernicus DEM GLO-30 | About 30 m. It is a surface model, so woods and buildings stand up. Resampled to 12.5 m. |
| Imagery | Sentinel-2 L2A true colour, scene `S2A_30UVB_20230904_0_L2A` | 10 m, colour-stretched. Water below the imaged waterline is replaced with a seabed colour. |
| Land cover | ESA WorldCover 2021 v200 | 10 m. Used only for close-up surface detail. |
| Offshore depths | AWS Terrain Tiles (Tilezen) | Coarse; smoothed and blended in beyond about 0.6–1.8 km from shore. |
| Forecast | Open-Meteo marine and weather APIs | Point at 51.12°N 4.40°W. Its sea level is less reliable near coasts. |

Credit lines:

- Contains modified Copernicus Sentinel data 2023.
- Copernicus DEM GLO-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
- ESA WorldCover 2021 © ESA, CC BY 4.0.
- Forecast data by Open-Meteo.com, CC BY 4.0.

Check each provider's current terms before any public or commercial use.

### Rebuilding `data/`

The scripts in `tools/` regenerate `data/` from the open buckets. They need Python with `rasterio pyproj mgrs numpy scipy pillow packaging`.

1. `1_pick_scene.py` scores Sentinel-2 scenes by cloud over the area.
2. `2_fetch_dem_landcover.py` and `3_fetch_bathymetry.py` download the elevation, land cover and coarse depths.
3. `4_bake.py` writes `terrain.bin` (int16, decimetres), `imagery.jpg`, `landcover.png` and `meta.json`.

Run them from the same working directory. The spot coordinates in `meta.json` were placed by hand against the imagery, so re-add them after a rebuild.

## Known limits

- **Higher-resolution sources are not used.** The original Hang Ten app uses Environment Agency 1 m lidar and EMODnet bathymetry. Neither was reachable from the environment this was built in, so the terrain is coarser and the near-shore seabed is modelled rather than surveyed. `4_bake.py` is the place to swap them in.
- **Beach slope is estimated.** It assumes the dune foot is at +3.6 m and the imaged waterline at −1.8 m. The second figure is a guess, because the tide at the image time wasn't checked.
- **Elevation datum.** Heights are relative to the EGM2008 geoid, treated as mean sea level, which may be off locally by a few tenths of a metre.
- **No diffraction, currents or wind-wave growth.** Lees come out quieter than reality. Only the main swell is drawn.
- **MapTiler is unverified.** Its tile URL follows its published pattern but wasn't tested here.

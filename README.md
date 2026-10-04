# Saunton Sands 3D

A 3D, browser-based view of Saunton Sands in North Devon with animated surf. It is a single file (`index.html`) built on three.js and has no build step.

## What it does

- **Terrain**: by default, a hand-built approximate model of the coast: Saunton Down, the beach, Braunton Burrows dunes, fields and the Taw/Torridge mouth. It is not survey data. With a Mapbox or MapTiler key, the app instead loads real aerial imagery and elevation tiles for the area (about 51.065–51.135°N, 4.18–4.29°W).
- **Waves**:
  - Swell is refracted over the seabed. An eikonal solver finds the crest pattern from the linear dispersion relation, so crests bend towards the beach and shorten in shallow water.
  - Waves shoal, then break once their height passes about 0.78 × the water depth. Broken waves run up the sand as bores with foam.
  - Swell height, period and direction, tide and wind chop are all adjustable.
- **Light**: the sun position comes from the date and the Saunton time of day. A procedural sky with clouds drives the water reflections, terrain lighting, wet-sand sheen and haze.
- **Views**: Overview, On the beach, In the line-up and Saunton Down.

## Run it

The tile servers need a normal web origin, so serve the folder over HTTP rather than opening the file directly:

```sh
python3 -m http.server 8000
# then open http://localhost:8000/
```

GitHub Pages also works. In the repo settings, go to Pages and deploy from the branch root.

## Satellite terrain

1. Open **Satellite terrain** in the panel.
2. Pick a provider and paste your key:
   - **Mapbox**: a public access token (`pk.…`). Uses the `mapbox.satellite` and `mapbox.terrain-rgb` raster tilesets.
   - **MapTiler**: an API key. Uses `satellite-v2` and `terrain-rgb-v2`.
3. Press **Load satellite**. The first load downloads roughly 36 elevation tiles and 36–144 imagery tiles.

The key lives only in your browser (in `localStorage` if "Remember on this device" is ticked) and is sent only to the provider you choose. Don't commit a key to this repo. Restrict the token to your site's URL in the provider's dashboard.

Elevation tiles carry little or no seabed detail along this coast. Below the low-water line, the app synthesises a gentle sandy profile with two sandbars, and keeps any deeper measured values.

## Known limits

- The modelled terrain is approximate and drawn from general knowledge of the area. Use satellite mode for the real shape.
- The seabed is synthetic in both modes. Wave refraction and breaking positions are therefore plausible, not a forecast.
- The tide slider range (±3.8 m) is a rough approximation of the local spring range. Check real tide tables for actual heights.
- The MapTiler tile URLs and its terrain-RGB encoding follow MapTiler's published patterns, but this build was only tested against Mapbox-format mock tiles. Verify against current MapTiler docs if loading fails.
- claude.ai-hosted previews block requests to map servers, so satellite mode only works when the page is self-hosted.
- Attribution strings shown in the app may need adjusting to the provider's current requirements.

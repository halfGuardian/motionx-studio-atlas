# MotionX Studio Atlas v0.5 — public prototype

Public-facing interactive world map of motion capture, previsualization, VFX, animation and game-related studios. This version contains a **provisional, non-exhaustive research seed** of 18 location records across 16 organisations. Entries are **not independently re-verified in this release** and neither operation nor registration status should be assumed.

## Deploy with GitHub Pages
1. Create a **public** repository called `motionx-studio-atlas`.
2. Add these files to the repository root (including `index.html`).
3. In GitHub, open **Settings → Pages**. Under **Build and deployment**, choose **Deploy from a branch**, branch **main**, folder **/(root)**, and Save.
4. Visit `https://YOUR-USERNAME.github.io/motionx-studio-atlas/` once the deployment completes.

This is a static site. The map uses Leaflet and standard OpenStreetMap tiles over HTTPS, which require an internet connection. No Google Maps API key is needed. Respect the OSM tile usage policy; transition to a production map tile provider before launch or significant traffic.

## Data maintenance
- Edit `studios.json` for the canonical public research seed.
- Validate: `python tools/validate.py studios.json --report data/validation_report.json`.
- For now, `index.html` carries an embedded snapshot of the seed to support opening on a phone. After editing `studios.json`, **regenerate the embedded snapshot** or the map will still show the old data. The next milestone is to automate that publication step.
- CSV research batch template: `data/research_template.csv`.
- Source links do not independently guarantee operating status, corporate registration, geolocation accuracy, or capabilities.

## Security
This repository contains **only the public directory and non-sensitive research**. The former local-only MotionX private dashboard demo was removed from this build. Do **not** commit private leads, outreach notes, client intelligence, API keys, or personal data. Secure authentication and private infrastructure will be developed separately.

## Legal / operations
Do not import third-party directories without checking usage rights and licenses. Public business contact information should be checked against official sources.

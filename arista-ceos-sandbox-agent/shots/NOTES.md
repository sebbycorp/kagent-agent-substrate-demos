# arista-ceos shots

**No live artifacts yet.** This directory stays empty of PNG/GIF/txt
captures until the Containerlab fabric has been deployed on Viper and
someone records **that** session.

## What is accepted

- Real Chromium `--headless=new --screenshot` (or a real interactive
  capture) of a tunneled or LAN kagent UI **after** the agent exists
- Real CLI dumps (`containerlab inspect`, `./scripts/02-verify.sh`,
  `docker exec … Cli`) saved as `.txt`
- A date/time and the host (Viper) in the commit message or a short
  note in this file

## What is rejected

- Reconstructed GIFs or “sample” UI frames
- AI-generated topology pictures presented as a live run
- Hand-typed `show ip bgp summary` that was not copied from a device
- Screenshots that show `.env`, Vault tokens, eAPI basic-auth headers,
  or `username … secret …` lines
- Stock photos of Arista hardware

If a file lands here without a live provenance note, delete it.
Do not invent a `cli-live-status.txt` to look finished.

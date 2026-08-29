# Upload Assistant — Jediten Fork

[![Docker build](https://github.com/Jediten/Upload-Assistant/actions/workflows/docker-image.yml/badge.svg?branch=main)](https://github.com/Jediten/Upload-Assistant/actions/workflows/docker-image.yml)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

Upload Assistant automates release preparation, metadata collection, screenshots, torrent creation, duplicate checking, tracker-specific naming, uploading, and client integration for private trackers.

This independently maintained fork keeps the established Upload Assistant workflow while incorporating compatible critical fixes from the [official Audionut project](https://github.com/Audionut/Upload-Assistant) and maintaining additional trackers and workflow customizations.

The official project is in development freeze and directs future upstream development to [autobrr/upbrr](https://github.com/autobrr/upbrr). This fork is not the official successor to Upload Assistant or affiliated with upbrr.

## Fork Highlights

- Additional and updated tracker support, including Diginette, MidnightScene, NordicQuality, PeerGarden, TorrentHaven, and Zenith.
- Interactive review before imported tracker descriptions or screenshots are accepted—even when a tracker ID was supplied explicitly.
- Declining imported screenshots clears the imported image metadata and all cached PNG files for that release, preventing stale screenshots from being reused.
- Unattended mode remains automatic and does not stop for these review prompts.
- TV release years are used as title disambiguators instead of being added unconditionally. `--force-year` adds one explicitly and `--no-year` always removes it.
- InfinityHD and DarkPeers retain their customized TMDB title and title/AKA/year ordering while sharing the same TV-year decision as the core name generator.
- PTP posters are rehosted through the selected image host instead of assuming PTPImg is available.
- The WebUI exposes the fork's trackers and tracker-reference arguments, including Diginette.
- Current compatible critical fixes from upstream are included, covering TVDB metadata, IMDb editions, PTP poster rehosting, Nebulance duplicate handling, and ImmortalSeed upload detection.

## Features

- Parses MediaInfo and BDInfo and generates tracker-specific release names.
- Collects TMDB, IMDb, TVDB, TVMaze, and MyAnimeList metadata.
- Generates and uploads screenshots, including HDR tone mapping and comparison workflows.
- Imports IDs, descriptions, and screenshots from supported tracker references.
- Checks for existing releases, banned groups, tracker requirements, and matching requests.
- Creates new torrents or reuses compatible torrents already present in supported clients.
- Supports qBittorrent, rTorrent, Deluge, Transmission, watch folders, and [qui](https://github.com/autobrr/qui) workflows.
- Supports movies, television, anime numbering, Blu-ray, DVD, HD DVD, remuxes, encodes, WEB releases, and HDTV releases.
- Provides CLI, queue, site-check, Emby, Docker, WebUI, and authenticated HTTP API workflows.

## Supported Trackers

The tracker registry currently contains 76 upload targets. Availability and account requirements are controlled through `data/config.py`; a listed integration does not imply that tracker registration is open or that every account has upload permission.

| Tracker | Code | Tracker | Code |
|---|:---:|---|:---:|
| Aither | `AITHER` | Alpharatio | `AR` |
| Amigos-Share | `ASC` | Anthelion | `ANT` |
| AsianCinema | `ACM` | Aura4K | `A4K` |
| AvistaZ | `AZ` | Beyond-HD | `BHD` |
| BitHDTV | `BHDTV` | Blutopia | `BLU` |
| BrasilJapão-Share | `BJS` | BrasilTracker | `BT` |
| CapybaraBR | `CBR` | Cinematik | `TIK` |
| CinemaZ | `CZ` | DarkPeers | `DP` |
| DesiTorrents | `DT` | Diginette | `DIGI` |
| DigitalCore | `DC` | Emuwarez | `EMUW` |
| FileList | `FL` | Friki | `FRIKI` |
| FunFile | `FF` | GreatPosterWall | `GPW` |
| hawke-uno | `HUNO` | HD-Space | `HDS` |
| HD-Torrents | `HDT` | HDBits | `HDB` |
| HomieHelpDesk | `HHD` | ImmortalSeed | `IS` |
| InfinityHD | `IHD` | ItaTorrents | `ITT` |
| KoKoCon | `KKC` | LastDigitalUnderground | `LDU` |
| Lat-Team | `LT` | Locadora | `LCD` |
| LST | `LST` | Luminarr | `LUME` |
| MidnightScene | `MNS` | MoreThanTV | `MTV` |
| Nebulance | `NBL` | NetHD | `NETHD` |
| NordicQuality | `NQ` | OldToonsWorld | `OTW` |
| OnlyEncodes+ | `OE` | PassThePopcorn | `PTP` |
| PeerGarden | `PG` | PolishTorrent | `PTT` |
| Portugas | `PT` | PrivateHD | `PHD` |
| PTerClub | `PTER` | PTSKIT | `PTS` |
| Racing4Everyone | `R4E` | Rastastugan | `RAS` |
| ReelFLiX | `RF` | RetroFlix | `RTF` |
| Samaritano | `SAM` | seedpool | `SP` |
| ShareIsland | `SHRI` | SkipTheCommercials | `STC` |
| SpeedApp | `SPD` | Swarmazon | `SN` |
| The Leach Zone | `TLZ` | TheOldSchool | `TOS` |
| Torrenteros | `TTR` | TorrentHaven | `THV` |
| TorrentHR | `THR` | TorrentLeech | `TL` |
| ToTheGlory | `TTG` | TVChaosUK | `TVC` |
| ULCX | `ULCX` | UTOPIA | `UTP` |
| VietMediaF | `VMF` | YOiNKED | `YOINK` |
| YUSCENE | `YUS` | Zenith | `ZNTH` |

## Requirements

- Python 3.9 or newer and `pip`. The included Dockerfile currently uses Python 3.12.
- [MediaInfo](https://mediaarea.net/en/MediaInfo) and [FFmpeg](https://ffmpeg.org/) available on `PATH`.
- A TMDB API key.
- Credentials, API keys, announce URLs, or cookies for the trackers and services you use.
- At least one operational image host for workflows that require hosted screenshots or posters.

PTPImg is retired and Imgbox is unavailable until its service returns, so both are skipped by default even if an older config still lists them. This is controlled by `disabled_image_hosts`; remove Imgbox from that setting if it becomes operational again. Configure multiple operational hosts with `img_host_1`, `img_host_2`, and `img_host_3` so uploads can fall back cleanly.

## Installation

Clone this fork and enter its directory:

```bash
git clone https://github.com/Jediten/Upload-Assistant.git
cd Upload-Assistant
```

Using a virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Create or update your configuration:

```bash
python config-generator.py
```

Alternatively, copy `data/example-config.py` to `data/config.py` and edit the copy. Keep `data/example-config.py` unchanged so the generator and WebUI can discover new options. The WebUI creates `data/config.py` automatically for first-time users.

Configuration fields are documented in [docs/example-config.md](docs/example-config.md). Obtain a TMDB API key from [TMDB account settings](https://www.themoviedb.org/settings/api).

## Updating This Fork

This fork is maintained on `main`; do not switch to an upstream release tag if you want to retain its tracker additions and custom behavior.

```bash
cd Upload-Assistant
git checkout main
git pull --ff-only origin main
python -m pip install -r requirements.txt
python config-generator.py
```

Review local changes before pulling. `data/config.py` contains your settings and should not be replaced with `data/example-config.py`.

## CLI Usage

```text
python upload.py "/path/to/content" [options]
```

Arguments follow the content path. Run `python upload.py --help` for the complete generated help or see [docs/cli-args.md](docs/cli-args.md).

Examples:

```bash
# Prepare one release for selected trackers
python upload.py "/data/movies/Example Movie (2026)" --trackers IHD,DIGI,DP

# Supply an existing Diginette torrent as a metadata reference
python upload.py "/data/tv/Example Show" --digi https://diginette.org/torrents/12345

# Start the WebUI with one allowed browse root
python upload.py "/data/torrents" --webui 127.0.0.1:5000
```

## Imported Tracker Data

Tracker references can supply external IDs, descriptions, screenshots, and torrent hashes. The supported reference arguments are documented in [docs/cli-args.md](docs/cli-args.md#tracker-specific-references-existing-torrent-idslinks).

During an interactive CLI or WebUI run:

- Imported descriptions are presented for editing, discarding, or keeping.
- Imported screenshots require confirmation before they replace generated screenshots.
- Declining imported screenshots clears their metadata and deletes every cached PNG in that release's `tmp/<uuid>/` directory.

In `--unattended` mode, imported data is accepted automatically. Use `--onlyID` when you want metadata IDs without importing description text; screenshot reuse remains governed by the relevant image settings.

## WebUI and API

Start the built-in WebUI with a browse root and bind address:

```bash
python upload.py "/data/torrents" --webui 127.0.0.1:5000
```

For Docker or more controlled deployments, set `UA_BROWSE_ROOTS` to a comma-separated list of directories the UI is allowed to expose. Bind to localhost unless remote access is intentionally protected by appropriate network controls or an authenticated reverse proxy.

- [WebUI guide](docs/web-ui-basic.md)
- [WebUI API reference](docs/web-ui-api.md)
- [Docker WebUI guide](docs/docker-gui-wiki-full.md)
- [Unraid guide](docs/unraid-wiki-full.md)

## Docker

The repository includes a Dockerfile, Compose example, multi-architecture build workflow, and WebUI entrypoint. To guarantee that the container contains this fork's changes, build the checked-out source locally:

```bash
docker build -t upload-assistant-jediten:local .
```

The existing Docker documentation and Compose examples may reference the official upstream image. Substitute your locally built image—or a verified image published from this fork—when you need the fork-specific trackers and behavior.

- [Docker CLI guide](docs/docker-wiki-full.md)
- [Docker WebUI/Compose guide](docs/docker-gui-wiki-full.md)

## Security and Configuration Notes

- Never commit `data/config.py`, tracker cookies, passkeys, API keys, session secrets, or WebUI authentication files.
- Restrict WebUI browse roots to only the paths Upload Assistant needs.
- Prefer a virtual environment or container instead of installing Python dependencies globally.
- Keep multiple image hosts configured and verify their current availability.
- Tracker rules and API behavior change independently of this repository; review generated names and upload data before submission.

## Documentation

- [Configuration reference](docs/example-config.md)
- [CLI arguments](docs/cli-args.md)
- [WebUI guide](docs/web-ui-basic.md)
- [WebUI API](docs/web-ui-api.md)
- [Docker CLI](docs/docker-wiki-full.md)
- [Docker WebUI](docs/docker-gui-wiki-full.md)
- [Unraid](docs/unraid-wiki-full.md)
- [Official Upload Assistant wiki](https://github.com/Audionut/Upload-Assistant/wiki)

## Support

Report fork-specific bugs and tracker integration issues through this repository's [GitHub issues](https://github.com/Jediten/Upload-Assistant/issues). The [upstream Discord](https://discord.gg/QHHAZu7e2A) remains a community resource, but fork-specific changes may not be supported there.

## Attribution

This project descends from the original work by [L4G](https://github.com/L4GSP1KE/Upload-Assistant) and the extensive continued development by [Audionut](https://github.com/Audionut/Upload-Assistant), wastaken7, and the wider Upload Assistant contributor community.

Upload Assistant uses or integrates with projects and services including [BDInfoCLI-ng](https://github.com/rokibhasansagar/BDInfoCLI-ng), [mkbrr](https://github.com/autobrr/mkbrr), [qui](https://github.com/autobrr/qui), FFmpeg, MediaInfo, TMDB, IMDb, TVDB, and TVMaze.

The repository is distributed under the terms in [LICENSE](LICENSE).

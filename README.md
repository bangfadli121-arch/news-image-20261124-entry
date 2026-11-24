# Tuesday 24 November 2026 — The World in One Page

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/bangfadli121-arch/news-image-20261124-entry/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/bangfadli121-arch/news-image-20261124-entry/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A one-page newspaper front page that sums up the world's news of
**Tuesday 24 November 2026** in a single 1024×1024 image.

## What is on the page

- **Giant date headline** — Tuesday 24 November 2026, the day the page sums up.
- **Three hero stories** — Nvidia brings Jensen Huang back as CEO and
  shares soar 31%; a Russian drone strike collapses a Dymer apartment
  block, 11 dead; a candy-plant fire in Cikande, Banten kills 24.
  Each has a hand-drawn illustration.
- **Six big numbers** — +31% Nvidia shares, $952bn value gained in a
  day, 24 dead in the Banten factory fire, 11 dead in the Dymer flat
  strike, 99% of Gaza shows contamination, 1,448 Dow points gained.
- **Where the news was** — stories counted by region.
- **Ten small cards** with mini illustrations — Sparta II, Gaza, Lisbon,
  O'Hare, Verstappen, Alcaraz, the India–Nepal train, BepiColombo at
  Mercury, the Sensex, Ferrari's new 296s.
- **Where it happened** — a structured table of the places in today's news.
- **Also on Tuesday** — 22 more stories, numbered, for a total of 35.
- **Date check** — the COP31 collapse in Antalya is deliberately left
  out: it was yesterday's front page.

Every story happened, or was first reported, on Tuesday 24 November 2026.
All drawings are original, drawn procedurally with Pillow. No photos.

## How it runs

`draw.py` draws `entry.png` at build time (Pillow, 4x supersampling
downscaled with LANCZOS for smooth HD edges). `main.py` is the
entrypoint: it copies `entry.png` to `/output/entry.png` (or
`$MAKEFUN_OUTPUT_DIR/entry.png`). Standard library only, no network,
so two runs write byte-identical output.

```sh
python3 draw.py            # redraw entry.png
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Sources

Reuters, CNN, AP, Al Jazeera, Oxfam/CEOBS, FAA, ESA, The Indian Express.
Attributions are printed on the page itself.

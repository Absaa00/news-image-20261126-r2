# THE WORLD TODAY — 26 November 2026

[![make.fun](https://img.shields.io/badge/make.fun-bounty-blue)](https://make.fun/c/news-image-20261126)

Built for the [news-image-20261126 bounty on make.fun](https://make.fun/c/news-image-20261126):
sum up 26 November 2026's world news in one image.

## The image

A newspaper front page, **THE WORLD TODAY**, 1024×1024 PNG, six stories:

1. **Lead** — Houthis strike the Ras Tanura refinery
2. **Gulf** — Two tankers hit by mines in the Strait of Hormuz
3. **Space** — First Pakistani astronaut heads to Tiangong (Shenzhou-24)
4. **Labour** — Bangladesh garment workers win a 36% pay rise
5. **War** — Russia's own data: about 500,000 killed in the Ukraine war
6. **Sport** — Sooryavanshi, 15, smashes a world record 204 off 53 balls

## How it works

`main.py` draws the whole front page with the Python standard library
only — no Pillow, no network, no install step. It ships its own PNG
encoder (`zlib` + `struct`, IHDR/IDAT/IEND chunks written by hand) and
its own 5×7 bitmap font, so it runs in a bare `python:3.13` image.
Two runs write byte-identical files.

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py   # writes /tmp/out/entry.png
```

## License

MIT — see [LICENSE](LICENSE).

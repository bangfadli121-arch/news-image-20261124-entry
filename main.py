#!/usr/bin/env python3
"""Entry program for news-image-20261124 (Koran 24).

Copies the pre-rendered front page ``entry.png`` to the output
directory. Standard library only: nothing is installed before this
program runs in the grading sandbox, so it must not import Pillow
or any other third-party package.

The image itself was drawn at build time by ``draw.py`` (Pillow,
4x supersampling, deterministic: no network, no clock, no
randomness) and saved as ``entry.png`` next to this file. This
program only copies those bytes, so every run produces an
identical file.
"""
import os
import shutil
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    out = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, out)
    print("wrote", out, os.path.getsize(out), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Regenerates everything: pack JSON and 3D models, icons and textures, sounds.

Usage:  python3 tools/gen/generate.py [--preview]
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for script in ("content.py", "art.py", "audio.py"):
    subprocess.run([sys.executable, str(HERE / script), *sys.argv[1:]], check=True)
if "--preview" in sys.argv:
    subprocess.run([sys.executable, str(HERE / "preview.py")], check=True)
    subprocess.run([sys.executable, str(HERE / "viewer.py")], check=True)

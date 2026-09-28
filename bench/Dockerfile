# Benchmark backend: the game, the renderer, and the publisher in one image.
# Videos and the catalogue go to the bucket through the Python client, which
# reads the service account off the metadata server, so the gcloud CLI (and the
# ~350MB it costs) is not installed.

# The emulator core is pinned, not pulled fresh. The libretro nightly at
# .../latest/dosbox_pure_libretro.so.zip is unversioned: it was re-published on
# 2026-09-10 15:00 UTC with a build that stalls the opening's attribute roll, so
# every image built after that could not author a start state. This stage is
# the last image whose core authored the opening reliably; the core is copied
# from it by digest below. To move the core deliberately, build that image from
# a known-good `latest`, smoke-test authoring, and bump this digest.
FROM us-central1-docker.pkg.dev/jinaai-dev/cloud-run-source-deploy/jy-crpg-bench@sha256:147bf0feb1c31992839bd4d96b99aea5f239f912315c3d7307da6cb1fa7597b2 AS core

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Sources/CoreHost /app/Sources/CoreHost
COPY server /app/server
COPY bench /app/bench
COPY skills /app/skills
COPY assets/game-data.tar.gz /app/assets/game-data.tar.gz

# the emulator core, pinned to the digest above rather than pulled from the
# libretro nightly `latest`, which is unversioned and drifts. The shim the
# server loads dlopens this at runtime, so it is not needed to build the shim.
COPY --from=core /app/cores/dosbox_pure_libretro.so /app/cores/dosbox_pure_libretro.so
RUN sh /app/server/build.sh
RUN tar xzf /app/assets/game-data.tar.gz -C /app && rm /app/assets/game-data.tar.gz

# Pinned so a rebuild reproduces the tested backend; these are the versions the
# code was exercised against. Pillow is held below 14, which removes
# Image.getdata, used by the progress reader.
RUN pip install --no-cache-dir \
      aiohttp==3.14.3 pillow==12.3.0 numpy==2.2.6 google-cloud-storage==3.14.1

# The world map the measure places route frames on, rendered from the game's
# own data files; every session process memory-maps the one copy.
RUN cd /app/server && python -m measure.worldmap /app/game /app/measure-cache

# Stamped at build time so the running backend can say which build it is, and
# the leaderboard can show it. Defaults to "dev" for a local image.
ARG QUNXIA_VERSION=dev
ENV QUNXIA_VERSION=$QUNXIA_VERSION \
    QUNXIA_PYTHON=/usr/local/bin/python \
    QUNXIA_CORE=/app/cores/dosbox_pure_libretro.so \
    QUNXIA_GAME=/app/game/PLAY.BAT \
    QUNXIA_START_STATE=/app/saves/start.state \
    QUNXIA_VIDEO_DIR=/app/videos \
    QUNXIA_RESULT_DIR=/app/videos/results \
    QUNXIA_CATALOG=/app/videos/catalog.json \
    QUNXIA_WORLDMAP_CACHE=/app/measure-cache \
    PYTHONPATH=/app/bench \
    PYTHONUNBUFFERED=1 \
    PORT=8080
EXPOSE 8080
CMD ["python", "/app/bench/broker.py"]

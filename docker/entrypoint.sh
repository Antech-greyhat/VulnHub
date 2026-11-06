#!/bin/sh
set -e
# First boot only: keep the data across restarts. `labctl reset` reseeds it.
python seed.py --if-missing
exec python run.py

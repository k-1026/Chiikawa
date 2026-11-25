#!/bin/zsh
cd "$(dirname "$0")" || exit 1
python3 -u backend/server_v06.py --port 8002

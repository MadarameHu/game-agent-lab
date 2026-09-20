#!/bin/zsh
cd -- "${0:A:h}"
python3 tools/serve.py --port 8766

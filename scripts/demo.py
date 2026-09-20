#!/usr/bin/env python3
"""Build local evidence data and start the 12-case viewer."""
import argparse
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8769)
    args = parser.parse_args()
    demo = ROOT / 'examples/game-trajectory-demo'
    runpy.run_path(str(demo / 'build_data.py'), run_name='__main__')
    sys.argv = [str(demo / 'server.py'), '--port', str(args.port)]
    runpy.run_path(str(demo / 'server.py'), run_name='__main__')

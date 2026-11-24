#!/usr/bin/env python3


import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from game.app import GameApp


def main():
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()

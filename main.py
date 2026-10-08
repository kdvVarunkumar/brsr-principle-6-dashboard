"""Entry point. Run:  python main.py --company "Tata Steel" --fy 2023-24

Kept deliberately tiny: all the real work lives inside the brsr_p6 package.
"""

import sys

from brsr_p6.cli import main

if __name__ == "__main__":
    sys.exit(main())

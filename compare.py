"""Entry point: python compare.py --company-a "Tata Steel" --company-b "Wipro" --fy 2025-26 --open

(A tiny file on purpose: the work is done in the brsr_p6 package.)"""

import sys

from brsr_p6.cli.compare_cli import main

if __name__ == "__main__":
    sys.exit(main())

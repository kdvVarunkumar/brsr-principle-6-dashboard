"""Entry point: python trends.py --company "Tata Steel" --from 2021-22 --to 2025-26 --open

(A tiny file on purpose: the work is done in the brsr_p6 package.)"""

import sys

from brsr_p6.trend_cli import main

if __name__ == "__main__":
    sys.exit(main())

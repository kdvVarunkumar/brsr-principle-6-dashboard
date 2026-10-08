"""Download BRSR filings from NSE.   Run:  python download_filings.py --company Reliance

Kept deliberately tiny: the real work lives inside the brsr_p6 package.
"""

import sys

from brsr_p6.download_cli import main

if __name__ == "__main__":
    sys.exit(main())

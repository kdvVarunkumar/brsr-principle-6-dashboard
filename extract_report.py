"""Clean a company's BRSR filing into the SEBI Principle 6 layout.   Run:  python extract_report.py --company Reliance --fy 2023-24

Kept deliberately tiny: the real work lives inside the brsr_p6 package.
"""

import sys

from brsr_p6.extract_cli import main

if __name__ == "__main__":
    sys.exit(main())

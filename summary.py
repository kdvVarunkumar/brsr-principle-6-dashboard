"""Entry point: python summary.py --company "Tata Steel" --open

(A tiny file on purpose: the work is done in the brsr_p6 package.)"""

import sys

from brsr_p6.summary_cli import main

if __name__ == "__main__":
    sys.exit(main())

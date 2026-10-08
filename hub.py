"""Entry point: python hub.py --open      (every page in output/ behind one page with a dropdown and a search box)

(A tiny file on purpose: the work is done in the brsr_p6 package.)"""

import sys

from brsr_p6.cli.hub_cli import main

if __name__ == "__main__":
    sys.exit(main())

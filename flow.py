"""The one command.  Run:  python flow.py --company "Tata Steel" --fy 2025-26 --open

That is the whole flow: download the filing from NSE, read it, clean and check it, write one HTML page (plain-English dashboard + SEBI-format report).
`python flow.py --help` lists the other commands (download, extract, trends, summary, compare, hub, samples).

Kept deliberately tiny: all the real work lives inside the brsr_p6 package.
"""

import sys

from brsr_p6.cli.flow_cli import main

if __name__ == "__main__":
    sys.exit(main())

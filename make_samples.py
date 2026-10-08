"""Rebuild the sample pages in samples/ :  python make_samples.py   (a tiny entry point; the work is in brsr_p6/samples.py)"""

import sys

from brsr_p6.samples import make_samples

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pages = make_samples()
    print(f"\n{len(pages)} sample pages are in the samples/ folder (see samples/README.md).")

"""What every command does when it fails: say what went wrong, and write an explanation page where the report would have been."""

import webbrowser

from brsr_p6.core.errors import BrsrError
from brsr_p6.rendering.render import write_error_page
from brsr_p6.views.error_view import build_error_view


def explain_failure(error, company_text, fy_text, output_dir, open_page, tool="main") -> int:
    """Print the problem and write the error page.  Returns the exit code (1 = something went wrong).

    Shared by main.py, trends.py and summary.py; `tool` ("main", "trends" or "summary") makes the suggested commands use that command."""
    if isinstance(error, BrsrError):
        print(f"Error: {error}")
    else:
        print(f"Unexpected problem ({type(error).__name__}: {error}). Run again with --debug to see the details.")
    try:
        page = write_error_page(build_error_view(error, company_text, fy_text, tool), company_text, fy_text, output_dir)
    except OSError as problem:   # even the explanation page could not be saved (for example a read-only folder)
        print(f"(Could not write the explanation page: {problem})")
        return 1
    print(f"An explanation page was written to: {page}")
    if open_page:
        webbrowser.open(page.as_uri())
    return 1

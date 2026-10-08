"""A cheap way to catch template mistakes: every opening tag must be closed, in the right order."""

from html.parser import HTMLParser

VOID_TAGS = {"meta", "br", "input", "link", "hr", "img"}


class TagBalance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.problems = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"unexpected </{tag}> (open: {self.stack[-3:]})")
        else:
            self.stack.pop()


def assert_well_formed(html):
    checker = TagBalance()
    checker.feed(html)
    assert checker.problems == [] and checker.stack == []

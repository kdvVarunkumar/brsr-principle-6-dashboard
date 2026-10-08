"""Helpers that build tiny, fake BRSR XBRL files for the tests (so tests never depend on downloaded data)."""

HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:link="http://www.xbrl.org/2003/linkbase" '
    'xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:in-capmkt="https://www.sebi.gov.in/xbrl/{release}/in-capmkt">\n'
    '<link:schemaRef xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="x.xsd"/>\n'
)

BASE_CONTEXTS = (
    '<xbrli:context id="DCYMain"><xbrli:entity><xbrli:identifier scheme="s">INE000</xbrli:identifier></xbrli:entity>'
    '<xbrli:period><xbrli:startDate>2023-04-01</xbrli:startDate><xbrli:endDate>2024-03-31</xbrli:endDate></xbrli:period></xbrli:context>\n'
    '<xbrli:context id="DPYMain"><xbrli:entity><xbrli:identifier scheme="s">INE000</xbrli:identifier></xbrli:entity>'
    '<xbrli:period><xbrli:startDate>2022-04-01</xbrli:startDate><xbrli:endDate>2023-03-31</xbrli:endDate></xbrli:period></xbrli:context>\n'
)


def context(context_id, axis, member, year="current", instant=False):
    """A context that carries one extra row label (axis=member)."""
    end = "2024-03-31" if year == "current" else "2023-03-31"
    start = "2023-04-01" if year == "current" else "2022-04-01"
    period = f"<xbrli:instant>{end}</xbrli:instant>" if instant else f"<xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate>"
    return (
        f'<xbrli:context id="{context_id}"><xbrli:entity><xbrli:identifier scheme="s">INE000</xbrli:identifier>'
        f'<xbrli:segment><xbrldi:explicitMember dimension="in-capmkt:{axis}">in-capmkt:{member}</xbrldi:explicitMember></xbrli:segment>'
        f"</xbrli:entity><xbrli:period>{period}</xbrli:period></xbrli:context>\n"
    )


def fact(tag, value, context_id="DCYMain", unit=""):
    unit_attr = f' unitRef="{unit}"' if unit else ""
    return f'<in-capmkt:{tag} contextRef="{context_id}"{unit_attr}>{value}</in-capmkt:{tag}>\n'


def both_years(tag, current, previous, unit=""):
    return fact(tag, current, "DCYMain", unit) + fact(tag, previous, "DPYMain", unit)


def build_xbrl(facts="", release="2024-04-30", extra_contexts="", raw_extra=""):
    return HEAD.format(release=release) + BASE_CONTEXTS + extra_contexts + facts + raw_extra + "</xbrli:xbrl>\n"


def write_xbrl(tmp_path, facts="", release="2024-04-30", extra_contexts="", raw_extra="", name="filing.xml", as_bytes=None):
    path = tmp_path / name
    if as_bytes is not None:
        path.write_bytes(as_bytes)
    else:
        path.write_text(build_xbrl(facts, release, extra_contexts, raw_extra), encoding="utf-8")
    return path

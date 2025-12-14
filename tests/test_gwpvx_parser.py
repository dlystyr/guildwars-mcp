"""Tests for parsing PvE builds from GWPvX."""

from guildwars_mcp.wiki_parser import parse_pve_builds, format_pve_builds_response


def test_parse_pve_builds_primary_selector():
    """Ensure we can parse build links from the modern Fandom layout."""
    html = """
    <div class="category-page__members">
        <a class="category-page__member-link" href="/wiki/Build:Mo/W_General_Survivor">Mo/W General Survivor</a>
        <a class="category-page__member-link" href="/wiki/Build:Me/N_Farming_SS">Me/N Farming SS</a>
    </div>
    """
    builds = parse_pve_builds(html)
    assert len(builds) == 2
    assert builds[0]["name"] == "Mo/W General Survivor"
    assert builds[0]["url"].endswith("Build:Mo/W_General_Survivor")


def test_format_pve_builds_response_limit():
    """Ensure formatting respects limits and reports totals."""
    builds = [
        {"name": "Build A", "url": "https://gwpvx.fandom.com/wiki/Build_A"},
        {"name": "Build B", "url": "https://gwpvx.fandom.com/wiki/Build_B"},
        {"name": "Build C", "url": "https://gwpvx.fandom.com/wiki/Build_C"},
    ]
    text = format_pve_builds_response("farming", builds, limit=2)
    assert "Build A" in text and "Build C" not in text
    assert "Showing first 2 builds of 3 total." in text

"""Tests for the Guild Wars Wiki MCP server."""

import pytest
from guildwars_mcp.wiki_parser import fetch_wiki_page, parse_quest_page


@pytest.mark.asyncio
async def test_fetch_wiki_page():
    """Test fetching a known quest page."""
    html = await fetch_wiki_page("The_Path_to_Glory")
    assert html is not None
    assert "Path to Glory" in html


@pytest.mark.asyncio
async def test_parse_quest():
    """Test parsing a quest page."""
    html = await fetch_wiki_page("Against_the_Charr")
    if html:
        quest_data = parse_quest_page(html, "Against the Charr")
        assert quest_data["found"] is True
        # Add more specific assertions based on the quest

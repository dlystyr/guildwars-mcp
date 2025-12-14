"""Wiki parsing utilities for Guild Wars Wiki and PvX builds."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

WIKI_BASE_URL = "https://wiki.guildwars.com/wiki"
USER_AGENT = "GuildWars-MCP-Bot/1.0 (Educational; Python)"
GWPVX_BASE_URL = "https://gwpvx.fandom.com/wiki"

# Category slugs for PvE builds on GWPvX
PVE_BUILD_CATEGORIES = {
    "general": "Category:All_working_general_builds",
    "farming": "Category:All_working_farming_builds",
    "running": "Category:All_working_running_builds",
    "quest": "Category:All_working_quest_builds",
    "hero": "Category:All_working_hero_builds",
    "speedclear": "Category:All_working_SC_builds",
    "teams": "Category:All_working_PvE_team_builds",
}


async def fetch_wiki_page(page_name: str) -> Optional[str]:
    """Fetch a wiki page by name."""
    url = f"{WIKI_BASE_URL}/{page_name.replace(' ', '_')}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching wiki page: {e}")
            return None


async def fetch_gwpvx_page(path: str) -> Optional[str]:
    """Fetch a GWPvX page by path."""
    url = f"{GWPVX_BASE_URL}/{path}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True
            )
            if response.status_code == 200:
                return response.text
            logger.warning(f"Failed to fetch {url}: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching GWPvX page: {e}")
            return None


def parse_quest_page(html: str, quest_name: str) -> Dict[str, Any]:
    """Parse a quest page and extract structured information."""
    soup = BeautifulSoup(html, 'lxml')
    
    result = {
        "name": quest_name,
        "found": True,
        "objectives": None,
        "rewards": None,
        "walkthrough": None,
        "notes": None,
    }
    
    # Extract objectives
    objectives_header = soup.find('span', id='Objectives')
    if objectives_header:
        objectives_section = objectives_header.find_parent()
        objectives_list = objectives_section.find_next_sibling(['ul', 'ol'])
        if objectives_list:
            result["objectives"] = [li.get_text(strip=True) for li in objectives_list.find_all('li')]
    
    # Extract rewards
    reward_header = soup.find('span', id='Reward')
    if reward_header:
        reward_section = reward_header.find_parent()
        reward_list = reward_section.find_next_sibling(['ul', 'ol'])
        if reward_list:
            result["rewards"] = [li.get_text(strip=True) for li in reward_list.find_all('li')]
    
    # Extract walkthrough/guide
    walkthrough_header = soup.find('span', id='Walkthrough')
    if walkthrough_header:
        walkthrough_section = walkthrough_header.find_parent()
        # Get the next few paragraphs/lists
        walkthrough_content = []
        for sibling in walkthrough_section.find_next_siblings():
            if sibling.name in ['h2', 'h3']:  # Stop at next header
                break
            if sibling.name in ['p', 'ul', 'ol']:
                walkthrough_content.append(sibling.get_text(strip=True))
        result["walkthrough"] = "\n".join(walkthrough_content) if walkthrough_content else None
    
    # Extract notes
    notes_header = soup.find('span', id='Notes')
    if notes_header:
        notes_section = notes_header.find_parent()
        notes_list = notes_section.find_next_sibling(['ul', 'ol'])
        if notes_list:
            result["notes"] = [li.get_text(strip=True) for li in notes_list.find_all('li')]
    
    return result


def format_quest_response(quest_data: Dict[str, Any]) -> str:
    """Format quest data into a readable response."""
    if not quest_data["found"]:
        return f"Quest '{quest_data['name']}' not found in the Guild Wars Wiki."
    
    response = f"# {quest_data['name']}\n\n"
    
    if quest_data["objectives"]:
        response += "## Objectives\n"
        for obj in quest_data["objectives"]:
            response += f"- {obj}\n"
        response += "\n"
    
    if quest_data["rewards"]:
        response += "## Rewards\n"
        for reward in quest_data["rewards"]:
            response += f"- {reward}\n"
        response += "\n"
    
    if quest_data["walkthrough"]:
        response += "## Walkthrough\n"
        response += quest_data["walkthrough"]
        response += "\n\n"
    
    if quest_data["notes"]:
        response += "## Notes\n"
        for note in quest_data["notes"]:
            response += f"- {note}\n"
    
    return response


def parse_skill_page(html: str, skill_name: str) -> Dict[str, Any]:
    """Parse a skill page and extract information."""
    soup = BeautifulSoup(html, 'lxml')
    
    result = {
        "name": skill_name,
        "found": True,
        "type": None,
        "profession": None,
        "attribute": None,
        "campaign": None,
        "energy": None,
        "activation": None,
        "recharge": None,
        "description": None,
    }
    
    # Look for the skill infobox
    infobox = soup.find('table', class_='skill-box')
    if not infobox:
        result["found"] = False
        return result
    
    # Extract basic info from infobox
    # Note: The actual structure varies, you'll need to inspect the wiki
    rows = infobox.find_all('tr')
    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) >= 2:
            header = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            
            if 'profession' in header:
                result["profession"] = value
            elif 'attribute' in header:
                result["attribute"] = value
            elif 'energy' in header:
                result["energy"] = value
            elif 'activation' in header:
                result["activation"] = value
            elif 'recharge' in header:
                result["recharge"] = value
    
    # Get skill description
    description_div = soup.find('div', class_='skill-description')
    if description_div:
        result["description"] = description_div.get_text(strip=True)
    
    return result


def format_skill_response(skill_data: Dict[str, Any]) -> str:
    """Format skill data into a readable response."""
    if not skill_data["found"]:
        return f"Skill '{skill_data['name']}' not found in the Guild Wars Wiki."
    
    response = f"# {skill_data['name']}\n\n"
    
    if skill_data["profession"]:
        response += f"**Profession:** {skill_data['profession']}\n"
    if skill_data["attribute"]:
        response += f"**Attribute:** {skill_data['attribute']}\n"
    if skill_data["campaign"]:
        response += f"**Campaign:** {skill_data['campaign']}\n"
    
    response += "\n**Stats:**\n"
    if skill_data["energy"]:
        response += f"- Energy: {skill_data['energy']}\n"
    if skill_data["activation"]:
        response += f"- Activation: {skill_data['activation']}\n"
    if skill_data["recharge"]:
        response += f"- Recharge: {skill_data['recharge']}\n"
    
    if skill_data["description"]:
        response += f"\n**Description:**\n{skill_data['description']}\n"
    
    return response


def parse_pve_builds(html: str) -> list[Dict[str, str]]:
    """Parse a GWPvX category page for PvE builds."""
    soup = BeautifulSoup(html, "lxml")
    builds: list[Dict[str, str]] = []

    # Newer Fandom layout
    for link in soup.select("a.category-page__member-link"):
        name = link.get_text(strip=True)
        href = link.get("href", "")
        if href and href.startswith("/"):
            href = f"{GWPVX_BASE_URL}{href}"
        builds.append({"name": name, "url": href})

    # Fallback to legacy category lists
    if not builds:
        for link in soup.select("div#mw-pages li a"):
            name = link.get_text(strip=True)
            href = link.get("href", "")
            if href and href.startswith("/"):
                href = f"{GWPVX_BASE_URL}{href}"
            builds.append({"name": name, "url": href})

    return builds


def format_pve_builds_response(category: str, builds: list[Dict[str, str]], limit: Optional[int] = None) -> str:
    """Format PvE builds into a readable response."""
    if not builds:
        return f"No builds found for category '{category}'."

    sliced = builds[:limit] if limit else builds
    response = f"# PvE builds - {category.title()}\n\n"
    for build in sliced:
        name = build.get("name", "Unknown build")
        url = build.get("url", "")
        response += f"- {name}"
        if url:
            response += f" — {url}"
        response += "\n"
    if limit and len(builds) > limit:
        response += f"\nShowing first {limit} builds of {len(builds)} total."
    return response

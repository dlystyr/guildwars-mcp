"""Guild Wars Wiki MCP Server with SSE support."""

import asyncio
import logging
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn

from .wiki_parser import (
    fetch_wiki_page,
    parse_quest_page,
    format_quest_response,
    parse_skill_page,
    format_skill_response,
    fetch_gwpvx_page,
    parse_pve_builds,
    format_pve_builds_response,
    PVE_BUILD_CATEGORIES,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp_server = Server("guildwars-wiki")
# Create a single SSE transport shared across requests
sse_transport = SseServerTransport("/messages/")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_quest_info",
            description="Gets detailed information about a Guild Wars quest including objectives, rewards, and walkthrough. Use this when users ask about specific quests.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quest_name": {
                        "type": "string",
                        "description": "The exact name of the quest (e.g., 'Against the Charr', 'The Path to Glory')"
                    }
                },
                "required": ["quest_name"]
            }
        ),
        Tool(
            name="get_skill_info",
            description="Gets information about a specific Guild Wars skill including stats, profession, attribute, and description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "The exact name of the skill (e.g., 'Meteor Shower', 'Healing Breeze')"
                    }
                },
                "required": ["skill_name"]
            }
        ),
        Tool(
            name="get_pve_builds",
            description="Gets PvE build names from the GWPvX wiki by category (e.g., farming, running, hero, speedclear).",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "One of: general, farming, running, quest, hero, speedclear, teams"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optional limit for number of builds to return (e.g., 10)"
                    }
                },
                "required": ["category"]
            }
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_quest_info":
            quest_name = arguments["quest_name"]
            logger.info(f"Fetching quest info for: {quest_name}")
            
            html = await fetch_wiki_page(quest_name)
            
            if html is None:
                return [TextContent(
                    type="text",
                    text=f"Could not fetch information for quest '{quest_name}'. The quest may not exist or there was a network error."
                )]
            
            quest_data = parse_quest_page(html, quest_name)
            response_text = format_quest_response(quest_data)
            
            return [TextContent(type="text", text=response_text)]
        
        elif name == "get_skill_info":
            skill_name = arguments["skill_name"]
            logger.info(f"Fetching skill info for: {skill_name}")
            
            html = await fetch_wiki_page(skill_name)
            
            if html is None:
                return [TextContent(
                    type="text",
                    text=f"Could not fetch information for skill '{skill_name}'. The skill may not exist or there was a network error."
                )]
            
            skill_data = parse_skill_page(html, skill_name)
            response_text = format_skill_response(skill_data)
            
            return [TextContent(type="text", text=response_text)]

        elif name == "get_pve_builds":
            category = arguments["category"].lower()
            limit = arguments.get("limit")

            if category not in PVE_BUILD_CATEGORIES:
                valid = ", ".join(PVE_BUILD_CATEGORIES.keys())
                return [TextContent(
                    type="text",
                    text=f"Invalid category '{category}'. Valid options: {valid}"
                )]

            logger.info(f"Fetching PvE builds for category: {category}")
            path = PVE_BUILD_CATEGORIES[category]
            html = await fetch_gwpvx_page(path)

            if html is None:
                return [TextContent(
                    type="text",
                    text=f"Could not fetch PvE builds for category '{category}'."
                )]

            builds = parse_pve_builds(html)
            response_text = format_pve_builds_response(category, builds, limit)

            return [TextContent(type="text", text=response_text)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error handling tool call: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# SSE endpoint handler
async def handle_sse(request):
    """Handle SSE connection for MCP."""
    logger.info("New SSE connection")
    
    async with sse_transport.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )
    
    return Response()


# Health check endpoint
async def health_check(request):
    """Health check endpoint."""
    return Response(
        content='{"status": "healthy"}',
        media_type="application/json"
    )


# Create Starlette app
app = Starlette(
    routes=[
        Route("/sse", handle_sse),
        Mount("/messages/", app=sse_transport.handle_post_message),
        Route("/health", health_check),
    ]
)


def run():
    """Run the SSE server."""
    logger.info("Starting Guild Wars Wiki MCP server with SSE transport")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    run()

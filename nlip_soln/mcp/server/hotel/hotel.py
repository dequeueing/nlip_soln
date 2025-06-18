from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("hotel")


@mcp.tool()
async def book_hotel(message: str) -> str:
    """Book a hotel.

    Args:
        message: The message to book a hotel
    """
    return f"Hotel Echo: {message}"

@mcp.tool()
async def hotel_info() -> str:
    """Get basic hotel information."""
    return "Welcome to the Simple Hotel Service! This is a server for testing purposes."


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")

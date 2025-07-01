# LangChain Demo - MCP Alternative

This demo showcases how to use **LangChain** to achieve the same functionality as the MCP (Model Context Protocol) implementation. It provides weather tools, hotel booking tools, and chat session management using LangChain's agent framework.

## Architecture Comparison

### MCP Version
- Uses MCP Client/Server protocol
- Tools defined as MCP servers
- Ollama integration via direct API calls
- NLIP message handling

### LangChain Version  
- Uses LangChain agents and tools
- Tools defined as LangChain `@tool` decorators
- Ollama integration via `ChatOllama`
- Same NLIP message handling

## Features

### Weather Tools
- `get_weather_alerts(state)` - Get active weather alerts for a US state
- `get_weather_forecast(lat, lon)` - Get detailed weather forecast for coordinates
- `get_location_coordinates(city, state)` - Get lat/lon for common cities

### Hotel Tools
- `book_hotel(message)` - Book a hotel with custom message
- `get_hotel_info()` - Get information about hotel services

## Prerequisites
- Python 3.8+
- Ollama CLI with `llama3.1` model
- NLIP SDK (for server mode)

## Setup

### 1. Install Dependencies
```bash
cd langchain_demo
pip install -r requirements.txt
```

### 2. Run Ollama Server
```bash
ollama run llama3.1
```

## Usage Options

### Option 1: Standalone Demo (Recommended for Testing)
```bash
python demo.py standalone
```

This runs an interactive chat interface where you can test all tools:
- "Get weather alerts for Indiana" 
- "What's the weather forecast for Bloomington, Indiana?"
- "Book a hotel room for tonight"
- "Tell me about hotel services"

### Option 2: NLIP Server Mode (Same as MCP)
```bash
poetry run uvicorn langchain_demo.demo:app --host 0.0.0.0 --port 8012 --reload
```

Then use the same curl commands as the MCP version:

```bash
curl -X POST http://localhost:8012/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english", 
  "content": "What are the weather alerts for Indiana?"
}'
```

```bash
curl -X POST http://localhost:8010/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english",
  "content": "What will the weather be like for Indiana Bloomington?"
}'
```

## Key Differences from MCP

| Aspect | MCP Version | LangChain Version |
|--------|-------------|-------------------|
| **Tool Definition** | MCP `@mcp.tool()` decorators | LangChain `@tool` decorators |
| **Agent Framework** | Manual tool calling logic | Built-in `AgentExecutor` |
| **Model Integration** | Direct Ollama API calls | `ChatOllama` wrapper |
| **Prompt Management** | String concatenation | `ChatPromptTemplate` |
| **Tool Orchestration** | Custom message handling | Agent automatically decides |
| **Streaming** | Not implemented | Built-in with callbacks |

## Advantages of LangChain Approach

1. **Simpler Tool Management** - Automatic tool selection by agent
2. **Better Prompt Engineering** - Template-based prompts
3. **Rich Ecosystem** - Many pre-built integrations
4. **Streaming Support** - Built-in streaming callbacks
5. **Memory Management** - Easy conversation memory
6. **Error Handling** - More robust error recovery

## Example Interactions

### Weather Query
```
You: What's the weather forecast for Bloomington, Indiana?
Assistant: I'll help you get the weather forecast for Bloomington, Indiana. Let me first get the coordinates and then fetch the forecast.

[Tool: get_location_coordinates]
Coordinates for Bloomington, Indiana: Latitude 39.1612, Longitude -86.5264

[Tool: get_weather_forecast] 
Tonight:
Temperature: 45°F
Wind: 5 mph NW
Forecast: Partly cloudy with overnight lows around 45...
```

### Hotel Booking
```
You: Book a hotel room for 2 nights in downtown
Assistant: [Tool: book_hotel]
Hotel Booking Confirmation: 2 nights in downtown

Your hotel reservation has been confirmed! The booking details for 2 nights in downtown have been processed.
```

## Code Structure

- `demo.py` - Main application with tools and session management
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Extending the Demo

To add new tools:

1. Define a new function with `@tool` decorator
2. Add it to the `tools` list in both standalone and server modes
3. The agent will automatically use it when relevant

```python
@tool
async def my_new_tool(param: str) -> str:
    """Description of what this tool does.
    
    Args:
        param: Description of the parameter
    """
    return f"Result: {param}"
``` 
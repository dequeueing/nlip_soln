# LlamaIndex Demo - MCP & LangChain Alternative

This demo showcases how to use **LlamaIndex** to achieve the same functionality as both the MCP (Model Context Protocol) and LangChain implementations. It provides weather tools, hotel booking tools, and chat session management using LlamaIndex's agent framework.

## Architecture Comparison

### MCP Version
- Uses MCP Client/Server protocol
- Tools defined as MCP servers
- Ollama integration via direct API calls
- NLIP message handling

### LangChain Version  
- Uses LangChain agents and tools
- Tools defined as LangChain `@tool` decorators
- Qwen integration via OpenAI-compatible API
- Same NLIP message handling

### LlamaIndex Version (This Demo)
- Uses LlamaIndex `FunctionAgent` workflow
- Tools defined as `FunctionTool` objects
- **Qwen integration via OpenAI-compatible API**
- Same NLIP message handling
- Built-in conversation context management

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
- **Qwen API Key** from Alibaba Cloud DashScope
- NLIP SDK (for server mode)

## Setup

### 1. Install Dependencies
```bash
cd llamaindex_demo
pip install -r requirements.txt
```

### 2. Set up Qwen API Key
```bash
export DASHSCOPE_API_KEY="your-qwen-api-key-here"
```

Get your API key from: https://dashscope.aliyun.com/

## Usage Options

### Option 1: Standalone Demo (Recommended for Testing)
```bash
python llamaindex_demo/demo.py standalone
```

This runs an interactive chat interface where you can test all tools:
- "Get weather alerts for Indiana" 
- "What's the weather forecast for Bloomington, Indiana?"
- "Book a hotel room for tonight"
- "Tell me about hotel services"

### Option 2: NLIP Server Mode (Same as MCP/LangChain)
```bash
NLIP_PII_ENABLED=true poetry run uvicorn llamaindex_demo.demo:app --host 0.0.0.0 --port 8013 --reload
```

Then use the same curl commands as the MCP/LangChain versions:

```bash
curl -X POST http://localhost:8013/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english", 
  "content": "What are the weather alerts for Indiana and what will the weather be like for Indiana Bloomington tonight?"
}'
```

```bash
curl -X POST http://localhost:8013/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english", 
  "content": "What are the weather alerts for Indiana? My name is John Doe and my phone number is 123-456-7890, my email is john.doe@example.com"
}'
```

## Key Differences from MCP & LangChain

| Aspect | MCP Version | LangChain Version | LlamaIndex Version |
|--------|-------------|-------------------|-------------------|
| **Tool Definition** | MCP `@mcp.tool()` decorators | LangChain `@tool` decorators | `FunctionTool.from_defaults()` |
| **Agent Framework** | Manual tool calling logic | `AgentExecutor` | `FunctionAgent` |
| **Model Integration** | Direct Ollama API calls | **Qwen via OpenAI-compatible API** | **Qwen via OpenAI-compatible API** |
| **Prompt Management** | String concatenation | `ChatPromptTemplate` | Built-in system prompt |
| **Tool Orchestration** | Custom message handling | Agent automatically decides | Agent automatically decides |
| **Context Management** | Manual correlation tokens | Stateless by default | Built-in `Context` object |

## Advantages of LlamaIndex Approach

1. **Built-in Context Management** - Automatic conversation state with `Context` object
2. **Simplified Tool Creation** - `FunctionTool.from_defaults()` handles metadata automatically
3. **Strong RAG Focus** - Better for data-driven applications (though not used in this demo)
4. **Workflow System** - More structured agent workflows compared to LangChain
5. **Research-Oriented** - Designed specifically for knowledge retrieval tasks
6. **Async-First** - Native async support throughout the framework

## Code Structure

- `demo.py` - Main application with tools and session management
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Extending the Demo

To add new tools:

1. Define a new async function
2. Create a `FunctionTool` from it
3. Add it to the tools list
4. The agent will automatically use it when relevant

```python
async def my_new_tool(param: str) -> str:
    """Description of what this tool does."""
    return f"Result: {param}"

new_tool = FunctionTool.from_defaults(
    fn=my_new_tool,
    name="my_new_tool",
    description="Description of what this tool does. Takes a parameter string."
) 
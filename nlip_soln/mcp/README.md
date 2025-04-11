# MCP Client & Server Setup

## Prerequisites
- Python 3.x
- Ollama CLI
- Uvicorn

## Setup Steps

### 1. Install Ollama CLI
Download and install the Ollama CLI from [ollama.com](https://ollama.com).

### 2. Run Ollama Server with IBM Granite 2B Model
Run the Ollama server:

```bash
ollama run granite3.2:2b
```

### 3. Run MCP command line Client with MCP 

```bash
cd mcp-client  
uv venv
source .venv/bin/activate
```

```bash
source mcp-client/.venv/bin/activate
```
```bash
uv run client.py ../mcp-server/weather/weather.py
```



import asyncio
import os
import httpx
from typing import Any, Dict, List, Optional
import os

from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from llama_index.llms.openai_like import OpenAILike

from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server.nlip_server import server


# Weather Tools (equivalent to MCP weather server)
async def get_weather_alerts(state: str) -> str:
    """Get weather alerts for a US state.
    
    Args:
        state: Two-letter US state code (e.g. CA, NY, IN)
    """
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "llamaindex-weather-demo/1.0"
    
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if not data or "features" not in data:
                return "Unable to fetch alerts or no alerts found."

            if not data["features"]:
                return f"No active weather alerts for {state.upper()}."

            alerts = []
            for feature in data["features"]:
                props = feature["properties"]
                alert = f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""
                alerts.append(alert)
            
            return "\n---\n".join(alerts)
            
        except Exception as e:
            return f"Error fetching weather alerts: {str(e)}"


async def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "llamaindex-weather-demo/1.0"
    
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    
    async with httpx.AsyncClient() as client:
        try:
            # First get the forecast grid endpoint
            points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
            points_response = await client.get(points_url, headers=headers, timeout=30.0)
            points_response.raise_for_status()
            points_data = points_response.json()

            # Get the forecast URL from the points response
            forecast_url = points_data["properties"]["forecast"]
            forecast_response = await client.get(forecast_url, headers=headers, timeout=30.0)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Format the periods into a readable forecast
            periods = forecast_data["properties"]["periods"]
            forecasts = []
            for period in periods[:5]:  # Only show next 5 periods
                forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
                forecasts.append(forecast)

            return "\n---\n".join(forecasts)
            
        except Exception as e:
            return f"Error fetching weather forecast: {str(e)}"


class LlamaIndexChatApplication(server.NLIP_Application):
    """LlamaIndex-powered chat application similar to MCP and LangChain versions."""
    
    async def startup(self):
        print("Starting LlamaIndex Chat Application...")

    async def shutdown(self):
        return None

    async def create_session(self) -> server.NLIP_Session:
        return LlamaIndexChatSession()


class LlamaIndexChatSession(server.NLIP_Session):
    """Chat session using LlamaIndex instead of MCP or LangChain."""
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.agent = None
        self.tools = []
        self.context = None

    async def start(self):
        """Initialize LlamaIndex components."""
        try:
            print("Initializing LlamaIndex components...")
            
            # Check for API key
            if not os.getenv("DASHSCOPE_API_KEY"):
                raise ValueError("DASHSCOPE_API_KEY environment variable is required. Get your key from https://dashscope.aliyun.com/")
            
            # Initialize Qwen model via OpenAI-compatible API using OpenAILike
            self.llm = OpenAILike(
                model="anthropic/claude-sonnet-4", 
                api_key=os.getenv("OPENROUTER_API_KEY"),
                api_base="https://openrouter.ai/api/v1",
                temperature=0.7,
                # Explicitly set the context window to match Qwen's context window
                context_window=128000,
                # Controls whether the model uses chat or completion endpoint
                is_chat_model=True,
                # Controls whether the model supports function calling
                is_function_calling_model=True,
            )
            
            # Create FunctionTool objects from our async functions
            self.tools = [
                FunctionTool.from_defaults(
                    fn=get_weather_alerts,
                    name="get_weather_alerts",
                    description="Get weather alerts for a US state. Takes a state code like 'CA', 'NY', 'IN'."
                ),
                FunctionTool.from_defaults(
                    fn=get_weather_forecast,
                    name="get_weather_forecast", 
                    description="Get weather forecast for coordinates. Takes latitude and longitude as numbers."
                ),
            ]
            
            # Create LlamaIndex FunctionAgent
            self.agent = FunctionAgent(
                tools=self.tools,
                llm=self.llm,
                verbose=True,
                system_prompt="You are a helpful assistant with access to weather tools. "
                             "You can get weather alerts and forecasts. "
                             "Use the tools when needed to help users with their weather-related requests."
            )
            
            # Initialize context for maintaining conversation state
            self.context = Context(self.agent)
            
            print("LlamaIndex components initialized successfully.")
            print(f"Available tools: {[tool.metadata.name for tool in self.tools]}")
            
        except Exception as e:
            print(f"Error initializing LlamaIndex components: {e}")
            raise

    async def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        """Execute user query using LlamaIndex agent."""
        logger = self.get_logger()
        text = msg.extract_text()
        
        try:
            print(f"🔧 [LlamaIndex] Processing delegated query: {text}")
            
            # Use the LlamaIndex agent to process the query
            response = await self.agent.run(text, ctx=self.context)
            response_text = str(response)
            
            print(f"✅ [LlamaIndex] Completed processing, returning result to LangChain")
            logger.info(f"LlamaIndex Response: {response_text}")
            return NLIP_Factory.create_text(response_text)
            
        except Exception as e:
            logger.error(f"Exception in LlamaIndex execution: {e}")
            return NLIP_Factory.create_text(f"Error processing request: {str(e)}")

    async def stop(self):
        """Clean up resources."""
        print("Stopping LlamaIndex chat session")
        self.llm = None
        self.agent = None
        self.tools = []
        self.context = None


# Standalone demo function
async def standalone_demo():
    """Run a standalone demo without NLIP integration."""
    print("=== LlamaIndex Standalone Demo ===")
    print("This demo showcases LlamaIndex with weather tools that process delegated requests.")
    print("Available commands:")
    print("- Weather alerts: 'Get weather alerts for Indiana'")
    print("- Weather forecast: 'What's the weather forecast for Bloomington, Indiana?'")
    print("- Quit: 'quit' or 'exit'")
    print()
    
    # Check for API key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ ERROR: DASHSCOPE_API_KEY environment variable is required!")
        print("Get your API key from: https://dashscope.aliyun.com/")
        print("Set it with: export DASHSCOPE_API_KEY='your-key-here'")
        return
    
    # Initialize LlamaIndex components using OpenAILike
    llm = OpenAILike(
        model="qwen-plus",  # Much stronger than llama3.1!
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.7,
        context_window=128000,
        is_chat_model=True,
        is_function_calling_model=True,
    )
    
    tools = [
        FunctionTool.from_defaults(
            fn=get_weather_alerts,
            name="get_weather_alerts",
            description="Get weather alerts for a US state. Takes a state code like 'CA', 'NY', 'IN'."
        ),
        FunctionTool.from_defaults(
            fn=get_weather_forecast,
            name="get_weather_forecast", 
            description="Get weather forecast for coordinates. Takes latitude and longitude as numbers."
        ),
    ]
    
    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        verbose=True,
        system_prompt="You are a helpful assistant with access to weather tools. "
                     "You can get weather alerts and forecasts. "
                     "Use the tools when needed to help users with their weather-related requests."
    )
    
    context = Context(agent)
    
    print("LlamaIndex agent initialized with tools:")
    for tool in tools:
        print(f"  - {tool.metadata.name}: {tool.metadata.description}")
    print()
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                break
                
            if not user_input:
                continue
                
            print("\nAssistant: ", end="")
            response = await agent.run(user_input, ctx=context)
            print(f"{str(response)}\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


# Create the FastAPI app (this is what uvicorn will look for)
app = server.setup_server(LlamaIndexChatApplication())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Run standalone demo
        asyncio.run(standalone_demo())
    else:
        print("LlamaIndex NLIP server ready!")
        print("This server executes weather tools and serves requests from LangChain server via NLIP protocol")
        print("Use 'poetry run uvicorn llamaindex_demo.demo:app --host 0.0.0.0 --port 8013 --reload' to start server")
        print("Or use the same curl commands as in the MCP README to test.")

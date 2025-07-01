import asyncio
import httpx
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.callbacks import BaseCallbackHandler

from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server.nlip_server import server


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses."""
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        print(token, end="", flush=True)


# Weather Tools (equivalent to MCP weather server)
@tool
async def get_weather_alerts(state: str) -> str:
    """Get weather alerts for a US state.
    
    Args:
        state: Two-letter US state code (e.g. CA, NY, IN)
    """
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "langchain-weather-demo/1.0"
    
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


@tool
async def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "langchain-weather-demo/1.0"
    
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


@tool
async def get_location_coordinates(city: str, state: str = "") -> str:
    """Get latitude and longitude for a city to use with weather forecast.
    
    Args:
        city: City name (e.g. "Bloomington")
        state: State name or abbreviation (e.g. "Indiana" or "IN")
    """
    # Simple coordinate lookup for demo purposes
    # In production, you'd use a geocoding service
    locations = {
        "bloomington,indiana": (39.1612, -86.5264),
        "bloomington,in": (39.1612, -86.5264),
        "indianapolis,indiana": (39.7684, -86.1581),
        "indianapolis,in": (39.7684, -86.1581),
        "chicago,illinois": (41.8781, -87.6298),
        "chicago,il": (41.8781, -87.6298),
        "new york,new york": (40.7128, -74.0060),
        "new york,ny": (40.7128, -74.0060),
    }
    
    key = f"{city.lower()},{state.lower()}" if state else city.lower()
    
    for location_key, coords in locations.items():
        if key in location_key:
            lat, lon = coords
            return f"Coordinates for {city}, {state}: Latitude {lat}, Longitude {lon}"
    
    return f"Coordinates not found for {city}, {state}. Try using specific lat/lon with get_weather_forecast."


# Hotel Tools (equivalent to MCP hotel server)
@tool
async def book_hotel(message: str) -> str:
    """Book a hotel with the given message.
    
    Args:
        message: The booking message or request details
    """
    return f"Hotel Booking Confirmation: {message}"


@tool
async def get_hotel_info() -> str:
    """Get basic hotel information and services."""
    return """Welcome to the LangChain Hotel Service! 
    
Available services:
- Room booking
- Restaurant reservations
- Concierge services
- Local area information
    
This is a demo service for testing LangChain tool integration."""


class LangChainChatApplication(server.NLIP_Application):
    """LangChain-powered chat application similar to MCP version."""
    
    async def startup(self):
        print("Starting LangChain Chat Application...")

    async def shutdown(self):
        return None

    async def create_session(self) -> server.NLIP_Session:
        return LangChainChatSession()


class LangChainChatSession(server.NLIP_Session):
    """Chat session using LangChain instead of MCP."""
    
    def __init__(self):
        super().__init__()
        self.llm = None
        self.agent_executor = None
        self.tools = []

    async def start(self):
        """Initialize LangChain components."""
        try:
            print("Initializing LangChain components...")
            
            # Initialize Ollama model
            self.llm = ChatOllama(
                model="llama3.1",
                temperature=0.7,
                callbacks=[StreamingCallbackHandler()]
            )
            
            # Define available tools
            self.tools = [
                get_weather_alerts,
                get_weather_forecast,
                get_location_coordinates,
                book_hotel,
                get_hotel_info
            ]
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant with access to weather and hotel booking tools. "
                          "Use the tools when needed to help users with their requests."),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
            
            # Create agent
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            
            print("LangChain components initialized successfully.")
            print(f"Available tools: {[tool.name for tool in self.tools]}")
            
        except Exception as e:
            print(f"Error initializing LangChain components: {e}")
            raise

    async def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        """Execute user query using LangChain agent."""
        logger = self.get_logger()
        text = msg.extract_text()
        
        try:
            print(f"Processing query: {text}")
            
            # Use the agent executor to process the query
            result = await self.agent_executor.ainvoke({"input": text})
            response = result["output"]
            
            logger.info(f"LangChain Response: {response}")
            return NLIP_Factory.create_text(response)
            
        except Exception as e:
            logger.error(f"Exception in LangChain execution: {e}")
            return NLIP_Factory.create_text(f"Error processing request: {str(e)}")

    async def stop(self):
        """Clean up resources."""
        print("Stopping LangChain chat session")
        self.llm = None
        self.agent_executor = None
        self.tools = []


# Standalone demo function
async def standalone_demo():
    """Run a standalone demo without NLIP integration."""
    print("=== LangChain Standalone Demo ===")
    print("This demo showcases LangChain with the same tools as the MCP version.")
    print("Available commands:")
    print("- Weather alerts: 'Get weather alerts for Indiana'")
    print("- Weather forecast: 'What's the weather forecast for Bloomington, Indiana?'")
    print("- Hotel booking: 'Book a hotel room for tonight'")
    print("- Hotel info: 'Tell me about hotel services'")
    print("- Quit: 'quit' or 'exit'")
    print()
    
    # Initialize LangChain components
    llm = ChatOllama(model="llama3.1", temperature=0.7)
    
    tools = [
        get_weather_alerts,
        get_weather_forecast,
        get_location_coordinates,
        book_hotel,
        get_hotel_info
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with access to weather and hotel booking tools. "
                  "Use the tools when needed to help users with their requests."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    print("LangChain agent initialized with tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
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
            result = await agent_executor.ainvoke({"input": user_input})
            print(f"\n{result['output']}\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


# Create the FastAPI app (this is what uvicorn will look for)
app = server.setup_server(LangChainChatApplication())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # Run standalone demo
        asyncio.run(standalone_demo())
    else:
        print("LangChain NLIP server ready!")
        print("Use 'poetry run uvicorn langchain_demo.demo:app --host 0.0.0.0 --port 8012 --reload' to start server")
        print("Or use the same curl commands as in the MCP README to test.") 
import asyncio
import os
import httpx
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack
import os
import json

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.callbacks import BaseCallbackHandler

from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server.nlip_server import server


# NLIP Client for inter-agent communication
class NLIPClient:
    """Client for sending NLIP messages to other agents using proper NLIP SDK."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def send_message(self, content: str, format_type: str = "text", subformat: str = "english") -> str:
        """Send a NLIP message to another agent and return the response."""
        url = f"{self.base_url}/nlip/"
        
        # Create NLIP message using the SDK
        nlip_message = NLIP_Factory.create_text(content)
        
        # Serialize the NLIP message to JSON (the message has a model_dump method)
        message_data = nlip_message.model_dump()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    json=message_data,
                    headers={"Content-Type": "application/json"},
                    timeout=60.0
                )
                response.raise_for_status()
                result_data = response.json()
                
                # Parse the response back into a NLIP message and extract text
                # The response should be a NLIP message in JSON format
                response_message = nlip.NLIP_Message.model_validate(result_data)
                return response_message.extract_text()
                
            except Exception as e:
                return f"Error communicating with agent at {self.base_url}: {str(e)}"


# Configuration for the LlamaIndex server
LLAMAINDEX_SERVER_URL = "http://localhost:8013"


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses."""
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        print(token, end="", flush=True)


# Delegating Weather Tools (delegate to LlamaIndex server via NLIP)
@tool
async def get_weather_alerts(state: str) -> str:
    """Get weather alerts for a US state by delegating to LlamaIndex server.
    
    Args:
        state: Two-letter US state code (e.g. CA, NY, IN)
    """
    print(f"\n🔄 [LangChain] Delegating weather alerts query for {state} to LlamaIndex server...")
    
    client = NLIPClient(LLAMAINDEX_SERVER_URL)
    query = f"Get weather alerts for {state}"
    
    response = await client.send_message(query)
    print(f"✅ [LangChain] Weather alerts response received from LlamaIndex server\n")
    return response


@tool
async def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location by delegating to LlamaIndex server.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    print(f"\n🔄 [LangChain] Delegating weather forecast query for ({latitude}, {longitude}) to LlamaIndex server...")
    
    client = NLIPClient(LLAMAINDEX_SERVER_URL)
    query = f"Get weather forecast for latitude {latitude} and longitude {longitude}"
    
    response = await client.send_message(query)
    print(f"✅ [LangChain] Weather forecast response received from LlamaIndex server\n")
    return response

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
            
            # Check for API key
            if not os.getenv("OPENROUTER_API_KEY"):
                raise ValueError("OPENROUTER_API_KEY environment variable is required. Get your key from https://openrouter.ai/")
            
            # Initialize model via OpenRouter API
            self.llm = ChatOpenAI(
                model="anthropic/claude-sonnet-4", 
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                temperature=0.7,
                callbacks=[StreamingCallbackHandler()]
            )
            
            # Define available tools (all delegating to LlamaIndex server)
            self.tools = [
                get_weather_alerts,
                get_weather_forecast
            ]
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant with access to weather tools. "
                          "You can get weather alerts and forecasts. "
                          "Use the tools when needed to help users with their weather-related requests."),
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
            print(f"\n📨 [LangChain] Processing client query: {text}")
            print("=" * 60)
            
            # Use the agent executor to process the query
            result = await self.agent_executor.ainvoke({"input": text})
            response = result["output"]
            
            print("=" * 60)
            print(f"📤 [LangChain] Sending final response to client\n")
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
    print("This demo showcases LangChain with weather tools delegating to LlamaIndex.")
    print("Available commands:")
    print("- Weather alerts: 'Get weather alerts for Indiana'")
    print("- Weather forecast: 'What's the weather forecast for Bloomington, Indiana?'")
    print("- Quit: 'quit' or 'exit'")
    print()
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ ERROR: OPENROUTER_API_KEY environment variable is required!")
        print("Get your API key from: https://openrouter.ai/")
        print("Set it with: export OPENROUTER_API_KEY='your-key-here'")
        return
    
    # Initialize LangChain components
    llm = ChatOpenAI(
        model="anthropic/claude-sonnet-4", 
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
    )
    
    tools = [
        get_weather_alerts,
        get_weather_forecast
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with access to weather tools. "
                  "You can get weather alerts and forecasts. "
                  "Use the tools when needed to help users with their weather-related requests."),
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
        print("This server delegates tool execution to LlamaIndex server via NLIP protocol")
        print("Make sure LlamaIndex server is running on port 8013 first!")
        print("Use 'poetry run uvicorn langchain_demo.demo:app --host 0.0.0.0 --port 8012 --reload' to start server")
        print("Or use the same curl commands as in the MCP README to test.") 
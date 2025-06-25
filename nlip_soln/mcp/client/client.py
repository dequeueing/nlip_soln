import asyncio
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import ollama
from dotenv import load_dotenv

load_dotenv()


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.ollama = ollama

    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:")
        # print tools with its name, description and input schema
        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input Schema: {tool.inputSchema}")
            print("--------------------------------")

    async def process_query(self, query: str) -> str:
        """Process the query (masked or original) through the MCP server."""
        # print(f"Processing query")
        print(f"To call tools, the query: {query}\n")
        
        
        messages = [{"role": "user", "content": query}]

        response = await self.session.list_tools()
        # print(f"Process query tools {response}")
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]
        
        response = self.ollama.chat(
            model="llama3.1", messages=messages, tools=available_tools
        )
        final_text = []

        # print(f"Response from ollama")
        # print(response)

        assistant_message_content = response.message.content
        final_text.append(assistant_message_content)

        if response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                result = await self.session.call_tool(tool_name, tool_args)
                
                # print(f"Debug: tool call result: {result}")
                
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                tool_use_id = f"{tool_name}_{hash(str(tool_args))}"

                messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {"function": {"name": tool_name, "arguments": tool_args}}
                        ],
                    }
                )

                messages.append({"role": "tool", "content": str(result.content)})

                response = self.ollama.chat(
                    model="llama3.1", messages=messages
                )
                
                # print(f"Response with tool call from ollama: {response}")

                final_text.append(response.message.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient()
    try:
        server_script_path = "/home/exouser/nlip_soln/nlip_soln/mcp/server/weather/weather.py"
        # server_script_path = "/home/exouser/nlip_soln/nlip_soln/mcp/server/hotel/hotel.py"
        await client.connect_to_server(server_script_path)
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())

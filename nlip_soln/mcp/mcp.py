from multiprocessing import get_logger
import os

from nlip_sdk.nlip import NLIP_Factory
from nlip_sdk import nlip
from nlip_server.nlip_server import server 

from .client.client import MCPClient

print(f"file for nlip_sdk: {nlip.__file__}")


logger = get_logger()


class ChatApplication(server.NLIP_Application):
    async def startup(self):
        logger.info("Starting app...")

    async def shutdown(self):
        return None

    async def create_session(self) -> server.NLIP_Session:
        return ChatSession(MCPClient())


class ChatSession(server.NLIP_Session):

    def __init__(self, client: MCPClient):
        # Framework will handle PII detection automatically
        super().__init__()  # This now includes optional PII setup
        self.client = client

    async def start(self):
        try:
            logger.info(f"Connecting to the MCP server...")
            await self.client.connect_to_server(
                "nlip_soln/mcp/server/weather/weather.py"
                # "nlip_soln/mcp/server/hotel/hotel.py"
            )
            logger.info(f"Connected.")
        except Exception as e:
            logger.info(f"Error connecting MCP server {e}")
            await self.client.cleanup()

    async def execute(
        self, msg: nlip.NLIP_Message
    ) -> nlip.NLIP_Message:
        logger = self.get_logger()
        text = msg.extract_text()
        
        # Framework handles PII automatically if enabled

        try:
            response = await self.client.process_query(text)
            logger.info(f"Response : {response}")
            return NLIP_Factory.create_text(response)
        except Exception as e:
            logger.error(f"Exception {e}")
            return None

    async def stop(self):
        logger.info(f"Stopping chat session")
        await self.client.cleanup()
        self.server = None


app = server.setup_server(ChatApplication())

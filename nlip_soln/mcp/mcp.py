from multiprocessing import get_logger
import os

from nlip_server import server
from nlip_sdk import nlip

from .client.client import MCPClient


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
        self.client = client

    async def start(self):
        try:
            logger.info(f"Connecting to the MCP server...")
            await self.client.connect_to_server(
                "nlip_soln/mcp/server/weather/weather.py"
            )
            logger.info(f"Connected.")
        except Exception as e:
            logger.info(f"Error connecting MCP server {e}")
            await self.client.cleanup()

    async def execute(
        self, msg: nlip.NLIP_Message | nlip.NLIP_BasicMessage
    ) -> nlip.NLIP_Message | nlip.NLIP_BasicMessage:
        logger = self.get_logger()
        text = nlip.nlip_extract_text(msg)

        try:
            response = await self.client.process_query(text)
            logger.info(f"Response : {response}")
            return nlip.nlip_encode_text(response)
        except Exception as e:
            logger.error(f"Exception {e}")
            return None

    async def stop(self):
        logger.info(f"Stopping chat session")
        await self.client.cleanup()
        self.server = None


app = server.setup_server(ChatApplication())

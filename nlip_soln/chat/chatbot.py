import os


from nlip_server import server
from nlip_sdk import nlip
from nlip_soln.genai import SimpleGenAI


class ChatApplication(server.SafeApplication):
    def startup(self):
        self.model = os.environ.get("CHAT_MODEL", "granite3-moe")
        self.host = os.environ.get("CHAT_HOST", "localhost")
        self.port = os.environ.get("CHAT_PORT", 11434)

    def shutdown(self):
        return None

    def create_session(self) -> server.NLIP_Session:
        return ChatSession(host=self.host, port=self.port, model=self.model)


class ChatSession(server.NLIP_Session):

    def __init__(self, host: str, port: int, model: str):
        self.host = host
        self.port = port
        self.model = model

    def start(self):
        self.chat_server = SimpleGenAI(self.host, self.port)

    def execute(
        self, msg: nlip.NLIP_Message
    ) -> nlip.NLIP_Message:
        text = msg.extract_text()
        response = self.chat_server.generate(self.model, text)
        return nlip.NLIP_Factory.create_text(response)

    def stop(self):
        self.server = None


app = server.setup_server(ChatApplication())

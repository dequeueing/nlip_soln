import os
import uuid
import time


from nlip_server import server
from nlip_sdk import nlip
from nlip_soln.genai import StatefulGenAI


class ChatApplication(server.NLIP_Application):
    def startup(self):
        self.model = os.environ.get("CHAT_MODEL", "granite3-moe")
        self.host = os.environ.get("CHAT_HOST", "localhost")
        self.port = os.environ.get("CHAT_PORT", 11434)
        self.session_dict = dict()
        self.touched = dict()

    def shutdown(self):
        return None

    def create_session(self) -> server.NLIP_Session:
        return ChatSession(host=self.host, port=self.port, model=self.model, app=self)

    def retrieve_session_data(self, correlator):
        answer = self.session_dict.get(correlator, None)
        self.touched[correlator] = time.time()
        return answer

    def store_session_data(self, correlator, session_data):
        self.session_dict[correlator] = session_data
        self.touched[correlator] = time.time()

    def purge_old(self):
        now = time.time()
        for x in self.touched.keys():
            if now - self.touched[x] > 3600:
                # Data has not been touched for an hour - can be removed.
                self.touched.pop(x, None)
                self.session_dict.pop(x, None)


class ChatSession(server.NLIP_Session):

    def __init__(self, host: str, port: int, model: str, app: ChatApplication):
        self.host = host
        self.port = port
        self.model = model
        self.app = app

    def start(self):
        logger = self.get_logger()

    def execute(
        self, msg: nlip.NLIP_Message | nlip.NLIP_BasicMessage
    ) -> nlip.NLIP_Message | nlip.NLIP_BasicMessage:
        logger = self.get_logger()

        text = nlip.nlip_extract_text(msg)
        correlators = nlip.nlip_extract_field_list(msg, nlip.AllowedFormats.token)
        correlator = ""
        chat_server = None
        if len(correlators) == 0:
            correlator = str(uuid.uuid4())
        else:
            correlator = str(correlators[0])
        chat_server = self.app.retrieve_session_data(correlator)
        if chat_server is None:
            chat_server = StatefulGenAI(self.host, self.port, self.model)
            self.app.store_session_data(correlator, chat_server)

        response = chat_server.chat(text)
        submsg = nlip.NLIP_SubMessage(
            format=nlip.AllowedFormats.token, subformat="correlator", content=correlator
        )
        response = nlip.NLIP_Message(
            control=False,
            format=nlip.AllowedFormats.text,
            subformat="English",
            content=response,
            submessages=[submsg],
        )
        return response

    def stop(self):
        self.app.purge_old()


app = server.setup_server(ChatApplication())

"""
This is an echo server which simply sends back the message
that is received to the client.

This is used to test that all types of messages can be encoded
and sent back to the client in the right manner.

"""

from nlip_server.server import NLIP_Application, NLIP_Session, setup_server
from nlip_sdk.nlip import (
    AllowedFormats,
    NLIP_BasicMessage,
    NLIP_Message,
    NLIP_SubMessage,
)


class EchoApplication(NLIP_Application):
    def startup(self):
        self.get_logger().info("EchoApplication Started")

    def shutdown(self):
        self.get_logger().info("EchoApplication Shut Down")

    def create_session(self) -> NLIP_Session:
        return EchoSession()


class EchoSession(NLIP_Session):
    def start(self):
        self.get_logger().info("EchoSession Started")

    def stop(self):
        self.get_logger().info("EchoSession Stopped")

    def execute(
        self, msg: NLIP_Message | NLIP_BasicMessage
    ) -> NLIP_Message | NLIP_BasicMessage:
        self.get_logger().error(f"Got Message {msg}")
        return msg


app = setup_server(EchoApplication())

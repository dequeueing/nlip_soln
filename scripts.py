import os
import subprocess
import sys

# _SERVER_MODULE_PATH = "app.server:app"
# _CHAT_SERVER_MODULE_PATH = "nlip_soln.chat.chatbot:app"
# _CHAT2_SERVER_MODULE_PATH = "nlip_soln.chat2.stateful_chatbot:app"
# _INTEGRATION_SERVER_MODULE_PATH = "nlip_soln.integrator.integrator:app"

# The solution configuration is a directory which contains a tuple
# The first element of the tuple is the name of the fastapi app
# The second element of the tuple is the port on which the app will run

soln_config = {
    "echo": ("nlip_soln.echo.echo:app", "8002"),
    "chat": ("nlip_soln.chat.chatbot:app", "8004"),
    "stateful_chat": ("nlip_soln.chat2.stateful_chatbot:app", "8006"),
    "integrator": ("nlip_soln.chat2.stateful_chatbot:app", "8008"),
    "mcp": ("nlip_soln.mcp.mcp:app", "8010"),
}

# def format_code() -> None:
#     """Format the code using black and isort."""
#     for formatter in ("black", "isort"):
#         print(f"Running {formatter}...")
#         subprocess.run([formatter, "."], check=True)


# def start_server() -> None:
#     """Start the FastAPI server."""
#     subprocess.run(
#         ["uvicorn", _SERVER_MODULE_PATH, *compose_shared_flags()],
#         check=True,
#     )


# def start_server_dev() -> None:
#     """Start the FastAPI server in development mode."""
#     subprocess.run(
#         ["uvicorn", _SERVER_MODULE_PATH, *compose_shared_flags(), "--reload"],
#         check=True,
#     )


def start_chat_server() -> None:
    """Start the FastAPI chat server."""
    subprocess.run(
        [
            "uvicorn",
            soln_config["chat"][0],
            *compose_shared_flags(),
            "--port",
            os.environ.get("PORT", soln_config["chat"][1]),
            "--reload",
        ],
        check=True,
    )


def start_stateful_chat_server() -> None:
    """Start the FastAPI stateful chat server."""
    subprocess.run(
        [
            "uvicorn",
            soln_config["stateful_chat"][0],
            *compose_shared_flags(),
            "--port",
            os.environ.get("PORT", soln_config["stateful_chat"][1]),
            "--reload",
        ],
        check=True,
    )


def start_integration_server() -> None:
    """Start the FastAPI integration server."""
    subprocess.run(
        [
            "uvicorn",
            soln_config["integrator"][0],
            *compose_shared_flags(),
            "--port",
            os.environ.get("PORT", soln_config["integrator"][1]),
            "--reload",
        ],
        check=True,
    )


def start_mcp() -> None:
    """Start the FastAPI integration server."""
    subprocess.run(
        [
            "uvicorn",
            soln_config["mcp"][0],
            *compose_shared_flags(),
            "--port",
            os.environ.get("PORT", soln_config["mcp"][1]),
            "--reload",
        ],
        check=True,
    )


def start_echo_server() -> None:
    """Start the FastAPI integration server."""
    subprocess.run(
        [
            "uvicorn",
            soln_config["echo"][0],
            *compose_shared_flags(),
            "--port",
            os.environ.get("PORT", soln_config["echo"][1]),
            "--reload",
        ],
        check=True,
    )


def compose_shared_flags() -> list[str]:
    """Compose shared command-line flags for Uvicorn."""
    return ["--host", "0.0.0.0"]

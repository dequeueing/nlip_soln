# NLIP Solutions  

Welcome to the NLIP Solutions! This project provides a few simple 
server side solutions that support the NLIP protocol. 

The solutions included in the repository are: 
* A simple stateless chatbot that responds to NLIP messages 
* An integrator bot which polls the answer across several backend servers. 


## Installation

This project uses [Poetry](https://python-poetry.org/docs/) for dependency management. First, please [install Poetry](https://python-poetry.org/docs/#installation).

To set up the Python project, create a virtual environment using the following commands.

1. Create the virtual environment:
    ```bash
    poetry env use python
    ```
  
2. Install the application dependencies
    ```bash
    poetry install
    ```

Once the Python environment is set up, you can run the server.

## Running the Ollama Servers. 

**Note:** This solution assumes that you have an Ollama Server running and properly configured. You can see the directions for running the Ollama server at ollama.com .The default configuration is an ollama server running a the local machine using granite3-moe model. 

The README in individual solutions describe how to configure the solution. 

## Running the Chatbot Server

Start the chat server with:

```bash
poetry run start-chat
```

To start the chat server with a specific model (e.g., `llama2`):

```bash
CHAT_MODEL=llama2 poetry run start-chat
```

## Running the Integration Server

Start the integration server with:

```bash
poetry run start-integration
```

## Using MCP on the Server Side

Start the MCP server with:

```bash
poetry run start-mcp
```

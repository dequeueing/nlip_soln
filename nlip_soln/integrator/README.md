# Integrator Proxy 

This provides an implementation of a NLIP Server which acts like the front-end of many different chatbots. Each of the chatbots is an Ollama server configured with a differnet models 

The system supports a configuration of 

[Client]----[NLIP-Server]---[LLM Servers]


The configuration file config.py defines all of the backend servers. 
Each server is configured by defining the host, port and the model. 

When a request is obtained, the NLIP-Server obtains an answer from each of the backend LLM services. Then it asks the services to rate each other's answers as correct or not, and picks the answer from the service which gets the highest count that the answer is collect. 

# Client command to send

```bash
curl -X POST http://localhost:8008/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english",
  "content": "Who are you?"
}'
```
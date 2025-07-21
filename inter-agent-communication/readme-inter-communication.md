# Inter-Agent Communication Demo with NLIP

This demo showcases **inter-agent communication** using the NLIP (Natural Language Interaction Protocol) framework. It demonstrates how AI agents can collaborate by delegating tasks to each other through structured NLIP messages.

## 🏗️ Architecture

### **LangChain Server (Port 8012)** - *Coordinator Agent*
- **Role**: Receives client requests and coordinates tool execution
- **Tools**: Has tool definitions but **delegates execution** to LlamaIndex server
- **Communication**: Uses NLIP protocol to send requests to LlamaIndex server
- **Flow**: Client → LangChain → (NLIP) → LlamaIndex → (NLIP) → LangChain → Client

### **LlamaIndex Server (Port 8013)** - *Worker Agent*
- **Role**: Actually executes the weather tools
- **Tools**: Contains the real tool implementations that call external APIs
- **Communication**: Receives NLIP requests from LangChain server
- **Flow**: Processes delegated requests and returns results via NLIP

## 🛠️ Available Tools

Both agents work together to provide these weather services:

1. **`get_weather_alerts(state)`** - Get weather alerts for a US state
2. **`get_weather_forecast(latitude, longitude)`** - Get weather forecast for coordinates

## 🚀 Running the Demo

### Prerequisites
- Python 3.8+
- Poetry installed
- API keys configured (see below)

### Step 1: Install Dependencies

```bash
cd /home/exouser/nlip_soln
poetry install
```

### Step 2: Set up API Keys

**For LangChain Server (Coordinator):**
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key-here"
```
Get your key from: https://openrouter.ai/

**For LlamaIndex Server (Worker):**
```bash
export DASHSCOPE_API_KEY="your-qwen-api-key-here"
```
Get your key from: https://dashscope.aliyun.com/

### Step 3: Start LlamaIndex Server (Worker Agent)

```bash
cd /home/exouser/nlip_soln
poetry run uvicorn llamaindex_demo.demo:app --host 0.0.0.0 --port 8013 --reload
```

**Wait for:** `LlamaIndex NLIP server ready!`

### Step 4: Start LangChain Server (Coordinator Agent)

Open a **new terminal** and run:

```bash
cd /home/exouser/nlip_soln
poetry run uvicorn langchain_demo.demo:app --host 0.0.0.0 --port 8012 --reload
```

**Wait for:** `LangChain NLIP server ready!`

## 🧪 Testing the Inter-Agent Communication

### Test 1: Weather Alerts

```bash
curl -X POST http://localhost:8012/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english", 
  "content": "What are the weather alerts for Indiana?"
}'
```

### Test 2: Weather Forecast

```bash
curl -X POST http://localhost:8012/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english",
  "content": "What will the weather be like at latitude 39.1612 and longitude -86.5264?"
}'
```

### Test 3: Complex Query (Demonstrates AI Reasoning)

```bash
curl -X POST http://localhost:8012/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english",
  "content": "Are there any weather alerts for Indiana? What will the weather be like for Bloomington, Indiana tonight?"
}'
```

## 🔍 Watching the Inter-Agent Flow

When you send a request, you'll see this delegation flow in the terminal logs:

1. **📨 [LangChain]** Processing client query
2. **🔄 [LangChain]** Delegating to LlamaIndex server  
3. **🔧 [LlamaIndex]** Processing delegated query
4. **✅ [LlamaIndex]** Returning result to LangChain
5. **✅ [LangChain]** Received response from LlamaIndex
6. **📤 [LangChain]** Sending final response to client

## 🎯 What This Demonstrates

### **NLIP Protocol Features**
- ✅ **Structured Communication**: Proper NLIP message format
- ✅ **Agent Interoperability**: Different frameworks (LangChain ↔ LlamaIndex) communicating
- ✅ **Task Delegation**: Coordinator delegates specific tasks to specialist agents
- ✅ **Protocol Abstraction**: Agents are unaware of delegation details

### **Real-World Applications**
- **Microservices Architecture**: Agents as specialized services
- **Load Distribution**: Distribute computational tasks across agents
- **Expertise Specialization**: Route queries to domain-specific agents
- **Fault Tolerance**: Fallback to different agents if one fails

## 🛡️ Optional: PII Protection

The demo includes optional PII (Personally Identifiable Information) protection:

```bash
curl -X POST http://localhost:8012/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text",
  "subformat": "english",
  "content": "My name is John Doe, email john@example.com. What are the weather alerts for Indiana?"
}'
```

With `NLIP_PII_ENABLED=true`, sensitive data is automatically detected and handled according to configured policies.

## 🔧 Troubleshooting

### Port Already in Use
If you get "Address already in use" errors, try different ports:

```bash
# LlamaIndex on port 8014
poetry run uvicorn llamaindex_demo.demo:app --host 0.0.0.0 --port 8014 --reload

# LangChain on port 8015 (update LLAMAINDEX_SERVER_URL in langchain_demo/demo.py)
poetry run uvicorn langchain_demo.demo:app --host 0.0.0.0 --port 8015 --reload
```

### API Key Issues
- Ensure environment variables are set in the same terminal where you run the servers
- Check API key validity and quotas
- For Qwen: Verify at https://dashscope.aliyun.com/
- For OpenRouter: Verify at https://openrouter.ai/

### Connection Errors
- Ensure LlamaIndex server (8013) starts **before** LangChain server (8012)
- Check that both servers show "ready" messages
- Verify network connectivity between the servers

## 🎉 Success Indicators

You'll know it's working when you see:

1. **Both servers start** without errors
2. **Tool delegation logs** appear in terminals  
3. **Structured responses** returned from curl commands
4. **Weather data** successfully retrieved and formatted

This demonstrates the power of NLIP for building collaborative AI agent systems! 🌟
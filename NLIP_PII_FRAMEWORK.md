# NLIP Framework PII Protection

## Overview

The NLIP framework now includes **optional, built-in PII (Personally Identifiable Information) detection** that automatically protects sensitive data in all NLIP applications.

## Key Features

- ✅ **Optional Protection**: Enable/disable via environment variable
- ✅ **Automatic Masking**: PII is masked during processing, unmasked in responses  
- ✅ **Flexible LLM Backend**: Works with Ollama, OpenAI, Azure, or custom implementations
- ✅ **Zero Code Changes**: Existing NLIP applications work unchanged
- ✅ **Backward Compatible**: Demos work exactly as before when PII is disabled

## Quick Start

### Enable PII Protection
```bash
# Enable PII protection with Ollama
export NLIP_PII_ENABLED=true
export NLIP_LLM_TYPE=ollama
export OLLAMA_MODEL=llama3.1

# Start your NLIP application (e.g., MCP demo)
poetry run start-mcp
```

### Test with PII Data
```bash
curl -X POST http://localhost:8010/nlip/ \
-H "Content-Type: application/json" \
-d '{
  "format": "text", 
  "subformat": "english", 
  "content": "Hi I am John Doe, my email is john@example.com. My phone number is 123-456-7890. What is the weather in Bloomington?"
}'
```

**Result**: PII is automatically masked during processing, response contains original unmasked data.

### Disable PII Protection (Default)
```bash
# Disable PII protection for backward compatibility
export NLIP_PII_ENABLED=false

# Start any NLIP application (e.g., Echo demo)  
poetry run start-echo
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NLIP_PII_ENABLED` | `false` | Enable/disable PII protection |
| `NLIP_LLM_TYPE` | `ollama` | LLM backend (`ollama`, `openai`, `azure`) |
| `OLLAMA_MODEL` | `llama3.1` | Ollama model for PII detection |
| `OPENAI_API_KEY` | - | OpenAI API key (if using OpenAI) |
| `OPENAI_MODEL` | `gpt-4` | OpenAI model for PII detection |
| `AZURE_ENDPOINT` | - | Azure OpenAI endpoint |
| `AZURE_API_KEY` | - | Azure OpenAI API key |
| `AZURE_DEPLOYMENT` | - | Azure deployment name |

## How It Works

### Framework Integration
The PII protection is built into the `NLIP_Session` class at the `correlated_execute()` level:

1. **Incoming Message**: Text is analyzed for PII before reaching your `execute()` method
2. **Masking**: If PII is found, it's replaced with placeholders (e.g., `[NAME_abc123]`)
3. **Processing**: Your application processes the masked text normally
4. **Response**: PII is automatically unmasked in the response to the user

### PII Detection Types
- Names (first, last, full names)
- Social Security Numbers  
- Email addresses
- Phone numbers
- Credit card numbers
- Addresses
- Dates of birth
- Driver's license numbers
- Passport numbers
- Custom patterns (configurable)

## Advanced Usage

### Custom LLM Implementation
You can implement your own PII detector by extending the `LLMInterface`:

```python
from nlip_server.pii import LLMInterface, PIIDetector

class MyCustomLLM(LLMInterface):
    def chat(self, prompt: str) -> str:
        # Your custom LLM implementation
        return my_llm_api.call(prompt)

# Use in your NLIP session
class MySession(NLIP_Session):
    def __init__(self):
        super().__init__()
        if self.pii_enabled:
            custom_llm = MyCustomLLM()
            self.pii_detector = PIIDetector(custom_llm)
```

## Demo Compatibility

### MCP Demo (with PII)
```bash
NLIP_PII_ENABLED=true poetry run start-mcp
# PII protection active - sensitive data is automatically protected
```

### Echo Demo (without PII)  
```bash
NLIP_PII_ENABLED=false poetry run start-echo
# Works exactly as before - no PII processing overhead
```

### All Other Demos
All existing NLIP demos work unchanged. Set `NLIP_PII_ENABLED=false` (default) for original behavior.

## Implementation Details

### Files Changed
- `nlip_server/pii/` - New PII detection module
- `nlip_server/server.py` - Enhanced `NLIP_Session` with optional PII  
- `nlip_soln/mcp/client/client.py` - Removed client-side PII logic
- `nlip_soln/mcp/mcp.py` - Updated to use framework PII protection

### Dependencies
- Optional `ollama` package for PII detection
- Install with: `poetry install --extras pii`

## Security Notes

- PII mappings are stored per session and automatically cleaned up
- No PII data persists beyond session lifetime
- LLM calls for PII detection are the only external dependency
- Framework fails safely - disables PII protection on errors

## Migration from Client-Side PII

If you had custom PII detection in your NLIP application:

1. **Remove** client-side PII detection code
2. **Set** `NLIP_PII_ENABLED=true` 
3. **Configure** your preferred LLM backend
4. **Test** - PII protection now happens automatically

The framework provides the same masking/unmasking functionality with better integration and consistency across all NLIP applications. 
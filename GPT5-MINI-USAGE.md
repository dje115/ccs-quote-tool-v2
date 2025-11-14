# GPT-5-Mini API Usage Reference

## CRITICAL: Correct Usage Pattern for This Project

### For Web Search Capabilities (Most Common Use Case)
```python
response = self.openai_client.responses.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "Your system prompt here"},
        {"role": "user", "content": "Your user prompt here"}
    ],
    tools=[{"type": "web_search"}],  # REQUIRED for web search
    max_completion_tokens=20000,  # Use 10000+ for complex tasks
    timeout=240.0  # Use 120.0+ for complex tasks
)
```

### Response Parsing (Handle Both Formats)
```python
if hasattr(response, 'choices') and len(response.choices) > 0:
    response_text = response.choices[0].message.content.strip()
elif hasattr(response, 'output'):
    response_text = response.output.strip()
else:
    response_text = str(response).strip()
```

### For Regular Chat (No Web Search)
```python
response = self.openai_client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "Your system prompt here"},
        {"role": "user", "content": "Your user prompt here"}
    ],
    max_completion_tokens=10000,  # Adjust as needed
    timeout=120.0  # Adjust as needed
)
```

## Key Points:
- ✅ Use `responses.create()` for web search capabilities
- ✅ Include `tools=[{"type": "web_search"}]` for web search
- ✅ Use `chat.completions.create()` for regular chat without web search
- ✅ Handle both response formats in parsing
- ❌ NEVER use `temperature` parameter (gpt-5-mini only supports default temperature)
- ✅ Use high token limits (10000+) for complex tasks
- ✅ Use longer timeouts (120.0+) for complex tasks

## Examples in Codebase:
- `ai_analysis_service.py` line 145: Website discovery with web search
- `lead_generation_service.py` line 331: Business list generation with web search
- Various other files use `chat.completions.create()` for regular AI tasks





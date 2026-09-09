---
name: openrouter-ai-sdk
description: Multi-model AI streaming and fallback router across 200+ LLMs via OpenRouter and Vercel AI SDK.
---

# OpenRouter & Vercel AI SDK Unified Router

Sovereign multi-model client routing requests across 200+ LLM backends (OpenAI, Anthropic, Google Gemini, Meta LLaMA 3.3, DeepSeek R1) with automated fallback, token streaming, and structured JSON outputs.

## Architecture

```text
[User Request]
       │
       ▼
[OpenRouter Router] ─── Failover Priority Chain ───► [1. Anthropic / Claude 3.7]
                                                    [2. OpenAI / GPT-4.5]
                                                    [3. DeepSeek / R1 671B]
                                                    [4. Meta / Llama 3.3 70B]
```

## Production Implementation: Python Sovereign Client

```python
import os
import json
import urllib.request

class OpenRouterClient:
    def __init__(self, api_key: str = None, site_url: str = "http://localhost:8899", app_name: str = "JARVIS"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": site_url,
            "X-Title": app_name,
            "Content-Type": "application/json"
        }

    def complete(self, prompt: str, models: list = None, temperature: float = 0.2) -> dict:
        models = models or [
            "anthropic/claude-3.7-sonnet",
            "openai/gpt-4o-mini",
            "deepseek/deepseek-r1",
            "meta-llama/llama-3.3-70b-instruct"
        ]
        payload = {
            "models": models,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, headers=self.headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
```

## TypeScript Vercel AI SDK Pattern

```typescript
import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import { streamText } from 'ai';

const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

export async function generateAutonomousResponse(prompt: string) {
  return await streamText({
    model: openrouter('anthropic/claude-3.7-sonnet'),
    prompt,
    system: 'You are an autonomous sovereign agent adhering to zero placeholders.'
  });
}
```

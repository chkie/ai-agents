import os
import anthropic
import time

_client = None

def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client

def complete(model: str, system: str, prompt: str, max_tokens: int = 1200, timeout_s: int = 60, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            resp = client().messages.create(
                model=model,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=timeout_s,
            )
            chunks = []
            for part in resp.content:
                if getattr(part, "type", "") == "text":
                    chunks.append(part.text)
            return "".join(chunks)
        except Exception as e:
            if attempt == retries:
                raise
            # Short backoff before retry
            time.sleep(1.5 ** attempt)
            continue
    
    # This should never be reached, but for type safety
    raise RuntimeError("All retry attempts failed")

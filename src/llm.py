import os
import anthropic
import time
import logging
from rich.console import Console

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

_client = None

def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client

def complete(model: str, system: str, prompt: str, max_tokens: int = 1200, timeout_s: int = 60, retries: int = 2) -> str:
    """Complete a chat with enhanced error handling and logging."""
    logger.info(f"Starting completion with model {model}, max_tokens={max_tokens}, timeout={timeout_s}s")
    
    for attempt in range(retries + 1):
        try:
            logger.debug(f"Attempt {attempt + 1}/{retries + 1} for model {model}")
            
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
            
            result = "".join(chunks)
            logger.info(f"Completion successful: {len(result)} characters returned")
            return result
            
        except anthropic.RateLimitError as e:
            wait_time = getattr(e, 'retry_after', 60)
            console.print(f"[yellow]⏳ Rate limit hit, waiting {wait_time}s...[/yellow]")
            logger.warning(f"Rate limit hit on attempt {attempt + 1}, waiting {wait_time}s")
            if attempt < retries:
                time.sleep(wait_time)
                continue
            else:
                raise SystemExit(f"Rate limit exceeded after {retries + 1} attempts")
                
        except anthropic.AuthenticationError as e:
            logger.error("Authentication failed - invalid API key")
            raise SystemExit("❌ Invalid ANTHROPIC_API_KEY - check your .env file")
            
        except anthropic.APITimeoutError as e:
            logger.warning(f"API timeout on attempt {attempt + 1}")
            console.print(f"[yellow]⏰ API timeout (attempt {attempt + 1}), retrying...[/yellow]")
            if attempt < retries:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise SystemExit(f"API timeout after {retries + 1} attempts")
                
        except anthropic.APIConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
            console.print(f"[yellow]🌐 Connection error (attempt {attempt + 1}), retrying...[/yellow]")
            if attempt < retries:
                time.sleep(3 ** attempt)  # Longer backoff for connection issues
                continue
            else:
                raise SystemExit(f"Connection failed after {retries + 1} attempts")
                
        except anthropic.BadRequestError as e:
            logger.error(f"Bad request error: {e}")
            raise SystemExit(f"❌ Bad request - check your parameters: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {e}")
            console.print(f"[red]💥 Unexpected error (attempt {attempt + 1}): {type(e).__name__}[/red]")
            if attempt < retries:
                time.sleep(1.5 ** attempt)
                continue
            else:
                logger.error(f"All {retries + 1} attempts failed")
                raise SystemExit(f"❌ All retry attempts failed: {type(e).__name__}: {e}")
    
    # This should never be reached, but for type safety
    raise RuntimeError("All retry attempts failed - this should not happen")

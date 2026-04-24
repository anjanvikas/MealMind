"""
MealMind v3 — Claude AI Client

Async Anthropic client. Platform-agnostic — no Telegram code here.
"""

import json
from datetime import datetime
from anthropic import AsyncAnthropic

from config import get_settings
from engine.prompts import SYSTEM_PROMPT

settings = get_settings()
client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# Simple in-memory cache: mapping context['id'] or a static key to recent messages
CONVERSATION_HISTORY = {}


async def ask_claude(
    prompt: str,
    context: dict = None,
    max_tokens: int = 4096,
) -> str:
    """
    Send a prompt to Claude and return the response.

    Args:
        prompt: The user prompt or generated prompt.
        context: Optional household context to append to system prompt.
        max_tokens: Maximum response length.

    Returns:
        Claude's response text, or a fallback message on error.
    """
    try:
        context_block = f"\n\nCURRENT DATE & TIME: {datetime.now().strftime('%A, %B %d, %Y, %I:%M %p')}\n"
        
        household_id = str(context.get("id")) if context and "id" in context else "anonymous"
        
        if context:
            context_block += (
                f"\nCURRENT HOUSEHOLD CONTEXT:\n"
                f"{json.dumps(context, indent=2, default=str)}"
            )

        # Retrieve memory
        memory = CONVERSATION_HISTORY.get(household_id, [])
        
        # Build message chain
        messages = memory + [{"role": "user", "content": prompt}]

        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT + context_block,
            messages=messages,
        )
        
        assistant_text = response.content[0].text
        
        # Store back in memory (limit to last 6 turns = 3 user, 3 assistant)
        memory.append({"role": "user", "content": prompt})
        memory.append({"role": "assistant", "content": assistant_text})
        CONVERSATION_HISTORY[household_id] = memory[-6:]
        
        return assistant_text

    except Exception as e:
        print(f"❌ Claude API error: {e}")
        return (
            "Sorry, I'm having trouble thinking right now. "
            "Please try again in a moment! 🙏"
        )


async def ask_claude_raw(
    prompt: str,
    system: str = None,
    max_tokens: int = 200,
) -> str:
    """
    Raw Claude call with a custom system prompt.
    Used for extraction tasks (dish names, recipe parsing, etc.)
    """
    try:
        message = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant. Be concise.",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"❌ Claude raw call error: {e}")
        return ""

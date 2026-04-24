"""
MealMind v3 — Pattern Detector

Detects implicit taste patterns from meal ratings.
Runs after every 5th rating — triggered from feedback handler.
"""

import json

from db import queries as db
from engine.claude_client import ask_claude_raw
from engine.prompts import PATTERN_ANALYSIS_PROMPT


async def run_pattern_detection(household) -> list:
    """
    Analyse meal ratings to detect implicit preference patterns.

    Returns list of detected patterns (may be empty).
    Each pattern has: pattern_type, description, suggestion.
    """
    ratings = await db.get_ratings_by_day_of_week(household.id)

    if not ratings:
        return []

    # Need at least some data to detect patterns
    total_ratings = sum(len(v) for v in ratings.values())
    if total_ratings < 5:
        return []

    prompt = PATTERN_ANALYSIS_PROMPT.format(
        ratings=json.dumps(ratings, indent=2)
    )
    raw = await ask_claude_raw(prompt, max_tokens=400)

    patterns = []
    try:
        cleaned = raw.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        detected = json.loads(cleaned)
        for p in detected:
            await db.save_pattern_signal(household.id, p)
            patterns.append(p)
    except (json.JSONDecodeError, IndexError):
        pass

    return patterns


async def get_patterns_to_surface(household) -> list:
    """Get unsurfaced patterns to present to the user as rule suggestions."""
    return await db.get_unsurfaced_patterns(household.id)


async def surface_pattern(pattern_id):
    """Mark a pattern as surfaced."""
    await db.mark_pattern_surfaced(pattern_id)


async def confirm_pattern_as_rule(pattern_id):
    """Confirm a pattern — converts it to a standing rule."""
    await db.confirm_pattern(pattern_id)

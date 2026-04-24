"""
MealMind v3 — Learning Engine

Taste profile updates: ratings, dislikes, priority changes, member parsing.
Platform-agnostic — no Telegram code here.
"""

import json
from datetime import date, timedelta

from db import queries as db
from engine.claude_client import ask_claude, ask_claude_raw
from engine.prompts import EXTRACT_DISH_PROMPT, PARSE_MEMBERS_PROMPT


async def process_rating(household, dish_name: str, rating: str) -> str:
    """Process a meal rating and update taste profile."""
    if rating == "bad":
        avoided_until = date.today() + timedelta(weeks=4)
        await db.add_dislike(household.id, dish_name, avoided_until)
        return (
            f"Got it — *{dish_name}* avoided for 4 weeks.\n"
            "I'll replace it in the next plan."
        )

    elif rating == "loved":
        await db.add_loved(household.id, dish_name)
        return f"🔥 Noted! *{dish_name}* coming back in 3–4 weeks."

    elif rating == "good":
        await db.save_rating(household.id, dish_name, "positive")
        return "Glad you enjoyed it! 😊"

    return "Noted! ✅"


async def process_dislike_freetext(household, message: str) -> str:
    """Extract dish name from freeform dislike and save."""
    prompt = EXTRACT_DISH_PROMPT.format(message=message)
    dish = await ask_claude_raw(
        prompt,
        system="Extract the dish name from this message. Reply with ONLY the dish name.",
        max_tokens=50,
    )

    if not dish or dish == "UNKNOWN":
        return "Which dish didn't you like? Just tell me the name."

    avoided_until = date.today() + timedelta(weeks=4)
    await db.add_dislike(household.id, dish, avoided_until)
    return f"Got it — *{dish}* removed from your plan for 4 weeks."


async def process_dislike_with_reason(
    household, dish_name: str, reason: str
) -> str:
    """Process a dislike with a specific reason."""
    avoided_until = date.today() + timedelta(weeks=4)
    await db.add_dislike(household.id, dish_name, avoided_until, reason=reason)

    reason_ack = {
        "dish": "Don't like this dish",
        "spicy": "Too spicy",
        "bland": "Too bland",
        "portion": "Wrong portion",
    }
    ack = reason_ack.get(reason, "Noted")
    return (
        f"{ack} — *{dish_name}* avoided for 4 weeks.\n"
        "I'll adjust future plans accordingly."
    )


async def update_priority(household, priority: str) -> str:
    """Handle dietary priority changes."""
    if priority == "increase_protein":
        await db.update_member_field(household.id, "protein_goal", "high")
        await db.add_standing_rule(
            household.id, "protein_priority", "extra_high", confirmed=True
        )
        return (
            "💪 Got it — I'll boost protein in your next plan.\n"
            "Expect more eggs at breakfast and extra dal/paneer/chicken."
        )

    elif priority == "lighter":
        await db.add_standing_rule(
            household.id, "lighter_meals", "true", confirmed=True
        )
        return "Noted — lighter meals for the next few days."

    return "Updated! ✅"


def extract_language_preference(text: str) -> str:
    """Extract requested language from text."""
    text = text.lower()
    if "hindi" in text:
        return "hindi"
    if "kannada" in text:
        return "kannada"
    if "telugu" in text:
        return "telugu"
    return "english"


async def parse_members_from_text(text: str) -> list:
    """Use Claude to parse freeform member descriptions into structured data."""
    prompt = PARSE_MEMBERS_PROMPT.format(text=text)
    raw = await ask_claude_raw(prompt, max_tokens=200)

    try:
        # Handle ```json ... ``` wrapping
        cleaned = raw.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        return [
            {"name": "User", "diet_type": "non_vegetarian"},
            {"name": "Wife", "diet_type": "vegetarian"},
        ]

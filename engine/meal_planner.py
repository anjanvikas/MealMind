"""
MealMind v3 — Meal Plan Generator

Platform-agnostic plan generation logic.
Builds context-rich prompts and calls Claude.
"""

from datetime import date
from typing import Optional

from db import queries as db
from engine.claude_client import ask_claude
from engine.prompts import (
    WEEKLY_PLAN_PROMPT_P1, WEEKLY_PLAN_PROMPT_P2, 
    DAILY_PLAN_PROMPT, SINGLE_MEAL_PROMPT,
)


async def generate_plan(
    household,
    plan_type: str = "week",
    meal: str = None,
    language: str = None,
) -> str:
    """
    Generate a meal plan.

    Args:
        household: Household ORM object.
        plan_type: "week", "day", or "meal".
        meal: Specific meal type (for plan_type="meal").
        language: Optional language override.

    Returns:
        Formatted meal plan text.
    """
    # Gather context
    profile = await db.get_full_profile(household.id)
    dislikes = await db.get_active_dislikes(household.id)
    loved = await db.get_loved_dishes(household.id)
    recent = await db.get_recent_meals(household.id, days=14)
    rules = await db.get_standing_rules(household.id)

    # Build member summary
    members_summary = _build_members_summary(profile)

    # Language instruction
    lang = language or profile.get("preferred_language", "english")
    language_instruction = ""
    if lang != "english":
        language_instruction = f"\n\nGenerate the full output in {lang}."

    # Common context
    ctx = {
        "members_summary": members_summary,
        "dislikes": ", ".join(dislikes) if dislikes else "none",
        "loved": ", ".join(loved[:4]) if loved else "none",
        "recent": ", ".join(recent) if recent else "none",
        "rules": ", ".join(rules) if rules else "none",
        "budget": profile.get("budget", "budget_friendly"),
        "has_cook": "Yes" if profile.get("has_cook", True) else "No",
        "language_instruction": language_instruction,
    }

    # Select prompt template & call Claude
    if plan_type == "week":
        # Make two calls for a weekly plan to avoid cutoff
        prompt_p1 = WEEKLY_PLAN_PROMPT_P1.format(**ctx)
        response_p1 = await ask_claude(prompt_p1, context=profile)
        
        ctx["part1_plan"] = response_p1
        prompt_p2 = WEEKLY_PLAN_PROMPT_P2.format(**ctx)
        response_p2 = await ask_claude(prompt_p2, context=profile)
        
        response = f"{response_p1}\n\n{response_p2}"
    else:
        if plan_type == "day":
            prompt = DAILY_PLAN_PROMPT.format(**ctx)
        elif plan_type == "meal":
            ctx["meal"] = meal or "dinner"
            prompt = SINGLE_MEAL_PROMPT.format(**ctx)
        else:
            prompt = DAILY_PLAN_PROMPT.format(**ctx)
        
        response = await ask_claude(prompt, context=profile)

    # Save plan to DB
    await db.save_plan(household.id, response, plan_type)

    return response


def _build_members_summary(profile: dict) -> str:
    """Build a readable member summary for prompts."""
    members = profile.get("members", [])
    if not members:
        return (
            "- Person 1: non-vegetarian, protein goal: high, spice: medium\n"
            "- Person 2 (wife): vegetarian, protein goal: high, spice: medium"
        )

    lines = []
    for m in members:
        allergies = ", ".join(m.get("allergies", [])) or "none"
        dislikes = ", ".join(m.get("disliked_ingredients", [])) or "none"
        lines.append(
            f"- {m['name']}: {m['diet_type']}, "
            f"protein: {m.get('protein_goal', 'high')}, "
            f"spice: {m.get('spice_level', 'medium')}, "
            f"allergies: {allergies}, "
            f"dislikes: {dislikes}"
        )
    return "\n".join(lines)

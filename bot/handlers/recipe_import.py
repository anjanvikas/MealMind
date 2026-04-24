"""
MealMind v3 — Recipe Import Handler

Extracts recipes from shared URLs using httpx + BeautifulSoup + Claude.
"""

import re
import json

import httpx
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes

from db import queries as db
from engine.claude_client import ask_claude_raw
from engine.prompts import EXTRACT_RECIPE_PROMPT
from bot.keyboards import yes_no_keyboard

URL_PATTERN = re.compile(r"https?://\S+")


async def import_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared URLs — extract and save recipe."""
    chat_id = update.effective_chat.id
    text = update.message.text or ""
    url_match = URL_PATTERN.search(text)

    if not url_match:
        return

    url = url_match.group(0)
    household = await db.get_household(chat_id)
    if not household or not household.onboarding_complete:
        return

    await update.message.reply_text("Analysing that link... 🔍")
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Fetch page content
    page_text = ""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; MealMind/1.0; "
                        "+https://mealmind.app)"
                    )
                },
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            page_text = soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        print(f"⚠️ URL fetch error: {e}")

    if not page_text:
        await update.message.reply_text(
            "Couldn't load that link 😕\nTry sharing a direct recipe page URL."
        )
        return

    # Extract recipe via Claude
    prompt = EXTRACT_RECIPE_PROMPT.format(url=url, content=page_text[:2000])
    raw = await ask_claude_raw(prompt, max_tokens=300)

    try:
        # Handle ```json wrapping
        cleaned = raw.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        recipe = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        await update.message.reply_text(
            "Couldn't read that link. Try a direct recipe page."
        )
        return

    if not recipe.get("found"):
        await update.message.reply_text("No recipe found in that link. 🤔")
        return

    # Assign to correct member by diet type
    member = await db.get_member_by_diet(
        household.id, recipe.get("diet_type", "non_vegetarian")
    )
    if member:
        await db.save_recipe(member.id, recipe, url)
        owner = f"<b>{member.name}</b>'s"
    else:
        owner = "your"

    await update.message.reply_text(
        f"✅ Saved: <b>{recipe.get('dish_name', 'Recipe')}</b> "
        f"({recipe.get('diet_type', 'unknown')})\n"
        f"🍽️ Cuisine: {recipe.get('cuisine_type', 'Unknown')}\n"
        f"💪 Protein: {recipe.get('protein_level', 'medium')}\n"
        f"Added to {owner} profile.\n\n"
        "Add to next week's plan?",
        reply_markup=yes_no_keyboard("recipe:add_to_plan", "recipe:skip"),
        parse_mode="HTML",
    )

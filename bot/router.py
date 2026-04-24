"""
MealMind v3 — Message Router

Dispatches incoming text messages to the right handler.
Uses keyword matching first, Claude freeform fallback.
"""

import re

from telegram import Update
from telegram.ext import ContextTypes

from db import queries as db
from bot.handlers.start import handle_onboarding_text
from bot.handlers.planner import plan_handler
from bot.handlers.feedback import (
    handle_dislike, handle_freeform_feedback, handle_priority_update,
)
from bot.handlers.grocery import grocery_handler
from bot.handlers.cook_brief import cook_brief_handler
from bot.handlers.recipe_import import import_handler
from bot.handlers.freeform import freeform_handler
from engine.learner import extract_language_preference

URL_PATTERN = re.compile(r"https?://\S+")


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main message dispatcher for text messages.

    Routes by:
    1. Onboarding in progress → onboarding handler
    2. URL detected → recipe import
    3. Keyword match → specific handler
    4. Fallback → Claude freeform
    """
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    text_lower = text.lower()

    household = await db.get_household(chat_id)

    # ── Onboarding in progress ───────────────────────────────
    if not household:
        from bot.handlers.start import start_handler
        await start_handler(update, context)
        return

    if not household.onboarding_complete:
        await handle_onboarding_text(update, context, household)
        return

    # ── URL → recipe import ──────────────────────────────────
    if URL_PATTERN.search(text):
        await import_handler(update, context)
        return

    # ── Weekly plan ──────────────────────────────────────────
    if any(w in text_lower for w in [
        "plan my week", "weekly plan", "plan week", "week plan"
    ]):
        await plan_handler(update, context, plan_type="week")
        return

    # ── Daily plan ───────────────────────────────────────────
    if any(w in text_lower for w in [
        "today", "what should i eat", "what to eat",
        "plan today", "today's plan"
    ]):
        await plan_handler(update, context, plan_type="day")
        return

    # ── Single meal ──────────────────────────────────────────
    if any(w in text_lower for w in ["dinner", "lunch", "breakfast", "snack"]):
        meal = next(
            (w for w in ["dinner", "lunch", "breakfast", "snack"] if w in text_lower),
            None,
        )
        if meal and any(w in text_lower for w in [
            "suggest", "what", "plan", "make", "should"
        ]):
            await plan_handler(update, context, plan_type="meal", meal=meal)
            return

    # ── Grocery list ─────────────────────────────────────────
    if any(w in text_lower for w in [
        "grocery", "ingredients", "shopping list", "shopping"
    ]):
        await grocery_handler(update, context)
        return

    # ── Cook briefing ────────────────────────────────────────
    if any(w in text_lower for w in [
        "cook", "instructions", "brief", "cooking"
    ]):
        lang = extract_language_preference(text)
        await cook_brief_handler(update, context, language=lang)
        return

    # ── Dislikes ─────────────────────────────────────────────
    if any(w in text_lower for w in [
        "didn't like", "don't like", "dislike", "hated",
        "didn't enjoy", "wasn't good"
    ]):
        await handle_dislike(update, context)
        return

    # ── Positive feedback ────────────────────────────────────
    if any(w in text_lower for w in [
        "loved", "amazing", "favourite", "favorite", "delicious"
    ]):
        await handle_freeform_feedback(update, context, sentiment="loved")
        return

    # ── Priority updates ─────────────────────────────────────
    if any(w in text_lower for w in [
        "more protein", "high protein", "extra protein"
    ]):
        await handle_priority_update(update, context, "increase_protein")
        return

    if any(w in text_lower for w in [
        "light meal", "less heavy", "keep it light", "lighter"
    ]):
        await handle_priority_update(update, context, "lighter")
        return

    # ── Language switch ──────────────────────────────────────
    if any(w in text_lower for w in [
        "in hindi", "in kannada", "in telugu", "in english"
    ]):
        lang = extract_language_preference(text)
        await plan_handler(update, context, plan_type="day", language=lang)
        return

    # ── Yes / confirmations (grocery follow-up) ──────────────
    if text_lower in ["yes", "yeah", "sure", "ok", "yep", "ya"]:
        plan = await db.get_active_plan(household.id)
        if plan:
            await grocery_handler(update, context)
            return

    # ── Fallback → Claude freeform ───────────────────────────
    await freeform_handler(update, context)

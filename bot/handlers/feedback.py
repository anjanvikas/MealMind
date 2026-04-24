"""
MealMind v3 — Feedback Handler

Handles meal ratings (inline buttons), dislikes, and priority updates.
Triggers pattern detection every 5th rating.
"""

from telegram import Update
from telegram.ext import ContextTypes

from db import queries as db
from engine.learner import (
    process_rating, process_dislike_freetext,
    process_dislike_with_reason, update_priority,
)
from engine.pattern_detector import run_pattern_detection
from bot.keyboards import dislike_reason_keyboard, pattern_confirm_keyboard


async def rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rating inline button presses."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    data = query.data  # e.g. "rating:good:Palak Dal"
    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    _, rating, dish_name = parts
    household = await db.get_household(chat_id)
    if not household:
        return

    if rating == "bad":
        # Ask for reason before saving
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"What was off about <b>{dish_name}</b>?",
            reply_markup=dislike_reason_keyboard(dish_name),
            parse_mode="HTML",
        )
        return

    # Process the rating
    response = await process_rating(household, dish_name, rating)
    await context.bot.send_message(
        chat_id=chat_id,
        text=response,
        parse_mode="HTML",
    )

    # Check if we should run pattern detection (every 5th rating)
    await _maybe_run_pattern_detection(household, chat_id, context)


async def dislike_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dislike reason inline button presses."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    data = query.data  # e.g. "dislike:spicy:Palak Dal"
    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    _, reason, dish_name = parts
    household = await db.get_household(chat_id)
    if not household:
        return

    response = await process_dislike_with_reason(household, dish_name, reason)
    await context.bot.send_message(
        chat_id=chat_id,
        text=response,
        parse_mode="HTML",
    )

    # Check pattern detection
    await _maybe_run_pattern_detection(household, chat_id, context)


async def handle_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle freeform dislike messages."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)
    if not household:
        return

    message = update.message.text
    response = await process_dislike_freetext(household, message)
    await update.message.reply_text(response, parse_mode="HTML")


async def handle_freeform_feedback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sentiment: str = "loved"
):
    """Handle freeform positive feedback messages."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)
    if not household:
        return

    last_meal = await db.get_last_meal(household.id)
    if last_meal:
        response = await process_rating(household, last_meal.dish_name, sentiment)
    else:
        response = "Thanks! Which dish did you love? Tell me and I'll remember it."

    await update.message.reply_text(response, parse_mode="HTML")
    await _maybe_run_pattern_detection(household, chat_id, context)


async def handle_priority_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE, priority: str
):
    """Handle dietary priority change messages."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)
    if not household:
        return

    response = await update_priority(household, priority)
    await update.message.reply_text(response, parse_mode="HTML")


async def pattern_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pattern confirmation/rejection callbacks."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    data = query.data  # e.g. "pattern:confirm:uuid"
    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    _, action, pattern_id = parts

    if action == "confirm":
        from engine.pattern_detector import confirm_pattern_as_rule
        await confirm_pattern_as_rule(pattern_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Locked in as a standing rule! I'll apply this to all future plans.",
        )
    else:
        from engine.pattern_detector import surface_pattern
        await surface_pattern(pattern_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text="No problem — I'll keep learning. 📊",
        )


async def _maybe_run_pattern_detection(household, chat_id, context):
    """Run pattern detection every 5th rating."""
    total = await db.count_ratings(household.id)
    if total > 0 and total % 5 == 0:
        patterns = await run_pattern_detection(household)
        for p in patterns:
            suggestion = p.get("suggestion", "I noticed a pattern in your preferences.")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📊 <b>Pattern Detected:</b>\n{p.get('description', '')}\n\n{suggestion}",
                reply_markup=pattern_confirm_keyboard(str(p.get("id", ""))),
                parse_mode="HTML",
            )

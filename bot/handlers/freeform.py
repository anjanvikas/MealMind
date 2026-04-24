"""
MealMind v3 — Freeform Message Handler

Handles messages that don't match any keyword pattern.
Uses Claude to interpret user intent.
"""

from telegram import Update
from telegram.ext import ContextTypes

from db import queries as db
from engine.claude_client import ask_claude
from engine.prompts import FREEFORM_PROMPT


async def freeform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unrecognized messages — let Claude interpret."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)

    if not household or not household.onboarding_complete:
        await update.message.reply_text(
            "Let's set up your profile first! Send /start"
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    message = update.message.text
    profile = await db.get_full_profile(household.id)

    prompt = FREEFORM_PROMPT.format(message=message)
    response = await ask_claude(prompt, context=profile)

    await update.message.reply_text(response, parse_mode="HTML")

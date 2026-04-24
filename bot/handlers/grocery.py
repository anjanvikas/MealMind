"""
MealMind v3 — Grocery List Handler

Generates consolidated grocery list from active meal plan.
"""

from telegram import Update
from telegram.ext import ContextTypes

from db import queries as db
from engine.claude_client import ask_claude
from engine.prompts import GROCERY_PROMPT


async def grocery_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    from_callback: bool = False,
):
    """Generate and send a grocery list."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)

    if not household:
        return

    plan = await db.get_active_plan(household.id)
    if not plan:
        msg = "No active plan found. Say <b>plan my week</b> first."
        if from_callback:
            await context.bot.send_message(
                chat_id=chat_id, text=msg, parse_mode="HTML"
            )
        else:
            await update.message.reply_text(msg, parse_mode="HTML")
        return

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    profile = await db.get_full_profile(household.id)
    prompt = GROCERY_PROMPT.format(
        plan_text=plan.plan_text,
        num_people=profile.get("num_people", 2),
    )

    result = await ask_claude(prompt)

    if from_callback:
        await context.bot.send_message(
            chat_id=chat_id, text=result, parse_mode="HTML"
        )
    else:
        await update.message.reply_text(result, parse_mode="HTML")

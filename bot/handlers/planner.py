"""
MealMind v3 — Plan Handler

Handles /plan, /today, /week commands and plan-related callbacks.
Splits long plans into multiple Telegram messages (4096 char limit).
"""

from telegram import Update
from telegram.ext import ContextTypes

from db import queries as db
from engine.meal_planner import generate_plan
from bot.keyboards import plan_actions_keyboard
from bot.handlers.grocery import grocery_handler
from bot.handlers.cook_brief import cook_brief_handler

# Telegram message character limit
TELEGRAM_CHAR_LIMIT = 4096


def split_message(text: str, limit: int = TELEGRAM_CHAR_LIMIT) -> list[str]:
    """Smartly split a long HTML message into chunks that fit Telegram's limit, preserving HTML tags."""
    if len(text) <= limit:
        return [text]

    chunks = []
    
    # Try splitting by days first (primary delimiter for weekly plans)
    delimiter = "<b>📅"
    if delimiter in text:
        parts = text.split(delimiter)
        # The first part might be leading intro text
        sections = [parts[0]] if parts[0].strip() else []
        for p in parts[1:]:
            sections.append(delimiter + p)
    else:
        # Fallback to block splitting by paragraphs
        sections = [part for part in text.split("\n\n") if part.strip()]

    current_chunk = ""
    for sec in sections:
        # Re-attach double newlines if we split by paragraphs
        sec_str = sec if delimiter in text else (sec + "\n\n")
        
        if len(current_chunk) + len(sec_str) <= limit:
            current_chunk += sec_str
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Sub-split by lines if a single section somehow exceeds the limit
            if len(sec_str) > limit:
                lines = sec_str.split("\n")
                temp_chunk = ""
                for line in lines:
                    if len(temp_chunk) + len(line) + 1 <= limit:
                        temp_chunk += line + "\n"
                    else:
                        chunks.append(temp_chunk.strip())
                        temp_chunk = line + "\n"
                current_chunk = temp_chunk
            else:
                current_chunk = sec_str

    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks


async def plan_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    plan_type: str = "week",
    meal: str = None,
    language: str = None,
):
    """Generate and send a meal plan."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)

    if not household or not household.onboarding_complete:
        await update.message.reply_text(
            "Let's set up your profile first! Send /start"
        )
        return

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Generate the plan
    response = await generate_plan(
        household,
        plan_type=plan_type,
        meal=meal,
        language=language,
    )

    # Split and send
    chunks = split_message(response)
    for i, chunk in enumerate(chunks):
        # Add action buttons to the last chunk
        kb = plan_actions_keyboard() if i == len(chunks) - 1 else None
        await context.bot.send_message(
            chat_id=chat_id,
            text=chunk,
            reply_markup=kb,
            parse_mode="HTML",
        )


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan-related inline button callbacks."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    data = query.data  # e.g. "plan:grocery", "plan:cook", "plan:change"
    _, action = data.split(":", 1)

    if action == "grocery":
        await grocery_handler(update, context, from_callback=True)
    elif action == "cook":
        await cook_brief_handler(update, context, from_callback=True)
    elif action == "change":
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "What would you like to change?\n\n"
                "Just tell me, e.g.:\n"
                "• <i>Make Monday dinner lighter</i>\n"
                "• <i>Replace Tuesday breakfast</i>\n"
                "• <i>More protein on Wednesday</i>"
            ),
            parse_mode="HTML",
        )
    elif action == "week:confirm":
        await plan_handler(update, context, plan_type="week")
    elif action == "week:skip":
        await context.bot.send_message(
            chat_id=chat_id,
            text="No problem! Just say <b>plan my week</b> whenever you're ready. 🍽️",
            parse_mode="HTML",
        )
